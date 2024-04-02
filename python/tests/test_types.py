from clay import types


def test_clb_init() -> None:
    c = types.Callback(Id="123", State=types.ModelStates.FAILED)
    assert c.State == types.ModelStates.FAILED


def test_clb_serialise_dict() -> None:
    c = types.Callback(Id="task123", State=types.ModelStates.FAILED)
    d = c.model_dump(by_alias=True)
    assert d == {
        "id": "task123",
        "state": "failed",
        "err_msg": "",
        "inputs": None,
        "result": None,
        "logs": "",
        "outputs": None,
        "user_logs": "",
        "recv_time": None,
        "send_time": None,
        "start_time": None,
        "end_time": None,
        "block_inf_start_time": None,
        "block_inf_end_time": None,
        "model_inf_start_time": None,
        "model_inf_end_time": None,
    }


def test_init_raster_model_from_dict_success() -> None:
    d = {
        "format": "raster",
        "type": "url",
        "name": "raster",
        "value": "some.tiff",
        "properties": {"bands": ["B01", "B02"]},
    }

    r = types.Raster.model_validate(d, context={"a": "b"})
    assert r.Properties.Bands == ["B01", "B02"]


def test_init_raster_model_from_dict_with_None_props_success() -> None:
    d = {
        "format": "raster",
        "type": "url",
        "name": "raster",
        "value": "some.tiff",
        "properties": None,
    }

    r = types.Raster.model_validate(d)
    assert r.Properties is None


def test_init_raster_model_from_dict_with_sun_elevation() -> None:
    d = {
        "format": "raster",
        "type": "url",
        "name": "raster",
        "value": "some.tiff",
        "properties": {
            "sun_elevation": 1.2,
        },
    }

    r = types.Raster.model_validate(d)
    assert r.Properties.SunElevation == 1.2
    assert r.Properties.SatelliteLookAngle is None


def test_init_raster_model_from_dict_with_satellite_look_angle() -> None:
    d = {
        "format": "raster",
        "type": "url",
        "name": "raster",
        "value": "some.tiff",
        "properties": {
            "satellite_look_angle": 3.4,
        },
    }

    r = types.Raster.model_validate(d)
    assert r.Properties.SatelliteLookAngle == 3.4
    assert r.Properties.SunElevation is None


def test_init_string_model_with_default_value() -> None:
    d = {"format": "string", "type": "str", "name": "s", "default": "hello"}
    s = types.String.model_validate(d)
    assert s.Default == "hello"


def test_init_string_model_with_no_value_or_default() -> None:
    d = {"format": "string", "type": "str", "name": "s"}
    s = types.String.model_validate(d)
    assert s.Value is None
    assert s.Default is None


def test_init_date_model_with_value() -> None:
    d = {"format": "date", "type": "str", "name": "d", "value": "12-02-2022"}
    v = types.Date.model_validate(d)
    assert v.Value == "12-02-2022"


def test_init_tabular_model_with_value() -> None:
    d = {"format": "tabular", "type": "url", "name": "t", "value": "f.csv"}
    v = types.Tabular.model_validate(d)
    assert v.Value == "f.csv"
