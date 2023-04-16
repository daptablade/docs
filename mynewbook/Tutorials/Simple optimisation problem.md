# Simple optimisation problem

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/2).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/open-mdao-paraboloid).

```{image} media/paraboloid_optimisation.gif
:alt: paraboloid-optimisation 
:class: bg-primary mb-1
:width: 400px
:align: right
```

**Duration: 15 min**

In this example we solve a simple analytical function minimisation problem. 
We create an optimisation driver component using the [openMDAO](https://openmdao.org) python package, and then use it to determine the unconstrained and constrained minimum values of the paraboloid function from the [previous example](./Simple%20component%20analysis.md).  

## Opening a saved session

Since we already created and analysed the paraboloid component previously, we can load our previous session to speed things up. 

Select `Open` from the interface controls to load the JSON formatted version of our previous session (dapta_input.json). 
Alternatively, copy the object below into a text editor and save it locally, then select `Open` to load it. 

```{literalinclude} ./paraboloid/dapta_input.json   
:language: json
```

The paraboloid component should have appeared in the workspace, but the question mark next to the component name indicates that it is missing some data. 
To fully define it, we need to upload the component `setup.py` and `compute.py` input files under the component `Properties` tab again. 
The file contents are available under the [Simple Component Analysis](tutorials-paraboloid-files) example.

## Create the driver component

Right-click in the workspace and select `Add Empty Node`.
This adds an empty template component to your workspace. 

Select the empty component to edit it. 

### Properties

In the `Properties` tab, fill in the component name, `open-mdao`, and select the driver component API `generic-python3-driver:latest`. 

Just as in the previous example, the python driver requires `setup.py` and `compute.py` input files to be uploaded. 
In addition, we also upload a `requirements.txt` file, so that we can access the openMDAO package in the python code.
You can inspect the contents of the files below. 

In the `compute.py` file, we can see that the imports include the 'numpy' and 'openmdao' packages that we listed in the `requirements.txt` file. 
In addition, we import a `call_compute` function from the `component_api2.py` module that is specific to the `generic-python3-driver` API and allows the driver to execute other components (this is the main difference with the `generic-python3-comp` API!). 

The last import in the `compute.py` module (`from om_component import ...`) is specific to our component and provides a custom implementation of the openMDAO ExplicitComponent class. The contents of the `om_component.py` module are shown below and we will upload this as a Parameter input file in the next section.   

Finally, check the box next to the `Driver` option as shown below.

(tutorials-open-mdao-paraboloid-files)=
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
````{tab-item} om_component
```{literalinclude} ./open-mdao-paraboloid/om_component.py
:language: python
```
````
`````

```{image} media/open-mdao-paraboloid-1.png
:alt: properties-tab-completed
:class: bg-primary mb-1
:width: 700px
:align: center
```

### Parameters

Select the `Parameters` tab and copy the 'unconstrained' parameters JSON object into the text box. 

(tutorials-open-mdao-paraboloid-parameters)=
`````{tab-set}
````{tab-item} unconstrained
```{literalinclude} ./open-mdao-paraboloid/unconstrained_params.json
:language: json
```
````
````{tab-item} constrained
```{literalinclude} ./open-mdao-paraboloid/constrained_params.json
:language: json
```
````
`````

These parameters are used in the `compute.py` module to define a standard openMDAO optimisation problem. 

Next, as mentioned in the previous section, we also need to upload the `om_component.py` module. 
Copy the contents of the ['om_component' tab above](tutorials-open-mdao-paraboloid-files) into a text editor and save as 'om_component.py'.  
Select the `upload user input files` link at the bottom of the `Parameters` tab to upload the file. 
The upload was successful if a corresponding entry appears under the 'user_input_files' section of the JSON object in the `Parameters` text box. 

By extracting parameters from the python code and defining them in the `Parameters` tab instead, we can change the optimisation setup without having to view or modify the python code. 
This makes it easier to track input changes and to compare Runs (e.g. via the session file). 
The component also becomes more general, robust and re-usable. 
We will demonstrate the benefits of this approach in the next section by replacing the 'unconstrained' parameters with the 'constrained' ones.  

Select `Save data` to save the edits and close the component interface. 

Select `Download` from the interface controls to save the current session as a local JSON file. 

## Executing the driver

We should now have a valid {term}`Run` with two components: the paraboloid analysis and the open-mdao driver.

Execute the {term}`Run` by selecting the play symbol ▶ in the {term}`Run` controls interface and wait for it to complete. 
As before, this may take a few minutes as your {term}`Run` is being processed in the Cloud. 
If you don't get a message saying that the {term}`Run` was successful, try to refresh your web browser page or consult the [FAQ](../Reference/FAQs.md) section for troubleshooting suggestions. 

### The unconstrained optimisation problem 

We can now inspect the outputs of the unconstrained optimisation {term}`Run`.

Select `View Log` to view the Run log as shown below.
The optimisation outcome is summarised in the 'open-mdao' entry, which indicates that the optimisation completed successfully. 
The optimisation input values (x, y) converged to the known analytical solution within a few decimals ($x=\frac{20}{3}$, $y=-\frac{22}{3}$). 
If we scroll down, we can see that the paraboloid component has 13 separate entries, each one corresponding to one analysis execution of the component.  

```{image} media/open-mdao-paraboloid-2.png
:alt: run-log-open-mdao-paraboloid-unconstrained
:class: bg-primary mb-1
:width: 700px
:align: center
```

We can also look at the outputs of the open-mdao component in more detail. 
Select the open-mdao component in the workspace and navigate to the `Log` tab, then select `download files snapshot`. The 'outputs' folder should contain three files:

* **n2.html** : A visual representation of the optimisation problem. We can switch this output off by removing the 'n2_diagram' entry from the 'visualise' list in the component Parameters.  
* **om_problem_recorder_(time-stamp).sqlite** : An openMDAO recorder database can be used for further data analysis, visualisation and results storage. The contents of the database can be adjusted (see the use of the 'om.SqliteRecorder' class in the open-mdao compute function).
* **run_driver.log** : a log file that contains the openMDAO stdout output and any additional print() function outputs from the `om_component.py` module. 

````{note}
Python print() output can be very useful for capturing intermediary variable values and for debugging purposes. 
In order to access this output in a log file, you can use the following python code construct (see the `compute.py` module for an example): 

```{code}
from contextlib import redirect_stdout

with open(run_folder / "filename.log", "w") as f:
    with redirect_stdout(f):
        print("This is a log message!")
```
````

Below is an extract from the end of the `run_driver.log` file. 
This file provides some interesting insights into the optimisation process. 

It appears that the SLSQP optimisation converged to an optimum after 4 iterations, which included 5 'Function evaluations' to calculate the function outputs and 4 'Gradient evaluations' to calculate the derivatives (gradient) of the paraboloid function with respect to the design variables x and y. 

Looking at the frequency of the 'Calling compute' message in the last iteration, we can see that the 'Function evaluation' executed the paraboloid component once and that the 'Gradient computation' executed it twice (once for each design variable). 
This is because we requested the finite difference gradient calculation method by setting `"approx_totals": true` in the in the Parameters (with the 'fd_step' parameter setting the size of the step). 

The paraboloid component was therefore executed a total of 13 times, which matches the {term}`Run` log output. 

Save the session data and Run log by selecting `Download` from the interface controls. 

```{code}
Driver debug print for iter coord: rank0:ScipyOptimize_SLSQP|5
--------------------------------------------------------------
Design Vars
{'paraboloid.x': array([6.66663333]), 'paraboloid.y': array([-7.33336667])}

Calling compute.
message: 
 {'component': 'paraboloid', 'inputs': {'y': [-7.333366666671174], 'x': [6.666633333303766]}, 'get_grads': False, 'get_outputs': True}
Nonlinear constraints
None

Linear constraints
None

Objectives
{'paraboloid.f_xy': array([-27.33333333])}

Driver total derivatives for iteration: 6
-----------------------------------------

Calling compute.
message: 
 {'component': 'paraboloid', 'inputs': {'y': [-7.333366666671174], 'x': [6.666733333303766]}, 'get_grads': False, 'get_outputs': True}
Calling compute.
message: 
 {'component': 'paraboloid', 'inputs': {'y': [-7.333266666671174], 'x': [6.666633333303766]}, 'get_grads': False, 'get_outputs': True}
Elapsed time to approx totals: 0.11306452751159668 secs

{('paraboloid.f_xy', 'paraboloid.x'): array([[-5.82076609e-11]])}
{('paraboloid.f_xy', 'paraboloid.y'): array([[-5.82076609e-11]])}

Optimization terminated successfully    (Exit mode 0)
            Current function value: -27.333333329999995
            Iterations: 4
            Function evaluations: 5
            Gradient evaluations: 4
Optimization Complete
-----------------------------------
```

### The constrained optimisation problem 

We now wish to add the following constraint to the optimisation problem

$$ 
  0.0 \leq g(x,y) \leq 10.0  \quad , \quad g(x,y) = x + y  . 
$$

Instead of adding another component to the {term}`Run`, we can implement this simple constraint using an openMDAO [ExecComp](https://openmdao.org/newdocs/versions/latest/features/building_blocks/components/exec_comp.html) component. 

Select the open-mdao component in the workspace to edit it, navigate to the `Parameters` tab, and copy and paste the [constrained](tutorials-open-mdao-paraboloid-parameters) Parameter values. 

A few changes have been made compared to the unconstrained problem Parameters:

* The 'ExplicitComponents' section is added to promote the paraboloid component x and y variables to global problem variables.
* The 'ExecComps' section is added to define the a component named 'constraint'.
* The constraint output is added to the 'output_variables' list.
* The finite difference gradient calculations are switched off by setting 'approx_totals' to false. 

Select `Save data` to save and close the component. 

Note that it is not necessary to upload the `om_component.py` module again. 
To verify this, you can open the open-mdao component `Parameters` tab and the file entry should appear again under 'user_input_files', just as before.   

Create a new {term}`Run` by selecting the play symbol ▶ in the {term}`Run` controls interface. 
This should execute very quickly. 

Select `View Log` to view the Run log as shown below. 
The open-mdao component entry lists optimal x and y values for the constrained problem, which have converged within a few decimals of the analytical solution ($x=7$, $y=-7$).

```{image} media/open-mdao-paraboloid-3.png
:alt: run-log-open-mdao-paraboloid-constrained
:class: bg-primary mb-1
:width: 700px
:align: center
```

Select the open-mdao component in the workspace, open the `Log` tab and select `download files snapshot`. 

Visually compare the N2 diagram (n2.html) shown below with that from the previous {term}`Run`.  
The new constraint component appears as another Explicit Component under the paraboloid component. 

Next, inspect the 'run_driver.log' output file. 
Only 2 iterations, with 2 'Function evaluations' and 2 'Gradient evaluations' were required to reach convergence. 
The 'Calling compute_partials' messages confirm that instead of using finite differencing, we are now requesting the analytical gradient information directly from the paraboloid component. 
With one paraboloid component evaluation yielding derivatives with respect to all variables, this approach is significantly more efficient than the finite differencing method.  

For comparison, a reference pure python/openMDAO implementation of this problem can be found in the [Optimization of Paraboloid](https://openmdao.org/newdocs/versions/latest/basic_user_guide/single_disciplinary_optimization/first_optimization.html) section of the openMDAO user guide. 

Save the session data and Run log by selecting `Download` from the interface controls. 

```{image} media/open-mdao-paraboloid-4.png
:alt: n2-open-mdao-paraboloid-constrained
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` session data (Run log and component logs) will be permanently deleted. 
```

## References

1. [Simple Optimization](https://openmdao.org/newdocs/versions/latest/examples/paraboloid.html?highlight=unconstrained) example from the openMDAO user guide.
2. [Optimization of Paraboloid](https://openmdao.org/newdocs/versions/latest/basic_user_guide/single_disciplinary_optimization/first_optimization.html) section of the openMDAO user guide.