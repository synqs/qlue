"""
The models that define our tests for this app.
"""
import json
import uuid
from decouple import config
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Backend
from .apps import BackendsConfig as ac

User = get_user_model()

# pylint: disable=E1101
class BackendCreationTest(TestCase):
    """
    The test for the creation of the backends.
    """

    def test_fermion_creation(self):
        """
        Can we create the standard fermion backend ?
        """

        payload = {
            "name": "fermions",
            "description": "simulator of a fermionic tweezer hardware. "
            "The even wires denote the occupations of the spin-up fermions and "
            "the odd wires denote the spin-down fermions",
            "version": "0.0.1",
            "cold_atom_type": "fermion",
            "gates": [
                {
                    "coupling_map": [
                        [0, 1, 2, 3],
                        [2, 3, 4, 5],
                        [4, 5, 6, 7],
                        [0, 1, 2, 3, 4, 5, 6, 7],
                    ],
                    "description": "hopping of atoms to neighboring tweezers",
                    "name": "fhop",
                    "parameters": ["j_i"],
                    "qasm_def": "{}",
                },
                {
                    "coupling_map": [[0, 1, 2, 3, 4, 5, 6, 7]],
                    "description": "on-site interaction of atoms of opposite spin "
                    "state",
                    "name": "fint",
                    "parameters": ["u"],
                    "qasm_def": "{}",
                },
                {
                    "coupling_map": [
                        [0, 1],
                        [2, 3],
                        [4, 5],
                        [6, 7],
                        [0, 1, 2, 3, 4, 5, 6, 7],
                    ],
                    "description": "Applying a local phase to tweezers through an "
                    "external potential",
                    "name": "fphase",
                    "parameters": ["mu_i"],
                    "qasm_def": "{}",
                },
            ],
            "max_experiments": 1000,
            "max_shots": 1000000,
            "simulator": True,
            "supported_instructions": [
                "load",
                "measure",
                "barrier",
                "fhop",
                "fint",
                "fphase",
            ],
            "wire_order": "interleaved",
        }

        fermion_backend = Backend.objects.create(**payload)
        self.assertEqual(fermion_backend.wire_order, "interleaved")
        self.assertTrue(fermion_backend.simulator, True)

    def test_singlequdit_creation(self):
        """
        Can we create the standard fermion backend ?
        """

        payload = {
            "name": "singlequdit",
            "description": "Setup of a cold atomic gas experiment with a single qudit.",
            "version": "0.0.2",
            "cold_atom_type": "spin",
            "gates": [
                {
                    "name": "rlz",
                    "parameters": ["delta"],
                    "qasm_def": "gate rlz(delta) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under the Z gate",
                },
                {
                    "name": "rlz2",
                    "parameters": ["chi"],
                    "qasm_def": "gate rlz2(chi) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under lz2",
                },
                {
                    "name": "rlx",
                    "parameters": ["omega"],
                    "qasm_def": "gate lrx(omega) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under Lx",
                },
            ],
            "max_experiments": 1000,
            "max_shots": 1000000,
            "simulator": True,
            "supported_instructions": [
                "rlx",
                "rlz",
                "rlz2",
                "measure",
                "barrier",
                "load",
            ],
            "num_wires": 1,
            "wire_order": "interleaved",
        }

        singlequdit_backend = Backend.objects.create(**payload)
        self.assertTrue(singlequdit_backend.simulator, True)
        self.assertEqual(singlequdit_backend.num_wires, 1)

    def test_multiqudit_creation(self):
        """
        Can we create the standard fermion backend ?
        """

        payload = {
            "name": "multiqudit",
            "description": "Setup of a cold atomic gas experiment with a multiple qudits.",
            "version": "0.0.1",
            "cold_atom_type": "spin",
            "gates": [
                {
                    "name": "rlz",
                    "parameters": ["delta"],
                    "qasm_def": "gate rlz(delta) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under the Z gate",
                },
                {
                    "name": "rlz2",
                    "parameters": ["chi"],
                    "qasm_def": "gate rlz2(chi) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under Lz2",
                },
                {
                    "name": "rlx",
                    "parameters": ["omega"],
                    "qasm_def": "gate lrx(omega) {}",
                    "coupling_map": [[0], [1], [2], [3], [4]],
                    "description": "Evolution under Lx",
                },
                {
                    "name": "rlxly",
                    "parameters": ["J"],
                    "qasm_def": "gate rlylx(J) {}",
                    "coupling_map": [[0, 1], [1, 2], [2, 3], [3, 4], [0, 1, 2, 3, 4]],
                    "description": "Entanglement between neighboring gates with an xy interaction",
                },
            ],
            "max_experiments": 1000,
            "max_shots": 1000000,
            "simulator": True,
            "supported_instructions": [
                "rlx",
                "rlz",
                "rlz2",
                "rlxly",
                "barrier",
                "measure",
                "load",
            ],
            "num_wires": 4,
            "wire_order": "interleaved",
        }

        multiqudit_backend = Backend.objects.create(**payload)
        self.assertTrue(multiqudit_backend.simulator, True)
        self.assertEqual(multiqudit_backend.num_wires, 4)


