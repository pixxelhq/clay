# Usage

To understand how to get started with Clay, we will be writing a simple model as a demonstration. Clay, is a tool that
_wraps your model_ and by definition, it is _not concerned with the internal working of your model_. In this example
too, we don't really care what the model is doing internally.

This usage guide is split into the following sections,

1. Creating your project.
2. Defining your inputs and outputs.
3. Writing and wrapping your model.
4. Defining your model spec file.
5. Uploading your model onto Orchestrator.

??? Note

    It is assumed that you have Clay installed on your system by now. If not, please visit here.

## Creating your project

For the sake of this example we will start from a fresh slate. Since this a Demo for Clay, we are going to call this
model `DemoClay`.

Before we proceed, if you are wondering why you should create your project with clay, please refer to
this [question here](faq.md#why-should-we-create-projects-with-clay).

The project would be created with the following command,

```shell
clay create project . DemoClay
```
