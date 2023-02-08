# Docs

This repository contains the dapta docs and associated tutorial files.

## Build docs

```
cd mynewbook
jupyter-book build . --all
```
## Push static html to git branch 'gh-pages' /build folder (https://github.com/c-w/ghp-import)

```
cd mynewbook
ghp-import -n -p -f --prefix=build _build/html
```
## Edit the flask app 

```
git checkout gh-pages 
(open app.py)
```