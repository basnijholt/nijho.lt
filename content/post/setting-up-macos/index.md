---
title: "🍏 Setting Up Your Fresh MacOS Installation: A Comprehensive Guide"
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
4.  [File-up](https://github.com/basnijholt/fileup), a simple tool I made to upload files to an FTP server and copy the URL to the clipboard

Set a [`host`](https://github.com/StevenBlack/hosts) file to block unwanted websites and advertisements.

* * *

## 2. Increase `sudo` Password Timeout

To increase the sudo password timeout, follow the instructions provided in this [StackExchange answer](https://apple.stackexchange.com/a/51763).

* * *

## 3. Homebrew

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
  zsh \
  

brew install rbenv ruby  # if/when needed
brew cask install homebrew/cask-drivers/logitech-options
# Then optionally install:
brew install homebrew/tex/git-latexdiff

brew install gromgit/fuse/osxfuse-mac
brew install gromgit/fuse/sshfs-mac
```

</details>

Otherwise, you can install the essential applications and tools one by one:

### 1. Browsers

#### Chrome
A fast and user-friendly browser with seamless Google service integration and extensive extension library.
*   Install with `brew install --cask google-chrome`

#### Brave Browser
A privacy-focused browser with built-in adblocker and support for Chrome extensions, rewarding content creators via BAT tokens.
*   Install with `brew install --cask brave-browser`

#### Firefox
An open-source browser prioritizing user privacy and security, offering a customizable experience with various add-ons.
*   Install with `brew install --cask firefox`

### 2. Productivity Tools

#### Alfred
A powerful application launcher and productivity tool for quick actions, searches, and workflow automation.
* Install with `brew install --cask alfred`

#### Bartender
A utility to organize and manage your Mac's menu bar icons, improving aesthetics and accessibility.
* Install with `brew install --cask bartender`

#### BetterTouchTool
A customizable input device manager that enables advanced gesture control and shortcuts for your Mac.
* Install with `brew install --cask bettertouchtool`

#### HiddenBar
A lightweight tool to hide menu bar icons and declutter your Mac's interface.
* Install with `brew install --cask hiddenbar`

#### iStat Menus
A comprehensive system monitor providing detailed information about your Mac's performance through customizable menu bar icons.
* Install with `brew install --cask istat-menus`

#### Karabiner-Elements
A powerful keyboard customizer allowing you to remap keys, create shortcuts, and improve typing efficiency on your Mac.
* Install with `brew install --cask karabiner-elements`

#### KeepingYouAwake
A utility to prevent your Mac from going to sleep or turning off the display when you need it to stay active.
* Install with `brew install --cask keepingyouawake`

#### Obsidian
A powerful note-taking and knowledge management application that uses plain text files with Markdown support.
* Install with `brew install --cask obsidian`

#### Rectangle
A window management tool to easily resize and position windows on your Mac using keyboard shortcuts or snap-to-edge functionality.
* Install with `brew install --cask rectangle`

#### Raycast
A productivity tool that allows you to control your Mac using powerful and customizable command-based actions.
* Install with `brew install --cask raycast`

### 3. Communication

#### Microsoft Teams
A collaboration and communication platform for businesses, integrating chat, meetings, file sharing, and more.
* Install with `brew install --cask microsoft-teams`

#### Signal
A secure and private messaging app with end-to-end encryption, supporting voice and video calls.
* Install with `brew install --cask signal`

#### Skype
A widely used communication tool for voice and video calls, instant messaging, and file sharing.
* Install with `brew install --cask skype`

#### Telegram
A cloud-based messaging platform with a focus on speed and security, supporting large groups and file sharing.
* Install with `brew install --cask telegram`

#### Zoom
A popular video conferencing tool for virtual meetings, webinars, and collaboration.
* Install with `brew install --cask zoom`

### 4. Development

#### Airflow
A platform for programmatically authoring, scheduling, and monitoring workflows.
* Install with `brew install airflow`

#### Autossh
A tool for automatically starting and maintaining SSH connections.
* Install with `brew install autossh`

#### Azure CLI
A command-line tool for managing Azure resources.
* Install with `brew install azure-cli`

#### Bat
A `cat` command clone with syntax highlighting and Git integration.
* Install with `brew install bat`

#### Chromedriver
A WebDriver for running web tests with Chrome.
* Install with `brew install chromedriver`

#### Docker
A platform for developing, shipping, and running containerized applications.
* Install with `brew install --cask docker`

#### Git
A widely used distributed version control system.
* Install with `brew install git`

#### Git Extras
Extra utilities and scripts for Git.
* Install with `brew install git-extras`

#### Git LFS
A Git extension for versioning large files.
* Install with `brew install git-lfs`

#### Git Secret
A tool for storing sensitive data in Git repositories.
* Install with `brew install git-secret`

#### Go
An open-source programming language designed for simplicity and concurrency.
* Install with `brew install go`

#### Hugo
A fast and flexible static site generator.
* Install with `brew install hugo`

#### Java
A popular programming language and development platform.
* Install with `brew install java`

#### Micro
A modern and intuitive terminal-based text editor.
* Install with `brew install micro`

#### Nano
A simple and easy-to-use terminal text editor.
* Install with `brew install nano`

#### Rbenv
A Ruby version management tool.
* Install with `brew install rbenv`

#### Ruby
A dynamic, open-source programming language focused on simplicity and productivity.
* Install with `brew install ruby`

#### Rustup-Init
A toolchain installer for the Rust programming language.
* Install with `brew install rustup-init`

#### Terraform
An infrastructure as code software tool for managing cloud resources.
* Install with `brew install terraform`

#### Visual Studio Code
A powerful and extensible code editor with integrated Git and debugging support.
* Install with `brew install --cask visual-studio-code`

### 5. Terminal and Shell

#### iTerm2
A highly customizable and powerful terminal emulator for macOS.
* Install with `brew install --cask iterm2`

#### Zsh
An interactive and highly extensible Unix shell.
* Install with `brew install zsh`

#### Starship
A minimal, fast, and customizable shell prompt for any shell.
* Install with `brew install starship`

#### Tmux
A terminal multiplexer for managing multiple terminal sessions within a single window.
* Install with `brew install tmux`

### 6. Fonts

#### Font Fira Code
A monospaced font with programming ligatures, designed for a modern coding experience. Enhances readability and aesthetics in code editors.
* Install with `brew install --cask font-fira-code`

### 7. File Management and Utilities

#### BalenaEtcher
A user-friendly tool for flashing OS images onto SD cards and USB drives, simplifying the creation of bootable media.
* Install with `brew install --cask balenaetcher`

#### Cakebrew
A GUI for managing Homebrew packages, providing an easy way to search, install, and update software.
* Install with `brew install --cask cakebrew`

#### Cryptomator
An open-source encryption solution for cloud storage services, offering transparent, client-side encryption for data security.
* Install with `brew install --cask cryptomator`

#### DB Browser for SQLite
A high-quality, visual tool to create, design, and edit SQLite database files, streamlining database management.
* Install with `brew install --cask db-browser-for-sqlite`

#### Disk Inventory X
A disk usage utility for macOS that displays folder and file sizes in a visual treemap, enabling quick identification of large files.
* Install with `brew install --cask disk-inventory-x`

#### Dropbox
A popular cloud storage service that seamlessly synchronizes files across devices, making file sharing and collaboration easy.
* Install with `brew install --cask dropbox`

#### Mounty
A user-friendly tool for mounting and writing to NTFS drives on macOS, providing seamless read/write access.
* Install with `brew install --cask mounty`

#### MPV
A free, open-source, and cross-platform media player with minimalistic design, supporting a wide range of media formats.
* Install with `brew install --cask mpv`

#### Rsync
A powerful file transfer utility that uses delta encoding and compression to minimize data transfer, optimizing file synchronization.
* Install with `brew install rsync`

#### SSH-Copy-ID
A utility to install your public key on a remote machine's authorized_keys, simplifying the setup of passwordless SSH connections.
* Install with `brew install ssh-copy-id`

#### Syncthing
A decentralized, open-source file synchronization tool that securely shares and synchronizes files between devices without relying on cloud services.
* Install with `brew install --cask syncthing`

#### Universal Media Server
A versatile media server that supports various devices and streaming protocols, allowing you to stream your media files across your home network.
* Install with `brew install --cask universal-media-server`

#### XQuartz
An open-source X Window System implementation for macOS that allows running X11 applications, enabling compatibility with many Unix programs.
* Install with `brew install --cask xquartz`

#### Inkscape
A professional vector graphics editor that supports various file formats, offering a powerful set of drawing tools for graphic design.
* Install with `brew install --cask inkscape`

### 8. Security and Privacy

#### Avast Security
A comprehensive antivirus and security suite, offering protection against various threats, as well as VPN and cleanup features.
*   Install with `brew install --cask avast-security`

#### eqMac
An open-source audio equalizer for macOS, enhancing your listening experience with customizable presets and manual adjustments.
*   Install with `brew install --cask eqmac`

#### LuLu
A lightweight, open-source firewall for macOS, offering control over outgoing connections and protecting against unauthorized access.
*   Install with `brew install --cask lulu`

#### NordVPN
A popular VPN service providing a secure and encrypted connection, allowing access to geo-restricted content and protecting your privacy.
*   Install with `brew install --cask nordvpn`

#### ProtonMail Bridge
A desktop application enabling the use of ProtonMail with your preferred email client, ensuring end-to-end encryption and privacy.
*   Install with `brew install --cask protonmail-bridge`

#### Tor Browser
A privacy-focused browser that routes your traffic through the Tor network, ensuring anonymity and access to hidden services on the dark web.
*   Install with `brew install --cask tor-browser`

#### Tunnelblick
A free, open-source VPN client for macOS, providing an easy-to-use interface for connecting to OpenVPN servers.
*   Install with `brew install --cask tunnelblick`

### 9. Multimedia

#### HandBrake
A versatile video converter and transcoder, supporting a wide range of formats and offering advanced customization options.
*   Install with `brew install --cask handbrake`

#### LICEcap
A lightweight screen capture tool, allowing you to create animated GIFs directly from your desktop.
*   Install with `brew install --cask licecap`

#### MusicBrainz Picard
An open-source music tagger, using the MusicBrainz database to automatically update and organize your audio files' metadata.
*   Install with `brew install --cask musicbrainz-picard`

#### OBS (Open Broadcaster Software)
A powerful and customizable software for live streaming and screen recording, widely used by content creators and gamers.
*   Install with `brew install --cask obs`

#### Spotify
A popular music streaming service, offering access to millions of songs, podcasts, and personalized playlists with a free or premium account.
*   Install with `brew install --cask spotify`

#### Steam
A digital distribution platform for purchasing and managing video games, providing a vast library of titles and social features.
*   Install with `brew install --cask steam`

#### VLC
A versatile and open-source media player, supporting a wide range of audio and video formats, as well as streaming and conversion capabilities.
*   Install with `brew install --cask vlc`

#### WebTorrent
A user-friendly torrent client that runs directly in your browser, enabling streaming of torrent files without the need for a separate application.
*   Install with `brew install --cask webtorrent`

### 10. Office and Document Management

#### Adobe Creative Cloud
A suite of creative applications for graphic design, video editing, web development, and more, including Photoshop, Illustrator, and Premiere Pro.
*   Install with `brew install --cask adobe-creative-cloud`

#### Adobe Digital Editions
An ebook reader and manager, supporting various formats and DRM-protected files, as well as syncing across devices.
*   Install with `brew install --cask adobe-digital-editions`

#### Calibre
An open-source ebook management tool, offering format conversion, syncing, and organization features, as well as a built-in reader.
*   Install with `brew install --cask calibre`

#### FileBot
A media file organization tool, simplifying the renaming and sorting of TV shows, movies, and music files.
*   Install with `brew install --cask filebot`

#### JabRef
An open-source reference manager, enabling the organization and citation of scientific publications in BibTeX and other formats.
*   Install with `brew install --cask jabref`

#### LyX
A document processor that combines the power of LaTeX with a user-friendly graphical interface, simplifying the creation of professional-looking documents.
*   Install with `brew install --cask lyx`

#### MacTeX
A comprehensive TeX distribution for macOS, including LaTeX, various utilities, and documentation.
*   Install with `brew install --cask mactex`

#### Mactracker
A comprehensive database of Apple hardware and software, providing detailed specifications, history, and support information.
*   Install with `brew install --cask mactracker`

#### Mendeley
A reference manager and academic social network, simplifying the organization, annotation, and citation of research papers.
*   Install with `brew install --cask mendeley`

#### Microsoft Office
A suite of productivity applications, including Word, Excel, PowerPoint, and Outlook, designed for creating, editing, and managing documents.
*   Install with `brew install --cask microsoft-office`

#### OnyX
A multifunctional utility for macOS, offering maintenance, optimization, and personalization features, as well as advanced options for power users.
*   Install with `brew install --cask onyx`

### 11. Miscellaneous

#### Bunq Community Bunq
An unofficial, open-source desktop client for the Bunq banking platform, simplifying account management and transactions.
*   Install with `brew install --cask bunqcommunity-bunq`

#### Exodus
A user-friendly cryptocurrency wallet, supporting a wide range of assets, exchange features, and portfolio management.
*   Install with `brew install --cask exodus`

#### File Up
A lightweight and easy-to-use file uploader for macOS, enabling quick sharing of files via drag-and-drop functionality.
*   Install with `brew install --cask file-up`

#### f.lux
A screen color temperature adjustment tool, reducing eye strain and promoting healthy sleep patterns by adapting your display to the time of day.
*   Install with `brew install --cask flux`

#### GitHub
The official GitHub desktop client, simplifying repository management, version control, and collaboration on macOS.
*   Install with `brew install --cask github`

#### Logitech Options
A configuration tool for Logitech devices, offering customization of buttons, tracking, and other settings to enhance productivity and comfort.
*   Install with `brew install --cask homebrew/cask-drivers/logitech-options`

#### MacFuse
A macOS filesystem extension enabling the use of non-native filesystems, offering compatibility with a wide range of formats.
*   Install with `brew install --cask macfuse`

#### Microsoft Azure Storage Explorer
A graphical tool for managing Azure Blob Storage, offering convenient access, organization, and management of your cloud storage.
*   Install with `brew install --cask microsoft-azure-storage-explorer`

#### MonitorControl
A utility for controlling your external monitor's settings, such as brightness and volume, directly from your macOS menu bar.
*   Install with `brew install --cask monitorcontrol`

#### pipx
A package manager for installing and running Python applications in isolated environments, ensuring clean and conflict-free installations.
*   Install with `brew install pipx`

#### qBittorrent
A free and open-source torrent client, featuring a clean interface, powerful search capabilities, and minimal resource usage.
*   Install with `brew install --cask qbittorrent`

#### QLVideo
A QuickLook plugin for macOS, providing thumbnail previews and playback of various video formats directly in Finder.
*   Install with `brew install --cask qlvideo`

#### Rotki
An open-source portfolio tracking and tax reporting tool for cryptocurrencies, offering extensive customization and privacy options.
*   Install with `brew install --cask rotki`

#### SABnzbd
A binary newsreader for Usenet, offering automation features, a web interface, and compatibility with popular download management tools.
*   Install with `brew install --cask sabnzbd`

#### SelfControl
A productivity tool for macOS, allowing you to block access to distracting websites and applications for a set period of time.
*   Install with `brew install --cask selfcontrol`

#### Sloth
A macOS utility for displaying open files and network connections, offering insights into system resource usage and potential bottlenecks.
*   Install with `brew install --cask sloth`

#### SwitchResX
A display resolution management tool for macOS, enabling custom resolutions, aspect ratios, and refresh rates for your monitor.
*   Install with `brew install --cask switchresx`

#### TeamViewer
A remote desktop and collaboration tool, offering screen sharing, file transfer, and remote control capabilities for personal and professional use.
*   Install with `brew install --cask teamviewer`

#### Unclack
A utility for macOS that automatically mutes your microphone while you type, preventing unwanted noise during conference calls and voice recordings.
*   Install with `brew install --cask unclack`

#### yq
A command-line tool for parsing and manipulating YAML files, offering powerful filtering and editing capabilities.
*   Install with `brew install yq`

#### Ext4Fuse
A macOS filesystem extension enabling read-only support for the ext4 file system, commonly used on Linux systems.
*   Install with `brew install gromgit/fuse/ext4fuse`

#### NTFS-3G
A macOS filesystem extension providing read-write support for the NTFS file system, commonly used on Windows systems.
*   Install with `brew install gromgit/fuse/ntfs-3g`

#### SSHFS
A macOS filesystem extension enabling mounting of remote filesystems via SSH, providing secure and convenient access to remote files.
*   Install with `brew install gromgit/fuse/sshfs`

### 12. Optional

#### Git LaTeXdiff
A command-line tool for generating diff files for LaTeX documents, simplifying the tracking of changes and collaboration on LaTeX projects.
*   Install with `brew install homebrew/tex/git-latexdiff`

{{% callout note %}}
[osxfuse (and thus sshfs) is deprecated from Homebrew](https://github.com/Homebrew/homebrew-core/issues/75656), there is this [tap](https://github.com/gromgit/homebrew-fuse) [[here](https://github.com/Homebrew/brew/blob/master/docs/Interesting-Taps-and-Forks.md#unsupported-interesting-taps)] that I can use to install osxfuse and sshfs.
{{% /callout %}}

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