import os

BASE = r"c:\Web Admin\app\templates"

def w(rel_path, content):
    full_path = os.path.join(BASE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Created: {rel_path}")

# 1. LOGIN
w("auth/login.html", """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Admin Login — YPlane Operations</title>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin=""/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
  <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet"/>
  <link rel="stylesheet" href="/static/css/admin.css"/>
</head>
<body class="login-body">
  <main class="login-container">
    <div class="login-card">
      <div class="login-logo">
        <div class="login-logo-icon">
          <span class="material-symbols-outlined">flight_takeoff</span>
        </div>
      </div>
      <div class="login-header">
        <h1 class="login-title">YPlane Operations Portal</h1>
        <p class="login-subtitle">Flight Management &amp; Sequential Queue Console (Panglao Hub)</p>
      </div>
      {% if error %}
      <div class="login-error">
        <span class="material-symbols-outlined">error</span>
        <span>{{ error }}</span>
      </div>
      {% endif %}
      <form class="login-form" method="post" action="/auth/login">
        <div class="form-field">
          <label class="form-label" for="email">Administrator Email</label>
          <input class="form-input" id="email" name="email" type="email" placeholder="admin@yplane.com" value="admin@ticketadmin.com" required autocomplete="email"/>
        </div>
        <div class="form-field">
          <div class="form-label-row">
            <label class="form-label" for="password">Password</label>
          </div>
          <div class="form-input-group">
            <input class="form-input" id="password" name="password" type="password" value="admin123" placeholder="••••••••" required autocomplete="current-password"/>
            <button type="button" class="form-input-action" id="toggle-pwd" aria-label="Toggle password visibility">
              <span class="material-symbols-outlined" id="pwd-icon">visibility</span>
            </button>
          </div>
        </div>
        <div class="form-remember">
          <label class="form-checkbox-label">
            <input type="checkbox" name="remember" class="form-checkbox" checked/>
            <span>Remember terminal session</span>
          </label>
        </div>
        <button type="submit" class="btn-primary w-full">Sign In to YPlane Admin</button>
      </form>
    </div>
    <div class="login-footer">
      <span class="material-symbols-outlined" style="font-size:16px">verified_user</span>
      <span>Panglao–Bohol International Airport (TAG) Hub · Group 1 Sequential Processing</span>
    </div>
  </main>
  <script>
    (function() {
      const btn = document.getElementById('toggle-pwd');
      const input = document.getElementById('password');
      const icon = document.getElementById('pwd-icon');
      if (btn) {
        btn.addEventListener('click', function() {
          const show = input.type === 'password';
          input.type = show ? 'text' : 'password';
          icon.textContent = show ? 'visibility_off' : 'visibility';
        });
      }
    })();
  </script>
</body>
</html>
""")

# 2. DASHBOARD
w("dashboard.html", """
{% extends "base.html" %}
{% block title %}Dashboard Overview{% endblock %}
{% block page_title %}Operations Dashboard{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Flight Operations Overview</h1>
    <p class="page-subtitle">Panglao–Bohol International Airport (TAG) Hub · Live metrics &amp; serialized transaction status.</p>
  </div>
  <div class="page-header-actions">
    <a href="/admin/queue" class="btn-primary">
      <span class="material-symbols-outlined">view_timeline</span>
      Live Queue Monitor
    </a>
    <a href="/admin/flights/new" class="btn-secondary">
      <span class="material-symbols-outlined">add</span>
      Schedule Flight
    </a>
  </div>
</div>

<div class="stat-grid dashboard-stats">
  <div class="stat-card">
    <div class="stat-top">
      <span class="stat-label">Active Aircraft</span>
      <span class="stat-icon"><span class="material-symbols-outlined">airlines</span></span>
    </div>
    <div><span class="stat-value">{{ stats.airplanes }}</span><span class="stat-unit"> In Fleet</span></div>
    <div class="stat-sub"><span class="trend-up">TAG Hub</span> RP-C8810 · RP-C3230 · RP-C5521</div>
  </div>

  <div class="stat-card">
    <div class="stat-top">
      <span class="stat-label">Hub Routes &amp; Flights</span>
      <span class="stat-icon"><span class="material-symbols-outlined">connecting_airports</span></span>
    </div>
    <div><span class="stat-value">{{ stats.flights }}</span><span class="stat-unit"> Scheduled Flights</span></div>
    <div class="stat-sub">{{ stats.routes }} routes connected to Panglao (MNL, DVO, ILO, ENI, CRK)</div>
  </div>

  <div class="stat-card">
    <div class="stat-top">
      <span class="stat-label">Confirmed Reservations</span>
      <span class="stat-icon"><span class="material-symbols-outlined">airplane_ticket</span></span>
    </div>
    <div><span class="stat-value">{{ stats.confirmed }}</span><span class="stat-unit"> Bookings</span><strong class="stat-side">₱{{ '%.2f'|format(stats.revenue) }}</strong></div>
    <div class="stat-sub">{{ stats.passengers }} registered passengers · Queue Depth: {{ stats.queue_depth }}</div>
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 380px;gap:1.5rem;align-items:start">
  <div class="card">
    <div class="card-header">
      <div>
        <h2 class="card-title"><span class="material-symbols-outlined">airplane_ticket</span>Recent Flight Bookings</h2>
        <p class="card-caption">Latest customer reservations processed through the sequential pipeline</p>
      </div>
      <a class="table-link" href="/admin/bookings">View all <span class="material-symbols-outlined">arrow_forward</span></a>
    </div>
    <div class="table-wrapper">
      <table class="admin-table">
        <thead>
          <tr>
            <th>Ref / Passenger</th>
            <th>Flight &amp; Route</th>
            <th>Seat</th>
            <th>Fare</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {% for b in recent_bookings %}
          <tr>
            <td>
              <div class="user-cell">
                <span class="user-avatar">{{ (b.user.name if b.user else 'P')[0].upper() }}</span>
                <span>
                  <strong><a href="/admin/bookings/{{ b.id }}" style="color:var(--on-surface)">{{ b.booking_reference }}</a></strong>
                  <small>{{ b.user.name if b.user else 'Unknown' }}</small>
                </span>
              </div>
            </td>
            <td>
              <strong>{{ b.flight.flight_number if b.flight else '-' }}</strong><br>
              <span class="form-help">{{ b.flight.route.origin_airport.airport_code if b.flight and b.flight.route else '' }} → {{ b.flight.route.destination_airport.airport_code if b.flight and b.flight.route else '' }}</span>
            </td>
            <td style="font-family:monospace;font-weight:600">
              {% for bs in b.booking_seats %}
                <span class="seat-chip" style="padding:2px 6px">{{ bs.seat.seat_number }}</span>
              {% else %}
                -
              {% endfor %}
            </td>
            <td style="font-weight:600">₱{{ '%.2f'|format(b.total_amount) }}</td>
            <td><span class="badge badge-{{ b.status.lower() }}">{{ b.status }}</span></td>
          </tr>
          {% else %}
          <tr><td colspan="5"><div class="empty-state"><h3>No bookings yet</h3><p>Booking requests will appear here as they are confirmed.</p></div></td></tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2 class="card-title"><span class="material-symbols-outlined">view_timeline</span>Sequential Stream</h2>
        <p class="card-caption">Single dedicated FIFO worker audit trail</p>
      </div>
      <span class="queue-live-badge"><span class="queue-live-dot"></span>Worker Active</span>
    </div>
    <div style="padding:1rem">
      {% for log in recent_logs %}
      <div style="padding:0.75rem;border-radius:8px;background:var(--surface-container-low);margin-bottom:0.5rem;display:flex;align-items:center;gap:0.75rem">
        <span class="material-symbols-outlined" style="font-size:18px;color:{% if log.status == 'SUCCESS' %}#16a34a{% elif log.status == 'REJECTED' %}#dc2626{% else %}#d97706{% endif %}">
          {% if log.status == 'SUCCESS' %}check_circle{% elif log.status == 'REJECTED' %}cancel{% else %}sync{% endif %}
        </span>
        <div style="flex:1;min-width:0">
          <div style="font-size:12px;font-weight:600;display:flex;justify-content:space-between">
            <span>{{ log.action }}</span>
            <span style="font-size:10px;color:var(--secondary)">{{ log.started_at.strftime('%H:%M:%S') }}</span>
          </div>
          <div style="font-size:11px;color:var(--secondary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
            {{ log.message or log.status }}
          </div>
        </div>
        <span class="badge badge-{{ log.status.lower() }}">{{ log.status }}</span>
      </div>
      {% else %}
      <div class="empty-state" style="padding:2rem 1rem">
        <span class="material-symbols-outlined" style="font-size:24px;color:var(--secondary)">inbox</span>
        <p style="font-size:12px;margin-top:0.5rem">No recent queue events logged yet.</p>
      </div>
      {% endfor %}

      <div style="margin-top:1rem;display:flex;flex-direction:column;gap:0.5rem">
        <form method="post" action="/admin/queue/demo-5-for-1">
          <button type="submit" class="btn-primary w-full">
            <span class="material-symbols-outlined">play_arrow</span>
            Run 5-for-1 Demo (Panglao)
          </button>
        </form>
        <a href="/admin/queue" class="btn-secondary w-full text-center">
          <span class="material-symbols-outlined">open_in_full</span>
          Open Full Monitor
        </a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""")

# 3. AIRPORTS
w("airports/list.html", """
{% extends "base.html" %}
{% block title %}Airports{% endblock %}
{% block page_title %}Airport Network{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Airports Management</h1>
    <p class="page-subtitle">Panglao–Bohol International Airport (TAG) home hub and destination airports.</p>
  </div>
  <a href="/admin/airports/new" class="btn-primary"><span class="material-symbols-outlined">add</span>Add Airport</a>
</div>

<div class="card">
  <div class="card-header">
    <form class="search-bar" method="get" action="/admin/airports">
      <div class="search-input-wrap">
        <span class="material-symbols-outlined">search</span>
        <input class="form-input" name="search" value="{{ search }}" placeholder="Search by IATA code, city, name...">
      </div>
      <button class="btn-secondary" type="submit">Search</button>
      {% if search %}<a href="/admin/airports" class="btn-secondary">Clear</a>{% endif %}
    </form>
  </div>
  <div class="table-wrapper">
    <table class="admin-table">
      <thead>
        <tr>
          <th>IATA Code</th>
          <th>Airport Name</th>
          <th>City</th>
          <th>Country</th>
          <th>Type</th>
          <th style="text-align:right">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for a in airports %}
        <tr>
          <td><strong style="font-size:14px;color:var(--primary-container)">{{ a.airport_code }}</strong></td>
          <td><strong>{{ a.airport_name }}</strong></td>
          <td>{{ a.city }}</td>
          <td>{{ a.country }}</td>
          <td>
            {% if a.airport_code == 'TAG' %}
            <span class="badge badge-confirmed">HOME HUB</span>
            {% else %}
            <span class="badge badge-customer">DESTINATION</span>
            {% endif %}
          </td>
          <td style="text-align:right">
            <div style="display:flex;align-items:center;justify-content:flex-end;gap:.375rem">
              <a href="/admin/airports/{{ a.id }}/edit" class="btn-icon" title="Edit"><span class="material-symbols-outlined">edit</span></a>
              {% if a.airport_code != 'TAG' %}
              <form id="del-apt-{{ a.id }}" method="post" action="/admin/airports/{{ a.id }}/delete" style="display:inline">
                <button type="button" class="btn-icon danger" onclick="confirmDelete('del-apt-{{ a.id }}', 'Delete airport {{ a.airport_code }}?')"><span class="material-symbols-outlined">delete</span></button>
              </form>
              {% endif %}
            </div>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="6"><div class="empty-state"><h3>No airports found</h3></div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("airports/form.html", """
{% extends "base.html" %}
{% block title %}{{ 'Edit' if airport else 'New' }} Airport{% endblock %}
{% block page_title %}{{ 'Edit Airport' if airport else 'New Airport' }}{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">{{ 'Edit Airport' if airport else 'Add New Airport' }}</h1>
    <p class="page-subtitle">Configure reference airport information.</p>
  </div>
  <a href="/admin/airports" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back</a>
</div>

<div class="card" style="max-width:600px">
  <div class="card-body">
    <form method="post" action="{{ '/admin/airports/' + airport.id|string + '/edit' if airport else '/admin/airports/new' }}">
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div class="form-field">
          <label class="form-label">Airport IATA Code (3 letters) *</label>
          <input class="form-input" name="airport_code" type="text" maxlength="10" placeholder="e.g. TAG, MNL, CEB" value="{{ airport.airport_code if airport else '' }}" required style="text-transform:uppercase">
          {% if errors.airport_code %}<div class="form-error">{{ errors.airport_code }}</div>{% endif %}
        </div>
        <div class="form-field">
          <label class="form-label">Full Airport Name *</label>
          <input class="form-input" name="airport_name" type="text" placeholder="e.g. Panglao–Bohol International Airport" value="{{ airport.airport_name if airport else '' }}" required>
        </div>
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">City *</label>
            <input class="form-input" name="city" type="text" placeholder="e.g. Panglao / Tagbilaran" value="{{ airport.city if airport else '' }}" required>
          </div>
          <div class="form-field">
            <label class="form-label">Country *</label>
            <input class="form-input" name="country" type="text" placeholder="Philippines" value="{{ airport.country if airport else 'Philippines' }}" required>
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:.75rem;padding-top:.75rem;border-top:1px solid var(--surface-container)">
          <a href="/admin/airports" class="btn-secondary">Cancel</a>
          <button type="submit" class="btn-primary"><span class="material-symbols-outlined">save</span>{{ 'Update' if airport else 'Save' }} Airport</button>
        </div>
      </div>
    </form>
  </div>
</div>
{% endblock %}
""")

# 4. ROUTES
w("routes/list.html", """
{% extends "base.html" %}
{% block title %}Flight Routes{% endblock %}
{% block page_title %}Route Network{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Flight Routes</h1>
    <p class="page-subtitle">Configured origin and destination airport pairs centered on Panglao (TAG).</p>
  </div>
  <a href="/admin/routes/new" class="btn-primary"><span class="material-symbols-outlined">add</span>New Route</a>
</div>

<div class="card">
  <div class="table-wrapper">
    <table class="admin-table">
      <thead>
        <tr>
          <th>Route ID</th>
          <th>Origin Hub</th>
          <th>Destination</th>
          <th>Distance (km)</th>
          <th>Est. Duration</th>
          <th>Connected Flights</th>
          <th style="text-align:right">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for r in routes %}
        <tr>
          <td style="font-family:monospace;font-weight:700">#{{ r.id }}</td>
          <td>
            <div style="display:flex;align-items:center;gap:.5rem">
              <span class="badge badge-confirmed">{{ r.origin_airport.airport_code }}</span>
              <span>{{ r.origin_airport.city }}</span>
            </div>
          </td>
          <td>
            <div style="display:flex;align-items:center;gap:.5rem">
              <span class="badge badge-customer">{{ r.destination_airport.airport_code }}</span>
              <span>{{ r.destination_airport.city }}</span>
            </div>
          </td>
          <td><strong>{{ r.distance or '-' }} km</strong></td>
          <td>{{ r.estimated_duration.strftime('%Hh %Mm') if r.estimated_duration else '-' }}</td>
          <td><span class="badge badge-available">{{ r.flights|length }} flights</span></td>
          <td style="text-align:right">
            <form id="del-rt-{{ r.id }}" method="post" action="/admin/routes/{{ r.id }}/delete" style="display:inline">
              <button type="button" class="btn-icon danger" onclick="confirmDelete('del-rt-{{ r.id }}', 'Delete route?')"><span class="material-symbols-outlined">delete</span></button>
            </form>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="7"><div class="empty-state"><h3>No routes configured</h3></div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("routes/form.html", """
{% extends "base.html" %}
{% block title %}New Flight Route{% endblock %}
{% block page_title %}New Route{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Add Flight Route</h1>
    <p class="page-subtitle">Define an airport pair and flight characteristics.</p>
  </div>
  <a href="/admin/routes" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back</a>
</div>

<div class="card" style="max-width:640px">
  <div class="card-body">
    <form method="post" action="/admin/routes/new">
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Origin Airport *</label>
            <select class="form-input" name="origin_airport_id" required>
              {% for a in airports %}
              <option value="{{ a.id }}" {% if a.airport_code == 'TAG' %}selected{% endif %}>{{ a.airport_code }} - {{ a.city }} ({{ a.airport_name }})</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-field">
            <label class="form-label">Destination Airport *</label>
            <select class="form-input" name="destination_airport_id" required>
              {% for a in airports %}
              <option value="{{ a.id }}">{{ a.airport_code }} - {{ a.city }} ({{ a.airport_name }})</option>
              {% endfor %}
            </select>
          </div>
        </div>
        {% if errors.origin_airport_id %}<div class="form-error">{{ errors.origin_airport_id }}</div>{% endif %}

        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Flight Distance (km) *</label>
            <input class="form-input" name="distance" type="number" step="0.1" placeholder="e.g. 630" required>
          </div>
          <div class="form-field">
            <label class="form-label">Duration (Hours &amp; Minutes) *</label>
            <div style="display:flex;gap:.5rem">
              <input class="form-input" name="duration_hours" type="number" min="0" max="23" value="1" placeholder="Hours" required>
              <input class="form-input" name="duration_minutes" type="number" min="0" max="59" value="25" placeholder="Mins" required>
            </div>
          </div>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:.75rem;padding-top:.75rem;border-top:1px solid var(--surface-container)">
          <a href="/admin/routes" class="btn-secondary">Cancel</a>
          <button type="submit" class="btn-primary"><span class="material-symbols-outlined">save</span>Create Route</button>
        </div>
      </div>
    </form>
  </div>
</div>
{% endblock %}
""")

# 5. AIRPLANES & SEATS
w("airplanes/list.html", """
{% extends "base.html" %}
{% block title %}Aircraft Fleet{% endblock %}
{% block page_title %}Aircraft &amp; Fleet{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Aircraft Fleet</h1>
    <p class="page-subtitle">Commercial aircraft allocated for YPlane flight schedules.</p>
  </div>
  <a href="/admin/airplanes/new" class="btn-primary"><span class="material-symbols-outlined">add</span>Add Aircraft</a>
</div>

<div class="card">
  <div class="table-wrapper">
    <table class="admin-table">
      <thead>
        <tr>
          <th>Tail / Code</th>
          <th>Aircraft Model</th>
          <th>Type</th>
          <th>Total Physical Seats</th>
          <th>Status</th>
          <th style="text-align:right">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for ap in airplanes %}
        <tr>
          <td><strong style="font-size:14px;color:var(--primary-container)">{{ ap.airplane_code }}</strong></td>
          <td><strong>{{ ap.airplane_name }}</strong></td>
          <td>{{ ap.airplane_type }}</td>
          <td>
            <span style="font-weight:600">{{ ap.total_seats }} seats</span>
            <span style="font-size:11px;color:var(--secondary)">({{ ap.seats|length }} registered)</span>
          </td>
          <td>
            {% if ap.status == 'ACTIVE' %}
            <span class="badge badge-confirmed">ACTIVE</span>
            {% elif ap.status == 'MAINTENANCE' %}
            <span class="badge badge-pending">MAINTENANCE</span>
            {% else %}
            <span class="badge badge-rejected">INACTIVE</span>
            {% endif %}
          </td>
          <td style="text-align:right">
            <div style="display:flex;align-items:center;justify-content:flex-end;gap:.375rem">
              <a href="/admin/airplanes/{{ ap.id }}/seats" class="btn-secondary" style="height:30px;font-size:11px;padding:0 8px">
                <span class="material-symbols-outlined" style="font-size:14px">event_seat</span> Seat Layout
              </a>
              <form id="del-plane-{{ ap.id }}" method="post" action="/admin/airplanes/{{ ap.id }}/delete" style="display:inline">
                <button type="button" class="btn-icon danger" onclick="confirmDelete('del-plane-{{ ap.id }}', 'Delete aircraft {{ ap.airplane_code }}?')"><span class="material-symbols-outlined">delete</span></button>
              </form>
            </div>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="6"><div class="empty-state"><h3>No aircraft in fleet</h3></div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("airplanes/form.html", """
{% extends "base.html" %}
{% block title %}Add Aircraft{% endblock %}
{% block page_title %}New Aircraft{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Add Aircraft to Fleet</h1>
    <p class="page-subtitle">Configure aircraft specifications and auto-generate seat inventory.</p>
  </div>
  <a href="/admin/airplanes" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back</a>
</div>

<div class="card" style="max-width:640px">
  <div class="card-body">
    <form method="post" action="/admin/airplanes/new">
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Tail / Aircraft Code *</label>
            <input class="form-input" name="airplane_code" type="text" placeholder="e.g. RP-C8820" required style="text-transform:uppercase">
            {% if errors.airplane_code %}<div class="form-error">{{ errors.airplane_code }}</div>{% endif %}
          </div>
          <div class="form-field">
            <label class="form-label">Status *</label>
            <select class="form-input" name="status">
              <option value="ACTIVE">ACTIVE</option>
              <option value="MAINTENANCE">MAINTENANCE</option>
              <option value="INACTIVE">INACTIVE</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Aircraft Name / Model *</label>
            <input class="form-input" name="airplane_name" type="text" placeholder="e.g. Airbus A320-200" required>
          </div>
          <div class="form-field">
            <label class="form-label">Aircraft Category *</label>
            <input class="form-input" name="airplane_type" type="text" placeholder="e.g. Narrow-body Jet / Turboprop" required>
          </div>
        </div>

        <div class="card" style="background:var(--surface-container-low);padding:1rem">
          <div class="card-title" style="font-size:13px;margin-bottom:0.75rem"><span class="material-symbols-outlined">event_seat</span>Seat Configuration</div>
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">Number of Rows</label>
              <input class="form-input" name="rows" type="number" min="5" max="60" value="20" required>
            </div>
            <div class="form-field">
              <label class="form-label">Columns (Letters comma-separated)</label>
              <input class="form-input" name="cols" type="text" value="A,B,C,D,E,F" placeholder="A,B,C,D,E,F" required>
            </div>
          </div>
          <div class="form-help">Rows 1-2 will be tagged as Business, 3-4 as Premium, and the rest as Economy.</div>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:.75rem;padding-top:.75rem;border-top:1px solid var(--surface-container)">
          <a href="/admin/airplanes" class="btn-secondary">Cancel</a>
          <button type="submit" class="btn-primary"><span class="material-symbols-outlined">save</span>Add Aircraft &amp; Generate Seats</button>
        </div>
      </div>
    </form>
  </div>
</div>
{% endblock %}
""")

w("airplanes/seats.html", """
{% extends "base.html" %}
{% block title %}Seats — {{ airplane.airplane_code }}{% endblock %}
{% block page_title %}Aircraft Seat Inventory{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">{{ airplane.airplane_name }} ({{ airplane.airplane_code }})</h1>
    <p class="page-subtitle">Physical seat inventory ({{ seats|length }} total seats registered).</p>
  </div>
  <a href="/admin/airplanes" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back to Aircraft</a>
</div>

<div class="card">
  <div class="card-header">
    <div class="card-title"><span class="material-symbols-outlined">event_seat</span>Physical Cabin Seat Map</div>
    <div style="display:flex;gap:.5rem">
      <span class="badge" style="background:#e0e7ff;color:#3730a3">Business</span>
      <span class="badge" style="background:#fef3c7;color:#92400e">Premium</span>
      <span class="badge" style="background:#f1f5f9;color:#475569">Economy</span>
    </div>
  </div>
  <div class="card-body">
    <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(70px, 1fr));gap:0.5rem">
      {% for s in seats %}
      <div style="border:1px solid #e2e8f0;border-radius:6px;padding:6px;text-align:center;background:{% if s.seat_type == 'BUSINESS' %}#e0e7ff{% elif s.seat_type == 'PREMIUM' %}#fef3c7{% else %}#ffffff{% endif %}">
        <div style="font-weight:700;font-size:13px">{{ s.seat_number }}</div>
        <div style="font-size:9px;color:#64748b">{{ s.seat_position }}</div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
""")

# 6. FLIGHTS
w("flights/list.html", """
{% extends "base.html" %}
{% block title %}Flight Operations{% endblock %}
{% block page_title %}Flights Management{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Scheduled Flights</h1>
    <p class="page-subtitle">Flight schedule catalog centered on Panglao–Bohol International Airport (TAG).</p>
  </div>
  <a href="/admin/flights/new" class="btn-primary"><span class="material-symbols-outlined">add</span>Schedule Flight</a>
</div>

<div class="card">
  <div class="card-header">
    <form class="search-bar" method="get" action="/admin/flights">
      <div class="search-input-wrap">
        <span class="material-symbols-outlined">search</span>
        <input class="form-input" name="search" value="{{ search }}" placeholder="Search flight #, aircraft...">
      </div>
      <button class="btn-secondary" type="submit">Search</button>
      {% if search %}<a href="/admin/flights" class="btn-secondary">Clear</a>{% endif %}
    </form>
  </div>
  <div class="table-wrapper">
    <table class="admin-table">
      <thead>
        <tr>
          <th>Flight #</th>
          <th>Route</th>
          <th>Aircraft</th>
          <th>Date</th>
          <th>Departure / Arrival</th>
          <th>Fare</th>
          <th>Seat Availability</th>
          <th>Status</th>
          <th style="text-align:right">Actions</th>
        </tr>
      </thead>
      <tbody>
        {% for item in flights %}
        {% set f = item.flight %}
        <tr>
          <td>
            <a href="/admin/flights/{{ f.id }}" style="font-weight:700;font-size:13px;color:var(--primary-container)">
              {{ f.flight_number }}
            </a>
          </td>
          <td>
            <strong>{{ f.route.origin_airport.airport_code }} → {{ f.route.destination_airport.airport_code }}</strong><br>
            <span class="form-help">{{ f.route.origin_airport.city }} to {{ f.route.destination_airport.city }}</span>
          </td>
          <td>
            <strong>{{ f.airplane.airplane_code }}</strong><br>
            <span class="form-help">{{ f.airplane.airplane_name }}</span>
          </td>
          <td>{{ f.departure_date.strftime('%b %d, %Y') }}</td>
          <td>
            <strong>{{ f.departure_time.strftime('%H:%M') }}</strong> - {{ f.arrival_time.strftime('%H:%M') }}
          </td>
          <td><strong style="color:var(--primary-container)">₱{{ '%.2f'|format(f.fare) }}</strong></td>
          <td>
            <span style="font-weight:600;color:{% if item.available_seats == 0 %}#dc2626{% elif item.available_seats <= 5 %}#d97706{% else %}#16a34a{% endif %}">
              {{ item.available_seats }}
            </span>
            <span style="color:var(--secondary)"> / {{ item.total_seats }}</span>
            <div class="progress-bar" style="max-width:80px;margin-top:3px">
              <div class="progress-fill" style="width:{{ ((item.available_seats / item.total_seats) * 100)|int if item.total_seats > 0 else 0 }}%"></div>
            </div>
          </td>
          <td><span class="badge badge-{{ f.status.lower() }}">{{ f.status }}</span></td>
          <td style="text-align:right">
            <div style="display:flex;align-items:center;justify-content:flex-end;gap:.375rem">
              <a href="/admin/flights/{{ f.id }}" class="btn-icon" title="View Seat Map &amp; Details"><span class="material-symbols-outlined">event_seat</span></a>
              <form id="del-fl-{{ f.id }}" method="post" action="/admin/flights/{{ f.id }}/delete" style="display:inline">
                <button type="button" class="btn-icon danger" onclick="confirmDelete('del-fl-{{ f.id }}', 'Delete flight {{ f.flight_number }}?')"><span class="material-symbols-outlined">delete</span></button>
              </form>
            </div>
          </td>
        </tr>
        {% else %}
        <tr><td colspan="9"><div class="empty-state"><h3>No flights scheduled</h3></div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("flights/form.html", """
{% extends "base.html" %}
{% block title %}Schedule Flight{% endblock %}
{% block page_title %}New Flight{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Schedule New Flight</h1>
    <p class="page-subtitle">Publish a flight on the YPlane reservation network.</p>
  </div>
  <a href="/admin/flights" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back</a>
</div>

<div class="card" style="max-width:680px">
  <div class="card-body">
    <form method="post" action="/admin/flights/new">
      <div style="display:flex;flex-direction:column;gap:1.25rem">
        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Flight Number *</label>
            <input class="form-input" name="flight_number" type="text" placeholder="e.g. YP-105" required style="text-transform:uppercase">
          </div>
          <div class="form-field">
            <label class="form-label">Flight Status *</label>
            <select class="form-input" name="status">
              <option value="SCHEDULED">SCHEDULED</option>
              <option value="BOARDING">BOARDING</option>
              <option value="COMPLETED">COMPLETED</option>
              <option value="CANCELLED">CANCELLED</option>
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Route *</label>
            <select class="form-input" name="route_id" required>
              {% for r in routes %}
              <option value="{{ r.id }}">{{ r.origin_airport.airport_code }} ({{ r.origin_airport.city }}) → {{ r.destination_airport.airport_code }} ({{ r.destination_airport.city }})</option>
              {% endfor %}
            </select>
          </div>
          <div class="form-field">
            <label class="form-label">Aircraft *</label>
            <select class="form-input" name="airplane_id" required>
              {% for ap in airplanes %}
              <option value="{{ ap.id }}">{{ ap.airplane_code }} — {{ ap.airplane_name }} ({{ ap.total_seats }} seats)</option>
              {% endfor %}
            </select>
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Departure Date *</label>
            <input class="form-input" name="departure_date" type="date" required>
          </div>
          <div class="form-field">
            <label class="form-label">Ticket Fare (₱) *</label>
            <input class="form-input" name="fare" type="number" step="0.01" min="1" placeholder="3500.00" required>
          </div>
        </div>

        <div class="form-row">
          <div class="form-field">
            <label class="form-label">Departure Time *</label>
            <input class="form-input" name="departure_time" type="time" required>
          </div>
          <div class="form-field">
            <label class="form-label">Arrival Time *</label>
            <input class="form-input" name="arrival_time" type="time" required>
          </div>
        </div>

        <div style="display:flex;justify-content:flex-end;gap:.75rem;padding-top:.75rem;border-top:1px solid var(--surface-container)">
          <a href="/admin/flights" class="btn-secondary">Cancel</a>
          <button type="submit" class="btn-primary"><span class="material-symbols-outlined">save</span>Publish Flight</button>
        </div>
      </div>
    </form>
  </div>
</div>
{% endblock %}
""")

w("flights/detail.html", """
{% extends "base.html" %}
{% block title %}Flight {{ flight.flight_number }}{% endblock %}
{% block page_title %}Flight Details &amp; Seat Map{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Flight {{ flight.flight_number }}</h1>
    <p class="page-subtitle">{{ flight.route.origin_airport.airport_name }} ({{ flight.route.origin_airport.airport_code }}) → {{ flight.route.destination_airport.airport_name }} ({{ flight.route.destination_airport.airport_code }})</p>
  </div>
  <a href="/admin/flights" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back</a>
</div>

<div class="stat-grid" style="grid-template-columns:repeat(4, 1fr);margin-bottom:1.5rem">
  <div class="stat-card">
    <div class="stat-label">Departure Date &amp; Time</div>
    <div class="stat-value" style="font-size:18px">{{ flight.departure_date.strftime('%b %d, %Y') }}</div>
    <div class="stat-sub">{{ flight.departure_time.strftime('%H:%M') }} → {{ flight.arrival_time.strftime('%H:%M') }}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Assigned Aircraft</div>
    <div class="stat-value" style="font-size:18px">{{ flight.airplane.airplane_code }}</div>
    <div class="stat-sub">{{ flight.airplane.airplane_name }}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Available Seats</div>
    <div class="stat-value" style="color:#16a34a">{{ available_count }}</div>
    <div class="stat-sub">out of {{ seats|length }} total seats</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Base Fare</div>
    <div class="stat-value" style="color:var(--primary-container)">₱{{ '%.2f'|format(flight.fare) }}</div>
    <div class="stat-sub">Status: {{ flight.status }}</div>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <div>
      <h2 class="card-title"><span class="material-symbols-outlined">event_seat</span>Live Flight Seat Map (Dynamic Availability)</h2>
      <p class="card-caption">Green = Available · Red = Reserved/Booked through sequential queue</p>
    </div>
    <div style="display:flex;gap:0.75rem">
      <span class="badge badge-confirmed"><span class="material-symbols-outlined">check_circle</span>{{ available_count }} Available</span>
      <span class="badge badge-rejected"><span class="material-symbols-outlined">cancel</span>{{ booked_count }} Reserved</span>
    </div>
  </div>
  <div class="card-body">
    <div style="display:grid;grid-template-columns:repeat(auto-fill, minmax(65px, 1fr));gap:0.5rem">
      {% for s in seats %}
      <div style="border:1px solid {% if s.is_available %}#86efac{% else %}#fca5a5{% endif %};border-radius:6px;padding:6px;text-align:center;background:{% if s.is_available %}#f0fdf4{% else %}#fef2f2{% endif %}">
        <div style="font-weight:700;font-size:13px;color:{% if s.is_available %}#16a34a{% else %}#dc2626{% endif %}">{{ s.seat_number }}</div>
        <div style="font-size:9px;color:#64748b">{{ s.seat_position }}</div>
        <div style="font-size:8px;font-weight:600;margin-top:2px;color:{% if s.is_available %}#16a34a{% else %}#dc2626{% endif %}">
          {{ 'AVAIL' if s.is_available else 'BOOKED' }}
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
""")

# 7. BOOKINGS & PAYMENTS
w("bookings/list.html", """
{% extends "base.html" %}
{% block title %}Bookings{% endblock %}
{% block page_title %}Customer Bookings{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Flight Bookings</h1>
    <p class="page-subtitle">All customer flight reservations. {{ bookings|length }} record(s) found.</p>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <form class="search-bar" method="get" action="/admin/bookings">
      <div class="search-input-wrap">
        <span class="material-symbols-outlined">search</span>
        <input class="form-input" name="search" value="{{ search }}" placeholder="Search ref, passenger, flight...">
      </div>
      <select class="form-input" name="status_filter" style="width:160px" onchange="this.form.submit()">
        <option value="">All Statuses</option>
        {% for s in statuses %}
        <option value="{{ s }}" {% if status_filter == s %}selected{% endif %}>{{ s }}</option>
        {% endfor %}
      </select>
      <button class="btn-secondary" type="submit">Filter</button>
      {% if search or status_filter %}<a href="/admin/bookings" class="btn-secondary">Clear</a>{% endif %}
    </form>
  </div>
  <div class="table-wrapper">
    <table class="admin-table">
      <thead>
        <tr>
          <th>Booking Reference</th>
          <th>Passenger</th>
          <th>Flight</th>
          <th>Route</th>
          <th>Seat(s)</th>
          <th>Total Amount</th>
          <th>Status</th>
          <th>Booked At</th>
          <th style="text-align:right">Action</th>
        </tr>
      </thead>
      <tbody>
        {% for b in bookings %}
        <tr>
          <td><a href="/admin/bookings/{{ b.id }}" style="font-family:monospace;font-weight:700;color:var(--primary-container)">{{ b.booking_reference }}</a></td>
          <td>
            <div class="user-cell">
              <span class="user-avatar">{{ (b.user.name if b.user else 'P')[0].upper() }}</span>
              <span>
                <strong>{{ b.user.name if b.user else '-' }}</strong>
                <small>{{ b.user.email if b.user else '' }}</small>
              </span>
            </div>
          </td>
          <td><strong>{{ b.flight.flight_number if b.flight else '-' }}</strong></td>
          <td>{{ b.flight.route.origin_airport.airport_code }} → {{ b.flight.route.destination_airport.airport_code }}</td>
          <td style="font-family:monospace;font-weight:600">
            {% for bs in b.booking_seats %}
            <span class="seat-chip" style="padding:2px 6px">{{ bs.seat.seat_number }}</span>
            {% else %}
            -
            {% endfor %}
          </td>
          <td><strong style="color:var(--primary-container)">₱{{ '%.2f'|format(b.total_amount) }}</strong></td>
          <td><span class="badge badge-{{ b.status.lower() }}">{{ b.status }}</span></td>
          <td style="font-size:11px;font-family:monospace;color:var(--secondary)">{{ b.booked_at.strftime('%b %d, %H:%M:%S') }}</td>
          <td style="text-align:right"><a href="/admin/bookings/{{ b.id }}" class="btn-icon" title="View"><span class="material-symbols-outlined">visibility</span></a></td>
        </tr>
        {% else %}
        <tr><td colspan="9"><div class="empty-state"><h3>No bookings found</h3></div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("bookings/detail.html", """
{% extends "base.html" %}
{% block title %}Booking {{ booking.booking_reference }}{% endblock %}
{% block page_title %}Booking Details{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Booking {{ booking.booking_reference }}</h1>
    <p class="page-subtitle">Submitted on {{ booking.booked_at.strftime('%B %d, %Y at %H:%M:%S') }}</p>
  </div>
  <div class="page-header-actions">
    <a href="/admin/bookings" class="btn-secondary"><span class="material-symbols-outlined">arrow_back</span>Back</a>
    {% if booking.status in ['PENDING', 'CONFIRMED'] %}
    <form id="cancel-booking-form" method="post" action="/admin/bookings/{{ booking.id }}/cancel" style="display:inline">
      <button type="button" class="btn-danger" onclick="confirmAction('cancel-booking-form', 'Cancel booking {{ booking.booking_reference }} and release its seat?')">
        <span class="material-symbols-outlined">cancel</span>Cancel Booking (Admin Override)
      </button>
    </form>
    {% endif %}
  </div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
  <div class="card">
    <div class="card-header"><h2 class="card-title"><span class="material-symbols-outlined">info</span>Passenger &amp; Reservation Details</h2></div>
    <div class="card-body">
      <div class="detail-grid">
        <div class="detail-label">Reference</div>
        <div class="detail-value" style="font-family:monospace;font-weight:700;font-size:15px">{{ booking.booking_reference }}</div>

        <div class="detail-label">Status</div>
        <div class="detail-value"><span class="badge badge-{{ booking.status.lower() }}">{{ booking.status }}</span></div>

        <div class="detail-label">Passenger</div>
        <div class="detail-value">{{ booking.user.name if booking.user else '-' }}</div>

        <div class="detail-label">Email</div>
        <div class="detail-value">{{ booking.user.email if booking.user else '-' }}</div>

        <div class="detail-label">Flight</div>
        <div class="detail-value"><strong>{{ booking.flight.flight_number }}</strong> ({{ booking.flight.route.origin_airport.airport_code }} → {{ booking.flight.route.destination_airport.airport_code }})</div>

        <div class="detail-label">Departure</div>
        <div class="detail-value">{{ booking.flight.departure_date.strftime('%b %d, %Y') }} at {{ booking.flight.departure_time.strftime('%H:%M') }}</div>

        <div class="detail-label">Reserved Seat(s)</div>
        <div class="detail-value" style="font-family:monospace;font-weight:700;color:var(--primary-container)">
          {% for bs in booking.booking_seats %}
            {{ bs.seat.seat_number }} ({{ bs.seat.seat_type }})
          {% else %}
            No seat assigned
          {% endfor %}
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header"><h2 class="card-title"><span class="material-symbols-outlined">receipt_long</span>Payment &amp; Transaction Details</h2></div>
    <div class="card-body">
      {% if booking.payment %}
      <div class="detail-grid">
        <div class="detail-label">Transaction Ref</div>
        <div class="detail-value" style="font-family:monospace;font-weight:700">{{ booking.payment.transaction_reference }}</div>

        <div class="detail-label">Amount Paid</div>
        <div class="detail-value" style="font-size:20px;font-weight:700;color:var(--primary-container)">₱{{ '%.2f'|format(booking.payment.amount) }}</div>

        <div class="detail-label">Method</div>
        <div class="detail-value">{{ booking.payment.payment_method }}</div>

        <div class="detail-label">Payment Status</div>
        <div class="detail-value"><span class="badge badge-{{ booking.payment.status.lower() }}">{{ booking.payment.status }}</span></div>

        <div class="detail-label">Timestamp</div>
        <div class="detail-value" style="font-size:12px;font-family:monospace">{{ booking.payment.paid_at.strftime('%Y-%m-%d %H:%M:%S') if booking.payment.paid_at else '-' }}</div>
      </div>
      {% else %}
      <div class="empty-state"><h3>No payment record</h3></div>
      {% endif %}
    </div>
  </div>
</div>
{% endblock %}
""")

w("payments/list.html", """
{% extends "base.html" %}
{% block title %}Payments{% endblock %}
{% block page_title %}Financial Transactions{% endblock %}

{% block content %}
<div class="page-header">
  <div>
    <h1 class="page-title">Payment Transactions</h1>
    <p class="page-subtitle">Simulated payment records tied to flight reservations. {{ payments|length }} record(s).</p>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <form class="search-bar" method="get" action="/admin/payments">
      <div class="search-input-wrap">
        <span class="material-symbols-outlined">search</span>
        <input class="form-input" name="search" value="{{ search }}" placeholder="Search transaction ref, booking ref...">
      </div>
      <button class="btn-secondary" type="submit">Search</button>
      {% if search %}<a href="/admin/payments" class="btn-secondary">Clear</a>{% endif %}
    </form>
  </div>
  <div class="table-wrapper">
    <table class="admin-table">
      <thead>
        <tr>
          <th>Transaction Ref</th>
          <th>Booking Reference</th>
          <th>Passenger</th>
          <th>Amount</th>
          <th>Payment Method</th>
          <th>Status</th>
          <th>Paid At</th>
        </tr>
      </thead>
      <tbody>
        {% for p in payments %}
        <tr>
          <td style="font-family:monospace;font-weight:700;color:var(--primary-container)">{{ p.transaction_reference }}</td>
          <td><a href="/admin/bookings/{{ p.booking_id }}" style="font-family:monospace;font-weight:600">{{ p.booking.booking_reference if p.booking else '-' }}</a></td>
          <td>{{ p.booking.user.name if p.booking and p.booking.user else '-' }}</td>
          <td><strong style="font-size:14px">₱{{ '%.2f'|format(p.amount) }}</strong></td>
          <td>{{ p.payment_method }}</td>
          <td><span class="badge badge-{{ p.status.lower() }}">{{ p.status }}</span></td>
          <td style="font-size:11px;font-family:monospace;color:var(--secondary)">{{ p.paid_at.strftime('%b %d, %Y %H:%M:%S') if p.paid_at else '-' }}</td>
        </tr>
        {% else %}
        <tr><td colspan="7"><div class="empty-state"><h3>No payments recorded yet</h3></div></td></tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

# 8. QUEUE MONITOR & TABLE PARTIAL
w("queue/monitor.html", """
{% extends "base.html" %}
{% block title %}Live Booking Logs Monitor{% endblock %}
{% block page_title %}Sequential Processing Monitor{% endblock %}

{% block content %}
<div class="page-header queue-header">
  <div>
    <div class="title-row">
      <h1 class="page-title">Live Sequential Processing Monitor</h1>
      <span class="mode-chip">FIFO Guarantee</span>
    </div>
    <p class="page-subtitle">Real-time auditable stream from <code>booking_logs</code> table. Strictly serialized single-worker execution.</p>
  </div>
  <div class="page-header-actions queue-actions">
    <span class="sync-status"><span class="queue-live-dot"></span>Auto-refreshing <small>350 ms</small></span>
    <form method="post" action="/admin/queue/demo-2-for-1" style="display:inline">
      <button type="submit" class="btn-secondary">
        <span class="material-symbols-outlined">play_arrow</span>Run 2-for-1 Warm-up
      </button>
    </form>
    <form method="post" action="/admin/queue/demo-5-for-1" style="display:inline">
      <button type="submit" class="btn-primary">
        <span class="material-symbols-outlined">bolt</span>Run 5-Customers-1-Seat Demo
      </button>
    </form>
  </div>
</div>

<div class="stat-grid queue-stats">
  <div class="stat-card">
    <div class="stat-top"><span class="stat-label">Total Requests Logged</span><span class="stat-icon"><span class="material-symbols-outlined">sync</span></span></div>
    <div><span class="stat-value">{{ total_logs }}</span><span class="trend-up stat-delta">↗ live</span></div>
    <div class="stat-sub">Auditable records in booking_logs</div>
  </div>

  <div class="stat-card">
    <div class="stat-top"><span class="stat-label">Sequential Queue Depth</span><span class="stat-icon"><span class="material-symbols-outlined">timer</span></span></div>
    <div><span class="stat-value">{{ queue_depth }}</span><span class="stat-unit"> requests</span></div>
    <div class="stat-sub">Single dedicated thread worker</div>
  </div>

  <div class="stat-card">
    <div class="stat-top"><span class="stat-label">Confirmed (SUCCESS)</span><span class="stat-icon"><span class="material-symbols-outlined">verified</span></span></div>
    <div><span class="stat-value" style="color:#16a34a">{{ success_count }}</span></div>
    <div class="stat-sub">Atomic lock acquired &amp; confirmed</div>
  </div>

  <div class="stat-card stat-card-alert">
    <div class="stat-top"><span class="stat-label">Prevented (REJECTED)</span><span class="material-symbols-outlined alert-icon">warning</span></div>
    <div><span class="stat-value" style="color:#dc2626">{{ rejected_count }}</span></div>
    <div class="stat-sub">{{ rejected_count }} double-booking conflicts prevented</div>
  </div>
</div>

<div class="card queue-card">
  <div class="card-header queue-toolbar">
    <div class="filter-chips">
      <span class="toolbar-label">Audit Log</span>
      <button class="filter-chip active">All Events ({{ total_logs }})</button>
      <button class="filter-chip">Success ({{ success_count }})</button>
      <button class="filter-chip">Rejected ({{ rejected_count }})</button>
    </div>
    <span class="stream-meta"><span class="queue-live-dot"></span>Hub Engine: Panglao–Bohol (TAG)</span>
  </div>
  <div class="table-wrapper">
    <table class="admin-table queue-table">
      <thead>
        <tr>
          <th>Log # / Action</th>
          <th>Passenger</th>
          <th>Processing Type</th>
          <th>Result Status</th>
          <th>Message / Evidence</th>
          <th>Started At</th>
          <th>Completed At</th>
        </tr>
      </thead>
      <tbody id="queue-rows" hx-get="/admin/queue/table" hx-trigger="load, every 400ms" hx-swap="innerHTML">
        {% include "queue/table_partial.html" %}
      </tbody>
    </table>
  </div>
</div>
{% endblock %}
""")

w("queue/table_partial.html", """
{% for log in logs %}
<tr>
  <td>
    <div class="request-type">
      <span class="request-badge">{{ log.action }}</span>
      <small>#{{ log.id }}</small>
    </div>
  </td>
  <td>
    <div class="user-cell">
      <span class="user-avatar">{{ (log.user.name if log.user else 'P')[0].upper() }}</span>
      <span>
        <strong>{{ log.user.name if log.user else ('User #' ~ log.user_id) }}</strong>
        <small>{{ log.user.email if log.user else '' }}</small>
      </span>
    </div>
  </td>
  <td>
    <span class="badge" style="background:#f0fdfa;color:#0f766e;font-weight:600">
      <span class="material-symbols-outlined" style="font-size:12px">swap_vert</span>{{ log.processing_type }}
    </span>
  </td>
  <td>
    <span class="badge badge-{{ log.status.lower() }}">
      <span class="material-symbols-outlined">{{ 'check_circle' if log.status == 'SUCCESS' else ('cancel' if log.status == 'REJECTED' else 'error') }}</span>
      {{ log.status }}
    </span>
  </td>
  <td>
    <div style="font-size:12px;font-weight:500;color:var(--on-surface)">
      {{ log.message or 'No message' }}
    </div>
  </td>
  <td>
    <strong class="time-value">{{ log.started_at.strftime('%H:%M:%S.%f')[:-3] }}</strong>
    <small class="time-sub">Received</small>
  </td>
  <td>
    <strong class="time-value">{{ log.completed_at.strftime('%H:%M:%S.%f')[:-3] if log.completed_at else 'Processing...' }}</strong>
    <small class="time-sub">{{ 'Completed' if log.completed_at else 'In-flight' }}</small>
  </td>
</tr>
{% else %}
<tr>
  <td colspan="7">
    <div class="empty-state" style="padding:2.5rem">
      <h3>Booking logs empty</h3>
      <p>Click "Run 5-Customers-1-Seat Demo" above to witness strict sequential processing.</p>
    </div>
  </td>
</tr>
{% endfor %}
""")

print("All YPlane templates successfully created!")

