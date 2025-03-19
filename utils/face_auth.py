import face_recognition
import numpy as np
import io
from PIL import Image

def compare_faces(known_image, unknown_image):
    # Convert images to face_recognition format
    known_encoding = face_recognition.face_encodings(
        face_recognition.load_image_file(io.BytesIO(known_image))
    )
    unknown_encoding = face_recognition.face_encodings(
        face_recognition.load_image_file(io.BytesIO(unknown_image))
    )
    
    if not known_encoding or not unknown_encoding:
        return False
    
    # Compare faces
    results = face_recognition.compare_faces(
        [known_encoding[0]], unknown_encoding[0]
    )
    return results[0]
