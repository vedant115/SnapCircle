"""
Face recognition utilities for SnapCircle.
Handles face detection, embedding generation, and face matching.
"""

import face_recognition
import numpy as np
import cv2
from PIL import Image
from typing import List, Tuple, Optional, Dict, Any
import logging
from sqlalchemy.orm import Session
from sqlalchemy import text
import requests
import io
import os
import tempfile
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configuration
try:
    from face_recognition_config import (
        FACE_RECOGNITION_TOLERANCE,
        MIN_FACE_SIZE,
        MAX_FACE_SIZE,
        MIN_FACE_RATIO,
        MAX_FACE_RATIO,
        MAX_IMAGE_DIMENSION
    )
except ImportError:
    # Fallback configuration if config file not found
    FACE_RECOGNITION_TOLERANCE = 0.6
    MIN_FACE_SIZE = 80
    MAX_FACE_SIZE = 1000
    MIN_FACE_RATIO = 0.01
    MAX_FACE_RATIO = 0.8
    MIN_ASPECT_RATIO = 0.7
    MAX_ASPECT_RATIO = 1.4
    MAX_IMAGE_DIMENSION = 1200


class FaceRecognitionError(Exception):
    """Custom exception for face recognition errors."""
    pass


def get_image_for_processing(image_path: str) -> str:
    """
    Get a local file path for image processing.
    Downloads S3 images to temporary files if needed.

    Args:
        image_path: Local file path or S3 URL

    Returns:
        Local file path that can be used for face recognition
    """
    # Check if it's a URL (S3)
    if image_path.startswith('http'):
        try:
            # Download the image from S3 URL to a temporary file
            response = requests.get(image_path, timeout=30)
            response.raise_for_status()

            # Create temporary file with appropriate extension
            parsed_url = urlparse(image_path)
            file_extension = os.path.splitext(parsed_url.path)[1] or '.jpg'

            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=file_extension,
                prefix='face_processing_'
            )

            # Write image data to temporary file
            temp_file.write(response.content)
            temp_file.close()

            logger.info(f"Downloaded S3 image to temporary file: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            logger.error(f"Failed to download S3 image {image_path}: {e}")
            raise FaceRecognitionError(f"Cannot access image for processing: {e}")

    # For local files, return as-is
    if not os.path.exists(image_path):
        raise FaceRecognitionError(f"Local image file not found: {image_path}")

    return image_path


def cleanup_temp_file(file_path: str):
    """Clean up temporary file if it was created for S3 processing."""
    if file_path.startswith(tempfile.gettempdir()) and 'face_processing_' in file_path:
        try:
            os.unlink(file_path)
            logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {file_path}: {e}")


def preprocess_image_for_face_detection(image_path: str) -> np.ndarray:
    """
    Preprocess image for better face detection.

    Args:
        image_path: Path to the image file

    Returns:
        Preprocessed image as numpy array
    """
    local_path = None
    try:
        # Get local file path (downloads S3 images if needed)
        local_path = get_image_for_processing(image_path)

        # Load image with PIL for better control
        pil_image = Image.open(local_path)

        # Auto-rotate image based on EXIF orientation
        try:
            exif = pil_image._getexif()
            if exif is not None:
                orientation_key = 274  # EXIF orientation tag
                if orientation_key in exif:
                    orientation = exif[orientation_key]
                    # Apply rotation based on EXIF orientation
                    if orientation == 2:
                        pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT)
                    elif orientation == 3:
                        pil_image = pil_image.transpose(Image.ROTATE_180)
                    elif orientation == 4:
                        pil_image = pil_image.transpose(Image.FLIP_TOP_BOTTOM)
                    elif orientation == 5:
                        pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
                    elif orientation == 6:
                        pil_image = pil_image.transpose(Image.ROTATE_270)
                    elif orientation == 7:
                        pil_image = pil_image.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
                    elif orientation == 8:
                        pil_image = pil_image.transpose(Image.ROTATE_90)
                    logger.info(f"Applied EXIF orientation correction: {orientation}")
        except Exception as e:
            logger.warning(f"Error applying EXIF orientation: {e}")

        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')

        # Resize if image is too large (for performance and accuracy)
        width, height = pil_image.size
        # Reduced MAX_IMAGE_DIMENSION from 1800 to 1000 for better performance
        max_dimension = 1000  # Reduced from original MAX_IMAGE_DIMENSION
        if max(width, height) > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int((height * max_dimension) / width)
            else:
                new_height = max_dimension
                new_width = int((width * max_dimension) / height)
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")

        # Convert to numpy array
        image = np.array(pil_image)

        return image

    except Exception as e:
        logger.error(f"Error preprocessing image {image_path}: {e}")
        # Fallback to original method
        try:
            if local_path and local_path != image_path:
                # For S3 images, we need to use the local path for fallback too
                result = face_recognition.load_image_file(local_path)
            else:
                result = face_recognition.load_image_file(image_path)
            return result
        except Exception as fallback_error:
            logger.error(f"Fallback also failed: {fallback_error}")
            raise FaceRecognitionError(f"Cannot process image: {e}")
    finally:
        # Clean up temporary file if it was created
        if local_path and local_path != image_path:
            cleanup_temp_file(local_path)


