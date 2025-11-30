---
title: "My favorite tools that keep my Python projects sane 🧰"
subtitle: A look at my preferred tools for improving code quality, testing, automation, and documentation in Python projects.
summary: A look at my preferred tools for improving code quality, testing, automation, and documentation in Python projects.
projects: []
date: '2023-04-22T00:00:00Z'
draft: false
featured: false

image:
  caption: 'Another hyper-modern way to deal with the snake'
  focal_point: ''
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  - python
  - pre-commit
  - black
  - ruff
  - tox
  - pyupgrade
  - isort
  - mypy
  - versioningit
  - versioneer
  - setuptools-scm
  - miniver
  - bumpversion
  - bump2version
  - nox
  - pytest
  - pyproject.toml
  - setup.py
  - setup.cfg
  - readthedocs
  - sphinx
  - jupyter
  - myst-nb
  - jupytext

categories:
  - setup
  - level:intermediate
---

## 🌟 1. Introduction

As a passionate Python developer, I am always on the hunt for the best tools to streamline my development process and enhance the quality of my projects. Over time, I have discovered a set of tools that have become indispensable in my workflow, making my coding experience more efficient and enjoyable. Using the right developer tools for Python projects is crucial for maximizing productivity, ensuring code consistency, and maintaining high-quality code.

