import shutil
from datetime import datetime
from pathlib import Path

from precice import run_ccx_preCICE


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

    if not "ccx_precice" in parameters:
        raise ValueError(
            "Missing required ccx_precice parmeter dictionary with keys 'infile', 'participant', 'subfolder' and 'env'."
        )

    infile = parameters["ccx_precice"]["infile"]
    participant = parameters["ccx_precice"]["participant"]
    env = parameters["ccx_precice"]["env"]
    subfolder = parameters["ccx_precice"]["subfolder"]

    resp = run_ccx_preCICE(
        infile=run_folder / subfolder / infile,
        run_folder=run_folder / subfolder,
        participant=participant,
        env=env,
    )
    with open(run_folder / f"ccx_precice_{participant}.log", "w") as f:
        f.write(resp["stdout"])
    if not resp["returncode"] == 0:
        raise ChildProcessError(
            f'ccx_precice returned non-zero exit status {resp["returncode"]}'
        )

    print("Executed CCX FEM analysis.")

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Compute completed."

    return {"message": message, "outputs": outputs}
