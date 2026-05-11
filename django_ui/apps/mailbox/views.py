from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .grpc_client import TurboMessageClient


def home(request: HttpRequest) -> HttpResponse:
    client = TurboMessageClient()
    context = {
        "title": "TurboMessage",
        "status": client.health_status(),
    }
    return render(request, "mailbox/home.html", context)
