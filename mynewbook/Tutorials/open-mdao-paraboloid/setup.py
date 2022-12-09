from datetime import datetime
from pathlib import Path


def setup(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    params: dict = None,
    run_folder: Path = None,
    inputs_folder: Path = None,
):
    """Editable setup function."""

    if "driver" not in params:
        # assume we want to run an optimisation with default settings
        params["driver"] = {"type": "optimisation"}

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."

    return {"message": message, **params}
