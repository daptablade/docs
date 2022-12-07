# Simple component analysis

In this example we explore the creation and analysis of a simple analytical function component.
If you are familiar with openMDAO, you may want to compare this example with the ['Paraboloid - A Single-Discipline Model'](https://openmdao.org/newdocs/versions/latest/basic_user_guide/single_disciplinary_optimization/first_analysis.html) example from the openMDAO user guide.


## Component description 
The paraboloid component solves the function

$$
  f(x,y) = (x-3.0)^2 + x y + (y + 4.0)^2 -3.0 
$$

where x and y are the component inputs and f(x,y) is the output. 
The minimum of this function is located at

$$
  x = \frac{20}{3} \quad , \quad y = -\frac{22}{3}
$$

## Create the component in the web interface

Navigate to the [dashboard](https://app.daptaflow.com/Interface) and create a blank workspace by selecting `New` (if required). 

Right-click in the workspace and select `Add Empty Node`.
This creates an empty template component in your workspace. 

Select the component to edit it. 

### Properties

The component interface opens on the Properties tab. This is where you define the core properties of your component.
Fill in a component name, `paraboloid`, and select the `generic-python3-comp:latest` component API. 

Press the tab key or click within the component interface to validate the selected API. This triggers the display of a list of API input files, as shown below.

```{image} media/paraboloid_1.png
:alt: paraboloid_1
:class: bg-primary mb-1
:width: 400px
:align: center
```

```{note}
Component Names should only contain lower case letters a-z, numbers 0-9 and dash (-), without spaces. 
```

```{warning}
Clicking outside the component interface closes the component without saving changes. 
```

We can see that the `generic-python3-comp` API has three input files: 

* `setup.py`
* `compute.py`
* `requirements.txt`

The first two files are required and the last one is optional. You can download the paraboloid example `setup.py` and `compute.py` files below. 
The `requirements.txt` file is optional and allows the setup and compute modules to access to a selection of third party python libraries (via Pypi). 

````{tab-set-code}

```{literalinclude} ./paraboloid/setup.py
:language: python
```

```{literalinclude} ./paraboloid/setup.py
:language: python
```

````

Next, select `setup.py` in the component interface to upload the corresponding file. Green ticks and file upload time stamps should appear to confirm the upload was successful. Repeat for the `compute.py` file.  

Leave the Options empty ({}) and check the boxes next to the `Start Node` and `End Node` options (since this run will only contain this one component), as shown below. 

Finally, select `Save data` to save the component and close the component interface.

```{image} media/paraboloid_2.png
:alt: paraboloid_1
:class: bg-primary mb-1
:width: 400px
:align: center
```

```{warning}
Although you have just 'saved' the component, the contents of your workspace have not actually been saved anywhere and you would lose your work if you refreshed the webpage or closed the web browser now. To avoid this situation you should save your edited components regularly and then select the workspace `Download` button to save an a JSON formatted version of your session (see the related sections in the User Manual). 
```

### Parameters

In your work space, the component name should have updated and a green tick should appear next to it to indicate that the component is apparently valid. However, if you tried to run it, you would get error messages as we haven't actually defined the python function inputs yet. 

We define Parameters as values that the component needs to execute, but that are not design inputs as such. For example, parameters could be constant values or application related input files. For this paraboloid example, we use the `Parameters` tab to define some default component input and output values, which are used to initialise the component in the setup function. For a more comprehensive use of Parameters see the example [Chaining component analyses](./Chaining%20component%20analyses.md). 

### Inputs

### Outputs

We can ignore the Log tab for now, we will look at it again in the next section. 
Select `Save data` to save the component and close it. 



