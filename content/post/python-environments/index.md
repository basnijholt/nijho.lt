---
title: "🐍 Python Environment Jungle: Finding My Perfect Workflow 🌴"
subtitle: A Personal Journey Through Pyenv, Pipenv, venv, Virtualenv, Homebrew, Anaconda, Miniconda, Micromamba, Pixi, and uv
summary: A Personal Journey Through Pyenv, Pipenv, venv, Virtualenv, Homebrew, Anaconda, Miniconda, Micromamba, Pixi, and uv
projects: []
date: "2025-01-03T00:00:00Z"
draft: false
featured: false

authors:
  - admin

tags:
  - python
  - conda
  - mamba
  - micromamba
  - pipenv
  - docker
  - nb_conda_kernels
  - pyenv
  - venv
  - virtualenv
  - homebrew
  - pixi
  - uv

categories:
  - setup
  - level:beginner
---

## 1. Introduction 🚀

Like many Python developers, I've spent considerable time trying different environment management tools to find what works best for me.

After exploring various options from virtualenv to Conda, I found that Conda-based solutions fit my needs well - mainly because they handle non-Python dependencies without much hassle.

While Conda itself can be slow when setting up environments, tools like Mamba and Pixi provide the same functionality with better performance.

In this post, I'll share my experience with different Python environment tools and provide practical commands for setting up Python environments.

{{% callout note %}}
TL;DR, I use `micromamba` for projects with non-Python dependencies and `uv` for projects without them.
This approach works well for me, you own mileage may vary.
{{% /callout %}}

{{< toc >}}

## 2. The Alternatives 🌟

Before we start look at this comparison tables for the most popular Python environment management tools.

_I had to split the tables into two because of the number of columns._

**_Table 1: Python Environment Management Tools_**

