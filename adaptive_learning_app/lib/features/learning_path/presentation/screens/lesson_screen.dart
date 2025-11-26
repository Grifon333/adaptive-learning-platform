import 'package:adaptive_learning_app/features/learning_path/data/dto/learning_path_dtos.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/widgets/lesson_web_viewer.dart';
import 'package:adaptive_learning_app/features/learning_path/presentation/widgets/lesson_youtube_player.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class LessonScreen extends StatefulWidget {
  const LessonScreen({required this.step, super.key});

  final LearningStepDto step;

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  ResourceDto? _selectedResource;

  @override
  void initState() {
    super.initState();
    if (widget.step.resources.isNotEmpty) _selectedResource = widget.step.resources.first;
  }

  void _selectResource(ResourceDto recource) {
    setState(() => _selectedResource = recource);
  }

  Future<void> _takeQuiz() async {
    final result = await context.pushNamed(
      'quiz',
      extra: {'stepId': widget.step.id, 'conceptId': widget.step.conceptId},
    );
    if (result == true && mounted) context.pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Step ${widget.step.stepNumber}')),
      body: LayoutBuilder(
        builder: (context, constraints) {
          final double totalHeight = constraints.maxHeight;
          final double bottomSheetHeight = totalHeight * 0.4;
          final double contentHeight = (totalHeight * 0.6) + 20;
          return Stack(
            children: [
              Positioned(
                top: 0,
                left: 0,
                right: 0,
                height: contentHeight,
                child: ColoredBox(
                  color: Colors.black12,
                  child: _ContentArea(resource: _selectedResource),
                ),
              ),
              Positioned(
                bottom: 0,
                left: 0,
                right: 0,
                height: bottomSheetHeight,
                child: _MaterialsSheet(
                  resources: widget.step.resources,
                  selectedResource: _selectedResource,
                  selectResource: _selectResource,
                  takeQuiz: _takeQuiz,
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _MaterialsSheet extends StatelessWidget {
  const _MaterialsSheet({
    required this.resources,
    required this.selectResource,
    required this.takeQuiz,
    this.selectedResource,
  });

  final List<ResourceDto> resources;
  final ResourceDto? selectedResource;
  final Function(ResourceDto resource) selectResource;
  final Function() takeQuiz;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [BoxShadow(blurRadius: 10, color: Colors.black12)],
      ),
      child: Column(
        children: [
          const SizedBox(height: 12),
          DecoratedBox(
            decoration: BoxDecoration(color: Colors.grey.shade300, borderRadius: BorderRadius.circular(2)),
            child: SizedBox(width: 40, height: 4),
          ),
          const Padding(
            padding: EdgeInsets.all(16),
            child: Text('Materials', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          ),
          Expanded(
            child: ListView.separated(
              itemBuilder: (context, index) {
                final resource = resources[index];
                final isSelected = resource == selectedResource;
                return _ResourceListItem(
                  resource: resource,
                  isSelected: isSelected,
                  onTap: () => selectResource(resource),
                );
              },
              separatorBuilder: (_, _) => const SizedBox(height: 8),
              itemCount: resources.length,
              padding: const EdgeInsets.symmetric(horizontal: 16),
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(16),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: takeQuiz,
                icon: const Icon(Icons.quiz),
                label: const Text('Take Quiz'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                  backgroundColor: Theme.of(context).primaryColor,
                  foregroundColor: Colors.white,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ContentArea extends StatelessWidget {
  const _ContentArea({this.resource});

  final ResourceDto? resource;

  @override
  Widget build(BuildContext context) {
    if (resource == null) return const Center(child: Text('No content selected'));
    // Simple logic to determine type.
    // Ideally, this should be an enum from the DTO.
    final url = resource!.url;
    final isVideo = resource!.type.toLowerCase().contains('video') || url.contains('youtube');
    return isVideo ? LessonYoutubePlayer(key: ValueKey(url), url: url) : LessonWebViewer(key: ValueKey(url), url: url);
  }
}

class _ResourceListItem extends StatelessWidget {
  const _ResourceListItem({required this.resource, required this.isSelected, required this.onTap});

  final ResourceDto resource;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final isVideo = resource.type.toLowerCase().contains('video');

    return Material(
      color: isSelected ? Colors.blue.shade50 : Colors.grey.shade50,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: isVideo ? Colors.red.shade100 : Colors.blue.shade100,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  isVideo ? Icons.play_arrow : Icons.article,
                  color: isVideo ? Colors.red : Colors.blue,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      resource.title,
                      style: TextStyle(
                        fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                        color: isSelected ? Colors.blue.shade900 : Colors.black87,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    Text('${resource.duration} min', style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                  ],
                ),
              ),
              if (isSelected) const Icon(Icons.bar_chart, color: Colors.blue),
            ],
          ),
        ),
      ),
    );
  }
}
