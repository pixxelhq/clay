<!--

Please provide a complete overview of the model, like:

- What does the model do?
- What are the inputs and outputs?
- Are there any specific parameters or configurations that end-users would find useful?

This Markdown document will be rendered as the description page on the marketplace.
Include as much relevant information as possible to help users make informed decisions.

INSTRUCTIONS

1. Provide model details below along with a "sample_input.png" and "sample_output.png" in
   the docs/ folder to be showcased on the platform.

2. To embed an image use the following template:
   ![]({{ addUrl "example.png" }})

3. Once you've written this document, upload it with the Clay CLI:
   - Ensure you are at the root of your model folder
   - Run: clay block assets upload ./docs --name <name> --bucket <bucket> --region <region> --readme
   - The command returns a URL. Update the catalog_content_url in your model spec file.

Fill in the details in the section below.
-->

---
name: Name of model
author: authorname
input-img: {{ addUrl "sample_input.png" }}
output-img: {{ addUrl "sample_output.png" }}
inputs: {input1: 'input description', input2: 'input description'}
outputs: {output1: 'output description', output2: 'output description'}
---

Provide model details here.
