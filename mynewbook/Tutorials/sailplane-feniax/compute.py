import os
from datetime import datetime
from pathlib import Path
import glob
import zipfile

import plotly.express as px
import pyNastran.op4.op4 as op4
import matplotlib.pyplot as plt
import shutil
import jax.numpy as jnp
import jax
import pandas as pd
import feniax.preprocessor.configuration as configuration  # import Config, dump_to_yaml
from feniax.preprocessor.inputs import Inputs
import feniax.feniax_main
import feniax.preprocessor.solution as solution
import feniax.unastran.op2reader as op2reader
import feniax.plotools.uplotly as uplotly
from tabulate import tabulate
from ruamel.yaml import YAML

# RUN CASES
import time

TIMES_DICT = dict()
SOL = dict()
CONFIG = dict()


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
    """A user editable compute function.

    Here the compute function copies input files to the output folder.

    Parameters
    ----------
    inputs: dict
        The component Inputs sorted by type (design, implicit or setup).
    outputs: dict
        The component Outputs sorted by type (design, implicit or setup).
    partials: dict, optional
        The derivatives of the component's "design" outputs with respect to its
        "design" inputs, used for gradient-based design optimisation Runs.
    options: dict, optional
        component data processing options and flags, inc. : "stream_call",
        "get_outputs", "get_grads"
    parameters: dict
        The component Parameters as returned by the setup function.

    Returns
    -------
    dict
        dictionary of JSON-serialisable keys and values, including:
        outputs: dict, optional
            The compute function can assign values to output keys, but the outputs
            keys should not be modified.
        partials: dict, optional
            The compute function can assign values to partials keys, but the
            partials keys should not be modified.
        message: str, optional
            A compute message that will appear in the Run log.
    """

    print("Starting user function evaluation.")

    run_folder = Path(parameters["outputs_folder_path"])
    cwd = os.getcwd()
    os.chdir(run_folder)

    # delete previous results
    output_zip = run_folder / "output_files.zip"
    if output_zip.is_file():
        shutil.rmtree(output_zip)

    # create results folders
    os.mkdir("./figs")
    os.mkdir("./results")
    os.chdir("./results")

    u_sp, u_spl = load_NASTRAN_results()

    number_of_modes_inputs = [
        key for key in inputs["design"] if key.startswith("number_of_modes")
    ]
    if number_of_modes_inputs:
        for case in number_of_modes_inputs:
            # rotate a fibre direction in the orientations parameter
            tree = case.split(".")
            case_name = tree[1]
            parameters["number_of_modes"][case_name] = inputs["design"][case]

    number_of_modes = parameters["number_of_modes"]
    print(f"Input mode cases are: {str(number_of_modes)}")

    generate_data(number_of_modes)
    postprocess(u_sp, u_spl)

    os.chdir(cwd)

    # zip all data in outputs folder to be able to recover it with structure
    result_files = [
        Path(f) for f in glob.glob("**/*.*", recursive=True, root_dir=run_folder)
    ]
    with zipfile.ZipFile(output_zip, mode="w") as archive:
        for file in result_files:
            if not (run_folder / file).is_file():
                raise FileNotFoundError(f"Cannot find output file {file}")
            archive.write(run_folder / file, arcname=file)
    shutil.rmtree(run_folder / "results")
    shutil.rmtree(run_folder / "figs")

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Completed compute."
    print(message)

    return {"message": message}


def load_NASTRAN_results():
    examples_path = feniax.PATH / "../examples"
    SP_folder = examples_path / "SailPlane"
    # nastran_path = wingSP_folder / "NASTRAN/"

    op2model = op2reader.NastranReader(
        SP_folder / "NASTRAN/static400/run.op2",
        SP_folder / "NASTRAN/static400/run.bdf",
        static=True,
    )
    op2model.readModel()
    t_sp, u_sp = op2model.displacements()

    op2modell = op2reader.NastranReader(
        SP_folder / "NASTRAN/static400/run_linear.op2",
        SP_folder / "NASTRAN/static400/run_linear.bdf",
        static=True,
    )

    op2modell.readModel()
    t_spl, u_spl = op2modell.displacements()
    sp_error3d = jnp.load(examples_path / "SailPlane/sp_err.npy")

    return u_sp, u_spl


def run(input1, **kwargs):
    jax.clear_caches()
    label = kwargs.get("label", "default")
    t1 = time.time()
    config = configuration.Config(input1)
    sol = feniax.feniax_main.main(input_obj=config)
    t2 = time.time()
    TIMES_DICT[label] = t2 - t1
    SOL[label] = sol
    CONFIG[label] = config


def save_times():
    pd_times = pd.DataFrame(dict(times=TIMES_DICT.values()), index=TIMES_DICT.keys())
    pd_times.to_csv("./run_times.csv")


