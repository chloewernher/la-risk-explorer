from sqlalchemy import Column, Integer, String, Float
from geoalchemy2 import Geometry
from app.database import Base


class Neighborhood(Base):
    __tablename__ = "neighborhoods_real"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    geom = Column(Geometry("MULTIPOLYGON", srid=4326))

    heat_risk = Column(Float, nullable=True)
    flood_risk = Column(Float, nullable=True)
    fire_risk = Column(Float, nullable=True)
    air_risk = Column(Float, nullable=True)