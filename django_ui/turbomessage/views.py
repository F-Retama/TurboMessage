from __future__ import annotations

from functools import wraps
from typing import Callable

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .grpc_client import TurboMessageClient

SESSION_USER_ID = "tm_user_id"
SESSION_USERNAME = "tm_username"
FLASH_KEY = "tm_flash"


def _current_user(request: HttpRequest) -> dict | None:
    user_id = request.session.get(SESSION_USER_ID, "")
    username = request.session.get(SESSION_USERNAME, "")
    if user_id and username:
        return {"id": user_id, "username": username}
    return None


def _set_flash(request: HttpRequest, message: str, level: str = "info") -> None:
    request.session[FLASH_KEY] = {"message": message, "level": level}


def _pop_flash(request: HttpRequest) -> dict | None:
    return request.session.pop(FLASH_KEY, None)


def _render(request: HttpRequest, template: str, context: dict) -> HttpResponse:
    base = {
        "current_user": _current_user(request),
        "flash": _pop_flash(request),
    }
    base.update(context)
    return render(request, template, base)


def _email_to_dict(email) -> dict:
    return {
        "id": int(email.id),
        "sender_id": email.sender_id,
        "recipient_id": email.recipient_id,
        "subject": email.subject,
        "body": email.body,
        "is_read": bool(email.is_read),
    }


def require_login(view_func: Callable) -> Callable:
    @wraps(view_func)
    def _wrapped(request: HttpRequest, *args, **kwargs):
        if not _current_user(request):
            _set_flash(request, "Inicia sesion para continuar.", "warning")
            return redirect("turbomessage_login")
        return view_func(request, *args, **kwargs)

    return _wrapped


def index(request: HttpRequest) -> HttpResponse:
    if _current_user(request):
        return redirect("turbomessage_dashboard")
    return redirect("turbomessage_login")


def register_view(request: HttpRequest) -> HttpResponse:
    if _current_user(request):
        return redirect("turbomessage_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if not username or not password:
            _set_flash(request, "Username y password son obligatorios.", "error")
            return redirect("turbomessage_register")

        client = TurboMessageClient()
        response = client.register(username, password)
        if response.result.ok:
            request.session[SESSION_USER_ID] = response.user_id
            request.session[SESSION_USERNAME] = username
            _set_flash(request, "Registro exitoso. Bienvenido.", "success")
            return redirect("turbomessage_dashboard")

        _set_flash(request, response.result.message, "error")
        return redirect("turbomessage_register")

    return _render(
        request,
        "turbomessage/auth_form.html",
        {
            "title": "Registro",
            "submit_label": "Crear cuenta",
            "switch_label": "Ya tienes cuenta?",
            "switch_href": "turbomessage_login",
            "switch_text": "Iniciar sesion",
        },
    )


def login_view(request: HttpRequest) -> HttpResponse:
    if _current_user(request):
        return redirect("turbomessage_dashboard")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()
        if not username or not password:
            _set_flash(request, "Username y password son obligatorios.", "error")
            return redirect("turbomessage_login")

        client = TurboMessageClient()
        response = client.login(username, password)
        if response.result.ok:
            request.session[SESSION_USER_ID] = response.user_id
            request.session[SESSION_USERNAME] = username
            _set_flash(request, "Sesion iniciada.", "success")
            return redirect("turbomessage_dashboard")

        _set_flash(request, response.result.message, "error")
        return redirect("turbomessage_login")

    return _render(
        request,
        "turbomessage/auth_form.html",
        {
            "title": "Iniciar sesion",
            "submit_label": "Entrar",
            "switch_label": "No tienes cuenta?",
            "switch_href": "turbomessage_register",
            "switch_text": "Registrarme",
        },
    )


@require_login
def logout_view(request: HttpRequest) -> HttpResponse:
    request.session.pop(SESSION_USER_ID, None)
    request.session.pop(SESSION_USERNAME, None)
    _set_flash(request, "Sesion cerrada.", "info")
    return redirect("turbomessage_login")


@require_login
def dashboard_view(request: HttpRequest) -> HttpResponse:
    user = _current_user(request)
    assert user is not None

    client = TurboMessageClient()
    response = client.list_emails(user["id"])
    if not response.result.ok:
        _set_flash(request, response.result.message, "error")
        return _render(
            request,
            "turbomessage/index.html",
            {"inbox": [], "outbox": []},
        )

    all_emails = [_email_to_dict(email) for email in response.emails]
    inbox = [email for email in all_emails if email["recipient_id"] == user["id"]]
    outbox = [email for email in all_emails if email["sender_id"] == user["id"]]

    return _render(
        request,
        "turbomessage/index.html",
        {
            "inbox": inbox,
            "outbox": outbox,
        },
    )


@require_login
def compose_view(request: HttpRequest) -> HttpResponse:
    user = _current_user(request)
    assert user is not None

    if request.method == "POST":
        recipient_id = request.POST.get("recipient_id", "").strip()
        subject = request.POST.get("subject", "").strip()
        body = request.POST.get("body", "").strip()

        if not recipient_id or not subject or not body:
            _set_flash(request, "Completa todos los campos.", "error")
            return redirect("turbomessage_compose")

        client = TurboMessageClient()
        response = client.send_email(
            sender_id=user["id"],
            recipient_id=recipient_id,
            subject=subject,
            body=body,
        )
        if response.result.ok:
            _set_flash(request, f"Correo enviado (ID {response.id}).", "success")
            return redirect("turbomessage_dashboard")

        _set_flash(request, response.result.message, "error")
        return redirect("turbomessage_compose")

    return _render(request, "turbomessage/compose.html", {})


@require_login
def email_detail_view(request: HttpRequest, email_id: int) -> HttpResponse:
    user = _current_user(request)
    assert user is not None

    client = TurboMessageClient()
    response = client.read_email(user_id=user["id"], email_id=email_id)
    if not response.result.ok:
        _set_flash(request, response.result.message, "error")
        return redirect("turbomessage_dashboard")

    email = _email_to_dict(response.email)
    return _render(
        request,
        "turbomessage/email_detail.html",
        {
            "email": email,
            "is_sender": email["sender_id"] == user["id"],
            "is_recipient": email["recipient_id"] == user["id"],
        },
    )


@require_login
def delete_email_view(request: HttpRequest, email_id: int) -> HttpResponse:
    if request.method != "POST":
        return redirect("turbomessage_dashboard")

    user = _current_user(request)
    assert user is not None

    client = TurboMessageClient()
    response = client.delete_email(user_id=user["id"], email_id=email_id)
    _set_flash(
        request,
        response.result.message,
        "success" if response.result.ok else "error",
    )
    return redirect("turbomessage_dashboard")
