from pydantic import BaseModel, Field
from typing import Literal


class EngineScore(BaseModel):
    kind: Literal["cp", "mate"]
    value: int
    perspective: Literal["white", "black"]


class Evidence(BaseModel):
    code: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: float = Field(ge=0.0)
    details: dict[str, str | int | float | bool]


class MoveAnalysis(BaseModel):
    ply: int
    fen_before: str
    played_move: str
    best_move: str | None
    score_before: EngineScore
    score_after: EngineScore
    centipawn_loss: int | None
    classification: str
    principal_variation: list[str]
    evidence: list[Evidence]


class PatternSummary(BaseModel):
    code: str
    sample_count: int
    affected_games: int
    average_cpl: float
    trend: Literal["improving", "stable", "worsening", "unknown"]
    confidence: float
