from datetime import datetime
from pathlib import Path


def setup(
    inputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    outputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    parameters: dict = {
        "user_input_files": [],
        "inputs_folder_path": "",
        "outputs_folder_path": "",
    },
) -> dict:
    """Editable setup function."""

    if "driver" not in parameters:
        # assume we want to run an optimisation with default settings
        parameters["driver"] = {"type": "optimisation"}

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."

    return {"message": message, "parameters": parameters}
