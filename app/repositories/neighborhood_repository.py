from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Neighborhood


def get_all_neighborhoods(db: Session):
    rows = db.query(Neighborhood).all()

    return {
        str(row.id): {
            "name": row.name,
            "factors": {
                "heat": row.heat_risk if row.heat_risk is not None else 0,
                "flood": row.flood_risk if row.flood_risk is not None else 0,
                "fire": row.fire_risk if row.fire_risk is not None else 0,
                "air": row.air_risk if row.air_risk is not None else 0,
            },
        }
        for row in rows
    }


def get_neighborhood_by_id(neighborhood_id: str, db: Session):
    row = db.query(Neighborhood).filter(Neighborhood.id == int(neighborhood_id)).first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown neighborhood_id '{neighborhood_id}'.",
        )

    return {
        "name": row.name,
        "factors": {
            "heat": row.heat_risk if row.heat_risk is not None else 0,
            "flood": row.flood_risk if row.flood_risk is not None else 0,
            "fire": row.fire_risk if row.fire_risk is not None else 0,
            "air": row.air_risk if row.air_risk is not None else 0,
        },
    }


def get_all_neighborhoods_geojson(db: Session):
    query = text("""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(geom)::json,
                'properties', json_build_object(
                    'id', id,
                    'name', name
                )
            ) AS feature
            FROM neighborhoods_real
            WHERE geom IS NOT NULL
        ) AS features;
    """)
    return db.execute(query).scalar()


def get_real_neighborhoods_geojson(db: Session):
    query = text("""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(ST_MakeValid(geom), 0.0002))::json,
                'properties', json_build_object(
                    'id', id,
                    'name', name,
                    'heat_risk', COALESCE(heat_risk, 0),
                    'flood_risk', COALESCE(flood_risk, 0),
                    'fire_risk', COALESCE(fire_risk, 0),
                    'air_risk', COALESCE(air_risk, 0),
                    'historical_flood_overlap_pct', COALESCE(historical_flood_overlap_pct, 0)
                )
            ) AS feature
            FROM neighborhoods_real
            WHERE geom IS NOT NULL
        ) AS features;
    """)
    return db.execute(query).scalar()


def get_fire_events_geojson(db: Session, fire_year: Optional[int] = None):
    if fire_year is None:
        query = text("""
            WITH la_extent AS (
                SELECT ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))) AS geom
                FROM neighborhoods_real
                WHERE geom IS NOT NULL
            )
            SELECT json_build_object(
                'type', 'FeatureCollection',
                'features', COALESCE(json_agg(feature), '[]'::json)
            )
            FROM (
                SELECT json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(
                        ST_SimplifyPreserveTopology(ST_MakeValid(f.geom), 0.0005)
                    )::json,
                    'properties', json_build_object(
                        'id', f.ogc_fid,
                        'name', f.fire_name,
                        'year', f.year_
                    )
                ) AS feature
                FROM fire_events f
                CROSS JOIN la_extent l
                WHERE f.geom IS NOT NULL
                  AND l.geom IS NOT NULL
                  AND ST_Intersects(ST_MakeValid(f.geom), l.geom)
            ) AS features;
        """)
        return db.execute(query).scalar()

    query = text("""
        WITH la_extent AS (
            SELECT ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))) AS geom
            FROM neighborhoods_real
            WHERE geom IS NOT NULL
        )
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(
                    ST_SimplifyPreserveTopology(ST_MakeValid(f.geom), 0.0005)
                )::json,
                'properties', json_build_object(
                    'id', f.ogc_fid,
                    'name', f.fire_name,
                    'year', f.year_
                )
            ) AS feature
            FROM fire_events f
            CROSS JOIN la_extent l
            WHERE f.geom IS NOT NULL
              AND l.geom IS NOT NULL
              AND f.year_ = :fire_year
              AND ST_Intersects(ST_MakeValid(f.geom), l.geom)
        ) AS features;
    """)
    return db.execute(query, {"fire_year": fire_year}).scalar()


def get_flood_raw_geojson(db: Session):
    query = text("""
        WITH la_extent AS (
            SELECT ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))) AS geom
            FROM neighborhoods_real
            WHERE geom IS NOT NULL
        )
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(
                    ST_SimplifyPreserveTopology(ST_MakeValid(f.geom), 0.0005)
                )::json,
                'properties', json_build_object(
                    'id', f.ogc_fid,
                    'objectid', f.objectid,
                    'fld_ar_id', f.fld_ar_id,
                    'study_typ', f.study_typ,
                    'fld_zone', f.fld_zone,
                    'zone_subty', f.zone_subty,
                    'sfha_tf', f.sfha_tf,
                    'f_exposure', f.f_exposure,
                    'flood_score', f.flood_score
                )
            ) AS feature
            FROM flood_raw f
            CROSS JOIN la_extent l
            WHERE f.geom IS NOT NULL
              AND l.geom IS NOT NULL
              AND ST_Intersects(ST_MakeValid(f.geom), l.geom)
        ) AS features;
    """)
    return db.execute(query).scalar()


