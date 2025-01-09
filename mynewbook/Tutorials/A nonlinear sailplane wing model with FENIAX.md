# A nonlinear sailplane wing model with FENIAX

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/12).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/sailplane-feniax).

**Duration: 10 min**

This example replicates the [sailplane example](https://github.com/ostodieck/FENIAX/blob/master/docs/documentation/examples/SailPlane/sailplane_nb.md) from the FENIAX repository and demonstrates the ability to modify analysis parameters and export outputs automatically through the dapta interface.

Note: This component uses python 3.12 - for details of the software available in this component see [FAQS - What software can I run in a component?](https://daptadocs.com/Reference/FAQs.html#what-software-can-i-run-in-a-component)

```{image} media/sailplane-feniax-1.png
:alt: sailplane wing deflections
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Component description
There is a single FENIAX component in this example. In future examples, we will connect FENIAX components to other components.

The static equilibrium of the aircraft under prescribed loads is first studied with follower loads normal to the wing applied at the tip of each wing (nodes 25 and 48). 

The response for an increasing load stepping of 200, 300, 400, 480 and 530 KN is computed and compared to reference NASTRAN linear and nonlinear solutions.

Then a convergence analysis with the number of modes in the solution is performed.

Component inputs are the number of modes used for the convergence study. 
The output is the array of wing z-deflections for the 530 KN load case (in addition to the zip file of the output folder structure from FENIAX).

## Create the component

Navigate to the [dashboard](https://app.daptaflow.com/Interface) and create a blank workspace by selecting `New` (if required). 

Right-click in the workspace and select `Add Empty Node`.
This creates an empty template component in your workspace. 

Select the component to edit it. 

### Properties

The component interface opens on the Properties tab. This is where you define the core properties of your component.
Fill in a component name, `sailplane-feniax`, and select the `feniax-comp:latest` component API. 

Press the tab key or click within the component interface to validate the selected API. This triggers the display of a list of API input files, as shown below.

```{image} media/feniax_1.png
:alt: properties-tab-empty
:class: bg-primary mb-1
:width: 700px
:align: center
```

```{note}
{term}`Component` Names should only contain lower case letters a-z, numbers 0-9 and dash (-), without spaces. 
```

```{warning}
Clicking outside the component interface closes the component without saving changes. 
```

We can see that the `feniax-comp` API has three input files: 

* `setup.py`
* `compute.py`
* `requirements.txt`

The first two files are required and the last one is optional. You can inspect the sailplane example file contents below. 
The `requirements.txt` file is not required here as the python code doesn't import any third-party python packages.   

The `setup.py` module has to include a **setup** function that returns data that will be available to the compute function. Here we set the type (integer) for the number of modes inputs. 

The `compute.py` module has to include a **compute** function that returns a dictionary of data, which includes the component outputs dictionary.

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./sailplane-feniax/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./sailplane-feniax/compute.py
:language: python
```
````
`````

For each file, copy the contents above into a text editor and save it locally. Make sure you include the '.py' extension in the file name.

Next, select `setup.py` in the component interface to upload the corresponding file. A green tick and a file upload time stamp should appear to confirm that the upload was successful. Repeat for the `compute.py` file.  

Check the boxes next to the `Start Node` and `End Node` options (since we only have one component in this {term}`Run`), as shown below. 

```{image} media/feniax_2.png
:alt: properties-tab-completed
:class: bg-primary mb-1
:width: 700px
:align: center
```

Finally, select `Save data` to save the component and close the component interface. 

In your work space, the component name should have updated and a green tick should appear next to it to indicate that the component is apparently valid. 
However, if you tried to run it now, you would get error messages as we haven't actually defined the python function Parameters and Inputs yet - see below. 

```{note}
Click the "Save" button in the top toolbar to save your workspace. 
```

### Parameters

Select the component again to edit it, then select the `Parameters` tab and copy the following JSON object into the text box. Select `Save data` to save the edits. 

```{code}
{
    {
        "SP1": 5,
        "SP2": 15,
        "SP3": 30,
        "SP4": 50,
        "SP5": 100
    },
    "user_input_files": []
}
```

We define Parameters as values that the component needs to execute, but that are not Inputs from other {term}`Component`s. 
For example, Parameters could be constant values or application related input files. For this example, we use the `Parameters` tab to define some default component input values, which are used to initialise the component in the compute function. For a more comprehensive use of Parameters see the example [Chaining component analyses](./Chaining%20component%20analyses.md). 

### Inputs and Outputs

Open the component to edit it and add the following JSON objects into the text boxes in the `Inputs` and `Outputs` tabs.
By defining {term}`Component` Inputs and Outputs respectively, we can expose these values to other {term}`Run` components, such as drivers. 
We have explored this in the [Simple optimisation problem](./Simple%20optimisation%20problem.md) tutorial.  

Input Handles:
```{code}
{
    "number_of_modes.SP1": 10,
    "number_of_modes.SP2": 20
}
```

Output Handles:
```{code}
{
  "deflection_output": 0
}
```

We will look at the `Log` tab in the next section. 

Select `Save data` to save the component and close it. You should now be able to see some input and output handles appear on the left and right of the component in the workspace. Hover over the handles with your mouse cursor to view the names of the variables. 

## Component analysis 

All being well, you should now be able to launch a {term}`Run` by selecting the play symbol ▶ in the {term}`Run` controls interface. 
The control symbols will start to fade in and out as your {term}`Run` is sent for analysis in the Cloud, this may take a few minutes the first time. 
Eventually, the {term}`Run` should execute, after which you should see an alert window confirming that 'The {term}`Run` has completed successfully'. 
If you don't get any messages, try to refresh your web browser page, or consult the [FAQ](../Reference/FAQs.md) section for troubleshooting suggestions. 

We can now inspect the outputs of the {term}`Run`. 

### The Run Log

Select `View Log` in the interface controls to view a summary of the {term}`Run` as a nested JSON text object. 

The 'time' entry corresponds to the time at which the Run Log file was generated, while the time stamps in the messages that appear in the 'run_output' and 'sailplane-feniax' relate to the setup and compute execution times. The inputs and outputs of the sailplane-feniax component are available under the corresponding 'sailplane-feniax' entries.   

To save a copy of the Run Log, select `Close` to return to the workspace view and then select `Download`. This should download two JSON files: the Run Log as 'runlog.json' and the copy of your work session as 'dapta_input.json'. 

### The Component Log

Select the component again and navigate to the `Log` tab. 

Both the Run Log and the Component Log are updated as the {term}`Run` executes, which allows us to monitor progress and view intermediary results.
The Component Log lists events related to the component in order of time of occurrence. A 'SETUP' event corresponds to the execution of the component's setup function and a 'COMPUTE' event corresponds to the execution of the compute function, as defined in the `setup.py` and `compute.py` modules. The event name is followed by a number, that indicates the number of times the component has been executed during the current {term}`Run`. Note that the Component Log is not cleared between successive Runs, but it will clear if you refresh the page. 

The Component Log has another important function: if errors occur during the execution of the component, the Log will list an 'ERROR' event with a description of the error message and traceback information.  

The `Log` tab also includes a `download files snapshot` link. Select this to download a zip file that contains all input and output files as they currently exist in your workspace for this component. 
Save this data, along with the JSON formatted version of your session ('dapta_input.json') and a copy of the {term}`Run` Log ('runlog.json'), to allow you to re-load this example in the future, or to compare inputs and outputs with other Runs. 


## Clean-up

You can delete a session by creating a new session (select `New` in from the interface controls) or by loading a JSON session file from your machine (select `Open`). 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` session data (Run log and component logs) will be permanently deleted. 
```

## References

[FENIAX Sailplane Example](https://github.com/ostodieck/FENIAX/blob/master/docs/documentation/examples/SailPlane/sailplane_nb.md) 