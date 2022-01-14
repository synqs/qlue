"""
The models that define our sql tables for the app.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser

# pylint: disable=W0611, W0107
class User(AbstractUser):
    """
    The class that will contain all the fancy features of a user.
    """

    pass


class Backend(models.Model):
    """
    The backend class, which allows us to safe the properties of the backends etc.

    Args:
        name: The name of the backend under which we will identify it later
        description: A description of the backend as it will be given to the user
        version: The version of the backend
        cold_atom_type: describes what kind of backend you have. Fermions, spins or bosons ?
        gates: the allowed gates. They should be described through an appropiate json
        max_experiments: number of experiments the user is allowed to run.
        max_shots: How many shots of each experiment are allowed.
        simulator: Is the backend a simulator or real hardware ?
        supported_instructions: a json string with the support instructions.
        num_wires: The number of wires on which informaiton is stored. For compatibility with qiskit
            it is sent out as n_qubits in the config file.
        wire_order: Could by interleaved or sequential.
        num_species: Number of internal states the backend is working with. Only relevant for
            the types `boson` or `fermion`
    """

    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=500)
    version = models.CharField(max_length=20)
    COLD_ATOM_TYPE_CHOICES = (
        ("fermion", "fermion"),
        ("spin", "spin"),
        ("boson", "boson"),
    )
    cold_atom_type = models.CharField(max_length=15, choices=COLD_ATOM_TYPE_CHOICES)
    gates = models.JSONField(null=True)
    max_experiments = models.IntegerField(default=1000)
    max_shots = models.IntegerField(default=100000000)
    simulator = models.BooleanField(default=True)
    supported_instructions = models.JSONField(null=True)
    num_wires = models.PositiveIntegerField(default=1)
    WIRE_ORDER_CHOICES = (("interleaved", "interleaved"), ("sequential", "sequential"))
    wire_order = models.CharField(max_length=15, choices=WIRE_ORDER_CHOICES)
    num_species = models.PositiveIntegerField(default=1)


# Create your models here.
