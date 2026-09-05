from datetime import timedelta
from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, decode_token, verify_password
from app.models import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("admin_token")
    if token:
        payload = decode_token(token)
        if payload and str(payload.get("role", "")).upper() == "ADMIN":
            return RedirectResponse("/admin/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request, "error": None})


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    remember: bool = Form(False),
    db: Session = Depends(get_db),
):
    clean_email = email.strip().lower()
    user = db.query(User).filter(User.email.ilike(clean_email)).first()
    
    pwd_valid = False
    if user:
        if user.password and verify_password(password, user.password):
            pwd_valid = True
        elif user.password_hash and verify_password(password, user.password_hash):
            pwd_valid = True

    if not user or str(user.role).upper() != "ADMIN" or not user.is_active or not pwd_valid:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Invalid administrator credentials."},
            status_code=401,
        )
    lifetime = timedelta(days=30) if remember else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        {"sub": str(user.id), "name": user.name, "email": user.email, "role": "ADMIN"},
        expires_delta=lifetime,
    )
    response = RedirectResponse("/admin/dashboard", status_code=303)
    response.set_cookie(
        "admin_token", token, max_age=int(lifetime.total_seconds()), httponly=True,
        secure=request.url.scheme == "https", samesite="lax",
    )
    return response


@router.post("/logout")
@router.get("/logout")
async def logout():
    response = RedirectResponse("/auth/login", status_code=303)
    response.delete_cookie("admin_token")
    return response
