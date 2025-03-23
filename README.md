# DSPy Examples

This repository contains practical examples of using DSPy for AI-powered code analysis and security evaluation.

- [DSPy Examples](#dspy-examples)
- [Setup](#setup)

# Setup

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .

uv pip install ipykernel -U --force-reinstall
uv pip install --upgrade jupyter ipywidgets
jupyter nbextension enable --py widgetsnbextension
```