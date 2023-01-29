from datetime import datetime
from pathlib import Path

from libreoffice import store, open_file


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
    """A user editable compute function."""

    run_folder = Path(parameters["outputs_folder_path"])

    print("Starting user function evaluation.")

    # open saved spreadsheet
    file = str(run_folder.resolve() / parameters["ods_file"])
    model = open_file(path=file)

    # add data and plot
    model, f_xy = paraboloid(model, inputs["design"])
    outputs["design"]["f_xy"] = f_xy

    # save spreadsheet
    store(model, file=file)
    model.close(True)

    message = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}: Saved ODS spreadsheet."
    print(message)

    return {"message": message, "outputs": outputs}


def paraboloid(model, inputs):

    # set inputs in spreadsheet
    sheet = model.Sheets.getByIndex(0)
    sheet.getCellRangeByName("B2").Value = inputs["x"]
    sheet.getCellRangeByName("B3").Value = inputs["y"]

    # get calculated value
    f_xy = sheet.getCellRangeByName("B5").Value

    # store inputs and outputs in the Optimisation History ranges
    starting_row = 8
    row = starting_row
    while True:
        if "EMPTY" in str(sheet[row, 0].getType()):
            break
        else:
            row += 1
    # set current iteration number
    if row == starting_row:
        sheet[row, 0].Value = 0
    else:
        sheet[row, 0].Value = sheet[row - 1, 0].Value + 1
    # set x, y, f_xy
    sheet[row, 1].Value = inputs["x"]
    sheet[row, 2].Value = inputs["y"]
    sheet[row, 3].Value = f_xy

    return model, f_xy
