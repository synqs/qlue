"""
Module that configures the app.
"""
from django.apps import AppConfig
from .storage_providers import DropboxProvider


class BackendsConfig(AppConfig):
    """
    Class that defines some basic configuration settings.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "backends"
    storage = DropboxProvider()
