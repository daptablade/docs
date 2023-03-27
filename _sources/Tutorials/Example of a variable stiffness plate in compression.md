# Example of a variable stiffness plate in compression

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/7).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/parametric-plate-buckling).

**Duration: 60 min**

We optimise the design of a variable stiffness RTS composite plate in compression.
We use CalculiX to model the plate and analyse the buckling behaviour, and OpenMDAO to minimise the mass of the plate, subject to a minimum buckling load constraint.

This example is based on [Reference 1](tutorials-Modelling-variable-stiffness-composite-plates-references) and results are compared to the reference data showing a good correlation. 

```{image} media/parametric-plate-buckling-rts_1.png
:alt: Buckling of an rts plate - mode 1
:class: bg-primary mb-1
:width: 500px
:align: center
```
## Model overview

### Variable stiffness RTS composites

With steered-fibre composites (also called variable-stiffness composites), engineers have the option to change the fibre directions within each ply, as well as stacking plies with different fibre orientations through the laminate thickness. 

The use of steered-fibre composites opens-up the design space and has been shown to lead to lighter, more efficient designs in a number of applications, for example, by steering fibres around holes or cut-outs in complex parts [[2]](tutorials-Modelling-variable-stiffness-composite-plates-references). 
By steering the fibres, the number of stacked plies and their surface area can be optimised for structural efficiency, which leads to lighter designs. 
The use of fewer plies and the increased control over ply shapes has another benefit: it could speed-up the manufacturing process and reduce material wastage.

Rapid tow shearing (RTS) is a new patented manufacturing method for steered-fibre composites that is being developed by iCOMAT (icomat.co.uk). 
One of the main benefits of RTS is that the fibres can be steered to a tight radius (50mm), without generating fibre wrinkling, gaps or overlaps, which are defects that can significantly compromise the structural performance. 
This is a key advantage compared to other steering methods, such as ATL, AFP or TFP. 

With RTS the thickness of the ply changes as a function of the steering angle (or more precisely “shearing”-angle) as shown in the figure below. This means that thickened laminate regions can be introduced purely by locally shearing the fibres, potentially removing the need to add plies near joints or other high stress areas. 

```{image} media/parametric-plate-buckling-rts_2.png
:alt: rts composites link thickness and steering angle
:class: bg-primary mb-1
:width: 400px
:align: center
```

### Modelling approach in Calculix

Our objective is to optimise an RTS composite plate design for minimum mass, subject to a minimum buckling load constraint and to compare our results with data from [Reference 1](tutorials-Modelling-variable-stiffness-composite-plates-references). 
We reduce the size of the optimisation problem compared to Reference 1 by using a fixed composite ply stacking sequence and only optimising the outer RTS ply steering angles.

We create a parametric Calculix finite element model of the plate to perform a linear eigenvalue buckling analysis.
This type of analysis can be used to estimate the critical (bifurcation) loads of “stiff” structures. 

#### Modelling the boundary conditions

The rectangular plate (250x750mm) described in the reference is simply supported on all edges and loaded in the x-direction as shown below. 
In the reference, the analytical boundary conditions are applied directly at the laminate neutral plane, the location of which is a function of the laminate properties. 
There is normally no requirement for element nodes to coincide with the laminate neutral plane. 
Therefore, it may be difficult to reproduce these boundary conditions in a finite element model - particularly with shell elements. 
Instead we will be using a 5x larger model (750mmx1250mm) and boundary conditions shown in the second figure. 
This allows us to model boundary conditions on the 250x750mm inner plate that closely resemble simply supported conditions.  

```{note}
For a constant stiffness panel, we could have reduced the size of the model by assuming symmetric boundary conditions in the x and y directions.
However, the plate's stiffness distributions here are not necessarily symmetric depending on the control point locations and fibre angle values.   
```

```{image} media/parametric-plate-buckling-rts_3.png
:alt: reference boundary conditions
:class: bg-primary mb-1
:width: 400px
:align: center
```
```{image} media/parametric-plate-buckling-rts_4.png
:alt: new boundary conditions
:class: bg-primary mb-1
:width: 400px
:align: center
```

#### Modelling the applied compression load

The compression load (750kN) shown in the second figure is the target load below which the panel should not buckle. 
The compression load is applied to the model via a kinematic coupling (using the *KINEMATIC keyword), which distributes the load to the edge nodes and ensures that the edge remains straight.
A second kinematic coupling is applied to the top edge of the plate to keep it straight, whilst allowing nodes to slide in the x and y directions.   

```{warning}
We actually apply a lower load (10kN) to the model in Calculix Crunchix and constraint the minimum buckling factor to 75.0 in the OpenMDAO driver parameters. 
This ensures that the compression load applied to the model is always lower than the expected buckling load factor during the design optimisation iterations, without which the solver may return erroneous buckling load factors. We also request the first 10 buckling modes as an output with the *BUCKLE keyword, to ensure that the lowest mode is calculated with sufficient accuracy.    
```


#### Defining the design variables

