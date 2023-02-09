# Automating the design optimisation of the composite wing model

**Duration: 15 min**

Driver components can be used to automate complex analysis workflows.

In the previous example, we performed a parametric study on a single variable.
In this tutorial we go one step further by re-using the OpenMDAO optimisation component from the [Simple optimisation problem](./Simple%20optimisation%20problem.md) example to optimise the wing design for minimum wing incidence at the tip.

```{image} media/open-mdao-parametric-model-1.png
:alt: chained process with optimiser
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Opening a saved session

Follow the process outlined in the previous example for [Opening a saved session](tutorials-automating-parametric-studies-opening-a-saved-session).

## Automating a design optimisation study

The aim is to determine which composite fibre angle minimises the deflected wing incidence ("Ry"), whilst satisfying the design constraint on the maximum allowable vertical deflection ("Uz") of 6 cm maximum. 

To answer this question, we can perform a design optimisation study.
This example is based on the pure python implementation in [Reference 1](tutorials-automating-design-optimisations-references).   

### The driver component 

As in the previous example, the variable of interest is the `calculix-fea` input variable `fibre_rotation_angle.ORI_0.1`.
The driver component is identical to the OpenMDAO optimisation component used in the [Simple optimisation problem](./Simple%20optimisation%20problem.md) example, except for the driver parameters, which have been adjusted for the wing optimisation problem:

* The "input_variables" and "output_variables" parameters set the optimisation variables, objective and constraint functions.
* The calculation of total derivatives across the chained components (using finite differencing) is requested by setting `"approx_totals": true` and `"fd_step": 1.0` in the driver parameters.
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
```{literalinclude} ./parametric_wing_model/3_Automating_the_design_optimisation/driver_parameters.json
:language: json
```
````
````{tab-item} om_component
```{literalinclude} ./open-mdao-paraboloid/om_component.py
:language: python
```
````
`````

### Add design variables and connections

Despite all the components seeming valid, we would encounter errors if we tried to launch the Run now. 

By inspecting the driver compute function, we can see that OpenMDAO is only aware of design variable inputs, outputs and connections (`connection["type"] == "design"`). 
The design variable connections in particular are used by OpenMDAO to determine the order of component execution.

It is necessary to define the following artificial design variables and connections before we can launch the Run. 

Select the **parametric-model** component and update the `Inputs` and `Outputs` tabs:
`````{tab-set}
````{tab-item} Inputs
```{code} 
{
    "input_0": 0.1
}
```
````
````{tab-item} Outputs
```{code} 
{
  "files.cgx_file": "default",
  "output_0": 1.1
}
```
````
`````

Select the **calculix-fea** component and update the `Inputs` and `Outputs` tabs:
`````{tab-set}
````{tab-item} Inputs
```{code} 
{
  "files.cgx_file": "default",
  "fibre_rotation_angle.ORI_0.1": 0,
  "output_0": 1.1
}
```
````
````{tab-item} Outputs
```{code} 
{
  "files.analysis_output_file": "default",
  "files.mesh_file": "default",
  "files.nodeset_file": "default",
  "output_1": 1.1
}
```
````
`````

Select the **fea-results-processor** component and update the `Inputs` tab only:
`````{tab-set}
````{tab-item} Inputs
```{code} 
{
  "files.analysis_output_file": "default",
  "files.mesh_file": "default",
  "files.nodeset_file": "default",
  "output_1": 1.1
}
```
````
`````

Next, create two design variable connections:

1. from the 'output_0' output handle of the parametric-model component to the 'output_0' input handle of the calculix-fea component. 
2. from the 'output_1' output handle of the calculix-fea component to the 'output_1' input handle of the fea-results-processor component.


### Execute the workflow

We can now execute the design optimisation by selecting the play symbol ▶ in the Run controls interface. 

The {term}`Run` should complete after 23 iterations of the chained components (1 iteration of the `open-mdao` component). 

```{note}
Note that the `parametric-model` component executes only once, since it's artificially created design variable input ("input_0": 0.1) doesn't change. 
```

### Inspect the outputs

The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 
The "run_output" entry (at the end of the log) should state that the "OpenMDAO compute completed".  

Next, close the {term}`Run` log and select the `open-mdao` component.
Then select the `Log` tab and click on `download files snapshot`.

The optimisation study outputs are summarised at the end of the 'run_driver.log' file in the 'outputs' folder, as shown below.
We can also inspect the convergence history plots of the design variable, objective and constraints functions in the same folder.

The optimal fibre rotation angle converges after 11 SLSQP algorithm iterations to ~22.68 degrees, which results in a wing tip incidence of -0.0377 radians and a vertical deflection of 6cm. 

```{code}
Driver debug print for iter coord: rank0:ScipyOptimize_SLSQP|22
---------------------------------------------------------------
Design Vars
{'calculix_fea.fibre_rotation_angle-ORI_0-1': array([22.68391541])}

Calling compute.
message: 
 {'component': 'parametric-model', 'inputs': {'design': {'input_0': [0.1]}}, 'get_grads': False, 'get_outputs': True}
Calling compute.
message: 
 {'component': 'calculix-fea', 'inputs': {'design': {'fibre_rotation_angle.ORI_0.1': [22.683915410923078], 'output_0': [1.1]}}, 'get_grads': False, 'get_outputs': True}
Calling compute.
message: 
 {'component': 'fea-results-processor', 'inputs': {'design': {'output_1': [24.0]}}, 'get_grads': False, 'get_outputs': True}
Nonlinear constraints
{'fea_results_processor.Uz': array([0.05999995])}

Linear constraints
None

Objectives
{'fea_results_processor.Ry': array([-0.03771947])}

Optimization terminated successfully    (Exit mode 0)
            Current function value: -0.03771946528223136
            Iterations: 11
            Function evaluations: 22
            Gradient evaluations: 11
Optimization Complete
-----------------------------------
```


```{image} media/open-mdao-parametric-model-2.png
:alt: results-plot
:class: bg-primary mb-1
:width: 400px
:align: center
```
```{image} media/open-mdao-parametric-model-3.png
:alt: results-plot
:class: bg-primary mb-1
:width: 400px
:align: center
```
```{image} media/open-mdao-parametric-model-4.png
:alt: results-plot
:class: bg-primary mb-1
:width: 400px
:align: center
```

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` data (session data, inputs and outputs) will be permanently deleted. 
```

(tutorials-automating-design-optimisations-references)=
## References

1. [Design optimisation in practice with Python, OpenMDAO and Scipy](https://www.dapta.com/design-optimisation-in-practice-with-python-openmdao-and-scipy/)