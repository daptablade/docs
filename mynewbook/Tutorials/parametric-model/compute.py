from datetime import datetime
from pathlib import Path
import csv
from math import ceil
import numpy as np
import matplotlib.pyplot as plt

PLOT_FLAG = True


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

    # check input files have been uploaded
    inputs_folder = Path(parameters["inputs_folder_path"])
    if not (inputs_folder / parameters["airfoil_csv_file"]).is_file():
        raise FileNotFoundError(
            f"{parameters['airfoil_csv_file']} needs to be uploaded by the user."
        )

    print("Starting user function evaluation.")
    component_inputs = parameters  # default values
    run_folder = Path(parameters["outputs_folder_path"])

    if inputs:
        for input_key, input_value in inputs["design"].items():
            component_inputs[input_key] = input_value

    geometry = get_geometry(
        component_inputs, run_folder, inputs_folder, plot_flag=PLOT_FLAG
    )
    cgx_fdb_path = get_cgx_input_file(geometry, component_inputs, run_folder)

    # check output has been saved
    if not cgx_fdb_path.is_file():
        FileNotFoundError(f"{str(cgx_fdb_path)} is not a file.")

    outputs["implicit"]["files.cgx_file"] = cgx_fdb_path.name

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Created cgx fdb file {cgx_fdb_path.name} with span {str(component_inputs['span'])}m."
    print(message)

    return {"message": message, "outputs": outputs}


def get_geometry(inputs, run_folder, inputs_folder, plot_flag=False):
    """Translate parameters into geometry description that CGX can understand,
    that's points, lines and surfaces."""

    if "airfoil_cut_chord_percentages" not in inputs:
        inputs["airfoil_cut_chord_percentages"] = None

    aerofoil = _get_aerofoil_from_file(
        Path(inputs_folder, inputs["airfoil_csv_file"]),
        plot_flag=plot_flag,
        splitpc=inputs["airfoil_cut_chord_percentages"],
        run_folder=run_folder,
    )
    points, seqa, split_points = _get_cgx_points_3d(
        aerofoil, inputs["chord"], inputs["span"]
    )
    lines, rib_surfaces, aero_surfaces, bodies, aero_surfaces_flip = _get_cgx_lines_3d(
        seqa,
        nele_foil=rint(inputs["nele_foil"]),
        nele_span=int(inputs["nele_span"]),
        split_points=split_points,
        filled_sections=inputs["filled_sections_flags"],
    )

    return {
        "aerofoil": aerofoil,
        "points": points,
        "point_seqa": seqa,
        "lines": lines,
        "surfaces": {
            "ribs": rib_surfaces,
            "aero": aero_surfaces,
            "aero_surfaces_flip": aero_surfaces_flip,
        },
        "bodies": bodies,
    }


def get_cgx_input_file(geometry, inputs, folder):
    """Write CGX batch commands to file."""

    fdb_geom_file = folder / "cgx_infile.fdb"

    if "boundary_conditions" in inputs:
        fix_lines = rint(inputs["boundary_conditions"]["fix_lines"])
        loaded_lines = rint(inputs["boundary_conditions"]["loaded_lines"])
        if "loaded_surfaces" in inputs["boundary_conditions"]:
            loaded_surfaces = rint(inputs["boundary_conditions"]["loaded_surfaces"])
        else:
            loaded_surfaces = None

    else:
        fix_lines = None
        loaded_lines = None
        loaded_surfaces = None

    # create string of all input commands
    cgx_commands = _get_commands(
        geometry,
        fix_lines,
        loaded_lines,
        loaded_surfaces=loaded_surfaces,
        merge_tol=inputs["node_merge_tol"],
        cgx_ele_type=int(inputs["cgx_ele_type"]),
        solver=inputs["cgx_solver"],
    )

    # write string of commands to file
    with open(fdb_geom_file, "w", encoding="utf-8") as f:
        f.write("".join(cgx_commands))

    return fdb_geom_file


########### Private functions that do not get called directly


def rint(items):
    # cover integer values after json import
    return [int(item) for item in items]


