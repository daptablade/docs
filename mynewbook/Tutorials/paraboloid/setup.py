from datetime import datetime
from pathlib import Path


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    parameters: dict = None,
) -> dict:
    """Editable setup function."""

    # initalise setup_data keys - none for paraboloid
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

    # initialise partials - required for OpenMDAO gradient-based optimisation
    response["partials"] = {
        "f_xy": {
            "x": {"val": [0.0], "method": "exact"},
            "y": {"val": [0.0], "method": "exact"},
        }
    }

    # optional
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    response["message"] = message

    return response
