---
title: "🍏 Setting Up Your Fresh MacOS Installation: A Comprehensive Guide"
subtitle: 🚀  Streamline your MacOS setup with Homebrew, over 100 essential apps, and customization tips
summary: 🚀  Streamline your MacOS setup with Homebrew, over 100 essential apps, and customization tips
projects: []
date: '2023-04-21T00:00:00Z'
draft: false
featured: false

image:
  caption: 'Setting up a full stack development environment on MacOS in 1 hour'
  focal_point: ''
  placement: 2
  preview_only: false

authors:
  - admin

tags:
  - macos
  - homebrew
  - oh-my-zsh

categories:
  - setup
  - level:beginner
---

## Introduction

Setting up a new MacOS installation can be a tedious process. This blog post will guide you through the essential steps and applications to install when setting up your fresh MacOS environment.
I'll cover a few unavoidable manual installations, homebrew, iTerm and VS Code font, oh-my-zsh, but can automate most other things.

> Note that this is just what I have been doing for the last years, and you might want to do things differently.

{{% callout note %}}
This post is based on a GitHub Gist I have been maintaining since 2015-03 with >160 revisions by now, see it at [`basnijholt/install-fresh-macOS.md`](https://gist.github.com/basnijholt/2df9845af97c69811b44)
{{% /callout %}}

{{< toc >}}

* * *

## 1. Manual Installations

First, let's manually install some essential tools and software:

1.  [homebrew](https://brew.sh/), the essential package manager for MacOS
2.  [micromamba](https://mamba.readthedocs.io/en/latest/installation.html#micromamba), my preferred conda package manager which is blazingly fast
3.  [Chrome](https://www.google.com/chrome/) (manual install because the brew version doesn't work with 1Password)
4.  [File-up](https://github.com/basnijholt/fileup), a simple tool I made to upload files to an FTP server and copy the URL to the clipboard **(optional)**

Set a [`host`](https://github.com/StevenBlack/hosts) file to block unwanted websites and advertisements.

* * *

## 2. Homebrew

Homebrew is a powerful package manager for MacOS. It allows you to quickly and easily install, update, and remove software.

<details>
<summary>To install a long list of essential applications and tools, run the following commands in your terminal (click to unfold):</summary>

```bash
brew install --cask \
  adobe-creative-cloud \
  adobe-digital-editions \
  airflow \
  alfred \
  avast-security \
  balenaetcher \
  bartender \
  bettertouchtool \
  brave-browser \
  cakebrew \
  calibre \
  chromedriver \
  cryptomator \
  db-browser-for-sqlite \
  disk-inventory-x \
  docker \
  dropbox \
  eqmac \
  exodus \
  filebot \
  firefox \
  flux \
  github \
  handbrake \
  hiddenbar \
  homebrew/cask-drivers/logitech-options \
  istat-menus \
  iterm2 \
  jabref \
  java \
  karabiner-elements \
  keepingyouawake \
  licecap \
  lulu \
  lyx \
  macfuse \
  mactex \
  mactracker \
  mendeley \
  microsoft-azure-storage-explorer \
  microsoft-office \
  microsoft-teams \
  monitorcontrol \
  mounty \
  mpv \
  musicbrainz-picard \
  nordvpn \
  obs \
  obsidian \
  onyx \
  protonmail-bridge \
  qbittorrent \
  qlvideo \
  raycast \
  rectangle \
  rotki \
  sabnzbd \
  selfcontrol \
  signal \
  skype \
  sloth \
  spotify \
  steam \
  sublime-merge \
  sublime-text \
  switchresx \
  syncthing \
  teamviewer \
  telegram \
  tor-browser \
  tunnelblick \
  unclack \
  universal-media-server \
  visual-studio-code \
  vlc \
  webtorrent \
  zoom

brew cask install xquartz inkscape

# Font used in iTerm/VS Code terminal for Starship
brew tap homebrew/cask-fonts
brew install --cask font-fira-code

brew tap microsoft/git
brew install --cask git-credential-manager-core

brew install \
  autossh \
  azure-cli \
  bat \
  brew-cask-completion \
  cointop \
  gh \
  gifsicle \
  git \
  git-extras \
  git-lfs \
  git-secret \
  go \
  gpg \
  graphviz \
  gromgit/fuse/ext4fuse \
  gromgit/fuse/ntfs-3g
  gromgit/fuse/sshfs \
  htop \
  hugo \
  imagemagick \
  jq \
  keychain \
  micro \
  nano \
  pipx \
  rclone \
  rsync \
  rustup-init \
  ssh-copy-id \
  starship \
  terraform \
  tmux \
  wget \
  yq \
  zsh
  

brew install rbenv ruby  # if/when needed
brew cask install homebrew/cask-drivers/logitech-options
# Then optionally install:
brew install homebrew/tex/git-latexdiff

brew install gromgit/fuse/osxfuse-mac
brew install gromgit/fuse/sshfs-mac
```

</details>

Otherwise, you can install the essential applications and tools one by one:

<!-- CODE:PYTHON:START -->
<!-- import json -->
<!--  -->
<!--  -->
<!-- def generate_markdown(json_data): -->
<!--     markdown = "" -->
<!--     for category, apps in json_data.items(): -->
<!--         markdown += f"### {category}\n\n" -->
<!--         for app in apps: -->
<!--             markdown += f"#### {app['name']}\n" -->
<!--             markdown += f"{app['description']}\n" -->
<!--             maybe_cask = "  --cask" if app["cask"] else "" -->
<!--             markdown += f"* Install with `brew install{maybe_cask} {app['brew']}`\n\n" -->
<!--     return markdown -->
<!--  -->
<!-- with open("brew.json", "r") as json_file: -->
<!--     json_data = json.load(json_file) -->
<!--  -->
<!-- markdown = generate_markdown(json_data) -->
<!-- print(markdown) -->
<!-- CODE:END -->

<!-- OUTPUT:START -->

<!-- OUTPUT:END -->

{{% callout note %}}
[osxfuse (and thus sshfs) is deprecated from Homebrew](https://github.com/Homebrew/homebrew-core/issues/75656), there is this [tap](https://github.com/gromgit/homebrew-fuse) [[here](https://github.com/Homebrew/brew/blob/master/docs/Interesting-Taps-and-Forks.md#unsupported-interesting-taps)] that I can use to install osxfuse and sshfs.
{{% /callout %}}

* * *

## 3. Increase `sudo` Password Timeout

To increase the sudo password timeout, follow the instructions provided in this [StackExchange answer](https://apple.stackexchange.com/a/51763).
* * *

## 4. oh-my-zsh

[oh-my-zsh](https://github.com/robbyrussell/oh-my-zsh) is a popular framework for managing your Zsh configuration. Follow the download instructions provided in the link, or use the `dotfiles` folder if you have it.

* * *

## 5. Set Your Mac Host/Computer Name

To set a custom host or computer name for your Mac, open a terminal and run the following commands:

```bash
NAME="your-custom-name"
sudo scutil --set HostName $NAME
sudo scutil --set LocalHostName $NAME
sudo scutil --set ComputerName $NAME
dscacheutil -flushcache
```

* * *

## 6. Quick Dock Hiding

For a cleaner desktop experience, follow this [StackExchange answer](https://apple.stackexchange.com/a/34097) to enable quick dock hiding.

* * *

## 7. iTerm and VS Code Font

The Fira Code font is a popular choice for developers. To set it as the default font for iTerm and Visual Studio Code:

*   iTerm should be set by [`Profiles.json`](https://github.com/basnijholt/dotfiles/blob/57c1b0d9b3a54f8beb93db42fd48c97eb0c67bec/pub/iterm/Profiles.json#L63)
*   Follow the [VS Code instructions](https://github.com/tonsky/FiraCode/wiki/VS-Code-Instructions)

* * *

## Conclusion

After completing these steps, restart your Mac. You now have a fully customized and functional MacOS environment, ready for productivity and creativity. Enjoy your freshly set-up MacOS!
