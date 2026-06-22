import numpy as np

from app.pipeline.liveness import assess_liveness
from tests.conftest import make_periodic_image


def test_smooth_image_is_not_flagged_as_spoof() -> None:
    # A smooth gradient has a natural frequency falloff (no concentrated
    # high-frequency spike), which is what the heuristic treats as
    # "probably live".
    height, width = 300, 300
    y, x = np.mgrid[0:height, 0:width]
    gradient = ((x + y) % 256).astype(np.uint8)
    image = np.stack([gradient] * 3, axis=-1)

    result = assess_liveness(image)

    assert result.spoof_suspected is False
    assert 0.0 <= result.liveness_score <= 1.0


def test_strong_periodic_pattern_is_flagged_as_spoof() -> None:
    # Checkerboard-like regular pattern -> concentrated high-frequency
    # spike, similar in spirit to moire from a screen/print recapture.
    image = make_periodic_image(width=256, height=256, period=4)

    result = assess_liveness(image)

    assert result.spoof_suspected is True


def test_empty_crop_is_flagged_as_spoof_with_zero_score() -> None:
    image = np.zeros((0, 0, 3), dtype=np.uint8)

    result = assess_liveness(image)

    assert result.spoof_suspected is True
    assert result.liveness_score == 0.0
