from app.database import engine, SessionLocal, Base
from app.models import Neighborhood

Base.metadata.create_all(bind=engine)

db = SessionLocal()

existing = db.query(Neighborhood).count()

if existing == 0:
    seed_data = [
        Neighborhood(id="dtla", name="Downtown LA", heat=0.70, flood=0.35, fire=0.10, air=0.85),
        Neighborhood(id="santa_monica", name="Santa Monica", heat=0.35, flood=0.25, fire=0.15, air=0.40),
        Neighborhood(id="pasadena", name="Pasadena", heat=0.60, flood=0.30, fire=0.45, air=0.55),
        Neighborhood(id="echo_park", name="Echo Park / Silver Lake", heat=0.62, flood=0.40, fire=0.25, air=0.65),
        Neighborhood(id="woodland_hills", name="Woodland Hills", heat=0.90, flood=0.20, fire=0.55, air=0.50),
        Neighborhood(id="compton", name="Compton", heat=0.78, flood=0.45, fire=0.10, air=0.80),
    ]

    db.add_all(seed_data)
    db.commit()
    print("Database seeded successfully.")
else:
    print("Database already contains data.")

db.close()