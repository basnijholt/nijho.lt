# [nijho.lt](http://www.nijho.lt/)

[![Netlify Status](https://api.netlify.com/api/v1/badges/1b9d8edc-3626-48f1-a6bd-52de691b2fda/deploy-status)](https://app.netlify.com/sites/nijholt/deploys)

This is my personal website build with [Hugo](https://gohugo.io/) and the [Academic theme](https://github.com/gcushen/hugo-academic/) ([docs](https://docs.hugoblox.com/)) and hosted via [Netlify](https://www.netlify.com/).

See the builds on Netlify [here](https://app.netlify.com/sites/nijholt/deploys?filter=main).


Run the following command to start the server locally:
```bash
docker build -t blog . && docker run -it -p 8080:80 blog
```