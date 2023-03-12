import os
from datetime import datetime
from pathlib import Path
from shutil import copy2

import time
from functools import wraps
from contextlib import redirect_stdout

import openvsp as vsp

stdout = vsp.cvar.cstdout
errorMgr = vsp.ErrorMgrSingleton_getInstance()

HOSTNAME = os.getenv("HOSTNAME")


def timeit(func):
    @wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(
            f"Elapsed time for function '{func.__name__}': {elapsed_time:0.4f} seconds"
        )
        return value

    return wrapper_timer


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
    """Wrapper around main function."""

    run_log = Path(parameters["outputs_folder_path"]) / f"run_{HOSTNAME}.log"
    with open(run_log, "a", encoding="utf-8") as f:
        with redirect_stdout(f):
            resp = main(inputs, outputs, partials, options, parameters)

    return resp


@timeit
def main(
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

    print(f"Starting VSPAERO run on {HOSTNAME} with: ", inputs["design"])

    # check that input files have been uploaded
    inputs_folder = Path(parameters["inputs_folder_path"])
    for file in ["vsp3_file", "des_file"]:
        if not (inputs_folder / parameters[file]).is_file():
            raise FileNotFoundError(
                f"{parameters[file]} needs to be uploaded by the user."
            )

    # copy input files to run folder
    run_folder = Path(parameters["outputs_folder_path"])
    for file in parameters["user_input_files"]:  # .vsp3 and .des files
        src = inputs_folder / file["filename"]
        copy2(src, run_folder / file["filename"])
    vsp_file = run_folder / parameters["vsp3_file"]
    des_file = run_folder / parameters["des_file"]

    # get inputs
    desvars = {
        k.split("_", 1)[1]: v
        for k, v in inputs["design"].items()
        if k.startswith("desvars_")
    }
    AoA = inputs["design"]["AoA"]
    # dynamically update trim desvars with input values
    desvars[parameters["HTP_RY_ID"]] = float(inputs["design"]["HTP_RY"])

    vsp.ClearVSPModel()
    vsp.Update()

    # read vsp3 input file
    vsp.ReadVSPFile(str(vsp_file))
    vsp.Update()

    # load the default OpenVSP design variables
    vsp.ReadApplyDESFile(str(des_file))
    vsp.Update()

    # get / set specific parameters by id - optional
    if desvars:
        for k, v in desvars.items():
            # vsp.GetParmVal(k)
            vsp.SetParmValUpdate(k, v)

    # create _DegenGeom.csv file input for VLM
    analysis_name = "VSPAEROComputeGeometry"
    vsp.SetAnalysisInputDefaults(analysis_name)
    method = list(vsp.GetIntAnalysisInput(analysis_name, "AnalysisMethod"))
    method[0] = vsp.VORTEX_LATTICE
    vsp.SetIntAnalysisInput(analysis_name, "AnalysisMethod", method)
    # vsp.PrintAnalysisInputs(analysis_name)
    vsp.ExecAnalysis(analysis_name)
    # vsp.PrintResults(resp)

    # setup VSPAERO - preconfigure everything else in the vsp3 file
    analysis_name = "VSPAEROSweep"
    vsp.SetAnalysisInputDefaults(analysis_name)
    wid = vsp.FindGeomsWithName("NormalWing")
    vsp.SetStringAnalysisInput(analysis_name, "WingID", wid, 0)
    vsp.SetDoubleAnalysisInput(analysis_name, "AlphaStart", (float(AoA),), 0)
    vsp.SetIntAnalysisInput(analysis_name, "AlphaNpts", (1,), 0)
    vsp.SetDoubleAnalysisInput(analysis_name, "MachStart", (0.0,), 0)
    vsp.SetIntAnalysisInput(analysis_name, "MachNpts", (1,), 0)
    vsp.Update()
    # # vsp.PrintAnalysisInputs(analysis_name)
    vsp.ExecAnalysis(analysis_name)
    # vsp.PrintResults(resp)

    # process outputs
    history_res = vsp.FindLatestResultsID("VSPAERO_History")
    # load_res = vsp.FindLatestResultsID("VSPAERO_Load")
    CL = vsp.GetDoubleResults(history_res, "CL", 0)
    CDtot = vsp.GetDoubleResults(history_res, "CDtot", 0)
    L2D = vsp.GetDoubleResults(history_res, "L/D", 0)
    E = vsp.GetDoubleResults(history_res, "E", 0)
    # cl = vsp.GetDoubleResults( load_res, "cl", 0 )
    CMy = vsp.GetDoubleResults(history_res, "CMy", 0)

    while errorMgr.GetNumTotalErrors() > 0:
        errorMgr.PopErrorAndPrint(stdout)

    outputs["design"]["CL"] = CL[-1]
    outputs["design"]["CMy"] = CMy[-1]
    outputs["design"]["CDtot"] = CDtot[-1]
    outputs["design"]["L2D"] = L2D[-1]
    outputs["design"]["E"] = E[-1]

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: VSPAERO Compute completed on host {HOSTNAME}."
    print(message)
    print(f"with:\nINPUTS: {str(inputs)},\nOUTPUTS: {str(outputs)}.")

    return {"message": message, "outputs": outputs}


if __name__ == "__main__":
    # for local testing only
    design_inputs = {"AoA": 0.0, "HTP_RY": 0.0, "desvars_PONPNSVRANE": 3.86}
    outputs = {"CL": 0.0, "CMy": 0.0, "CDtot": 0.0, "L2D": 0.0, "E": 0.0}
    options = {}
    parameters = {
        "desvars": {"PONPNSVRANE": 3.86},
        "AoA": 0.0,
        "HTP_RY": 0.0,
        "HTP_RY_ID": "ABCVDMNNBOE",
        "vsp3_file": "Cessna-210_metric.vsp3",
        "des_file": ".des",
        "outputs_folder_path": "../outputs",
        "inputs_folder_path": "../inputs",
        "user_input_files": [".des", "Cessna-210_metric.vsp3"],
    }
    response = main(
        inputs={"design": design_inputs},
        outputs={"design": outputs},
        partials=None,
        options=options,
        parameters=parameters,
    )
