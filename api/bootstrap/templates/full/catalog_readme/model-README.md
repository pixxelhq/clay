<!--

# Model Description

This Markdown file is intended to provide a comprehensive description of the model that will be displayed on the marketplace. Please ensure that you include all relevant information to help users understand the model's functionality and capabilities.

## Model Overview

Please provide a complete overview of the model, like:

- What does the model do?
- What are the satellite images used as input?
- What is the resolution of the output images?
- Are there any specific parameters or configurations that end-users would find useful?

This Markdown document will be rendered as the final description page on the frontend of the marketplace. Therefore, it's crucial to include as much relevant information as possible to assist users in making informed decisions.

## Including Artifacts

If this document contains any artifacts, such as images, please place them in the "catalog_readme" folder and embed them using the "addUrl" keyword as shown below:

```markdown
This is an image ![alt text]({{ addUrl "example.png" }})

## Uploading the README
Once you've written the README document, please use the following command with the Clay CLI to upload it to S3:
-  ensure you are at the root of model folder
- run `clay upload readme` . The command returns a catalog_content_url
- Update the catalog_content_url in model spec file

Provide model description below
-->
