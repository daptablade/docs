from datetime import datetime
from pathlib import Path


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
    """Use this script to join the visual results (.frd files) of beam1 and beam2."""

    print("Post-processing started.")

    # get components inputs
    run_folder = Path(parameters["outputs_folder_path"])

    beam1_frd = inputs["implicit"]["files.beam1_frd"]
    beam2_frd = inputs["implicit"]["files.beam2_frd"]

    # check input files have been uploaded
    inputs_folder = Path(parameters["inputs_folder_path"])
    for f in [beam1_frd, beam2_frd]:
        if not (inputs_folder / f).is_file():
            raise FileNotFoundError(f"{f} file connection needed from beam component.")

    join_frd(
        inputs_folder / beam1_frd, inputs_folder / beam2_frd, run_folder=run_folder
    )

    resp = {}
    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Post-processing completed."
    resp["message"] = message

    return resp


def join_frd(frd1, frd2, run_folder=None):
    """
    Append the nodes and elements from frd2 to those in frd1 and write the result in a new frd.
    """

    #### params ####

    # size of complete node sets
    # nsize1 = 201
    # nsize2 = 81
    nsizem = 261  # nsize1 + nsize2 - nsize_coupling_surface

    # time steps. set in precice-config.xml and .inp files
    nsteps = 50

    with open(frd1, "r") as f1, open(frd2, "r") as f2, open(
        run_folder / "beam_full.frd", "w"
    ) as fp:
        # copy frd header in new file
        for i in range(11):
            fp.write(f1.readline())
            f2.readline()

        # node header (change number of nodes)
        line_f1 = f1.readline()
        line_f1 = line_f1[:33] + str(nsizem) + line_f1[36:]
        fp.write(line_f1)
        f2.readline()

        # merging node lines. each iteration in the for uses a new line from frd2. lines in frd1 are advanced manually
        line_f1 = f1.readline()
        for line_f2 in iter(f2.readline, " -3\n"):  # -3 indicates end of line block
            # same node in both files (interface): write any (assuming their values are correct!!)
            if line_f1[:13] == line_f2[:13]:
                if line_f1[2] == "3":
                    continue
                else:
                    fp.write(line_f1)
                    line_f1 = f1.readline()
            # sorting lines according to node index
            elif line_f2 < line_f1:
                fp.write(line_f2)
            else:
                while line_f2 > line_f1:
                    fp.write(line_f1)
                    line_f1 = f1.readline()

                if line_f1[:13] != line_f2[:13]:
                    fp.write(line_f2)

        fp.write(" -3\n")

        # element header (change number of elements)
        line_f1 = f1.readline()
        line_f1 = line_f1[:34] + "32" + line_f1[36:]
        fp.write(line_f1)
        f2.readline()

        # merge element lines. assuming they are sorted and non-overlapping in frd1 and frd2
        for line_f1 in iter(f1.readline, " -3\n"):
            fp.write(line_f1)
        for line_f2 in iter(f2.readline, " -3\n"):
            fp.write(line_f2)
        fp.write(" -3\n")

        # merging blocks of lines for each step
        for i in range(nsteps):
            print("step", i + 1)
            # step header
            fp.write(f1.readline())
            f2.readline()
            line_f1 = f1.readline()
            line_f1 = line_f1[:33] + str(nsizem) + line_f1[36:]
            fp.write(line_f1)
            f2.readline()
            for j in range(5):
                fp.write(f1.readline())
                f2.readline()

            line_f1 = f1.readline()
            for line_f2 in iter(f2.readline, " -3\n"):  # -3 indicates end of line block
                # same node in both files (interface): write any (assuming their values are correct!!)
                if line_f1[:13] == line_f2[:13]:
                    if line_f1[2] == "3":
                        continue
                    else:
                        # this is an interface node for both beams. write the mean of the values in beam1 and beam2
                        mean_vals = [
                            (float(x) + float(y)) / 2.0
                            for x, y in zip(
                                [line_f1[13:25], line_f1[25:37], line_f1[37:49]],
                                [line_f2[13:25], line_f2[25:37], line_f2[37:49]],
                            )
                        ]
                        fp.writelines(
                            line_f1[:13]
                            + "{:12.5E}".format(mean_vals[0])
                            + "{:12.5E}".format(mean_vals[1])
                            + "{:12.5E}".format(mean_vals[2])
                            + "\n"
                        )
                        line_f1 = f1.readline()
                # sorting lines according to node index
                elif line_f2 < line_f1:
                    fp.write(line_f2)
                else:
                    while line_f2[:13] > line_f1[:13]:
                        fp.write(line_f1)
                        line_f1 = f1.readline()

                    if line_f1[:13] != line_f2[:13]:
                        fp.write(line_f2)
                    else:
                        mean_vals = [
                            (float(x) + float(y)) / 2.0
                            for x, y in zip(
                                [line_f1[13:25], line_f1[25:37], line_f1[37:49]],
                                [line_f2[13:25], line_f2[25:37], line_f2[37:49]],
                            )
                        ]
                        fp.writelines(
                            line_f1[:13]
                            + "{:12.5E}".format(mean_vals[0])
                            + "{:12.5E}".format(mean_vals[1])
                            + "{:12.5E}".format(mean_vals[2])
                            + "\n"
                        )
                        line_f1 = f1.readline()

            fp.write(" -3\n")

        fp.write("9999\n")  # EOF
