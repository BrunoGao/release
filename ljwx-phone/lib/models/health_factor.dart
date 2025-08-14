class HealthFactor {
  final String name;
  final double score;
  final String status;
  final double weight;
  final String unit;
  final double currentValue;
  final List<double> normalRange;

  HealthFactor({
    required this.name,
    required this.score,
    required this.status,
    required this.weight,
    required this.unit,
    required this.currentValue,
    required this.normalRange,
  });

  factory HealthFactor.fromJson(Map<String, dynamic> json) {
    return HealthFactor(
      name: json['name'] as String? ?? '',
      score: ((json['score'] as num?) ?? 0).toDouble(),
      status: json['status'] as String? ?? '',
      weight: ((json['weight'] as num?) ?? 0).toDouble(),
      unit: json['unit'] as String? ?? '',
      currentValue: ((json['currentValue'] as num?) ?? 0).toDouble(),
      normalRange: ((json['normalRange'] as List?) ?? [])
          .map((e) => (e as num).toDouble())
          .toList(),
    );
  }
} 