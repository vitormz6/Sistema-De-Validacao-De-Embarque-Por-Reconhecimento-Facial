"""
1:N face matching against the local cache — plain NumPy cosine distance,
no ANN index. A single bus's active passenger list is small (tens to a
few hundred), so a linear scan comfortably fits the RNF01 ≤2s budget.
"""

import uuid
from dataclasses import dataclass

import numpy as np

from app.modules.cache.model import LocalFaceEmbedding


@dataclass(frozen=True, slots=True)
class MatchResult:
    passenger_id: uuid.UUID
    distance: float


def find_nearest(
    probe_embedding: list[float],
    candidates: list[LocalFaceEmbedding],
) -> MatchResult | None:
    if not candidates:
        return None

    probe = np.asarray(probe_embedding, dtype=np.float64)
    probe_norm = np.linalg.norm(probe)

    if probe_norm == 0:
        return None

    matrix = np.asarray([candidate.embedding for candidate in candidates], dtype=np.float64)
    matrix_norms = np.linalg.norm(matrix, axis=1)

    # Avoid division by zero for any degenerate cached row.
    safe_norms = np.where(matrix_norms == 0, np.inf, matrix_norms)

    cosine_similarities = (matrix @ probe) / (safe_norms * probe_norm)
    distances = 1.0 - cosine_similarities

    best_index = int(np.argmin(distances))

    return MatchResult(
        passenger_id=candidates[best_index].passenger_id,
        distance=float(distances[best_index]),
    )
