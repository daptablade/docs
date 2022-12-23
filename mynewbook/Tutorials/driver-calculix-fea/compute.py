from datetime import datetime
from pathlib import Path
from component_api2 import call_compute

import matplotlib.pyplot as plt


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

    """Editable compute function."""

    workflow = parameters["workflow"]
    component_inputs = parameters["component_inputs"]  # note: params not accessible
    run_folder = Path(parameters["outputs_folder_path"])

    study_results = []
    parameter_values = []
    rotation_min = float(parameters["rotation_min"])
    rotation_inc = float(parameters["rotation_inc"])
    rotation_max = float(parameters["rotation_max"])

    if "calculix-fea" in component_inputs:
        rotation = rotation_min
        while rotation <= rotation_max:

            # update rotation input variable
            component_inputs["calculix-fea"]["fibre_rotation_angle.ORI_0.1"] = rotation

            (msg, output) = run_workflow(workflow, component_inputs)

            if not "outputs" in output:
                raise ValueError(
                    "Cannot find 'output' dictionary in run_workflow output."
                )

            study_results.append(output["outputs"]["design"])
            parameter_values.append(rotation)
            rotation += rotation_inc

        _plot_study_results(
            study_results,
            x=parameter_values,
            y=["Uz", "Ry"],
            saveas=str(run_folder / "results_plot"),
        )
    else:
        (msg, output) = run_workflow(workflow, component_inputs)

    print("Parametric study completed.")

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: {msg}"
    print(message)

    return {"message": message}


def run_workflow(workflow, component_inputs):
    """Execute the workflow components in the same way the Orchestrator would do."""

    msgs = ""
    for component in workflow:
        indict = {
            "component": component,
            "get_grads": False,
            "get_outputs": True,
        }
        if component in component_inputs:
            indict["inputs"] = {
                "design": component_inputs[component],
                "implicit": {},
                "setup": {},
            }
        (msg, output) = call_compute(indict)
        print(msg)
        msgs += msg + "\n"

    # only return the last output captured
    return (msgs, output)


def _plot_study_results(
    output: list,  # list of dictionaries
    x: list,  # x-values
    y: list,  # key of y-values
    xlabel="ply rotation angle (deg)",
    ylabel="displacements (m) or rotation (rad)",
    saveas=None,
):

    y_series = []
    for result in output:
        if len(y) == 1 and isinstance(result[y[0]], list):
            if len(output) > 1:
                y_series.append(result[y[0]])
            else:
                y_series = result[y[0]]
        else:
            y_series.append([result[label] for label in y])

    lineObjects = plt.plot(x, y_series)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(iter(lineObjects), y)

    if saveas:
        plt.savefig(saveas + ".png")
        plt.savefig(saveas + ".pdf")

    plt.show()

    return {
        "x_label": "rotation_angles",
        "x_values": x,
        "y_labels": y,
        "y_values": y_series,
    }
