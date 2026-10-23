"""Load the official model and infer on an empty synthetic frame, no camera."""
import argparse
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    args = parser.parse_args()
    options = vision.PoseLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=args.model, delegate=python.BaseOptions.Delegate.CPU))
    with vision.PoseLandmarker.create_from_options(options) as detector:
        result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.zeros((256,256,3), dtype=np.uint8)))
        assert len(result.pose_landmarks) == 0
        print(f'MediaPipe {mp.__version__}: modelo cargado, imagen vacía sin falsas personas.')


if __name__ == '__main__':
    main()
