"""
Face Recognition Configuration
Adjust these settings to improve accuracy based on your specific use case.
"""

# Detection Model Configuration
# "hog" - Faster, works on CPU, less accurate
# "cnn" - Slower, requires GPU, more accurate
FACE_DETECTION_MODEL = "hog"  # Changed from "cnn" to "hog"

# Tolerance Settings (Lower = More Strict = Higher Accuracy)
# 0.3 - Very strict (high accuracy, may miss some matches)
# 0.4 - Strict (good balance of accuracy and recall)
# 0.5 - Moderate (more matches, some false positives)
# 0.6 - Loose (many matches, more false positives) - RECOMMENDED for better matching
FACE_RECOGNITION_TOLERANCE = 0.8  # Very lenient for better matching

# Face Size Constraints (Very relaxed for event photos)
MIN_FACE_SIZE = 20          # Minimum face size in pixels (very small for distant faces)
MAX_FACE_SIZE = 1000        # Maximum face size in pixels
MIN_FACE_RATIO = 0.001      # Minimum face area as ratio of image (0.1% - very small)
MAX_FACE_RATIO = 0.9        # Maximum face area as ratio of image (90%)

# Face Quality Constraints
MIN_ASPECT_RATIO = 0.7      # Minimum width/height ratio for valid face
MAX_ASPECT_RATIO = 1.4      # Maximum width/height ratio for valid face

# Detection Parameters (Balanced for stability)
FACE_DETECTION_UPSAMPLES = 1    # Number of times to upsample for detection (stable)
MAX_IMAGE_DIMENSION = 1000  # Reduced from 1800 to 1000

# Matching Algorithm
USE_MULTIPLE_METRICS = True     # Use both Euclidean and cosine distance
REQUIRE_BUILTIN_MATCH = True    # Require face_recognition.compare_faces to agree

# Logging Level
FACE_RECOGNITION_LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# Performance Settings
ENABLE_IMAGE_PREPROCESSING = True    # Enable image preprocessing for better detection
ENABLE_FACE_QUALITY_CHECK = True     # Enable face quality validation

# Accuracy Profiles
ACCURACY_PROFILES = {
    "high_accuracy": {
        "tolerance": 0.3,
        "min_face_size": 100,
        "min_face_ratio": 0.02,
        "upsamples": 2,
        "model": "cnn"  # Requires GPU
    },
    "balanced": {
        "tolerance": 0.6,  # Increased for better matching
        "min_face_size": 30,
        "min_face_ratio": 0.003,
        "upsamples": 2,
        "model": "hog"
    },
    "high_recall": {
        "tolerance": 0.5,
        "min_face_size": 25,
        "min_face_ratio": 0.002,
        "upsamples": 2,
        "model": "hog"
    }
}

# Current profile
CURRENT_PROFILE = "balanced"

def apply_profile(profile_name: str):
    """Apply a predefined accuracy profile."""
    global FACE_RECOGNITION_TOLERANCE, MIN_FACE_SIZE, MIN_FACE_RATIO
    global FACE_DETECTION_UPSAMPLES, FACE_DETECTION_MODEL
    
    if profile_name not in ACCURACY_PROFILES:
        raise ValueError(f"Unknown profile: {profile_name}")
    
    profile = ACCURACY_PROFILES[profile_name]
    
    FACE_RECOGNITION_TOLERANCE = profile["tolerance"]
    MIN_FACE_SIZE = profile["min_face_size"]
    MIN_FACE_RATIO = profile["min_face_ratio"]
    FACE_DETECTION_UPSAMPLES = profile["upsamples"]
    FACE_DETECTION_MODEL = profile["model"]
    
    print(f"Applied face recognition profile: {profile_name}")
    print(f"  Tolerance: {FACE_RECOGNITION_TOLERANCE}")
    print(f"  Min face size: {MIN_FACE_SIZE}")
    print(f"  Model: {FACE_DETECTION_MODEL}")

def get_current_config():
    """Get current configuration as dictionary."""
    return {
        "model": FACE_DETECTION_MODEL,
        "tolerance": FACE_RECOGNITION_TOLERANCE,
        "min_face_size": MIN_FACE_SIZE,
        "max_face_size": MAX_FACE_SIZE,
        "min_face_ratio": MIN_FACE_RATIO,
        "max_face_ratio": MAX_FACE_RATIO,
        "upsamples": FACE_DETECTION_UPSAMPLES,
        "max_image_dimension": MAX_IMAGE_DIMENSION
    }

# Apply default profile
if CURRENT_PROFILE in ACCURACY_PROFILES:
    apply_profile(CURRENT_PROFILE)

