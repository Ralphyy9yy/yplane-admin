# YPlane — Online Flight Ticketing and Booking System
**Desktop / Web Admin Panel**
*Group 1 | Sequential Processing | Base Hub: Panglao–Bohol International Airport (TAG)*

FastAPI, PostgreSQL (SQLAlchemy + Psycopg 3), Jinja2, HTMX, and Bootstrap/Tailwind-inspired Stitch Minimalist Teal admin dashboard.

---

## 1. System Architecture & Sequential Processing

All state-changing flight booking and cancellation requests pass through a serialized single-worker queue (`queue.Queue()` in Python) backed by PostgreSQL transactional check-and-reserve (`SELECT ... FOR UPDATE`):
- **Arrival Order Guarantee**: Requests are enqueued in strict arrival order (FIFO).
- **No Concurrency in Critical Section**: Exactly one worker pulls and verifies active seat availability against `booking_seats` joined with `bookings`.
- **Live Auditing**: Every operation writes to `booking_logs` (`action`, `processing_type = 'SEQUENTIAL'`, `status`, `message`, `started_at`, `completed_at`), which is displayed live in real-time on the Admin Live Booking Logs Monitor.

---

## 2. Official 11-Table Database Schema

1. `users` — Customers and administrators (`role = 'CUSTOMER' | 'ADMIN'`)
2. `airports` — Airport master data (TAG, MNL, DVO, ILO, ENI, CRK)
3. `routes` — Airport pairs (Distance, duration, origin & destination)
4. `airplanes` — Aircraft fleet (Code, model, category, total seats, status)
5. `seats` — Physical seats allocated to aircraft (`seat_number`, `seat_type`, `seat_position`)
6. `flights` — Scheduled flights on routes (`flight_number`, date, departure/arrival times, fare, status)
7. `bookings` — Customer reservations (`booking_reference`, `flight_id`, `total_amount`, `status`)
8. `booking_seats` — Physical seats held by a booking
9. `payments` — Payment records (`amount`, `payment_method`, `transaction_reference`, `status`)
10. `booking_logs` — Auditable chronological sequential processing event trail
11. `system_logs` — Administrative audit records

---

## 3. Quick Start & Setup

1. **Configure Environment (`.env`)**:
   ```env
   DATABASE_URL=postgresql://postgres:...@...pooler.supabase.com:5432/postgres
   SECRET_KEY=yplane-secret-key-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ADMIN_EMAIL=admin@yplane.com
   ADMIN_PASSWORD=admin123
   ```

2. **Install Dependencies**:
   ```powershell
   python -m pip install -r requirements.txt
   ```

3. **Initialize Database & Seed Data**:
   ```powershell
   python seed_yplane.py
   ```

4. **Start Web Admin Server**:
   ```powershell
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. **Open Admin Console**:
   Navigate to `http://127.0.0.1:8000/auth/login`
   - Email: `admin@yplane.com` (or `admin@ticketadmin.com`)
   - Password: `admin123`

---

## 4. Live Demo Scenarios

In `/admin/queue` (or `/admin/booking-logs`):
- **5-Customers-1-Seat Competition Demo**:
  Click **"Run 5-Customers-1-Seat Demo"**.
  5 passenger requests fire simultaneously targeting seat `1A` on Panglao flight `YP-DEMO`.
  - **Result**: Exactly **1 row resolves to SUCCESS**, and **4 rows resolve to REJECTED** in strict arrival sequence.
- **2-Customers-1-Seat Warm-up Demo**:
  Click **"Run 2-for-1 Warm-up"** for a quick 2-row projector demonstration.

---

## 5. Mobile Client API (Shared Backend)

- `GET /api/flights` — List all scheduled flights
- `GET /api/flights/{id}/seats` — Live dynamic seat availability map
- `POST /api/bookings` — Enqueue booking request (`{"user_id": 1, "flight_id": 1, "seat_id": 1}`) -> returns HTTP 202 Accepted

---

## 6. Automated Tests

```powershell
python -m unittest discover -s tests -v
```
Verifies strict sequential ordering and single-winner guarantees under high contention.
