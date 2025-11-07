# [nijho.lt](http://www.nijho.lt/)

[![Netlify Status](https://api.netlify.com/api/v1/badges/1b9d8edc-3626-48f1-a6bd-52de691b2fda/deploy-status)](https://app.netlify.com/sites/nijholt/deploys)

This is my personal website build with [Hugo](https://gohugo.io/) and the [Academic theme](https://github.com/gcushen/hugo-academic/) ([docs](https://docs.hugoblox.com/)) and hosted via [Netlify](https://www.netlify.com/).

See the builds on Netlify [here](https://app.netlify.com/sites/nijholt/deploys?filter=main).


## Local Development

Run the following command to start the development server with live reload:
```bash
docker-compose up -d
```

The site will be available at http://localhost:1313 and will automatically rebuild when you make changes.

To view logs:
```bash
docker-compose logs -f hugo
```

To stop the server:
```bash
docker-compose down
```