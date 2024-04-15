# Do's And Don'ts

Guidelines for model development

1. No Print statement 
   
    You should never use print statement in your model, rather use logger explained in the [Model Development](model-development.md)

2. Logging properly (with log levels  use only INFO, WARNING, ERROR)
    
    Logging should be used instead of print statement with proper log [levels](https://stackoverflow.com/questions/2031163/when-to-use-the-different-log-levels).


3. Don’t share envs between projects for model development  ❌


4. Don’t mix up conda and pip  ❌
    
    Use either pip or conda as dependency manager for the model development. 


5. Clay.failure
    
    Use Clay.failure in case of any validation error or any error which you want the end user to show in case of failure. 


6. Validation check before/in the preprocess


7. Ensure proper documentation for the repository (about the model itself, link examples)


8. Follow git best practices.
