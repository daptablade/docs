# Chaining component analyses

# TODO: remove the setup data keys from the setup.py files and check runs

**Duration: 45 min**

In this tutorial we explore the usage of Connections to chain the execution of Components. 
The example also introduces a finite element analysis specific 'calculix-fea-comp' component API.  

```{image} media/parametric-model-1.png
:alt: chained process
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Create the Components

This example replicates the chained analyses described in Parts 1 and 2 of the [Parametric wing model series](https://youtube.com/playlist?list=PL3ZV4Vo-Sjze6-DaoPgJcIvU-uAYB7KpZ). 
We make use of python and the open source software [CalculiX GraphiX](http://www.dhondt.de/) to create a parametric finite element model of a composite wing subject to a static tip load, which is then analysed using [CalculiX CrunchiX](http://www.dhondt.de/).

We show how the previously monolithic python code can be split into discrete and potentially re-usable Components.   
This tutorial doesn't go into the details of the python code, which were previously covered in the videos and associated blog posts (see [references 1 and 2](tutorials-chaining-component-analyses-references)). 

We group the parametric model analysis processes into three distinct Components as shown in the figure below. 

```{image} media/parametric-model-2.png
:alt: chained-process-components
:class: bg-primary mb-1
:width: 700px
:align: center
```

### Parametric-model component

The parametric-model component defines a parametric three-dimensional wing geometry in python. It also outputs meshing instructions for Calculix GraphiX in the .fdb file format.  

The component Parameters include the span and chord of the wing, as well as the aerofoil wing cross-section, which is defined by uploading a CSV input file with x and y section coordinates.  

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `parametric-model`, and select the generic python component API `generic-python3-comp:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` and `naca0012.csv` files from below into a text editor, save them locally.
Then upload the first 3 files under the `Properties` tab and upload the `naca0012.csv` under the `Parameters` tab by selecting `upload user input files`. 

* In the `Properties` tab check the box next to the `Start Node` option. 

* Copy the contents of the parameters JSON object below into the `Parameters` tab text box. 

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
  "files.cgx_file": "default"
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./parametric-model/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./parametric-model/compute.py
:language: python
```
````
````{tab-item} requirements
```{literalinclude} ./parametric-model/requirements.txt
:language: text
```
````
````{tab-item} naca0012
```{literalinclude} ./parametric-model/naca0012.csv
:language: text
```
````
````{tab-item} parameters
```{literalinclude} ./parametric-model/parameters.json
:language: json
```
````
`````

### Calculix-fea component

This component first executes CalculiX GraphiX in batch mode on the .fdb file from the parametric-model component to generate the finite element model mesh file (all.msh). 
Then, the composite material shell section properties are generated in python and written to file (composite_shell.inp), before the finite element analysis (FEA) of the model is executed with CalculiX CrunchiX. 

The component outputs the mesh node deflections at the tip of the wing (FEA output file 'ccx_static_tip_shear.dat'), as well as the model mesh file and a node set definition file, which will be needed for post-processing of the FEA results in the next component.

Here we use an application-specific component API called 'calculix-fea-comp', which ensures Calculix is installed in the local compute environment. 
It also allows us to execute CalculiX from python, by importing the `execute_cgx` and `execute_fea` methods from the `calculix` module in the compute function. 
In all other respects, this API is identical to the generic python component API `generic-python3-comp`.

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `calculix-fea`, and select the component API `calculix-fea-comp:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` and `ccx_static_tip_shear.inp` files from below into a text editor, save them locally.
Then upload the first 3 files under the `Properties` tab and upload the last one under the `Parameters` tab by selecting `upload user input files`. 

* Copy the contents of the parameters JSON object below into the `Parameters` tab text box. 

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
  "files.cgx_file": "default",
  "fibre_rotation_angle.ORI_0.1": 0
}
```

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
  "files.analysis_output_file": "default",
  "files.mesh_file": "default",
  "files.nodeset_file": "default"
}
```

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./calculix-fea/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./calculix-fea/compute.py
:language: python
```
````
````{tab-item} requirements
```{literalinclude} ./calculix-fea/requirements.txt
:language: text
```
````
````{tab-item} ccx_static_tip_shear
```{literalinclude} ./calculix-fea/ccx_static_tip_shear.inp
:language: text
```
````
````{tab-item} parameters
```{literalinclude} ./calculix-fea/parameters.json
:language: json
```
````
`````

### Results processor component

The last component in the execution chain reads the FEA analysis outputs at the mesh nodes at the tip of the wing and calculates average wing tip deflections and rotations. 
This data is output as a python dictionary with six entries: the 3 deflections ("U") in global x, y and z, and the 3 rotations ("R") about x, y, z.  

Create the component:

* Right-click in the workspace and select `Add Empty Node`. Select the empty component to edit it.

* In the `Properties` tab, fill in the component name, `fea-results-processor`, and select the component API `generic-python3-comp:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