def get_air_full_geojson(db: Session, pollutant: str = "pm2_5"):
    valid_columns = {
        "pm2_5": "pm2_5",
        "ozone": "ozone",
        "diesel": "dieselpm",
        "traffic": "traffic",
        "tox": "tox_rel",
        "pesticide": "pesticide",
    }

    selected_column = valid_columns.get(pollutant, "pm2_5")

    query = text(f"""
        WITH la_extent AS (
            SELECT ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))) AS geom
            FROM neighborhoods_real
            WHERE geom IS NOT NULL
        )
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
            SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(
                    ST_SimplifyPreserveTopology(ST_MakeValid(a.geom), 0.0005)
                )::json,
                'properties', json_build_object(
                    'id', a.ogc_fid,
                    'pollutant', :pollutant,
                    'value', a.{selected_column}
                )
            ) AS feature
            FROM air_full a
            CROSS JOIN la_extent l
            WHERE a.geom IS NOT NULL
              AND l.geom IS NOT NULL
              AND a.{selected_column} IS NOT NULL
              AND ST_Intersects(ST_MakeValid(a.geom), l.geom)
        ) AS features;
    """)

    return db.execute(query, {"pollutant": pollutant}).scalar()


def get_fire_history_neighborhood_ids(db: Session, fire_year: Optional[int] = None):
    if fire_year is None:
        query = text("""
            SELECT DISTINCT n.id
            FROM neighborhoods_real n
            JOIN fire_events f
              ON ST_Intersects(ST_MakeValid(n.geom), ST_MakeValid(f.geom))
            WHERE n.geom IS NOT NULL
              AND f.geom IS NOT NULL
        """)
        rows = db.execute(query).fetchall()
    else:
        query = text("""
            SELECT DISTINCT n.id
            FROM neighborhoods_real n
            JOIN fire_events f
              ON ST_Intersects(ST_MakeValid(n.geom), ST_MakeValid(f.geom))
            WHERE n.geom IS NOT NULL
              AND f.geom IS NOT NULL
              AND f.year_ = :fire_year
        """)
        rows = db.execute(query, {"fire_year": fire_year}).fetchall()

    return {str(row[0]) for row in rows}


def get_fire_overlap_percent_by_neighborhood(db: Session, fire_year: Optional[int] = None):
    if fire_year is None:
        query = text("""
            WITH fire_union AS (
                SELECT ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))) AS geom
                FROM fire_events
                WHERE geom IS NOT NULL
            )
            SELECT
                n.id,
                CASE
                    WHEN ST_Area(n.geom::geography) = 0 THEN 0
                    WHEN fu.geom IS NULL THEN 0
                    ELSE ROUND(
                        (
                            (
                                ST_Area(
                                    ST_Intersection(
                                        ST_MakeValid(n.geom),
                                        ST_MakeValid(fu.geom)
                                    )::geography
                                )
                                / ST_Area(n.geom::geography)
                            ) * 100.0
                        )::numeric,
                        2
                    )
                END AS overlap_pct
            FROM neighborhoods_real n
            CROSS JOIN fire_union fu
            WHERE n.geom IS NOT NULL
        """)
        rows = db.execute(query).fetchall()
    else:
        query = text("""
            WITH fire_union AS (
                SELECT ST_UnaryUnion(ST_Collect(ST_MakeValid(geom))) AS geom
                FROM fire_events
                WHERE geom IS NOT NULL
                  AND year_ = :fire_year
            )
            SELECT
                n.id,
                CASE
                    WHEN ST_Area(n.geom::geography) = 0 THEN 0
                    WHEN fu.geom IS NULL THEN 0
                    ELSE ROUND(
                        (
                            (
                                ST_Area(
                                    ST_Intersection(
                                        ST_MakeValid(n.geom),
                                        ST_MakeValid(fu.geom)
                                    )::geography
                                )
                                / ST_Area(n.geom::geography)
                            ) * 100.0
                        )::numeric,
                        2
                    )
                END AS overlap_pct
            FROM neighborhoods_real n
            CROSS JOIN fire_union fu
            WHERE n.geom IS NOT NULL
        """)
        rows = db.execute(query, {"fire_year": fire_year}).fetchall()

    return {
        str(row[0]): float(row[1]) if row[1] is not None else 0.0
        for row in rows
    }


def get_flood_overlap_percent_by_neighborhood(db: Session):
    query = text("""
        SELECT
            id,
            COALESCE(historical_flood_overlap_pct, 0) AS overlap_pct
        FROM neighborhoods_real
    """)

    rows = db.execute(query).fetchall()

    return {
        str(row[0]): float(row[1]) if row[1] is not None else 0.0
        for row in rows
    }


def get_air_average_by_neighborhood(db: Session):
    query = text("""
        SELECT
            id,
            COALESCE(air_context_pm25, 0) AS air_context_value
        FROM neighborhoods_real
    """)

    rows = db.execute(query).fetchall()

    return {
        str(row[0]): float(row[1]) if row[1] is not None else 0.0
        for row in rows
    }



  