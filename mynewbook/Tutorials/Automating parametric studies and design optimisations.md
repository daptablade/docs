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

We will load the session file from the previous example to speed things up.

Select `Open` from the interface controls to load the JSON formatted version of our previous session (dapta_input.json). 
Alternatively, copy the object below into a text editor and save it locally, then select `Open` to load it. 
The three connected components should appear in the workspace. 

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

### Create the driver component 

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
`````

### Execute the workflow


### Inspect the outputs


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