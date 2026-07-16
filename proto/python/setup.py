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
    description="Schema for supported data-types in Clay blocks.",
    url="https://github.com/pixxelhq/clay",
    license="Apache-2.0",
    packages=find_packages(
        include=["datatypes"], exclude=["datatypes/tests", "test_*",]
    ),
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=[
        "protobuf>=6.33.2,<7"
    ],
    include_package_data=True,
    package_data={"datatypes-schema": ["py.typed"]}
)
