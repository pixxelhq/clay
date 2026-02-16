# Clay Registry: Model Management System
The Clay Registry is a component designed to streamline the management of models. It decouples model development from model execution, allowing model authors to focus on their model's logic without being concerned with the specifics of deployment or the number of execution environments

## Supported commands
◦ **clay run**: Runs models inside a Docker environment.

◦ **clay build**: Builds the Docker image for the model.

◦ **clay publish**: Publishes a specific version of the model. 
This is intended to be used via GitHub CI in Pixxel. (Can't be used via local setup)

◦ **clay block list**: Lists all models with their latest version.

◦ **clay block describe {model_name}**: Lists all versions of a given model.








