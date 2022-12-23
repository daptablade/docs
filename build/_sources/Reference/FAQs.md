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

Your {term}`Run` data is saved on cloud resources managed by our cloud service provider [DigitalOcean](https://www.digitalocean.com/legal/terms-of-service-agreement). 
Although your data is password controlled, we recommend that you do not upload any sensitive data to the Dapta platform at this time.   
We may also need to access your data for support and system maintenance purposes.

## Troubleshooting

### Is it a component error?

Sometimes you will encounter bugs and execution errors related to the user-defined component code. 
In the workspace view, a component with a warning triangle signals a component error. 
You can view the error message and traceback information in the component Log. 
To resolve a component error, modify the affected component input file and upload it again. Then restart the {term}`Run`.     

### Something else is broken - what can I do?

Refresh your browser to see if this resolves the problem. Wait a few minutes between refresh attempts, as cloud processes can take some time to complete. This is particularly the case when you are starting a new {term}`Run` for the first time or clearing your session.

You can force terminate a session (stop a run and delete everything) by selecting the `Terminate` option from the `Interface Controls > ... > Run Management` Menu.  

## Contact support

You can reach our support team via email or via our website chat option. 
For bug reports, please include screenshots and other details in your message.  
We will review your support request and get back to you as soon as possible. 

* **website chat**: navigate to [www.dapta.com](https://www.dapta.com) and click the "chat" button in the bottom right of the window.   
* **email**: support@dapta.com