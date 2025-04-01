# DSPy <3 Examples

This repository contains practical examples of using DSPy for AI-powered code analysis and security evaluation.

- [DSPy \<3 Examples](#dspy-3-examples)
  - [Process](#process)
  - [Setup](#setup)
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

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e .
uv pip compile pyproject.toml > uv.lock

uv pip install ipykernel -U --force-reinstall
uv pip install --upgrade jupyter ipywidgets
jupyter nbextension enable --py widgetsnbextension
```

## References

inspo:
  - https://x.com/tom_doerr
  - [https://dspy.ai/](https://dspy.ai/)
  - [https://blog.haizelabs.com/posts/dspy/](https://blog.haizelabs.com/posts/dspy/)
  - DSPy [cheatsheet](https://dspy.ai/cheatsheet)