def get_inputs():
    SP_folder = feniax.PATH / "../examples/SailPlane"
    inp = Inputs()
    inp.engine = "intrinsicmodal"
    inp.fem.eig_type = "inputs"
    inp.fem.connectivity = dict(
        FuselageFront=["RWingInner", "LWingInner"],
        FuselageBack=["BottomTail", "Fin"],
        RWingInner=["RWingOuter"],
        RWingOuter=None,
        LWingInner=["LWingOuter"],
        LWingOuter=None,
        BottomTail=["LHorizontalStabilizer", "RHorizontalStabilizer"],
        RHorizontalStabilizer=None,
        LHorizontalStabilizer=None,
        Fin=None,
    )

    inp.fem.folder = Path(SP_folder / "FEM/")
    inp.fem.num_modes = 50
    inp.driver.typeof = "intrinsic"
    inp.simulation.typeof = "single"
    inp.systems.sett.s1.solution = "static"
    inp.systems.sett.s1.solver_library = "diffrax"
    inp.systems.sett.s1.solver_function = "newton"
    inp.systems.sett.s1.solver_settings = dict(
        rtol=1e-6, atol=1e-6, max_steps=50, norm="linalg_norm", kappa=0.01
    )
    # inp.systems.sett.s1.solver_library = "scipy"
    # inp.systems.sett.s1.solver_function = "root"
    # inp.systems.sett.s1.solver_settings = dict(method='hybr',#'krylov',
    #                                           tolerance=1e-9)
    inp.systems.sett.s1.xloads.follower_forces = True
    inp.systems.sett.s1.xloads.follower_points = [[25, 2], [48, 2]]

    inp.systems.sett.s1.xloads.x = [0, 1, 2, 3, 4, 5, 6]
    inp.systems.sett.s1.xloads.follower_interpolation = [
        [0.0, 2e5, 2.5e5, 3.0e5, 4.0e5, 4.8e5, 5.3e5],
        [0.0, 2e5, 2.5e5, 3.0e5, 4.0e5, 4.8e5, 5.3e5],
    ]
    inp.systems.sett.s1.t = [1, 2, 3, 4, 5, 6]

    return inp, SP_folder


# plotting functions
def fig_out(name, figformat="png", update_layout=None):
    def inner_decorator(func):
        def inner(*args, **kwargs):
            fig = func(*args, **kwargs)
            if update_layout is not None:
                fig.update_layout(**update_layout)
            # fig.show()
            figname = f"figs/{name}.{figformat}"
            fig.write_image(f"../{figname}", scale=6)
            return fig, figname

        return inner

    return inner_decorator


def fig_background(func):

    def inner(*args, **kwargs):
        fig = func(*args, **kwargs)
        # if fig.data[0].showlegend is None:
        #     showlegend = True
        # else:
        #     showlegend = fig.data[0].showlegend

        fig.update_xaxes(
            titlefont=dict(size=20),
            tickfont=dict(size=20),
            mirror=True,
            ticks="outside",
            showline=True,
            linecolor="black",
            # zeroline=True,
            # zerolinewidth=2,
            # zerolinecolor='LightPink',
            gridcolor="lightgrey",
        )
        fig.update_yaxes(
            tickfont=dict(size=20),
            titlefont=dict(size=20),
            zeroline=True,
            mirror=True,
            ticks="outside",
            showline=True,
            linecolor="black",
            gridcolor="lightgrey",
        )
        fig.update_layout(
            plot_bgcolor="white",
            yaxis=dict(zerolinecolor="lightgrey"),
            showlegend=True,  # showlegend,
            margin=dict(autoexpand=True, l=0, r=0, t=2, b=0),
        )
        return fig

    return inner


def fn_spError(sol_list, config, u_sp, print_info=True):

    sol_sp = [solution.IntrinsicReader(f"./SP{i}") for i in range(1, 6)]
    err = {f"M{i}_L{j}": 0.0 for i in range(1, 6) for j in range(6)}
    for li in range(6):  # loads
        for mi in range(1, 6):  # modes
            count = 0
            r_spn = []
            r_sp = []
            for index, row in config.fem.df_grid.iterrows():
                r_spn.append(u_sp[li, row.fe_order, :3] + config.fem.X[index])
                r_sp.append(sol_sp[mi - 1].data.staticsystem_s1.ra[li, :, index])
                # print(f"nas = {r_spn}  ,  {r_sp}")
                # count += 1
            r_spn = jnp.array(r_spn)
            r_sp = jnp.array(r_sp)
            err[f"M{mi}_L{li}"] += jnp.linalg.norm(
                r_spn - r_sp
            )  # / jnp.linalg.norm(r_spn)
            err[f"M{mi}_L{li}"] /= len(r_sp)
            if print_info:
                print(f"**** LOAD: {li}, NumModes: {mi} ****")
                print(err[f"M{mi}_L{li}"])
    return err


