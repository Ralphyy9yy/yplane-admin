from sqlalchemy import text
from app.core.database import engine

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(20) USING role::text;"))
    conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE role ILIKE 'admin';"))
    conn.execute(text("UPDATE users SET role = 'CUSTOMER' WHERE role ILIKE 'customer';"))
print("Converted users.role to VARCHAR(20) successfully.")
