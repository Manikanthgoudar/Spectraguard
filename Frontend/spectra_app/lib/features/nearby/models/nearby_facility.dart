/// Represents a real facility fetched from the Overpass API.
enum FacilityType { pharmacy, laboratory, hospital, regulator }

class NearbyFacility {
  const NearbyFacility({
    required this.id,
    required this.name,
    required this.type,
    required this.lat,
    required this.lon,
    required this.distance,
    this.address,
    this.phone,
    this.openingHours,
    this.isOpen,
    this.website,
  });

  final int id;
  final String name;
  final FacilityType type;
  final double lat;
  final double lon;

  /// Distance from user in km.
  final double distance;

  /// Full formatted address (may be null if not in OSM data).
  final String? address;

  /// Phone number from OSM `contact:phone` or `phone` tag.
  final String? phone;

  /// Raw opening_hours string from OSM (e.g. "Mo-Fr 08:00-18:00").
  final String? openingHours;

  /// Parsed open/closed status; null if unknown.
  final bool? isOpen;

  /// Website URL, if present.
  final String? website;

  NearbyFacility copyWith({double? distance}) => NearbyFacility(
        id: id,
        name: name,
        type: type,
        lat: lat,
        lon: lon,
        distance: distance ?? this.distance,
        address: address,
        phone: phone,
        openingHours: openingHours,
        isOpen: isOpen,
        website: website,
      );
}
