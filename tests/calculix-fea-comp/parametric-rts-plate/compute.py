""" Create a 3D element mesh for the RTS panel buckling analysis. """

from shutil import copy2
from datetime import datetime
from pathlib import Path
from math import sqrt, floor, ceil, cos, sin, radians, log10
import numpy as np
import itertools

import time
from functools import wraps
from contextlib import redirect_stdout

from calculix import execute_cgx, execute_fea

PARAMS = {
    "length_x": 1.250,
    "width_y": 0.75,
    "split_at_x": [0.25, 1.0],
    "split_at_y": [0.25, 0.5],
    "boundary_conditions": {
        "fixed_y0": {"lines": [0, 1, 2], "SPC": "23"},
        "fixed_x0": {"lines": [9, 10, 11], "SPC": "13"},
        "support_z": {
            "lines": range(12, 24),
            "SPC": "3",
        },
        "support_ymax": {
            "lines": [6, 7, 8],
            "kinematic": "23",
            "ref_node_SPC": "34",
            "surface_vector": [0.0, 1.0, 0.0],
        },
        "loaded_xmax": {
            "lines": [3, 4, 5],
            "kinematic": "13",
            "ref_node_SPC": "35",
            "surface_vector": [1.0, 0.0, 0.0],
            "ref_node_forces": [-750000.0, 0.0, 0.0],
        },
    },
    "edge_length": 0.025,
    "material": {
        "E1": 163.0e9,
        "E2": 12.0e9,
        "nu12": 0.3,
        "G12": 5.0e9,
        "thickness": 0.000125,
        "density": 1571.0,
        "tape_width": 0.100,
        "stress_allowables": {},
        "name": "IM7_8552",
        "description": " Units are: kg, m; data from Groh_2015.",
    },
    "plies": [
        {
            "path_start": [0, 0, 0],
            "path_end": [0, 0.750, 0],
            "ply_ref_angle": 90.0,
            "ply_ref_thickness_multiplier": 33.941125496954285,
            "combine_plus_minus_plies": True,
            "control_pts": [
                {"d": -0.01, "inc_angle": 45.0, "id": "T0"},
                {"d": 0.760, "inc_angle": 45.0, "id": "T1"},
            ],
        }
    ],
    "mesh_files": {
        "mesh": "all.msh",
        "solid_mesh": "solid_mesh.inp",
        "materials": "materials.inp",
        "element_sets": "element_sets.inp",
        "solid_sections": "solid_sections.inp",
        "node_sets": "node_sets.inp",
        "surfaces": "surfaces.inp",
        "constraints": "constraints.inp",
        "loads": "loads.inp",
    },
    "analysis_file": "ccx_compression_buckle.inp",
    "number_of_modes": 10,
    "user_input_files": [],
    "inputs_folder_path": Path(__file__).parent,
    "outputs_folder_path": Path(__file__).parent / "outputs",
}


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

    """Editable compute function."""
    run_folder = Path(parameters["outputs_folder_path"])
    with open(run_folder / "run.log", "w") as f:
        with redirect_stdout(f):
            resp = main(
                inputs=inputs,
                outputs=outputs,
                partials=partials,
                options=options,
                parameters=parameters,
            )

    return resp


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
):

    inputs_folder = Path(parameters["inputs_folder_path"])
    if not (inputs_folder / parameters["analysis_file"]).is_file():
        raise FileNotFoundError(
            f"{parameters['analysis_file']} needs to be uploaded by the user."
        )

    print("Starting user function evaluation.")

    run_folder = Path(parameters["outputs_folder_path"])

    # set design variables
    if inputs["design"]:
        input_data = inputs["design"]  # ["ply-ctrl_pt_id-inc_angle": value, ]
        for key, value in input_data.items():
            k = key.strip().split("-")
            ply = int(k[0])
            ctrl_pt_id = k[1]
            var_key = k[2]
            for pt in parameters["plies"][ply]["control_pts"]:
                if pt["id"] == ctrl_pt_id:
                    pt[var_key] = value
        print("Applied design inputs.")

    # 1) Define a 2D mould surfaces in CGX and generate the 2D mesh
    cgx_input_file = get_geometry(
        length_x=parameters["length_x"],
        width_y=parameters["width_y"],
        split_at_x=parameters["split_at_x"],
        split_at_y=parameters["split_at_y"],
        boundary_conditions=parameters["boundary_conditions"],
        edge_length=parameters["edge_length"],
        run_folder=run_folder,
    )
    resp = execute_cgx(infile=cgx_input_file.name, run_folder=run_folder)
    with open(run_folder / "cgx.log", "w") as f:
        f.write(resp["stdout"])
    if not resp["returncode"] == 0:
        raise ChildProcessError(
            f'cgx returned non-zero exit status {resp["returncode"]}'
        )

    # read the 2D mesh from CGX output file
    elements, nodes, constraints = get_2Dmesh(
        mesh_files=parameters["mesh_files"],
        run_folder=run_folder,
        bcs=parameters["boundary_conditions"],
    )

    # 2) Calculate the element normals, and then the node normal
    corner_nodes = set()
    set_element_normals(elements=elements, nodes=nodes, corner_nodes=corner_nodes)
    set_node_normals(nodes=nodes, elements=elements)

    # 3) Offset the 2D mesh nodes by local thickness distribution for each laminate substack
    nid_offset = 10 ** ceil(log10(max(nodes.keys())))
    eid_offset = 10 ** ceil(log10(max(elements.keys())))

    materials = {}
    element_sets = {}
    set_name_format = "P{:d}_A{:d}"
    for plyid, ply in enumerate(parameters["plies"]):
        # define functions to interpolate rts ply local properties
        f_inc_angle, f_thickness, upath = get_rts_distributions(
            ply, ref_thickness=parameters["material"]["thickness"]
        )
        offset_nodes(
            plyid,
            nodes,
            constraints,
            f_inc_angle,
            f_thickness,
            upath,
            set_of_corner_nodes=corner_nodes,
            start=np.array(ply["path_start"]),
            nid_offset=nid_offset,
        )

        # 4) create 3D elements from 2D mesh and offset nodes
        offset_elements(
            plyid,
            elements,
            element_sets,
            constraints,
            f_inc_angle,
            f_thickness,
            upath,
            start=np.array(ply["path_start"]),
            eid_offset=eid_offset,
            nid_offset=nid_offset,
            nodes=nodes,
        )

        # 5) calculate the local material properties for each group of elements from the reference angle and shearing angles
        set_materials(
            plyid,
            materials,
            list(element_sets[plyid].keys()),
            ply,
            parameters["material"],
            nformat=set_name_format,
        )

    # calculate reference node positions for the kinematic constraints
    update_kinematic_constraints_ref_nodes(
        constraints, nodes, offset=nid_offset * ((plyid + 1) * 2 + 1)
    )
    # calculate the plate mass from elements
    volume = get_volume(elements)
    mass = volume * parameters["material"]["density"]

    # 6) output the mesh to file
    fname = parameters["mesh_files"]
    write_solid_mesh(nodes, elements, run_folder=run_folder, file=fname["solid_mesh"])
    write_materials(materials, run_folder=run_folder, file=fname["materials"])
    write_element_sets(
        element_sets, set_name_format, run_folder=run_folder, file=fname["element_sets"]
    )
    write_solid_sections(
        materials, set_name_format, run_folder=run_folder, file=fname["solid_sections"]
    )

    write_node_sets(constraints, run_folder=run_folder, file=fname["node_sets"])
    write_surface(constraints, run_folder=run_folder, file=fname["surfaces"])
    write_constraints(constraints, run_folder=run_folder, file=fname["constraints"])
    write_loading(constraints, run_folder=run_folder, file=fname["loads"])

    print("Created CCX solid mesh files.")

    # 7) Perform ccx FEM analysis
    infile = copy2(
        inputs_folder / parameters["analysis_file"],
        run_folder / parameters["analysis_file"],
    )
    resp = execute_fea(infile.stem, run_folder=run_folder)
    with open(run_folder / "ccx.log", "w") as f:
        f.write(resp["stdout"])
    if not resp["returncode"] == 0:
        raise ChildProcessError(
            f'ccx returned non-zero exit status {resp["returncode"]}'
        )

    # check output has been saved
    outfile = run_folder / (infile.stem + ".dat")
    if not outfile.is_file():
        FileNotFoundError(f"{str(outfile)} is not a file.")
    print("Executed CCX FEM analysis.")

    buckling_factors = get_buckling_factors(
        outfile, number_modes=parameters["number_of_modes"]
    )

    outputs = {"mass": mass, "buckling_factors": buckling_factors}
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Executed Calculix finite element analysis."
    print(message)

    return {"message": message, "outputs": outputs}


