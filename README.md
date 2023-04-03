# Clay

```yaml
deployment:
    storage:
        - provider: azure
          type: str
          value: container
model:
    init:
        - name: key
            type: int
            val: 12
        - name: key2
            type: str
            val: avc
    inputs:
        - name: val
            type: str
```

```python
from clay import ModelWrapper
from clay import

class Model(ModelWrapper):
    pass

#create_docker_image(model = m)

if __name__ == "__main__":
    m = create_server(model = Model)
    m.start()
    m.stop()
```
