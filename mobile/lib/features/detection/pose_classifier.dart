import 'dart:math';

const poseLabels = ['supina', 'lateral-izquierda', 'lateral-derecha'];
const bodyIndices = [11, 12, 23, 24, 25, 26, 27, 28];

/// Local geometry only; score is similarity, not clinical probability.
List<double>? poseFeatures(List<dynamic> poses) {
  if (poses.length != 1 || (poses.first as List).length != 33) return null;
  final points = bodyIndices
      .map((i) => Map<String, dynamic>.from(poses.first[i] as Map))
      .toList();
  for (final p in points) {
    if ([
      'x',
      'y',
      'z',
      'visibility',
      'presence',
    ].any((k) => p[k] is! num || !(p[k] as num).isFinite)) {
      return null;
    }
    if ((p['visibility'] as num) < .7 || (p['presence'] as num) < .7) {
      return null;
    }
  }
  final center = [
    for (final k in ['x', 'y', 'z'])
      ((points[2][k] as num) + (points[3][k] as num)) / 2,
  ];
  final shoulder = [
    for (final k in ['x', 'y', 'z'])
      ((points[0][k] as num) + (points[1][k] as num)) / 2,
  ];
  final scale = sqrt(
    List.generate(
      3,
      (i) => pow(center[i] - shoulder[i], 2),
    ).reduce((a, b) => a + b),
  );
  if (scale < .05) return null;
  return [
    for (final p in points)
      for (int i = 0; i < 3; i++)
        ((p[['x', 'y', 'z'][i]] as num) - center[i]) / scale,
  ];
}

({String posture, double score}) classifyPose(
  List<double>? frame,
  Map<String, List<double>> references,
) {
  if (frame == null ||
      frame.length != 24 ||
      frame.any((v) => !v.isFinite) ||
      poseLabels.any(
        (label) =>
            references[label]?.length != 24 ||
            references[label]!.any((v) => !v.isFinite),
      )) {
    return (posture: 'indeterminada', score: 0);
  }
  final distances =
      poseLabels
          .map(
            (label) => (
              label: label,
              distance: sqrt(
                List.generate(
                      24,
                      (i) => pow(frame[i] - references[label]![i], 2),
                    ).reduce((a, b) => a + b) /
                    24,
              ),
            ),
          )
          .toList()
        ..sort((a, b) => a.distance.compareTo(b.distance));
  final best = distances.first;
  if (best.distance > .35 || distances[1].distance - best.distance < .08) {
    return (posture: 'indeterminada', score: 0);
  }
  return (
    posture: best.label,
    score: (1 - best.distance / .35).clamp(0, 1).toDouble(),
  );
}
