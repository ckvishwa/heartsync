import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:network_info_plus/network_info_plus.dart';
import 'package:permission_handler/permission_handler.dart';

/// The Wi-Fi network the phone is on right now. Only the name: Android and iOS
/// never give an app a saved Wi-Fi password.
abstract class PhoneWifiRepository {
  /// The connected network's name, or null when unknown (no permission, location
  /// services off, not on Wi-Fi, or the platform hides it).
  Future<String?> currentSsid();
}

class PlatformPhoneWifiRepository implements PhoneWifiRepository {
  @override
  Future<String?> currentSsid() async {
    try {
      // Android hides the network name unless location permission is granted
      // (and location services are on). iOS needs the same permission.
      final status = await Permission.locationWhenInUse.request();
      if (!status.isGranted) return null;
      var name = await NetworkInfo().getWifiName();
      if (name == null) return null;
      if (name.length >= 2 && name.startsWith('"') && name.endsWith('"')) {
        name = name.substring(1, name.length - 1);
      }
      if (name.isEmpty || name == '<unknown ssid>' || name == '0x') return null;
      return name;
    } catch (_) {
      return null; // never block setup on this
    }
  }
}

final phoneWifiRepositoryProvider = Provider<PhoneWifiRepository>(
  (ref) => PlatformPhoneWifiRepository(),
);
