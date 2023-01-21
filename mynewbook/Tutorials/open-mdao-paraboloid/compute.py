from datetime import datetime
from pathlib import Path
import traceback
from contextlib import redirect_stdout
import numpy as np
import openmdao.api as om

from component_api2 import call_compute
from om_component import OMexplicitComp  # type: ignore


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

    print("OpenMDAO problem setup started.")

    workflow = parameters["workflow"]
    all_connections = parameters["all_connections"]
    run_folder = Path(parameters["outputs_folder_path"])

    # 1) define the simulation components
    prob = om.Problem()
    for component in workflow:
        if "ExplicitComponents" in parameters:
            kwargs = [
                comp["kwargs"]
                for comp in parameters["ExplicitComponents"]
                if comp["name"] == component
            ][0]
        else:
            kwargs = {}
        prob.model.add_subsystem(
            component, OMexplicitComp(name=component, run_number=0), **kwargs
        )
    if "ExecComps" in parameters and parameters["ExecComps"]:
        for component in parameters["ExecComps"]:
            prob.model.add_subsystem(
                component["name"],
                om.ExecComp(component["exprs"]),
                **component["kwargs"],
            )
            if "connections" in component:
                for c in component["connections"]:
                    prob.model.connect(c["src"], c["target"])

    # 2) define the component connections
    for connection in all_connections:
        if connection["type"] == "design":
            prob.model.connect(
                connection["origin"]
                + "."
                + connection["name_origin"].replace(".", "-"),
                connection["target"]
                + "."
                + connection["name_target"].replace(".", "-"),
            )

    if parameters["driver"]["type"] == "optimisation":
        # 3) setup the optimisation driver options
        prob.driver = om.ScipyOptimizeDriver()
        prob.driver.options["optimizer"] = parameters["optimizer"]
        prob.driver.options["maxiter"] = parameters["max_iter"]
        prob.driver.options["tol"] = parameters["tol"]
        prob.driver.opt_settings["disp"] = parameters["disp"]
        prob.driver.options["debug_print"] = parameters["debug_print"]

        if "approx_totals" in parameters and parameters["approx_totals"]:
            # ensure FD gradients are used
            prob.model.approx_totals(
                method="fd", step=parameters["fd_step"], form=None, step_calc=None
            )

    elif parameters["driver"]["type"] == "doe":
        # 3) alternative: setup a design of experiments
        prob.driver = om.DOEDriver(
            om.UniformGenerator(num_samples=parameters["driver"]["samples"])
        )

    # 4) add design variables
    for var in parameters["input_variables"]:
        upper = var["upper"]
        lower = var["lower"]
        if "component" in var:
            comp = var["component"]
            prob.model.add_design_var(
                f"{comp}.{var['name'].replace('.', '-')}",
                lower=lower,
                upper=upper,
            )
        else:
            prob.model.add_design_var(
                var["name"].replace(".", "-"), lower=lower, upper=upper
            )
            prob.model.set_input_defaults(var["name"].replace(".", "-"), var["value"])

    # 5) add an objective and constraints
    for var in parameters["output_variables"]:
        comp = var["component"]
        name = f"{comp}.{var['name'].replace('.', '-')}"

        # set scaling from parameter input file
        if "scaler" in var:
            scaler = var["scaler"]
        else:
            scaler = None
        if "adder" in [var]:
            adder = var["adder"]
        else:
            adder = None

        if var["type"] == "objective":
            prob.model.add_objective(name, scaler=scaler, adder=adder)
        elif var["type"] == "constraint":
            if "lower" in var:
                lower = var["lower"]
            else:
                lower = None
            if "upper" in var:
                upper = var["upper"]
            else:
                upper = None
            prob.model.add_constraint(
                name, lower=lower, upper=upper, scaler=scaler, adder=adder
            )

    prob.setup()  # required to generate the n2 diagram
    print("OpenMDAO problem setup completed.")

    if "visualise" in parameters and "n2_diagram" in parameters["visualise"]:
        # save n2 diagram in html format
        om.n2(
            prob,
            outfile=str(run_folder / "n2.html"),
            show_browser=False,
        )

    if parameters["driver"]["type"] == "optimisation":
        dict_out = run_optimisation(prob, parameters, run_folder)

    # elif parameters["driver"]["type"] == "check_partials":
    #     dict_out = run_check_partials(prob, parameters)

    # elif parameters["driver"]["type"] == "check_totals":
    #     dict_out = run_check_totals(prob, parameters)

    # elif parameters["driver"]["type"] == "doe":
    #     dict_out = run_doe(prob, parameters)

    # elif parameters["driver"]["type"] == "post":
    #     dict_out = run_post(prob, parameters)

    else:
        raise ValueError(
            f"driver {parameters['driver']['type']} is not a valid component driver type."
        )

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: OpenMDAO compute completed."
    print(message)

    outputs["design"] = dict_out

    return {"message": message, "outputs": outputs}


def run_optimisation(prob, parameters, run_folder):

    # 6) add a data recorder to the optimisation problem
    r_name = str(
        run_folder
        / (
            "om_problem_recorder_"
            + datetime.now().strftime("%Y%m%d-%H%M%S")
            + ".sqlite"
        )
    )
    r = om.SqliteRecorder(r_name)
    prob.driver.add_recorder(r)
    prob.driver.recording_options["record_derivatives"] = True

    # setup the problem again
    prob.setup()

    if "visualise" in parameters and "scaling_report" in parameters["visualise"]:
        # NOTE: running the model can generate large large amounts of stored data in orchestrator, which
        # can cause prob.setup() to fail if it is called again, so only execute
        # prob.run_model() after all setup has been completed
        with open(run_folder / "scaling_report.log", "w") as f:
            with redirect_stdout(f):
                prob.run_model()
                prob.driver.scaling_report(
                    outfile=str(run_folder / "driver_scaling_report.html"),
                    title=None,
                    show_browser=False,
                    jac=True,
                )

    # 7) execute the optimisation
    try:
        with open(run_folder / "run_driver.log", "w") as f:
            with redirect_stdout(f):
                prob.run_driver()
    except Exception as e:
        print(f"run driver exited with error: {e}")
        tb = traceback.format_exc()
        raise ValueError("OpenMDAO Optimisation error: " + tb)

    opt_output = {}
    # print("Completed model optimisation - solution is: \n inputs= (")
    for var in parameters["input_variables"]:
        name = var["name"]
        # print(
        #     f"{comp}.{name}: "
        #     + str(prob.get_val(f"{comp}.{name.replace('.', '-')}"))
        #     + " "
        # )
        if "component" in var:
            comp = var["component"]
            opt_output[f"{comp}.{name}"] = prob.get_val(
                f"{comp}.{name.replace('.', '-')}"
            ).tolist()
        else:
            opt_output[name] = prob.get_val(name.replace(".", "-")).tolist()
    # print("), \n outputs = (")
    for var in parameters["output_variables"]:
        comp = var["component"]
        name = var["name"]
        # print(
        #     f"{comp}.{name}: "
        #     + str(prob.get_val(f"{comp}.{name.replace('.', '-')}"))
        #     + " "
        # )
        opt_output[f"{comp}.{name}"] = prob.get_val(
            f"{comp}.{name.replace('.', '-')}"
        ).tolist()
    # print(")")

    print(opt_output)

    return opt_output