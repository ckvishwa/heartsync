/// An event in `couples/{coupleId}/events`. See docs/protocol.md.
/// Used from Phase 3, when the app starts listening to the partner's events.
enum CoupleEventType { heart, touch, art, mood, voice }

class CoupleEvent {
  const CoupleEvent({
    required this.id,
    required this.type,
    required this.from,
    required this.payload,
    this.createdAt,
  });

  final String id;
  final CoupleEventType type;
  final String from;
  final Map<String, Object?> payload;
  final DateTime? createdAt;

  /// Returns null for an unknown type, so newer event types do not crash
  /// older app versions.
  static CoupleEventType? typeFromName(String? name) {
    for (final type in CoupleEventType.values) {
      if (type.name == name) return type;
    }
    return null;
  }
}
