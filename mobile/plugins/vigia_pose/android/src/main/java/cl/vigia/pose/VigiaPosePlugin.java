package cl.vigia.pose;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.media.ExifInterface;
import android.os.Handler;
import android.os.Looper;
import com.google.mediapipe.framework.image.BitmapImageBuilder;
import com.google.mediapipe.tasks.core.BaseOptions;
import com.google.mediapipe.tasks.vision.core.RunningMode;
import com.google.mediapipe.tasks.vision.poselandmarker.PoseLandmarker;
import io.flutter.embedding.engine.plugins.FlutterPlugin;
import io.flutter.plugin.common.MethodCall;
import io.flutter.plugin.common.MethodChannel;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Serial inference off the UI thread. No network and no persistent frames. */
public class VigiaPosePlugin implements FlutterPlugin, MethodChannel.MethodCallHandler {
    private MethodChannel channel;
    private Context context;
    private String model;
    private PoseLandmarker detector;
    private ExecutorService worker;
    private final Handler main = new Handler(Looper.getMainLooper());
    @Override public void onAttachedToEngine(FlutterPluginBinding binding) {
        context = binding.getApplicationContext();
        model = binding.getFlutterAssets().getAssetFilePathByName("assets/models/pose_landmarker_lite.task");
        worker = Executors.newSingleThreadExecutor();
        channel = new MethodChannel(binding.getBinaryMessenger(), "cl.vigia/pose");
        channel.setMethodCallHandler(this);
    }
    private void release() { if (detector != null) { detector.close(); detector = null; } }
    @Override public void onDetachedFromEngine(FlutterPluginBinding binding) {
        channel.setMethodCallHandler(null);
        worker.execute(this::release);
        worker.shutdown();
    }
    @Override public void onMethodCall(MethodCall call, MethodChannel.Result result) {
        if (!call.method.equals("detect") && !call.method.equals("release")) { result.notImplemented(); return; }
        worker.execute(() -> {
            Bitmap bitmap = null;
            try {
                if (call.method.equals("release")) { release(); main.post(() -> result.success(null)); return; }
                String path = call.argument("path");
                if (path == null) throw new IllegalArgumentException("Missing local image");
                if (detector == null) {
                    detector = PoseLandmarker.createFromOptions(context, PoseLandmarker.PoseLandmarkerOptions.builder()
                        .setBaseOptions(BaseOptions.builder().setModelAssetPath(model).build())
                        .setRunningMode(RunningMode.IMAGE).setNumPoses(2)
                        .setMinPoseDetectionConfidence(0.7f).setMinPosePresenceConfidence(0.7f).build());
                }
                bitmap = BitmapFactory.decodeFile(path);
                if (bitmap == null) throw new IllegalArgumentException("Unreadable image");
                int orientation = new ExifInterface(path).getAttributeInt(ExifInterface.TAG_ORIENTATION, ExifInterface.ORIENTATION_NORMAL);
                Matrix rotation = new Matrix();
                if (orientation == ExifInterface.ORIENTATION_ROTATE_90) rotation.postRotate(90);
                else if (orientation == ExifInterface.ORIENTATION_ROTATE_180) rotation.postRotate(180);
                else if (orientation == ExifInterface.ORIENTATION_ROTATE_270) rotation.postRotate(270);
                else if (orientation != ExifInterface.ORIENTATION_NORMAL && orientation != ExifInterface.ORIENTATION_UNDEFINED)
                    throw new IllegalArgumentException("Mirrored orientation unsupported; use rear camera");
                if (!rotation.isIdentity()) {
                    Bitmap original = bitmap;
                    bitmap = Bitmap.createBitmap(original, 0, 0, original.getWidth(), original.getHeight(), rotation, true);
                    if (bitmap != original) original.recycle();
                }
                List<Object> poses = new ArrayList<>();
                try (var image = new BitmapImageBuilder(bitmap).build()) {
                    var detected = detector.detect(image);
                    for (var pose : detected.worldLandmarks()) {
                        List<Object> points = new ArrayList<>();
                        for (var p : pose) {
                            Map<String, Object> point = new HashMap<>();
                            point.put("x", (double)p.x()); point.put("y", (double)p.y()); point.put("z", (double)p.z());
                            point.put("visibility", (double)p.visibility().orElse(0f));
                            point.put("presence", (double)p.presence().orElse(0f));
                            points.add(point);
                        }
                        poses.add(points);
                    }
                }
                main.post(() -> result.success(poses));
            } catch (Exception e) {
                main.post(() -> result.error("POSE_FAILED", "No se pudo analizar la imagen local. Revisa modelo y cámara.", null));
            } finally { if (bitmap != null && !bitmap.isRecycled()) bitmap.recycle(); }
        });
    }
}
