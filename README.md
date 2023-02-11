# Docs

This repository contains the dapta docs and associated tutorial files.

## Build docs

```
cd mynewbook
jupyter-book build . --all
```
## Push static html to git branch 'gh-pages'

```
cd mynewbook
ghp-import -n -p -f _build/html --cname=daptadocs.com
```
## License

Copyright 2023 Dapta LTD

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.