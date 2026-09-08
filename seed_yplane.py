import os
import sys
from datetime import datetime, date, time as dt_time, timedelta
from decimal import Decimal
from sqlalchemy import text
from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.core.config import settings
from app.models import (
    User, Airplane, Airport, Route, Flight, Seat,
    Booking, BookingSeat, Payment, BookingLog, SystemLog
)
import uuid

def init_db():
    print("Creating all tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    db = SessionLocal()
    try:
        def seed_user(email: str, name: str, role: str, password: str):
            existing = db.query(User).filter(User.email == email).first()
            hashed = get_password_hash(password)
            if not existing:
                user_id = uuid.uuid4()
                # Insert into auth.users which triggers insert into public.users
                db.execute(text("""
                    INSERT INTO auth.users (instance_id, id, aud, role, email, encrypted_password, email_confirmed_at, raw_user_meta_data, created_at, updated_at, confirmation_token, email_change, email_change_token_new, recovery_token)
                    VALUES ('00000000-0000-0000-0000-000000000000', :id, 'authenticated', 'authenticated', :email, '', now(), :meta, now(), now(), '', '', '', '')
                    ON CONFLICT (id) DO NOTHING
                """), {"id": user_id, "email": email, "meta": f'{{"name": "{name}"}}'})
                db.flush()
                # The trigger might take a split second or be part of the same transaction
                existing = db.query(User).filter(User.id == user_id).first()
                # If trigger failed or we need to insert manually:
                if not existing:
                    db.execute(text("INSERT INTO public.users (id, name, email, role, password_hash, is_active) VALUES (:id, :name, :email, :role, :phash, true)"),
                               {"id": user_id, "name": name, "email": email, "role": role, "phash": hashed})
                    existing = db.query(User).filter(User.id == user_id).first()
                print(f"Seeded User: {email} ({role})")
            
            if existing:
                existing.password_hash = hashed
                existing.role = role
                existing.is_active = True

        # 1. Seed Admin & Demo Users
        admin_emails = [settings.ADMIN_EMAIL, "admin@yplane.com"]
        for email in admin_emails:
            seed_user(email, "YPlane Administrator", "ADMIN", settings.ADMIN_PASSWORD)

        # Seed 5 Demo Customers
        for i in range(1, 6):
            seed_user(f"customer{i}@yplane.com", f"Passenger {i}", "CUSTOMER", "password123")
            
        db.commit()

        # 2. Seed Airports (Panglao Hub + Destinations)
        airports_data = [
            {"code": "TAG", "name": "Panglao–Bohol International Airport", "city": "Panglao", "country": "Philippines"},
            {"code": "MNL", "name": "Ninoy Aquino International Airport", "city": "Manila", "country": "Philippines"},
            {"code": "DVO", "name": "Francisco Bangoy International Airport", "city": "Davao", "country": "Philippines"},
            {"code": "ILO", "name": "Iloilo International Airport", "city": "Iloilo", "country": "Philippines"},
            {"code": "ENI", "name": "El Nido Airport (Lio Airport)", "city": "El Nido", "country": "Philippines"},
            {"code": "CRK", "name": "Clark International Airport", "city": "Clark", "country": "Philippines"},
        ]
        airport_map = {}
        for a_data in airports_data:
            airport = db.query(Airport).filter(Airport.code == a_data["code"]).first()
            if not airport:
                airport = Airport(
                    code=a_data["code"],
                    name=a_data["name"],
                    city=a_data["city"],
                    country=a_data["country"]
                )
                db.add(airport)
                db.flush()
                print(f"Seeded Airport: {airport.code} - {airport.city}")
            airport_map[a_data["code"]] = airport
        db.commit()

        # 3. Seed Airplanes & Physical Seats
        airplanes_data = [
            {"code": "RP-C8810", "name": "Airbus A320-200", "type": "Narrow-body Jet", "rows": 30, "cols": ["A", "B", "C", "D", "E", "F"]},
            {"code": "RP-C3230", "name": "ATR 72-600", "type": "Regional Turboprop", "rows": 18, "cols": ["A", "B", "C", "D"]},
            {"code": "RP-C5521", "name": "De Havilland Dash 8-400", "type": "Turboprop", "rows": 20, "cols": ["A", "B", "C", "D"]},
        ]
        airplane_map = {}
        for ap_data in airplanes_data:
            airplane = db.query(Airplane).filter(Airplane.model_number == ap_data["name"]).first()
            total_seats = ap_data["rows"] * len(ap_data["cols"])
            if not airplane:
                airplane = Airplane(
                    model_number=ap_data["name"],
                    total_seats=total_seats
                )
                db.add(airplane)
                db.flush()
                print(f"Seeded Airplane: {airplane.model_number} with {total_seats} seats")

                # Generate seats
                for row in range(1, ap_data["rows"] + 1):
                    seat_type = "BUSINESS" if row <= 2 else ("PREMIUM_ECONOMY" if row <= 5 else "ECONOMY")
                    for col in ap_data["cols"]:
                        seat_num = f"{row}{col}"
                        if len(ap_data["cols"]) == 6:
                            pos = "WINDOW" if col in ["A", "F"] else ("MIDDLE" if col in ["B", "E"] else "AISLE")
                        else:
                            pos = "WINDOW" if col in ["A", "D"] else "AISLE"
                        seat = Seat(
                            airplane_id=airplane.id,
                            seat_number=seat_num,
                            seat_class=seat_type,
                            seat_position=pos
                        )
                        db.add(seat)
                db.commit()
            airplane_map[ap_data["code"]] = airplane

        # 4. Seed Routes (Centered on TAG Hub)
        tag_id = airport_map["TAG"].id
        routes_data = [
            {"dest": "MNL", "dist": Decimal("630.00"), "duration": dt_time(1, 25)},
            {"dest": "DVO", "dist": Decimal("390.00"), "duration": dt_time(1, 5)},
            {"dest": "ILO", "dist": Decimal("210.00"), "duration": dt_time(0, 50)},
            {"dest": "ENI", "dist": Decimal("520.00"), "duration": dt_time(1, 30)},
            {"dest": "CRK", "dist": Decimal("700.00"), "duration": dt_time(1, 35)},
        ]
        route_map = {}
        for r_info in routes_data:
            dest_id = airport_map[r_info["dest"]].id
            # Outbound: TAG -> Dest
            r_out = db.query(Route).filter(Route.origin_airport_id == tag_id, Route.destination_airport_id == dest_id).first()
            if not r_out:
                r_out = Route(origin_airport_id=tag_id, destination_airport_id=dest_id, distance_km=r_info["dist"], estimated_duration_minutes=r_info["duration"].hour * 60 + r_info["duration"].minute)
                db.add(r_out)
                db.flush()
                print(f"Seeded Route: TAG -> {r_info['dest']}")
            route_map[f"TAG-{r_info['dest']}"] = r_out

            # Inbound: Dest -> TAG
            r_in = db.query(Route).filter(Route.origin_airport_id == dest_id, Route.destination_airport_id == tag_id).first()
            if not r_in:
                r_in = Route(origin_airport_id=dest_id, destination_airport_id=tag_id, distance_km=r_info["dist"], estimated_duration_minutes=r_info["duration"].hour * 60 + r_info["duration"].minute)
                db.add(r_in)
                db.flush()
                print(f"Seeded Route: {r_info['dest']} -> TAG")
            route_map[f"{r_info['dest']}-TAG"] = r_in
        db.commit()

        # 5. Seed Scheduled Flights for Today & Next Days
        today = datetime.utcnow()
        flights_config = [
            {"fn": "YP-101", "route": "TAG-MNL", "plane": "RP-C8810", "dep": today + timedelta(hours=1), "arr": today + timedelta(hours=2, minutes=25), "fare": Decimal("3450.00")},
            {"fn": "YP-102", "route": "MNL-TAG", "plane": "RP-C8810", "dep": today + timedelta(hours=3), "arr": today + timedelta(hours=4, minutes=25), "fare": Decimal("3450.00")},
            {"fn": "YP-201", "route": "TAG-DVO", "plane": "RP-C3230", "dep": today + timedelta(hours=5), "arr": today + timedelta(hours=6, minutes=5), "fare": Decimal("2890.00")},
            {"fn": "YP-301", "route": "TAG-ILO", "plane": "RP-C5521", "dep": today + timedelta(hours=7), "arr": today + timedelta(hours=7, minutes=50), "fare": Decimal("2150.00")},
            {"fn": "YP-401", "route": "TAG-ENI", "plane": "RP-C3230", "dep": today + timedelta(hours=9), "arr": today + timedelta(hours=10, minutes=30), "fare": Decimal("4200.00")},
            {"fn": "YP-501", "route": "TAG-CRK", "plane": "RP-C8810", "dep": today + timedelta(hours=11), "arr": today + timedelta(hours=12, minutes=35), "fare": Decimal("3100.00")},
            # Dedicated Live Demo Flight:
            {"fn": "YP-DEMO", "route": "TAG-MNL", "plane": "RP-C3230", "dep": today + timedelta(hours=24), "arr": today + timedelta(hours=25, minutes=25), "fare": Decimal("2999.00")},
        ]
        for f_info in flights_config:
            flight = db.query(Flight).filter(Flight.flight_number == f_info["fn"]).first()
            if not flight:
                airplane = airplane_map[f_info["plane"]]
                flight = Flight(
                    flight_number=f_info["fn"],
                    route_id=route_map[f_info["route"]].id,
                    airplane_id=airplane.id,
                    departure_time=f_info["dep"],
                    arrival_time=f_info["arr"],
                    price=f_info["fare"],
                    available_seats=airplane.total_seats,
                    status="SCHEDULED"
                )
                db.add(flight)
                print(f"Seeded Flight: {flight.flight_number} ({f_info['route']})")
        db.commit()

        print("\nSeed completed successfully for YPlane (Panglao Hub)!")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
