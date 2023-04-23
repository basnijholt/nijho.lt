---
title: 👩‍💻 Be a Ninja in the Terminal 🥷
subtitle: A setup for maximal productivity and minimal keystrokes, with `zsh`, `oh-my-zsh`, `keychain`, `starship`, `autoenv`, `z`, `zsh-autosuggestions`, and more.
summary: A setup for maximal productivity and minimal keystrokes, with `zsh`, `oh-my-zsh`, `keychain`, `starship`, `autoenv`, `z`, `zsh-autosuggestions`, and more.
projects: []
date: '2023-04-21T00:00:00Z'
draft: false
featured: false

image:
  caption: 'My top 25 most used Terminal commands, as you can see, most commands are 1 or 2 characters long'
  focal_point: ''
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  - terminal
  - productivity
  - zsh
  - oh-my-zsh
  - dotfiles
  - dotbot
  - starship
  - autoenv
  - z
  - autoenv
  - zsh-autosuggestions
  - git

categories:
  - terminal
  - level:intermediate
---

Welcome to the dojo, fellow terminal warriors!
Today, I'll guide you through the mystic arts of terminal productivity, sharing with you the tools I use to maximize efficiency and minimize keystrokes.
When helping others with programming problems on their computer, I often find myself in their terminal, and feel like walking through sand.
When I show how awesome of an experience it can be, I often find myself repeating the same suggestions over and over again.
So, I decided to write this guide to help others set up their terminal in a similar fashion.
In this short post, we'll explore the wonders of [`zsh`](https://www.zsh.org/), [`oh-my-zsh`](https://ohmyz.sh/), [`keychain`](https://wiki.gentoo.org/wiki/Keychain), [`starship`](https://starship.rs/), [`autoenv`](https://github.com/hyperupcall/autoenv), [`z`](https://github.com/agkozak/zsh-z), [`zsh-autosuggestions`](https://github.com/zsh-users/zsh-autosuggestions), several Oh My ZSH plugins, having a `dotfiles` repo, and more!

