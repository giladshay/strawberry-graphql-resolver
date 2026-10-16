from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "Strawberry GraphQL Resolver"
copyright = "2026, Gil-Ad Shay"
author = "Gil-Ad Shay"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]
autosummary_generate = True
autodoc_default_options = {
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_theme = "alabaster"
suppress_warnings = [
    "autodoc",
    "ref",
    "ref.python",
    "sphinx_autodoc_typehints.forward_reference",
]
