# 10000 Feet View: How does ML @ Pixxel Work?

This document is intended for someone satisfying one (or more) of the following criteria,

* You are on the Analytics / R&D team but haven't deployed a model yet and this is your first rodeo.
* You just joined the Platform / Analytics / R&D Team and trying to wrap your head around.
* You are one of the friendly folks on the product team wanting to understand how it all works.
* Anyone else whose job doesn't involve writing code.

If you don't satisfy any of these criteria, you probably already know all of these. In spite of this, you are more than welcome to carry-on!

## Glossary

Before we march on, let us settle on a common vocabulary.

* **Model**: Any *F(x)* that does some math. As in, takes an input, does some *math*, and returns an output. *X + Y = Z* yes that's a model. A cutting edge deep-learning model, yes that too, is a model.

* **Infrastructure**: Engineer-speak for hotch-potch of servers, networks, gateways and some other buzzwords. All our software runs on these things (At least most of it). Oh and they are very expensive.

* **Kubernetes**: A magical software over infrastructure that manages and runs all our software.

* **Cluster**: Referred also as "*an environment*" internally, a (mostly) isolated version of *kubernetes* that runs different versions of our software. There are essentially *three clusters* - **dev**, **staging** and **production**.

    1. *Dev Cluster*: Well, it's for devs. Any software written first gets deployed here. Usually this doesn't work most of the times.

    2. *Staging Cluster*: Post a lot of fixing, software deployed earlier in dev, gets promoted to staging. This is the last step before code is pushed to `production` for customers to use. Hence, software deployed here needs to be *stable*.

    3. *Production Cluster*: Well, this is the final stage and ideally everything *must* work.

* **Orchestrator**: A service that manages and runs all ML related features on Platform.

* **Clay**: A tool that *wraps* any *model* and ensures that they work on our *infrastructure*.

## How it works

![orchestrator-high-level](assets/orchestrator-high-level.png)

* The model author does a lot of research and creates a model.
* After the model is determined fit for release, the author *wraps* the model with *clay*.
* The author then adds the model to Orchestrator.
* Orchestrator then makes this model available for broader consumption by users.
* A user selects the model on Platform, runs it for some input and gets the outputs.

Done. That's it.

## Things I *skipped* over

* The web of dependencies between different services (eg: Atlas <> Orchestrator) and teams (analyics <> MLOps, Studio <> MLOps etc).

* *Data types* i.e. data that the models are allowed to accept and produce.

* Intricacies of workflow and direct insight execution. (*They are different*)

* The *actual* APIs that people will be using.
