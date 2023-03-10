# Using OpenVSP for aircraft performance analysis

```{image} media/paraboloid_rotation.gif
:alt: paraboloid-surface
:class: bg-primary mb-1
:width: 400px
:align: right
```

**Duration: 60 min**




**>> The files for this tutorial are now on [Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/parametric-plate-buckling).**


## Simulation workflow overview

In this example we create a simple aircraft performance analysis workflow using [OpenVSP]() and [OpenMDAO](). 

The OpenVSP aircraft model (Cessna-210_metric.vsp3) is representative of a Cessna 210 as shown below. 
It is suitable for vortex lattice method (VLM) aero analysis using the VSPAERO solver that comes with OpenVSP.
The model is in SI units (m/s/kg). 
Only the wing and the horizontal tailplane (HTP) are modelled in the VLM analysis.
Local installation of OpenVSP is required view the model and execute VSPAERO on your machine - see installation instructions on the OpenVSP website. 

```{image} media/parametric-model-1.png
:alt: vsp3 model of a Cessna 210
:class: bg-primary mb-1
:width: 700px
:align: center
```

In this example, we wish to plot the aircraft's lift to drag ratio (L/D) with respect to cruise velocity (`Vinfinity`) to graphically determine the aircraft's optimal cruise velocity for a range of different wing aspect ratios. 
Indeed, theory tells us that the optimal cruise velocity occurs where L/D is maximised, which also corresponds to flight velocity where the total drag (including lift-induced drag) is minimised.

To plot L/D we need to be able to perform multiple trimmed aircraft analyses for different cruise velocities and wing aspect ratios. 
The aircraft is trimmed in level flight when all forces and moments about the aircraft's centre of gravity (CG) cancel out. 

Unfortunately, VSPAERO only does part of the job for us.
It allows us to calculate the aircraft's lift and the drag, but it won't adjust the aircraft pitch angle (AoA) or the HTP angle to balance the aero forces and moments out with the aircraft's weight (let's assume that thrust can be set to cancel out drag). 

To solve this problem we can add a trim component to our simulation workflow as shown in the next figure. The trim component introduces a feedback cycle that adjusts the trim variables (AoA and HTP angles) based on the forces and moments at the aircraft's CG. 
We can then use Newton's method to converge the cycle to a trimmed solution.

In this example, we again choose to use OpenMDAO as the driver for our workflow for 3 main reasons: 
 1. It allows us to easily implement the trim analysis cycle by using an 'implicit' component and variable promotion (where normal dapta design variable connections can only go forwards).
 2. It includes a nonlinear solvers, including a [Newton solver](https://openmdao.org/newdocs/versions/latest/features/building_blocks/solvers/newton.html) to converge the trim cycle.
 3. It allows us to set up a design of experiments analysis to iteratively solve the trim problem for different flight conditions and aircraft designs.

```{image} media/parametric-model-1.png
:alt: trim analysis cycle
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Create the components


## Automating the design study



## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` data (session data, inputs and outputs) will be permanently deleted. 
```

(tutorials-Modelling-variable-stiffness-composite-plates-references)=
## References
