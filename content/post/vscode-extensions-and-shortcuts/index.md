---
title: ⚡ VSCode Setup and Most Used Keystrokes for Turbocharged (Mostly Python) Development 🐍
subtitle: My personal setup for maximal productivity and minimal keystrokes.
summary: My personal setup for maximal productivity and minimal keystrokes.
projects: []
date: '2023-04-16T00:00:00Z'
draft: false
featured: false

image:
  caption: 'My favorite extensions'
  focal_point: ''
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  - vscode
  - vscode-extension
  - editor
  - ide

categories:
  - editor
  - level:beginner
---

Visual Studio Code, or VSCode, has rapidly become one of the most popular code editors available today, and for good reason. With a vast amount of development activity behind it, VSCode is a powerful and extensible platform that allows users to customize it to their needs through a wide variety of extensions. As a long-time Sublime Text user, I was initially skeptical about making the switch due to concerns about performance. However, as I spent more time using VSCode, I became convinced of its many benefits and have since made it my go-to editor for all my development needs, particularly for Python.

In this blog post, I will share my personal setup for turbocharging Python development in VSCode, including my favorite extensions and most-used keystrokes. By tailoring your editor to your specific requirements and preferences, you can maximize productivity and minimize keystrokes, making your development experience as smooth and efficient as possible.

{{< toc >}}

## My most common Shortcuts

Personally, I use the Sublime Keymap extension to add Sublime Text keybindings to VSCode.

It is a valuable extension for those who are transitioning from Sublime Text to Visual Studio Code or simply prefer Sublime Text's keybindings.
This extension replicates Sublime Text's keyboard shortcuts in VSCode, allowing you to maintain your productivity and muscle memory.

Here are ***my*** commonly used shortcuts when using the Sublime Keymap extension and the default VSCode keybindings (if missing both are the same):

| Keybinding (Sublime)                                       | Keybinding (VS Code)                                       | Description                                                                                                                                                             |
| ---------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Command + Shift + L (Mac) / Ctrl + Shift + L (Windows)** | **Shift + Alt + L**                                        | Place a cursor at the end of all selected lines                                                                                                                         |
| **Command + D (Mac) / Ctrl + D (Windows)**                 | *same*                                                     | Select the next occurrence of the current word                                                                                                                          |
| **Command + U (Mac) / Ctrl + U (Windows)**                 | *same*                                                     | Undo the last "select next word" operation                                                                                                                              |
| **Alt + up/down arrow**                                    | *same*                                                     | Move the selected lines up or down                                                                                                                                      |
| **Alt + Shift + up/down arrows**                           | *same*                                                     | Duplicate the selected lines above or below                                                                                                                             |
| **Control + - (minus)**                                    | *same*                                                     | Navigate to the previous location in the editor                                                                                                                         |
| **Command + Shift + P (Mac) / Ctrl + Shift + P (Windows)** | *same*                                                     | Open the command palette                                                                                                                                                |
| **Command + R (Mac) / Ctrl + R (Windows)**                 | **Command + Shift + O (Mac) / Ctrl + Shift + O (Windows)** | Open the command palette and search for definitions in the file                         (bonus, add a `:`, to get `@:` to group by functions, methods, variables, etc.) |
| **Command + T (Mac) / Ctrl + T (Windows)**                 | **Command + P (Mac) / Control + P (Windows)**              | Browse files in the workspace                                                                                                                                           |
| **Command + B (Mac) / Ctrl + B (Windows)**                 | *same*                                                     | Toggle the visibility of the sidebar (explorer, search, etc.)                                                                                                           |
| **Command + Shift + F (Mac) / Ctrl + Shift + F (Windows)** | *same*                                                     | Search across all files in your workspace                                                                                                                               |
| **Command + Shift + E (Mac) / Ctrl + Shift + E (Windows)** | *same*                                                     | Open the file explorer                                                                                                                                                  |
| **Control + Space**                                        | *same*                                                     | Open the autocomplete menu                                                                                                                                              |
| **Command + Mouse click**                                  | *same*                                                     | Go to the definition of the selected word (when using the Python extension (see below))                                                                                 |
| **Command + I**                                            | *same*                                                     | Open GitHub Copilot prompt inline                                                                                                                                       |
| **Command + Shift + I**                                    | *same*                                                     | Open GitHub Copilot prompt in side bar                                                                                                                                  |
| **Shift + Alt + F**                                        | *same*                                                     | Autoformat                                                                                                                                                              |
| **Command + Control + G**                                  | **Command + Shift + L (Mac) / Ctrl + Shift + L (Windows)** | Select all occurrences of current word                                                                                                                                  |

