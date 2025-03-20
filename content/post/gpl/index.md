---
title: "⚖ GPL for Python Packaging"
subtitle: Understanding GPL licenses and their implications for Python code and packaging
summary: Clarifying GPL licenses (GPLv2, GPLv3, LGPL, AGPL) and how they affect Python software, including the concept of "linking" in Python through imports.
projects: []
date: "2025-02-10T00:00:00Z"
draft: false
featured: false

authors:
  - admin

tags:
  - python
  - licensing
  - gpl
  - packaging
  - open-source

categories:
  - licensing
  - level:intermediate

image:
  caption: "GPL Licenses in Python - navigating licensing in your projects"
  focal_point: ""
  placement: 2
  preview_only: false

---

## Understanding GPL for Python Packaging

Over the last 10 years–since I started working on and with open source projects–the GPL topic has frequently come up with friends and colleagues.
I simply write this post as a reminder to myself and to have something concise and clear to link to later.
Also, [IANAL](https://en.wikipedia.org/wiki/IANAL), so if you are relying on this post, please do your own research, I have included all the links I used to make this post.

The GNU General Public License (GPL) is widely used in the open-source world, but its implications can be unclear, especially regarding Python packaging.
If you develop or distribute Python software, understanding GPL variants is crucial.

### What is GPL?

GPL is a strong copyleft license—meaning software using GPL-licensed code must also be released under the GPL.
There are several key variants relevant to Python:

- **GPLv2 & GPLv3**:
  These licenses require that software using GPL code (directly or indirectly) also be open-sourced under GPL upon distribution.([^gpl-faq-if-library],[^stack-include-gpl])
  If your Python application imports or depends on a GPL package, your code must adopt GPL licensing.

- **LGPL (Lesser GPL)**:
  LGPL is more permissive and is usually applied to libraries.
  It allows proprietary software to link or import the library without forcing the proprietary software itself to adopt LGPL.([^lgpl-license],[^stack-lgpl-commercial])
  You just need to ensure users can replace or modify the LGPL component.

- **AGPL (Affero GPL)**:
  AGPL is similar to GPLv3 but includes a critical extra clause: it applies even when users access the software remotely over a network (such as web services or APIs).
  If you use an AGPL-licensed Python library, your entire application must be open-sourced under AGPL, even if you're only hosting it online.([^agpl-license],[^stack-agpl-backend])

### What Does "Linking" Mean in Python?

GPL licenses often refer to "linking," traditionally associated with compiled languages (e.g., C, C++).
Python doesn't link code in the traditional sense.
However, it is generally agreed upon that importing a Python module counts as linking for licensing purposes.([^gpl-faq-if-library],[^stack-non-gpl-using-gpl])
Therefore, directly importing a GPL-licensed Python package typically triggers the GPL's copyleft requirements.

### Why Does This Matter for Python Packaging?

Python makes it easy to incorporate third-party libraries.
But unintentionally using GPL-licensed libraries (especially GPL or AGPL) legally obligates you to open-source your proprietary code.

- **Direct Dependencies**:
  If you directly import a GPL-licensed Python library, your software must be GPL-licensed upon distribution.([^gpl-faq-if-library],[^stack-include-gpl])

- **Indirect (Transitive) Dependencies**:
  If any dependency in your Python project indirectly relies on GPL-licensed code, your entire software must also adopt GPL licensing upon distribution.
  Even a hidden, indirect GPL dependency triggers the GPL requirements.([^gpl-faq-all-compatibility],[^dev-to-8000-packages],[^stackoverflow-transitive])

### Recommendations

- **Check Licenses Carefully**:
  Always verify the licenses of both your direct and indirect dependencies to prevent unintended GPL licensing obligations.([^gnu-license-list],[^stack-non-gpl-using-gpl])

- **Use Permissive or LGPL Licenses**:
  When planning to keep your own software proprietary, prioritize libraries with permissive licenses (e.g., MIT, Apache, BSD) or LGPL-licensed libraries, as they allow for proprietary use without triggering GPL requirements.([^lgpl-license],[^stack-lgpl-commercial])

- **Separate GPL Code**:
  If you must utilize GPL code, explicitly separate it from proprietary code.
  Using subprocess calls or isolated microservices is often recommended since it counts as "mere aggregation," not linking, thus avoiding GPL obligations.([^gpl-faq-mere-aggregation],[^stack-non-gpl-using-gpl])

By clearly understanding GPL licensing implications, you can confidently manage your Python project's dependencies and safely distribute your software.

<!-- Footnotes -->
[^gpl-faq-if-library]: [GNU GPL FAQ - If a library is released under the GPL](https://www.gnu.org/licenses/gpl-faq.html#IfLibraryIsGPL)
[^stack-include-gpl]: [Stack Exchange - If I include some GPL code in my project, can I release it as BSD?](https://opensource.stackexchange.com/questions/35/if-i-include-some-gpl-code-in-my-project-can-i-release-it-as-bsd)
[^lgpl-license]: [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl-3.0.en.html)
[^stack-lgpl-commercial]: [Stack Exchange - Can I use GPL/LGPL libraries in commercial closed source projects?](https://opensource.stackexchange.com/questions/6831/can-i-use-gpl-3-0-or-lgpl-licensed-libraries-in-my-commercial-closed-source-iot)
[^agpl-license]: [GNU Affero General Public License](https://www.gnu.org/licenses/agpl-3.0.en.html)
[^stack-agpl-backend]: [Stack Exchange - Can I use AGPL/GPL package for closed source backend API?](https://opensource.stackexchange.com/questions/11826/can-i-use-a-agpl-gpl-package-and-software-for-closed-source-backend-api)
[^stack-non-gpl-using-gpl]: [Stack Exchange - Can a non-GPL Python program use a GPL Python module?](https://opensource.stackexchange.com/questions/6033/can-a-non-gpl-python-program-use-gpl-python-module)
[^gpl-faq-all-compatibility]: [GNU GPL FAQ - License Compatibility](https://www.gnu.org/licenses/gpl-faq.html#AllCompatibility)
[^dev-to-8000-packages]: [Dev.to - 8000 Python packages might have to change to GNU General Public License](https://dev.to/wagenrace/8000-python-packages-might-have-to-change-to-gnu-general-public-license-1000)
[^stackoverflow-transitive]: [Stack Overflow - Import a library that imports a GPL library](https://stackoverflow.com/questions/6748333/import-a-library-that-imports-a-gpl-library)
[^gnu-license-list]: [GNU License List](https://www.gnu.org/licenses/license-list.html)
[^gpl-faq-mere-aggregation]: [GNU GPL FAQ - What is "mere aggregation"?](https://www.gnu.org/licenses/gpl-faq.html#MereAggregation)
