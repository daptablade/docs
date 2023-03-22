from datetime import datetime


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

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    print(message)
    response["message"] = message

    return response