def _get_aerofoil_from_file(
    file, plot_flag=True, splitpc=None, pt_offset=6, run_folder=None
):
    """
    This function reads an aerofoil geometry from csv and calculates tc_max.

    Args:
        file: file with xy-positions of the airfoil outline in Selig format.
              For example http://airfoiltools.com/airfoil/seligdatfile?airfoil=n0012-il

    Returns:
        airfoil data
    """

    # read aerofoil input file
    airfoil = []
    with open(file, mode="r", encoding="utf-8") as infile:
        reader = csv.reader(infile, skipinitialspace=True)
        for row in reader:
            airfoil.append(row)
    name = airfoil[0]
    coordinates = np.array([string[0].split() for string in airfoil[1:]], dtype=float)

    # replace the last coordinate to close the airfoil at the trailing-edge
    coordinates[-1] = coordinates[0]

    # we assume that there is a [0.0, 0.0] point in the airfoil
    LE_index = np.where(coordinates[:, 0] == 0.0)[0][0]
    leading_edge_pt = LE_index

    splits = []
    if splitpc:
        # check that there are enough points to split the section
        min_points = 100
        if len(coordinates) < min_points:
            raise ValueError(
                "The parameter 'airfoil_cut_chord_percentages' requires "
                f"at least {min_points:d} airfoil spline points in 'airfoil_csv_file'"
            )

        # re-order the pc from TE to LE
        splitpc.sort(reverse=True)

        # trim points that are within min number of points form leading or trailing edge
        trimmed_coords = np.hstack(
            [np.array([np.arange(len(coordinates))]).T, coordinates]
        )
        trimmed_coords = np.vstack(
            [
                trimmed_coords[pt_offset : int(LE_index - ceil(pt_offset / 2)), :],
                trimmed_coords[int(LE_index + ceil(pt_offset / 2)) : -pt_offset, :],
            ]
        )
        # find two points that match the percentage chord closely
        for split_number, split in enumerate(splitpc):
            point_distances_x = np.abs(trimmed_coords[:, 1] - split / 100)
            pt = {"top": 0, "bot": 0}
            dist_top = point_distances_x[0]
            dist_bot = point_distances_x[-1]
            for index, dist in enumerate(point_distances_x):
                if dist < dist_top and trimmed_coords[index, 2] > 0:
                    pt["top"] = int(trimmed_coords[index, 0])
                    dist_top = dist
                if dist < dist_bot and trimmed_coords[index, 2] < 0:
                    pt["bot"] = int(trimmed_coords[index, 0])
                    dist_bot = dist

            if split_number >= 1:
                # check number of points separating splits
                if (
                    np.abs(pt["top"] - splits[-1]["top"]) < pt_offset
                    or np.abs(pt["bot"] - splits[-1]["bot"]) < pt_offset
                ):
                    raise ValueError(
                        f"Values {splitpc[split_number-1]} and {split:f} in "
                        "'airfoil_cut_chord_percentages' are too close together."
                    )
            splits.append(pt)

    if plot_flag:
        plt.plot(coordinates[:, 0], coordinates[:, 1], "-xr")
        if splitpc:
            for split in splits:
                plt.plot(
                    [coordinates[split["top"], 0], coordinates[split["bot"], 0]],
                    [coordinates[split["top"], 1], coordinates[split["bot"], 1]],
                    "-b",
                )
        plt.xlabel("x")
        plt.ylabel("y")
        plt.title(name)
        plt.savefig(str(run_folder / "airfoil_coordinates.png"))

    return dict(
        name=name,
        coordinates=coordinates,
        splits=splits,
        leading_edge_pt=leading_edge_pt,
    )


