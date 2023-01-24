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

    response = {}

    # set default inputs
    if inputs:
        for input_key, input_value in inputs["design"].items():
            if input_value == "default":
                try:
                    inputs["design"][input_key] = float(parameters[input_key])
                except Exception as e:
                    print(f"Could not find {input_key} in the input parameters.")
        response["inputs"] = inputs

    # initialise outputs - required for OpenMDAO
    if outputs:
        for output_key, output_value in outputs["design"].items():
            if output_value == "default":
                try:
                    outputs["design"][output_key] = float(parameters[output_key])
                except Exception as e:
                    print(f"Could not find {output_key} in the input parameters.")
        response["outputs"] = outputs

    # declare default parameter inputs - overriden by connection data if available
    if "files.analysis_output_file" in parameters:
        response["inputs"]["implicit"]["files.analysis_output_file"] = parameters[
            "files.analysis_output_file"
        ]
    else:
        response["inputs"]["implicit"]["files.analysis_output_file"] = "default"

    if "files.mesh_file" in parameters:
        response["inputs"]["implicit"]["files.mesh_file"] = parameters[
            "files.mesh_file"
        ]
    else:
        response["inputs"]["implicit"]["files.mesh_file"] = "default"

    if "files.nodeset_file" in parameters:
        response["inputs"]["implicit"]["files.nodeset_file"] = parameters[
            "files.nodeset_file"
        ]
    else:
        response["inputs"]["implicit"]["files.nodeset_file"] = "default"

    response[
        "message"
    ] = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."

    return response
