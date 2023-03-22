from datetime import datetime
from fluids.atmosphere import ATMOSPHERE_1976


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
    """A user editable compute function."""

    print(f"Starting residuals check.")

    g = 9.81  # gravity acceleration in m/s**2
    rho = ATMOSPHERE_1976(parameters["Altitude"]).rho
    m = parameters["Mass"]
    s = parameters["S"]

    v = inputs["design"]["Vinfinity"]

    CL_target = 2 * m * g / (rho * v**2 * s)

    outputs["design"]["AoA"] = inputs["design"]["CL"] - CL_target
    outputs["design"]["HTP_RY"] = inputs["design"]["CMy"]

    message = (
        f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Trim residual compute completed."
    )
    print(message)
    print(f"with:\nINPUTS: {str(inputs)},\nOUTPUTS: {str(outputs)}.")

    return {"message": message, "outputs": outputs}


if __name__ == "__main__":
    # for local testing only
    design_inputs = {"CL": 0.0, "CMy": 0.0, "Vinfinity": 40.0}
    outputs = {"AoA": 0.0, "HTP_RY": 0.0}
    options = {}
    parameters = {"Mass": 1111.0, "Altitude": 3000.0, "Vinfinity": 40.0, "S": 16.234472}
    response = compute(
        inputs={"design": design_inputs},
        outputs={"design": outputs},
        partials=None,
        options=options,
        parameters=parameters,
    )
