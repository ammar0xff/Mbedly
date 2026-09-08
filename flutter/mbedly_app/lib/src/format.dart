/// Small formatting helpers - the Dart mirror of the dashboard's format helpers.
library;

String formatBytes(num bytes) {
  if (bytes <= 0) return '0 B';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  var value = bytes.toDouble();
  var u = 0;
  while (value >= 1024 && u < units.length - 1) {
    value /= 1024;
    u++;
  }
  final s = value >= 100 ? value.toStringAsFixed(0) : value.toStringAsFixed(1);
  return '$s ${units[u]}';
}
