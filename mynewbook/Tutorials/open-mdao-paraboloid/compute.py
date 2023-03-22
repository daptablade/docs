from datetime import datetime
from pathlib import Path
import traceback
from contextlib import redirect_stdout
import numpy as np
import json
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor

import openmdao.api as om
from matplotlib import pyplot as plt  # type: ignore

from om_component import OMexplicitComp, OMimplicitComp  # type: ignore

OM_DEFAULTS = {
    "nonlinear_solver": {
        "class": om.NewtonSolver,
        "kwargs": {"solve_subsystems": False},
    },
    "linear_solver": {
        "class": om.DirectSolver,
        "kwargs": {},
    },
}


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
    run_folder = Path(parameters["outputs_folder_path"])
    all_connections = parameters.get("all_connections", [])

    # 1) define the simulation components
    prob = om.Problem()

    # add groups
    groups = {}
    if "Groups" in parameters:
        for group in parameters["Groups"]:
            name = reformat_compname(group["name"])
            kwargs = group.get("kwargs", {})
            groups[name] = prob.model.add_subsystem(
                name,
                om.Group(),
                **kwargs,
            )
            if "solvers" in group:
                for solver in group["solvers"]:
                    if solver["type"] == "nonlinear_solver":
                        groups[name].nonlinear_solver = OM_DEFAULTS["nonlinear_solver"][
                            "class"
                        ](**OM_DEFAULTS["nonlinear_solver"]["kwargs"])
                        solver_obj = groups[name].nonlinear_solver
                    elif solver["type"] == "linear_solver":
                        groups[name].linear_solver = OM_DEFAULTS["linear_solver"][
                            "class"
                        ](**OM_DEFAULTS["linear_solver"]["kwargs"])
                        solver_obj = groups[name].nonlinear_solver
                    else:
                        raise ValueError(
                            f"Solver of type {solver['type']} is not implemented."
                        )
                    if "options" in solver:
                        for option, val in solver["options"].items():
                            if option in ["iprint", "maxiter"]:
                                solver_obj.options[option] = int(val)
                            else:
                                solver_obj.options[option] = val

    # add components
    def get_comp_by_name(name, objs: dict):

        comp_type_lookup = {
            "ExplicitComponents": OMexplicitComp,
            "ImplicitComponents": OMimplicitComp,
        }

        for key, obj in objs.items():
            filtered = [comp_obj for comp_obj in obj if comp_obj["name"] == name]
            if filtered:
                return [comp_type_lookup[key], filtered[0]]
        return OMexplicitComp, None  # default

    model_lookup = {}
    for component in workflow:
        # defaults
        kwargs = {}
        fd_step = 0.1
        model = prob.model
        has_compute_partials = True  # set this to False if fd gradients should be used

        objs = {
            k: parameters[k]
            for k in ["ExplicitComponents", "ImplicitComponents"]
            if k in parameters
        }
        comp_type, comp_obj = get_comp_by_name(component, objs)
        if comp_obj:
            kwargs = comp_obj.get("kwargs", kwargs)
            fd_step = comp_obj.get("fd_step", fd_step)
            has_compute_partials = comp_obj.get(
                "has_compute_partials", has_compute_partials
            )
            model = groups.get(comp_obj.get("group"), model)

        model_lookup[component] = model
        model.add_subsystem(
            reformat_compname(component),
            comp_type(
                compname=component,
                fd_step=fd_step,
                has_compute_partials=has_compute_partials,
            ),
            **kwargs,
        )

    if "ExecComps" in parameters and parameters["ExecComps"]:
        for component in parameters["ExecComps"]:
            prob.model.add_subsystem(
                reformat_compname(component["name"]),
                om.ExecComp(component["exprs"]),
                **component["kwargs"],
            )

    # 2) define the component connections
    def get_var_str(c, name):
        return f"{reformat_compname(c)}.{name.replace('.','-')}"

    for connection in all_connections:
        if connection["type"] == "design":
            prob.model.connect(
                get_var_str(connection["origin"], connection["name_origin"]),
                get_var_str(connection["target"], connection["name_target"]),
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

        levels = parameters["driver"]["kwargs"].get("levels", 2)
        if isinstance(levels, float):  # All have the same number of levels
            levels = int(levels)
        elif isinstance(levels, dict):  # Different DVs have different number of levels
            levels = {k: int(v) for k, v in levels.items()}

        prob.driver = DOEDriver(
            om.FullFactorialGenerator(levels=levels),
            reset_vars=parameters["driver"]["kwargs"].get("reset_vars", {}),
            store_case_data=parameters["driver"]["kwargs"].get("store_case_data", {}),
            store_parameters=parameters["driver"]["kwargs"].get("store_parameters", {}),
            run_folder=run_folder,
        )

    # 4) add design variables
    if "input_variables" in parameters:
        for var in parameters["input_variables"]:
            upper = var["upper"]
            lower = var["lower"]
            if "component" in var:
                comp_obj = reformat_compname(var["component"])
                prob.model.add_design_var(
                    f"{comp_obj}.{var['name'].replace('.', '-')}",
                    lower=lower,
                    upper=upper,
                )
            else:
                prob.model.add_design_var(
                    var["name"].replace(".", "-"), lower=lower, upper=upper
                )
                val_default = var.get("value", lower)
                prob.model.set_input_defaults(
                    var["name"].replace(".", "-"), val_default
                )

    # 5) add an objective and constraints
    if "output_variables" in parameters:
        for var in parameters["output_variables"]:
            comp_obj = reformat_compname(var["component"])
            name = f"{comp_obj}.{var['name'].replace('.', '-')}"

            # set scaling from parameter input file
            scaler = var.get("scaler", None)
            adder = var.get("adder", None)

            if var["type"] == "objective":
                prob.model.add_objective(name, scaler=scaler, adder=adder)
            elif var["type"] == "constraint":
                lower = var.get("lower", None)
                upper = var.get("upper", None)
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

    elif parameters["driver"]["type"] == "doe":
        nb_threads = int(parameters["driver"].get("nb_threads", 1))
        dict_out = run_doe(prob, parameters, run_folder, nb_threads=nb_threads)

    # elif parameters["driver"]["type"] == "post":
    #     dict_out = run_post(prob, parameters)

    else:
        with open(run_folder / "trim_convergence.log", "w") as f:
            with redirect_stdout(f):
                prob.run_model()
                dict_out = {}

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: OpenMDAO compute completed."
    print(message)

    if dict_out:
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
                f"{reformat_compname(comp)}.{name.replace('.', '-')}"
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
            f"{reformat_compname(comp)}.{name.replace('.', '-')}"
        ).tolist()
    # print(")")

    print(opt_output)

    if "visualise" in parameters and "plot_history" in parameters["visualise"]:
        post_process_optimisation(parameters, run_folder, r_name)

    return opt_output


