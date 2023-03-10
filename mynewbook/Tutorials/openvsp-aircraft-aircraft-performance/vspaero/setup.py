import os
from datetime import datetime
from pathlib import Path

HOSTNAME = os.getenv("HOSTNAME")


def setup(
    inputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    outputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    parameters: dict = {
        "user_input_files": [],
        "inputs_folder_path": "",
        "outputs_folder_path": "",
    },
) -> dict:
    """A user editable setup function."""

    # initalise setup_data keys
    response = {}

    # delete previous run log
    run_log = Path(parameters["outputs_folder_path"]) / f"run_{HOSTNAME}.log"
    if run_log.is_file():
        os.remove(run_log)

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed on host {HOSTNAME}."
    print(message)
    response["message"] = message

    return response