def _get_cgx_points_3d(aerofoil, chord, span):
    """This function generates the CGX input file points and point sequences."""

    if not isinstance(span, list):
        span = [span]
    if not isinstance(chord, list):
        chord = [chord]

    def wing_with_splits(aerofoil, chord, span):
        seqa = []
        starting_y = 0
        pt_counter = 0
        split_points = np.empty((len(aerofoil["splits"]), 2, 0), dtype=int)
        for section_index, length_y in enumerate(span):

            x = aerofoil["coordinates"][:, 0] * chord[section_index]
            z = aerofoil["coordinates"][:, 1] * chord[section_index]

            if section_index == 0:  # only needed at the root of the wing
                y_root = np.ones(x.size) * starting_y
                points = np.vstack([x, y_root, z]).T

            # section tip
            y_tip = np.ones(x.size) * (starting_y + length_y)
            points = np.append(points, np.vstack([x, y_tip, z]).T, axis=0)

            def airfoil_seqa(pt_counter, seqa, all_split_points, x_size):
                # SEQA for first airfoil top splines
                pt = 0
                split_points = []
                for split in aerofoil["splits"]:
                    indices = np.arange(pt_counter + pt + 1, pt_counter + split["top"])
                    seqa.append(indices)
                    pt = split["top"]
                    split_points.append(pt_counter + split["top"])
                # SEQA for first airfoil LE spline
                seqa.append(
                    np.arange(
                        pt_counter + pt + 1,
                        pt_counter + aerofoil["leading_edge_pt"],
                    )
                )

                if any(aerofoil["splits"]):
                    seqa.append(
                        np.arange(
                            pt_counter + aerofoil["leading_edge_pt"] + 1,
                            pt_counter + aerofoil["splits"][-1]["bot"],
                        )
                    )
                    # SEQA for first airfoil bot spline
                    pt = x_size - 1
                    bot_seqa = []
                    for split in aerofoil["splits"]:
                        indices = np.flipud(
                            np.arange(
                                pt_counter + pt - 1, pt_counter + split["bot"], -1
                            )
                        )
                        bot_seqa.append(indices)
                        pt = split["bot"]
                        split_points.append(pt_counter + split["bot"])
                    bot_seqa.reverse()
                    seqa += bot_seqa
                    # all_split_point is nested list of dim 3: aerofoil -> split -> point
                    all_split_points = np.dstack(
                        [
                            all_split_points,
                            np.reshape(split_points, (len(aerofoil["splits"]), 2)).T,
                        ]
                    )
                else:
                    seqa.append(
                        np.arange(
                            pt_counter + aerofoil["leading_edge_pt"] + 1,
                            pt_counter + x_size - 2,
                        )
                    )
                    all_split_points = []

                return seqa, all_split_points

            seqa, split_points = airfoil_seqa(
                pt_counter=pt_counter,
                seqa=seqa,
                all_split_points=split_points,
                x_size=x.size,
            )
            if section_index == 0:  # only needed at the root of the wing
                seqa, split_points = airfoil_seqa(
                    pt_counter=pt_counter + x.size,
                    seqa=seqa,
                    all_split_points=split_points,
                    x_size=x.size,
                )

            starting_y += length_y
            pt_counter = seqa[-1][-1] + 2

        return points, seqa, split_points

    points, seqa, split_points = wing_with_splits(aerofoil, chord, span)

    return points, seqa, split_points


