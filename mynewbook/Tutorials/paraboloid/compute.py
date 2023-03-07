import os
from datetime import datetime
from pathlib import Path

HOSTNAME = os.getenv("HOSTNAME")


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
    """A user editable compute function.

    Here the compute function evaluates the equation
    f(x,y) = (x-3)^2 + xy + (y+4)^2 - 3.
    with function minimum at: x = 20/3; y = -22/3

    Parameters
    ----------
    inputs: dict
        The component Inputs sorted by type (design, implicit or setup).
    outputs: dict
        The component Outputs sorted by type (design, implicit or setup).
    partials: dict, optional
        The derivatives of the component's "design" outputs with respect to its
        "design" inputs, used for gradient-based design optimisation Runs.
    options: dict, optional
        component data processing options and flags, inc. : "stream_call",
        "get_outputs", "get_grads"
    parameters: dict
        The component Parameters as returned by the setup function.

    Returns
    -------
    dict
        dictionary of JSON-serialisable keys and values, including:
        outputs: dict, optional
            The compute function can assign values to output keys, but the outputs
            keys should not be modified.
        partials: dict, optional
            The compute function can assign values to partials keys, but the
            partials keys should not be modified.
        message: str, optional
            A compute message that will appear in the Run log.
    """

    x = inputs["design"]["x"]
    y = inputs["design"]["y"]
    outputs["design"]["f_xy"] = (x - 3.0) ** 2 + x * y + (y + 4.0) ** 2 - 3.0

    resp = {}
    resp["outputs"] = outputs

    if options["get_grads"]:
        partials["f_xy"]["x"]["val"] = [2 * (x - 3.0) + y]
        partials["f_xy"]["y"]["val"] = [x + 2 * (y + 4.0)]
        resp["partials"] = partials

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Compute paraboloid f(x:{str(x)},y:{str(y)}) = {str(outputs['design']['f_xy'])} on host {HOSTNAME}"
    resp["message"] = message

    return resp