def run_doe(prob, parameters, run_folder, nb_threads=1):

    # 7) execute the driver in parallel
    def run_cases_thread(color):
        print(f"Starting thread {color}.")
        prob_copy = deepcopy(prob)
        print(f"problem id for color {color}: ", id(prob_copy))

        # set driver instance properties
        prob_copy.driver.nb_threads = nb_threads
        prob_copy.driver.color = color
        try:
            prob_copy.run_driver()
        except Exception as e:
            print(f"run driver exited with error: {e}")
            tb = traceback.format_exc()
            return f"OpenMDAO DOE error: {tb}"

        print(f"Completed thread {color}.")

    with open(run_folder / f"run_driver.log", "w") as f:
        with redirect_stdout(f):
            with ThreadPoolExecutor(max_workers=nb_threads) as executor:
                msgs = executor.map(run_cases_thread, range(nb_threads))
                errors = list(msgs)
                if errors and errors[0]:
                    raise ValueError(errors[0])

    print("completed all threads")

    if "visualise" in parameters and "plot_history" in parameters["visualise"]:
        from post import post_process_doe

        post_process_doe(
            parameters,
            run_folder,
            files=[f"results_{c}.json" for c in range(nb_threads)],
        )

    return {}


def reformat_compname(name):
    # openmdao doesn't allow "-" character in component names
    return name.replace("-", "_")


def post_process_optimisation(
    parameters, run_folder, r_name, only_plot_major_iter=True
):
    # read database
    # Instantiate your CaseReader
    cr = om.CaseReader(r_name)
    # Isolate "problem" as your source
    driver_cases = cr.list_cases("driver", out_stream=None)

    # plot the iteration history from the recorder data
    inputs_history = {
        key: []
        for key in [
            f"{reformat_compname(var['component'])}.{var['name'].replace('.', '-')}"
            for var in parameters["input_variables"]
        ]
    }
    outputs_history = {
        key: []
        for key in [
            f"{reformat_compname(var['component'])}.{var['name'].replace('.', '-')}"
            for var in parameters["output_variables"]
        ]
    }
    for key in driver_cases:
        case = cr.get_case(key)
        if (only_plot_major_iter and case.derivatives) or not only_plot_major_iter:
            # get history of inputs
            for key in inputs_history:
                inputs_history[key].append(case.outputs[key])
            # get history of outputs
            for key in outputs_history:
                outputs_history[key].append(case.outputs[key])

    # plot output in userfriendly fashion
    _plot_iteration_histories(
        inputs_history=inputs_history,
        outputs_history=outputs_history,
        run_folder=run_folder,
    )


