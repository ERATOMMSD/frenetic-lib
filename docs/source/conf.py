# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../../src/'))



# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'frenetic-lib'
copyright = '2022, Stefan Klikovits, Ezequiel Castellano, Ahmet Cetinkaya, Paolo Arcaini'
author = 'Stefan Klikovits, Ezequiel Castellano, Ahmet Cetinkaya, Paolo Arcaini'
release = '0.0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'autoapi.extension',
    # 'sphinx.ext.autodoc',
    # 'sphinx_autodoc_typehints',
    'sphinx.ext.napoleon',  # allow Google-style documentation
    'myst_parser',  # allow Markdown
    'sphinx_rtd_theme',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    # 'sphinx.ext.autosummary',
]

templates_path = ['_templates']
exclude_patterns = []


source_suffix = ['.rst', '.md']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


autoapi_type = 'python'
autoapi_dirs = ['../../src/freneticlib']
autoapi_python_class_content = "both"