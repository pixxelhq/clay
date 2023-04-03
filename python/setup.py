from setuptools import find_packages, setup


def get_version() -> dict:
    version = {}  # type: ignore
    with open("clay/__version__.py") as f:
        exec(f.read(), version)
    print(version)
    return version["__VERSION__"]


setup(
    name="clay",
    version=str(get_version()),
    description="This is the SDK that would be used to deploy all models at pixxel.",
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
    install_requires=[
        "uvicorn",
        "fastapi",
        "click",
        "click-plugins",
        "pydantic",
        "Jinja2",
        "uvloop",
        "pika",
    ],
    package_data={"clay": ["templates/*.jinja"]},
    include_package_data=True,
)
