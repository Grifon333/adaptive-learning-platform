// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class AdminConceptDto {
  const AdminConceptDto({
    required this.id,
    required this.name,
    this.description,
    this.difficulty = 1.0,
    this.estimatedTime = 30,
  });

  final String id;
  final String name;
  final String? description;
  final double difficulty;
  final int estimatedTime;

  factory AdminConceptDto.fromJson(Map<String, dynamic> json) {
    return AdminConceptDto(
      id: json['id'] as String,
      name: json['name'] as String,
      description: json['description'] as String?,
      difficulty: (json['difficulty'] as num).toDouble(),
      estimatedTime: (json['estimated_time'] as num).toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
    'name': name,
    'description': description,
    'difficulty': difficulty,
    'estimated_time': estimatedTime,
  };
}

@immutable
class CreateRelationshipDto {
  const CreateRelationshipDto({required this.startId, required this.endId, this.type = 'PREREQUISITE'});

  final String startId;
  final String endId;
  final String type;

  Map<String, dynamic> toJson() => {'start_concept_id': startId, 'end_concept_id': endId, 'type': type};
}
