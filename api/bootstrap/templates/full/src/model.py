from clay import ModelWrapper


class {{.ModelName}}(ModelWrapper):
    def setup(self, weights, **hyperparameters):
        # download weights, initialize model,
        # setup directories, etc.
        pass

    async def preprocess(self, user_input, extra):
        # pre-process user-input if needed to get it
        # ready for inference
        model_inputs, extra = None, None
        return model_inputs, extra

    async def inference(self, model_inputs, extra):
        # simply run inference and return the results
        # and anything extra if required
        inference_results, extra = None, None
        return inference_results, extra

    async def postprocess(self, inference_results, extra):
        # perform any post-processing, uploads, etc.
        upload_location = None
        return upload_location
