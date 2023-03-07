import os
import sys
from typing import List

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "ramen"
copyright = "2022, Pixxel Data"
author = "Pixxel Data"
master_doc = 'index'
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
]

autodoc_default_options = {
    "members": None,
    "member-order": "bysource",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}

templates_path = ["_templates"]
exclude_patterns: List[str] = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "classic"
html_theme_options = {"relbarbgcolor": "black"}

html_static_path = ["_static"]

# Adding paths

sys.path.insert(0, os.path.abspath(f"../{project}"))
