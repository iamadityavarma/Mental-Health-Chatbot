# TheraBot Android Deployment Guide

Complete guide for deploying the TheraBot INT8 GGUF model on Android devices.

## 📋 Quick Start Checklist

- [ ] Android Studio installed
- [ ] NDK configured
- [ ] Model file ready (`therabot_int8.gguf`)
- [ ] Target device meets requirements
- [ ] Crisis resources configured for your region

## 🛠️ Step-by-Step Deployment

### 1. Environment Setup

#### Install Android Studio
```bash
# Download from: https://developer.android.com/studio
# Install with default settings including:
# - Android SDK
# - Android SDK Platform-Tools
# - Android SDK Build-Tools
# - Android Emulator
```

#### Configure NDK
```bash
# In Android Studio:
# Tools → SDK Manager → SDK Tools
# Check "NDK (Side by side)" and install
# Note the installation path for later
```

#### Update local.properties
```properties
sdk.dir=/path/to/Android/Sdk
ndk.dir=/path/to/Android/Sdk/ndk/25.2.9519653
```

### 2. Project Setup

#### Clone Repository Structure
```bash
mkdir TheraBot
cd TheraBot
# Copy all Android project files to this directory
```

#### Install llama.cpp
```bash
cd android/app/src/main/cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp
git checkout b3514  # Use stable release
```

#### Add Model File
```bash
# Create assets directory
mkdir -p android/app/src/main/assets

# Copy your trained model
cp models/int8/therabot_int8.gguf android/app/src/main/assets/
```

### 3. Build Configuration

#### Update build.gradle
Ensure these configurations in `app/build.gradle`:

```gradle
android {
    compileSdk 34
    
    defaultConfig {
        minSdk 24  // Android 7.0+
        targetSdk 34
        
        ndk {
            abiFilters 'arm64-v8a', 'armeabi-v7a', 'x86_64'
        }
    }
    
    packagingOptions {
        pickFirst '**/libc++_shared.so'
        pickFirst '**/libllama.so'
    }
}
```

#### Configure CMake
Verify `CMakeLists.txt` has correct optimization flags:

```cmake
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -ffast-math")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O3 -ffast-math")

# Enable ARM NEON optimizations
if(CMAKE_ANDROID_ARCH_ABI STREQUAL "arm64-v8a")
    target_compile_definitions(llama PRIVATE GGML_USE_NEON)
endif()
```

### 4. Model Integration

#### Verify Model File
```bash
# Check model file size and format
ls -lh android/app/src/main/assets/therabot_int8.gguf
file android/app/src/main/assets/therabot_int8.gguf
```

#### Test Model Loading
Add this debug code temporarily in `LlamaModel.kt`:

```kotlin
private suspend fun verifyModelFile(): Boolean {
    val modelFile = File(context.filesDir, MODEL_FILENAME)
    Log.i(TAG, "Model file size: ${modelFile.length()} bytes")
    return modelFile.exists() && modelFile.length() > 0
}
```

### 5. Build Process

#### Clean Build
```bash
cd android
./gradlew clean
```

#### Debug Build
```bash
./gradlew assembleDebug
```

#### Check APK Size
```bash
ls -lh app/build/outputs/apk/debug/
# Should be ~1.5-2GB due to model file
```

### 6. Testing

#### Device Testing
```bash
# Install on connected device
./gradlew installDebug

# Monitor logs
adb logcat | grep TheraBot
```

#### Performance Testing
Monitor these metrics during testing:

```bash
# Memory usage
adb shell dumpsys meminfo com.therabot.app

# CPU usage
adb shell top | grep therabot

# Battery usage
adb shell dumpsys batterystats | grep therabot
```

### 7. Optimization

#### Model Loading Optimization
```kotlin
// In llama_interface.cpp
llama_model_params model_params = llama_model_default_params();
model_params.use_mmap = true;    // Enable memory mapping
model_params.use_mlock = false;  // Don't lock memory on mobile
model_params.n_gpu_layers = 0;   // CPU only
```

#### Memory Management
```kotlin
// In LlamaModel.kt
private fun optimizeForDevice() {
    // Reduce context size for lower-end devices
    val contextSize = when {
        getTotalRAM() < 4 * 1024 * 1024 * 1024 -> 1024  // < 4GB RAM
        getTotalRAM() < 6 * 1024 * 1024 * 1024 -> 1536  // < 6GB RAM
        else -> 2048  // 6GB+ RAM
    }
}
```

### 8. Release Build

#### Configure Signing
Add to `app/build.gradle`:

```gradle
android {
    signingConfigs {
        release {
            storeFile file("path/to/keystore.jks")
            storePassword "your_store_password"
            keyAlias "your_key_alias"
            keyPassword "your_key_password"
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

#### Build Release APK
```bash
./gradlew assembleRelease
```

### 9. Distribution

#### APK Distribution
```bash
# Generate release APK
./gradlew assembleRelease

# APK location
# app/build/outputs/apk/release/app-release.apk
```

#### Split APKs (Optional)
For reduced download size per architecture:

```gradle
android {
    splits {
        abi {
            enable true
            reset()
            include 'arm64-v8a', 'armeabi-v7a', 'x86_64'
            universalApk false
        }
    }
}
```

### 10. Device-Specific Considerations

#### High-End Devices (8GB+ RAM)
```cpp
// Increase context size for better conversations
ctx_params.n_ctx = 4096;
ctx_params.n_threads = 6;
```

#### Mid-Range Devices (4-6GB RAM)
```cpp
// Balanced settings
ctx_params.n_ctx = 2048;
ctx_params.n_threads = 4;
```

#### Low-End Devices (3-4GB RAM)
```cpp
// Conservative settings
ctx_params.n_ctx = 1024;
ctx_params.n_threads = 2;
```

## 🔧 Troubleshooting

### Common Issues

#### Model Loading Fails
```
Error: Failed to load model from: /data/data/.../therabot_int8.gguf

Solutions:
1. Check model file exists in assets/
2. Verify file is not corrupted
3. Ensure sufficient storage space
4. Check file permissions
```

#### Out of Memory During Inference
```
Error: OutOfMemoryError

Solutions:
1. Reduce n_ctx parameter
2. Lower thread count
3. Clear other apps before use
4. Use device with more RAM
```

#### Slow Response Generation
```
Issue: Responses take >30 seconds

Solutions:
1. Reduce max_tokens in generation
2. Optimize thread count for device
3. Check CPU throttling
4. Ensure device isn't overheating
```

#### Native Library Loading Issues
```
Error: UnsatisfiedLinkError

Solutions:
1. Rebuild native libraries
2. Check NDK version compatibility
3. Verify ABI filters in build.gradle
4. Clean and rebuild project
```

### Performance Optimization

#### Memory Usage
```bash
# Monitor memory during app usage
adb shell dumpsys meminfo com.therabot.app

# Target memory usage:
# - Model loading: <2GB
# - Idle: <500MB
# - During inference: <1GB additional
```

#### Battery Optimization
```kotlin
// In AndroidManifest.xml
<uses-permission android:name="android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS" />

// Request battery optimization exemption for better performance
```

## 📱 Device Testing Matrix

### Test Configurations

| Device Type | RAM | CPU | Expected Performance |
|-------------|-----|-----|---------------------|
| Flagship | 8GB+ | Snapdragon 8xx | <3s response |
| Mid-range | 6GB | Snapdragon 7xx | <5s response |
| Budget | 4GB | Snapdragon 6xx | <10s response |
| Minimum | 3GB | Snapdragon 4xx | <15s response |

### Test Scenarios
1. **Cold Start**: App launch + model loading
2. **First Response**: Initial message response time
3. **Continuous Chat**: 10+ message conversation
4. **Memory Pressure**: With other apps running
5. **Battery Drain**: Extended usage monitoring

## 🚀 Production Deployment

### Pre-Release Checklist
- [ ] Crisis detection thoroughly tested
- [ ] Model responses reviewed for appropriateness
- [ ] Performance tested on target devices
- [ ] Battery usage optimized
- [ ] Privacy compliance verified
- [ ] Emergency contacts updated for target region
- [ ] Crash reporting implemented (optional)

### App Store Preparation
- [ ] Screenshots prepared
- [ ] App description emphasizes privacy and on-device processing
- [ ] Medical disclaimer included
- [ ] Age rating set appropriately
- [ ] Keywords optimized for mental health apps

### Post-Deployment Monitoring
- Monitor user feedback for response quality
- Track crash reports and performance issues
- Monitor battery usage complaints
- Gather feedback on crisis detection accuracy

## 🔒 Privacy & Compliance

### Data Handling
- All processing happens on-device
- No network requests for model inference
- Chat history stored locally only
- User controls data deletion

### Medical Compliance
- Clear disclaimers about not replacing professional care
- Crisis resources prominently displayed
- Appropriate age restrictions
- Regular review of therapy responses

This deployment guide ensures a successful rollout of TheraBot while maintaining the highest standards for privacy, safety, and user experience.