def _get_cgx_lines_3d(
    seqa,
    nele_foil=20,
    nele_span=40,
    nele_split=4,
    split_points=None,
    filled_sections=None,
):
    """This function creates the aerofoil section splines and the spanwise bounding lines in CGX."""

    nele_multiplier = 2  # =2 to account for quadratic elements
    lines = []
    aero_surfaces = []
    aero_surfaces_flip = []
    rib_surfaces = []

    if not isinstance(nele_span, list):
        nele_span = [nele_span]

    if not isinstance(nele_foil, list):
        nele_foil = [nele_foil]

    if not isinstance(filled_sections, list):
        filled_sections = [filled_sections]

    splits = 0
    seqas_per_aerofoil = 2
    if isinstance(split_points, np.ndarray):
        splits = split_points.shape[0]
        seqas_per_aerofoil = splits * 2 + 2
    aerofoils = int(len(seqa) / seqas_per_aerofoil)

    airfoil_index = 0
    lcounter = 0
    for seqa_id, seq in enumerate(seqa):

        # aerofoil lines
        lines.append(
            [
                seq[0] - 1,
                seq[-1] + 1,
                seqa_id,
                int(nele_foil[seqa_id % seqas_per_aerofoil] * nele_multiplier),
            ]
        )
        lcounter += 1

        if (seqa_id + 1) % seqas_per_aerofoil == 0:

            if isinstance(split_points, np.ndarray):
                for split_index, split in enumerate(split_points[:, :, airfoil_index]):

                    # aerofoil split lines
                    lines.append(
                        [split[0], split[1], int(nele_split * nele_multiplier)]
                    )
                    lcounter += 1

                    if split_index > 0:
                        # prepare rib surfaces definition
                        rib_surfaces.append(
                            [
                                lcounter - 1 - seqas_per_aerofoil,
                                lcounter - 1,
                                lcounter - split_index * 2 - 2,
                                -(lcounter - 2),
                            ]
                        )

            # spanwise lines at trailing edge
            if (seqa_id + 1) / seqas_per_aerofoil < aerofoils:

                for te_line_inc in range(seqas_per_aerofoil + 1):
                    if te_line_inc < seqas_per_aerofoil:
                        start_id = seqa_id + 1 - seqas_per_aerofoil + te_line_inc
                        end_id = seqa_id + 1 + te_line_inc
                        side = 0
                        pt_offset = -1
                    else:
                        start_id = seqa_id - seqas_per_aerofoil + te_line_inc
                        end_id = seqa_id + te_line_inc
                        side = -1
                        pt_offset = 1
                    lines.append(
                        [
                            seqa[start_id][side] + pt_offset,
                            seqa[end_id][side] + pt_offset,
                            int(nele_span[airfoil_index] * nele_multiplier),
                        ]
                    )
                    lcounter += 1

                    if te_line_inc < seqas_per_aerofoil:
                        if te_line_inc < seqas_per_aerofoil / 2:  # top surface
                            aero_surfaces_flip.append(True)
                        else:  # bot surface
                            aero_surfaces_flip.append(False)
                        # prepare aero surfaces definition
                        aero_surfaces.append(
                            [
                                lcounter - 1 - splits - seqas_per_aerofoil,
                                lcounter,
                                -(lcounter + seqas_per_aerofoil),
                                -(lcounter - 1),
                            ]
                        )

            airfoil_index += 1

    # check that ptB_id > ptA_id
    if not all([line[0] < line[1] for line in lines]):
        raise ValueError("something has gone wrong in the line definition.")

    # solid bodies
    bodies = []
    for surf_id, _ in enumerate(rib_surfaces[1:]):
        if filled_sections[surf_id]:
            bodies.append([surf_id, surf_id + 1])

    return lines, rib_surfaces, aero_surfaces, bodies, aero_surfaces_flip