The design variables for the RTS panel are the outer ply shearing angles T0 and T1, which are defined at 7 equally spaced control points in the 90 degree ply reference direction (model y-direction) as shown in the next figure.
The location of the control points is also a variable in the component parameters, but we will not change these positions in this example.

For example, by defining angles of 0 and 69 degrees at T0 and T1 respectively, we can now model the fibre paths shown below in green and orange for the +/- RTS plies. 
Note that the plate lower surface is flat, so that the thickness variation shown below due to the fibre shearing is only visible on the upper surface.   

```{image} media/parametric-plate-buckling-rts_5.png
:alt: control points
:class: bg-primary mb-1
:width: 400px
:align: center
```
```{image} media/parametric-plate-buckling-rts_5_1.png
:alt: fibre paths example
:class: bg-primary mb-1
:width: 300px
:align: center
```
```{image} media/parametric-plate-buckling-rts_5_2.png
:alt: thickness distribution
:class: bg-primary mb-1
:width: 350px
:align: center
```
    

#### Choosing the element type 

We choose to model the plate directly with solid C3D20R elements, as the alternative of using S8R shell elements with varying thicknesses in CalculiX would introduce undesired rigid body constraints at element interfaces [[3]](tutorials-Modelling-variable-stiffness-composite-plates-references).
To reduce the number of elements through the thickness of the plate, we also choose to calculate homogenised material properties for +/- plies, so that the optimal 28-ply RTS laminate design $[(90 \pm \langle 0|69 \rangle)_4 / 90 \pm \langle 0|67 \rangle / \pm 80 / 90_2]_s$  from Reference 1 can be approximated with only 3 element layers consisting of the following sub-laminates: $[(90 \pm \langle 0|69 \rangle)_5]$, $[90_8]$ and $[(90 \pm \langle 0|69 \rangle)_5]$.

## Automating the design optimisation

### Load a workflow from file

Copy the JSON object below into a text editor and save it locally, then select `Open` to load it. 
Two components should appear in the workspace. 
Since the second component is a driver we do not define any connections between components in this workflow. 

````{dropdown} dapta_input.json
```{literalinclude} ./parametric-plate-buckling/dapta_input_RTS28.json   
:language: json
```
````

The question marks next to the component names indicate that they are missing some data. 
To fully define them, we need to upload all the components' `setup.py`, `compute.py`, `requirements.txt` and user input files, as described in the next sections. 

### Update the plate component

The parametric plate component performs 3 main tasks:

1. It creates a set of analysis input files from the component parameters and design variable inputs;
2. It executes a CalculiX CrunchiX finite element analysis;
3. It then reads the analysis outputs and returns the model mass and buckling load factors as component outputs.

To achieve the first task, we first use CalculiX GraphiX to create the plate 2D geometry and mesh this using second order S8 elements. 
This 2D mesh is then used to extrude solid elements for each composite ply.
The extrusion thickness at each node is calculated from the local RTS shearing angle, which is linearly interpolated from the two closest control point values (determined by projecting the node onto the line of control points).  

Note that this analysis workflow could be generalised by splitting it up into 3 components, one for each task. 

To update the parametric plate component:

* Select the component in the workspace to edit it.

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

* Copy the contents of the `ccx_compression_buckle.inp` file from below into a text editor and save it locally. 
Then upload it under the `Parameters` tab by selecting `upload user input files`.
The other parameters, inputs and outputs should have been pre-populated by loading the session file in the previous section. 

* Select `Save data` to save and close the component. 

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./parametric-plate-buckling/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./parametric-plate-buckling/compute.py
:language: python
```
````
````{tab-item} requirements
```{literalinclude} ./parametric-plate-buckling/requirements.txt
:language: text
```
````
````{tab-item} ccx_compression_buckle.inp
```{literalinclude} ./parametric-plate-buckling/ccx_compression_buckle.inp
:language: python
```
````
`````

### Update the driver component

The driver component is identical to the OpenMDAO optimisation component used in the [Simple optimisation problem](./Simple%20optimisation%20problem.md) example, except for the driver parameters, which have been adjusted for the plate optimisation problem:

* The "input_variables" and "output_variables" parameters set the optimisation variables, objective and constraint functions.
* The calculation of total derivatives across the chained components (using finite differencing) is requested by setting `"approx_totals": true` and `"fd_step": 0.2` in the driver parameters.
* Optimisation iteration history plots are requested by adding the "plot_history" option into the "visualise" parameter list.   

To create the driver component:

* Select the open-mdao component to edit it.

