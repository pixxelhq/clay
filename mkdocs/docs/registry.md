# Clay Registry: Block Management System
The Clay Registry is a component designed to streamline the management of blocks. It decouples block development from block execution, allowing block authors to focus on their block's logic without being concerned with the specifics of deployment or the number of execution environments

## Supported commands
◦ **clay run**: Runs blocks inside a Docker environment.

◦ **clay build**: Builds the Docker image for the block.

◦ **clay publish**: Publishes a specific version of the block.
This is intended to be used via GitHub CI in Pixxel. (Can't be used via local setup)

◦ **clay block list**: Lists all blocks with their latest version.

◦ **clay block describe {block_name}**: Lists all versions of a given block.