| Tool                                                                            | Key Features                  | Native/3rd Party | Non-Python Deps |
| ------------------------------------------------------------------------------- | ----------------------------- | ---------------- | --------------- |
| [Pyenv](https://github.com/pyenv/pyenv)                                         | Python version management     | 3rd Party        | ❌              |
| [Pipenv](https://pipenv.pypa.io/en/latest/)                                     | Package & env management      | 3rd Party        | ❌              |
| [Conda](https://docs.conda.io/en/latest/)                                       | Package & env management      | 3rd Party        | ✅              |
| [Mamba](https://mamba.readthedocs.io/en/latest/)                                | Fast Conda replacement        | 3rd Party        | ✅              |
| [Micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html) | Lightweight Mamba             | 3rd Party        | ✅              |
| [Docker](https://www.docker.com/)                                               | Containerization              | 3rd Party        | ✅              |
| [Venv](https://docs.python.org/3/library/venv.html)                             | Built-in env management       | Native           | ❌              |
| [Virtualenv](https://virtualenv.pypa.io/en/latest/)                             | Env management (pre-3.3)      | 3rd Party        | ❌              |
| [Homebrew](https://brew.sh/)                                                    | macOS/Linux package manager   | 3rd Party        | ✅              |
| [Pixi](https://prefix.dev/docs/pixi/overview)                                   | Fast Conda alternative        | 3rd Party        | ✅              |
| [uv](https://github.com/astral-sh/uv)                                           | Fast pip and venv replacement | 3rd Party        | ❌              |
| System Package Managers                                                         | OS-based package management   | Native           | ✅              |

**_Table 2: Python Environment Management Tools_**

| Tool                                                                            | Ease of Use | Isolation | Cross-Platform Support | Community & Support | Performance |
| ------------------------------------------------------------------------------- | ----------- | --------- | ---------------------- | ------------------- | ----------- |
| [Pyenv](https://github.com/pyenv/pyenv)                                         | Medium      | ✅        | Windows, macOS, Linux  | Good                | Good        |
| [Pipenv](https://pipenv.pypa.io/en/latest/)                                     | Easy        | ✅        | Windows, macOS, Linux  | Good                | Good        |
| [Conda](https://docs.conda.io/en/latest/)                                       | Easy        | ✅        | Windows, macOS, Linux  | Excellent           | Average     |
| [Mamba](https://mamba.readthedocs.io/en/latest/)                                | Easy        | ✅        | Windows, macOS, Linux  | Growing             | Fast        |
| [Micromamba](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html) | Medium      | ✅        | Windows, macOS, Linux  | Growing             | Fast        |
| [Docker](https://www.docker.com/)                                               | Hard        | ✅        | Windows, macOS, Linux  | Excellent           | Good        |
| [Venv](https://docs.python.org/3/library/venv.html)                             | Easy        | ✅        | Windows, macOS, Linux  | Excellent           | Good        |
| [Virtualenv](https://virtualenv.pypa.io/en/latest/)                             | Medium      | ✅        | Windows, macOS, Linux  | Good                | Good        |
| [Homebrew](https://brew.sh/)                                                    | Easy        | ❌        | macOS, Linux           | Excellent           | Good        |
| [Pixi](https://prefix.dev/docs/pixi/overview)                                   | Easy        | ✅        | Windows, macOS, Linux  | Growing             | Fast        |
| [uv](https://github.com/astral-sh/uv)                                           | Easy        | ✅        | Windows, macOS, Linux  | Growing             | Very Fast   |
| System Package Managers                                                         | Easy        | ❌        | Depends on OS          | Depends on OS       | Good        |

Now that we've seen the alternatives, let's dive into setting up environments with the help of Conda and Mamba.

### 🐍 Pyenv

A popular tool that enables you to easily manage multiple Python versions on a single system.
It allows you to switch between different Python versions without interfering with system-level installations.

**_Setup Instructions_**

1.  Install pyenv:

    - macOS: `brew install pyenv`
    - Ubuntu: `curl https://pyenv.run | bash`

2.  Add the following lines to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`):

    ```bash
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    ```

3.  Restart your shell or run `source ~/.bashrc` (or `source ~/.zshrc`)
4.  Install a specific Python version: `pyenv install 3.8.5`
5.  Set the Python version for your project: `pyenv local 3.8.5`

### 📦 Pipenv

A package management and virtual environment management tool that combines the functionality of pip and virtualenv.
It streamlines the process of installing and managing packages within isolated environments.

**_Setup Instructions_**

1. Install pipenv: `pip install --user pipenv`
2. Change to your project directory: `cd my_project`
3. Initialize a new virtual environment: `pipenv --python 3.8`
4. Install packages: `pipenv install <package_name>`
5. Activate the environment: `pipenv shell`

### 🌐 Conda

A cross-platform package manager and environment management tool, often used in conjunction with Anaconda and Miniconda.
Conda simplifies the installation and management of packages and dependencies, especially for data science and machine learning projects.

**_Setup Instructions_**

1. Download and install Miniconda: https://github.com/conda-forge/miniforge#miniforge3
2. Create a new environment: `conda create --name my_env python=3.8`
3. Activate the environment: `conda activate my_env`
4. Install packages: `conda install <package_name>`

### 🚀 Mamba

Mamba is a fast, drop-in replacement for Conda, designed to resolve and install packages more quickly.
It uses the same Conda repositories and environment files, making it easy to switch between the two.

**_Setup Instructions_**

1.  Install Mambaforge with Mamba pre-installed:

    Download and install Mambaforge with Mamba for your platform: https://github.com/conda-forge/miniforge#mambaforge

    Alternatively, you can install Mamba within an existing Conda environment:

    ```
    conda install -c conda-forge mamba
    ```

2.  Create a new environment with Mamba:

    ```bash
    mamba create --name my_env python=3.8
    ```

3.  Activate the environment:

    ```bash
    mamba activate my_env
    ```

4.  Install packages using Mamba:

    ```bash
    mamba install <package_name> -c conda-forge
    ```

By using Mamba instead of Conda, you can significantly speed up environment resolution and package installation while still benefiting from the Conda ecosystem.

### 🌌 Micromamba

Micromamba is a lightweight and fast alternative to the Mamba package manager.
It is a statically linked C++ executable that doesn't require a base environment or come with a default Python version.
It supports a subset of Mamba and Conda commands and is designed to resolve and install packages quickly.
For those who need Conda features, you can install Conda using Micromamba with `micromamba install conda`.

**_Setup Instructions_**

1.  Download the appropriate Micromamba binary for your platform from [the official repository](https://github.com/mamba-org/mamba/releases).
2.  Make the binary executable and move it to a directory in your `PATH`:
    ```bash
    chmod +x micromamba mv micromamba /usr/local/bin/
    ```
3.  Create a new environment with Micromamba:
    ```bash
    micromamba create -n my_env python -c conda-forge
    ```
4.  Activate the environment:
    ```bash
    micromamba activate my_env
    ```
5.  Install packages using Micromamba:
    ```bash
    micromamba install <package_name> -c conda-forge
    ```
6.  If you need Conda's features, you can install Conda within your Micromamba environment:
    ```bash
    micromamba install conda
    ```

For example, if you need nb_conda_kernels to use your Micromamba environment in JupyterLab:

```bash
micromamba install conda nb_conda_kernels
```

And you are set up!

Micromamba is the perfect solution for those who want a fast and lightweight package manager while still being able to access Conda's features when needed.

### 🐳 Docker

A containerization platform that allows you to create lightweight, portable environments called containers.
With Docker, you can package your Python application along with its dependencies, ensuring consistent execution across different systems.

**_Setup Instructions_**

1.  Install Docker: https://docs.docker.com/get-docker/
2.  Create a `Dockerfile` in your project directory with the following contents:
    ```bash
    FROM python:3.11
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    COPY . .
    CMD ["python", "your_script.py"]
    ```
3.  Build the Docker image: `docker build -t my_project .`
4.  Run the Docker container: `docker run my_project`

### 🏞️ Venv

A built-in Python module available since Python 3.3, which allows you to create lightweight virtual environments.
Venv simplifies the process of creating isolated environments for different projects, ensuring that package dependencies don't conflict with each other.

**_Setup Instructions_**

1.  Create a new virtual environment: `python3 -m venv my_env`
2.  Activate the environment:
    - macOS/Linux: `source my_env/bin/activate`
    - Windows: `my_envScriptsactivate`
3.  Install packages: `pip install <package_name>`

### 🌐 Virtualenv

Virtualenv is a third-party Python environment management tool that predates the built-in `venv` module. It allows you to create isolated environments for different projects, ensuring that package dependencies don't conflict with each other. Virtualenv is compatible with Python 2.7 and later versions, whereas `venv` is only available since Python 3.3.

**_Setup Instructions_**

1.  Install virtualenv: `pip install virtualenv`
2.  Create a new virtual environment: `virtualenv my_env`
3.  Activate the environment:
    - macOS/Linux: `source my_env/bin/activate`
    - Windows: `my_env\Scripts\activate`
4.  Install packages: `pip install <package_name>`

### 🍺 Homebrew

Homebrew is a popular package manager for macOS and Linux that simplifies the installation and management of software. Though it is not a dedicated Python environment management tool, it does offer support for installing and managing multiple Python versions alongside other software.

Homebrew can be useful for installing and managing Python versions for system-level usage, but it's not the best choice for managing isolated project-specific dependencies. For project-specific dependency management, it's recommended to use other tools like venv, virtualenv, or Conda in conjunction with Homebrew-installed Python.

**_Setup Instructions_**

1.  Install Homebrew (if not already installed):
    - macOS: Follow the instructions at [https://brew.sh](https://brew.sh/)
    - Linux: Follow the instructions at [https://docs.brew.sh/Homebrew-on-Linux](https://docs.brew.sh/Homebrew-on-Linux)
2.  Install a specific Python version:
    ```bash
    brew install python@3.11
    ```
3.  Add the installed Python version to your `PATH` by adding the following line to your shell configuration file (e.g., `~/.bashrc`, `~/.zshrc`):
    ```bash
    export PATH="/usr/local/opt/python@3.11/bin:$PATH"
    ```
4.  Restart your shell or run `source ~/.bashrc` (or `source ~/.zshrc`) to apply the changes.
5.  Verify the Python version: `python3.11 --version`

Keep in mind that Homebrew is mainly for installing and managing software at the system level. To manage project-specific dependencies and create isolated environments, combine Homebrew with other tools like venv or virtualenv for better dependency management.

### 💻 System package managers

Some operating systems have their own package managers (e.g., apt for Ubuntu, pacman for Arch Linux, or Homebrew for macOS) that can be used to install and manage Python environments.
However, using system package managers may lead to conflicts with other system packages and is generally not recommended for managing project-specific dependencies.

I will skip the setup instructions for this one, as it is just not recommended to do this!

### 🌟 Pixi

Pixi is a new package manager built in Rust that uses Conda-forge packages but aims to be significantly faster and simpler than Conda.
It's developed by prefix.dev (the team behind Mamba) and focuses on providing a more streamlined experience.
It is inspired by tools like Cargo, nix, and npm and aims to provide a modern package management experience for Python developers.

**_Setup Instructions_**

1.  Install pixi following instructions at [prefix.dev](https://prefix.dev/docs/pixi/installation)
2.  Initialize a new project:
    ```bash
    pixi init my-project
    cd my-project
    ```
3.  Add dependencies:
    ```bash
    pixi add python numpy pandas
    ```
4.  Run Python in the environment:
    ```bash
    pixi run python
    ```
5.  Create and run tasks (defined in pixi.toml):

    ```bash
    # Add a task
    pixi task add hello "python hello_world.py"

    # Run the task
    pixi run hello
    ```

6.  Start an interactive shell in the environment:
    ```bash
    pixi shell
    ```

Pixi can also be used as a global installation tool:

```bash
# Install tools globally
pixi global install starship
pixi global install fish

# Create a named environment with multiple packages
pixi global install --environment data-science-env \
    --expose python --expose jupyter \
    python jupyter numpy pandas
```

Key features:

- Fast package resolution and installation
- Uses Conda-forge packages
- Built-in task runner
- Global package installation support
- GitHub Actions integration with automatic caching
- Simple and intuitive CLI

### ⚡ uv

uv is an extremely fast Python package installer and resolver written in Rust.
It can be used as a drop-in replacement for pip and can generate virtual environments.
While it is quite new it is already being used by many developers due to its speed and ease of use.
Besides being fast, it is awesome because it is a single binary that can be used to also bootstrap Python itself.

**_Setup Instructions_**

1.  [Install uv](https://docs.astral.sh/uv/getting-started/installation/):
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  Create a new virtual environment:
    ```bash
    uv venv
    ```
3.  Activate the environment:
    - Unix/macOS: `source .venv/bin/activate`
    - Windows: `.venv\Scripts\activate`
4.  Install packages (much faster than pip):
    ```bash
    uv pip install numpy pandas
    ```

It will automatically maintain a `uv.lock` file to ensure deterministic builds.
Install this lock file with `uv sync`.

Key features of uv:

- Up to 10x faster than pip
- Built-in virtual environment support
- Compatible with pip's CLI interface
- Global package caching
- Deterministic builds

There is much more to uv, so check out the [documentation](https://docs.astral.sh/uv/) for more details.

## 3. Conclusion 🏁

The choice you make for managing your Python environments ultimately depends on your use case.
If you don't have to frequently deal with non-Python dependencies, I would recommend using `uv` for its speed and simplicity.
However, because I often work with projects that require non-Python dependencies, I've found that Micromamba is the perfect fit for me.

That being said, each tool has its own strengths and weaknesses, and it's important to choose the one that works best for your specific needs.
I hope this journey through Python environment management has been helpful and informative.
Good luck in finding your perfect Python environment workflow! 🐍

## 4. Further Reading 📚

Here are some resources for further exploration:

- [**Pyenv**](https://github.com/pyenv/pyenv): Pyenv GitHub repository and documentation
- [**Pipenv**](https://pipenv.pypa.io/en/latest/): Pipenv documentation
- [**Conda**](https://docs.conda.io/en/latest/): Conda documentation
- [**Mamba**](https://mamba.readthedocs.io/en/latest/): Mamba documentation
- [**Micromamba**](https://mamba.readthedocs.io/en/latest/user_guide/micromamba.html): Micromamba documentation
- [**venv**](https://docs.python.org/3/library/venv.html): venv documentation
- [**virtualenv**](https://virtualenv.pypa.io/en/latest/): virtualenv documentation
- [**Anaconda**](https://www.anaconda.com/): Anaconda homepage
- [**Miniconda**](https://docs.conda.io/en/latest/miniconda.html): Miniconda documentation
- [**Homebrew**](https://brew.sh/): Homebrew homepage
- [**Pixi**](https://prefix.dev/docs/pixi/overview): Pixi documentation
- [**uv**](https://docs.astral.sh/uv/): uv documentation
