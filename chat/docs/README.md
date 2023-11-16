# Generating Docs from Python Code Using Sphinx

## Prerequisite

Using Sphinx to generate document for Python project code requires at least two libraries, `sphinx` and `sphinx_rtd_theme`.

```
pip install sphinx sphinx_rtd_theme
```

## Step 1: Generating .rst files

```
%
% sphinx-quickstart
Welcome to the Sphinx 7.1.2 quickstart utility.

Please enter values for the following settings (just press Enter to
accept a default value, if one is given in brackets).

Selected root path: .

You have two options for placing the build directory for Sphinx output.
Either, you use a directory "_build" within the root path, or you separate
"source" and "build" directories within the root path.
> Separate source and build directories (y/n) [n]:

The project name will occur in several places in the built documentation.
> Project name: Chat Demo
> Author name(s): Chuan Zhang
> Project release []: 1.0.0

If the documents are to be written in a language other than English,
you can select a language here by its language code. Sphinx will then
translate text that it generates into that language.

For a list of supported codes, see
https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-language.
> Project language [en]:

Creating file /home/czhang/Projects/chat-demo/chat/docs/conf.py.
Creating file /home/czhang/Projects/chat-demo/chat/docs/index.rst.
Creating file /home/czhang/Projects/chat-demo/chat/docs/Makefile.
Creating file /home/czhang/Projects/chat-demo/chat/docs/make.bat.

Finished: An initial directory structure has been created.

You should now populate your master file /home/czhang/Projects/chat-demo/chat/docs/index.rst and create other documentation
source files. Use the Makefile to build the docs, like so:
   make builder
where "builder" is one of the supported builders, e.g. html, latex or linkcheck.

%
```
This above command generates the following files
```
% ls -lah
total 36K
drwxr-xr-x 5 czhang czhang 4.0K Nov 15 21:39 .
drwxr-xr-x 5 czhang czhang 4.0K Nov 15 21:37 ..
-rw-r--r-- 1 czhang czhang  634 Nov 15 21:39 Makefile
drwxr-xr-x 2 czhang czhang 4.0K Nov 15 21:39 _build
drwxr-xr-x 2 czhang czhang 4.0K Nov 15 21:39 _static
drwxr-xr-x 2 czhang czhang 4.0K Nov 15 21:39 _templates
-rw-r--r-- 1 czhang czhang  961 Nov 15 21:39 conf.py
-rw-r--r-- 1 czhang czhang  443 Nov 15 21:39 index.rst
-rw-r--r-- 1 czhang czhang  800 Nov 15 21:39 make.bat
%
```
Now we are ready to generate the .rst files. As our application code is under the `app` folder, we can generate the .rst files as follows.
```
%
% cd ..
%
% sphinx-apidoc -o docs app
Creating file docs/app.rst.
Creating file docs/modules.rst.
%
% tree docs
docs
├── Makefile
├── _build
├── _static
├── _templates
├── app.rst
├── conf.py
├── index.rst
├── make.bat
└── modules.rst

3 directories, 6 files
%
```
## Step 2. Updating the index.rst files and conf.py
### Updating index.rst
```
% 
% vi docs/index.rst
%
% cat docs/index.rst
.. Chat Demo documentation master file, created by
   sphinx-quickstart on Wed Nov 15 21:39:52 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Chat Demo's documentation!
=====================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules                                          <=== add this line

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
%
```
### Updating conf.py
```
% vi docs/conf.py
%
% cat docs/conf.py
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('..'))               <=== add these three lines for abspath

project = 'Chat Demo'
copyright = '2023, Chuan Zhang'
author = 'Chuan Zhang'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [                                          <=== add the following three extensions
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc"
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'                        <=== replace the theme with sphinx_rtd_theme
html_static_path = ['_static']
%
```

## Step 3. Build HTML Docs
```
%
% make html
Running Sphinx v7.1.2
loading pickled environment... done
building [mo]: targets for 0 po files that are out of date
writing output...
building [html]: targets for 0 source files that are out of date
updating environment: 0 added, 1 changed, 0 removed
reading sources... [100%] app
looking for now-outdated files... none found
pickling environment... done
checking consistency... done
preparing documents... done
copying assets... copying static files... done
copying extra files... done
done
writing output... [100%] modules
generating indices... genindex py-modindex done
highlighting module code... [100%] redis.client
writing additional pages... search done
dumping search index in English (code: en)... done
dumping object inventory... done
build succeeded.

The HTML pages are in _build/html.
%
```
After this step, the document is ready for browsing. The generated `index.html` file under `docs/_build/html/` directory looks like the screenshot below.
![image](https://github.com/chuan2019/chat-demo/assets/47965229/72533911-9c0c-4827-a74f-f22cda9f2a9b)