In this blog post, I will share these essential tools that I now use for every single new project. We will explore the benefits of each tool and discuss how they can help you supercharge your Python development. The tools covered in this post include [pre-commit](https://pre-commit.com/), [Black](https://black.readthedocs.io/en/stable/), [Ruff](https://beta.ruff.rs/docs/rules/), [Mypy](https://mypy.readthedocs.io/en/stable/), [Versioningit](https://versioningit.readthedocs.io/en/latest/), [Pyproject.toml with PEP 621](https://www.python.org/dev/peps/pep-0621/), [Nox](https://nox.thea.codes/en/stable/), [pytest](https://docs.pytest.org/en/7.3.x/), [GitHub Actions CI matrix](https://docs.github.com/en/actions/learn-github-actions), and [Read the Docs](https://readthedocs.org/), [Sphinx](https://www.sphinx-doc.org/), [MyST-NB](https://myst-nb.readthedocs.io/en/latest/), and [Jupytext notebooks](https://jupytext.readthedocs.io/en/latest/) for documentation. Let's dive in and learn how to enhance your Python projects with these powerful tools!

{{< toc >}}

{{% callout note %}}
This post is based the way I develop Python projects. For full examples see [Adaptive Scheduler](https://github.com/basnijholt/adaptive-scheduler/) (full project), [`markdown-code-runner`](https://github.com/basnijholt/markdown-code-runner) (for a single module package), and [Adaptive](https://github.com/python-adaptive/adaptive/) (for cool documentation and nox).
Over time I might change my mind about some of the tools, but I will try to keep this post up-to-date.
{{% /callout %}}

## 🛠️ 2. Pre-commit

One of the most common challenges developers face when working on a project, whether alone or in a team, is maintaining code quality and consistency. As projects grow, it becomes increasingly difficult to enforce coding standards and catch issues before they make their way into the codebase. This is where pre-commit comes in.

[Pre-commit](https://pre-commit.com/) is a powerful tool that helps you manage and maintain code quality by automating checks before commits. It achieves this by setting up a series of hooks that run before each commit, ensuring that only code that meets your predefined standards is committed to the repository. By catching issues early, pre-commit helps you keep your code clean and consistent, making it easier to review and maintain.

One of the reasons pre-commit has gained widespread adoption is its flexibility and extensibility. You can choose from a vast range of built-in hooks, such as code formatters, linters, and security checkers, or even create your own custom hooks. This allows you to tailor pre-commit to the specific needs of your project, ensuring that it enforces the exact coding standards you require.

Using pre-commit is beneficial for both individual developers and teams. For solo developers, it helps maintain discipline and enforces coding standards, making it easier to onboard collaborators in the future. For teams, it streamlines the review process by catching issues before they are submitted for review, reducing the time spent on addressing code inconsistencies and style violations.

Let's take a look at an example. Suppose your project follows the PEP 8 coding standard, and you want to ensure that all code committed to the repository adheres to these guidelines. You can configure pre-commit to run a PEP 8 linter, such as Flake8, before each commit. This way, any code that does not meet the PEP 8 standard will be flagged, and the commit will be blocked until the issues are resolved.

In summary, pre-commit is an invaluable tool for maintaining code quality and consistency in your Python projects. By automating checks before commits, it ensures that your codebase remains clean and adheres to your chosen standards, making your development process more efficient and enjoyable.

Adding pre-commit to your Python project is simple and straightforward. To get started, you'll first need to install the pre-commit package using pip:

```bash
pip install pre-commit
```

Next, create a configuration file named `.pre-commit-config.yaml` in your project's root directory. This file will define the hooks you want to run before each commit. For example, to use Black for code formatting and Flake8 for linting, your configuration file might look like this:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: stable
    hooks:
      - id: black
  - repo: https://github.com/pycqa/flake8
    rev: master
    hooks:
      - id: flake8
```

Once you have set up the configuration file, run the following command to install the pre-commit hooks:

```bash
pre-commit install
```

Now, every time you attempt to make a commit, pre-commit will run the specified hooks. If any issues are found, the commit will be blocked, and you'll be prompted to fix the problems before trying again. To run pre-commit manually on all files in your repository, use the following command:

```bash
pre-commit run --all-files
```

By incorporating pre-commit into your development process, you'll be able to catch and fix issues before they make their way into your codebase, ensuring a consistent and high-quality Python project.

## 🎨 3. Black: auto-formatting for Python

As a developer who has always been particular about coding style, I've had my fair share of discussions on the proper way to indent multiline statements and other formatting nuances. These conversations, although sometimes necessary, can take up valuable time that could be better spent on actual development. That's where Black, the uncompromising code formatter, comes in and saves the day.

Adopting [Black](https://black.readthedocs.io/en/stable/) has made a significant impact on my development workflow. No more unnecessary discussions about formatting preferences; everyone on the team simply follows the rules set forth by Black. This consistency across the codebase not only makes the code more readable but also reduces the time spent on formatting debates.

One of the best aspects of Black is that you don't need to worry about writing perfectly formatted code initially. You can write your code as quickly as you want, even if it's poorly formatted, and then simply run Black to transform it into a beautifully formatted masterpiece. This can be a real time-saver, especially when working on large projects with many contributors.

To install Black, run the following command:

```bash
pip install black
```

You can then format your code by running Black in the terminal:

```bash
black your_file.py
```

Alternatively, you can use the VS Code command palette to run Black on the currently open file. However, the most efficient way to use Black is in combination with pre-commit, as mentioned in the previous section. This way, your code is automatically formatted every time you commit, ensuring a consistent codebase without any extra effort.

In summary, Black is an invaluable tool for enforcing consistent code formatting throughout your Python projects. By adopting it and integrating it with pre-commit, you can save time and focus on what truly matters: writing great code.

## 🚀 4. Ruff: the fastest Python linter and auto-formatter

In the past, I've used several tools to maintain code quality, such as isort, pyupgrade, flake8, and pydocstyle. However, I've recently discovered a powerful new tool called [Ruff](https://beta.ruff.rs/docs/rules/)), an extremely fast Python linter written in Rust. Ruff is not only capable of replacing all these tools but also executes much faster, which significantly improves the development workflow.

Ruff offers an impressive range of features and performance enhancements. Some of its standout features include:

*   10-100x faster than existing linters
*   Over 500 built-in rules
*   Autofix support for automatic error correction
*   Built-in caching to avoid re-analyzing unchanged files
*   First-party editor integrations for VS Code and more

Moreover, Ruff has gained widespread adoption in the Python community and is used in major open-source projects like Apache Airflow, FastAPI, Hugging Face, Pandas, and SciPy. The tool is backed by Astral, which provides active development and support.

One of the best aspects of Ruff is the native VS Code extension, which continuously scans your code and can fix problems as you write. This seamless integration makes it an indispensable part of any Python development workflow.

To install Ruff, simply run the following command:

```bash
pip install ruff
```

To use Ruff in your project, run the following command in the terminal:

```bash
ruff your_file.py
```

For the best experience, I highly recommend using Ruff in conjunction with pre-commit, as mentioned earlier. This ensures that your code is always linted and formatted before committing, maintaining a consistent and high-quality codebase.

In conclusion, Ruff is an incredibly fast and powerful Python linter that streamlines the development process by consolidating multiple tools into a single, efficient package. By adopting Ruff and integrating it with pre-commit, you can enjoy a more productive and enjoyable Python development experience.

{{% callout note %}}
Pro tip: Go extreme, and use `--select ALL` to enable all (>500) rules. This will ensure that your code is always in top shape.
{{% /callout %}}

## 🔍 5. Mypy: static type checking for Python (find bugs before they happen)

As developers, we're always looking for ways to improve the quality of our code and minimize the time spent on debugging. This is where [Mypy](https://mypy.readthedocs.io/en/stable/) comes in. Mypy is a powerful static type checker for Python, designed to catch potential runtime errors before they occur. By using Mypy, you can ensure that your code adheres to type hints and that it runs smoothly without unexpected issues.

Mypy offers several advantages to Python developers, including:

*   Early detection of potential type errors, preventing many common bugs
*   Improved code readability and self-documentation through type annotations
*   Easier refactoring and code maintenance, as type annotations provide clear contracts between functions and modules
*   Better collaboration and communication within teams, since type annotations make the code's intent and expectations more explicit

Adding Mypy to an existing project may initially seem time-consuming and frustrating, as it might flag numerous issues that require attention. However, once you've addressed these concerns and properly set up Mypy, the benefits far outweigh the initial effort. In fact, the time you invest in fixing type-related issues will quickly be recovered as Mypy helps you prevent bugs and reduce debugging time.

For a long time, I too ignored Mypy and only typed my code without actually checking it with the tool. But after truly embracing Mypy and integrating it into my development process, I can confidently say that I will never go back. The value it brings to the table in terms of code quality, readability, and reliability is simply too great to ignore.

By proactively identifying and resolving type-related issues, Mypy not only saves you precious debugging time but also enhances the overall quality of your codebase. As you continue to rely on Mypy, you'll find that it becomes an indispensable part of your Python development toolkit, ensuring that your projects remain robust and maintainable.

To start using Mypy in your project, first install it with the following command:

```bash
pip install mypy
```

Then, you can run Mypy on your Python files by executing the following command in your terminal:

```bash
mypy your_file.py
```

For even better integration, you can add Mypy as a pre-commit hook, ensuring that your code is always checked for type consistency before being committed. This further strengthens the code quality and helps prevent potential runtime errors.

In summary, incorporating Mypy into your Python development workflow adds an extra layer of safety and clarity, making it easier to write high-quality, reliable code. By combining Mypy with other tools like Ruff and pre-commit, you can create a robust development environment that promotes productivity and code quality.

## 🧪 6. Nox and pytest for testing: a powerful combination

When developing software, it's essential to ensure that your code is reliable and functions as expected. The key to achieving this goal is writing thorough tests, which not only help you identify issues early on but also prevent regressions in the future. While it's often tempting to dive headfirst into coding, taking a step back and first writing tests for your solution can lead to more efficient and effective development. Even if this approach doesn't come naturally, it's crucial to write tests for every problem you encounter to keep your codebase stable and reliable.

In the realm of Python testing, [Nox](https://nox.thea.codes/en/stable/) and [pytest](https://docs.pytest.org) stand out as powerful tools that can greatly enhance your testing process. Nox is a versatile automation tool that simplifies running tests in multiple virtual environments, while pytest is a popular and feature-rich testing framework for Python. Together, these tools provide a formidable testing environment that simplifies test management and execution.

In the past, you may have used [Tox](https://tox.wiki/en/latest/), a tool that manages test environments with a text-based configuration file (e.g., in `setup.cfg` or `pyproject.toml`). While Tox has served developers well for many years, including myself, Nox offers a more flexible alternative. Instead of relying on a text-based configuration, Nox takes advantage of a Python configuration file, providing virtually limitless configurability. This added flexibility makes it easy to create complex test matrices with different versions and dependencies, and even accommodate special conditions using simple if statements. After happily using Tox for years, I discovered Nox and found that it elevated my testing workflow to a whole new level.

To get started with Nox and pytest, create a basic `nox.py` file and a sample test file for pytest. Here's an example `nox.py` configuration:

```python
import nox

@nox.session(python=["3.7", "3.8", "3.9"])
def tests(session):
    session.install("-r", "requirements.txt")
    session.install("-r", "test-requirements.txt")
    session.run("pytest")
```

And an example test file for pytest:

```python
import pytest

def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 3 - 1 == 2
```

Beyond basic testing functionality, pytest boasts powerful features such as fixtures, mocking and patching, and parameterization. Pytest fixtures enable you to create reusable resources for your tests, while mocking and patching allow you to replace parts of your system with fake objects, isolating your tests from external dependencies. Parameterization, implemented using `pytest.mark.parametrize`, enables running the same test with multiple sets of inputs and expected outputs.

In conclusion, leveraging Nox and pytest for testing offers numerous advantages for developers who strive to improve code reliability and automate their testing workflows. By harnessing Nox's exceptional configurability and pytest's extensive testing features, you'll establish a robust testing environment that bolsters code quality and ensures optimal performance.

## 🏷️ 7. Versioningit: version management with Git tags

> (Optional, only related when making a Python package)

For developers seeking an automated and customizable package versioning solution, [Versioningit](https://versioningit.readthedocs.io/en/latest/) offers a powerful yet flexible approach. It is a setuptools plugin that automatically determines your package's version based on your version control repository's tags. The real advantage of Versioningit lies in its ability to customize the version format and even override separate functions used for version extraction and calculation.

Versioningit makes your release workflow extremely simple, especially if you have set up an automated build and twine PyPI upload pipeline. To create a new release, you only need to tag a version, and then click on the "Release" button in GitHub.

One of the major advantages of Versioningit is its minimal boilerplate code compared to other tools like [Versioneer](https://github.com/python-versioneer/python-versioneer). Additionally, the Python `__version__` string works seamlessly with editable installs (`pip install -e .`), unlike [setuptools_scm](https://github.com/pypa/setuptools_scm), which is a common issue faced by developers.

Over the years, I have explored many options for package versioning, including [Versioneer](https://github.com/python-versioneer/python-versioneer), [Miniver](https://github.com/jbweston/miniver), [setuptools_scm](https://github.com/pypa/setuptools_scm), [bumpversion](https://github.com/peritus/bumpversion) (or [bump2version](https://github.com/c4urself/bump2version)), and manually setting everything. Versioningit stands out due to its simplicity, customization options, and compatibility with various workflows.

Some key features of Versioningit include:

*   Support for Git, modern Git archives, and Mercurial
*   Customizable version formatting using template strings
*   Optional writing of the final version and other details to a file for loading at runtime
*   Custom setuptools commands for inserting the final version and other details into a source file at build time
*   Customizable functions for VCS querying, tag-to-version calculation, version bumping, version formatting, and writing the version to a file

To use Versioningit in your project, simply add it to your project's `pyproject.toml` file in the `build-system.requires` key. Then, create a `[tool.versioningit]` table in your `pyproject.toml` file. You can get up and running with just the minimal configuration - an empty table.

Once you have a `[tool.versioningit]` table in your `pyproject.toml` and your repository has at least one tag, building your project with `setuptools` will automatically set your project's version based on the latest tag in your Git repository. With Versioningit, you can customize the version format using placeholder strings, making it adaptable to your project's specific needs.

In summary, Versioningit streamlines the package versioning process and simplifies the release workflow. By automating package versioning based on version control repository tags and providing extensive customization options, it helps make the management of package versions more efficient and less error-prone.



## 📝 8. Pyproject.toml and PEP 621: Configuration Consolidation

The `pyproject.toml` file plays a crucial role in consolidating configurations and setup for various tools in a Python project, such as Black, Ruff, Mypy, Versioningit, Nox, and pytest. This adherence to [PEP 621](https://www.python.org/dev/peps/pep-0621/) standards streamlines the development process by providing a single source of truth for multiple tools, eliminating the need for additional configuration files like `setup.cfg` or `setup.py`.

By specifying packaging details directly in the `pyproject.toml` file, you can efficiently manage your project's dependencies and metadata. For example, the Adaptive Scheduler package demonstrates this approach with a comprehensive `pyproject.toml` file containing all the necessary configurations.

<details>
<summary>(click to unfold):</summary>

<!-- CODE:START -->
<!-- import urllib.request -->
<!-- url = 'https://raw.githubusercontent.com/basnijholt/adaptive-scheduler/main/pyproject.toml' -->
<!-- print("```toml") -->
<!-- with urllib.request.urlopen(url) as response: -->
<!--    content = response.read() -->
<!--    print(content.decode('utf-8')) -->
<!-- print("```") -->
<!-- CODE:END -->
<!-- OUTPUT:START -->
<!-- ⚠️ This content is auto-generated by `markdown-code-runner`. -->
```toml
[build-system]
build-backend = "setuptools.build_meta"
requires = ["setuptools", "wheel", "versioningit"]

[project]
name = "adaptive_scheduler"
description = "Run many `adaptive.Learner`s on many cores (>10k) using `mpi4py.futures`, `ipyparallel`, `dask-mpi`, or `process-pool`."
requires-python = ">=3.8"
dynamic = ["version"]
maintainers = [{ name = "Bas Nijholt", email = "bas@nijho.lt" }]
license = { text = "BSD-3" }
classifiers = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: BSD License",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Topic :: Scientific/Engineering",
    "Topic :: System :: Distributed Computing",
]
dependencies = [
    "adaptive >= 0.14.1",
    "cloudpickle",
    "dill",
    "ipyparallel",
    "ipywidgets",
    "itables",
    "jinja2",
    "loky",
    "numpy",
    "pandas",
    "psutil",
    "pyarrow",
    "pyzmq",
    "rich",
    "structlog",
    "tinydb",
    "toolz",
    "tqdm",
    "versioningit",
]
[project.optional-dependencies]
all = ["dask-mpi", "mpi4py"]
test = ["pytest", "pytest-asyncio", "coverage", "pytest-cov"]
docs = [
    "myst-nb",
    "sphinx_fontawesome",
    "sphinx",
    "furo",
    "myst-parser",
    "emoji",
]
[project.urls]
homepage = "https://adaptive-scheduler.readthedocs.io/"
documentation = "https://adaptive-scheduler.readthedocs.io/"
repository = "https://github.com/basnijholt/adaptive-scheduler"

[project.readme]
content-type = "text/x-rst"
file = "README.rst"

[project.scripts]
adaptive-scheduler-launcher = "adaptive_scheduler._server_support.launcher:main"

[tool.versioningit]

[tool.versioningit.onbuild]
build-file = "adaptive_scheduler/_version.py"
source-file = "adaptive_scheduler/_version.py"

[tool.setuptools.packages.find]
include = ["adaptive_scheduler.*", "adaptive_scheduler"]

[tool.pytest.ini_options]
addopts = """
    -vvv
    --cov=adaptive_scheduler
    --cov-report term
    --cov-report html
    --cov-report xml
    --cov-fail-under=35
    --asyncio-mode=auto
"""

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]

[tool.black]
line_length = 88

[tool.ruff]
line-length = 150
target-version = "py38"
select = ["ALL"]
ignore = [
    "T20",     # flake8-print
    "ANN101",  # Missing type annotation for {name} in method
    "S101",    # Use of assert detected
    "PD901",   # df is a bad variable name. Be kinder to your future self.
    "ANN401",  # Dynamically typed expressions (typing.Any) are disallowed in {name}
    "D402",    # First line should not be the function's signature
    "PLW0603", # Using the global statement to update `X` is discouraged
    "D401",    # First line of docstring should be in imperative mood
    "SLF001",  # Private member accessed
]

[tool.ruff.per-file-ignores]
"tests/*" = ["SLF001"]
"tests/test_examples.py" = ["E501"]
".github/*" = ["INP001"]

[tool.ruff.mccabe]
max-complexity = 18

[tool.mypy]
python_version = "3.8"

```

<!-- OUTPUT:END -->

</details>

(from [here](https://github.com/basnijholt/adaptive-scheduler/blob/main/pyproject.toml))

As seen in the example, the `pyproject.toml` file includes details about the build system, project metadata, dependencies, optional dependencies, URLs, and configurations for various tools such as Versioningit, setuptools, pytest, coverage, Black, Ruff, and Mypy. By consolidating these configurations, you can maintain a more organized and maintainable project, making it easier to understand and update settings for different tools.

In summary, the `pyproject.toml` file and adherence to PEP 621 provide a unified approach to configuring and setting up your Python project, making it easier to manage dependencies, metadata, and tool-specific settings. This streamlined process ultimately leads to a more efficient and maintainable development workflow.

## 🌐 9. GitHub Actions CI Matrix: Testing on Multiple Platforms and Auto Publishing to PyPI

[GitHub Actions](https://docs.github.com/en/actions/learn-github-actions) is an excellent tool for automating workflows and improving code quality through continuous integration (CI). By using a CI matrix, you can test your code on multiple platforms and Python versions, ensuring that your package remains compatible and stable across different environments.

To set up a `.github/workflows/nox.yaml` file for GitHub Actions, you can use the following simplified example:

```yaml
name: nox

on:
  pull_request:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.platform }}
    strategy:
      fail-fast: false
      matrix:
        platform: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.8", "3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: pip install nox
    - name: Test with nox
      run: nox -e py${{ matrix.python-version }}
```

This configuration file specifies the platforms and Python versions for testing, as well as the steps to set up the environment, install dependencies, and run tests using nox.
With this simple configuration, you set up tests on MacOS, Windows, Linux, and multiple Python versions, ensuring that your package remains compatible across different environments.

Another essential part of the CI/CD process is deploying your Python package. You can use the `.github/workflows/publish-package.yaml` file to automate the package deployment to PyPI whenever a new release is published:

```yaml
name: Upload Python Package

on:
  release:
    types: [published]

jobs:
  deploy:

    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install setuptools wheel twine build
    - name: Build and publish
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
      run: |
        python -m build
        twine upload dist/*
```

This workflow sets up Python, installs necessary dependencies, builds the package, and publishes it to PyPI using Twine. The process integrates seamlessly with versioningit, ensuring that the published package has the correct version number based on the git history.

In summary, leveraging GitHub Actions for continuous integration and automated workflows enhances code quality and reliability, while also simplifying the development and deployment processes. By testing across various platforms and Python versions, and automating package deployment, you can be confident that your package is well-maintained and accessible to users.

## 📚 10. Read the Docs, Sphinx, MyST-NB, and Jupytext notebooks for documentation

Documentation is crucial for any software project, as it helps users understand how to use the package and provides guidance for contributors. [Read the Docs](https://readthedocs.org/), [Sphinx](https://www.sphinx-doc.org/), [MyST-NB](https://myst-nb.readthedocs.io/en/latest/), and [Jupytext notebooks](https://jupytext.readthedocs.io/en/latest/) are powerful tools that, when combined, facilitate the creation and maintenance of high-quality documentation.

tl;dr: check out the [Adaptive documentation](https://adaptive.readthedocs.io/) for an example of how to use these tools to create a comprehensive documentation website.

[**Read the Docs**](https://readthedocs.org/) is a documentation hosting platform that automatically builds, version controls, and hosts your documentation for free. It integrates well with Sphinx and GitHub, allowing your documentation to be updated whenever you push changes to your repository.

[**Sphinx**](https://www.sphinx-doc.org/) is a documentation generator that can transform reStructuredText files, MyST files, or Jupyter notebooks into various output formats, such as HTML, LaTeX, or PDF. It is highly extensible, supporting custom themes and plugins, and can automatically generate API documentation from your Python code.

[**MyST-NB**](https://myst-nb.readthedocs.io/en/latest/) is an extension to Sphinx that enables it to parse Jupyter notebooks and execute the code cells during the build process. It uses the MyST (short for Markedly Structured Text) markdown parser, which adds support for Sphinx roles and directives, making it a powerful alternative to reStructuredText.

[**Jupytext notebooks**](https://jupytext.readthedocs.io/en/latest/) is a Jupyter extension that enables you to save Jupyter notebooks in Markdown format (or other text-based formats) instead of the default JSON format. By using Jupytext notebooks, you can store your code, explanations, and visualizations as plain text, which is easier to version control and can be seamlessly integrated with MyST-NB and Sphinx.

With [MyST-NB](https://myst-nb.readthedocs.io/en/latest/) and [Jupytext](https://jupytext.readthedocs.io/en/latest/), you can write your documentation using Jupyter notebooks in Markdown format. This approach combines the benefits of Jupyter notebooks, such as interactive code execution and rich output, with the simplicity of Markdown and the powerful features of Sphinx. The result is a highly readable, user-friendly, and maintainable documentation that caters to both users and developers.

To get started with MyST-NB, you'll need to install it using pip:
```bash
pip install myst-nb
```

Next, configure your Sphinx project to use MyST-NB by adding the following lines to your `conf.py` file:

```python
extensions = [
    "myst_nb",
]
```

Now, Sphinx will be able to parse and execute your Jupyter notebooks during the documentation build process, integrating them seamlessly with your existing documentation.

In summary, using Read the Docs, Sphinx, MyST-NB, and Jupytext notebooks for your documentation enables you to create high-quality, interactive, and easily maintainable documentation that benefits your project's users and contributors. This combination of tools ensures that your documentation remains up-to-date, easily navigable, and engaging, ultimately enhancing the overall experience for your project's audience.

For a full example, see how I setup [Adaptive's documentation](https://adaptive.readthedocs.io/en/latest/) using Sphinx, MyST-NB, and Jupytext notebooks. [`readthedocs.yaml`](https://github.com/python-adaptive/adaptive/blob/1b0f15e44235643731c56d335f6711c5584d4828/readthedocs.yml), [`docs/source/conf.py`](https://github.com/python-adaptive/adaptive/blob/1b0f15e44235643731c56d335f6711c5584d4828/docs/source/conf.py), and here is an example notebook that is used in the [documentation](https://adaptive.readthedocs.io/en/latest/tutorial/tutorial.Learner1D.html): [`docs/source/tutorial/tutorial.Learner1D.md`](https://github.com/python-adaptive/adaptive/blob/main/docs/source/tutorial/tutorial.Learner1D.md)


## 🎉 11. Conclusion

In conclusion, incorporating these powerful tools into your Python development workflow can significantly enhance your productivity and code quality. By adopting [pre-commit](https://pre-commit.com/), [Black](https://black.readthedocs.io/en/stable/), [Ruff](https://beta.ruff.rs/docs/rules/), [Mypy](https://mypy.readthedocs.io/en/stable/), [Versioningit](https://versioningit.readthedocs.io/en/latest/), [Pyproject.toml with PEP 621](https://www.python.org/dev/peps/pep-0621/), [Nox](https://nox.thea.codes/en/stable/), [pytest](https://docs.pytest.org/), [GitHub Actions CI matrix](https://docs.github.com/en/actions/learn-github-actions), and [Read the Docs](https://readthedocs.org/), [Sphinx](https://www.sphinx-doc.org/), [MyST-NB](https://myst-nb.readthedocs.io/en/latest/), and [Jupytext notebooks](https://jupytext.readthedocs.io/en/latest/) for documentation, you create a streamlined, efficient, and reliable development environment.

These tools help maintain code consistency, catch issues early, automate package versioning, simplify testing, consolidate configurations, and create high-quality documentation. By integrating them into your projects, you can focus on writing great code while ensuring that your work remains robust, maintainable, and accessible to users and contributors alike.

Don't hesitate to explore these tools and incorporate them into your Python development toolkit. They can transform your development experience, making it more enjoyable and efficient, ultimately leading to higher-quality projects and happier developers. Happy coding!
