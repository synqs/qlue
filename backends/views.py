"""
Module that defines the user api.
"""
import datetime
import json
import uuid
from typing import Tuple

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate

from dropbox.exceptions import ApiError, AuthError

from .models import Backend
from .apps import BackendsConfig as ac

# pylint: disable=E1101


def check_request(
    request, backend_name: str, req_method: str = "GET"
) -> Tuple[dict, int]:
    """
    A function that allows us to easily check if the request is valid

    Args:
        request: The request we would like to check
        backend_name: The backend we would like to use
        req_method: the method the user is allowed to call
    Returns:
        status, json_dict that has the appropiate answers
    """
    job_response_dict = {
        "job_id": "None",
        "status": "None",
        "detail": "None",
        "error_message": "None",
    }

    if not request.method == req_method:
        job_response_dict["status"] = "ERROR"
        job_response_dict["error_message"] = "Only " + req_method + " request allowed!"
        job_response_dict["detail"] = "Only " + req_method + " request allowed!"
        return job_response_dict, 405

    if req_method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
    elif req_method == "GET":
        username = request.GET["username"]
        password = request.GET["password"]
    else:
        raise NotImplementedError("Your method is unknown")
    user = authenticate(username=username, password=password)

    if user is None:
        job_response_dict["status"] = "ERROR"
        job_response_dict["error_message"] = "Invalid credentials!"
        job_response_dict["detail"] = "Invalid credentials!"
        return job_response_dict, 401

    try:
        _ = Backend.objects.get(name=backend_name)
    except Backend.DoesNotExist:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Unknown back-end!"
        job_response_dict["error_message"] = "Unknown back-end!"
        return job_response_dict, 404
    return job_response_dict, 200


