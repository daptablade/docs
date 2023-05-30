from datetime import datetime


def setup(
    inputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    outputs: dict = {"design": {}, "implicit": {}, "setup": {}},
    parameters: dict = {
        "user_input_files": [],
        "inputs_folder_path": "",
        "outputs_folder_path": "",
    },
) -> dict:
    """A user editable setup function.

    Parameters
    ----------
    inputs: dict
        The component Inputs sorted by type (design, implicit or setup).
    outputs: dict
        The component Outputs sorted by type (design, implicit or setup).
    parameters: dict
        The component Parameters as defined in the component 'Parameters' tab.
        Includes the following special keys:
        'user_input_files': list of user-uploaded input file filenames
        'inputs_folder_path': path to all user and connection input files (str)
        'outputs_folder_path': path to component outputs folder (str)

    Returns
    -------
    dict
        dictionary of JSON-serialisable keys and values, including:
        inputs: dict, optional
            The setup function can assign values to input keys, but the inputs
            keys should not be modified.
        outputs: dict, optional
            The setup function can assign values to output keys, but the outputs
            keys should not be modified.
        parameters: dict, optional
            The setup function can add key/value pairs to the parameters dict,
            but the existing key/value pairs cannot be modified.
        partials: dict, optional
            The derivatives of the component's "design" outputs with respect to its
            "design" inputs, used for gradient-based design optimisation Runs.
        message: str, optional
            A setup message that will appear in the Run log.
    """

    # initalise setup_data keys
    response = {}

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Setup completed."
    print(message)
    response["message"] = message

    return response