* Copy the contents of the `setup.py`, `compute.py`, `requirements.txt` files from below into a text editor, save them locally.
Then upload them under the `Properties` tab. 

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
````{tab-item} om_component.py
```{literalinclude} ./open-mdao-paraboloid/om_component.py
:language: python
```
````
`````

### Execute the workflow

We can now execute the design optimisation by selecting the play symbol ▶ in the Run controls interface. 

The {term}`Run` should complete after approximately 57 iterations of the parametric-plate-buckling component (1 iteration of the `open-mdao` component). 
Since each component execution takes just under a minute to complete (of which ~40s are allocated to the actual CalculiX CrunchiX finite element analysis), the design optimisation task should complete within 50min.

### Inspect results

#### Run log
The {term}`Run` log summarises the output of the components. Open the log by selecting `View Log` in the interface controls. 
The "run_output" entry (at the end of the log) should state that the "OpenMDAO compute completed".  

#### Plate component analysis outputs 

Next, close the {term}`Run` log and select the `parametric-plate-buckling` component.
Then select the `Log` tab and click on `download files snapshot`.

The zip file includes an 'outputs' folder that contains the outputs of the `compute.py` script and the CalculiX CrunchiX input and output files. 

Open the 'run.log' file in a text editor to view the standard python command-line output. This includes any log statement output with the `print()` function, as well as function execution times captures with the `timeit()` decorator. 

Open the 'ccx_compression_buckle.dat' file in a text editor to view a list of the lowest 10 buckling factors.
View the buckling mode shapes by opening the 'ccx_compression_buckle.frd' file in a CalculiX compatible post-processor, such as CalculiX GraphiX.
The lowest mode shape should look similar to the one shown in the figure at the top of this tutorial.

````{dropdown} run.log
```{literalinclude} ./parametric-plate-buckling/run.log   
```
````
````{dropdown} ccx_compression_buckle.dat
```{literalinclude} ./parametric-plate-buckling/ccx_compression_buckle.dat  
```
````

#### Optimisation driver outputs 

Next, close the plate component and select the `open-mdao` component.
Then select the `Log` tab and click on `download files snapshot`.

The optimisation study outputs are summarised at the end of the 'run_driver.log' file in the 'outputs' folder, as shown below.
We can also inspect the convergence history plots of the design variables, objective and constraint functions in the same folder.

```{code}
Driver debug print for iter coord: rank0:ScipyOptimize_SLSQP|28
---------------------------------------------------------------
Design Vars
{'parametric_plate_buckling.T0': array([4.63764166]),
 'parametric_plate_buckling.T1': array([68.21746728])}

Calling compute.
message: 
 {'component': 'parametric-plate-buckling', 'inputs': {'design': {'T1': [68.21746728435265], 'T0': [4.637641660750407]}}, 'get_grads': False, 'get_outputs': True}
Nonlinear constraints
{'parametric_plate_buckling.buckling_factors': array([75.00001])}

Linear constraints
None

Objectives
{'parametric_plate_buckling.mass': array([6.76051059])}

Optimization terminated successfully    (Exit mode 0)
            Current function value: 6.76051059005866
            Iterations: 16
            Function evaluations: 28
            Gradient evaluations: 16
Optimization Complete
-----------------------------------
```

```{image} media/parametric-plate-buckling-rts_6.png
:alt: parametric_plate_buckling.T0
:class: bg-primary mb-1
:width: 350px
:align: left
```
```{image} media/parametric-plate-buckling-rts_7.png
:alt: parametric_plate_buckling.T1
:class: bg-primary mb-1
:width: 350px
:align: right
```
```{image} media/parametric-plate-buckling-rts_8.png
:alt: parametric_plate_buckling.mass
:class: bg-primary mb-1
:width: 350px
:align: left
```
```{image} media/parametric-plate-buckling-rts_9.png
:alt: parametric_plate_buckling.buckling_factor
:class: bg-primary mb-1
:width: 350px
:align: right
```

The control point fibre shearing angles converge after 16 SLSQP algorithm iterations to T0=5 and T1=68 degrees.
 
The mass and buckling load results are compared with the optimal design from Reference 1 below, showing a good correlation. 

```{list-table}
:header-rows: 1

* - Value
  - Reference 1
  - Present study
  - Relative Error
* - Mass (g)
  - 1321
  - 1352
  - 2 %
* - Buckling load (kN) 
  - 750
  - 750
  - 0 %
```

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` data (session data, inputs and outputs) will be permanently deleted. 
```

(tutorials-Modelling-variable-stiffness-composite-plates-references)=
## References

1. Rainer M. Groh and Paul Weaver. "Mass Optimisation of Variable Angle Tow, Variable Thickness Panels with Static Failure and Buckling Constraints," AIAA 2015-0452. 56th AIAA/ASCE/AHS/ASC Structures, Structural Dynamics, and Materials Conference. January 2015, url: https://doi.org/10.2514/6.2015-0452 

2. C.S. Lopes, Z. Gürdal, P.P. Camanho, "Tailoring for strength of composite steered-fibre panels with cutouts", Composites Part A: Applied Science and Manufacturing, Volume 41, Issue 12, 2010, Pages 1760-176, url: https://doi.org/10.1016/j.compositesa.2010.08.011

3. Guido Dhondt, "CalculiX CrunchiX USER’S MANUAL version 2.20", July 31, 2022, url: http://www.dhondt.de/ccx_2.20.pdf 
