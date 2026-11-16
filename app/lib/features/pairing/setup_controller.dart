import 'dart:async';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../data/board_setup_protocol.dart';
import '../../data/board_setup_repository.dart';
import '../../data/device_repository.dart';

/// Steps of "Set up a board" (docs/protocol.md "BLE provisioning", ADR 0009).
enum SetupStep {
  idle,
  scanning,
  connecting, // includes pairing: codes match on phone and board, BOOT tap
  pickWifi,
  joiningWifi,
  registering,
  sendingKey,
  finishing,
  done,
  failed,
}

/// Screen state. Never holds the Wi-Fi password or the board token: those live
/// only in local variables for the duration of one write.
class SetupState {
  const SetupState({
    this.step = SetupStep.idle,
    this.boards = const [],
    this.board,
    this.info,
    this.networks = const [],
    this.scanningWifi = false,
    this.wifiError,
    this.wifiErrorReason,
    this.selected,
    this.manualEntry = false,
    this.manualSsid = '',
    this.wifiAttempts = 0,
    this.message,
  });

  final SetupStep step;
  final List<FoundBoard> boards;
  final FoundBoard? board;
  final BoardInfo? info;
  final List<WifiNetwork> networks;
  final bool scanningWifi;
  final String? wifiError; // shown on the Wi-Fi step (e.g. wrong password)
  final String? wifiErrorReason; // board reason behind wifiError, for help text
  final WifiNetwork? selected; // the network page is open for this one
  final bool manualEntry; // the network page is open for a typed name
  final String manualSsid; // kept across a failed attempt (not a secret)
  final int wifiAttempts; // failed attempts on the open network page
  final String? message; // shown on the failed step

  /// The network page (rather than the list) is showing.
  bool get networkPageOpen => selected != null || manualEntry;

  SetupState copyWith({
    SetupStep? step,
    List<FoundBoard>? boards,
    FoundBoard? board,
    BoardInfo? info,
    List<WifiNetwork>? networks,
    bool? scanningWifi,
    String? wifiError,
    String? wifiErrorReason,
    bool clearWifiError = false,
    WifiNetwork? selected,
    bool clearSelected = false,
    bool? manualEntry,
    String? manualSsid,
    int? wifiAttempts,
    String? message,
  }) => SetupState(
    step: step ?? this.step,
    boards: boards ?? this.boards,
    board: board ?? this.board,
    info: info ?? this.info,
    networks: networks ?? this.networks,
    scanningWifi: scanningWifi ?? this.scanningWifi,
    wifiError: clearWifiError ? null : (wifiError ?? this.wifiError),
    wifiErrorReason: clearWifiError ? null : (wifiErrorReason ?? this.wifiErrorReason),
    selected: clearSelected ? null : (selected ?? this.selected),
    manualEntry: manualEntry ?? this.manualEntry,
    manualSsid: manualSsid ?? this.manualSsid,
    wifiAttempts: wifiAttempts ?? this.wifiAttempts,
    message: message ?? this.message,
  );

  @override
  String toString() => 'SetupState($step, board: ${board?.name}, networks: ${networks.length})';
}

class SetupController extends Notifier<SetupState> {
  static const wifiTimeout = Duration(seconds: 40);
  static const signInTimeout = Duration(seconds: 30);

  BoardLink? _link;
  StreamSubscription<List<FoundBoard>>? _scan;
  StreamSubscription<BoardStatus>? _statusSub;
  final _statuses = StreamController<BoardStatus>.broadcast();

  BoardSetupRepository get _boards => ref.read(boardSetupRepositoryProvider);
  DeviceRepository get _devices => ref.read(deviceRepositoryProvider);

  @override
  SetupState build() {
    ref.onDispose(() {
      _scan?.cancel();
      _statusSub?.cancel();
      _link?.disconnect();
      _statuses.close();
    });
    return const SetupState();
  }

  void _fail(String message) {
    _statusSub?.cancel();
    _statusSub = null;
    _link?.disconnect();
    _link = null;
    state = state.copyWith(step: SetupStep.failed, message: message);
  }

  Future<void> startScan() async {
    unawaited(_scan?.cancel());
    state = const SetupState(step: SetupStep.scanning);
    final done = Completer<void>();
    _scan = _boards.scan().listen(
      (found) {
        if (state.step == SetupStep.scanning) state = state.copyWith(boards: found);
      },
      onError: (Object e) {
        if (!done.isCompleted) done.complete();
        _fail(e is BoardSetupFailure ? e.message : 'Could not scan for boards.');
      },
      onDone: () {
        if (!done.isCompleted) done.complete();
        if (state.step == SetupStep.scanning) state = state.copyWith(step: SetupStep.idle);
      },
    );
    await done.future;
  }

