---
title: 🍏 Setting Up Your Fresh MacOS Installation: A Comprehensive Guide
subtitle: 🚀 Streamline your MacOS setup with homebrew, essential apps, and customization tips
summary: 🚀 Streamline your MacOS setup with homebrew, essential apps, and customization tips
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
---

## Introduction

Setting up a new MacOS installation can be a tedious process. This blog post will guide you through the essential steps and applications to install when setting up your fresh MacOS environment. I'll cover manual installations, homebrew, iTerm and VS Code font, oh-my-zsh, and more.

> Note that this is just what I have been doing for the last years, and you might want to do things differently.

* * *

## 1. Manual Installations

First, let's manually install some essential tools and software:

1.  [homebrew](https://brew.sh/)
2.  [micromamba](https://mamba.readthedocs.io/en/latest/installation.html#micromamba)
3.  [Chrome](https://www.google.com/chrome/) (manual install because the brew version doesn't work with 1Password)
4.  [File-up](https://github.com/basnijholt/fileup)

Set a [`host`](https://github.com/StevenBlack/hosts) file to block unwanted websites and advertisements.

* * *

## 2. Increase `sudo` Password Timeout

To increase the sudo password timeout, follow the instructions provided in this [StackExchange answer](https://apple.stackexchange.com/a/51763).

* * *

## 3. Homebrew

Homebrew is a powerful package manager for MacOS. It allows you to quickly and easily install, update, and remove software. To install a long list of essential applications and tools, run the following commands in your terminal:

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
  bunqcommunity-bunq \
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
  zsh \
  gromgit/fuse/sshfs \
  gromgit/fuse/ext4fuse \
  gromgit/fuse/ntfs-3g
  

brew install rbenv ruby  # if/when needed
brew cask install homebrew/cask-drivers/logitech-options
```

Then optionally install:

`brew install homebrew/tex/git-latexdiff`

### FUSE related tools

[osxfuse (and thus sshfs) is deprecated from Homebrew](https://github.com/Homebrew/homebrew-core/issues/75656), there is this [tap](https://github.com/gromgit/homebrew-fuse) [[here](https://github.com/Homebrew/brew/blob/master/docs/Interesting-Taps-and-Forks.md#unsupported-interesting-taps)] that I can use to install osxfuse and sshfs.

* * *

## 4. iTerm and VS Code Font

The Fira Code font is a popular choice for developers. To set it as the default font for iTerm and Visual Studio Code:

*   iTerm should be set by [`Profiles.json`](https://github.com/basnijholt/dotfiles/blob/57c1b0d9b3a54f8beb93db42fd48c97eb0c67bec/pub/iterm/Profiles.json#L63)
*   Follow the [VS Code instructions](https://github.com/tonsky/FiraCode/wiki/VS-Code-Instructions)

* * *

## 5. oh-my-zsh

[oh-my-zsh](https://github.com/robbyrussell/oh-my-zsh) is a popular framework for managing your Zsh configuration. Follow the download instructions provided in the link, or use the `dotfiles` folder if you have it.

* * *

## 6. Alfred Plugins

Alfred is a productivity app for MacOS that allows you to search your Mac and the web efficiently. Enhance your Alfred experience by installing these useful plugins:

*   Symbols Search
*   Open with Sublime Text
*   IMDB
*   WiFi
*   Synonyms

* * *

## 7. Set Your Mac Host/Computer Name

To set a custom host or computer name for your Mac, open a terminal and run the following commands:

```bash
NAME="your-custom-name"
sudo scutil --set HostName $NAME
sudo scutil --set LocalHostName $NAME
sudo scutil --set ComputerName $NAME
dscacheutil -flushcache
```

* * *

## 8. Quick Dock Hiding

For a cleaner desktop experience, follow this [StackExchange answer](https://apple.stackexchange.com/a/34097) to enable quick dock hiding.

* * *

## Conclusion

After completing these steps, restart your Mac. You now have a fully customized and functional MacOS environment, ready for productivity and creativity. Enjoy your freshly set-up MacOS!