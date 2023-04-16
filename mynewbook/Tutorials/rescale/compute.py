from datetime import datetime
from pathlib import Path

import rescale


def compute(
    inputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    outputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    partials: dict = {},
    options: dict = {},
    parameters: dict = {
        "user_input_files": [],
        "inputs_folder_path": "",
        "outputs_folder_path": "",
    },
) -> dict:
    """A user editable compute function."""

    print("Starting user function evaluation.")

    inputs_folder = Path(parameters["inputs_folder_path"])
    run_folder = Path(parameters["outputs_folder_path"])

    inputs_paths = []
    for file in parameters["user_input_files"]:
        src = inputs_folder / file["filename"]
        inputs_paths.append(src)

    # define rescale job parameters
    job = parameters["job"]
    for key in ["coresPerSlot", "slots", "walltime"]:
        job["hardware"][key] = int(job["hardware"][key])

    # launch rescale job
    rescale.main(job, inputs_paths, run_folder)

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Rescale job completed."
    print(message)

    return {"message": message}
