from pathlib import Path
import pandas as pd

from matplotlib import pyplot as plt  # type: ignore

from fluids.atmosphere import ATMOSPHERE_1976


def post_process_doe(
    parameters=None,
    run_folder=None,
    files=["results.json"],
):
    """Plot VSPAERO outputs and save figures as pngs."""

    case_outputs_keys = parameters["driver"]["post"]["case_outputs_keys"]
    plt_x_label = parameters["driver"]["post"]["plt_x_label"]
    columns = parameters["driver"]["post"]["columns"]
    variable_names = parameters["driver"]["post"]["variable_names"]

    df = pd.concat([pd.read_json(run_folder / file) for file in files])
    df.sort_values(by=["Vinfinity"], inplace=True)

    # calculate derived properties
    df["rho"] = df.apply(lambda x: ATMOSPHERE_1976(x["Altitude"]).rho, axis=1)
    df["drag_tot"] = df["CDtot"] * 1 / 2 * df["rho"] * df["Vinfinity"] ** 2 * df["S"]
    case_outputs_keys.append("drag_tot")

    for output in case_outputs_keys:
        _, ax = plt.subplots()
        for key, grp in df.groupby(columns):
            ax = grp.plot(ax=ax, kind="line", x=plt_x_label, y=output, label=key)
        plt.grid(True)
        plt.xlabel(variable_names[plt_x_label])
        plt.ylabel(variable_names[output])
        plt.legend(title=variable_names[columns])
        plt.savefig(run_folder / f"results_{output}.png")
    plt.close("all")  # avoid memory warning for repeated runs


if __name__ == "__main__":
    parameters = {
        "driver": {
            "post": {
                "case_outputs_keys": ["CL", "CMy", "CDtot", "L2D", "AoA", "E"],
                "plt_x_label": "Vinfinity",
                "columns": "desvars_PONPNSVRANE",
                "variable_names": {
                    "Mass": "Mass, kg",
                    "Altitude": "Altitude, m",
                    "S": "Wing S, sqm",
                    "Vinfinity": "Vinfinity, m/s",
                    "desvars_PONPNSVRANE": "Wing AR",
                    "CL": "CL",
                    "CMy": "CMy",
                    "CDtot": "CDtot",
                    "L2D": "L/D",
                    "AoA": "AoA, degrees",
                    "E": "Oswald Efficiency Factor",
                    "drag_tot": "Drag, N",
                },
            }
        }
    }
    run_folder = Path("outputs")
    files = ["results_0.json", "results_1.json", "results_2.json", "results_3.json"]
    post_process_doe(run_folder=run_folder, parameters=parameters, files=files)
