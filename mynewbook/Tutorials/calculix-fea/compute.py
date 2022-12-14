import shutil
from datetime import datetime
from pathlib import Path
from shutil import copy2

import numpy as np
from scipy.spatial.transform import Rotation

from calculix import execute_cgx, execute_fea

PLOT_FLAG = True


def compute(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    parameters: dict = None,
) -> dict:

    """Editable compute function."""

    # check input files have been uploaded
    inputs_folder = Path(parameters["inputs_folder_path"])
    if not (inputs_folder / inputs["implicit"]["files.cgx_file"]).is_file():
        raise FileNotFoundError(
            f"{inputs['implicit']['files.cgx_file']} param file connection needed from parametric-model component."
        )
    if not (inputs_folder / parameters["analysis_file"]).is_file():
        raise FileNotFoundError(
            f"{parameters['analysis_file']} needs to be uploaded by the user."
        )

    print("Starting user function evaluation.")

    run_folder = Path(parameters["outputs_folder_path"])
    # Generate the ccx input mesh with cgx
    infile = copy2(
        inputs_folder / inputs["implicit"]["files.cgx_file"],
        run_folder / inputs["implicit"]["files.cgx_file"],
    )
    resp = execute_cgx(infile.name, run_folder=run_folder)
    with open(run_folder / "cgx.log", "w") as f:
        f.write(resp)

    # check output has been saved
    mesh_file_path = run_folder / parameters["mesh_file"]
    if not mesh_file_path.is_file():
        FileNotFoundError(f"{str(mesh_file_path)} is not a file.")
    print("Created CCX analysis mesh file with CGX.")

    # define composite material properties
    if "composite_layup" in parameters:

        fibre_rotation_angles = [
            key for key in inputs["design"] if key.startswith("fibre_rotation_angle")
        ]
        for angle in fibre_rotation_angles:
            # rotate a fibre direction in the orientations parameter
            tree = angle.split(".")
            id = tree[1]
            direction = tree[2]
            ori_index = [ori["id"] == id for ori in parameters["orientations"]].index(
                True
            )
            parameters["orientations"][ori_index][direction] = _rotate_vector(
                angle=float(inputs["design"][angle]),
                starting=parameters["orientations"][ori_index][direction],
                axis=[0.0, 0.0, 1.0],
            )
            print(
                f"Orientation {id} direction {direction} set to {str(parameters['orientations'][ori_index][direction])}"
            )

        get_composite_properties_input(parameters, run_folder)
        print("Created CCX composite properties file.")

    # run the FEM model analysis
    infile = copy2(
        inputs_folder / parameters["analysis_file"],
        run_folder / parameters["analysis_file"],
    )
    resp = execute_fea(infile.stem, run_folder=run_folder)
    with open(run_folder / "ccx.log", "w") as f:
        f.write(resp)

    # check output has been saved
    outfile = run_folder / (infile.stem + ".dat")
    if not outfile.is_file():
        FileNotFoundError(f"{str(outfile)} is not a file.")
    print("Executed CCX FEM analysis.")

    # set outputs
    # outputs = {"output_files": [outfile.name]}
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Executed Calculix finite element analysis."
    print(message)

    outputs["implicit"]["files.analysis_output_file"] = outfile.name
    outputs["implicit"]["files.mesh_file"] = "all.msh"
    outputs["implicit"]["files.nodeset_file"] = "LAST.nam"

    return {"message": message, "outputs": outputs}


def get_composite_properties_input(inputs, run_folder):
    """write an FEA input file with the composite properties."""

    # check and update the element type in the mesh input file
    str_find = "*ELEMENT, TYPE=S8,"
    str_replace = "*ELEMENT, TYPE=S8R,"
    _file_find_replace(
        file=(run_folder / inputs["mesh_file"]),
        find=str_find,
        replace_with=str_replace,
    )

    if "filled_sections_flags" in inputs and not isinstance(
        inputs["filled_sections_flags"], list
    ):
        inputs["filled_sections_flags"] = [inputs["filled_sections_flags"]]

    shell_set_name = inputs["shell_set_name"]
    if "filled_sections_flags" in inputs and any(inputs["filled_sections_flags"]):

        if not (
            isinstance(inputs["airfoil_cut_chord_percentages"], list)
            and len(inputs["airfoil_cut_chord_percentages"]) == 2
        ):
            raise ValueError(
                "if 'filled_sections_flags' is switched on, 'airfoil_cut_chord_percentages'"
                "should be a list of length 2."
            )

        # create separate element sets for shells and solids
        str_find = "*ELEMENT, TYPE=S8R, ELSET=Eall"
        str_replace = "*ELEMENT, TYPE=S8R, ELSET=SURF"
        _file_find_replace(
            file=(run_folder / inputs["mesh_file"]),
            find=str_find,
            replace_with=str_replace,
        )
        str_find = "*ELEMENT, TYPE=C3D20, ELSET=Eall"
        str_replace = "*ELEMENT, TYPE=C3D20, ELSET=CORE"
        _file_find_replace(
            file=(run_folder / inputs["mesh_file"]),
            find=str_find,
            replace_with=str_replace,
        )

    # get input file cards for this solver
    ccx_commands = _get_ccx_composite_shell_props(
        plies=inputs["composite_plies"],
        orientations=inputs["orientations"],
        layup=inputs["composite_layup"],
        shell_set_name=shell_set_name,
    )

    # write string of commands to file
    with open(run_folder / inputs["composite_props_file"], "w", encoding="utf-8") as f:
        f.write("".join(ccx_commands))


########### Private functions that do not get called directly


def _file_find_replace(file, find: str, replace_with: str):
    with open(file, "r", encoding="utf-8") as f:
        contents = f.readlines()

    for index, line in enumerate(contents):
        if find in line:
            contents[index] = line.replace(find, replace_with)
            print(f"Find & Replace edited file '{file}' at line {index:d}.")
            break

    with open(file, "w", encoding="utf-8") as f:
        f.write("".join(contents))


def _get_ccx_composite_shell_props(
    plies=None, orientations=None, layup=None, shell_set_name=None
):

    commands = []
    if not shell_set_name:
        shell_set_name = {"ribs": "ERIBS", "aero": "EAERO"}

    # orientation cards
    for ori in orientations:
        commands.append(f"*ORIENTATION,NAME={ori['id']}\n")
        commands.append(", ".join(str(x) for x in [*ori["1"], *ori["2"]]) + "\n")

    commands.append("** =============== \n")
    # shell property
    for (key, section_name) in shell_set_name.items():
        commands.append(f"*SHELL SECTION,ELSET={section_name},COMPOSITE\n")
        for ply in layup[key]:
            props = [p for p in plies if p["id"] == ply][0]
            commands.append(
                f"{props['thickness']:6f},,{props['material']},{props['orientation']}\n"
            )

    return commands


def _rotate_vector(angle, starting, axis):
    """Rotate a vector about an axis by an angle in degrees."""

    r = Rotation.from_rotvec(angle * np.array(axis), degrees=True)
    return r.apply(starting)
