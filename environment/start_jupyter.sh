#!/usr/bin/env bash
set -euo pipefail
# Create a virtualenv, install requirements, register kernel, and launch Jupyter Lab
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r environment/requirements.txt
python -m ipykernel install --user --name aml-env --display-name "AML Jupyter (aml-env)"
exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
