# The dashboard

The dashboard is a graphical web interface that allows user to create, edit, execute and inspect the outputs of an analysis {term}`Run`. 
To access your dashboard, open your web browser and navigate to [https://www.dapta.com](https://www.dapta.com). 
Then log in with your user credentials and click on the 'Dashboard' button that has appeared in the main website menu. 

```{image} media/dashboard-overview.png
:alt: dashboard-overview
:class: bg-primary mb-1
:width: 700px
:align: center
```

## Interface controls
 
**New** : Reset the workspace. Also use this to delete your session from the Cloud after completing a Run. 

**Open** : Open a saved workspace session by uploading a JSON formatted session definition file. 

**Download** : Download a JSON-formatted version of your current session (dapta_input.json) and of the current Run Log (if available).

**View Log** : View the current Run Log (is available). 

**...** : Secondary controls and useful links (this menu will evolve over time). 

## The workspace

The workspace provides a visual representation of the components and connections currently defined in your session. 

**Right-click** in the workspace to open a workspace context menu. Select the 'Add Empty Node' option to add an empty template component to the session. 

**Left-click** components or connections to edit or delete them. 

**Left-click and hold** to drag components or connections across the workspace.

**Scroll** to zoom-in or out. 

You can also use the workspace controls **+** and **-** to zoom in and out, or the **◻** to fit all components into the current view.
## Components

Components appear as boxes in the workspace. 
Select a component to edit it. 

Each component has a name that is displayed at the top of the component box in the workspace view.
A symbol appearing next to the name indicates the validity status of the component:

**?** : Pending : Some inputs are missing.

**🗸** : Valid : All necessary inputs have been defined. 

**!** : Invalid : Some inputs are erroneous. 

## Connections

There are three types of connections....

The data transferred through a Connection can be a JSON serialisable python object (this includes most python data types) or a file reference. 

## Run Controls

