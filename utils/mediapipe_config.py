import os
from utils.logger import logger

def configure_mediapipe():
    """Configure MediaPipe with conservative thread settings for macOS"""
    try:
        # Basic MediaPipe configuration
        os.environ["MEDIAPIPE_CPU_ONLY"] = "1"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        
        # Thread pool configuration
        os.environ["MEDIAPIPE_CPU_THREADS"] = "1"  # Minimum thread count
        os.environ["OMP_NUM_THREADS"] = "1"  # OpenMP threads
        os.environ["MEDIAPIPE_THREAD_STACK_SIZE"] = "131072"  # 128KB stack size
        
        # Resource limits
        os.environ["MEDIAPIPE_USE_MINIMAL_THREADPOOL"] = "true"
        os.environ["MEDIAPIPE_THREAD_PRIORITY"] = "normal"
        
        # Face mesh specific configuration
        os.environ["MEDIAPIPE_FACE_MESH_MODEL_PATH"] = "mediapipe/modules/face_detection/face_detection_front.tflite"
        os.environ["MEDIAPIPE_FACE_MESH_WITH_ATTENTION"] = "true"
        
        logger.info("MediaPipe configured with minimal threading mode and face mesh support")
    except Exception as e:
        logger.error(f"Failed to configure MediaPipe: {str(e)}")
