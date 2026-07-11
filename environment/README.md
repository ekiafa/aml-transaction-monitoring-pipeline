# Jupyter environment setup

Quick steps to create an environment to run notebooks in this repo.

Option A — Python `venv` (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r environment/requirements.txt
# (optional) register kernel for the notebook UI
python -m ipykernel install --user --name aml-env --display-name "AML Jupyter (aml-env)"
# start Jupyter Lab
jupyter lab
```

Option B — Conda:

```bash
conda env create -f environment/conda_env.yml
conda activate aml-jupyter
python -m ipykernel install --user --name aml-jupyter --display-name "AML Jupyter (conda)"
jupyter lab
```

Quick start script:

```bash
bash environment/start_jupyter.sh
```

Notes:
- The `start_jupyter.sh` script creates a `.venv` in the repository root and installs packages into it.
- If running inside a container/devbox, prefer the container's Python or Conda.
