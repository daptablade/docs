# Automating parametric studies and design optimisations

**Duration: 45 min**

Driver components can be used to automate complex analysis workflows.

In this tutorial, we first automate the execution of a parametric study using the chained component analyses from the previous example. 
Then, we optimise the model parameters by replacing the parametric driver component with the OpenMDAO optimisation component from the [Simple optimisation problem](./Simple%20optimisation%20problem.md) example. 

```{image} media/driver-parametric-model-1.png
:alt: chained process
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Opening a saved session

Start by loading the session file from the previous example.

Select `Open` from the interface controls to load the JSON formatted version of our previous session (dapta_input.json). 
Alternatively, copy the object below into a text editor and save it locally, then select `Open` to load it. 
Three connected components should appear in the workspace. 

````{dropdown} dapta_input.json
```{literalinclude} ./automating_parametric_studies/dapta_input.json   
:language: json
```
````

The question marks next to the component names indicate that they are missing some data. 
To fully define them, we need to upload all the components' `setup.py`, `compute.py`, `requirements.txt` and user input files, as described in the previous example. 

Here are quick links to the file contents available under the [Chaining component analyses](./Chaining%20component%20analyses.md) example:

* [Parametric model component](tutorials-chained_components-parametric_model-files)
* [Calculix-fea component](tutorials-chained_components-calculix_fea-files)
* [Results processor component](tutorials-chained_components-results_processor-files)

Once the files are uploaded, check that the all components are valid. 
There should be green tick marks next to the component names in the workspace view.


## Automating a parametric study

What is the effect of changing the composite material properties on the deflections at the tip of the wing?

To answer this question, we can perform a parametric study. 
We execute the chained analyses for a range of composite property inputs and record the output average wing tip deflections and rotations.   

### The driver component 

The variable of interest is the `calculix-fea` input variable `fibre_rotation_angle.ORI_0.1`, which was previously set to a zero value. 
The driver `compute.py` function performs the following tasks:

1. the `while` loop iterates over a range of variable values, defined it the component `Parameters` tab as a range from `rotation_min` (-10 degrees) to `rotation_max` (10 degrees), with increments of `rotation_inc` (5 degrees);
2. in each iteration, the `run_workflow` function is called to execute the chained component analyses with the current fibre rotation angle;
3. finally, the plotting function (`_plot_study_results`) generates a line plot of the wing tip deflections as a function of the fibre rotation angle.  

```{note}
You may notice that the `parametric-model` component executes in each workflow iteration, even though it's inputs do not change. 
To reduce the overhead associated with this component, we could move the `parametric-model` compute function logic into the setup function, which is only executed once.  
```

To create the driver component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `parametric-study-driver`, and select the component API `generic-python3-driver:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

* In the `Properties` tab check the box next to the `Driver` option. 

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./driver-calculix-fea/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./driver-calculix-fea/compute.py
:language: python
```
````
````{tab-item} requirements
```{literalinclude} ./driver-calculix-fea/requirements.txt
:language: text
```
````
````{tab-item} parameters
```{literalinclude} ./driver-calculix-fea/parameters.json
:language: json
```
````
`````

### Execute the workflow

We can now execute the parametric study by selecting the play symbol ▶ in the Run controls interface. 

Once the run has started, each component will setup and then execute one at a time. 
The setup order is arbitrary, but the compute functions will always be executed from the 'Start Node' to the 'End Node' (see dashboard Reference section for details).

The {term}`Run` should complete after 5 iterations of the connected components (1 iteration of the `parametric-study-driver` component). 

### Inspect the outputs

The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 

We can see that the each component's compute function was executed 5 times. 
The "run_output" (at the end of the log) lists the compute output messages for the 5th workflow iteration only.  

Next, close the {term}`Run` log and select the `parametric-study-driver` component.
Then select the `Log` tab and click on `download files snapshot`.

The parametric study outputs are summarised in the 'results_plot.png' and 'results_plot.png' plots in the 'outputs' folder.

```{image} media/driver-parametric-model-2.png
:alt: results-plot
:class: bg-primary mb-1
:width: 400px
:align: center
```

## Automating a design optimisation

Question

Approach

### Update the driver component

### Execute the workflow


### Inspect the outputs

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` data (session data, inputs and outputs) will be permanently deleted. 
```

## References