"""
Module that defines the forms that can be used in the Django templates.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.validators import RegexValidator
from django import forms


# pylint: disable=C0115, R0903
class SignUpForm(UserCreationForm):
    """
    Form that is used to register users.
    """

    alphanumeric = RegexValidator(
        r"^[a-zA-Z][a-zA-Z0-9_]*$",
        "Username must start with an alphabet. Only underscore and alphanumeric"
        "characters are allowed.",
    )
    username = forms.CharField(max_length=150, validators=[alphanumeric])

    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "email",
            "password1",
            "password2",
        )
