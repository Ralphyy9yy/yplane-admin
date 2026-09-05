import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.core.config import settings
from app.models import User
from app.services import queue_service

from app.routes import (
    auth, dashboard, airports, routes_mgmt, airplanes, flights,
    bookings, payments, users, queue as queue_route, api
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is initialized
    Base.metadata.create_all(bind=engine)
    # Ensure initial admin is present
    _seed_admin()
    # Start single sequential background worker
    queue_service.start_worker()
    yield
    # Graceful worker shutdown
    queue_service.stop_worker()


def _seed_admin():
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.ADMIN_EMAIL).first()
        hashed = get_password_hash(settings.ADMIN_PASSWORD)
        if not admin:
            admin = User(
                name="YPlane Administrator",
                email=settings.ADMIN_EMAIL,
                password=hashed,
                password_hash=hashed,
                role="ADMIN",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"[SEED] YPlane Admin created: {settings.ADMIN_EMAIL}")
        else:
            admin.role = "ADMIN"
            admin.password = hashed
            admin.password_hash = hashed
            db.commit()
    finally:
        db.close()


from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="YPlane Web Admin Portal",
    description="Online Flight Ticketing and Booking System — Group 1 Sequential Processing (Panglao Hub)",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for Flutter mobile/web apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static assets (Stitch Minimalist Teal CSS & JS)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount Routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/admin", tags=["dashboard"])
app.include_router(airports.router, prefix="/admin", tags=["airports"])
app.include_router(routes_mgmt.router, prefix="/admin", tags=["routes"])
app.include_router(airplanes.router, prefix="/admin", tags=["airplanes"])
app.include_router(flights.router, prefix="/admin", tags=["flights"])
app.include_router(bookings.router, prefix="/admin", tags=["bookings"])
app.include_router(payments.router, prefix="/admin", tags=["payments"])
app.include_router(users.router, prefix="/admin", tags=["users"])
app.include_router(queue_route.router, prefix="/admin", tags=["queue"])
app.include_router(api.router, prefix="/api", tags=["api"])


@app.get("/")
async def root():
    return RedirectResponse(url="/admin/dashboard", status_code=302)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