@timeit
def get_geometry(
    length_x,
    width_y,
    split_at_x,
    split_at_y,
    boundary_conditions,
    edge_length,
    fname="cgx_2d_mesh.fdb",
    run_folder=None,
):

    # corner points 1-4
    points = [[0.0, 0.0], [length_x, 0.0], [length_x, width_y], [0.0, width_y]]

    # side points
    points.extend(
        [
            [split_at_x[0], 0.0],
            [split_at_x[1], 0.0],
            [length_x, split_at_y[0]],
            [length_x, split_at_y[1]],
            [split_at_x[1], width_y],
            [split_at_x[0], width_y],
            [0.0, split_at_y[1]],
            [0.0, split_at_y[0]],
        ]
    )

    # mid-panel nodes
    points.extend(
        [
            [split_at_x[0], split_at_y[0]],
            [split_at_x[1], split_at_y[0]],
            [split_at_x[1], split_at_y[1]],
            [split_at_x[0], split_at_y[1]],
        ]
    )
    # all at z = 0
    [p.append(0.0) for p in points]

    # Lines 0 to 11 are the outside bounds defined by point indices
    lines = [
        [0, 4],  # 0
        [4, 5],
        [5, 1],
        [1, 6],
        [6, 7],  # 4
        [7, 2],
        [2, 8],
        [8, 9],
        [9, 3],  # 8
        [3, 10],
        [10, 11],
        [11, 0],
    ]

    # split lines 12 to 23 defined by point indices
    lines.extend(
        [
            [4, 12],  # 12
            [5, 13],
            [6, 13],
            [7, 14],
            [8, 14],  # 16
            [9, 15],
            [10, 15],
            [11, 12],
            [12, 13],  # 20
            [13, 14],
            [14, 15],
            [15, 12],
        ]
    )
    # add number of elements per edge
    def nele(pt1, pt2, edge):
        p1 = points[pt1]
        p2 = points[pt2]
        l = sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)
        return floor(l / edge)

    [line.append(nele(line[0], line[1], edge_length)) for line in lines]

    # surfaces defined by line indices (negative for direction reversal)
    surfaces = [
        [0, 12, -19, 11],
        [1, 13, -20, -12],
        [2, 3, 14, -13],
        [4, 15, -21, -14],
        [5, 6, 16, -15],
        [7, 17, -22, -16],
        [8, 9, 18, -17],
        [10, 19, -23, -18],
        [20, 21, 22, 23],
    ]

    commands = get_commands(points, lines, surfaces, boundary_conditions)

    # write string of commands to file
    with open(run_folder / fname, "w", encoding="utf-8") as f:
        f.write("".join(commands))
    cgx_input_file = run_folder / fname

    return cgx_input_file


