""" Optimisation Component classes for OpenMDAO and associated utilities."""

import numpy as np
import openmdao.api as om  # type: ignore

from component_api2 import call_compute, call_setup
import traceback


class OMexplicitComp(om.ExplicitComponent):
    """standard component that follows the OM conventions"""

    def __init__(self, name, run_number):
        self.name = name
        self.run_number = run_number
        self.get_grads = False
        self.iter = 0
        self.partial_dict = None
        super().__init__()

    def setup(self):

        message = {"component": self.name}
        _, component_dict = call_setup(message)
        inputs = component_dict["input_data"]["design"]
        outputs = component_dict["output_data"]["design"]

        # initialise the inputs
        if inputs:
            for variable in inputs:
                self.add_input(variable.replace(".", "-"), val=inputs[variable])

        # initialise the outputs
        if outputs:
            for variable in outputs:
                self.add_output(variable.replace(".", "-"), val=outputs[variable])

    def setup_partials(self):
        # Get the component partial derivative information

        message = {"component": self.name}
        _, component_dict = call_setup(message)

        if "partials" in component_dict and component_dict["partials"]:
            self.partial_dict = component_dict["partials"]
            for resp, vars in self.partial_dict.items():
                for var, vals in vars.items():
                    self.declare_partials(
                        resp.replace(".", "-"), var.replace(".", "-"), **vals
                    )
        else:
            # calculate all paritials using finite differencing
            self.declare_partials("*", "*", method="fd")

    def compute(self, inputs, outputs, discrete_inputs=None, discrete_outputs=None):

        print("Calling compute.")
        # calculate the outputs
        # Note: transform all np.ndarrays into nested lists to allow formatting to json
        input_dict = {"design": reformat_inputs(inputs._copy_views())}

        message = {
            "component": self.name,
            "inputs": input_dict,
            "get_grads": False,
            "get_outputs": True,
        }
        print("message: \n", str(message))

        try:
            _, data = call_compute(message)
            if not "outputs" in data:
                raise ValueError(f"Error: Compute output missing - output was: {data}.")
        except Exception as e:
            print(f"Compute of {self.name} failed, input data was: {str(message)}")
            tb = traceback.format_exc()
            print(tb)
            raise ValueError(f"OM Explicit component {self.name} compute error: " + tb)

        val_outputs = data["outputs"]["design"]

        # OpenMDAO doesn't like the outputs dictionary to be overwritten, so
        # assign individual outputs one at a time instead
        for output in outputs:
            outputs[output] = val_outputs[output.replace("-", ".")]

    def compute_partials(self, inputs, J):
        """Jacobian of partial derivatives."""

        print("Calling compute_partials.")

        self.iter += 1
        input_dict = reformat_inputs(inputs._copy_views())

        message = {
            "component": self.name,
            "inputs": input_dict,
            "get_grads": True,
            "get_outputs": False,
        }
        print("message: \n", str(message))

        try:
            _, data = call_compute(message)
            if not "partials" in data:
                raise ValueError(
                    f"Error: Compute partial derivatives missing - output was: {data}."
                )
            self.partial_dict = data["partials"]
        except Exception as e:
            print(
                f"Compute partials of {self.name} failed, input data was: {str(message)}"
            )
            tb = traceback.format_exc()
            print(tb)
            raise ValueError(f"OM Explicit component {self.name} compute error: " + tb)

        if self.partial_dict:
            for resp, vars in self.partial_dict.items():
                for var, vals in vars.items():
                    if "val" in vals:
                        J[resp.replace(".", "-"), var.replace(".", "-")] = vals["val"]
            # print(dict(J))
        else:
            raise ValueError(f"Component {self.name} has no Jacobian defined.")


def reformat_inputs(inputs):
    input_dict = inputs
    for key in [*input_dict.keys()]:
        new_key = key.split(".")[1].replace("-", ".")
        input_dict[new_key] = input_dict.pop(key)
        if isinstance(input_dict[new_key], np.ndarray):
            input_dict[new_key] = input_dict[new_key].tolist()
    return input_dict