def detect_faces_in_image(image_path: str) -> List[Dict[str, Any]]:
    """
    Detect faces in an image and return face data.

    Args:
        image_path: Path to the image file or S3 URL

    Returns:
        List of dictionaries containing face data:
        [
            {
                "face_index": 0,
                "embedding": np.array,
                "bounding_box": (top, right, bottom, left),
                "confidence": float
            }
        ]
    """
    try:
        # Preprocess image for better detection
        image = preprocess_image_for_face_detection(image_path)

        # Use HOG model for faster detection
        logger.info(f"Detecting faces in {image_path}")
        face_locations = face_recognition.face_locations(
            image,
            number_of_times_to_upsample=1,
            model="hog"  # Changed from "cnn" to "hog" for faster processing
        )

        if not face_locations:
            logger.warning(f"No faces detected in {image_path}")
            return []

        logger.info(f"Detected {len(face_locations)} faces in {image_path}")
        
        # Generate face encodings
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        faces_data = []
        for i, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
            top, right, bottom, left = face_location

            # Check face size constraints
            face_width = right - left
            face_height = bottom - top

            # Temporarily commented out face size validation to avoid discarding valid faces
            # if face_width < MIN_FACE_SIZE or face_height < MIN_FACE_SIZE:
            #     logger.warning(f"Face {i} too small ({face_width}x{face_height}), skipping")
            #     continue

            # if face_width > MAX_FACE_SIZE or face_height > MAX_FACE_SIZE:
            #     logger.warning(f"Face {i} too large ({face_width}x{face_height}), skipping")
            #     continue

            # Check face aspect ratio (relaxed for group photos)
            aspect_ratio = face_width / face_height
            # Temporarily commented out aspect ratio validation
            # if aspect_ratio < 0.5 or aspect_ratio > 2.0:  # More relaxed than MIN/MAX_ASPECT_RATIO
            #     logger.warning(f"Face {i} has unusual aspect ratio ({aspect_ratio:.2f}), skipping")
            #     continue

            # Calculate face quality score based on size and position
            face_area = face_width * face_height
            image_area = image.shape[0] * image.shape[1]
            face_ratio = face_area / image_area

            # Temporarily commented out face ratio validation
            # Face should be within acceptable size ratio range
            # if face_ratio < MIN_FACE_RATIO or face_ratio > MAX_FACE_RATIO:
            #     logger.warning(f"Face {i} has unusual size ratio ({face_ratio:.3f}), skipping")
            #     continue

            # Calculate confidence based on face quality metrics
            confidence = min(1.0, face_ratio * 10)  # Higher confidence for larger faces

            # Convert bounding box to PostgreSQL box format: (x1,y1),(x2,y2)
            # Note: face_recognition returns (top, right, bottom, left)
            # PostgreSQL box expects (x1,y1),(x2,y2) where (x1,y1) is bottom-left
            bounding_box = f"({left},{bottom}),({right},{top})"

            faces_data.append({
                "face_index": i,
                "embedding": face_encoding,
                "bounding_box": bounding_box,
                "confidence": confidence,
                "face_size": (face_width, face_height),
                "face_ratio": face_ratio
            })

            logger.info(f"Valid face {i}: size={face_width}x{face_height}, ratio={face_ratio:.3f}, confidence={confidence:.2f}")
        
        logger.info(f"Detected {len(faces_data)} valid faces in {image_path}")
        return faces_data
        
    except Exception as e:
        logger.error(f"Error detecting faces in {image_path}: {e}")
        raise FaceRecognitionError(f"Failed to detect faces: {e}")


