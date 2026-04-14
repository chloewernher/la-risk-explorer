from typing import Dict, List, Tuple, Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas import (
    Weights,
    FactorValues,
    ScoreRequest,
    ScoreResponse,
    RiskLevel,
    Preset,
)
from app.repositories.neighborhood_repository import get_neighborhood_by_id


PRESET_DESCRIPTIONS: Dict[Preset, str] = {
    "balanced": "Equal emphasis across all environmental risk factors.",
    "heat_focused": "Prioritizes heat exposure while still considering other factors.",
    "flood_focused": "Prioritizes flood risk while still considering other factors.",
    "fire_focused": "Prioritizes wildfire exposure while still considering other factors.",
    "air_focused": "Prioritizes air quality while still considering other factors.",
}

PRESET_WEIGHTS: Dict[Preset, Weights] = {
    "balanced": Weights(heat=25, flood=25, fire=25, air=25),
    "heat_focused": Weights(heat=50, flood=15, fire=15, air=20),
    "flood_focused": Weights(heat=15, flood=50, fire=15, air=20),
    "fire_focused": Weights(heat=20, flood=15, fire=50, air=15),
    "air_focused": Weights(heat=20, flood=15, fire=15, air=50),
}


def round_factor(value: Optional[float]) -> float:
    return round(value if value is not None else 0.0, 2)


def get_factors_for_neighborhood(neighborhood_id: str, db: Session) -> FactorValues:
    neighborhood = get_neighborhood_by_id(neighborhood_id, db=db)

    raw_factors = neighborhood["factors"]

    return FactorValues(
        heat=round_factor(raw_factors.get("heat")),
        flood=round_factor(raw_factors.get("flood")),
        fire=round_factor(raw_factors.get("fire")),
        air=round_factor(raw_factors.get("air")),
    )


def normalize_weights(weights: Weights) -> Weights:
    total = weights.heat + weights.flood + weights.fire + weights.air

    if total <= 0:
        raise HTTPException(status_code=400, detail="Weights must sum to a value greater than 0.")

    return Weights(
        heat=weights.heat / total,
        flood=weights.flood / total,
        fire=weights.fire / total,
        air=weights.air / total,
    )


def classify_risk(score: float) -> RiskLevel:
    if score < 35:
        return "low"
    elif score < 70:
        return "medium"
    return "high"


def get_top_drivers(contributions: FactorValues, top_n: int = 2) -> List[str]:
    contribution_map = {
        "heat": contributions.heat,
        "flood": contributions.flood,
        "fire": contributions.fire,
        "air": contributions.air,
    }
    return sorted(contribution_map, key=contribution_map.get, reverse=True)[:top_n]


def resolve_weights(
    preset: Optional[Preset],
    weights: Optional[Weights],
) -> Tuple[Preset, Weights, Weights, bool]:
    if weights is not None:
        preset_used = preset or "balanced"
        raw_weights = weights
        custom_weights_provided = True
    else:
        preset_used = preset or "balanced"
        raw_weights = PRESET_WEIGHTS[preset_used]
        custom_weights_provided = False

    normalized = normalize_weights(raw_weights)
    return preset_used, raw_weights, normalized, custom_weights_provided


def calculate_score_response(req: ScoreRequest, db: Session) -> ScoreResponse:
    neighborhood = get_neighborhood_by_id(req.neighborhood_id, db=db)
    factors = get_factors_for_neighborhood(req.neighborhood_id, db=db)

    preset_used, raw_weights, weights_used, custom_weights_provided = resolve_weights(
        req.preset,
        req.weights,
    )

    raw_heat = factors.heat * weights_used.heat
    raw_flood = factors.flood * weights_used.flood
    raw_fire = factors.fire * weights_used.fire
    raw_air = factors.air * weights_used.air

    score_value = raw_heat + raw_flood + raw_fire + raw_air

    contributions = FactorValues(
        heat=round(raw_heat, 2),
        flood=round(raw_flood, 2),
        fire=round(raw_fire, 2),
        air=round(raw_air, 2),
    )

    risk_score_0to100 = round(score_value * 100, 2)
    risk_level = classify_risk(risk_score_0to100)
    top_drivers = get_top_drivers(contributions)

    return ScoreResponse(
        neighborhood_id=req.neighborhood_id,
        neighborhood_name=neighborhood["name"],
        season=req.season,
        year=req.year,
        preset_used=preset_used,
        custom_weights_provided=custom_weights_provided,
        factors_normalized=factors,
        weights_input_raw=raw_weights,
        weights_used=weights_used,
        risk_score_0to100=risk_score_0to100,
        risk_level=risk_level,
        top_drivers=top_drivers,
        contributions=contributions,
    )