def divide_chunks(l, n):
    if not isinstance(l, list):
        l = list(l)
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i : i + n]


@timeit
def get_commands(
    points,
    lines,
    surfaces,
    boundary_conditions,
    max_entries_per_line=9,
    cgx_ele_type=10,  # s8 elements
    nele_multiplier=2,  # for s8 elements
    merge_tol=0.001,
    solver="abq",
):
    """create string of all cgx input commands"""

    commands = []
    # points
    for entity_id, point in enumerate(points):
        commands.append(
            f"PNT P{entity_id:05d} {point[0]:e} {point[1]:e} {point[2]:e}\n"
        )
    commands.append("# =============== \n")
    # lines
    for entity_id, line in enumerate(lines):
        if len(line) == 3:  # straight line
            commands.append(
                f"LINE L{entity_id:05d} P{line[0]:05d} P{line[1]:05d} {line[2]*nele_multiplier:d} \n"
            )
    commands.append("# =============== \n")
    # surfaces
    for entity_id, surf in enumerate(surfaces):
        commands.append(
            f"GSUR V{entity_id:05d} + BLEND "
            + " ".join(
                [f"+ L{line:05d}" if line >= 0 else f"- L{-line:05d}" for line in surf]
            )
            + "\n"
        )
    commands.append("# =============== \n")
    # SPC and load sets
    for name, bc in boundary_conditions.items():
        for chunk in divide_chunks(bc["lines"], max_entries_per_line):
            commands.append(
                f"SETA {name.upper()} l "
                + " ".join([f"L{int(line):05d}" for line in chunk])
                + "\n"
            )
    commands.append("# =============== \n")
    # surface meshes
    for entity_id, _ in enumerate(surfaces):
        commands.append(f"MSHP V{entity_id:05d} s {cgx_ele_type:d} 0 1.000000e+00\n")
    commands.append("# =============== \n")
    # custom export statement
    commands.append("mesh all\n")
    commands.append(f"merg n all {merge_tol:6f} 'nolock'\n")
    commands.append("comp nodes d\n")
    for name, bc in boundary_conditions.items():
        commands.append(f"comp {name.upper()} d\n")
        # commands.append(f"send {name.upper()} {solver} spc {bc['SPC']}\n")
        commands.append(f"send {name.upper()} {solver} names\n")
    commands.append("# =============== \n")
    commands.append(f"send all {solver} \n")
    commands.append("quit\n")

    return commands


