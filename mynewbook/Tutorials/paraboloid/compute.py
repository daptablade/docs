from datetime import datetime
from pathlib import Path


def compute(
    setup_data: dict = None,
    params: dict = None,
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    run_folder: Path = None,
    inputs_folder: Path = None,
):

    """
    Evaluates the equation f(x,y) = (x-3)^2 + xy + (y+4)^2 - 3.
    Minimum at: x = 6.6667; y = -7.3333
    """

    x = inputs["x"]
    y = inputs["y"]
    outputs["f_xy"] = (x - 3.0) ** 2 + x * y + (y + 4.0) ** 2 - 3.0

    resp = {}
    resp["outputs"] = outputs

    if options["get_grads"]:
        partials["f_xy"]["x"]["val"] = [2 * (x - 3.0) + y]
        partials["f_xy"]["y"]["val"] = [x + 2 * (y + 4.0)]
        resp["partials"] = partials

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Compute paraboloid f(x:{str(x)},y:{str(y)}) = {str(outputs['f_xy'])} with options: {str(options)}"
    resp["message"] = message

    return resp