def fn_spWingsection(sol_list, config, u_sp, u_spl):

    sol_sp = [solution.IntrinsicReader(f"./SP{i}") for i in range(1, 6)]
    r_spn = []
    r_spnl = []
    r_sp = []
    for li in range(6):  # loads
        for mi in [4]:  # range(1,6):  # modes
            r_spni = []
            r_spnli = []
            r_spi = []
            r_sp0 = []
            for index, row in config.fem.df_grid.iterrows():
                if row.fe_order in list(range(20)):
                    r_sp0.append(config.fem.X[index])
                    r_spni.append(u_sp[li, row.fe_order, :3] + config.fem.X[index])
                    r_spnli.append(u_spl[li, row.fe_order, :3] + config.fem.X[index])
                    r_spi.append(sol_sp[mi - 1].data.staticsystem_s1.ra[li, :, index])
                # print(f"nas = {r_spn}  ,  {r_sp}")
                # count += 1

            r_spn.append(jnp.array(r_spni))
            r_spnl.append(jnp.array(r_spnli))
            r_sp.append(jnp.array(r_spi))
    r_sp0 = jnp.array(r_sp0)
    return r_sp0, r_sp, r_spn, r_spnl


@fig_background
def plot_spWingsection(r0, r, rn, rnl):
    fig = None
    # colors=["darkgrey", "darkgreen",
    #         "blue", "magenta", "orange", "black"]
    # dash = ['dash', 'dot', 'dashdot']
    modes = [5, 15, 30, 50, 100]
    for li in range(6):
        if li == 0:
            fig = uplotly.lines2d(
                (r[li][:, 0] ** 2 + r[li][:, 1] ** 2) ** 0.5,
                r[li][:, 2] - r0[:, 2],
                fig,
                dict(name=f"NMROM", line=dict(color="blue", dash="solid")),
                dict(),
            )
            fig = uplotly.lines2d(
                (rn[li][:, 0] ** 2 + rn[li][:, 1] ** 2) ** 0.5,
                rn[li][:, 2] - r0[:, 2],
                fig,
                dict(name=f"FullFE-NL", line=dict(color="black", dash="dash")),
                dict(),
            )
            fig = uplotly.lines2d(
                (rnl[li][:, 0] ** 2 + rnl[li][:, 1] ** 2) ** 0.5,
                rnl[li][:, 2] - r0[:, 2],
                fig,
                dict(name=f"FullFE-Lin", line=dict(color="orange", dash="solid")),
                dict(),
            )

        else:
            fig = uplotly.lines2d(
                (r[li][:, 0] ** 2 + r[li][:, 1] ** 2) ** 0.5,
                r[li][:, 2] - r0[:, 2],
                fig,
                dict(showlegend=False, line=dict(color="blue", dash="solid")),
                dict(),
            )
            fig = uplotly.lines2d(
                (rn[li][:, 0] ** 2 + rn[li][:, 1] ** 2) ** 0.5,
                rn[li][:, 2] - r0[:, 2],
                fig,
                dict(showlegend=False, line=dict(color="black", dash="dash")),
                dict(),
            )
            fig = uplotly.lines2d(
                (rnl[li][:, 0] ** 2 + rnl[li][:, 1] ** 2) ** 0.5,
                rnl[li][:, 2] - r0[:, 2],
                fig,
                dict(showlegend=False, line=dict(color="orange", dash="solid")),
                dict(),
            )
    fig.update_yaxes(title=r"$\large u_z [m]$")
    fig.update_xaxes(title=r"$\large S [m]$", range=[6.81, 36])
    fig.update_layout(legend=dict(x=0.6, y=0.95), font=dict(size=20))
    # fig = uplotly.lines2d((rnl[:,0]**2 + rnl[:,1]**2)**0.5, rnl[:,2], fig,
    #                       dict(name=f"NASTRAN-101",
    #                            line=dict(color="grey",
    #                                      dash="solid")
    #                                  ),
    #                             dict())
    return fig