@timeit
def get_2Dmesh(mesh_files, run_folder, bcs):

    elements, nodes = get_nodes_and_elements(run_folder, file=mesh_files["mesh"])
    constraints = get_constraints(run_folder, bcs=bcs)

    return elements, nodes, constraints


def get_nodes_and_elements(run_folder, file):

    with open(run_folder / file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    read_nodes = False
    read_elements = False
    ele_type = None
    nodes = {}
    elements = {}
    for line in lines:
        if line.startswith("*NODE"):  # all nodes in one set assumed
            print("start reading nodes.")
            read_nodes = True
            read_elements = False
            ele_type = None
            continue
        elif line.startswith("*ELEMENT"):  # all elements in one set assumed
            print("start reading elements.")
            read_nodes = False
            read_elements = True
            ele_type = {
                data.split("=")[0].strip(): data.split("=")[1].strip()
                for data in line.split(",")
                if "=" in data
            }["TYPE"]
            continue
        elif read_nodes:
            data = line.split(",")
            # parse nodes into { ID: {"global_xyz": [x,y,z]}}
            nodes[int(data[0])] = {"global_xyz": [float(v) for v in data[1:]]}
        elif read_elements:
            data = line.split(",")
            # parse elements into { ID: {"type": S8, "nodes": [1-8]}}
            elements[int(data[0])] = {
                "type": ele_type,
                "nodes": [int(v) for v in data[1:]],
            }

    return elements, nodes


def get_constraints(run_folder, bcs):

    all_constrained_nodes = set()

    def get_constraint_starting_nodes(constraints):
        for cname, constraint in constraints.items():
            with open(
                run_folder / (cname.upper() + ".nam"), "r", encoding="utf-8"
            ) as f:
                lines = f.readlines()

            read_nodes = False
            for line in lines:
                if line.startswith("*NSET"):
                    print(f"start reading node set {cname}.")
                    read_nodes = True
                    continue
                elif read_nodes:
                    data = line.split(",")
                    if int(data[0]) not in all_constrained_nodes:
                        constraint["nodes"].add(int(data[0]))
                        all_constrained_nodes.add(int(data[0]))
                    else:
                        print(
                            f"Node {int(data[0])} is removed from constraint {cname.upper()} as it is already constrained."
                        )

    constraints = {"SPCs": {}, "kinematic_MPCs": {}}
    for cname, constraint in bcs.items():

        if "SPC" in constraint:
            ctype = "SPCs"
            constraints[ctype][cname] = {"nodes": set(), **constraint}
        elif "kinematic" in constraint:
            ctype = "kinematic_MPCs"
            constraints[ctype][cname] = {"nodes": set(), "faces": set(), **constraint}

    # get constraints in order to avoid over-constraining nodes where constraints overlap
    get_constraint_starting_nodes(
        constraints["kinematic_MPCs"]
    )  # define face constraints first
    get_constraint_starting_nodes(
        constraints["SPCs"]
    )  # exclude nodes in face constraints

    return constraints


@timeit
def set_element_normals(elements, nodes, corner_nodes):

    for _, element in elements.items():
        centroid = [0.0, 0.0, 0.0]
        for nid in element["nodes"]:
            xyz = nodes[nid]["global_xyz"]
            centroid = [c1 + c2 for c1, c2 in zip(centroid, xyz)]
        centroid = [c / len(element["nodes"]) for c in centroid]
        element["global_xyz"] = centroid

        ## TODO for each element normal is the average of the normals calculated at the elemnent nodes from the element edges ( sum of vectors / nb nodes)
        # (assume n = [0,0,1] for the flat panel)
        element["normal"] = [0.0, 0.0, 1.0]
        if element["type"] == "S8":
            corner_nodes.update(element["nodes"][:4])

    return None


@timeit
def set_node_normals(nodes, elements):

    for nid in nodes:
        ## TODO for each node, find the connected elements and average normal at the node as sum of vectors / nb connected elements
        # (assume n = [0,0,1] for the flat panel)
        nodes[nid]["normal"] = [0.0, 0.0, 1.0]

    return None


def piecewise_linear_angle_interp(x, ranges, ctrl_points):
    f_angles = lambda x, a0, a1, d0, d1: round((a1 - a0) / (d1 - d0) * (x - d0) + a0)
    for d, a in zip(ranges, ctrl_points):
        if x >= d[0] and x < d[1]:
            return f_angles(x, a[0], a[1], d[0], d[1])
    raise ValueError(f"x value {x} is outside control point range.")


@timeit
def get_rts_distributions(ply, ref_thickness):

    # get path unit vector
    upath = np.array(ply["path_end"]) - np.array(ply["path_start"])
    upath = upath / np.linalg.norm(upath)

    # linear interpolation
    ranges = []
    ctrl_points = []
    for p0, p1 in zip(ply["control_pts"][:-1], ply["control_pts"][1:]):
        ranges.append((p0["d"], p1["d"]))
        ctrl_points.append((p0["inc_angle"], p1["inc_angle"]))

    # input to f_inc_angle is dot product of upath with vector from path start to node
    f_inc_angle = {
        "f": piecewise_linear_angle_interp,
        "args": [ranges, ctrl_points],
    }
    f_thickness = (
        lambda x: ply["ply_ref_thickness_multiplier"] * ref_thickness / cos(radians(x))
    )

    return f_inc_angle, f_thickness, upath


def project_to_point(xyz, start, upath, f_inc_angle, f_thickness):
    vector2node = np.array(xyz) - start
    projected_length = np.dot(upath, vector2node)
    inc_angle = f_inc_angle["f"](projected_length, *f_inc_angle["args"])
    thickness = f_thickness(inc_angle)
    return {"inc_angle": inc_angle, "thickness": thickness}


def offset_point_by_vector(magnitude, vector, pt):
    return [c + v * magnitude for v, c in zip(vector, pt)]


@timeit
def offset_nodes(
    plyid,
    nodes,
    constraints,
    f_inc_angle,
    f_thickness,
    upath,
    set_of_corner_nodes,
    start,
    nid_offset,
):
    ## project the shearing angle and thickness values to the model nodes and centroids in a direction normal to upath
    for nid, node in list(nodes.items()):
        # filter nodes by ID - take only nodes at the bottom of the current layer
        if nid > plyid * 2 * nid_offset and nid < (plyid * 2 + 1) * nid_offset:
            props = project_to_point(
                node["global_xyz"],
                start,
                upath,
                f_inc_angle,
                f_thickness,
            )
            thickness = props["thickness"]
            # save offset nodes
            new_nids = []
            if nid - plyid * 2 * nid_offset in set_of_corner_nodes:
                nodes[nid + nid_offset] = {
                    "normal": node["normal"],
                    "global_xyz": offset_point_by_vector(
                        thickness / 2, node["normal"], node["global_xyz"]
                    ),
                }  # mid-height node
                new_nids.append(nid + nid_offset)
            nodes[nid + nid_offset * 2] = {
                "normal": node["normal"],
                "global_xyz": offset_point_by_vector(
                    thickness, node["normal"], node["global_xyz"]
                ),
            }  # top node
            new_nids.append(nid + nid_offset * 2)
            # update the spc constraint node sets
            for cname, constraint in constraints["SPCs"].items():
                if nid in constraint["nodes"]:
                    constraint["nodes"].update(new_nids)

    return None


@timeit
def offset_elements(
    plyid,
    elements,
    element_sets,
    constraints,
    f_inc_angle,
    f_thickness,
    upath,
    start,
    eid_offset,
    nid_offset,
    nodes,
):

    # element faces from ccx manual for C3D20/ C3D20R elements
    faces = {
        "S1": [n - 1 for n in (1, 2, 3, 4)],
        "S2": [n - 1 for n in (5, 8, 7, 6)],
        "S3": [n - 1 for n in (1, 5, 6, 2)],
        "S4": [n - 1 for n in (2, 6, 7, 3)],
        "S5": [n - 1 for n in (3, 7, 8, 4)],
        "S6": [n - 1 for n in (4, 8, 5, 1)],
    }

    ## TODO check that the offset values at each node are small compared to the edge
    # lengths of the connected elements (<1/5 edge?) to avoid badly shaped elements
    ## project the shearing angle and thickness values to the model nodes and centroids in a direction normal to upath
    element_sets[plyid] = {}
    for eid, element in list(elements.items()):
        # filter 2D elements - reference for the property calculation
        if element["type"] == "S8":
            props = project_to_point(
                element["global_xyz"],
                start,
                upath,
                f_inc_angle,
                f_thickness,
            )
            inc_angle = props["inc_angle"]
            thickness = props["thickness"]
            # save offset element
            new_eid = eid + eid_offset * (plyid + 1)
            nids = [
                *[
                    n + nid_offset * 2 * plyid for n in element["nodes"][:4]
                ],  # base corners
                *[
                    n + nid_offset * 2 * (1 + plyid) for n in element["nodes"][:4]
                ],  # top corners
                *[
                    n + nid_offset * 2 * plyid for n in element["nodes"][4:]
                ],  # base mid-side
                *[
                    n + nid_offset * 2 * (1 + plyid) for n in element["nodes"][4:]
                ],  # top mid-side
                *[
                    n + nid_offset * (1 + 2 * plyid) for n in element["nodes"][:4]
                ],  # mid-height nodes
            ]
            volume = hexahedron_volume_from_nodes(nids[:8], nodes)
            elements[new_eid] = {
                "global_xyz": offset_point_by_vector(
                    thickness * (plyid + 1 / 2),
                    element["normal"],
                    element["global_xyz"],
                ),
                "type": "C3D20R",
                "inc_angle": inc_angle,
                "t": thickness,
                "nodes": nids,
                "volume": volume,
            }
            # Create sets of elements by ply and common inc_angle.
            if inc_angle in element_sets[plyid]:
                element_sets[plyid][inc_angle].append(new_eid)
            else:
                element_sets[plyid][inc_angle] = [new_eid]
            # update kinematic constraints if needed
            update_kinematic_constraints(constraints, nids, faces, new_eid, nodes)

    return None


def hexahedron_volume_from_nodes(nids, nodes):

    n = lambda i: np.array(nodes[nids[i - 1]]["global_xyz"])
    # sum the volume of the 5 tetrahedrons composing the hex
    volume = 0.0
    for tet in (
        (n(1), n(2), n(4), n(5)),
        (n(3), n(2), n(4), n(7)),
        (n(5), n(6), n(7), n(2)),
        (n(5), n(7), n(8), n(4)),
        (n(2), n(4), n(7), n(5)),
    ):
        volume += get_tetrahedron_volume(tet)
    return volume


def get_tetrahedron_volume(tet):
    if not all([isinstance(n, np.ndarray) for n in tet]) or not len(tet) == 4:
        raise ValueError(
            "input should be list of 4 np.array(xyz) coordinates of tet corners."
        )
    matrix = np.array(
        [
            tet[0] - tet[3],
            tet[1] - tet[3],
            tet[2] - tet[3],
        ]
    )
    return 1 / 6 * np.abs(np.linalg.det(matrix))


def update_kinematic_constraints(constraints, nids, faces, new_eid, nodes):
    # update the kinematic constraint node sets and face=(element,faceID) sets

    # NOTE:
    # the function is exited after the first constraint on an element is found,
    # this avoids over-constraining element nodes, which results in error messages

    iterables = [constraints["kinematic_MPCs"].values(), faces.items()]
    for constraint, (face, face_node_indices) in list(itertools.product(*iterables)):
        face_nids = [nids[i] for i in face_node_indices]
        if any([n in constraint["nodes"] for n in face_nids]):
            face_nodes = [nodes[i] for i in face_nids]
            face_vector = get_surface_normal_from_nodes(face_nodes)
            if np.dot(
                face_vector, np.array(constraint["surface_vector"])
            ) > 0.9 * np.linalg.norm(face_vector):
                # update the face set
                constraint["faces"].add((new_eid, face))
                # update the node set
                constraint["nodes"].update(face_nids)
                return


def get_volume(elements):
    volume = 0.0
    for e in elements.values():
        if e["type"] == "C3D20R":
            volume += e["volume"]
    return volume


@timeit
def update_kinematic_constraints_ref_nodes(constraints, nodes, offset):
    nid = offset + 1
    for constraint in constraints["kinematic_MPCs"].values():
        face_nodes = [nodes[i] for i in constraint["nodes"]]
        constraint["ref_node"] = {nid: {"global_xyz": get_mid_point(face_nodes)}}
        nid += 1


def get_surface_normal_from_nodes(nodes: list) -> np.ndarray:
    # assumes coplanar nodes on face by only using first 3 nodes
    if not len(nodes) >= 3:
        raise ValueError("Need at least 3 nodes to calculate surface normal vector.")
    v01 = np.array(nodes[1]["global_xyz"]) - np.array(nodes[0]["global_xyz"])
    v02 = np.array(nodes[2]["global_xyz"]) - np.array(nodes[0]["global_xyz"])
    # TODO check angle between vectors is > 10
    # deg?
    return np.cross(v02, v01)  # order so that the norm points out of the element


def get_mid_point(face_nodes):
    # find the average xyz position from a set of nodes
    mid_point = np.zeros(3)
    for node in face_nodes:
        mid_point += np.array(node["global_xyz"])
    mid_point /= len(face_nodes)
    return list(mid_point)


@timeit
def set_materials(plyid, materials, set_inc_angles, ply, ref_material, nformat):

    # get composite ply Q matrix
    q_matrix = get_Qmatrix(ref_material)

    # calculate D from A/t, from the Q matrix and from the fibre angles
    set_D_matrix(plyid, materials, q_matrix, ply, set_inc_angles, ref_material, nformat)

    return None


def get_Qmatrix(material):

    modulus_E1 = material["E1"]
    modulus_E2 = material["E2"]
    pr_nu12 = material["nu12"]
    modulus_G12 = material["G12"]
    pr_nu21 = pr_nu12 * modulus_E2 / modulus_E1

    denominator = 1 - pr_nu12 * pr_nu21
    q11 = modulus_E1 / denominator
    q22 = modulus_E2 / denominator
    q12 = pr_nu12 * modulus_E2 / denominator
    q66 = modulus_G12

    return np.array([[q11, q12, 0.0], [q12, q22, 0.0], [0.0, 0.0, q66]])


def rotate_q_matrix(angle, q):

    s = lambda angle: sin(radians(angle))
    c = lambda angle: cos(radians(angle))
    T_mat = np.array(
        [
            [c(angle) ** 2, s(angle) ** 2, 2 * c(angle) * s(angle)],
            [s(angle) ** 2, c(angle) ** 2, -2 * c(angle) * s(angle)],
            [-c(angle) * s(angle), c(angle) * s(angle), c(angle) ** 2 - s(angle) ** 2],
        ]
    )
    R_mat = np.array(
        [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 2.0]]
    )  # Reuter matrix

    # equation 2.82 from Mechanics of Composite materials
    q_rotated = np.linalg.inv(T_mat) @ q @ R_mat @ T_mat @ np.linalg.inv(R_mat)

    return q_rotated


