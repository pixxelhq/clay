from setuptools import find_packages, setup

version_string = "0.0.1"

setup(
    name="ramen",
    version=version_string,
    description="This is the SDK that would be used to deploy all models at pixxel.",
    # Author details
    author_email="ml@pixxel.co.in",
    url="https://github.com/example/ramen",
    # Choose your license
    license="Ask Raghav",
    packages=find_packages(include=["ramen", "ramen.*"]),
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
    ],
)