* In the `Properties` tab check the box next to the `End Node` option. 

* Copy the following JSON object into the `Inputs` tab text box:

```{code}
{
  "files.analysis_output_file": "default",
  "files.mesh_file": "default",
  "files.nodeset_file": "default"
}
```

* Copy the following JSON object into the `Outputs` tab text box:

```{code}
{
    "Ux": "default",
    "Uy": "default",
    "Uz": "default",
    "Rx": "default",
    "Ry": "default",
    "Rz": "default"
}
```

* Select `Save data` to save and close the component. 

```{note}
Remember to save the session data now by selecting `Download` from the interface controls. 
```

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./fea-results-processor/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./fea-results-processor/compute.py
:language: python
```
````
````{tab-item} requirements
```{literalinclude} ./fea-results-processor/requirements.txt
:language: text
```
````
`````

## Create the Connections

We can now connect the Components we created to ensure that outputs and inputs are passed between them as expected. A Connection is defined as a data link from a Component output handle to another Component input handle. 

### First connection 

Create a first connection by selecting the output handle of the parametric-model component and dragging a line to the 'files.cgx_file' input handle of the calculix-fea component. 
Hover the mouse pointer over a handle to see the name of the associated input or output data appear below the component.   

By default, a new connection is a 'Design variable' type connection (black line), that is not valid for transferring files (see the TODO Reference entry for details).  

Edit the Connection by selecting it in the workspace. 
In the `Properties` tab change the Connection Type option from the default 'Design variable' to the 'Implicit variable or file' option by selecting the corresponding radio button.

Select `Save data` to save the change and close the connection interface.
Verify that the connection line colour has become green, which indicates an 'implicit' type data connection. 

```{note}
By default the connection label is set to the name of the associated output handle data. 
Indeed, there is no requirement for the input and output data names to match - so we could easily connect output 'apples' to input 'oranges' if we are not careful!    
```

### More connections

In the same way, create 3 more connections between the calculix-fea component and the fea-results-processor component, linking the handles with matching data names. 

Edit all 3 connections to modify them to 'implicit' type data connections, since we are again transferring files and not design variables.

Check that all 3 components have green tick marks appearing next to the component name to indicate that they are valid. 

Save the session data now by selecting `Download` from the interface controls. 

```{note}
The four connection objects should appear under the 'connections' key in the session data file.    
```

## Execute the workflow

We can now execute the chained component analysis Run by selecting the play symbol ▶ in the Run controls interface. 

Once the run has started, each component with setup and then execute one at a time. 
The setup order is arbitrary, but the compute functions will always be executed from the 'Start Node' to the 'End Node' (see TODO Reference manual section on valid workflows).

The Run should complete once the fea-results-component compute has completed.

## Inspect the outputs

The Run log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 

Scroll down to the "run_output" section to see that this contains the compute function output messages from all three components in the order of execution as shown below. 
The last message contains the wing tip deflection and rotation data as expected.

Also inspect the `Log` tab of all 3 components and download the file snapshots to view the input, connection and output files of all components. 

Save the session data and the Run log now by selecting `Download` from the interface controls. 

```{note}
The 'connections' folder that appears in the 'files snapshot' zip folder contains any incoming connection files. This is to differentiate them from parametric and API input files in the user file storage system, where these files exist as symbolic links to the upstream component file to improve efficiency. However, the connection files are copied into the `parameters["inputs_folder_path"]` before the compute function starts.    
```

```{image} media/parametric-model-3.png
:alt: run log
:class: bg-primary mb-1
:width: 700px
:align: center
```
## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a Run. If you select to continue, then all the Run data (session data, inputs and outputs) will be permanently deleted. 
```

(tutorials-chaining-component-analyses-references)=
## References:

1. [Parametric FEM model creation with Python and CalculiX GraphiX (cgx)](https://www.dapta.com/parametric-fem-model-creation-with-python-and-calculix-graphix-cgx/)
2. [Automated FEM analysis and output processing with Python and CalculiX CrunchiX (ccx)](https://www.dapta.com/automated-fem-analysis-and-output-processing-with-python-and-calculix-crunchix-ccx/)