# DSPy Examples

This repository contains practical examples of using DSPy for AI-powered code analysis and security evaluation.

- [DSPy Examples](#dspy-examples)
  - [Process](#process)
  - [Setup](#setup)
    - [Troubleshooting](#troubleshooting)
  - [References](#references)

## Process

1. Program

   1. Design
   2. Experiment

2. Evaluate:

   1. Create first dataset
   2. Refine a metric
   3. Iterate

3. Optimize:
   1. Tune the things

## Setup

To run the notebooks efficiently, I recommend using the `uv` tool to create a virtual environment and install the required packages.

```bash
uv sync
source .venv/bin/activate
```

To generate a fresh `uv lock` file, run:

```bash
rm uv.lock
uv lock
```

### Troubleshooting

Need to install the `ipykernel` package to run Jupyter notebooks?

```bash
uv pip install ipykernel -U --force-reinstall
uv pip install --upgrade jupyter ipywidgets
jupyter nbextension enable --py widgetsnbextension
```

## References

Inspiration:
  - https://x.com/tom_doerr
  - [https://dspy.ai/](https://dspy.ai/)
  - [https://blog.haizelabs.com/posts/dspy/](https://blog.haizelabs.com/posts/dspy/)
  - DSPy [cheatsheet](https://dspy.ai/cheatsheet)