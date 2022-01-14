"""
Module that connects the view functions with a specific path url.
"""
from django.urls import path
from frontend import views

urlpatterns = [
    path("", views.index, name="index"),
    path("change_password/", views.change_password, name="change_password"),
]
