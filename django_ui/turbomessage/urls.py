from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="turbomessage_index"),
    path("register/", views.register_view, name="turbomessage_register"),
    path("login/", views.login_view, name="turbomessage_login"),
    path("logout/", views.logout_view, name="turbomessage_logout"),
    path("mailbox/", views.dashboard_view, name="turbomessage_dashboard"),
    path("compose/", views.compose_view, name="turbomessage_compose"),
    path(
        "email/<int:email_id>/",
        views.email_detail_view,
        name="turbomessage_email_detail",
    ),
    path(
        "email/<int:email_id>/delete/",
        views.delete_email_view,
        name="turbomessage_email_delete",
    ),
]