def _get_commands(
    geometry,
    fix_lines,
    loaded_lines,
    loaded_surfaces,
    merge_tol=0.001,
    cgx_ele_type=10,
    solver="abq",
    max_entries_per_line=9,
):
    def divide_chunks(l, n):
        # looping till length l
        for i in range(0, len(l), n):
            yield l[i : i + n]

    commands = []

    # points
    for entity_id, point in enumerate(geometry["points"]):
        commands.append(
            f"PNT P{entity_id:05d} {point[0]:e} {point[1]:e} {point[2]:e}\n"
        )

    commands.append("# =============== \n")
    # point sequences
    for entity_id, points in enumerate(geometry["point_seqa"]):
        commands.append(f"SEQA A{entity_id:05d} pnt ")
        for ii in range(0, len(points), 8):
            line_end = " = \n" if ii + 8 < len(points) else "\n"
            commands.append(
                " ".join([f"P{point:05d}" for point in points[ii : ii + 8]]) + line_end
            )

    commands.append("# =============== \n")
    # lines
    for entity_id, line in enumerate(geometry["lines"]):
        if len(line) == 3:  # straight line
            commands.append(
                f"LINE L{entity_id:05d} P{line[0]:05d} P{line[1]:05d} {line[2]:d} \n"
            )
        elif len(line) == 4:  # spline
            commands.append(
                f"LINE L{entity_id:05d} P{line[0]:05d} P{line[1]:05d} A{line[2]:05d} {line[3]:d} \n"
            )

    commands.append("# =============== \n")
    # surfaces
    rib_ids = []
    for entity_id, surf in enumerate(geometry["surfaces"]["ribs"]):
        commands.append(
            f"GSUR V{entity_id:05d} + BLEND "
            + " ".join(
                [
                    f"+ L{np.abs(line):05d}"
                    if np.sign(line) >= 0
                    else f"- L{np.abs(line):05d}"
                    for line in surf
                ]
            )
            + "\n"
        )
        rib_ids.append(entity_id)

    aero_ids = []
    flip_surfaces = []
    for counter, surf in enumerate(geometry["surfaces"]["aero"]):
        entity_id = counter + (rib_ids[-1] if rib_ids else -1) + 1
        commands.append(
            f"GSUR V{entity_id:05d} + BLEND "
            + " ".join(
                [
                    f"+ L{np.abs(line):05d}"
                    if np.sign(line) >= 0
                    else f"- L{np.abs(line):05d}"
                    for line in surf
                ]
            )
            + "\n"
        )
        if geometry["surfaces"]["aero_surfaces_flip"][counter]:
            flip_surfaces.append(f"FLIP V{entity_id:05d}" + "\n")
        aero_ids.append(entity_id)

    commands.append("# =============== \n")
    # bodies
    for entity_id, body in enumerate(geometry["bodies"]):
        commands.append(f"BODY B{entity_id:05d} V{body[0]:05d} V{body[1]:05d}" + "\n")

    commands.append("# =============== \n")
    # SPC and load sets
    if fix_lines:
        for chunk in divide_chunks(fix_lines, max_entries_per_line):
            commands.append(
                "SETA SPC l " + " ".join([f"L{line:05d}" for line in chunk]) + "\n"
            )
    if loaded_lines:
        for chunk in divide_chunks(loaded_lines, max_entries_per_line):
            commands.append(
                "SETA LAST l " + " ".join([f"L{line:05d}" for line in chunk]) + "\n"
            )
    if loaded_surfaces:
        for chunk in divide_chunks(loaded_surfaces, max_entries_per_line):
            commands.append(
                "SETA TOP s " + " ".join([f"V{id:05d}" for id in chunk]) + "\n"
            )

    commands.append("# =============== \n")
    # surface meshes
    surfaces = geometry["surfaces"]["ribs"] + geometry["surfaces"]["aero"]
    for entity_id, _ in enumerate(surfaces):
        commands.append(f"MSHP V{entity_id:05d} s {cgx_ele_type:d} 0 1.000000e+00\n")

    commands.append("")
    # sets of surfaces
    if rib_ids:
        for chunk in divide_chunks(rib_ids, max_entries_per_line):
            commands.append(
                "SETA RIBS s " + " ".join([f"V{id:05d}" for id in chunk]) + "\n"
            )
    if aero_ids:
        for chunk in divide_chunks(aero_ids, max_entries_per_line):
            commands.append(
                "SETA AERO s " + " ".join([f"V{id:05d}" for id in chunk]) + "\n"
            )

    commands.append("# =============== \n")
    # body meshes
    if geometry["bodies"]:
        for entity_id, _ in enumerate(geometry["bodies"]):
            commands.append(f"MSHP B{entity_id:05d} b 4 0 1.000000e+00\n")

    commands.append("# =============== \n")
    # custom export statement
    commands.append("mesh all\n")
    commands.append(f"merg n all {merge_tol:6f} 'nolock'\n")
    commands.append("comp nodes d\n")
    if flip_surfaces:
        commands += flip_surfaces
    if fix_lines:
        commands.append("comp SPC d\n")
        commands.append(f"send SPC {solver} spc 123456\n")
    if loaded_lines:
        commands.append("comp LAST d\n")
        commands.append(f"send LAST {solver} names\n")
    if loaded_surfaces:
        commands.append("comp TOP d\n")
        commands.append(f"send TOP {solver} names\n")
    if rib_ids:
        commands.append("comp RIBS d\n")
        commands.append(f"send RIBS {solver} names\n")
    if aero_ids:
        commands.append("comp AERO d\n")
        commands.append(f"send AERO {solver} names\n")
    commands.append(f"send all {solver} \n")
    commands.append("quit\n")

    return commands