def set_D_matrix(
    plyid, materials, q_matrix, ply, set_inc_angles, ref_material, nformat
):
    def is_pos_def(A):
        if np.allclose(A, A.T, atol=1e-3):
            try:
                np.linalg.cholesky(A)
                return True
            except np.linalg.LinAlgError:
                return False
        else:
            return False

    # indices for upper triangular 6x6 matrix in column by column order
    # (order for calculix anisotropic material elasticity inputs)
    indices = [[], []]
    rows_upper_triangular = 1
    for col in range(6):
        for row in range(rows_upper_triangular):
            indices[0].append(row)
            indices[1].append(col)
        rows_upper_triangular += 1

    materials[plyid] = {}
    for inc_angle in set_inc_angles:

        if ply["combine_plus_minus_plies"]:
            rotations = [-inc_angle, inc_angle]
        else:
            rotations = [inc_angle]

        # calculate A/t matrix
        a_matrix_by_t = np.zeros([3, 3])
        for r in rotations:
            a_matrix_by_t += rotate_q_matrix(angle=r + ply["ply_ref_angle"], q=q_matrix)
        a_matrix_by_t = a_matrix_by_t / len(rotations)

        # derive the dimensionless D stiffness matrix in 3D, check that it is positive definite
        d_matrix = np.zeros([6, 6])
        d_matrix[:2, :2] = a_matrix_by_t[:2, :2]
        d_matrix[:2, 3] = a_matrix_by_t[:2, 2]
        d_matrix[3, :2] = a_matrix_by_t[2, :2]
        d_matrix[3, 3] = a_matrix_by_t[2, 2]
        d_matrix[2, 2] = ref_material["E2"]
        d_matrix[4, 4] = ref_material["G12"]
        d_matrix[5, 5] = ref_material["G12"]
        if not is_pos_def(d_matrix):
            raise ValueError("Calculated stiffness matrix is not positive definite.")
        materials[plyid][inc_angle] = {
            "name": nformat.format(plyid, inc_angle),
            "D_matrix": d_matrix[tuple(indices)].tolist(),
            "density": ref_material["density"],
        }

    return None


