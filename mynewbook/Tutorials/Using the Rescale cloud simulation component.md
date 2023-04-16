# Using the Rescale cloud simulation component

[<img src="media/Dapta-Brandmark-RGB.svg" alt="dapta" width="25px" height="25px"> Load tutorial into dapta app](https://app.daptaflow.com/tutorial/9).
[<img src="media/github.svg" alt="github" width="25px" height="25px"> View files on Github](https://github.com/daptablade/docs/tree/master/mynewbook/Tutorials/rescale).

**Duration: 15 min**

Rescale is a cloud-based platform for computational engineering and R&D that offers access to [many commercial simulation software tools](https://rescale.com/platform/software-catalog/). 
This includes FEA and CFD solvers that are commonly used in industry.

In this example we demonstrate how to setup and execute a simple Rescale simulation from within a dapta analysis workflow.

The following sections will guide you through the creation of the simulation workflow starting from an empty workspace.
**Already signed-up?**
[Access your workspace here.](https://app.daptaflow.com/) 

## Prerequisites

The tutorial runs a python script in [miniconda](https://docs.conda.io/en/latest/miniconda.html) via Rescale resources. 
You will need a [Rescale](https://rescale.com/) account to execute the analysis, but no other software licenses are required. 

Although the Rescale job executes within a few seconds on a small compute node, be aware that it will use a very small amount of credit from your Rescale account.

Before you start, setup a dedicated Rescale API key following the instructions from the advanced user guide: [Using Rescale’s REST API](https://rescale.com/documentation/main/rescale-advanced-features/rest-api/).
This API key is required to authenticate your account when interacting with the Rescale API via the dapta web app. 

## Create the component

Navigate to your dapta [dashboard](https://app.daptaflow.com/Interface) and create a blank workspace by selecting `New` (if required). 

Right-click in the workspace and select `Add Empty Node`.
This creates an empty template component in your workspace. 

Select the component to edit it:

* In the `Properties` tab, fill in the component name, `rescale-comp`, and select the component API `rescale-comp:latest`. 

* Copy the contents of the `setup.py`, `compute.py`, `paraboloid.py` files from below into a text editor, save them locally.
Then upload the first 2 files under the `Properties` tab and upload the `paraboloid.py` file under the `Parameters` tab by selecting `upload user input files`. 

* Also in the `Properties` tab check the box next to the `Start Node` and `End Node` options. 

* Insert the following "job" JSON object into the `Parameters` tab text box (below the "user_input_files" entry). 

```{code}
{
  "job": {
    "API_token_name": "rescale",
    "analysis": {
      "code": "miniconda",
      "version": "4.8.4"
    },
    "archiveFilters": [
      {
        "selector": "*"
      }
    ],
    "command": "python paraboloid.py",
    "hardware": {
      "coreType": "emerald",
      "coresPerSlot": 1,
      "slots": 1,
      "walltime": 1
    },
    "name": "test"
  }
}
```

* Select `Save data` to save and close the component. 


The "job" parameter contains the standard Rescale job information:

* "analysis": a description of the analysis software by Rescale code and version number;
* "hardware": a description of the Rescale execution nodes you want to use;
* "name": a customizable job name;
* "command": a string of commands that should be executed to launch the analysis; 
* "archiveFilters": contains a list of selectors that are used to filter the analysis output files returned to the dapta interface - here we use a wildcard `"*"` to recover all analysis output files.

The value of "API_token_name" refers to the name of a dapta user secret as explained in the next section.

`````{tab-set}
````{tab-item} setup
```{literalinclude} ./rescale/setup.py
:language: python
```
````
````{tab-item} compute
```{literalinclude} ./rescale/compute.py
:language: python
```
````
````{tab-item} paraboloid
```{literalinclude} ./rescale/paraboloid.py
:language: python
```
````
`````


## Setup a user secret 

User Secrets are a secure way of saving third-party software/API tokens to your dapta user account.

In this section we create a User Secret in the dapta web app to save the Rescale API token:

* In the dapta interface controls, select the "..." button and then "User Secrets" as shown below. 
```{image} media/rescale_1.png
:alt: select user secrets from settings
:class: bg-primary mb-1
:width: 700px
:align: center
```

* Select the "+" icon to add user secret, which consists of a NAME and VALUE pair. 

* Enter "rescale" in the NAME box and the value of your Rescale API Token in the VALUE box as shown below. 
```{image} media/rescale_2.png
:alt: select user secrets from settings
:class: bg-primary mb-1
:width: 700px
:align: center
```

*  Select `Save` to save the new User Secret, then select `Close`. 

The rescale component created in the previous section can now access the token value by reference to the user secret name.

## Execute the workflow

We can now execute the {term}`Run` by selecting the play symbol ▶ in the Run controls interface. 
Once the run has started, the component will setup and then execute. 
The Run should complete within 5-10 min.

```{note}
When the dapta component is executing you can also view the job status in the Rescale web interface. 
However, do not edit the job or the files manually in Rescale, as this can cause dapta to crash.   
```

## Inspect the outputs

Select `View Log` in the interface controls to view a summary of the {term}`Run` as a nested JSON text object.

Select the rescale-comp component in the workspace to open it and then navigate to the `Log` tab.
The `Log` tab includes a `download files snapshot` link. Select this to download a zip file that contains all input and output files as they currently exist in your workspace for this component. 

The "ouputs" folder includes all analysis output files (here the unmodified paraboloid.py only), as well as the following two files:

* input_files.zip : an compressed archive that is uploaded to Rescale and contains all input files (here paraboloid.py only);  
* process_output.log : a log file that contains a list of time-stamped events and messages as shown below.

```{code}
[2023-04-12T13:48:40Z]: Launching python paraboloid.py, Working dir: /enc/udeprod_gmhfPb/work/shared.  Process output follows:
[2023-04-12T13:48:40Z]: 20230412-134840: Compute paraboloid f(x:5.0,y:5.0) = 107.0.
[2023-04-12T13:48:40Z]: Exited with code 0
```

## Clean-up

Delete your session by selecting `New` in the interface. 
It may take a minute or so for the Cloud session to be reset. 

```{warning}
You should see a warning message whenever you are about to delete a {term}`Run`. If you select to continue, then all the {term}`Run` session data (Run log and component logs) will be permanently deleted. 
```
