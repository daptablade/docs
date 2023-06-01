import shutil
from datetime import datetime
from pathlib import Path

from precice import run_openfoam_preCICE, run_openfoam_blockMesh


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
    print("Compute started.")

    # get components inputs
    run_folder = Path(parameters["outputs_folder_path"])

    if not "openfoam_precice" in parameters:
        raise ValueError(
            "Missing required openfoam_precice parmeter dictionary with keys 'subfolder'."
        )

    subfolder = parameters["openfoam_precice"]["subfolder"]

    resp = run_openfoam_blockMesh(run_folder=run_folder / subfolder)
    with open(run_folder / f"openfoam_precice.log", "w") as f:
        f.write(resp["stdout"])
    if not resp["returncode"] == 0:
        raise ChildProcessError(
            f'run_openfoam_blockMesh returned non-zero exit status {resp["returncode"]}'
        )

    resp = run_openfoam_preCICE(run_folder=run_folder / subfolder)
    with open(run_folder / f"openfoam_precice.log", "a") as f:
        f.write(resp["stdout"])
    if not resp["returncode"] == 0:
        raise ChildProcessError(
            f'run_openfoam_precice returned non-zero exit status {resp["returncode"]}'
        )

    print("Executed OpenFOAM analysis.")

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Compute completed."

    return {"message": message, "outputs": outputs}