@timeit
def write_solid_mesh(nodes, elements, run_folder=None, file="solid_mesh.inp"):

    lines = []

    #  nodes
    lines.append("*NODE, NSET=Nall\n")
    for nid, node in nodes.items():
        lines.append("{:6d},{:e},{:e},{:e}\n".format(nid, *node["global_xyz"]))

    # elements
    lines.append("*ELEMENT, TYPE=C3D20R, ELSET=Eall\n")
    format_C3D20R = "".join(["{:6d},"] * 16 + ["\n"] + ["{:6d},"] * 5)[:-1] + "\n"
    for eid, element in elements.items():
        if element["type"] == "C3D20R":
            lines.append(format_C3D20R.format(eid, *element["nodes"]))

    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))

    return None


@timeit
def write_materials(materials, run_folder=None, file="materials.inp"):

    lines = []
    format_aniso = (
        "".join(["{:e},"] * 8 + ["\n"] + ["{:e},"] * 8 + ["\n"] + ["{:e},"] * 5)[:-1]
        + "\n"
    )
    for ply in materials.values():
        for material in ply.values():
            lines.append(f"*MATERIAL,NAME={material['name']}\n")
            lines.append(
                "*ELASTIC, TYPE =ANISO\n" + format_aniso.format(*material["D_matrix"])
            )
            lines.append("*DENSITY\n{:e}\n".format(float(material["density"])))

    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