def generate_face_embedding(image_path: str) -> Optional[np.ndarray]:
    """
    Generate face embedding for a single face image (like a selfie).

    Args:
        image_path: Path to the image file or S3 URL

    Returns:
        Face embedding as numpy array, or None if no face detected
    """
    try:
        faces_data = detect_faces_in_image(image_path)

        if not faces_data:
            logger.warning(f"No faces detected for embedding generation in {image_path}")
            return None

        if len(faces_data) > 1:
            # Sort by confidence and use the best face
            faces_data.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            logger.info(f"Multiple faces detected in {image_path}, using the highest confidence face")

        best_face = faces_data[0]
        logger.info(f"Generated embedding for face with confidence {best_face.get('confidence', 0):.2f}")

        return best_face["embedding"]

    except Exception as e:
        logger.error(f"Error generating face embedding for {image_path}: {e}")
        raise FaceRecognitionError(f"Failed to generate face embedding: {e}")


def find_matching_users(face_embedding: np.ndarray, db: Session, threshold: float = FACE_RECOGNITION_TOLERANCE, event_id: Optional[int] = None) -> List[Tuple[int, float]]:
    """
    Find users with similar face embeddings using improved matching algorithm.
    Optionally limit search to users registered for a specific event.

    Args:
        face_embedding: Face embedding to match against
        db: Database session
        threshold: Similarity threshold (lower is more strict)
        event_id: Optional event ID to limit search to registered users only

    Returns:
        List of tuples (user_id, distance) sorted by similarity
    """
    try:
        from models.user import User
        from models.event_registration import EventRegistration

        # Build query based on whether event filtering is requested
        if event_id:
            # Optimized: Only get users registered for this specific event
            users_with_embeddings = db.query(User).join(
                EventRegistration, User.id == EventRegistration.user_id
            ).filter(
                EventRegistration.event_id == event_id,
                User.embedding.isnot(None)
            ).all()

            # Also get total users for comparison
            total_users_with_embeddings = db.query(User).filter(User.embedding.isnot(None)).count()

            logger.info(f"🎯 OPTIMIZED SEARCH: Checking {len(users_with_embeddings)} users registered for event {event_id}")
            logger.info(f"📊 Performance gain: {total_users_with_embeddings - len(users_with_embeddings)} fewer comparisons ({((total_users_with_embeddings - len(users_with_embeddings)) / max(total_users_with_embeddings, 1) * 100):.1f}% reduction)")
        else:
            # Fallback: Get all users with embeddings (original behavior)
            users_with_embeddings = db.query(User).filter(User.embedding.isnot(None)).all()
            logger.info(f"🔍 FULL SEARCH: Checking {len(users_with_embeddings)} users with face embeddings")

        all_matches = []  # Store all comparisons for analysis
        confirmed_matches = []  # Store only confirmed matches

        for user in users_with_embeddings:
            if user.embedding:
                try:
                    # Convert JSON back to numpy array
                    stored_embedding = np.array(user.embedding)

                    # Validate embedding dimensions
                    if stored_embedding.shape != face_embedding.shape:
                        logger.warning(f"Embedding dimension mismatch for user {user.id}: {stored_embedding.shape} vs {face_embedding.shape}")
                        continue

                    # Calculate distance with detailed logging
                    logger.info(f"Comparing with user {user.id} ({user.name})")
                    is_match, distance = compare_faces(stored_embedding, face_embedding, threshold)

                    # Store all comparisons for analysis
                    all_matches.append((user.id, user.name, distance, is_match))

                    if is_match:
                        confirmed_matches.append((user.id, distance))
                        logger.info(f"✅ MATCH FOUND: User {user.id} ({user.name}) - distance: {distance:.3f}")
                    else:
                        logger.info(f"❌ No match: User {user.id} ({user.name}) - distance: {distance:.3f}")

                except Exception as e:
                    logger.warning(f"Error comparing embedding for user {user.id}: {e}")
                    continue

        # Log analysis summary
        logger.info(f"\n📊 Face Matching Analysis:")
        logger.info(f"   Total users checked: {len(users_with_embeddings)}")
        logger.info(f"   Confirmed matches: {len(confirmed_matches)}")

        # Show top 5 closest matches for debugging
        all_matches.sort(key=lambda x: x[2])  # Sort by distance
        logger.info(f"   Top 5 closest distances:")
        for i, (user_id, name, distance, is_match) in enumerate(all_matches[:5]):
            status = "✅ MATCH" if is_match else "❌ No match"
            logger.info(f"     {i+1}. User {user_id} ({name}): {distance:.3f} - {status}")

        # Sort confirmed matches by distance (lower is better)
        confirmed_matches.sort(key=lambda x: x[1])

        logger.info(f"Found {len(confirmed_matches)} confirmed user matches")
        return confirmed_matches[:10]  # Return top 10 matches

    except Exception as e:
        logger.error(f"Error finding matching users: {e}")
        return []


