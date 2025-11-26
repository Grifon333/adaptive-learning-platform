import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';

class LessonWebViewer extends StatefulWidget {
  const LessonWebViewer({required this.url, super.key});

  final String url;

  @override
  State<LessonWebViewer> createState() => _LessonWebViewerState();
}

class _LessonWebViewerState extends State<LessonWebViewer> {
  late final WebViewController _controller;
  bool _isLoading = true;
  double _progress = 0.0;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (_) => setState(() => _isLoading = true),
          onPageFinished: (_) => setState(() => _isLoading = false),
          onProgress: (progress) => setState(() => _progress = progress / 100),
          onWebResourceError: (error) {
            debugPrint('WebView error: ${error.description}');
          },
        ),
      )
      ..loadRequest(Uri.parse(widget.url));
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        if (_isLoading) LinearProgressIndicator(value: _progress),
        Expanded(child: WebViewWidget(controller: _controller)),
      ],
    );
  }
}
