# The dashboard

The dashboard is a graphical web interface that allows user to create, edit, execute and inspect the outputs of an analysis {term}`Run`. 
To access your dashboard, open a web browser and navigate to [https://www.dapta.com](https://www.dapta.com). 
Then log in with your user credentials and click on the 'Dashboard' button that has appeared in the main website menu. 

```{image} media/dashboard-overview.png
:alt: dashboard-overview
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Interface controls
 
**New** : Reset the workspace. Also use this to delete your session from the Cloud after completing a {term}`Run`. 

**Open** : Open a saved workspace session by uploading a JSON-formatted session definition file. 

**Download** : Download a JSON-formatted version of your current session and the Run Log (if available).

**View Log** : View the current Run Log (if available). 

**...** : View menu of secondary controls, useful links and new features. 

## The workspace

The workspace provides a visual representation of the {term}`Component`s and {term}`Connection`s currently defined in your session. 

**Right-click** in the workspace to open a workspace context menu. Select the 'Add Empty Node' option to add an empty template {term}`Component` to the session. 

**Left-click** {term}`Component`s or {term}`Connection`s to edit or delete them. 

**Left-click and hold** to drag {term}`Component`s or {term}`Connection`s across the workspace.

**Scroll** to zoom-in or out. 

Select the workspace controls **+** and **-** to zoom in and out, or the **◻** to fit all {term}`Component`s into the current view.
## Components

{term}`Component`s are defined as calculation blocks that appear as boxes in the workspace. 
Select a {term}`Component` to edit it. 

Each {term}`Component` has a name that is displayed at the top of the {term}`Component` box in the workspace view.
A symbol appearing next to the name indicates the validity status of the {term}`Component`:

**?** : Pending : Some inputs are missing.

**🗸** : Valid : All necessary inputs have been defined. 

**!** : Invalid : Some inputs are erroneous. 

## Connections

A {term}`Connection` is defined as a data link from an origin {term}`Component` output handle (right side handle) to a target {term}`Component` input handle (left side handle).
There are three types of {term}`Connection`s:

**Design variable connection** : transfer design variable values (numbers or arrays of numbers only) between {term}`Component`s. 
They appear as **black** arrows in the workspace view.
Updated variables are transferred after every origin {term}`Component` calculation iteration.
This is the default {term}`Connection` type.

**Implicit variable or file connection** : transfer implicit variables (any JSON serialisable object) or files between {term}`Component`s. 
They appear as **green** arrows in the workspace view.
Updated variables are transferred after every origin {term}`Component` calculation iteration.
This is the default {term}`Connection` type for file {term}`Connection`s.

**Setup variable or file connection** :  transfer setup variables (any JSON serialisable object) or files between {term}`Component`s.
They appear as **blue** arrows in the workspace view.
Updated variables are transferred only once after all {term}`Component`s completed setup and before the first compute of the connection target {term}`Component`.

The data transferred through {term}`Connection`s has to be a JSON serialisable python object (this includes most python data types) or a file reference. 
File reference keys start with the prefix "files." .

### Valid Connections

The compute functions will always be executed in order from a single 'Start Node' to a single 'End Node'. 
This means that a 'Start Node' may not have any incoming connections, and an 'End Node' may not have any outgoing connections. 
Driver components cannot have any connections. 

## Run Controls

**▶** / **Play**: Launch a new {term}`Run`. This option only becomes available once all {term}`Component`s are valid. 

**⏸** / **Pause** : Pause a {term}`Run`. This option only becomes available once a {term}`Run` has been started. Execution can be continued by selecting the play ▶ button.

**⏹** / **Stop**: Stop a {term}`Run`. This option only becomes available once a {term}`Run` has been started. This terminates the current {term}`Run` and may result in an error message.  

