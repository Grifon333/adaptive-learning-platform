// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'package:flutter/foundation.dart';

@immutable
class AdminResourceDto {
  const AdminResourceDto({
    required this.id,
    required this.title,
    required this.type,
    required this.url,
    required this.duration,
  });

  final String id;
  final String title;
  final String type; // 'Video', 'Article', etc.
  final String url;
  final int duration;

  factory AdminResourceDto.fromJson(Map<String, dynamic> json) {
    return AdminResourceDto(
      id: json['id'] as String,
      title: json['title'] as String,
      type: json['type'] as String,
      url: json['url'] as String,
      duration: (json['duration'] as num).toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        'title': title,
        'type': type,
        'url': url,
        'duration': duration,
      };
}