def find_matching_users_for_event(face_embedding: np.ndarray, event_id: int, db: Session, threshold: float = FACE_RECOGNITION_TOLERANCE) -> List[Tuple[int, float]]:
    """
    Optimized function to find matching users specifically for an event.
    Only compares against users registered for the given event.

    Args:
        face_embedding: Face embedding to match against
        event_id: Event ID to limit search to registered users
        db: Database session
        threshold: Similarity threshold (lower is more strict)

    Returns:
        List of tuples (user_id, distance) sorted by similarity
    """
    import time
    start_time = time.time()

    result = find_matching_users(face_embedding, db, threshold, event_id)

    processing_time = time.time() - start_time
    logger.info(f"⚡ Event-optimized face matching completed in {processing_time:.3f} seconds")

    return result


def compare_faces(known_embedding: np.ndarray, unknown_embedding: np.ndarray, tolerance: float = FACE_RECOGNITION_TOLERANCE) -> Tuple[bool, float]:
    """
    Compare two face embeddings using face_recognition.face_distance.

    Args:
        known_embedding: Known face embedding
        unknown_embedding: Unknown face embedding to compare
        tolerance: Comparison tolerance

    Returns:
        Tuple of (is_match, distance)
    """
    try:
        # Use face_recognition's distance calculation (most reliable method)
        face_distances = face_recognition.face_distance([known_embedding], unknown_embedding)
        face_distance = face_distances[0]

        # Simple comparison based on distance threshold
        is_match = face_distance <= tolerance

        logger.info(f"Face comparison: distance={face_distance:.3f}, tolerance={tolerance:.3f}, match={is_match}")

        return is_match, face_distance

    except Exception as e:
        logger.error(f"Error comparing faces: {e}")
        return False, float('inf')


def validate_face_image(image_path: str) -> bool:
    """
    Validate that an image contains at least one detectable face suitable for selfies.

    Args:
        image_path: Path to the image file

    Returns:
        True if image contains at least one good quality face, False otherwise
    """
    try:
        faces_data = detect_faces_in_image(image_path)

        if not faces_data:
            logger.warning(f"No faces detected in selfie: {image_path}")
            return False

        # For selfies, we prefer exactly one face, but allow multiple if one is dominant
        if len(faces_data) == 1:
            logger.info(f"Perfect selfie: exactly one face detected in {image_path}")
            return True

        # If multiple faces, check if one is significantly larger (dominant face)
        if len(faces_data) > 1:
            # Sort faces by confidence/size
            faces_data.sort(key=lambda x: x.get('confidence', 0), reverse=True)

            # Check if the largest face is significantly bigger than others
            largest_face = faces_data[0]
            largest_confidence = largest_face.get('confidence', 0)

            # If the largest face has good confidence, accept it
            if largest_confidence > 0.3:  # Reasonable confidence threshold
                logger.info(f"Acceptable selfie: dominant face detected among {len(faces_data)} faces in {image_path}")
                return True
            else:
                logger.warning(f"Multiple faces detected but no dominant face in selfie: {image_path}")
                return False

        return False

    except Exception as e:
        logger.error(f"Error validating face image {image_path}: {e}")
        return False


def resize_image_for_face_detection(image_path: str, max_size: int = 800) -> str:
    """
    Resize image for faster face detection while maintaining aspect ratio.
    
    Args:
        image_path: Path to the original image
        max_size: Maximum dimension size
        
    Returns:
        Path to the resized image (same as input if no resize needed)
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Check if resize is needed
            if max(width, height) <= max_size:
                return image_path
            
            # Calculate new dimensions
            if width > height:
                new_width = max_size
                new_height = int((height * max_size) / width)
            else:
                new_height = max_size
                new_width = int((width * max_size) / height)
            
            # Resize and save
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            resized_path = image_path.replace('.', '_resized.')
            resized_img.save(resized_path, optimize=True, quality=85)
            
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            return resized_path
            
    except Exception as e:
        logger.error(f"Error resizing image {image_path}: {e}")
        return image_path  # Return original path if resize fails



