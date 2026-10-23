import 'package:flutter_test/flutter_test.dart';
import 'package:vigia_mobile/pose_classifier.dart';

void main() {
  test('Missing or multiple people never produce a posture', () {
    expect(poseFeatures([]), isNull);
    expect(poseFeatures([[], []]), isNull);
  });
  test('Ambiguous references and invalid geometry stay indeterminate', () {
    final point = List.filled(24, 0.0);
    final same = {for (final label in poseLabels) label: point};
    expect(classifyPose(point, same).posture, 'indeterminada');
    expect(
      classifyPose(List.filled(24, double.nan), same).posture,
      'indeterminada',
    );
    expect(classifyPose(point, {}).posture, 'indeterminada');
  });
  test(
    'Separated calibrated references discriminate while distant frames do not',
    () {
      final refs = {
        'supina': List.filled(24, 0.0),
        'lateral-izquierda': List.filled(24, 1.0),
        'lateral-derecha': List.filled(24, -1.0),
      };
      expect(
        classifyPose(List.filled(24, 1.0), refs).posture,
        'lateral-izquierda',
      );
      expect(classifyPose(List.filled(24, 4.0), refs).posture, 'indeterminada');
    },
  );
  test(
    'Low visibility or nonfinite coordinates invalidate a detected body',
    () {
      final points = List.generate(
        33,
        (_) => <String, num>{
          'x': 0,
          'y': 0,
          'z': 0,
          'visibility': 1,
          'presence': 1,
        },
      );
      points[11]['y'] = 1;
      points[12]['y'] = 1;
      expect(poseFeatures([points]), hasLength(24));
      points[11]['visibility'] = .2;
      expect(poseFeatures([points]), isNull);
      points[11]['visibility'] = 1;
      points[23]['x'] = double.infinity;
      expect(poseFeatures([points]), isNull);
    },
  );
}
