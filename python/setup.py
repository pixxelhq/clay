from pathlib import Path

from setuptools import find_packages, setup

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_REQ = "requirements/requirements.txt"


def load_requirements(fname: str = DEFAULT_REQ) -> list[str]:
    req_file = PROJECT_ROOT / fname
    if not req_file.is_file():
        raise FileNotFoundError(f"[setup.py] Cannot locate dependency file:\n  {req_file}")

    lines = (line.strip() for line in req_file.read_text(encoding="utf-8").splitlines())
    return [ln for ln in lines if ln and not ln.startswith("#")]


def get_version() -> dict:
    version = {}  # type: ignore
    with open("clay/__version__.py") as f:
        exec(f.read(), version)
    print(version)
    return version["__VERSION__"]


setup(
    name="pixxel-clay",
    version=str(get_version()),
    description="SDK for packaging ML models as deployable, declaratively-configured blocks.",
    url="https://github.com/example/clay",
    license="Apache-2.0",
    packages=find_packages(include=["clay", "clay.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    install_requires=load_requirements(),
    package_data={"clay": ["py.typed"]},
    include_package_data=True,
)
