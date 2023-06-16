# A structure-structure interaction simulation with preCICE and CalculiX

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/10).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/precice/partitioned_elastic_beam).

**Duration: 45 min**

In this tutorial we explore the usage of the [preCICE multi-physics simulations library](https://precice.org/) with a simple partitioned elastic beam example. We run a structure-structure interaction simulation with CalculiX running on both sides and then automate the post-processing of the output files for visualisation.

This tutorial is based on the [Partitioned elastic beam](https://precice.org/tutorials-partitioned-elastic-beam.html) preCICE tutorial.  

```{image} media/precice-elastic-beam-1.png
:alt: structure-structure interaction simulation
:class: bg-primary mb-1
:width: 700px
:align: center
```

## What is preCICE?

[preCICE](https://precice.org/) stands for Precise Code Interaction Coupling Environment. Its main component is a library that can be used for partitioned multi-physics simulations, including, but not restricted to fluid-structure interaction and conjugate heat transfer simulations. Partitioned (as opposite to monolithic) means that preCICE couples existing programs (solvers) which simulate a subpart of the complete physics involved in a simulation. 

The main elements of the preCICE library are shown in the following figure and include: communication, data mapping, coupling schemes and time interpolation. Read the [preCICE docs](https://precice.org/docs.html) to find out more about preCICE and how to use it. 

```{image} media/precice-elastic-beam-2.png
:alt: preCICE overview
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Beam model description

We have a rectangular linear elastic beam of dimensions 1 x 1 x 8 m, divided in two subdomains by a splitting plane at z = 6 m. This plane corresponds to the coupling surface. Both ends of the beam (z = 0 and z = 8 m) are fixed. A mechanical load F = -0.001 N is applied constantly along the y-axis onto a small set of nodes near the end of the beam. These boundary conditions can be seen in the input files beam<x>.inp. Initial conditions are zero both for position and velocity. Other parameters can be found and customized in the .inp files.

```{image} media/precice-elastic-beam-3.png
:alt: elastic beam
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Create the Components

### Beam-1

This component simulates the structural dynamic behaviour of the first beam subdomain (from z = 0 to z = 6 m). 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `beam-1`, and select the preCICE-CalculiX component API `precice-calculix-comp:latest`. 

* Copy the contents of the `setup.py` and `compute.py` files from below into a text editor, save them locally. 
Then upload them under the `Properties` tab.

* In the `Properties` tab check the box next to the `Start Node` option.

* Copy the contents of the parameters JSON object below into the `Parameters` tab text box. 

* From github download copies of the preCICE configuration file [precice-config.xml](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/partitioned_elastic_beam/beam/precice-config.xml) and of the zip folder with the CalculiX mesh files [part_1.zip](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/partitioned_elastic_beam/beam/part_1.zip). Then upload these two files under the `Parameters` tab by selecting `upload user input files`.  

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
  "dummy_output": 0,
  "files.beam_frd": "default"
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./precice/partitioned_elastic_beam/beam/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./precice/partitioned_elastic_beam/beam/compute.py
:language: python
```
````
````{tab-item} parameters
```{literalinclude} ./precice/partitioned_elastic_beam/beam/parameters-beam-1.json
:language: json
```
````
`````

### Beam-2

This component simulates the structural dynamic behaviour of the second beam subdomain (from z = 6 to z = 8 m). 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `beam-2`, and select the preCICE-CalculiX component API `precice-calculix-comp:latest`. 

* The `setup.py` and `compute.py` files are identical to the files from the beam-1 component. 
Upload them again here under the `Properties` tab.

* Copy the contents of the parameters JSON object below into the `Parameters` tab text box. 

* From github download a copy of the zip folder with the CalculiX mesh files [part_2.zip](https://github.com/daptablade/docs/blob/master/mynewbook/Tutorials/precice/partitioned_elastic_beam/beam/part_2.zip).
The preCICE configuration file precice-config.xml is identical to that from the previous component. 
Upload these two files under the `Parameters` tab by selecting `upload user input files`.  

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
  "dummy-in": 0
}
```

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
  "files.beam_frd": "default"
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} parameters
```{literalinclude} ./precice/partitioned_elastic_beam/beam/parameters-beam-2.json
:language: json
```
````
`````

### Post-processing

This component runs only after the coupled structure-structure interaction simulation completes.   
It joins the .frd output files from both beam simulation participants to form a new file with the entire beam.
The output can be visualised in CalculiX GraphiX as described in the [Inspect the outputs](tutorials-precice-beam-inspect-outputs) section. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `post-processing`, and select the generic python component API `generic-python3-comp:latest`. 

* Copy the contents of the `setup.py` and `compute.py` files from below into a text editor, save them locally. 
Then upload them under the `Properties` tab.

* In the `Properties` tab check the box next to the `End Node` option. 

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
  "files.beam1_frd": "default",
  "files.beam2_frd": "default"
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./precice/partitioned_elastic_beam/post-processing/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./precice/partitioned_elastic_beam/post-processing/compute.py
:language: python
```
````
`````


### PreCICE-driver

In general, preCICE participants are launched in separate processes and the coupled simulation only starts once both processes have been launched.

To replicate this approach, we define a driver component that launches the two beam components in parallel using the python [ThreadPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#threadpoolexecutor) class. 
Once both beam component compute threads complete, the driver launches the post-processing component execution. 

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `precice-driver`, and select the generic python driver API `generic-python3-driver:latest`. 

* Copy the contents of the `setup.py` and `compute.py` files from below into a text editor, save them locally. 
Then upload them under the `Properties` tab.

* In the `Properties` tab check the box next to the `Driver` option. 

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./precice/partitioned_elastic_beam/precice-driver/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./precice/partitioned_elastic_beam/precice-driver/compute.py
:language: python
```
````
`````

## Create the Connections

We can now connect the {term}`Component`s we created to ensure that outputs and inputs are passed between them as expected.

### Dummy design connection

This 'Design variable' type connection (black line) links the beam-1 component to the beam-2 component.
It exists purely to satisfy the basic workflow requirements that simulation workflows should have a single starting component and that all (non-driver) components should be connected.
In this case we choose the beam-1 component to be the start node.  

Selecting the 'dummy_output' output handle of the beam-1 component and drag a line to the 'dummy-in' input handle of the beam-2 component.
 
### File connections

We create two file connections to transfer the beam analysis output files from each beam component to the post-processing component. 

For the first connection, select the 'files.beam_frd' output handle of the beam-1 component and drag a line to the 'files.beam1_frd' input handle of the post-processing component.

Edit this {term}`Connection` by selecting it in the workspace. 
In the `Properties` tab change the {term}`Connection` Type option from the default 'Design variable' to the 'Implicit variable or file' option by selecting the corresponding radio button.

Select `Save data` to save the change and close the connection interface.
Verify that the connection line colour has become green, which indicates an 'implicit' type data connection. 

Repeat to create a similar connection from the beam-2 component. 

## Execute the workflow

We can now execute the analysis {term}`Run` by selecting the play symbol ▶ in the Run controls interface. 

Once the run has started, each component will setup one at a time. 
The setup order is arbitrary. 
Then the compute on the driver, beam-1 and beam-2 will run in simultaneously until the coupled analysis completes and the post-processing component compute starts. 

The {term}`Run` should complete once the post-processing component compute has completed.

(tutorials-precice-beam-inspect-outputs)=
## Inspect the outputs

The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 
Scroll down to the "run_output" section to see that this contains the setup and compute function output messages from all four components (including the driver) in the order of execution as shown below.

```{image} media/precice-elastic-beam-4.png
:alt: run log
:class: bg-primary mb-1
:width: 700px
:align: center
```

You can download the session data and the {term}`Run` log now by selecting `Download` from the interface controls. 

To access the analysis output, select the post-processing component, navigate to the `Log` tab and select `download files snapshot` to download a zip folder containing the component files. 
The outputs subfolder contains the consolidated CalculiX .frd output file with results from both beam components. 

Local access to CalculiX GraphiX (CGX) is required to visualise the analysis output.
Save a local copy of the following .fdb script in the same folder as the .frd file: [visualize.fbd](https://github.com/daptablade/docs/tree/preCICE/mynewbook/Tutorials/precice/partitioned_elastic_beam/post-processing/expected_output/visualize.fbd)

In a command line execute: `cgx -b visualize.fbd` to view an animation of the magnified beam deflections.

```{image} media/precice-elastic-beam-5.png
:alt: run log
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Clean-up

Delete your workflow by selecting `Open` in the interface and then select the `Delete` button for the loaded workflow. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` session data (Run log and component logs) will be permanently deleted. 
```

(tutorials-precice-beam-references)=
## References

1. [Partitioned elastic beam preCICE tutorial](https://precice.org/tutorials-partitioned-elastic-beam.html)