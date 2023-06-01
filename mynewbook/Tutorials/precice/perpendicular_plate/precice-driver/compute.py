""" preCICE driver component that launches the FSI components."""

import os
from datetime import datetime
from pathlib import Path

from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor

from component_api2 import call_compute

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

    print("preCICE problem solution started.")

    # get components inputs
    workflow = parameters["workflow"]
    run_folder = Path(parameters["outputs_folder_path"])

    coupled_components = workflow  # [:-1]
    # post_component = workflow[-1]

    with open(run_folder / f"run_driver.log", "w") as f:
        with redirect_stdout(f):
            with ThreadPoolExecutor(max_workers=2) as executor:
                # launch each component compute in separate thread
                msgs = executor.map(run_component_compute, coupled_components)
                errors = list(msgs)
                if errors and errors[0]:
                    raise ValueError(errors[0])

            # # post-process results
            # run_component_compute(post_component)

    resp = {}
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: preCICE compute completed on host {HOSTNAME}"
    resp["message"] = message

    return resp


def run_component_compute(component):
    message = {"component": component}
    try:
        _, data = call_compute(message)
    except Exception as exc:
        print(f"Compute of {component} failed, input data was: {str(message)}")
        raise ValueError(f"Component {component} compute error.") from exc

    print(
        f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Completed compute for component {component}."
    )
