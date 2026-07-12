class ReferenceSpectrum {
  const ReferenceSpectrum({
    required this.id,
    required this.drugName,
    required this.wavenumberData,
    required this.intensityData,
    required this.createdAt,
    this.manufacturer,
    this.batchReference,
    this.source,
    this.addedBy,
  });

  final int id;
  final String drugName;
  final List<double> wavenumberData;
  final List<double> intensityData;
  final DateTime createdAt;
  final String? manufacturer;
  final String? batchReference;
  final String? source;
  final int? addedBy;

  factory ReferenceSpectrum.fromJson(Map<String, dynamic> j) =>
      ReferenceSpectrum(
        id: j['id'] as int,
        drugName: j['drug_name'] as String,
        wavenumberData: List<double>.from(
          (j['wavenumber_data'] as List).map((e) => (e as num).toDouble()),
        ),
        intensityData: List<double>.from(
          (j['intensity_data'] as List).map((e) => (e as num).toDouble()),
        ),
        createdAt: DateTime.parse(j['created_at'] as String),
        manufacturer: j['manufacturer'] as String?,
        batchReference: j['batch_reference'] as String?,
        source: j['source'] as String?,
        addedBy: j['added_by'] as int?,
      );
}
