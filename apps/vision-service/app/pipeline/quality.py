# Cálculo do score de qualidade da imagem facial.
# Combina 5 métricas: detecção, tamanho, nitidez, brilho e pose.

import cv2
import numpy as np

from app.core.config import settings
from app.pipeline.face_engine import DetectedFace

_WEIGHTS = {
    "detection": 0.20,
    "size": 0.20,
    "sharpness": 0.25,
    "brightness": 0.15,
    "pose": 0.20,
}


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def crop_face(image: np.ndarray, bbox: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    x1, y1, x2, y2 = bbox

    x1 = max(0, int(x1))
    y1 = max(0, int(y1))
    x2 = min(width, int(x2))
    y2 = min(height, int(y2))

    if x2 <= x1 or y2 <= y1:
        return image[0:0, 0:0]

    return image[y1:y2, x1:x2]


def _size_score(image: np.ndarray, bbox: np.ndarray) -> float:
    image_area = image.shape[0] * image.shape[1]
    if image_area <= 0:
        return 0.0

    x1, y1, x2, y2 = bbox
    face_area = max(0.0, float(x2 - x1)) * max(0.0, float(y2 - y1))
    ratio = face_area / image_area

    return _clip01(ratio / settings.MIN_FACE_SIZE_RATIO)


def _sharpness_score(face_crop: np.ndarray) -> float:
    if face_crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if face_crop.ndim == 3 else face_crop
    variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    return _clip01(variance / settings.BLUR_VARIANCE_REFERENCE)


def _brightness_score(face_crop: np.ndarray) -> float:
    if face_crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY) if face_crop.ndim == 3 else face_crop
    mean_brightness = float(gray.mean())

    if settings.BRIGHTNESS_MIN <= mean_brightness <= settings.BRIGHTNESS_MAX:
        return 1.0

    if mean_brightness < settings.BRIGHTNESS_MIN:
        return _clip01(mean_brightness / settings.BRIGHTNESS_MIN)

    overshoot = mean_brightness - settings.BRIGHTNESS_MAX
    return _clip01(1.0 - overshoot / settings.BRIGHTNESS_MAX)


def _pose_score(keypoints: np.ndarray | None) -> float:
    # estima se a face está de frente pela posição do nariz em relação aos olhos
    if keypoints is None or len(keypoints) < 3:
        return 0.75

    left_eye, right_eye, nose = keypoints[0], keypoints[1], keypoints[2]
    eye_distance = float(np.linalg.norm(right_eye - left_eye))

    if eye_distance <= 0:
        return 0.5

    eye_midpoint_x = (left_eye[0] + right_eye[0]) / 2.0
    offset_ratio = abs(float(nose[0]) - eye_midpoint_x) / eye_distance

    return _clip01(1.0 - offset_ratio / 0.5)


def compute_quality_score(image: np.ndarray, face: DetectedFace) -> float:
    face_crop = crop_face(image, face.bbox)

    components = {
        "detection": _clip01(face.detection_score),
        "size": _size_score(image, face.bbox),
        "sharpness": _sharpness_score(face_crop),
        "brightness": _brightness_score(face_crop),
        "pose": _pose_score(face.keypoints),
    }

    score = sum(_WEIGHTS[name] * value for name, value in components.items())
    return round(_clip01(score), 4)