@fig_background
def fn_spPloterror(error):

    loads = [200, 250, 300, 400, 480, 530]
    num_modes = [5, 15, 30, 50, 100]
    e250 = jnp.array([error[f"M{i}_L1"] for i in range(1, 6)])
    e400 = jnp.array([error[f"M{i}_L3"] for i in range(1, 6)])
    e530 = jnp.array([error[f"M{i}_L5"] for i in range(1, 6)])
    fig = None
    fig = uplotly.lines2d(
        num_modes, e250, fig, dict(name="F = 250 KN", line=dict(color="red")), dict()
    )
    fig = uplotly.lines2d(
        num_modes,
        e400,
        fig,
        dict(name="F = 400 KN", line=dict(color="green", dash="dash")),
        dict(),
    )
    fig = uplotly.lines2d(
        num_modes,
        e530,
        fig,
        dict(name="F = 530 KN", line=dict(color="black", dash="dot")),
        dict(),
    )
    fig.update_xaxes(
        title={"font": {"size": 20}, "text": "Number of modes"}
    )  # title="Number of modes",title_font=dict(size=20))
    fig.update_yaxes(
        title=r"$\Large \epsilon$",
        type="log",  # tickformat= '.1r',
        tickfont=dict(size=12),
        exponentformat="power",
        # dtick=0.2,
        # tickvals=[2e-2, 1e-2, 7e-3,5e-3,3e-3, 2e-3, 1e-3,7e-4, 5e-4,3e-4, 2e-4, 1e-4, 7e-5, 5e-5]
    )
    # fig.update_layout(height=650)
    fig.update_layout(legend=dict(x=0.7, y=0.95), font=dict(size=20))

    return fig


@fig_background
def fn_spPloterror3D(error, error3d):

    loads = [200, 250, 300, 400, 480, 530]
    fig = None
    if error is not None:
        fig = uplotly.lines2d(
            loads,
            error,
            fig,
            dict(
                name="Error ASET", line=dict(color="red"), marker=dict(symbol="square")
            ),
            dict(),
        )

    fig = uplotly.lines2d(
        loads,
        error3d,
        fig,
        dict(name="Error full 3D", line=dict(color="green")),
        dict(),
    )

    fig.update_yaxes(type="log", tickformat=".0e")
    fig.update_layout(  # height=700,
        # showlegend=False,
        # legend=dict(x=0.7, y=0.95),
        xaxis_title="Loading [KN]",
        yaxis_title=r"$\Large \epsilon$",
    )

    return fig


@fig_background
def plot_spAD(rn, r0):

    loads = [200, 250, 300, 400, 480, 530]
    fig = None
    x = list(range(1, 7))
    y = [rn[i - 1][-1, 2] - r0[-1, 2] for i in x]
    fig = uplotly.lines2d(
        x,
        y,
        fig,
        dict(  # name="Error ASET",
            # line=dict(color="red"),
            # marker=dict(symbol="square")
        ),
        dict(),
    )

    # fig.update_yaxes(type="log", tickformat= '.0e')
    fig.update_layout(  # height=700,
        showlegend=False, xaxis_title=r"$\Large{\tau}$", yaxis_title="Uz [m]"
    )

    return fig


def generate_data(number_of_modes):

    # number_of_modes = {"SP1": 5, "SP2": 15, "SP3": 30, "SP4": 50, "SP5": 100}

    for name in number_of_modes.keys():
        inp, _ = get_inputs()
        inp.fem.num_modes = int(number_of_modes[name])
        inp.driver.sol_path = Path(f"./{name}")
        run(inp, label=name)

    save_times()


def postprocess(u_sp, u_spl):
    t1 = time.time()

    # NOTE: correct config matrix names - default doesn't work
    yaml = YAML()
    yaml_dict = yaml.load(Path("SP1/config.yaml"))
    yaml_dict["fem"]["Ka_name"] = "Ka.npy"
    yaml_dict["fem"]["Ma_name"] = "Ma.npy"
    yaml_dict["fem"]["grid"] = "structuralGrid"
    yaml.dump(yaml_dict, Path("SP1/config.yaml"))

    config = configuration.Config.from_file("SP1/config.yaml")
    t2 = time.time()
    print(f"Time for config: {t2-t1}")

    t1 = time.time()
    sol_sp = [solution.IntrinsicReader(f"./SP{i}") for i in range(1, 6)]
    r_sp0, r_sp, r_spn, r_spnl = fn_spWingsection(sol_sp, config, u_sp, u_spl)
    fig, figname = fig_out("SPWingsection")(plot_spWingsection)(
        r_sp0, r_sp, r_spn, r_spnl
    )
    t2 = time.time()
    print(figname)
    print(f"Time for figure: {t2-t1}")

    # # config = configuration.Config.from_file("SP1/config.yaml")
    # # sol_sp = [solution.IntrinsicReader(f"./SP{i}") for i in range(1, 6)]
    t1 = time.time()
    sp_error = fn_spError(sol_sp, config, u_sp, print_info=True)
    fig, figname = fig_out("SPstatic_3D")(fn_spPloterror)(sp_error)
    t2 = time.time()
    print(figname)
    print(f"Time for figure: {t2-t1}")


if __name__ == "__main__":
    compute()
