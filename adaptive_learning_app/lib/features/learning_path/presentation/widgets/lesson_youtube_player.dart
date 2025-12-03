import 'package:adaptive_learning_app/app/app_context_ext.dart';
import 'package:adaptive_learning_app/features/events/service/tracking_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:youtube_player_flutter/youtube_player_flutter.dart';

class LessonYoutubePlayer extends StatefulWidget {
  const LessonYoutubePlayer({required this.url, super.key});

  final String url;

  @override
  State<LessonYoutubePlayer> createState() => _LessonYoutubePlayerState();
}

class _LessonYoutubePlayerState extends State<LessonYoutubePlayer> {
  late YoutubePlayerController _controller;
  bool _isPlayerReady = false;
  late TrackingService _trackingService;
  PlayerState _lastState = PlayerState.unknown;

  @override
  void initState() {
    super.initState();
    // Access service safely in initState since we aren't using context across async gaps yet
    // Note: context.read is safe here but typically done in didChangeDependencies if inherited widget.
    // However, context.di extension uses read(), which is valid.

    final videoId = YoutubePlayer.convertUrlToId(widget.url);
    if (videoId == null) {
      // Fallback logic could be added here
      return;
    }
    _controller = YoutubePlayerController(initialVideoId: videoId, flags: const YoutubePlayerFlags(autoPlay: false))
      ..addListener(_listener);
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    _trackingService = context.di.services.trackingService;
  }

  void _listener() {
    if (_isPlayerReady && mounted) {
      // 1. Handle State Changes
      final currentState = _controller.value.playerState;
      if (currentState != _lastState) {
        final position = _controller.value.position.inSeconds;
        final meta = {'url': widget.url, 'position_seconds': position};

        if (currentState == PlayerState.playing) {
          _trackingService.log('VIDEO_PLAY', metadata: meta);
        } else if (currentState == PlayerState.paused) {
          _trackingService.log('VIDEO_PAUSE', metadata: meta);
        } else if (currentState == PlayerState.ended) {
          _trackingService.log('VIDEO_COMPLETE', metadata: meta);
        }
        _lastState = currentState;
      }

      // 2. Handle Fullscreen (UI update only)
      if (!_controller.value.isFullScreen) {
        setState(() {});
      }
    }
  }

  @override
  void deactivate() {
    _controller.pause(); // Pauses video while navigating to next page.
    super.deactivate();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Check if URL was valid
    if (YoutubePlayer.convertUrlToId(widget.url) == null) {
      return const Center(
        child: Text('Invalid YouTube URL', style: TextStyle(color: Colors.red)),
      );
    }

    return YoutubePlayerBuilder(
      onExitFullScreen: () {
        // The player forces portraitUp after exiting fullscreen.
        // This ensures the app UI returns to normal.
        SystemChrome.setPreferredOrientations(DeviceOrientation.values);
      },
      player: YoutubePlayer(
        controller: _controller,
        showVideoProgressIndicator: true,
        progressIndicatorColor: Colors.blueAccent,
        onReady: () => _isPlayerReady = true,
      ),
      builder: (context, player) {
        return Column(
          children: [
            AspectRatio(aspectRatio: 16 / 9, child: player),
            // Optional: Add playback controls or info below
          ],
        );
      },
    );
  }
}
