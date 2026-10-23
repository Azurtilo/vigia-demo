import unittest

from edge.posture import CalibratedClassifier, ImmobilityRule, features


def landmarks(delta=0):
    p = [
        {"x": 0.0, "y": 0.0, "z": 0.0, "visibility": 1.0, "presence": 1.0}
        for _ in range(33)
    ]
    for i in (11, 12):
        p[i]["y"] = -1.0
    for i in (11, 23, 25, 27):
        p[i]["z"] = delta
    return p


class PoseTests(unittest.TestCase):
    def setUp(self):
        self.refs = {
            label: features(landmarks(d))
            for label, d in [
                ("supina", 0),
                ("lateral-izquierda", 1),
                ("lateral-derecha", -1),
            ]
        }
        self.detector = CalibratedClassifier(self.refs)

    def test_stability_and_labels(self):
        for label, d in [
            ("supina", 0),
            ("lateral-izquierda", 1),
            ("lateral-derecha", -1),
        ]:
            detector = CalibratedClassifier(self.refs)
            self.assertEqual(detector.classify(landmarks(d), 0)[0], "indeterminada")
            for t in (1, 2, 3):
                result = detector.classify(landmarks(d), t)
            self.assertEqual(result[0], label)

    def test_missing_occluded_and_ambiguous_are_not_positions(self):
        self.assertEqual(self.detector.classify([], 0), ("indeterminada", 0))
        p = landmarks()
        p[11]["visibility"] = 0.1
        self.assertIsNone(features(p))
        self.assertEqual(self.detector.classify(landmarks(0.5), 1)[0], "indeterminada")

    def test_gap_resets_stability(self):
        self.detector.classify(landmarks(), 0)
        self.assertEqual(self.detector.classify(landmarks(), 10)[0], "indeterminada")

    def test_missing_signal_never_generates_immobility(self):
        rule = ImmobilityRule(60)
        for t in range(120):
            self.assertEqual(rule.observe("indeterminada", t), "")

    def test_immobility_once_and_reset_on_gap_or_position(self):
        rule = ImmobilityRule(60)
        for t in range(60):
            self.assertEqual(rule.observe("supina", t), "")
        self.assertEqual(rule.observe("supina", 60), "immobility")
        self.assertEqual(rule.observe("supina", 61), "")
        self.assertEqual(rule.observe("supina", 100), "")
        self.assertEqual(rule.observe("lateral-izquierda", 101), "")
