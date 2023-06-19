# A fluid-structure interaction simulation with preCICE, OpenFOAM and CalculiX

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/11).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/precice/perpendicular_plate).

**Duration: 45 min**

In this tutorial we explore the usage of the [preCICE multi-physics simulations library](https://precice.org/) with an FSI example. We run a fluid-structure interaction simulation with OpenFOAM to model the fluid flow and CalculiX to model the behaviour of a flexible flap exposed to the fluid flow.

This tutorial is based on the [Perpendicular flap](https://precice.org/tutorials-perpendicular-flap.html) preCICE tutorial.  

```{image} media/precice-perpendicular-flap-1.gif
:alt: FSI simulation with preCICE
:class: bg-primary mb-1
:width: 700px
:align: center
```

## What is preCICE?

[preCICE](https://precice.org/) stands for Precise Code Interaction Coupling Environment. Its main component is a library that can be used for partitioned multi-physics simulations, including, but not restricted to fluid-structure interaction and conjugate heat transfer simulations. Partitioned (as opposite to monolithic) means that preCICE couples existing programs (solvers) which simulate a subpart of the complete physics involved in a simulation. 

The main elements of the preCICE library are shown in the following figure and include: communication, data mapping, coupling schemes and time interpolation. Read the [preCICE docs](https://precice.org/docs.html) to find out more about preCICE and how to use it. 

```{image} media/precice-1.png
:alt: preCICE overview
:class: bg-primary mb-1
:width: 700px
:align: center
```

## FSI model description

We model a two-dimensional fluid flowing through a channel. A solid, elastic flap is fixed to the floor of this channel. The flap oscillates due to the fluid pressure building up on its surface. 
The setup is shown schematically in the figure below. 

The simulated flow domain is 6 units long (x) and 4 units tall (y). The flap is located at the center of the bottom (x=0) and is 1 unit long (y) and 0.1 units thick (x). We set the fluid density to 1.0kg/m, the kinematic viscosity to 1.0m^2/s, the solid density to 3.0\*10^3kg/m^3, the solid Young’s modulus to E=4.0\*10^6kg/ms^2 and Poisson ratio to 0.3.
​On the left boundary a constant inflow profile in x-direction of 10m/s is prescribed. The right boundary is an outflow and the top and bottom of the channel as well as the surface of the flap are no-slip walls.

```{image} media/precice-perpendicular-flap-2.png
:alt: FSI model overview
:class: bg-primary mb-1
:width: 400px
:align: center
```

## Create the Components

### OpenFOAM fluid

This component simulates the fluid flow in the channel. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `fluid-openfoam`, and select the preCICE-openFOAM component API `precice-openfoam-comp:latest`. 

* Copy the contents of the `setup.py` and `compute.py` files from below into a text editor, save them locally. 
Then upload them under the `Properties` tab.

* In the `Properties` tab check the box next to the `Start Node` option.

* Copy the the following JSON object into the `Parameters` tab text box:

```{code}
{
  "openfoam_precice": {
    "subfolder": "fluid-openfoam"
  }
}
```

* From github download copies of the preCICE configuration file [precice-config.xml](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/perpendicular_plate/fluid-openfoam/precice-config.xml) and of the zip folder with the openFOAM input files [fluid-openfoam.zip](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/perpendicular_plate/fluid-openfoam/fluid-openfoam.zip). Then upload these two files under the `Parameters` tab by selecting `upload user input files`.  

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
  "dummy_output": 0
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./precice/perpendicular_plate/fluid-openfoam/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./precice/perpendicular_plate/fluid-openfoam/compute.py
:language: python
```
````
`````

### CalculiX solid

This component simulates the flexible flap fixed to the lower surface of the channel. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `solid-calculix`, and select the preCICE-CalculiX component API `precice-calculix-comp:latest`.

* Copy the contents of the `setup.py` and `compute.py` files from below into a text editor, save them locally. 
Then upload them under the `Properties` tab.

* In the `Properties` tab check the box next to the `End Node` option.

* Copy the the following JSON object into the `Parameters` tab text box:

```{code}
{
  "ccx_precice": {
    "env": {},
    "infile": "flap.inp",
    "participant": "Solid",
    "subfolder": "solid-calculix"
  }
}
```

* From github download copies of the preCICE configuration file [precice-config.xml](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/perpendicular_plate/solid-calculix/precice-config.xml) and of the zip folder with the CalculiX input files [solid-calculix.zip](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/perpendicular_plate/solid-calculix/solid-calculix.zip). Then upload these two files under the `Parameters` tab by selecting `upload user input files`.  

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
  "dummy-input": 0
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./precice/perpendicular_plate/solid-calculix/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./precice/perpendicular_plate/solid-calculix/compute.py
:language: python
```
````
`````

### PreCICE driver

In general, preCICE participants are launched in separate processes and the coupled simulation only starts once both processes have been launched.

To replicate this approach, we define a driver component that launches the fluid and solid components in parallel using the python [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor) class. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `precice-driver`, and select the generic python driver API `generic-python3-driver:latest`. 

* Copy the contents of the `setup.py` and `compute.py` files from below into a text editor, save them locally. 
Then upload them under the `Properties` tab.

* In the `Properties` tab check the box next to the `Driver` option. 

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./precice/perpendicular_plate/precice-driver/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./precice/perpendicular_plate/precice-driver/compute.py
:language: python
```
````
`````

## Create the Connections

We need to create a 'Design variable' type connection (black line) that links the fluid component to solid component.
It exists purely to satisfy the basic workflow requirements that simulation workflows should have a single starting component and that all (non-driver) components should be connected.
In this case we choose the fluid component to be the start node (you can equally choose the solid component, without affecting the analysis in this case).  

Selecting the 'dummy_output' output handle of the fluid-openfoam component and drag a line to the 'dummy-in' input handle of the solid-calculix component.

## Execute the workflow

We can now execute the analysis {term}`Run` by selecting the play symbol ▶ in the Run controls interface. 

Once the run has started, each component will setup one at a time. 
The setup order is arbitrary. 
Then the compute on the driver, fluid and solid components will run in simultaneously until the coupled analysis completes, which should take less than ~10min.

The workspace should appear as shown below.

```{image} media/precice-perpendicular-flap-3.png
:alt: preCICE overview
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Inspect the outputs

The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 
Scroll down to the "run_output" section to see that this contains the setup and compute function output messages from all three components (including the driver) in the order of execution as shown below.

```{image} media/precice-perpendicular-flap-4.png
:alt: run log
:class: bg-primary mb-1
:width: 700px
:align: center
```

You can download the session data and the {term}`Run` log now by selecting `Download` from the interface controls. 

To access the openFOAM analysis output, select the fluid-openfoam component, navigate to the `Log` tab and select `download files snapshot` to download a zip folder containing the component files. 
The outputs subfolder contains a zipped openFOAM outputs folder. 

Local access to Paraview is required to visualise the openFOAM analysis output.
Unzip the outputs folder into a local directory, then open the fluid-openfoam.foam file in Paraview, for example by executing the following shell command: 
`paraview fluid-openfoam.foam`

Similarly, to access the CalculiX outputs, select the solid-calculix component, navigate to the `Log` tab and select `download files snapshot`. 
This output contains a 5s trace of the solid flap tip deflections and applied forces in the precice-Solid-watchpoint-Flap-Tip.log file, which can be plotted as described in [Ref 1](tutorials-precice-perpendicular-flap-references).

## Clean-up

Delete your workflow by selecting `Open` in the interface and then select the `Delete` button for the loaded workflow. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` session data (Run log and component logs) will be permanently deleted. 
```

(tutorials-precice-perpendicular-flap-references)=
## References

1. [Perpendicular flap preCICE tutorial](https://precice.org/tutorials-perpendicular-flap.html)