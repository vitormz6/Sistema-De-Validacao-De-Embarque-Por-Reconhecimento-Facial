import numpy as np

from app.pipeline.face_engine import DetectedFace
from app.pipeline.quality import compute_quality_score
from tests.conftest import make_face, make_image


def test_good_face_scores_high() -> None:
    image = make_image(400, 400)
    face = make_face(bbox=(100, 100, 300, 300), detection_score=0.97)

    score = compute_quality_score(image, face)

    assert 0.0 <= score <= 1.0
    # Flat gray image has near-zero Laplacian variance (no sharpness), so
    # the score won't be near 1 — but it shouldn't be near 0 either, since
    # size/detection/brightness/pose are all favorable.
    assert score > 0.4


def test_tiny_face_scores_lower_than_large_face() -> None:
    image = make_image(400, 400)
    small_face = make_face(bbox=(190, 190, 210, 210), detection_score=0.9)
    large_face = make_face(bbox=(50, 50, 350, 350), detection_score=0.9)

    small_score = compute_quality_score(image, small_face)
    large_score = compute_quality_score(image, large_face)

    assert small_score < large_score


def test_off_center_nose_lowers_pose_component() -> None:
    image = make_image(400, 400)

    frontal_face = make_face(bbox=(100, 100, 300, 300))

    turned_keypoints = np.array(
        [[150, 160], [250, 160], [260, 200], [160, 250], [240, 250]],
        dtype=np.float32,
    )
    turned_face = make_face(bbox=(100, 100, 300, 300), keypoints=turned_keypoints)

    assert compute_quality_score(image, turned_face) < compute_quality_score(
        image, frontal_face
    )


def test_no_keypoints_does_not_crash() -> None:
    image = make_image(400, 400)
    base_face = make_face(bbox=(100, 100, 300, 300))
    # make_face() substitutes synthetic keypoints when None is passed, so
    # build the dataclass directly here to genuinely exercise the
    # "no landmarks available" branch in `_pose_score`.
    face = DetectedFace(
        bbox=base_face.bbox,
        keypoints=None,
        detection_score=base_face.detection_score,
        embedding=base_face.embedding,
    )

    score = compute_quality_score(image, face)
    assert 0.0 <= score <= 1.0


def test_empty_image_does_not_crash() -> None:
    image = np.zeros((0, 0, 3), dtype=np.uint8)
    face = make_face()

    # Degenerate input: size/sharpness/brightness all bottom out at 0, but
    # detection_score and pose are face-only signals that still contribute
    # — the important contract here is "doesn't raise", not a specific value.
    score = compute_quality_score(image, face)

    assert 0.0 <= score <= 1.0
