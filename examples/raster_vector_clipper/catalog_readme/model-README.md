<!--

Please provide a complete overview of the model, like:

- What does the model do?
- What are the satellite images used as input?
- What is the resolution of the output images?
- Are there any specific parameters or configurations that end-users would find useful?

This Markdown document will be rendered as the final description page on the frontend of the marketplace. Therefore, it's crucial to include as much relevant information as possible to assist users in making informed decisions.

INSTRUCTIONS

1. Provide model details below along with a "sample_input.png" and "sample_output.png" in
catalog_readme folder to be showcased on the platform

2. To embedd an image in "about" section use the following template
![]({{ addUrl "example.png" }})

3. Once you've written the README document, please use the following command with the Clay CLI to upload it to S3:
    - ensure you are at the root of model folder
    - run `clay upload readme -n name -v version` . The command returns a catalog_content_url
    - Update the catalog_content_url in model spec file

Fill in the details in below section
-->

---
name: Name of model
author: authorname
input-img: {{ addUrl "sample_input.png" }}
output-img: {{ addUrl "sample_output.png" }}
inputs: {input1: 'input description', input2: 'input description'}
outputs: {output1: 'output description', output2: 'output description' }
---

Provide model details here
