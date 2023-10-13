# Clay - Package models for deployment

## What is `Clay` ?

`Clay` is a framework to help you package your models in a standardised format that the rest of Pixxel’s infrastructure can understand and make use of.

Clay lets you focus on defining your model, and abstracts away **all the engineering** required to:

* **Deploy** it on Pixxel’s infrastructure
* Let other services **discover** your model
* Communicate the `inputs` and `outputs` of your model to let the front-end and other services automatically determine how to:
  * **Use** or **call** your model in exactly the way you specify
  * Understand and render it’s `outputs` in a way that users can benefit from
* Guarantee a certain amount of compute that your model will always get during runtime
* Build docker images / containers for your model

In other words, `Clay` separates the model development cycle in 2 stages:

* First, **you build the model** and write all the model specific code using whatever frameworks and libraries that you are comfortable with.
* Next, you merely **describe**, or rather, **declare** the deployment of the model, and `clay` takes care of the **how**. You do that in a very simple configuration file where you mention things like:
  * The compute requirements of the model.
  * The environment it will need to run.
  * The inputs it will take, and the constraints on each input; and
  * The outputs it will generate.

After this stage, `clay` will automatically:

* Create a `Dockerfile` for your model
* Build the docker container and push it to Pixxel’s container registry; and
* Let  `orchestrator` know about this new and really amazing model that has just been created and how it works, so that `orchestrator` can in turn deploy it and let all of Pixxel’s infrastructure discover and use it.

## Nomenclature
* `clay` CLI : A command line tool which is used to create project template for models
* `clay` python package:  which will be used in the created projected as a dependency

## Installation

Install the **latest** version of `clay` CLI tool from here: https://github.com/example/clay/releases

## Getting Started
* Prerequisite: `clay` CLI should be installed in your systeam

### Clay CLI
<details>
  <summary>Use this guide as a reference for the available commands supported by clay
  for operations related to a model</summary>


1. `clay create project [outputDir] [modelName]`

    Generate starter files for your model

2. `clay create dockerfile [modelSpecificationPath] [sourceCodeFolder] [useHttpRunner] [flags]`

    Creates a dockerfile using your model spec assuming that sourceCodeFolder contains all the necessray code
    Set the http Flag to create a dockerfile that runs the model as a server instead of a job.
    --http   Set flag to package model as an http server instead of a job

3. `clay add block [specFilePath] [flags]`

    Add a new block in Pixxel Labs
    A block, with the specification file, will be added to orchestrator.
    -e, --env Set environment flag to add new block to: dev, stg, prod (default "dev")

4. `clay list block [flags]`

    List the blocks available in database
    If no flag is provided, it lists all the "released" blocks of "dev" environment
    Set blockname to list the versions of a block
    Set status to list the blocks by status

    -n, --name string     Name of block
    -s, --status string   Possible status of block: draft, released, disabled (default "released")
    -e, --env string   Environment to add new block to: dev, stg, prod (default "dev")

5. `clay get block [flags]`

    Get spec file of a block version
    By Default only "released" block spec is provided
    -n, --name string      Name of block
    -s, --status string    Status of block: draft, released, disabled (default "released")
    -v, --version string   Version of block
    -e, --env string   Environment to add new block to: dev, stg, prod (default "dev")

6. `clay update block [specFilePath] [flags]`

   Update an existing block
   Provide updated specfile path with the fields to be updated
   Set the blockname, version, status flag
   Use flag 'env' to specify the environment in which the block is to be updated
   -n, --name string      Name of block
   -s, --status string    Status of block: draft, released, disabled (default "released")
   -v, --version string   Version of block
   -e, --env string   Environment to add new block to: dev, stg, prod (default "dev")

7. `clay upload readme [flags] `

   Upload the readme for the model to cloud

   -n, --name string      Name of block as specified in spec file
   -v, --version string   Version of block

   Note: Once readme folder is uploaded, link of `parsed.md` file provided
   in the output of this command
   Please update the `catalog_content_url` in the spec file with the link


</details>



### Build Model using Clay
<details>
  <summary>Steps to create a clay model</summary>


### Step 1: Create your project

Create your project with:

```bash
clay create project path/to/outputDirectory ModelNameInCamelCase
```

This will create your project here: `path/to/outputDirectory/ModelNameInCamelCase`.

