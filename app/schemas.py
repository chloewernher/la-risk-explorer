from pydantic import BaseModel, Field
from typing import Literal, List, Optional

Season = Literal["summer", "winter"]
RiskLevel = Literal["low", "medium", "high"]
Preset = Literal[
    "balanced",
    "heat_focused",
    "flood_focused",
    "fire_focused",
    "air_focused",
]


class Weights(BaseModel):
    heat: float = Field(..., ge=0)
    flood: float = Field(..., ge=0)
    fire: float = Field(..., ge=0)
    air: float = Field(..., ge=0)


class FactorValues(BaseModel):
    heat: float = Field(..., ge=0, le=1)
    flood: float = Field(..., ge=0, le=1)
    fire: float = Field(..., ge=0, le=1)
    air: float = Field(..., ge=0, le=1)


class ScoreRequest(BaseModel):
    neighborhood_id: str
    season: Season
    year: int = Field(..., ge=2000, le=2100)
    preset: Optional[Preset] = None
    weights: Optional[Weights] = None


class NeighborhoodInfo(BaseModel):
    id: str
    name: str


class NeighborhoodDetail(BaseModel):
    id: str
    name: str
    factors_normalized: FactorValues


class ScoreResponse(BaseModel):
    neighborhood_id: str
    neighborhood_name: str
    season: Season
    year: int
    preset_used: Preset
    custom_weights_provided: bool
    factors_normalized: FactorValues
    weights_input_raw: Weights
    weights_used: Weights
    risk_score_0to100: float
    risk_level: RiskLevel
    top_drivers: List[str]
    contributions: FactorValues


class PresetInfo(BaseModel):
    preset_name: Preset
    description: str
    raw_weights: Weights


class CompareResponseItem(BaseModel):
    neighborhood_id: str
    neighborhood_name: str
    risk_score_0to100: float
    risk_level: RiskLevel
    top_drivers: List[str]