@timeit
def write_element_sets(
    element_sets, set_name_format, run_folder=None, file="element_sets.inp"
):
    lines = []

    for plyid, plyset in element_sets.items():
        for inc_angle, elset in plyset.items():
            lines.append(
                "*ELSET,ELSET=E" + set_name_format.format(plyid, inc_angle) + "\n"
            )
            for chunk in divide_chunks(elset, 16):
                # note trailing comas are no a problem for ccx or abaqus
                lines.append(", ".join([f"{int(eid):d}" for eid in chunk]) + ",\n")

    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


@timeit
def write_solid_sections(
    materials, set_name_format, run_folder=None, file="solid_sections.inp"
):

    lines = []

    for plyid, ply in materials.items():
        for inc_angle in ply.keys():
            name = set_name_format.format(plyid, inc_angle)
            lines.append("*SOLID SECTION,MATERIAL=" + name)
            lines.append(",ELSET=E" + name + "\n")

    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


@timeit
def write_node_sets(constraints, run_folder=None, file="node_sets.inp"):

    lines = []
    for cname, constraint in constraints["SPCs"].items():
        lines.append("*NSET,NSET=N" + cname.upper() + "\n")
        for chunk in divide_chunks(constraint["nodes"], 16):
            # note trailing comas are no a problem for ccx or abaqus
            lines.append(", ".join([f"{int(eid):d}" for eid in chunk]) + ",\n")
    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def write_surface(constraints, run_folder=None, file="surfaces.inp"):

    lines = []
    for cname, constraint in constraints["kinematic_MPCs"].items():
        lines.append("*SURFACE, NAME=S" + cname.upper() + "\n")
        for face in constraint["faces"]:
            lines.append(f"{face[0]:6d},{face[1]}\n")
    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def write_constraints(constraints, run_folder=None, file="constraints.inp"):

    lines = []

    # spc constraints
    lines.append("*BOUNDARY\n")
    for cname, constraint in constraints["SPCs"].items():
        for dof in constraint["SPC"]:
            lines.append(f"N{cname.upper()}, {dof}, ,\n")  # NSET, DOF

    # kinematic constraints
    for cname, constraint in constraints["kinematic_MPCs"].items():
        nid = list(constraint["ref_node"].keys())[0]
        lines.append(f"*NODE, NSET=N{cname.upper()}\n")
        lines.append(
            "{:6d},{:e},{:e},{:e}\n".format(
                nid, *constraint["ref_node"][nid]["global_xyz"]
            )
        )
        lines.append(
            f"*COUPLING, REF NODE={nid}, SURFACE=S{cname.upper()}, CONSTRAINT NAME={cname.upper()}\n"
        )
        lines.append("*KINEMATIC\n")
        for dof in constraint["kinematic"]:
            lines.append(f"{dof}\n")  # DOF
        lines.append("*BOUNDARY\n")
        for dof in constraint["ref_node_SPC"]:
            lines.append(f"{nid:6d}, {dof}, ,\n")

    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def write_loading(constraints, run_folder=None, file="loads.inp"):

    lines = []
    for cname, constraint in constraints["kinematic_MPCs"].items():
        if "ref_node_forces" in constraint:
            lines.append("*CLOAD\n")
            nid = list(constraint["ref_node"].keys())[0]
            for dof, value in enumerate(constraint["ref_node_forces"]):
                if not value == 0.0:
                    lines.append(f"{nid:6d}, {dof+1:d}, {value:e}\n")

    # write string of input lines to file
    with open(run_folder / file, "w", encoding="utf-8") as f:
        f.write("".join(lines))


def get_buckling_factors(outfile, number_modes):

    with open(outfile, "r", encoding="utf-8") as f:
        data = f.readlines()

    index = 1
    factors = []
    for line in data[6 : 7 + number_modes]:
        output = line.strip().split()
        mode_no = int(output[0])
        factor = float(output[1])
        if not mode_no == index:
            raise ValueError(
                "Mode number doesn't match expected index. Check dat file."
            )
        index += 1
        factors.append(factor)

    return factors


if __name__ == "__main__":
    design = {"0-T0-inc_angle": 45.0}
    resp = main(
        inputs={"design": design, "implicit": {}, "setup": {}},
        outputs={"design": {}, "implicit": {}, "setup": {}},
        partials={},
        options={},
        parameters=PARAMS,
    )
    assert np.isclose(resp["outputs"]["mass"], 8.836875, rtol=1e-6)
    assert np.isclose(resp["outputs"]["buckling_factors"][0], 1.126453, rtol=1e-6)