## My favorite extensions

I have ranked my top 8 extensions, which I would recommend to anyone who is looking to improve their productivity and efficiency in VSCode.

### 1. GitHub Copilot

GitHub Copilot is an AI-powered code completion extension that provides seamless integration with the Copilot service, helping you write code faster and smarter.

- Use `code --install-extension GitHub.copilot` to install the GitHub Copilot extension [(docs)](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)

![](https://user-images.githubusercontent.com/37570492/212964557-8d832278-61bb-4288-a8a7-47f35859e868.gif)

### 2. GitLens

GitLens supercharges the built-in Git support in VSCode, providing useful insights into your code history and changes, including advanced blame annotations, code lens, and more.

- Use `code --install-extension eamodio.gitlens` to install the GitLens extension [(docs)](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)

![](https://raw.githubusercontent.com/gitkraken/vscode-gitlens/633fc030f6f6b372d6d487c2bd35a8346507f0b2/images/docs/revision-navigation.gif)

### 3. Python and Pylance

These extensions offer comprehensive support for Python development, with features like IntelliSense, linting, debugging, and code navigation. Pylance enhances Python support with improved code completion, type checking, and language features.

- Use `code --install-extension ms-python.python` to install the Python extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- Use `code --install-extension ms-python.vscode-pylance` to install the Pylance extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)

![](https://raw.githubusercontent.com/microsoft/vscode-python/d905cf0555e0032cfe10a2af2b925e686246e30e/images/InterpreterSelectionZoom.gif)
![](https://github.com/microsoft/pylance-release/raw/77c8d25c51376faa488e69b8fb670ddc64c5bb3e/images/all-features.gif)

### 4. Jupyter

The Jupyter extensions enable you to work with Jupyter Notebooks in VSCode, with support for running cells, debugging, and more. Jupyter Keymap adds customizable keyboard shortcuts for Jupyter commands.

- Use `code --install-extension ms-toolsai.jupyter` to install the Jupyter extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
![](https://github.com/Microsoft/vscode-jupyter/raw/e3eee370c97505ce390858a4645f73bc1b3912fc/images/Jupyter%20README/notebookui.png)

### 5. Sublime Keybindings

Sublime Keybindings adds keybindings from Sublime Text to VSCode, making it easier for developers familiar with Sublime Text to transition to VSCode.

- Use `code --install-extension ms-vscode.sublime-keybindings` to install the Sublime Keybindings extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode.sublime-keybindings)

### 6. Remote Containers, SSH, and Remote Extension Pack

These extensions provide support for working with remote development environments in VSCode, such as developing inside a container or connecting to remote machines via SSH. The Extension Pack bundles all the remote development extensions for convenience.

- Use `code --install-extension ms-vscode-remote.remote-ssh-edit` to install the Remote SSH Edit extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-ssh-edit)
- Use `code --install-extension ms-vscode-remote.vscode-remote-extensionpack` to install the Remote Extension Pack [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack)
- Use `code --install-extension ms-vscode.remote-explorer` to install the Remote Explorer extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode.remote-explorer)
- Use `code --install-extension ms-vscode.remote-repositories` to install the Remote Repositories extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode.remote-repositories)

