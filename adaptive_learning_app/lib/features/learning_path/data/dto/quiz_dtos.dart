// ignore_for_file: public_member_api_docs, sort_constructors_first

class QuizQuestionDto {
  QuizQuestionDto({required this.id, required this.text, required this.options});

  final String id;
  final String text;
  final List<QuizOptionDto> options;

  factory QuizQuestionDto.fromJson(Map<String, dynamic> json) {
    return QuizQuestionDto(
      id: json['id'],
      text: json['text'],
      options: (json['options'] as List).map((e) => QuizOptionDto.fromJson(e)).toList(),
    );
  }
}

class QuizOptionDto {
  QuizOptionDto({required this.text, required this.isCorrect});

  final String text;
  final bool isCorrect;

  factory QuizOptionDto.fromJson(Map<String, dynamic> json) {
    return QuizOptionDto(text: json['text'], isCorrect: json['is_correct']);
  }
}