![](https://camo.githubusercontent.com/18cdb04e93fe276412b588dbed23bc328614bf7a4d09ea4d8862d38f1c466c65/687474703a2f2f6d656469612e74756d626c722e636f6d2f74756d626c725f6c74757a6a766251364c31717a677078392e676966)

{{< toc >}}

## 💾 Dotfiles: Version Control Your Configuration Files

As a terminal ninja, you know the importance of your configuration files. They hold the keys to your productivity, personalizing your terminal experience and making it truly your own.
To ensure the safety and portability of your configurations, it's essential to keep a `dotfiles` folder, where you store and version control your configuration files and plugin repositories.

By keeping your `.bashrc`, `.zshrc`, and other configuration files under version control, you can:

1.  Keep track of changes and easily revert to previous versions if something goes wrong.
2.  Synchronize your settings across multiple machines, allowing you to recreate your terminal setup on any system.
3.  Share your configurations with others, helping them improve their own terminal experience.

As an example, these are the submodules (we will go over a few later in this post) I am tracking in my `dotfiles` repository:

```bash
[submodule "configs/zsh/oh-my-zsh"]
	path = submodules/oh-my-zsh
	url = git@github.com:robbyrussell/oh-my-zsh.git
[submodule "configs/zsh/zsh-syntax-highlighting"]
	path = submodules/zsh-syntax-highlighting
	url = git@github.com:zsh-users/zsh-syntax-highlighting.git
[submodule "configs/zsh/zsh-autosuggestions"]
	path = submodules/zsh-autosuggestions
	url = git@github.com:zsh-users/zsh-autosuggestions.git
[submodule "submodules/keychain"]
	path = submodules/keychain
	url = git@github.com:funtoo/keychain.git
[submodule "syncthing-resolve-conflicts"]
	path = submodules/syncthing-resolve-conflicts
	url = git@github.com:dschrempf/syncthing-resolve-conflicts.git
[submodule "configs/zsh/k"]
	path = submodules/k
	url = git@github.com:supercrabtree/k.git
[submodule "submodules/.tmux"]
	path = submodules/tmux
	url = https://github.com/gpakosz/.tmux.git
[submodule "configs/zsh/autoenv"]
	path = submodules/autoenv
	url = https://github.com/hyperupcall/autoenv
[submodule "submodules/bypass-paywalls-chrome"]
	path = submodules/bypass-paywalls-chrome
	url = git@github.com:iamadamdev/bypass-paywalls-chrome.git
[submodule "submodules/dotbot"]
	path = submodules/dotbot
	url = https://github.com/anishathalye/dotbot
[submodule "dotbot"]
	ignore = dirty
# (... a couple more ...)
```

In this example, you store not only your configuration files but also several of the plugins as git submodules.
This approach ensures that all your essential settings and tools are in one place, making it easy to manage, backup, and share.

To get started with version controlling your dotfiles, create a new Git repository and add your configuration files and submodules.
Then, commit your changes and push them to a remote repository (such as GitHub or GitLab) for safekeeping and easy access.

I highly recommend using [Dotbot](https://github.com/anishathalye/dotbot) to automate the installation of your dotfiles.

Embrace the power of version control and keep your dotfiles safe and secure, as any true terminal ninja would.

{{% callout note %}}
Although I keep my dotfiles in a Git repository, I have not made it public. I might do so in the future, let me know if you're interested!
{{% /callout %}}

## 🐚 The Art of Shell: Zsh and Oh-my-zsh

The first step in our journey is choosing the right shell.
We want a shell that is powerful, versatile, and expressive.
Enter the Zen of Zsh, a fantastic shell for interactive use, with features that make your life easier.

But why stop there? Let's add some spice to our shell with Oh-my-zsh, a delightful framework for managing Zsh configurations.
It's the secret sauce that brings our terminal to life with themes, plugins, and functions.
I suggest a few plugins in the example below and go through them in more detail later in this post.

To set up Zsh and Oh-my-zsh, follow these steps:

1.  Install Zsh (check your system's package manager for instructions).
2.  Install Oh-my-zsh by running:
    
    ```bash
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
    ```
    
3.  Edit your `.zshrc` file and add the following lines to customize your plugins and theme:
    
    ```bash
    ZSH_THEME="your-theme"
    plugins=(git z dirhistory history sudo)
    ```

## 🚀 Oh-my-zsh Z Plugin: Jump Around!

A true ninja can swiftly navigate through the file system, and Z is our secret weapon.
Z is a fantastic utility that allows us to jump around our directories based on the frequency and recency of use.
With the power of Z, we can leap to any folder in an instant, vanishing and reappearing like a shadow in the night.

To set up Z, add the following lines to your `.zshrc`:

```bash
plugins=(... z ...)
source $ZSH/oh-my-zsh.sh
```

![](https://github.com/agkozak/zsh-z/raw/da8dee3ccaf882d1bf653c34850041025616ceb5/img/demo.gif)

## ⏰ Oh-my-zsh Dirhistory Plugin: Time Travel Through Directories

The `dirhistory` plugin in Oh-my-zsh allows you to navigate your directory history and hierarchy with ease, using simple keyboard shortcuts. Let's go through its functionalities:

*   **ALT-LEFT**: Move back to previously visited directories.
*   **ALT-RIGHT**: Undo the effect of ALT-LEFT, returning to the directories you moved back from.
*   **ALT-UP**: Move up one level in the directory hierarchy (equivalent to `cd ..`).
*   **ALT-DOWN**: Move into the first directory found in alphabetical order within the current directory.

To set up the Oh-my-zsh `dirhistory` plugin, add the following lines to your `.zshrc`:

```bash
plugins=(... dirhistory ...)
source $ZSH/oh-my-zsh.sh
```

With the `dirhistory` plugin, navigating through directories becomes a breeze.
You'll be able to move up and down the directory hierarchy and traverse your directory history with just a few keystrokes, making your terminal experience even more efficient and enjoyable.

## 🔧 Oh-my-zsh Git Plugin: Turbocharge Your Git Workflow

If you are a developer, you probably use Git *a lot*!
I know I do.
Writing out `git checkout` and `git commit` every time I want to switch branches or commit changes is a waste of time, therefore I use the `git` plugin in Oh-my-zsh which provides useful aliases to make my Git workflow more efficient.
Let's go through some of ***my*** most commonly used aliases (ranked by frequency of use):

*   `gco`: `git checkout` - Switch branches or restore working tree files.
*   `gd`: `git diff` - Show changes between the working tree and the index or a tree.
*   `g`: `git` - The git command itself.
*   `gcb`: `git checkout -b` - Create a new branch and switch to it.
*   `gc`: `git commit --verbose` - Create a new commit with a verbose message.
*   `gc!`: `git commit --verbose` --amend - Amend the previous commit with a verbose message.
*   `ga`: git add - Add file contents to the index.
*   `gca`: `git commit --verbose --all` - Commit all changes with a verbose message.
*   `gca!`: `git commit --verbose --all --amend` - Amend the previous commit with a verbose message.
*   `gcp`: `git cherry-pick` - Apply the changes introduced by some existing commits.
*   `gst`: `git status` - Show the working tree status.
*   `gp`: `git push` - Update remote refs along with associated objects.
*   `gmom`: `git merge origin/$(git_main_branch)` - Merge changes from the main branch.
*   `grbom`: `git rebase origin/$(git_main_branch)` - Rebase current branch onto the main branch.
*   `gfa`: `git fetch --all --prune --jobs=10` - Fetch all remote branches and remove any stale remote-tracking references, using 10 parallel jobs.

To set up the Oh-my-zsh `git` plugin, add the following lines to your `.zshrc`:

```bash
plugins=(... git ...)
source $ZSH/oh-my-zsh.sh
```

## 🔑 Keychain: The Keeper of Secrets

As ninjas, we must keep our secrets safe.
Keychain helps us do just that by managing our SSH keys, ensuring we have secure access to remote systems.
This is particularly useful when cloning Git repositories or interacting with remote servers using SSH.

With Keychain, you only need to ***enter your SSH password once*** after rebooting, and it will remember it for future sessions, saving you valuable time and effort.

To set up Keychain clone the Keychain tool (to e.g., your `dotfiles` directory):
```bash
git clone git@github.com:funtoo/keychain.git ~/dotfiles/keychain
```

Then in your `.bash_profile`, add the following lines:

```bash
if [[ `hostname` == 'Linux' ]]; then
    export PATH="$PATH:${HOME}/dotfiles/pub/keychain/"
    if ps -p $SSH_AGENT_PID > /dev/null; then
        echo "ssh-agent is already running"
    else
        eval `keychain --eval --quiet id_ed25519`
    fi
fi
if [[ `uname` == 'Darwin' ]]; then
    eval `keychain --eval --quiet --agents ssh --inherit any-once id_ed25519`
fi
```

## 🌌 Starship: The Cosmic Shell Prompt

With our shell of choice and secrets secured, it's time to gaze upon the stars! Starship is a minimal, blazing-fast, and fully customizable shell prompt that provides us with essential information at a glance.
It gives us valuable feedback about our current environment, such as the Git branch, Python virtual environment, and more.

To set up Starship, follow these steps:

1.  Install Starship using the appropriate command for your system:
    
    ```bash
    curl -fsSL https://starship.rs/install.sh | bash
    ```
    
2.  Add the following line to your `.bashrc` or `.zshrc`:
    
    ```bash
    eval "$(starship init zsh)"
    ```

<video controls>
  <source src="https://starship.rs/demo.webm" type="video/webm">
  Your browser does not support the video tag.
</video>

## 🌍 Autoenv: Automatic Environment Management

In the life of a terminal ninja, we frequently traverse different projects, each with its unique environment requirements.
Autoenv comes to our rescue by automating the process of activating and deactivating project-specific settings.
It magically detects when we enter or leave a directory and takes the appropriate actions to set or unset environment variables.

For example you can setup a `.env` file in your project directory to automatically activate a virtual environment when you enter the directory.
I frequently create a `.env` file in a repo and activate a Python environment:

```bash
conda activate myenv
```

To set up Autoenv, follow these steps:

1.  Install Autoenv by cloning the repository (or add it to your `dotfiles`):
    
    ```bash
    git clone git://github.com/hyperupcall/autoenv.git ~/.autoenv
    ```
    
2.  Add the following line to your `.zshrc`:
    
    ```bash
    source ~/.autoenv/activate.sh
    ```

## 💡 Zsh-autosuggestions: The Wisest of Mentors

As we hone our terminal skills, we often find ourselves repeating commands.
Zsh-autosuggestions is our trusted mentor, always ready with sage advice.
It suggests commands based on our command history, saving us precious keystrokes and making our terminal life more enjoyable.

To set up Zsh-autosuggestions, follow these steps:

1.  Clone the repository:
    
    ```bash
    git clone https://github.com/zsh-users/zsh-autosuggestions.git $ZSH_CUSTOM/plugins/zsh-autosuggestions
    ```
    
2.  Add the following line to your `.zshrc`:
    
    ```bash
    source $ZSH_CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
    ```

![](https://user-images.githubusercontent.com/6897215/233818577-189256ff-b1e2-4790-984e-6fd191df5c00.gif)

## 🧩 Putting it All Together

Now that you know the secrets of our terminal ninja setup, it's time to embark on your own journey.
Armed with these powerful tools, you'll conquer the terminal with grace and efficiency.
Remember, the path of the ninja is one of continuous learning and growth.
Embrace the way of the terminal, and become one with the command line. 🥷

Feel free to reach out if you have any questions or require clarification on any of the tools mentioned.
Happy ninja-ing!
