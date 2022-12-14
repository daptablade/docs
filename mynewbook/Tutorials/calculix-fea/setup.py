from datetime import datetime
from pathlib import Path


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    parameters: dict = None,
) -> dict:
    """Editable setup function."""

    # declare default parameter inputs - overriden by connection data if available
    if "files.cgx_file" in parameters:
        inputs["implicit"]["files.cgx_file"] = parameters["files.cgx_file"]
    else:
        inputs["implicit"]["files.cgx_file"] = "default"

    fibre_rotation_angles = [
        key for key in inputs["design"] if key.startswith("fibre_rotation_angle")
    ]
    for angle in fibre_rotation_angles:
        # set to float
        inputs["design"][angle] = float(inputs["design"][angle])

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."

    return {"message": message, "inputs": inputs}
