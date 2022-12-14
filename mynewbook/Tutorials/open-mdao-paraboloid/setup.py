from datetime import datetime
from pathlib import Path


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    parameters: dict = None,
) -> dict:
    """Editable setup function."""

    if "driver" not in parameters:
        # assume we want to run an optimisation with default settings
        driver = {"type": "optimisation"}
    else:
        driver = parameters["driver"]

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."

    return {"message": message, "driver": driver}
