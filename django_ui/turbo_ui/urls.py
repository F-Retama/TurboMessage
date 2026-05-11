from django.urls import include, path

urlpatterns = [
    path("", include("apps.mailbox.urls")),
]
