import 'package:flutter/services.dart';

class VigiaPose {
  static const _channel = MethodChannel('cl.vigia/pose');
  static Future<List<dynamic>> detect(String imagePath) async =>
      await _channel.invokeListMethod<dynamic>('detect', {'path': imagePath}) ??
      [];
  static Future<void> release() => _channel.invokeMethod<void>('release');
}
