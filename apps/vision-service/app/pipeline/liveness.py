"""
Basic liveness / anti-spoofing heuristic (RFC 3.4 - R2 "Ataques de
Spoofing" / M6 "Anti-Spoofing Inicial": "aplicação de regras básicas de
consistência para reduzir falsos aceites no MVP; a arquitetura prevê
evolução para mecanismos avançados de liveness em etapas futuras").

This is intentionally NOT a trained anti-spoofing model — just two cheap
signals computed on the face crop:

1. Frequency-domain "peakiness": printed photos and screen recaptures
   often introduce halftone/moire patterns that show up as a few
   concentrated high-frequency spikes, instead of the smoother frequency
   falloff a direct camera capture of a real face tends to have.
2. Flat sharpness: an unusually low Laplacian variance combined with the
   peakiness signal raises confidence that the input is a flat
   reproduction rather than a live face.

Both signals are folded into a single `liveness_score` in [0, 1] (1 = most
likely live); `spoof_suspected` is a hard boolean cut on the frequency
signal alone, since it's the more specific indicator of the two.
"""

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

    # Mask out the low-frequency core (DC + immediate neighborhood), which
    # dominates any natural image and isn't informative for this check.
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