# Create your views here.
@csrf_exempt
def get_config(request, backend_name: str) -> JsonResponse:
    """
    A view that returns the user the configuration dictionary of the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    job_response_dict, html_status = check_request(request, backend_name)

    if job_response_dict["status"] == "ERROR":
        return JsonResponse(job_response_dict, status=html_status)

    backend = Backend.objects.get(name=backend_name)

    config_dict = {
        "conditional": False,
        "coupling_map": "linear",
        "dynamic_reprate_enabled": False,
        "local": False,
        "memory": True,
        "open_pulse": False,
    }

    # add information that is derived from the core information of the system
    config_dict["display_name"] = backend_name
    config_dict["description"] = backend.description
    config_dict["backend_version"] = backend.version
    config_dict["cold_atom_type"] = backend.cold_atom_type
    config_dict["simulator"] = backend.simulator
    config_dict["num_species"] = backend.num_species
    config_dict["max_shots"] = backend.max_shots
    config_dict["max_experiments"] = backend.max_experiments
    config_dict["n_qubits"] = backend.num_wires
    config_dict["supported_instructions"] = backend.supported_instructions
    config_dict["wire_order"] = backend.wire_order
    if backend.simulator:
        config_dict["backend_name"] = "synqs_" + backend_name + "_simulator"
    else:
        config_dict["backend_name"] = "synqs_" + backend_name + "_machine"
    config_dict["gates"] = backend.gates

    config_dict["basis_gates"] = []
    for gate in config_dict["gates"]:
        config_dict["basis_gates"].append(gate["name"])

    # it would be really good to remove the first part and replace it by the domain
    config_dict["url"] = "https://coquma-sim.herokuapp.com/api/" + backend_name + "/"
    return JsonResponse(config_dict, status=200)


@csrf_exempt
def post_job(request, backend_name: str) -> JsonResponse:
    """
    A view to submit the job to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    job_response_dict, html_status = check_request(request, backend_name, "POST")
    if job_response_dict["status"] == "ERROR":
        return JsonResponse(job_response_dict, status=html_status)

    username = request.POST["username"]
    try:
        data = request.POST["json"].encode("utf-8")
    except UnicodeDecodeError:
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "The encoding of your json seems non utf-8!"
        job_response_dict[
            "error_message"
        ] = "The encoding of your json seems non utf-8!"
        return JsonResponse(job_response_dict, status=406)
    try:
        job_id = (
            (datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
            + "-"
            + backend_name
            + "-"
            + username
            + "-"
            + (uuid.uuid4().hex)[:5]
        )
        job_json_dir = "/Backend_files/Queued_Jobs/" + backend_name + "/"
        job_json_name = "job-" + job_id + ".json"
        job_json_path = job_json_dir + job_json_name

        storage_provider = getattr(ac, "storage")
        storage_provider.upload(
            dump_str=data.decode("utf-8"), storage_path=job_json_path
        )
        status_json_dir = "/Backend_files/Status/" + backend_name + "/" + username + "/"
        status_json_name = "status-" + job_id + ".json"
        status_json_path = status_json_dir + status_json_name
        job_response_dict["job_id"] = job_id
        job_response_dict["status"] = "INITIALIZING"
        job_response_dict["detail"] = "Got your json."
        status_str = json.dumps(job_response_dict)
        storage_provider.upload(dump_str=status_str, storage_path=status_json_path)
        return JsonResponse(job_response_dict)
    except (AuthError, ApiError):
        job_response_dict["status"] = "ERROR"
        job_response_dict["detail"] = "Error saving json data to database!"
        job_response_dict["error_message"] = "Error saving json data to database!"
        return JsonResponse(job_response_dict, status=406)


@csrf_exempt
def get_job_status(request, backend_name: str) -> JsonResponse:
    """
    A view to check the job status that was previously submitted to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend for the configuration should
            be obtained

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)

    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702
    try:
        data = json.loads(request.GET["json"])
        job_id = data["job_id"]
        status_msg_dict["job_id"] = job_id
        extracted_username = job_id.split("-")[2]
    except:
        status_msg_dict["status"] = "ERROR"
        status_msg_dict["detail"] = "Error loading json data from input request!"
        status_msg_dict["error_message"] = "Error loading json data from input request!"
        return JsonResponse(status_msg_dict, status=406)
    try:
        status_json_dir = (
            "/Backend_files/Status/" + backend_name + "/" + extracted_username + "/"
        )
        status_json_name = "status-" + job_id + ".json"
        status_json_path = status_json_dir + status_json_name

        storage_provider = getattr(ac, "storage")
        status_msg_dict = json.loads(
            storage_provider.get_file_content(storage_path=status_json_path)
        )
        return JsonResponse(status_msg_dict, status=200)
    except:
        status_msg_dict["status"] = "ERROR"
        status_msg_dict[
            "detail"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        status_msg_dict[
            "error_message"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        return JsonResponse(status_msg_dict, status=406)


@csrf_exempt
def get_job_result(request, backend_name: str) -> JsonResponse:
    """
    A view to obtain the results of job that was previously submitted to the backend.

    Args:
        request: The request coming in
        backend_name (str): The name of the backend

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)

    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702

    # decode the job-id to request the data from the queue
    try:
        data = json.loads(request.GET["json"])
        job_id = data["job_id"]
        status_msg_dict["job_id"] = job_id
        extracted_username = job_id.split("-")[2]
    except:
        status_msg_dict["detail"] = "Error loading json data from input request!"
        status_msg_dict["error_message"] = "Error loading json data from input request!"
        return JsonResponse(status_msg_dict, status=406)

    # request the data from the queue
    try:
        status_json_dir = (
            "/Backend_files/Status/" + backend_name + "/" + extracted_username + "/"
        )
        status_json_name = "status-" + job_id + ".json"
        status_json_path = status_json_dir + status_json_name
        storage_provider = getattr(ac, "storage")
        status_msg_dict = json.loads(
            storage_provider.get_file_content(storage_path=status_json_path)
        )
        if status_msg_dict["status"] != "DONE":
            return JsonResponse(status_msg_dict, status=200)
    except:
        status_msg_dict[
            "detail"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        status_msg_dict[
            "error_message"
        ] = "Error getting status from database. Maybe invalid JOB ID!"
        return JsonResponse(status_msg_dict, status=406)
    # and if the status is switched to done, we can also obtain the result
    # one might attempt to connect this to the code above
    try:
        result_json_dir = (
            "/Backend_files/Result/" + backend_name + "/" + extracted_username + "/"
        )
        result_json_name = "result-" + job_id + ".json"
        result_json_path = result_json_dir + result_json_name
        storage_provider = getattr(ac, "storage")
        result_dict = json.loads(
            storage_provider.get_file_content(storage_path=result_json_path)
        )
        return JsonResponse(result_dict, status=200)
    except:
        status_msg_dict["detail"] = "Error getting result from database!"
        status_msg_dict["error_message"] = "Error getting result from database!"
        return JsonResponse(status_msg_dict, status=406)


@csrf_exempt
def get_next_job_in_queue(request, backend_name: str) -> JsonResponse:
    """
    A view that obtains the next job in the queue. It is only allowed for the
    user, which is named `spooler`

    Args:
        request: The request coming in
        backend_name (str): The name of the backend

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)
    username = request.GET["username"]
    if not username == "spooler":
        status_msg_dict["status"] = "ERROR"
        status_msg_dict["error_message"] = "This is for the spooler only"
        status_msg_dict["detail"] = "This is for the spooler only"
        return JsonResponse(status_msg_dict, status=406)

    job_msg_dict = {"job_id": "None", "job_json": "None"}

    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702
    try:
        ###_Checking already queued files for a possible freeze_##
        job_json_dir = "/Backend_files/Running_Jobs/"
        storage_provider = getattr(ac, "storage")
        job_list = storage_provider.get_file_queue(job_json_dir)
        if job_list:
            job_id_list = [name[4:-5] for name in job_list]
            for job_id_el in job_id_list:
                split_job_id = job_id_el.split("-")
                if backend_name == split_job_id[1]:
                    job_msg_dict["job_id"] = job_id_el
                    job_msg_dict["job_json"] = (
                        job_json_dir + job_list[job_id_list.index(job_id_el)]
                    )
                    return JsonResponse(job_msg_dict, status=200)
        ###_Now proceed as usual_##
        job_json_dir = "/Backend_files/Queued_Jobs/" + backend_name + "/"
        storage_provider = getattr(ac, "storage")
        job_list = storage_provider.get_file_queue(job_json_dir)
        assert len(job_list) != 0
        job_json_name = job_list[0]
        job_msg_dict["job_id"] = job_json_name[4:-5]
        job_json_start_path = job_json_dir + job_json_name
        job_json_final_path = "/Backend_files/Running_Jobs/" + job_json_name

        storage_provider.move_file(
            start_path=job_json_start_path, final_path=job_json_final_path
        )
        job_msg_dict["job_json"] = job_json_final_path
        return JsonResponse(job_msg_dict, status=200)
    except:
        return JsonResponse(job_msg_dict, status=406)


@csrf_exempt
def get_user_jobs(request, backend_name: str) -> JsonResponse:
    """
    A view that all the jobs of a user for the specified backend

    Args:
        request: The request coming in
        backend_name (str): The name of the backend

    Returns:
        JsonResponse : send back a response with the dict if successful
    """
    status_msg_dict, html_status = check_request(request, backend_name)
    if status_msg_dict["status"] == "ERROR":
        return JsonResponse(status_msg_dict, status=html_status)

    user_job_dict = {"job_ids": "None"}
    username = request.GET["username"]
    # We should really handle these exceptions cleaner, but this seems a bit
    # complicated right now
    # pylint: disable=W0702
    try:
        job_json_dir = (
            "/Backend_files/Finished_Jobs/" + backend_name + "/" + username + "/"
        )
        storage_provider = getattr(ac, "storage")
        job_list = storage_provider.get_file_queue(job_json_dir)
        assert len(job_list) != 0
        job_list = [job_json_name[4:-5] for job_json_name in job_list]
        user_job_dict["job_ids"] = job_list
        return JsonResponse(user_job_dict)
    except:
        return JsonResponse(user_job_dict)
