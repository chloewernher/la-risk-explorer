from typing import List, Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    NeighborhoodInfo,
    NeighborhoodDetail,
    PresetInfo,
    ScoreRequest,
    ScoreResponse,
    FactorValues,
)
from app.repositories.neighborhood_repository import (
    get_all_neighborhoods,
    get_neighborhood_by_id,
    get_all_neighborhoods_geojson,
    get_real_neighborhoods_geojson,
    get_fire_events_geojson,
    get_flood_raw_geojson,
    get_air_full_geojson,
    get_fire_history_neighborhood_ids,
    get_flood_overlap_percent_by_neighborhood,
    get_air_average_by_neighborhood,
)

from app.services.scoring import (
    PRESET_DESCRIPTIONS,
    PRESET_WEIGHTS,
    calculate_score_response,
)

router = APIRouter()


SCENARIO_TO_PRESET = {
    "baseline": "balanced",
    "heat_fire": "fire_focused",
    "storm_flood": "flood_focused",
    "air_focus": "air_focused",
}


def normalize_top_drivers(top_drivers):
    if not top_drivers:
        return []

    label_map = {
        "heat": "Heat",
        "flood": "Flood",
        "fire": "Fire",
        "air": "Air",
        "heat_risk": "Heat",
        "flood_risk": "Flood",
        "fire_risk": "Fire",
        "air_risk": "Air",
    }

    output = []
    for item in top_drivers:
        output.append(label_map.get(str(item), str(item)))
    return output


def build_confidence_note(
    has_historical_fire: bool,
    fire_value: float,
    insight_flag: bool,
    flood_overlap_pct: float,
    flood_mismatch: bool,
):
    notes = []

    if insight_flag:
        notes.append(
            "Historical wildfire context is present while the modeled overall risk remains relatively low."
        )
    elif has_historical_fire and fire_value >= 0.4:
        notes.append(
            "Historical wildfire context and the modeled fire factor appear broadly aligned."
        )
    elif not has_historical_fire:
        notes.append(
            "No intersecting historical fire perimeter was found for the current fire-year filter."
        )

    if flood_mismatch:
        notes.append(
            "Flood-zone overlap is relatively high compared with the modeled flood factor."
        )
    elif flood_overlap_pct >= 10 and not flood_mismatch:
        notes.append(
            "Flood-zone overlap is present and broadly reflected in the modeled flood factor."
        )
    elif flood_overlap_pct == 0:
        notes.append(
            "No mapped flood-zone overlap was found for this neighborhood."
        )

    if not notes:
        notes.append(
            "Modeled factors and historical context do not show a strong mismatch under the current settings."
        )

    return " ".join(notes)


@router.get("/")
def root():
    return {
        "message": "LA Urban Environmental Risk Explorer API running",
        "version": "0.4.0",
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/presets", response_model=List[PresetInfo])
def list_presets():
    return [
        PresetInfo(
            preset_name=preset_name,
            description=PRESET_DESCRIPTIONS[preset_name],
            raw_weights=weights,
        )
        for preset_name, weights in PRESET_WEIGHTS.items()
    ]


@router.get("/neighborhoods", response_model=List[NeighborhoodInfo])
def list_neighborhoods(db: Session = Depends(get_db)):
    neighborhoods = get_all_neighborhoods(db=db)
    return [
        NeighborhoodInfo(id=neighborhood_id, name=data["name"])
        for neighborhood_id, data in neighborhoods.items()
    ]


@router.get("/neighborhoods/geojson")
def neighborhoods_geojson(db: Session = Depends(get_db)):
    return get_all_neighborhoods_geojson(db=db)


@router.get("/neighborhoods/{neighborhood_id}", response_model=NeighborhoodDetail)
def get_neighborhood_detail(neighborhood_id: str, db: Session = Depends(get_db)):
    neighborhood = get_neighborhood_by_id(neighborhood_id, db=db)
    return NeighborhoodDetail(
        id=neighborhood_id,
        name=neighborhood["name"],
        factors_normalized=FactorValues(**neighborhood["factors"]),
    )


@router.get("/real-neighborhoods/geojson")
def real_neighborhoods_geojson(db: Session = Depends(get_db)):
    return get_real_neighborhoods_geojson(db=db)


@router.get("/fire-events/geojson")
def fire_events_geojson(
    fire_year: Optional[str] = Query("all"),
    db: Session = Depends(get_db),
):
    selected_fire_year = None if fire_year == "all" else int(fire_year)
    return get_fire_events_geojson(db=db, fire_year=selected_fire_year)


@router.get("/flood-raw/geojson")
def flood_raw_geojson(db: Session = Depends(get_db)):
    return get_flood_raw_geojson(db=db)

@router.get("/air-full/geojson")
def air_full_geojson(
    pollutant: str = Query("pm2_5"),
    db: Session = Depends(get_db),
):
    return get_air_full_geojson(db=db, pollutant=pollutant)


@router.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest, db: Session = Depends(get_db)):
    return calculate_score_response(req, db=db)


