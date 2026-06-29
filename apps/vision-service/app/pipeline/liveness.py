# Detecção básica de liveness via análise de frequência e nitidez.
# Não é um modelo treinado — só heurística por enquanto.
# TODO: substituir por modelo de anti-spoofing treinado se der tempo

from dataclasses import dataclass

import cv2
import numpy as np

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class LivenessAssessment:
    liveness_score: float
    spoof_suspected: bool


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _frequency_peak_ratio(gray_crop: np.ndarray) -> float:
    if gray_crop.size == 0:
        return 0.0

    spectrum = np.fft.fftshift(np.fft.fft2(gray_crop.astype(np.float32)))
    magnitude = np.abs(spectrum)

    height, width = magnitude.shape
    center_y, center_x = height // 2, width // 2

    # ignora as baixas frequências (DC), que dominam qualquer imagem
    radius = max(2, min(height, width) // 8)
    y_grid, x_grid = np.ogrid[:height, :width]
    low_freq_mask = (y_grid - center_y) ** 2 + (x_grid - center_x) ** 2 <= radius**2

    high_freq = magnitude[~low_freq_mask]

    if high_freq.size == 0:
        return 0.0

    mean_energy = float(high_freq.mean())
    if mean_energy <= 1e-6:
        return 0.0

    peak_energy = float(high_freq.max())
    return peak_energy / (mean_energy * high_freq.size)


def assess_liveness(face_crop_bgr: np.ndarray) -> LivenessAssessment:
    if face_crop_bgr.size == 0:
        return LivenessAssessment(liveness_score=0.0, spoof_suspected=True)

    gray = (
        cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
        if face_crop_bgr.ndim == 3
        else face_crop_bgr
    )

    sharpness_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    peak_ratio = _frequency_peak_ratio(gray)

    spoof_suspected = peak_ratio >= settings.LIVENESS_FREQ_PEAK_RATIO_THRESHOLD

    sharpness_component = _clip01(
        sharpness_variance / settings.LIVENESS_MIN_SHARPNESS_VARIANCE
    )
    peak_component = _clip01(
        1.0 - peak_ratio / settings.LIVENESS_FREQ_PEAK_RATIO_THRESHOLD
    )

    liveness_score = round(0.5 * sharpness_component + 0.5 * peak_component, 4)

    return LivenessAssessment(
        liveness_score=_clip01(liveness_score),
        spoof_suspected=spoof_suspected,
    )
