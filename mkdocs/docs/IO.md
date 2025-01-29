# Input/Output
An ML model can be considered as black box functiontakes something as input and return something which is treated as output. Clay enforces the model to have input and output of certain `types`. We internally call these types as `datatypes`

#### Why do we need `Types`?

You might be wondering, *why do we even need types? what is this additional layer of complexity? why should I learn one more thing?* The answer boils down to this,

> For models to work together and with each other, they need to speak the same language.

Since models are developed in silioes and as independent entities, *but* are expected to work with each other in connected chains, they need to have a common *dialect*, that they and the broader system understands. Using this *dialect*, the models specify their *inputs* and their *outputs*. Since all models and the system speak the same language, they can determine whether the output of one model can be compatible with the input of another model.

For example, if `ModelA` outputs a `GeoTiff` file and `ModelB` accepts a `GeoJSON` as input, they output of `ModelA` cannot be provided as input to `ModelB`, because well, they are of different `Types`.

![types-1](assets/types-1.png)

But this works,

![types-2](assets/types-2.png)

#### What do these `Types` mean?

??? abstract "TLDR"

    `Types` represent high-level concepts that mean something in the context of our platform and product. They may or may not coincide with programming constructs.

*Technically* Python doesn't have a *strong type system*. As a result, the language itself doesn't intrensically provide us with the ability to build types that represent higher level concepts.

Hence, we use [Pydantic's](https://docs.pydantic.dev/latest/) [Model Objects](https://docs.pydantic.dev/latest/concepts/models/) to create our Types.

!!! warning

    The user is not expected to interact with Pydantic's APIs with respect to Clay's Types, during usage.

These `Types` represent **high level** concepts that *mean something in the broader system*. Some types like [Rasters](#raster) and [Tabular](#tabular) are not programming concepts but are concepts that are relevant in the broader context of our product (1). On the other hand, types like [String](#string) and [Number](#number) have a meaning in programming constructs. Incidentally, it just so happens that these types also have a meaning in our product context.

#### Supported `Types`

While these are the types we are starting with, this list is in no way complete and we will be considering including more types as we go forward.

* **Raster** - *Used to represent GeoTIFFs*
* **Vector** - *Used to represent GeoJSONs*
* **Tabular** - *Used to represent tabular data*
* **Date** - *Used to represent dates*
* **Number** - *Used to represent numerical data*
* **String** - *Used to represent strings*

All the types are defined in `clay.types`. While each type might have some specific *properties*, they all share some common attributes. The common attributes are documented at [Common Attributes](#common-attributes). The entire list of types supported are mentioned in the subsequent [Fundamental Types](#fundamental-types) section.

## Common Attributes
Below is the contract defined by clay for I/O types.
```json
{
 "format": ""  //required
 "type": ""    //required
 "name": ""    //required
 "value": ""   //required
 "properties": {}  //optional
}
```

### Nomenclature
1. **Name:**
Identifier / name for the data. This has to match with the expected parameter name in the model’s preprocess function in clay. This could also be mutated when trying to chain different models together.

2. **Format:**
This specifies the *type of entity* that the data represents. Is it a *raster*, *number*, *date*, *vector* or a *string*?
This is independent of the extension that the file is stored with.
For instance, an *image* can be stored as any one of *jpeg, png, or gif*, and a vector can be stored as *geojson, gpkg, or shp*.
The storage schema does not change the fact that the data is to be interpreted as an *image* or a *vector* respectively.\
  Supported formats:
    - raster
    - vector
    - number
    - date
    - string
    - tabular

3. **Value:** Contains the actual data for primitive formats like number, string and date. For compound types like raster and vector, it may contain a URL to the file containing the data (i.e. the actual raster or vector).

4. **Type:** This represents the intended dtype of data contained in value. A combination of format and type will let the model know how to read the data. For instance, if the data has a format specified as raster and type specified as str, then it is assumed that its value contains a URL to the raster in question. This way the type is decoupled from the format.
This is also important for clay to be able to cast the value properly before giving it to the model. \
Supported types are:
    - string
    - float
    - int
    - bool
    - url
    - list
    - dict

5. **Properties:** This contains any metadata needed by the model to better understand and process its inputs. This can change depending on the format.

??? abstract "A disambiguation between `format` and `type`:"

    Format is a high level entity that has some conceptual meaning, which may or may not have any meaning in programming languages. For example, raster / vectors etc.

    On the other hand, type is an actual data type (like string, number, float) that means something in general programming languages. type is technically the actual dtype of the value parameter.

    It tells the consumer how to actually interact with the value attribute.


!!! warning "Types in Clay is being deprecated"

    We are in the process of deprecating existing *Types* implementation in Clay and move to newer external implementation. For more information please visit the [datatypes-schema docs](https://datatypes-schema.example.com/). The conceptual foundation is still the same, but the technical implementation and usage has changed slightly. You can read more about this in at [docs](https://datatypes-schema.example.com/). For tracking the model migration please check out this [linear ticket](https://linear.app/REDACTED/issue/REDACTED-TICKET/[tracker]-model-integration-with-datatypes-schema).


## Fundamental Types

### Raster
::: clay.types.Raster

### Vector
::: clay.types.Vector

### Tabular
::: clay.types.TabularProperties

### Date
::: clay.types.Date

### String
::: clay.types.String

### Number
::: clay.types.Number


## Type Properties

### RasterProperties
::: clay.types.RasterProperties

### VectorProperties
::: clay.types.VectorProperties

### TabularProperties
::: clay.types.TabularProperties

### DateProperties
::: clay.types.DateProperties

## Visualisation in supported types

### RasterVisualisation
::: clay.types.RasterVisualisation

#### Raster Visualisation Types

##### VizContinuous
::: clay.types.VizContinuous

##### VizBucket
::: clay.types.VizBucket

## Raster Discretization

##### RasterDiscretization
::: clay.types.RasterDiscretization

##### DiscretizationItem
::: clay.types.DiscretizationItem

## Input Validations
We support validating input values, which is configured while defining inputs, for following types
1. Number: checking if the number is in the range of `min_value` and `max_value`
```yaml
  - name: some_input
    format: number
    type: int
    validation:
      min_value: 1
      max_value: 20
```
2. String: checking if the string value is matching with given `regex_match`. In the example, we are checking if `some_input_str` matches with `regex_match`
```yaml
  - name: some_input_str
    format: string
    type: str
    validation:
      regex_match: '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
```
3. Raster: checking whether area of AOI for given raster is within the range of `min_area` and `max_area` in sqkm. In the given example, we are configure for validation if the area of some_raster is within 50 sqkm and 100sqkm.
```yaml
  - name: some_raster
    format: raster
    type: url
    validation:
      min_area: 50
      max_area: 100
```

4. Vector: checking whether area of AOI for given vector is within the range of `min_area` and `max_area`. In the given example, we are configure for validation if the area of some_vector is within 50 sqkm and 100sqkm.
```yaml
  - name: some_vector
    format: vector
    type: int
    validation:
      min_area: 50
      max_area: 100
```