def _plot_iteration_histories(
    inputs_history=None, outputs_history=None, run_folder=None
):
    # plot input histories
    for key in inputs_history:
        input_data = inputs_history[key]
        input_data = np.array(input_data)
        iterations = range(input_data.shape[0])

        plt.figure()
        for data_series in input_data.T:
            plt.plot(iterations, data_series, "-o")
            plt.grid(True)
            plt.title(key)
        plt.savefig(str(run_folder / (key + ".png")))

    # plot output histories
    for key in outputs_history:
        output_data = outputs_history[key]
        output_data = np.array(output_data)
        iterations = range(output_data.shape[0])

        plt.figure()
        for data_series in output_data.T:
            plt.plot(iterations, data_series, "-o")
            plt.grid(True)
            plt.title(key)
        plt.savefig(str(run_folder / (key + ".png")))

    plt.show()


class DOEDriver(om.DOEDriver):
    def __init__(
        self,
        generator=None,
        reset_vars: dict = None,
        store_case_data: list = None,
        store_parameters: dict = None,
        run_folder: Path = None,
        **kwargs,
    ):
        self.reset_vars = reset_vars
        self.cases_store = []
        self.store_case_data = store_case_data
        self.store_parameters = store_parameters
        self.run_folder = run_folder
        self.nb_threads = 1
        self.color = 0
        super().__init__(generator=generator, **kwargs)

    def run(self):
        """
        Generate cases and run the model for each set of generated input values.

        Returns
        -------
        bool
            Failure flag; True if failed to converge, False is successful.
        """
        self.iter_count = 0
        self._quantities = []

        # set driver name with current generator
        self._set_name()

        # Add all design variables
        dv_meta = self._designvars
        self._indep_list = list(dv_meta)

        # Add all objectives
        objs = self.get_objective_values()
        for name in objs:
            self._quantities.append(name)

        # Add all constraints
        con_meta = self._cons
        for name, _ in con_meta.items():
            self._quantities.append(name)

        for case in self._parallel_generator(self._designvars, self._problem().model):
            print(f"Starting case on thread {self.color}.")
            self._custom_reset_variables()
            self._run_case(case)
            self.iter_count += 1
            self._custom_store_to_json()

        return False

    def _custom_reset_variables(self):
        # reset the initial variable guesses
        for k, v in self.reset_vars.items():
            self._problem()[k] = v

    def _custom_store_to_json(self):
        # store the outputs to the json database
        self.cases_store.append(
            {
                **self.store_parameters,
                **{
                    k.split(".")[-1]: self._problem()[k][0]
                    for k in self.store_case_data
                },
            }
        )
        # dump to json file
        fname = f"results_{self.color}.json"
        with open(self.run_folder / fname, "w", encoding="utf-8") as f:
            json.dump(self.cases_store, f)

    def _parallel_generator(self, design_vars, model=None):
        """
        Generate case for this thread.

        Parameters
        ----------
        design_vars : dict
            Dictionary of design variables for which to generate values.

        model : Group
            The model containing the design variables (used by some generators).

        Yields
        ------
        list
            list of name, value tuples for the design variables.
        """
        size = self.nb_threads
        color = self.color

        generator = self.options["generator"]
        for i, case in enumerate(generator(design_vars, model)):
            if i % size == color:
                yield case


if __name__ == "__main__":
    with open("open-mdao-driver/parameters.json", "r") as f:
        parameters = json.load(f)
    parameters["all_connections"] = [
        {
            "origin": "vspaero",
            "name_origin": "CL",
            "target": "trim",
            "name_target": "CL",
            "type": "design",
        },
        {
            "origin": "vspaero",
            "name_origin": "CMy",
            "target": "trim",
            "name_target": "CMy",
            "type": "design",
        },
    ]
    parameters["workflow"] = ["vspaero", "trim"]  # defined by controller
    parameters["outputs_folder_path"] = "outputs"  # defined by component generic api
    compute(
        inputs={},
        outputs={"design": {}},
        partials=None,
        options=None,
        parameters=parameters,
    )