You should take some time to look at the files that have been created. You can refer to [this demo model](https://github.com/example/demo-clay-model) to understand the structure of the project.

### Setp 2: Setup project

1. Create and activate a fresh python envrionment based on the tool you are using, `venv` or `conda`
    * For `venv` run:
        - create new environment: `python3 -m venv <env_name>`
        - activate new environment: `source venv/bin/activate`
    * For `conda` run:
        - create new environment: `conda create --name <env_name> python=3.9`
        - activate new environment: `conda activate <env_name>`

2. Install the required private dependencies `clay` and `pixxelsign` python package
    Installation Tips:
    * `Clay` requires `GDAL` to be installed and working correctly in your environment.
    * Make sure you're installing the latest version of `clay` where possible.
    * Contact the MLOps Team for help with `YOUR-GITLAB-TOKEN`.
    <br> <br>
    Now run
    ```bash
    pip install clay pixxelsign --index-url https://gitlab+deploy-token-1735743:<YOUR-GITLAB-TOKEN>@gitlab.com/api/v4/projects/38508365/packages/pypi/simple
    ```

Next, you should run:

```bash
make setup
```

This will initialize `git` if needed, install some packages from the `requirements.txt` file, and set-up `pre-commit` to enforce some formatting and git commit rules for the project.

---

### Step 3: Define your model's inputs and outputs

At this point, we're ready to dive head on into writing our model code and creating the model specification.

First, you will need to open `ModelName/specifications/model_specification_dev.yaml` and fill in the `parameters`, `inputs` and `outputs` fields. They have some pre-filled values to help you understand the expected format and available options.

You can ignore other keys for now. Read further to understand how to fill in the specification file.

Open up `src/model.py` to see an empty scaffolding for your model. You are (not yet) expected to write all these functions to describe how your model works.

* The `setup` function will be called once at the time of model initialization
    * The setup function can take any number of parameters, where each parameter can be either a `string`, `float`, or `int`
    * `list` is not fully supported (yet), and you will have to make do with accepting a `string` that you manually convert to a list.
    * You will put the model setup parameters in the `parameters` key in the model specification file. Each element of the list will have three keys:
        * `name`: The corresponding name of the parameter in the `setup` function
        * `type`: one of `int`, `float`, or `string`
        * `default`: the literal value of the given parameter

* The `preprocess` function is the **entry point** for all inferences run using the model at runtime. The parameters that this function expects will be specified in the `inputs` key in the model specification file. Each parameter will have the following keys:
    * `name`: the corresponding name of the parameter in the `preprocess` function
    * `type`: the literal data type of the parameter that is expected. For instance:
        * A URL for a raster will be expected in the `string` data type.
        * A parameter such as a threshold will be expected in the `float` data type.
    * `format`: the actual entity that the parameter is supposed to **represent**. For instance:
        * If the parameter is a URL for a raster, then `format` will be `raster`.
        * If it is a `float` or an `int`, then `format` would be `number`.
        * If it is a URL to a geojson, then `format` would be `vector`.
    * [OPTIONAL] `properties`: This parameter will contain the properties and constraints applied to the **entity** that is **represented** by the parameter.
        * For a raster, you can have properties like the sensor, avialable bands and the array dtype.
        * For a vector, you can have properties like the kind of geometries it represents.
        * As of now, this field is more of a filler, and is not actuall used anywhere for any purpose.
        * In the future, this will be used to validate inputs and guarantee model outputs.

    In plain English, you are telling `clay` that a parameter called `name` is to be passed with a dtype of `type`, representing an entity of the `format` kind, with certain guaranteed `properties`.

    As you'd expect, each `format` can be represented by and supports certain `type`s:

    * `raster`: `url`, `string`, `path`, `str`
    * `vector`: `string`, `str`
    * `number`: `float`, `int`
    * `string`: `string`, `str`
    * Note: `str` is the same as and short for `string`

    In the future we plan to add the `list` `type` and the `datetime` `format`.

* Opposite of `preprocess`, the `postprocess` function's return values determine the `outputs` key in the model specification file. The `outputs` have to be filled-in in the same way as `inputs`.

With these values in place, we can now move on to writing the actual model code.

---

### Step 4: Write and test your model code

First, open up `src/model.py` and:

* Implement the `setup`, `preprocess`, `inference` and `postprocess` functions.
* It would help to know that:
    * The outputs of `preprocess` are passed as is to `inference`
    * The outputs of `inference` are passed as it to `postprocess`
    * The outputs of `postprocess` are supposed to be in the order and of the `type`s that are defined in `outputs` key in the model specification.
* Try and avoid using `print` statements. Prefer `self.logger` that has been insantiated for you by the `ModelWrapper` class automatically.
* Optionally add `self.logger.info(something)` and `self.logger.debug(something_else)` throughout the model code to help you monitor what is going on when an inference request is run.

Then, open up `src/sample_model_inputs.json` and:

* Modify the inputs to reflect the inputs your `preprocess` function expects. The `value` key is expected to hold the literal value of the input to the model.
* Leave the `task_id` input as is.
* Run: `python3 src/test_model.py`

If all goes well, this should run smoothly.

---

### Step 5: Finish the model specification

You can go ahead and first fill in these self explanatory keys in the model specification:

* `description`
* `author`
* `resources`
    * Note that for `cpu`, `1000m` ~= `1 CPU`
    * For `mem`, `1000mi` ~= `1 GB`

Then, go ahead and fill the `build` key to specify the environment in which your model will run:

* `python-version`: Python version
* `conda`: Whether to build the environment using `conda`. By default, `conda` is `false` and we use a regular python `virtualenv`
* `gdal`: Whether `gdal` is required. This is `true` by default and will almost always stay that way
* `apt-get`: any apt get packages that are required. This list can be empty as well, although `wget` is present by default for demonstration purposes
* `requirements`: the path to the `requirements.txt` or the `conda-environment.yml` file relative to the project root.

You can ignore the `options` key.

---

### Step 6: Package and test the model

Go to your project root, and type in the following command:

```bash
make package-and-test-model
```

The above command will:

* Create a `Dockerfile` for your model
* Build the docket image for the model.
* Test it with `sample_model_inputs.json`

The above command will not work if you are using a model specification file at a location other than the default one, or if your source code is in a location other than the `src` folder. In that case, the following set of commands will work:

```bash
clay create dockerfile path/to/model_specification_dev.yaml path/to/source/code
```

After building the dockerfile, assuming it is present at the root of the project, run the below to create a docker image:

```bash
make docker-image
```

This will create the docker image. You can then test the image like so:

```bash
make test-docker-image
```

---

### Step 7: Update the version file and push to GitHub

Open `src/__version__.py` and edit the version.

Refer to [semver](https://semver.org) for details on how to version your model.

Commit your code, and push it to GitHub. `Clay` and `Orchestrator` will take it from here!



</details>
