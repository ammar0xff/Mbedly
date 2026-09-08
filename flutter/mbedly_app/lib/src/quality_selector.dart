import 'package:flutter/material.dart';

/// Row of selectable quality chips (144p..mp3). Mirrors the dashboard's
/// quality buttons: the active one is highlighted.
class QualitySelector extends StatelessWidget {
  final List<String> qualities;
  final String selected;
  final ValueChanged<String> onChanged;

  const QualitySelector({
    super.key,
    required this.qualities,
    required this.selected,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 40,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: qualities.length,
        separatorBuilder: (_, __) => const SizedBox(width: 6),
        itemBuilder: (context, i) {
          final q = qualities[i];
          final active = q == selected;
          return ChoiceChip(
            label: Text(q),
            selected: active,
            onSelected: (_) => onChanged(q),
            selectedColor: Theme.of(context).colorScheme.primary,
            labelStyle: TextStyle(
              fontSize: 13,
              color: active
                  ? Theme.of(context).colorScheme.onPrimary
                  : null,
            ),
          );
        },
      ),
    );
  }
}
