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

def init_db():
    print("Creating all tables in PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    db = SessionLocal()
    try:
        # 1. Seed Admin & Demo Users
        admin_emails = [settings.ADMIN_EMAIL, "admin@yplane.com"]
        for email in admin_emails:
            existing = db.query(User).filter(User.email == email).first()
            hashed = get_password_hash(settings.ADMIN_PASSWORD)
            if not existing:
                admin = User(
                    name="YPlane Administrator",
                    email=email,
                    password=hashed,
                    password_hash=hashed,
                    role="ADMIN",
                    is_active=True
                )
                db.add(admin)
                print(f"Seeded Admin: {email}")
            else:
                existing.password = hashed
                existing.password_hash = hashed
                existing.role = "ADMIN"

        # Seed 5 Demo Customers
        for i in range(1, 6):
            c_email = f"customer{i}@yplane.com"
            existing = db.query(User).filter(User.email == c_email).first()
            c_hashed = get_password_hash("password123")
            if not existing:
                customer = User(
                    name=f"Passenger {i}",
                    email=c_email,
                    password=c_hashed,
                    password_hash=c_hashed,
                    role="CUSTOMER",
                    is_active=True
                )
                db.add(customer)
            else:
                existing.password = c_hashed
                existing.password_hash = c_hashed
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
            airport = db.query(Airport).filter(Airport.airport_code == a_data["code"]).first()
            if not airport:
                airport = Airport(
                    airport_code=a_data["code"],
                    airport_name=a_data["name"],
                    city=a_data["city"],
                    country=a_data["country"]
                )
                db.add(airport)
                db.flush()
                print(f"Seeded Airport: {airport.airport_code} - {airport.city}")
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
            airplane = db.query(Airplane).filter(Airplane.airplane_code == ap_data["code"]).first()
            total_seats = ap_data["rows"] * len(ap_data["cols"])
            if not airplane:
                airplane = Airplane(
                    airplane_code=ap_data["code"],
                    airplane_name=ap_data["name"],
                    airplane_type=ap_data["type"],
                    total_seats=total_seats,
                    status="ACTIVE"
                )
                db.add(airplane)
                db.flush()
                print(f"Seeded Airplane: {airplane.airplane_code} ({airplane.airplane_name}) with {total_seats} seats")

                # Generate seats
                for row in range(1, ap_data["rows"] + 1):
                    seat_type = "BUSINESS" if row <= 2 else ("PREMIUM" if row <= 5 else "ECONOMY")
                    for col in ap_data["cols"]:
                        seat_num = f"{row}{col}"
                        if len(ap_data["cols"]) == 6:
                            pos = "WINDOW" if col in ["A", "F"] else ("MIDDLE" if col in ["B", "E"] else "AISLE")
                        else:
                            pos = "WINDOW" if col in ["A", "D"] else "AISLE"
                        seat = Seat(
                            airplane_id=airplane.id,
                            seat_number=seat_num,
                            seat_type=seat_type,
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
                r_out = Route(origin_airport_id=tag_id, destination_airport_id=dest_id, distance=r_info["dist"], estimated_duration=r_info["duration"])
                db.add(r_out)
                db.flush()
                print(f"Seeded Route: TAG -> {r_info['dest']}")
            route_map[f"TAG-{r_info['dest']}"] = r_out

            # Inbound: Dest -> TAG
            r_in = db.query(Route).filter(Route.origin_airport_id == dest_id, Route.destination_airport_id == tag_id).first()
            if not r_in:
                r_in = Route(origin_airport_id=dest_id, destination_airport_id=tag_id, distance=r_info["dist"], estimated_duration=r_info["duration"])
                db.add(r_in)
                db.flush()
                print(f"Seeded Route: {r_info['dest']} -> TAG")
            route_map[f"{r_info['dest']}-TAG"] = r_in
        db.commit()

        # 5. Seed Scheduled Flights for Today & Next Days
        today = date.today()
        flights_config = [
            {"fn": "YP-101", "route": "TAG-MNL", "plane": "RP-C8810", "dep": dt_time(8, 0), "arr": dt_time(9, 25), "fare": Decimal("3450.00")},
            {"fn": "YP-102", "route": "MNL-TAG", "plane": "RP-C8810", "dep": dt_time(10, 30), "arr": dt_time(11, 55), "fare": Decimal("3450.00")},
            {"fn": "YP-201", "route": "TAG-DVO", "plane": "RP-C3230", "dep": dt_time(12, 15), "arr": dt_time(13, 20), "fare": Decimal("2890.00")},
            {"fn": "YP-301", "route": "TAG-ILO", "plane": "RP-C5521", "dep": dt_time(14, 0), "arr": dt_time(14, 50), "fare": Decimal("2150.00")},
            {"fn": "YP-401", "route": "TAG-ENI", "plane": "RP-C3230", "dep": dt_time(15, 30), "arr": dt_time(17, 0), "fare": Decimal("4200.00")},
            {"fn": "YP-501", "route": "TAG-CRK", "plane": "RP-C8810", "dep": dt_time(18, 0), "arr": dt_time(19, 35), "fare": Decimal("3100.00")},
            # Dedicated Live Demo Flight:
            {"fn": "YP-DEMO", "route": "TAG-MNL", "plane": "RP-C3230", "dep": dt_time(9, 0), "arr": dt_time(10, 25), "fare": Decimal("2999.00")},
        ]
        for f_info in flights_config:
            flight = db.query(Flight).filter(Flight.flight_number == f_info["fn"]).first()
            if not flight:
                flight = Flight(
                    flight_number=f_info["fn"],
                    route_id=route_map[f_info["route"]].id,
                    airplane_id=airplane_map[f_info["plane"]].id,
                    departure_date=today,
                    departure_time=f_info["dep"],
                    arrival_time=f_info["arr"],
                    fare=f_info["fare"],
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