![](https://microsoft.github.io/vscode-remote-release/images/remote-containers-readme.gif)

### 7. Indent Rainbow

Indent Rainbow is a VSCode extension that colorizes indentation levels in your code, making it easier to visualize and navigate complex code structures.

- Use `code --install-extension oderwat.indent-rainbow` to install the Indent Rainbow extension [(docs)](https://marketplace.visualstudio.com/items?itemName=oderwat.indent-rainbow)

![](https://raw.githubusercontent.com/oderwat/vscode-indent-rainbow/913f5a704b54730a5cea5a4de97e245fcd8c8596/assets/example.png)


### 8. Code Spell Checker

Code Spell Checker is a helpful extension that checks your code and comments for spelling errors, helping you maintain clean and professional code.

- Use `code --install-extension streetsidesoftware.code-spell-checker` to install the Code Spell Checker extension [(docs)](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)

![](https://raw.githubusercontent.com/streetsidesoftware/vscode-spell-checker/main/images/example.gif)

### Ruff

Ruff is a Visual Studio Code extension that provides support for the Ruff linter, an extremely fast Python linter written in Rust. It offers numerous features such as built-in caching, autofix support, and a comprehensive set of built-in rules. Ruff aims to replace multiple tools like Flake8, isort, pydocstyle, yesqa, eradicate, pyupgrade, and autoflake, while executing much faster than any individual tool.

- Use `code --install-extension charliermarsh.ruff` to install the Ruff extension [(docs)](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)

![](https://user-images.githubusercontent.com/1309177/205176932-44cfc03a-120f-4bad-b710-612bdd7765d6.gif)
![](https://user-images.githubusercontent.com/1309177/205175987-82e23e21-14bb-467d-9ef0-027f24b75865.gif)

### GitHub Copilot Labs

GitHub Copilot Labs is an extension that allows users to access experimental features for GitHub Copilot, an AI-powered code completion tool.

- Use `code --install-extension GitHub.copilot-labs` to install the GitHub Copilot Labs extension [(docs)](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-labs)

![](https://user-images.githubusercontent.com/8978670/160909091-70c1d70c-2850-4483-91ed-4de87efe5285.gif)

### GitHub Codespaces, RemoteHub, and Pull Request

These GitHub extensions provide seamless integration with various GitHub services, including Codespaces (cloud-based development environments), RemoteHub (browse remote repositories), and Pull Request management.

- Use `code --install-extension GitHub.codespaces` to install the GitHub Codespaces extension [(docs)](https://marketplace.visualstudio.com/items?itemName=GitHub.codespaces)
- Use `code --install-extension GitHub.remotehub` to install the GitHub RemoteHub extension [(docs)](https://marketplace.visualstudio.com/items?itemName=GitHub.remotehub)
- Use `code --install-extension GitHub.vscode-pull-request-github` to install the GitHub Pull Request extension [(docs)](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-pull-request-github)

![](https://github.com/Microsoft/vscode-pull-request-github/raw/HEAD/.readme/demo.gif)

### Rainbow CSV

Rainbow CSV adds syntax highlighting for CSV and TSV files in VSCode, making it easier to read and analyze data by color-coding columns.

- Use `code --install-extension mechatroner.rainbow-csv` to install the Rainbow CSV extension [(docs)](https://marketplace.visualstudio.com/items?itemName=mechatroner.rainbow-csv)

![](https://i.imgur.com/ryjBI1R.png)

### Better Comments

Better Comments is a VSCode extension that helps improve the readability of your code comments by adding color and style to different types of comments, such as TODOs, highlights, questions, and alerts.

- Use `code --install-extension aaron-bond.better-comments` to install the Better Comments extension [(docs)](https://marketplace.visualstudio.com/items?itemName=aaron-bond.better-comments)

![](https://github.com/aaron-bond/better-comments/raw/084a906e73a3ca96d5319441714be8e3a2a8c385/images/better-comments.PNG)


### Markdown Preview Enhanced

Markdown Preview Enhanced is a feature-rich extension that provides a real-time preview of your Markdown files, supporting various Markdown flavors, interactive diagrams, and more.

- Use `code --install-extension shd101wyy.markdown-preview-enhanced` to install the Markdown Preview Enhanced extension [(docs)](https://marketplace.visualstudio.com/items?itemName=shd101wyy.markdown-preview-enhanced)

![](https://user-images.githubusercontent.com/1908863/28495106-30b3b15e-6f09-11e7-8eb6-ca4ca001ab15.png)

### Markdown All in One

Markdown All in One is a comprehensive extension that provides a range of features for working with Markdown files in VSCode, including syntax highlighting, auto-completion, table of contents, and more.

- Use `code --install-extension yzhang.markdown-all-in-one` to install the Markdown All in One extension [(docs)](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one)

![](https://raw.githubusercontent.com/yzhang-gh/vscode-markdown/78775f6caeb353bee905d7f72702364467b10ef1/images/gifs/toggle-bold.gif)

### WakaTime

WakaTime is an open source VS Code plugin for metrics, insights, and time tracking automatically generated from your programming activity. This service will keep a summary of how much time you spend in which project and which programming language.

- Use `code --install-extension WakaTime.vscode-wakatime` to install the WakaTime extension [(docs)](https://marketplace.visualstudio.com/items?itemName=WakaTime.vscode-wakatime)

![](https://wakatime.com/static/img/ScreenShots/Screen-Shot-2016-03-21.png)


## Other extensions I use

The following extensions are not as essential as the ones listed above, but I still find them useful for various tasks.

### LaTeX Workshop

LaTeX Workshop is a comprehensive extension for working with LaTeX documents in VSCode, featuring syntax highlighting, building and previewing, IntelliSense, and more.

- Use `code --install-extension James-Yu.latex-workshop` to install the LaTeX Workshop extension [(docs)](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop)

![](https://github.com/James-Yu/LaTeX-Workshop/raw/2a843a258002f05807203c078715dd6836faeeb8/demo_media/preview.gif)

### Live Share

Visual Studio Live Share is a real-time collaboration extension that allows you to share your workspace with others, enabling pair programming, code reviews, and collaborative debugging.

- Use `code --install-extension ms-vsliveshare.vsliveshare` to install the Live Share extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vsliveshare.vsliveshare)

![](https://aka.ms/vsls/quickstart/invite)

### Azure Account and Repos

These extensions offer a range of Azure-related functionality, including managing your Azure account, working with Azure Repos, exploring remote resources, and browsing remote Git repositories.

- Use `code --install-extension ms-vscode.azure-account` to install the Azure Account extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-account)
- Use `code --install-extension ms-vscode.azure-repos` to install the Azure Repos extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-vscode.azure-repos)

### CodeSnap

CodeSnap is a handy extension for creating beautiful code screenshots directly from your editor, making it easier to share code snippets on social media, blog posts, or documentation.

- Use `code --install-extension adpyke.codesnap` to install the CodeSnap extension [(docs)](https://marketplace.visualstudio.com/items?itemName=adpyke.codesnap)

![](https://user-images.githubusercontent.com/6897215/233820944-bfb1f980-4eb6-4bbd-8118-a960888b2d32.png)

### Micromamba

The Micromamba extension for VSCode integrates the Micromamba package manager, making it easier to manage Conda environments and packages within the editor.

- Use `code --install-extension corker.vscode-micromamba` to install the Micromamba extension [(docs)](https://marketplace.visualstudio.com/items?itemName=corker.vscode-micromamba)

### Markdownlint

Markdownlint is a VSCode extension that provides linting and style-checking for Markdown files, ensuring consistent and clean Markdown content.

- Use `code --install-extension DavidAnson.vscode-markdownlint` to install the Markdownlint extension [(docs)](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)

### Prettier

Prettier is a powerful code formatter that supports multiple languages, including JavaScript, TypeScript, HTML, CSS, and more. It enforces a consistent code style across your project.

- Use `code --install-extension esbenp.prettier-vscode` to install the Prettier extension [(docs)](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)

### Code Runner

Code Runner is a versatile extension that enables you to quickly run code snippets or whole files for multiple programming languages within VSCode, without the need to switch to an external terminal.

- Use `code --install-extension formulahendry.code-runner` to install the Code Runner extension [(docs)](https://marketplace.visualstudio.com/items?itemName=formulahendry.code-runner)

### Go

The Go extension by the Go team provides rich language support for the Go programming language, with features like IntelliSense, debugging, linting, and code navigation.

- Use `code --install-extension golang.go` to install the Go extension [(docs)](https://marketplace.visualstudio.com/items?itemName=golang.go)

### Home Assistant

The Home Assistant extension for VSCode provides integration with Home Assistant configuration files, offering syntax highlighting, auto-completion, and validation.

- Use `code --install-extension keesschollaart.vscode-home-assistant` to install the Home Assistant extension [(docs)](https://marketplace.visualstudio.com/items?itemName=keesschollaart.vscode-home-assistant)

### Azure Pipelines, Resource Groups, Storage, and Terraform

These Microsoft Azure extensions provide powerful integrations with various Azure services, allowing you to manage pipelines, resource groups, storage, and Terraform configurations directly within VSCode.

- Use `code --install-extension ms-azure-devops.azure-pipelines` to install the Azure Pipelines extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-azure-devops.azure-pipelines)
- Use `code --install-extension ms-azuretools.vscode-azureresourcegroups` to install the Azure Resource Groups extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureresourcegroups)
- Use `code --install-extension ms-azuretools.vscode-azurestorage` to install the Azure Storage extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurestorage)
- Use `code --install-extension ms-azuretools.vscode-azureterraform` to install the Azure Terraform extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azureterraform)

### Docker

The Docker extension adds rich support for working with Docker containers and images in VSCode, including building, managing, and deploying containerized applications.

- Use `code --install-extension ms-azuretools.vscode-docker` to install the Docker extension [(docs)](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)

### AutoDocstring

AutoDocstring is a helpful extension that automatically generates docstrings for Python functions and classes, following popular docstring formats like Google, NumPy, and reStructuredText.

- Use `code --install-extension njpwerner.autodocstring` to install the AutoDocstring extension [(docs)](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring)

### XML and YAML

These extensions by Red Hat provide rich language support for XML and YAML, including syntax highlighting, validation, code navigation, and more.

- Use `code --install-extension redhat.vscode-xml` to install the XML extension [(docs)](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-xml)
- Use `code --install-extension redhat.vscode-yaml` to install the YAML extension [(docs)](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)

### Rust Analyzer

Rust Analyzer is a powerful language server for the Rust programming language, offering features like syntax highlighting, code navigation, and auto-completion.

- Use `code --install-extension rust-lang.rust-analyzer` to install the Rust Analyzer extension [(docs)](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)

### Even Better TOML

Even Better TOML is a VSCode extension that provides syntax highlighting, validation, and auto-completion for TOML (Tom's Obvious, Minimal Language) configuration files.

### Terrastruct

Terrastruct is a VSCode extension that helps you visualize your Terraform dependency graphs as interactive diagrams, making it easier to understand complex infrastructure-as-code projects.

- Use `code --install-extension Terrastruct.d2` to install the Terrastruct extension [(docs)](https://marketplace.visualstudio.com/items?itemName=Terrastruct.d2)

### PDF

The PDF extension allows you to view and manage PDF files directly within VSCode, with support for zooming, rotating, and searching text.

- Use `code --install-extension tomoki1207.pdf` to install the PDF extension [(docs)](https://marketplace.visualstudio.com/items?itemName=tomoki1207.pdf)

### LTeX

LTeX is a grammar and spell checker extension for LaTeX, Markdown, and other markup languages, with support for multiple languages and customizable rules.

- Use `code --install-extension valentjn.vscode-ltex` to install the LTeX extension [(docs)](https://marketplace.visualstudio.com/items?itemName=valentjn.vscode-ltex)

### IntelliCode API Usage Examples and IntelliCode

These extensions by the Visual Studio Expt Team provide AI-powered code completion and code examples, helping you write code faster and with fewer errors.

- Use `code --install-extension VisualStudioExptTeam.intellicode-api-usage-examples` to install the IntelliCode API Usage Examples extension [(docs)](https://marketplace.visualstudio.com/items?itemName=VisualStudioExptTeam.intellicode-api-usage-examples)
- Use `code --install-extension VisualStudioExptTeam.vscodeintellicode` to install the IntelliCode extension [(docs)](https://marketplace.visualstudio.com/items?itemName=VisualStudioExptTeam.vscodeintellicode)

### vscode-icons

vscode-icons is a popular extension that adds file icons to VSCode, making it easier to identify file types in the file explorer.

- Use `code --install-extension vscode-icons-team.vscode-icons` to install the vscode-icons extension [(docs)](https://marketplace.visualstudio.com/items?itemName=vscode-icons-team.vscode-icons)
