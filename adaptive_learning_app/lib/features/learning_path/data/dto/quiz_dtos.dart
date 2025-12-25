// ignore_for_file: public_member_api_docs, sort_constructors_first

class QuizQuestionDto {
  QuizQuestionDto({required this.id, required this.text, required this.options, this.hint});

  final String id;
  final String text;
  final String? hint;
  final List<QuizOptionDto> options;

  factory QuizQuestionDto.fromJson(Map<String, dynamic> json) {
    return QuizQuestionDto(
      id: json['id'],
      text: json['text'],
      hint: json['hint'] ?? '1', // Map the new field
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