class BackendConfigTest(TestCase):
    """
    The class that contains all the tests for this backends app.
    """

    fixtures = ["backend.json"]

    def setUp(self):
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

    def test_get_unknown_backend(self):
        """
        Test if we can nicely recover known backends and refuse unknown backends.
        """
        url = reverse("get_config", kwargs={"backend_name": "something_weird"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        self.assertEqual(req.status_code, 404)

    def test_fermions_get_config(self):
        """
        Test the API that presents the capabilities of the backend
        """
        url = reverse("get_config", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)
        self.assertEqual(req.status_code, 200)
        self.assertCountEqual(data["basis_gates"], ["fhop", "fint", "fphase"])
        self.assertEqual(data["backend_name"], "synqs_fermions_simulator")
        self.assertEqual(data["display_name"], "fermions")
        self.assertEqual(data["url"], "https://coquma-sim.herokuapp.com/api/fermions/")
        self.assertEqual(data["n_qubits"], 8)

        gates = data["gates"]
        for gate in gates:
            if gate["name"] == "fhop":
                self.assertEqual(
                    gate["coupling_map"],
                    [
                        [0, 1, 2, 3],
                        [2, 3, 4, 5],
                        [4, 5, 6, 7],
                        [0, 1, 2, 3, 4, 5, 6, 7],
                    ],
                )
            if gate["name"] == "fint":
                self.assertEqual(gate["coupling_map"], [[0, 1, 2, 3, 4, 5, 6, 7]])

    def test_singlequdit_get_config(self):
        """
        Test the API that presents the capabilities of the backend
        """
        url = reverse("get_config", kwargs={"backend_name": "singlequdit"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)
        self.assertEqual(data["display_name"], "singlequdit")
        self.assertEqual(data["backend_name"], "synqs_singlequdit_simulator")
        self.assertEqual(
            data["url"], "https://coquma-sim.herokuapp.com/api/singlequdit/"
        )
        self.assertEqual(req.status_code, 200)

    def test_multiqudit_get_config(self):
        """
        Test the API that presents the capabilities of the backend
        """
        url = reverse("get_config", kwargs={"backend_name": "multiqudit"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        data = json.loads(req.content)

        self.assertCountEqual(data["basis_gates"], ["rlx", "rlz", "rlz2", "rlxly"])
        self.assertEqual(data["backend_name"], "synqs_multiqudit_simulator")
        self.assertEqual(data["display_name"], "multiqudit")
        self.assertEqual(
            data["url"], "https://coquma-sim.herokuapp.com/api/multiqudit/"
        )
        self.assertEqual(req.status_code, 200)
        gates = data["gates"]

        for gate in gates:
            if gate["name"] == "rlx":
                self.assertEqual(gate["coupling_map"], [[0], [1], [2], [3], [4]])
            if gate["name"] == "rlz":
                self.assertEqual(gate["coupling_map"], [[0], [1], [2], [3], [4]])
            if gate["name"] == "rlxly":
                self.assertEqual(
                    gate["coupling_map"],
                    [[0, 1], [1, 2], [2, 3], [3, 4], [0, 1, 2, 3, 4]],
                )


class JobSubmissionTest(TestCase):
    """
    The class that contains all the tests for this backends app.
    """

    fixtures = ["backend.json"]

    def setUp(self):
        self.username = config("USERNAME_TEST")
        self.password = config("PASSWORD_TEST")
        user = User.objects.create(username=self.username)
        user.set_password(self.password)
        user.save()

    def test_post_job(self):
        """
        Test the API that presents the capabilities of the backend
        """
        job_payload = {
            "experiment_0": {
                "instructions": [
                    ("load", [7], []),
                    ("load", [2], []),
                    ("measure", [2], []),
                    ("measure", [6], []),
                    ("measure", [7], []),
                ],
                "num_wires": 8,
                "shots": 4,
                "wire_order": "sequential",
            },
        }

        url = reverse("post_job", kwargs={"backend_name": "fermions"})
        req = self.client.post(
            url,
            {
                "json": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

    def test_get_job_status(self):
        """
        Test the API that checks the job status
        """
        job_payload = {
            "experiment_0": {
                "instructions": [
                    ("load", [7], []),
                    ("load", [2], []),
                    ("measure", [2], []),
                    ("measure", [6], []),
                    ("measure", [7], []),
                ],
                "num_wires": 8,
                "shots": 4,
                "wire_order": "sequential",
            },
        }

        url = reverse("post_job", kwargs={"backend_name": "fermions"})
        req = self.client.post(
            url,
            {
                "json": json.dumps(job_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        data = json.loads(req.content)
        self.assertEqual(data["status"], "INITIALIZING")
        self.assertEqual(req.status_code, 200)

        req_id = data["job_id"]
        status_payload = {"job_id": req_id}
        url = reverse("get_job_status", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url,
            {
                "json": json.dumps(status_payload),
                "username": self.username,
                "password": self.password,
            },
        )
        self.assertEqual(req.status_code, 200)
        data = json.loads(req.content)
        self.assertEqual(data["job_id"], req_id)

    def test_get_next_job_in_queue(self):
        """
        Test the API that gets the next job in the queue.
        """
        url = reverse("get_next_job_in_queue", kwargs={"backend_name": "fermions"})
        req = self.client.get(
            url, {"username": self.username, "password": self.password}
        )
        self.assertEqual(req.status_code, 406)
        data = json.loads(req.content)
        self.assertEqual(data["status"], "ERROR")


class DropboxProvideTest(TestCase):
    """
    The class that contains all the tests for the dropbox provider.
    """

    def setUp(self):
        """
        set up the test.
        """
        self.storage_provider = getattr(ac, "storage")

    def test_upload_etc(self):
        """
        Test that it is possible to upload a file.
        """

        # upload a file and get it back
        file_id = uuid.uuid4().hex
        dump_str = "Hello world"
        self.storage_provider.upload(dump_str, f"/test_folder/world-{file_id}.txt")
        world_str = self.storage_provider.get_file_content(
            f"/test_folder/world-{file_id}.txt"
        )
        self.assertEqual("Hello world", world_str)

        # move it and get it back
        self.storage_provider.move_file(
            f"/test_folder/world-{file_id}.txt",
            f"/test_folder/copied_world-{file_id}.txt",
        )
        world_str = self.storage_provider.get_file_content(
            f"/test_folder/copied_world-{file_id}.txt"
        )
        self.assertEqual("Hello world", world_str)
        # this is not really meaningful to be
        file_list = self.storage_provider.get_file_queue("/test_folder/")
        self.assertTrue(len(file_list))

        # clean up our mess
        self.storage_provider.delete_file(f"/test_folder/copied_world-{file_id}.txt")
