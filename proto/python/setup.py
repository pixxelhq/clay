import os
from setuptools import find_packages, setup


def get_version() -> dict:
    version = {}  # type: ignore
    print("--------", os.getcwd())
    with open("datatypes/__version__.py") as f:
        exec(f.read(), version)
    print(version)
    return version["__VERSION__"]

setup(
    name="pixxel-datatypes",
    version=str(get_version()),
    description="Schema for supported data-types within the Pixxel ecosystem",
    # Author details
    author_email="mlops@pixxel.co.in",
    url="https://github.com/example/datatypes-schema",

    # Choose your license
    license="Ask Raghav",
    packages=find_packages(
        include=["datatypes"], exclude=["datatypes/tests", "test_*",]
    ),

    # What does your project relate to?
    # keywords = 'put keywords here'
    # List run-time dependencies here. These will be installed by pip when
    # your project is installed.
    install_requires=[
        "protobuf"
    ],
    include_package_data=True,
    package_data={"datatypes-schema": ["py.typed"]}
)