@router.get("/compare")
def compare_neighborhoods(
    scenario: Optional[str] = Query("baseline"),
    year: int = Query(2026, ge=2000, le=2100),
    fire_year: Optional[str] = Query("all"),
    insight: Optional[str] = Query("on"),
    db: Session = Depends(get_db),
):
    neighborhoods = get_all_neighborhoods(db=db)
    results = []

    preset = SCENARIO_TO_PRESET.get(scenario or "baseline", "balanced")
    season = "summer"

    selected_fire_year = None if fire_year == "all" else int(fire_year)
    fire_history_ids = get_fire_history_neighborhood_ids(db=db, fire_year=selected_fire_year)
    flood_overlap_lookup = get_flood_overlap_percent_by_neighborhood(db=db)
    air_average_lookup = get_air_average_by_neighborhood(db=db)
    insight_enabled = str(insight).lower() == "on"

    for neighborhood_id in neighborhoods.keys():
        req = ScoreRequest(
            neighborhood_id=neighborhood_id,
            season=season,
            year=year,
            preset=preset,
            weights=None,
        )
        scored = calculate_score_response(req, db=db)

        fire_value = float(scored.factors_normalized.fire)
        flood_value = float(scored.factors_normalized.flood)
        air_value = float(scored.factors_normalized.air)

        has_historical_fire = str(neighborhood_id) in fire_history_ids
        flood_overlap_pct = float(flood_overlap_lookup.get(str(neighborhood_id), 0.0))
        air_context_value = float(air_average_lookup.get(str(neighborhood_id), 0.0))

        model_low = scored.risk_score_0to100 < 40
        insight_flag = bool(insight_enabled and has_historical_fire and model_low)

        flood_mismatch = bool(insight_enabled and flood_overlap_pct >= 10 and flood_value < 0.3)
        air_mismatch = bool(insight_enabled and air_context_value >= 20 and air_value < 0.3)

        if insight_flag:
            insight_message = (
                "This neighborhood intersects historical fire perimeters, "
                "but its modeled baseline risk remains relatively low."
            )
        else:
            insight_message = None

        if flood_mismatch:
            flood_insight_message = (
                "This neighborhood has notable flood-zone overlap, "
                "but its modeled flood factor remains relatively low."
            )
        else:
            flood_insight_message = None

        if air_mismatch:
            air_insight_message = (
                "This neighborhood shows elevated air pollution burden, "
                "but its modeled air factor remains relatively low."
            )
        else:
            air_insight_message = None

        results.append(
            {
                "neighborhood_id": scored.neighborhood_id,
                "neighborhood_name": scored.neighborhood_name,
                "scenario": scenario,
                "preset_used": preset,
                "risk_score_0to100": scored.risk_score_0to100,
                "risk_level": scored.risk_level,
                "top_drivers": normalize_top_drivers(scored.top_drivers),
                "heat": float(scored.factors_normalized.heat),
                "flood": flood_value,
                "fire": fire_value,
                "air": air_value,
                "has_historical_fire": has_historical_fire,
                "insight_flag": insight_flag,
                "insight_message": insight_message,
                "historical_flood_overlap_pct": flood_overlap_pct,
                "flood_mismatch_flag": flood_mismatch,
                "flood_insight_message": flood_insight_message,
                "air_context_value": air_context_value,
                "air_mismatch_flag": air_mismatch,
                "air_insight_message": air_insight_message,
                "confidence_note": build_confidence_note(
                    has_historical_fire=has_historical_fire,
                    fire_value=fire_value,
                    insight_flag=insight_flag,
                    flood_overlap_pct=flood_overlap_pct,
                    flood_mismatch=flood_mismatch,
                ),
            }
        )

    results.sort(key=lambda item: item["risk_score_0to100"], reverse=True)
    return results
