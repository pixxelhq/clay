from pathlib import Path

from setuptools import find_packages, setup

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_REQ = "requirements/requirements.txt"


def load_requirements(fname: str = DEFAULT_REQ) -> list[str]:
    req_file = PROJECT_ROOT / fname
    if not req_file.is_file():
        raise FileNotFoundError(
            f"[setup.py] Cannot locate dependency file:\n  {req_file}"
        )

    lines = (
        line.strip()
        for line in req_file.read_text(encoding="utf-8").splitlines()
    )
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
    description="This is the SDK that would be used to deploy all blocks at pixxel.",
    # Author details
    author_email="ml@pixxel.co.in",
    url="https://github.com/example/clay",
    # Choose your license
    license="Ask Raghav",
    packages=find_packages(include=["clay", "clay.*"]),
    classifiers=[
        # Indicate who your project is intended for
        "Development Status :: 0 - Pre-alpha",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Developers",
        "Topic :: Scientific/Engineering",
        # Pick your license as you wish (should match "license" above)
        # 'License :: OSI Approved :: The Unlicense (Unlicense)',
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    # What does your project relate to?
    # keywords = 'put keywords here'
    # List run-time dependencies here. These will be installed by pip when
    # your project is installed.
    install_requires=load_requirements(),
    package_data={"clay": ["py.typed"]},
    include_package_data=True,
)
