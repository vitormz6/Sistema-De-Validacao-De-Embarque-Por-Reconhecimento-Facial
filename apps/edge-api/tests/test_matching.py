import uuid

from app.modules.cache.matching import find_nearest
from app.modules.cache.model import LocalFaceEmbedding


def _embedding(passenger_id: uuid.UUID, vector: list[float]) -> LocalFaceEmbedding:
    return LocalFaceEmbedding(
        id=uuid.uuid4(),
        passenger_id=passenger_id,
        embedding=vector,
        model_name="arcface",
        model_version="buffalo_l",
    )


def test_no_candidates_returns_none() -> None:
    assert find_nearest([1.0, 0.0, 0.0], []) is None


def test_identical_vector_has_zero_distance() -> None:
    passenger_id = uuid.uuid4()
    candidates = [_embedding(passenger_id, [1.0, 0.0, 0.0])]

    result = find_nearest([1.0, 0.0, 0.0], candidates)

    assert result is not None
    assert result.passenger_id == passenger_id
    assert result.distance < 1e-9


def test_orthogonal_vector_has_distance_one() -> None:
    passenger_id = uuid.uuid4()
    candidates = [_embedding(passenger_id, [1.0, 0.0, 0.0])]

    result = find_nearest([0.0, 1.0, 0.0], candidates)

    assert result is not None
    assert abs(result.distance - 1.0) < 1e-9


def test_picks_closest_among_multiple_candidates() -> None:
    near_id = uuid.uuid4()
    far_id = uuid.uuid4()
    candidates = [
        _embedding(far_id, [0.0, 1.0, 0.0]),
        _embedding(near_id, [0.99, 0.01, 0.0]),
    ]

    result = find_nearest([1.0, 0.0, 0.0], candidates)

    assert result is not None
    assert result.passenger_id == near_id


def test_zero_probe_vector_returns_none() -> None:
    candidates = [_embedding(uuid.uuid4(), [1.0, 0.0, 0.0])]

    assert find_nearest([0.0, 0.0, 0.0], candidates) is None
