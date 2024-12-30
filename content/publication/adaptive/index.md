---
title: "Adaptive: parallel active learning of mathematical functions"
date: "2021-09-19T00:00:00"

authors:
- Bas Nijholt
- Joseph Weston
- Anton R. Akhmerov
publication_types: ["paper"]  # Preprint / Working Paper

publication: "Preprint"
# publication_short: "In *PRL*"
abstract: >
  Large scale computer simulations are time-consuming to run and often require sweeps over input parameters to obtain a qualitative understanding of the simulation output.
  These sweeps of parameters can potentially make the simulations prohibitively expensive.
  Therefore, when evaluating a function numerically, it is advantageous to sample it more densely in the interesting regions (called adaptive sampling) instead of evaluating it on a manually-defined homogeneous grid.
  Such adaptive algorithms exist within the machine learning field.
  These methods can suggest a new point to calculate based on *all* existing data at that time; however, this is an expensive operation.
  An alternative is to use local algorithms---in contrast to the previously mentioned global algorithms---which can suggest a new point, based only on the data in the immediate vicinity of a new point.
  This approach works well, even when using hundreds of computers simultaneously because the point suggestion algorithm is cheap (fast) to evaluate.
  We provide a reference implementation in Python and show its performance.

summary: "Large scale computer simulations are time-consuming to run and often require sweeps over input parameters to obtain a qualitative understanding of the simulation output."

featured: true

url_pdf: "https://gitlab.kwant-project.org/qt/adaptive-paper/-/jobs/119119/artifacts/raw/paper.pdf?inline=false"
url_preprint: "https://github.com/python-adaptive/paper"
url_code: "https://github.com/python-adaptive/adaptive/"
links: [{name: "Paper draft source code", url: "https://github.com/python-adaptive/paper"}, {name: "Documentation", url: "https://adaptive.readthedocs.io/en/latest/"}]

---
