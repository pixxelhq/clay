# Clay Registry: Model Management System
The Clay Registry is a new component designed to streamline the management of models. It decouples model development from model execution, allowing model authors to focus on their model's logic without being concerned with the specifics of deployment or the number of execution environments


## Background and Motivation
Currently, only Pixxel models are available in the Platform marketplace. Our goal is to simplify model onboarding to the extent that individuals outside Pixxel can effortlessly introduce their own models.

Presently, all models are directly introduced to Orchestrator with various versions. Clay and Orchestrator(Model Runner/Orchestrator in Pixxel) work in tandem throughout the entire model onboarding process. Model creators require Orchestrator API access to introduce their models(Orchestrator API needs authorization headers or token). Without Orchestrator, there's no repository for storing the models. 

To address this, Clay will undergo modifications so that all model development and registration processes can occur independently of Orchestrator.

In summary:

* **Clay:** Facilitates the model lifecycle (development, running locally and  registering different versions of model).
* **Orchestrator**: Handles model execution on the platform.

## Components:
* **Clay Registry:** Introduce a registry within clay itself which will store all the models with different versions. It will be deployed as an HTTP server in development and production.

* **Model Config:** A central repository which will store the config of models across environments.It will have an CI pipeline which will build the required config for a specific environment in the same way as helm does and push the block to orchestrator.

* **Orchestrator** will store the blocks with all the required configs with different versions. 

## Key features and benefit
• Decoupled Model Development: Separates model development and registration from execution, allowing developers to work independently of Orchestrator. (You don't need to mention FRONTIER HEADERS in your model)

• __Simplified Model Onboarding__: Makes it easier for both internal and external users to introduce their models.

• __Centralized Model Storage__: Introduces a registry within Clay to store models with different versions, deployed as an HTTP server. This registry will be the source of truth for any model.

• __Model Versioning__: Supports versioning of models, allowing for easy management and rollback.

• __Standardized Model Configuration__: Uses a central repository to store model configurations across different environments. This is supported by a CI pipeline that builds configurations for specific environments.

• __Flexibility for Custom Logic__: Enables custom logic implementation on models (e.g., `depends on` fields for workflows, adding `cost_config` which is pixxel logic 
not the model logic) within Orchestrator, as it's now decoupled from model development.

## Supported commands
◦ **clay run**: Runs models inside a Docker environment.

◦ **clay build**: Builds the Docker image for the model.

◦ **clay publish**: Publishes a specific version of the model. 
This is intended to be used via GitHub CI in Pixxel. (Can't be used via local setup)

◦ **clay block list**: Lists all models with their latest version.

◦ **clay block describe {model_name}**: Lists all versions of a given model.








