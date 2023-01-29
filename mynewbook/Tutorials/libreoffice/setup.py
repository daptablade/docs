from datetime import datetime
from pathlib import Path
from shutil import copy2

from libreoffice import start_libreoffice


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

    # start libreoffice in headless mode
    start_libreoffice()

    # check that the spreadsheet file has been uploaded
    inputs_folder = Path(parameters["inputs_folder_path"])
    if not (inputs_folder / parameters["ods_file"]).is_file():
        raise FileNotFoundError(
            f"{parameters['ods_file']} needs to be uploaded by the user."
        )

    # copy spreadsheet to output folder
    run_folder = Path(parameters["outputs_folder_path"])
    copy2(
        inputs_folder / parameters["ods_file"],
        run_folder / parameters["ods_file"],
    )

    # set default inputs
    if inputs:
        for input_key, input_value in inputs["design"].items():
            if input_value == "default":
                try:
                    inputs["design"][input_key] = float(parameters[input_key])
                except Exception as e:
                    print(f"Could not find {input_key} in the input parameters.")

    # initialise outputs - required for OpenMDAO
    if outputs:
        for output_key, output_value in outputs["design"].items():
            if output_value == "default":
                try:
                    outputs["design"][output_key] = float(parameters[output_key])
                except Exception as e:
                    print(f"Could not find {output_key} in the input parameters.")

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    print(message)

    return {
        "message": message,
        "parameters": parameters,
        "inputs": inputs,
        "outputs": outputs,
    }