  Future<void> choose(FoundBoard board) async {
    unawaited(_scan?.cancel()); // stops the BLE scan; nothing to wait for
    _scan = null;
    state = state.copyWith(step: SetupStep.connecting, board: board);
    try {
      final link = await _boards.connect(board);
      _link = link;
      final info = await link.readInfo();
      final mismatch = protocolMismatch(info.protocol);
      if (mismatch != null) {
        _fail(mismatch); // also disconnects
        return;
      }
      _statusSub = link.status().listen(_statuses.add, onError: (_) {});
      state = state.copyWith(step: SetupStep.pickWifi, info: info);
      await refreshWifi();
    } on BoardSetupFailure catch (e) {
      _fail(e.message);
    }
  }

  /// Opens the network page for [network].
  void selectNetwork(WifiNetwork network) => state = state.copyWith(
    selected: network,
    manualEntry: false,
    wifiAttempts: 0,
    clearWifiError: true,
  );

  /// Opens the network page for a network typed by hand (hidden networks).
  void enterManually() => state = state.copyWith(
    clearSelected: true,
    manualEntry: true,
    manualSsid: '',
    wifiAttempts: 0,
    clearWifiError: true,
  );

  /// Back from the network page to the list.
  void backToNetworks() => state = state.copyWith(
    clearSelected: true,
    manualEntry: false,
    wifiAttempts: 0,
    clearWifiError: true,
  );

  Future<void> refreshWifi() async {
    final link = _link;
    if (link == null) return;
    state = state.copyWith(scanningWifi: true);
    try {
      final networks = await link.scanWifi();
      state = state.copyWith(networks: networks, scanningWifi: false);
    } on BoardSetupFailure catch (e) {
      state = state.copyWith(scanningWifi: false, wifiError: e.message);
    } on TimeoutException {
      state = state.copyWith(scanningWifi: false, wifiError: 'The board found no networks.');
    }
  }

  /// Sends the Wi-Fi details, then registers the board and hands it its key.
  /// [password] is used for one write and not kept.
  Future<void> joinWifi(String ssid, String password) async {
    final link = _link;
    final info = state.info;
    if (link == null || info == null) return;
    final invalid = validateWifi(ssid, password);
    if (invalid != null) {
      state = state.copyWith(wifiError: invalid, wifiErrorReason: 'bad_creds');
      return;
    }
    if (state.manualEntry) state = state.copyWith(manualSsid: ssid);
    state = state.copyWith(step: SetupStep.joiningWifi, clearWifiError: true);
    try {
      // Listen before writing: only answers to this write count.
      final wifiResult = _statuses.stream
          .firstWhere(
            (s) =>
                s.state == 'wifi_ok' ||
                s.state == 'wifi_failed' ||
                s.reason == 'bad_creds' ||
                s.reason == 'not_ready',
          )
          .timeout(wifiTimeout);
      wifiResult.ignore(); // if the write throws, this wait is abandoned
      await link.writeCreds(ssid, password);
      final wifi = await wifiResult;
      if (wifi.state != 'wifi_ok') {
        // Back to the same network page (not the list), with the reason on top.
        state = state.copyWith(
          step: SetupStep.pickWifi,
          wifiError: describeReason(wifi.reason),
          wifiErrorReason: wifi.reason,
          wifiAttempts: state.wifiAttempts + 1,
        );
        return;
      }

      state = state.copyWith(step: SetupStep.registering);
      final token = await _devices.registerDevice(info.deviceId);

      state = state.copyWith(step: SetupStep.sendingKey);
      final signIn = _statuses.stream
          .firstWhere((s) => s.state == 'signed_in' || s.reason != null)
          .timeout(signInTimeout);
      signIn.ignore();
      await link.writeToken(token); // the token is not kept after this write
      state = state.copyWith(step: SetupStep.finishing);
      final result = await signIn;
      if (result.state != 'signed_in') {
        _fail(describeReason(result.reason));
        return;
      }
      unawaited(_statusSub?.cancel());
      _statusSub = null;
      await link.disconnect();
      _link = null;
      state = state.copyWith(step: SetupStep.done);
    } on BoardSetupFailure catch (e) {
      _fail(e.message);
    } on DeviceFailure catch (e) {
      _fail(e.message);
    } on TimeoutException {
      _fail(
        state.step == SetupStep.joiningWifi
            ? 'The board did not report back about Wi-Fi.'
            : 'The board did not confirm it signed in. Check it shows the heart screen.',
      );
    } on StateError {
      _fail('Lost the board. Is it still powered and showing the setup screen?');
    }
  }

  Future<void> cancel() async {
    unawaited(_scan?.cancel());
    unawaited(_statusSub?.cancel());
    _statusSub = null;
    await _link?.disconnect();
    _link = null;
    state = const SetupState();
  }
}

final setupControllerProvider = NotifierProvider.autoDispose<SetupController, SetupState>(
  SetupController.new,
);
