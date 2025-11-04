# type: ignore
import os
import shutil
import sys
from pathlib import Path

import nest_asyncio
import pytest

from .models.ymxplusc import YMXPLUSC, YMXPLUSC_CONFIG

sys.path.append(str((Path(__file__).parent) / "testrepo"))


@pytest.fixture(scope="session")
def session_setup(request):
    os.mkdir("./tmp")

    def fin():
        shutil.rmtree("./tmp")

    request.addfinalizer(fin)


@pytest.fixture(scope="function")
def toy_model() -> YMXPLUSC:
    return YMXPLUSC(config=YMXPLUSC_CONFIG)

def pytest_configure():
    nest_asyncio.apply()