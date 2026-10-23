Pod::Spec.new do |s|
  s.name = 'vigia_pose'
  s.version = '0.1.0'
  s.summary = 'Local VIGIA pose inference'
  s.description = 'MediaPipe IMAGE inference via a Flutter method channel.'
  s.homepage = 'https://developers.google.com/edge/mediapipe/solutions/vision/pose_landmarker/ios'
  s.license = { :type => 'Proprietary' }
  s.author = { 'VIGIA' => 'development@example.invalid' }
  s.source = { :path => '.' }
  s.source_files = 'Classes/**/*'
  s.dependency 'Flutter'
  s.dependency 'MediaPipeTasksVision', '0.10.21'
  s.platform = :ios, '15.0'
  s.swift_version = '5.0'
  s.static_framework = true
  s.pod_target_xcconfig = { 'DEFINES_MODULE' => 'YES', 'EXCLUDED_ARCHS[sdk=iphonesimulator*]' => 'i386' }
end
