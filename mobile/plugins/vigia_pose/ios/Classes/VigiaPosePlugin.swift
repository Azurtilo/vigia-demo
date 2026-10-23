import Flutter
import UIKit
import MediaPipeTasksVision

public class VigiaPosePlugin: NSObject, FlutterPlugin {
  private let queue = DispatchQueue(label: "cl.vigia.pose")
  private let modelPath: String?
  private var detector: PoseLandmarker?
  init(modelPath: String?) { self.modelPath = modelPath; super.init() }
  public static func register(with registrar: FlutterPluginRegistrar) {
    let key = registrar.lookupKey(forAsset: "assets/models/pose_landmarker_lite.task")
    let instance = VigiaPosePlugin(modelPath: Bundle.main.path(forResource: key, ofType: nil))
    registrar.addMethodCallDelegate(instance, channel: FlutterMethodChannel(name: "cl.vigia/pose", binaryMessenger: registrar.messenger()))
  }
  public func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    guard call.method == "detect" || call.method == "release" else { result(FlutterMethodNotImplemented); return }
    queue.async {
      if call.method == "release" {
        self.detector = nil
        DispatchQueue.main.async { result(nil) }
        return
      }
      do {
        guard let args = call.arguments as? [String: Any], let path = args["path"] as? String,
              let image = UIImage(contentsOfFile: path), let model = self.modelPath else {
          throw NSError(domain: "VIGIA", code: 1)
        }
        if self.detector == nil {
          let options = PoseLandmarkerOptions()
          options.baseOptions.modelAssetPath = model
          options.runningMode = .image
          options.numPoses = 2
          options.minPoseDetectionConfidence = 0.7
          options.minPosePresenceConfidence = 0.7
          self.detector = try PoseLandmarker(options: options)
        }
        // Normalize EXIF orientation before inference, including portrait capture.
        let normalized = UIGraphicsImageRenderer(size: image.size).image { _ in
          image.draw(in: CGRect(origin: .zero, size: image.size))
        }
        let output = try self.detector!.detect(image: MPImage(uiImage: normalized))
        let poses = output.worldLandmarks.map { pose in pose.map { p in
          ["x": Double(p.x), "y": Double(p.y), "z": Double(p.z),
           "visibility": p.visibility?.doubleValue ?? 0, "presence": p.presence?.doubleValue ?? 0]
        }}
        DispatchQueue.main.async { result(poses) }
      } catch {
        DispatchQueue.main.async { result(FlutterError(code: "POSE_FAILED", message: "No se pudo analizar la imagen local. Revisa modelo y cámara.", details: nil)) }
      }
    }
  }
}
