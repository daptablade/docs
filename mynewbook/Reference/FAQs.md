# FAQs


## Which browser should I use?

We recommend using [Chrome](https://www.google.com/chrome/) v.108 or later.

## How big a job can I run?

Current maximum user resource limits for the trial version are:

* **5 components** including a driver.
* **1 Giga byte (Gi) Memory** per component 
* **1 CPU** per component
* **1 Mega byte (Mi)** storage per uploaded file
* **5 user input files** per component (not including API files)
* **24 hours** per {term}`Run` 

You may encounter component resource error messages when these limits are exceeded. 

## Who can see my data?

Your {term}`Run` data is saved on shared cloud resources managed by our cloud service provider [DigitalOcean](https://www.digitalocean.com/legal/terms-of-service-agreement). 
Although your data is password controlled, we recommend that you do not upload any sensitive data to the Dapta platform at this time.   
We may also need to access your data for support and system maintenance purposes.

## What software can I run in a component?

The following table provides an overview of currently available software APIs. 
[Contact support](../Support.md) to get your own OS or commercial software tools added to the list.  

| API name                 | Github folder            | Software available |
| --------                 | ---------                | ---------                    |
| calculix-fea-comp        | [generic-python3-comp](https://github.com/daptablade/generic-python3-comp) | Python 3.8, Calculix GraphiX (cgx_2.20), Calculix CrunchiX (ccx_2.20)| 
| generic-python3-comp     | [generic-python3-comp](https://github.com/daptablade/generic-python3-comp) | Python 3.8 only|
| generic-python3-driver    | [generic-python3-comp](https://github.com/daptablade/generic-python3-comp) | Python 3.8 only|

## What python packages can I use?

Current package lists:
[Python 3.8 packages](Packages%20list%20for%20python%203.8.md)

## Troubleshooting

### Is it a component error?

Sometimes you will encounter bugs and execution errors related to the user-defined component code. 
In the workspace view, a component with a warning triangle signals a component error. 
You can view the error message and traceback information in the component Log. 
To resolve a component error, modify the affected component input file and upload it again. Then restart the {term}`Run`.     

### Something else is broken - what can I do?

Refresh your browser to see if this resolves the problem. Wait a few minutes between refresh attempts, as cloud processes can take some time to complete. This is particularly the case when you are starting a new {term}`Run` for the first time or clearing your session.

You can force terminate a session (stop a run and delete everything) by selecting the `Terminate` option from the `Interface Controls > ... > Run Management` Menu.  

### Ask for help

Check our [support](../Support.md) options. 