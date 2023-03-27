# Using OpenVSP for aircraft performance analysis

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/8).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/openvsp-aircraft-aircraft-performance).

```{image} media/openvsp-performance-1.png
:alt: vsp3 model of a Cessna 210
:class: bg-primary mb-1
:width: 400px
:align: right
```

**Duration: 60 min**

In this example we create a simple aircraft performance analysis workflow using [OpenVSP](https://openvsp.org/) and [OpenMDAO](https://openmdao.org/). 

We also demonstrate how to execute components in parallel to speed up large parametric studies.   


## Problem description

Theory tells us that an aircraft's optimal cruise velocity for minimum thrust is where its lift to drag ratio (L/D) is maximised, which also corresponds to the flight velocity where the total drag (including lift-induced drag) is minimised.
In this example, we wish to graphically determine this optimal cruise velocity for a Cessna 210 for a range of different wing aspect ratios, given a certain flight altitude and fixed aircraft total mass.

We use a representative OpenVSP aircraft model (Cessna-210_metric.vsp3) as shown above. 
The aircraft's aerodynamic lift, drag and pitching moment coefficients are calculated using the vortex lattice method (VLM) implemented in the VSPAERO solver that comes with OpenVSP.
The model is in SI units (m/s/kg). 
Only the wing and the horizontal tailplane (HTP) are modelled in the VLM analysis, with the input mesh and a example output pressure distribution shown below. 

It is not necessary to install OpenVSP on your machine for this example, since most of the analysis input and output data can also be accessed by opening the files in a simple text editor. 
However, you will need to install OpenVSP if you want to run the component code locally since we will be using the OpenVSP python API in the next section.   

```{image} media/openvsp-performance-2.png
:alt: VLM mesh and pressure distribution
:class: bg-primary mb-1
:width: 700px
:align: center
```

To determine the optimum flight velocity, we need to be able to perform multiple trimmed aircraft analyses for different cruise velocities and wing aspect ratios. 
The aircraft is trimmed in level flight when all forces and moments about the aircraft's centre of gravity (CG) cancel out. 

Unfortunately, VSPAERO only does part of the job for us.
It allows us to calculate the aircraft's aerodynamic coefficients for a certain configuration, but it can't calculate the aircraft trim angle of attack (AoA) or the HTP angle required to balance the aero forces and moments out with the aircraft's weight (assuming that thrust can be set to cancel out drag). 

To solve this problem we can add a trim component to our simulation workflow as shown below. The trim component introduces a feedback cycle that adjusts the trim variables (AoA and HTP angles) based on the forces and moments at the aircraft's CG. 
We can use Newton's method to converge the cycle to a trimmed solution.

```{image} media/openvsp-performance-3.png
:alt: trim analysis cycle
:class: bg-primary mb-1
:width: 700px
:align: center
```

Finally, we choose to use OpenMDAO as the driver component for our workflow for 3 main reasons: 
 1. It allows us to easily implement the trim analysis cycle mentioned above by using an 'implicit' component and variable promotion (where normal dapta design variable connections can only go forwards).
 2. It includes nonlinear solvers, including a versatile [Newton solver](https://openmdao.org/newdocs/versions/latest/features/building_blocks/solvers/newton.html) which can be used to converge the trim solution.
 3. It allows us to set up a design of experiments workflow to iteratively solve the aircraft trim problem for different flight conditions and aircraft designs.

## Create the components

The following sections will guide you through the creation of the simulation workflow starting from an empty workspace.
**Already signed-up?**
[Access your workspace here.](https://app.daptaflow.com/) 
### VSPAERO component

The purpose of this component is to calculate the aerodynamic forces and moments about the aircraft's CG for a given set of inputs and parameters.
The inputs include the aircraft angle of attack (AoA), the HTP angle (HTP_RY) and the half-wing aspect ratio (desvars_PONPNSVRANE). 
Multiply the half-wing aspect ratio by 2 to recover an approximate full wing aspect ratio value (with the error due to dihedral angle). 

Parameters include the OpenVSP model input file (Cessna-210_metric.vsp3), an OpenVSP design variables file (Cessna-210_metric.des) and a "HTP_RY_ID" lookup  parameter.
Note that the wing aspect ratio variable name and the value of the "HTP_RY_ID" parameter both refer to 11 character IDs from the OpenVPS design variables file instead of being hard-coded in the python script. 

The `compute.py` module makes use of the [OpenVSP python API](https://openvsp.org/api_docs/latest/) to read the model files, to apply the input values to the model, to setup and execute the VSPAERO analysis and to recover the analysis outputs.     
The API is contained in the `vsp` object that is imported at the top of the file (`import openvsp as vsp`).

**Parallel execution:** We use the "replicas" option on the `Properties` tab to create 4 independent copies of this component. This number should match the number of python threads set up in the OpenMDAO DOE driver. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `vspaero`, and select the OpenVSP component API `openvsp-comp:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `Cessna-210_metric.vsp3` and `Cessna-210_metric.des` files from below into a text editor, save them locally.
Then upload the first 2 files under the `Properties` tab and upload the `.vsp3` and `.des` files under the `Parameters` tab by selecting `upload user input files`. 

* In the `Properties` tab copy the following JSON object into the `Options` text box:

```{code}
{
    "replicas": 4
}
```

* Also in the `Properties` tab check the box next to the `Start Node` option. 

* Insert the following JSON object into the `Parameters` tab text box (below the "user_input_files" entry):

```{code}
{
    "HTP_RY_ID": "ABCVDMNNBOE",
    "vsp3_file": "Cessna-210_metric.vsp3",
    "des_file": "Cessna-210_metric.des"
}
```

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
    "AoA": 0,
    "HTP_RY": 0,
    "desvars_PONPNSVRANE": 3.86
}
```

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
    "CL": 0,
    "CMy": 0,
    "CDtot": 0,
    "L2D": 0,
    "E": 0
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./openvsp-aircraft-aircraft-performance/vspaero/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./openvsp-aircraft-aircraft-performance/vspaero/compute.py
:language: python
```
````
````{tab-item} Cessna-210_metric.vsp3
[Download Cessna-210_metric.vsp3 from Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/openvsp-aircraft-aircraft-performance/vspaero/Cessna-210_metric.vsp3)
````
````{tab-item} Cessna-210_metric.des
```{literalinclude} ./openvsp-aircraft-aircraft-performance/vspaero/Cessna-210_metric.des
:language: text
```
````
`````


### Trim component

This is a simple analytical implicit component that calculates the force and pitching moment residuals at the aircraft CG. 
The inputs are the lift and pitching moment coefficients from the vspaero component and the flight velocity (Vinfinity). 
Fixed parameters include the aircraft total mass, flight altitude and wing reference area (S).       

Note that OpenMDAO implicit components don't usually have a compute function. 
By inspecting the OM_component.py file in the OpenMDAO component below, we can see that the trim component's `compute` function is actually called from within the implicit component's `apply_nonlinear` method.     
The [OpenMDAO Advanced user guide](https://openmdao.org/newdocs/versions/latest/advanced_user_guide/models_implicit_components/models_with_solvers_implicit.html) explains the structure and purpose of implicit components in more detail.  

**Parallel execution:** This component is not parallelised as it executes quickly compared to the vspaero analysis. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `trim`, and select the generic python component API `generic-python3-comp:latest`. 

* Copy the contents of the `setup.py`, `compute.py` and `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

* Also in the `Properties` tab check the box next to the `End Node` option. 

* Insert the following JSON object into the `Parameters` tab text box (below the "user_input_files" entry):

```{code}
{
    "Mass": 1111,
    "Altitude": 3000,
    "S": 16.234472
}
```

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
    "CL": 0,
    "CMy": 0,
    "Vinfinity": 40
}
```

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
    "AoA": 0,
    "HTP_RY": 0
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./openvsp-aircraft-aircraft-performance/trim/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./openvsp-aircraft-aircraft-performance/trim/compute.py
:language: python
```
````
````{tab-item} requirements.txt
```{literalinclude} ./openvsp-aircraft-aircraft-performance/trim/requirements.txt
:language: text
```
````
`````


### OpenMDAO driver component

The driver component is identical to the OpenMDAO component used in the [Simple optimisation problem](./Simple%20optimisation%20problem.md) example, except for the driver parameters (defined on the `Parameters` tab), which have been adjusted for this problem:

* The driver type is set to "doe" instead of "optimisation" to request a sweep of the design space. In the `compute.py` module, this selects the use of the [OpenMDAO "FullFactorialGenerator"](https://openmdao.org/newdocs/versions/latest/features/building_blocks/drivers/doe_driver.html) to define the design points to evaluate. The number of design points can be increased via the {"driver":{"kwargs":{"levels":{"Vinfinity": 2, "desvars_PONPNSVRANE": 2}}}} parameter values (minimum of 2 points per design variable).    
* The design space is defined by the "input_variables" object, listing upper and lower values for the flight velocity range (Vinfinity) and for the wing aspect ratio range (desvars_PONPNSVRANE).
* We define a OpenMDAO group object named "cycle", which has both a nonlinear solver and linear solver attached. 
By referencing this group by name in the vspaero and trim component entries (under "ExplicitComponents" and "ImplicitComponents"), these components are automatically included in the cycle group. 
* The trim variables ("AoA" and "HTP_RY") feedback connection is implemented by promotion of the variables as inputs in the vspaero component and as outputs in the trim component. 
* The {"visualise":"plot_history"} option here is used to call a custom plotting function imported from the `post.py` user file.   

**Parallel execution:** We use the {"driver":{"nb_threads":4}} parameter to create 4 python execution threads, each launching a quarter of the design cases (using a modified OpenMDAO DOEDriver class, defined in the `compute.py` module). The number of doe threads should match the number of vspaero replicas set up earlier.   

To create the driver component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `open-mdao`, and select the component API `generic-python3-driver:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

* In the `Properties` tab check the box next to the `Driver` option. 

* Copy the contents of the parameters JSON object below into the `Parameters` tab text box. 

* Copy the contents of the `om_component.py` and `post.py` files from below into a text editor and save them locally. 
Then upload them under the `Parameters` tab by selecting `upload user input files`.

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
```{literalinclude} ./openvsp-aircraft-aircraft-performance/driver_parameters.json
:language: json
```
````
````{tab-item} om_component
```{literalinclude} ./open-mdao-paraboloid/om_component.py
:language: python
```
````
````{tab-item} post
```{literalinclude} ./openvsp-aircraft-aircraft-performance/post.py
:language: python
```
````
`````

### Connections

Finally, we connect the outputs of the vspaero component to the inputs of the trim analysis component.

In the workspace view, create a connection by selecting the "CL" output handle of the vspaero component and dragging a line to the corresponding input handle of the trim component.
Repeat for the "CMy" handles. 
Hover the mouse pointer over a handle to see the name of the associated input or output data appear below the component.   
Both connections are 'Design variable' type connections by default (black line), which is the type of connection we need in this case.  

The workspace should now contain the 3 components and 2 connections as shown below. 

```{image} media/openvsp-performance-4.png
:alt: workspace view
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Execute the workflow

We can now execute the {term}`Run` by selecting the play symbol ▶ in the Run controls interface. 
Once the run has started, each component will setup and then execute. 

Open the vspaero component and select the `Log` tab as shown below.
Each log line lists a component event by time and iteration number. 
Notice that the first 4 compute events happen practically simultaneously, indicating that the 4 replicas are active. 
After that, new compute requests are executed as soon as a free replica is available, resulting in seemingly random series of "SLEEP" and "COMPUTE" events.  

The {term}`Run` should complete after a couple of minutes once the vspaero component compute has completed 44 iterations (1 iteration of the open-mdao component). 

```{image} media/openvsp-performance-8.png
:alt: vspaero log entries
:class: bg-primary mb-1
:width: 700px
:align: center
```

(tutorials-openvsp-aircraft-performance-outputs)=
## Inspect the outputs

The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 
The first three "run_output" entries are setup messages from the vspaero component 4 replicas, the trim and open-mdao components.
Notice that the vspaero messages include the replica hostname, which is different for each replica and always starts with "vspaero-".     
The last "run_output" entry should state that the "OpenMDAO compute completed".  

Next, close the {term}`Run` log and select the `open-mdao` component.
Then select the `Log` tab and click on `download files snapshot`.
The outputs folder should include the n2 diagram (shown below), the driver log file (useful to check Newton solver convergence), one results file per driver thread in JSON format and results plots in .png format. 

```{image} media/openvsp-performance-5.png
:alt: n2 diagram
:class: bg-primary mb-1
:width: 700px
:align: center
```

Since we set the DOE driver "levels" values to 2 for both input variables, the driver only executed 4 cases in total (1 per thread), each case being a combination of the maximum / minimum variable values.
As a result, the plots show straight lines as shown below.  

Clearly, we do not have enough data from this run to graphically determine the optimal cruise velocity.
We'll resolve this problem in the next section. 

```{image} media/openvsp-performance-6.png
:alt: L/D from the first run
:class: bg-primary mb-1
:width: 500px
:align: center
```

## Increase the number of design points and re-run

Select the open-mdao component in the workspace to edit it:

* Select the `Parameters` tab and scroll to the "driver" object. 
* Update the existing {"driver":{"kwargs":{"levels":{}}}} parameter values to:

```{code}
"levels": {
    "Vinfinity": 21,
    "desvars_PONPNSVRANE": 3
}
```

* Select `Save data` to save and close the component. 

Execute {term}`Run` again by selecting the play symbol ▶ in the Run controls interface. 
The DOE driver will execute 63 cases (21 velocities for 3 aspect ratios) and should complete within ~33min. 

The figure below shows the L/D variation obtained. 
The maximum L/D cruise velocity occurs between 55m/s and 60m/s. 
As expected, the maximum L/D increases with increasing half-wing aspect ratio and the maximum L/D cruise velocity decreases.  

```{image} media/openvsp-performance-7.png
:alt: L/D from the second run
:class: bg-primary mb-1
:width: 500px
:align: center
```

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` data (session data, inputs and outputs) will be permanently deleted. 
```
