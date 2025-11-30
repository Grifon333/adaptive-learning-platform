import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';

class LessonMarkdownViewer extends StatefulWidget {
  const LessonMarkdownViewer({required this.url, super.key});

  final String url;

  @override
  State<LessonMarkdownViewer> createState() => _LessonMarkdownViewerState();
}

class _LessonMarkdownViewerState extends State<LessonMarkdownViewer> {
  String? _content;
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _fetchContent();
  }

  Future<void> _fetchContent() async {
    try {
      // Use Dio directly or via DI. For a simple GET string, a fresh instance is fine here
      // or use context.read<DiContainer>().httpClient but cast response.
      final response = await Dio().get<String>(widget.url, options: Options(responseType: ResponseType.plain));

      if (mounted) {
        setState(() {
          _content = response.data;
          _isLoading = false;
        });
      }
    } on Object catch (e) {
      if (mounted) {
        setState(() {
          _error = 'Failed to load content: $e';
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) return const Center(child: CircularProgressIndicator());

    if (_error != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 16),
            Text(_error!, textAlign: TextAlign.center),
            TextButton(onPressed: _fetchContent, child: const Text('Retry')),
          ],
        ),
      );
    }

    return Markdown(
      data: _content ?? '',
      selectable: true,
      styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
        p: const TextStyle(fontSize: 16, height: 1.5),
        h1: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
        code: const TextStyle(backgroundColor: Color(0xFFEEEEEE), fontFamily: 'monospace'),
      ),
    );
  }
}
