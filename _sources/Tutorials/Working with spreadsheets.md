# Working with spreadsheets


**Duration: 15 min**

In this example we explore the use of **spreadsheets and macros** within simulation workflows.

We replicate the [Simple optimisation problem](./Simple%20optimisation%20problem.md) simulation workflow, but this time using the spreadsheet component `libreoffice-comp` for the paraboloid function calculation instead of a pure python component. 

Don't have time to work though the example yourself? 
Watch the **[video tutorial](https://youtu.be/2GaVVrot-4I)** instead.

```{image} media/spreadsheet_1.png
:alt: paraboloid-spreadsheet
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Component description

Spreadsheets, such as Microsoft's Excel® files, are widely used in engineering. 

In simulation workflows, spreadsheets can be used to:

* import data, from experiments for example; 
* perform calculations on input data in an automated fashion;
* record, visualise and store outputs.

Using the `libreoffice-comp` component API, spreadsheets can easily be integrated into any dapta {term}`Run`.

The `libreoffice-comp` includes a full installation of [LibreOffice](https://www.libreoffice.org/), which includes a spreadsheet editor (Calc). 
Calc can open and save files in its native Open Document Format (.ods), as well as Microsoft Excel® format (.xls), and it is also is compatible with macros (currently supported languages are LibreOffice Basic, BeanShell, JavaScript, and Python, with some support for importing Microsoft VBA macros too). 
To find out more about writing LibreOffice macros, we recommend having a look at the [Getting Started with Macros](https://books.libreoffice.org/en/GS70/GS7013-GettingStartedWithMacros.html) guide. [Reference 1](tutorials-working-with-spreadsheets-references) also provides a good introduction to python macros for Calc. 

Download the example spreadsheet (shown in the figure above) here: [paraboloid.ods](https://github.com/daptablade/parametric_cgx_model/raw/dapta-components/dapta_model_components/libreoffice/paraboloid.ods). 

It includes a VBA macro that automatically calculates the paraboloid function f(x,y) from the [Simple component analysis](./Simple%20component%20analysis.md) example, whenever the spreadsheet x and y inputs are updated.
The spreadsheet also contains an initially empty optimisation history table, which will be used to store and plot the optimisation history data during the {term}`Run`.   

## Opening a saved session

Since we already created and analysed the paraboloid component previously, we can load our previous session to speed things up. 

Select `Open` from the interface controls to load the JSON formatted version of our previous session (dapta_input.json). 
Alternatively, copy the object below into a text editor and save it locally, then select `Open` to load it. 

```{literalinclude} ./paraboloid/paraboloid.json    
:language: json
```

The paraboloid component should have appeared in the workspace, but the question mark next to the component name indicates that it is missing some data. 

## Update the paraboloid component

Copy the contents of the new `setup.py` and `compute.py` API files below into a text editor and save the files locally: 

* The `setup.py` function is similar to the previous one, but it also copies the spreadsheet file into the outputs folder and starts LibreOffice in headless mode by calling the `start_libreoffice` function. 

* The `compute.py` function opens the spreadsheet, writes the input x and y values to the input cells (which automatically executes the spreadsheet macro), and then copies the current x, y and calculated f(x,y) values to the optimisation history table. 
This also automatically updates the line plots. 
Finally the spreadsheet is saved and closed.     

Open the paraboloid component by selecting it in the workspace. 

Update the `Properties` tab:

1. From the API dropdown menu, choose `libreoffice-comp:latest`
2. Upload the new `setup.py` and `compute.py` API files by clicking on the corresponding links

Then, update the `Parameters` tab:

1. Add the following key / value pair to the JSON object: `"ods_file": "paraboloid.ods"`
2. Upload the input spreadsheet (paraboloid.ods) by selecting `upload user input files`. 

Save and close the component by selecting the `Save data` button.

You can check that the component works as expected by executing the {term}`Run` now, or you can add a driver component in the next section before launching the {term}`Run`. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./libreoffice/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./libreoffice/compute.py
:language: python
```
````
`````

## Adding the driver component

We will re-use the OpenMDAO driver we used previously in the [Simple optimisation problem](./Simple%20optimisation%20problem.md). 
We adjust the driver parameters for this optimisation problem:

* The calculation of total derivatives across the chained components (using finite differencing) is requested by setting `"approx_totals": true` and `"fd_step": 0.0001` in the driver parameters.
* Optimisation iteration history plots are requested by adding the "plot_history" option into the "visualise" parameter list.   

To create the driver component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `open-mdao`, and select the component API `generic-python3-driver:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

* In the `Properties` tab check the box next to the `Driver` option. 

* Copy the contents of the parameters JSON object below into the `Parameters` tab text box. 

* Copy the contents of the `om_component.py` file from below into a text editor and save it locally. 
Then upload it under the `Parameters` tab by selecting `upload user input files`.

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./open-mdao-paraboloid/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./open-mdao-paraboloid/compute.py
:language: python
```
````
````{tab-item} requirements
```{literalinclude} ./open-mdao-paraboloid/requirements.txt
:language: text
```
````
````{tab-item} parameters
```{literalinclude} ./libreoffice/driver_parameters.json
:language: json
```
````
````{tab-item} om_component
```{literalinclude} ./open-mdao-paraboloid/om_component.py
:language: python
```
````
`````

### Execute the workflow

We can now execute the design optimisation by selecting the play symbol ▶ in the Run controls interface. 

As before, the {term}`Run` should complete after 13 iterations of the paraboloid component (1 iteration of the open-mdao component). 

### Inspect the outputs

The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 
The "run_output" entry (at the end of the log) should state that the "OpenMDAO compute completed".  

Next, close the {term}`Run` log and select the paraboloid component.
Then select the `Log` tab and click on `download files snapshot`.

Open the downloaded zip folder and open the 'paraboloid.ods' output spreadsheet under the outputs folder.
The optimisation history data should appear as iterations 0 to 12 to the left of the sheet.
This data should also be plotted in the line-plots to the right.
The history data includes major iterations, minor iterations (line searches) and function evaluations used to calculate the finite difference gradients used by the SLSQP algorithm.    

Similarly, you can inspect the outputs of the open-mdao component, which should include convergence history plots, showing the major iterations only. 

Finally, you can save the session data and Run log by selecting `Download` from the interface controls. 

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` data (session data, inputs and outputs) will be permanently deleted. 
```


(tutorials-working-with-spreadsheets-references)=
## References

1. [Interface-oriented programming in OpenOffice / LibreOffice : automate your office tasks with Python Macros, 06/12/2015](http://christopher5106.github.io/office/2015/12/06/openoffice-libreoffice-automate-your-office-tasks-with-python-macros.html)