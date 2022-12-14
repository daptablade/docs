from datetime import datetime
from pathlib import Path
import numpy as np


def compute(
    inputs: dict = None,
    outputs: dict = None,
    partials: dict = None,
    options: dict = None,
    parameters: dict = None,
) -> dict:

    """Editable compute function."""

    datfile = inputs["implicit"]["files.analysis_output_file"]
    mesh_file = inputs["implicit"]["files.mesh_file"]
    node_set_file = inputs["implicit"]["files.nodeset_file"]

    # check input files have been uploaded
    inputs_folder = Path(parameters["inputs_folder_path"])
    for f in [datfile, mesh_file, node_set_file]:
        if not (inputs_folder / f).is_file():
            raise FileNotFoundError(
                f"{f} param file connection needed from calculix-fea component."
            )

    print("Starting user function evaluation.")

    # recover the analysis results
    outputs["design"] = get_fea_outputs(
        datfile=datfile,
        mesh_file=mesh_file,
        node_set_file=node_set_file,
        folder=inputs_folder,
    )
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Completed fea output processing: \n{str(outputs)}"

    return {"message": message, "outputs": outputs}


def get_fea_outputs(datfile, mesh_file, folder, node_set_file):
    """Recover the analysis outputs and process them for plotting."""

    # read file and recover node displacements
    output_file = folder / datfile
    # all_disp : [nodeid, vx, vy, vz]
    all_disps = _get_from_dat(output_file, data="displacements")

    # get node ids for displacement output > read from LAST.nam file
    node_ids = np.array(
        _get_from_inp(file=Path(folder, node_set_file), keyword="NSET,NSET="),
        dtype=float,
    )

    # filter all_disp by node ids
    disp_filter = np.isin(all_disps[:, 0], node_ids)
    tip_disps = all_disps[disp_filter, :]

    # average the deflections
    v_mean = np.zeros((3))
    for disp in range(3):
        v_mean[disp] = np.average(tip_disps[:, disp + 1])

    # calculate the average rotations
    rotations_mean = _get_average_rotation(
        all_disps=tip_disps, mesh_file=folder / mesh_file
    )

    outputs = {
        "Ux": v_mean[0],
        "Uy": v_mean[1],
        "Uz": v_mean[2],
        "Rx": rotations_mean[0],
        "Ry": rotations_mean[1],
        "Rz": rotations_mean[2],
    }
    return outputs


########### Private functions that do not get called directly


def _get_from_dat(file, data: str = None):
    with open(file, "r", encoding="utf-8") as f:
        contents = f.readlines()

    # extract data assuming this is the only output
    for index, line in enumerate(contents):
        if data in line:
            data_values = contents[index + 2 :]
            break

    # parse data
    if data == "displacements":
        output = np.array(
            [
                [float(val) for val in line.strip().split()]
                for line in data_values
                if line
            ],
            dtype=float,
        )

    return output


def _get_from_inp(file, keyword: str = None):
    with open(file, "r", encoding="utf-8") as f:
        contents = f.readlines()

    # extract data
    read_flag = False
    data = []
    for line in contents:
        if "*" in line and keyword in line:
            read_flag = True
            continue
        if not "**" in line and "*" in line and not keyword in line:
            break
        if read_flag:
            data.append(line.strip().rstrip(",").split(","))

    return data


def _get_average_rotation(
    all_disps: np.ndarray = None,
    mesh_file: str = None,
    axes: tuple = (
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ),  # basic x, y, z axes
):
    # for each output node, recover the node undeformed mesh position
    # node_positions : [nodeid, x, y, z]
    node_positions = _get_nodes_from_inp(mesh_file, ref_nodes=all_disps[:, 0])

    origin_index = np.where(node_positions[:, 1] == 0.0)[0][0]  # LE
    # calculate the approximate rotation from each node
    rotations = _get_rot_from_disp(all_disps, node_positions, axes, origin_index)

    # average the rotation values
    rotations_mean = np.zeros((3))
    for rot in rotations:
        rotations_mean[rot] = np.average(rotations[rot])

    return rotations_mean


def _get_nodes_from_inp(file, ref_nodes=None):
    with open(file, "r", encoding="utf-8") as f:
        contents = f.readlines()

    # find node definitions in the file
    start = None
    nodes = []
    for index, line in enumerate(contents):
        if "*NODE" in line:
            start = index + 1
        elif start and "*" in line:  # marks the next keyword
            break
        elif start and index >= start:
            nodes.append(line)

    # parse to array
    nodes_vals = np.array(
        [[float(val) for val in line.strip().split(",")] for line in nodes if line],
        dtype=float,
    )

    # filter reference nodes
    if any(ref_nodes):
        nodes_vals = np.array(
            [line for line in nodes_vals if any(line[0] == ref_nodes)], dtype=float
        )

    return nodes_vals


def _get_rot_from_disp(all_disps, node_positions, axes, origin_index):
    """Return an array of rotations in radians. Using small deflection assumptions."""

    all_rots = {key: [] for key in range(len(axes))}
    origin_displacements = all_disps[origin_index, 1:]
    origin_location = node_positions[origin_index, 1:]
    # loop throught the nodes and y rotation axes
    for index, node in enumerate(node_positions):
        # vector from origin to node position
        v_op = node[1:] - origin_location
        if np.linalg.norm(v_op) > 0:  # skip the origin
            for col, axis in enumerate(axes):
                # calculate local rotation unit vector
                v_r = np.cross(axis, v_op)
                if np.linalg.norm(v_r) > 0.0:
                    v_r = v_r / np.linalg.norm(v_r)
                    d_vect = np.cross(v_r, axis)  # this should already be a unit vector
                    dist_from_axis = v_op @ d_vect / np.linalg.norm(d_vect)
                    # calculate local rotation at the centroid
                    rot = np.arctan(
                        ((all_disps[index, 1:] - origin_displacements) @ v_r)
                        / dist_from_axis
                    )
                    all_rots[col].append(rot)
                else:
                    print(
                        f"Skip point [{str(node)}] on the local rotation axis {str(axis)}."
                    )

    return all_rots
