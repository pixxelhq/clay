# type: ignore
import os
import shutil
import sys
from pathlib import Path

import pytest

sys.path.append(str((Path(__file__).parent) / "testrepo"))
from entry import M


@pytest.fixture(scope="session")
def session_setup(request):
    os.mkdir("./tmp")

    def fin():
        shutil.rmtree("./tmp")

    request.addfinalizer(fin)


@pytest.fixture(scope="function")
def toy_model():
    return M(config="tests/testrepo/config.yaml")
