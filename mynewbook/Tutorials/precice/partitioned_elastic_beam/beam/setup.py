import shutil
from datetime import datetime
import zipfile
from pathlib import Path


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

    # unzip the analysis input files into run folder
    inputs_folder = Path(parameters["inputs_folder_path"])
    run_folder = Path(parameters["outputs_folder_path"])
    for file in parameters["user_input_files"]:
        src = inputs_folder / file["filename"]
        if src.suffix == ".zip":
            print(f"Unzipping {file['filename']} into local component outputs folder.")
            with zipfile.ZipFile(src, mode="r") as f:
                f.extractall(run_folder)
        else:
            shutil.copy(src, run_folder / src.name)

    if not (run_folder / "precice-config.xml").is_file():
        raise ValueError("Missing precice configuration 'precice-config.xml'.")

    # make frd file accessible for post-processing
    outputs["implicit"]["files.beam_frd"] = parameters["beam_frd"]

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    print(message)

    return {"message": message, "outputs": outputs}
