# DSPy Examples

This repository contains practical examples of using DSPy for AI-powered code analysis and security evaluation.

- [DSPy Examples](#dspy-examples)
  - [Projects](#projects)
    - [Security Code Evaluator Agent](#security-code-evaluator-agent)
      - [Usage](#usage)
      - [Output Format](#output-format)
      - [Example Output](#example-output)
    - [GitHub Security Diff Evaluator](#github-security-diff-evaluator)
      - [Usage](#usage-1)
      - [Output Format](#output-format-1)
    - [Bandit CTF Solver](#bandit-ctf-solver)
      - [Features](#features)
      - [Usage](#usage-2)

## Projects

### Security Code Evaluator Agent
Located in `security_eval_agent.py`, this tool:
- Analyzes code for security vulnerabilities using LLM-powered evaluation
- Uses Qwen 2.5 Coder model via Ollama for analysis
- Processes the SecurityEval dataset (120 examples of potentially insecure code)
- Provides detailed security analysis, vulnerability lists, and verdicts
- Saves results incrementally in JSONL format

#### Usage
```bash
# Ensure you have Ollama installed and Qwen model pulled
ollama pull qwen2.5-coder

# Install required packages
pip install dspy-ai datasets litellm

# Run the security evaluation
python security_eval_agent.py
```

#### Output Format
The tool generates two files in the `datasets/` directory:
- `security_evaluated_dataset.jsonl`: Contains the analyzed examples with:
  - Original prompt and code
  - Security analysis
  - List of identified vulnerabilities
  - Final verdict (SECURE/INSECURE)
- `error_log.txt`: Logs any errors encountered during processing

#### Example Output
```json
{
  "ID": "example_id",
  "Prompt": "Original prompt that generated the code",
  "Insecure_code": "The potentially vulnerable code",
  "security_analysis": "Detailed analysis of security issues",
  "vulnerabilities": ["List", "of", "vulnerabilities"],
  "verdict": "INSECURE - Contains SQL injection vulnerability"
}
```

### GitHub Security Diff Evaluator
Located in `github_security_diff_evaluator.py`, this tool:
- Analyzes security implications of code changes between GitHub releases
- Uses GitHub API to fetch commit information and diffs
- Evaluates each changed file for potential security risks
- Tracks commit authors and metadata
- Provides risk levels and recommendations

#### Usage
```bash
# Set your GitHub token
export GITHUB_TOKEN='your-token-here'

# Run the analysis
python github_security_diff_evaluator.py
```

#### Output Format
Generates JSONL files in `output/github_diffs/` with detailed analysis:
```json
{
  "sha": "commit-sha",
  "author": "github-username",
  "commit_message": "commit message",
  "date": "2024-01-01T00:00:00Z",
  "file_path": "path/to/changed/file",
  "security_analysis": "detailed analysis",
  "risk_level": "HIGH/MEDIUM/LOW",
  "vulnerabilities": ["list", "of", "vulnerabilities"],
  "recommendations": ["security", "recommendations"]
}
```

### Bandit CTF Solver
Located in [`bandit_ctf_solver.py`](bandit_ctf_solver.py), this tool:
- Automates solving OverTheWire Bandit CTF challenges
- Uses LLM-powered command generation via DSPy
- Maintains progress and discovered passwords between sessions
- Handles SSH connections and command execution asynchronously

#### Features
- Automatic level progression
- AI-driven command generation
- Progress persistence
- Pattern-based password detection
- Detailed execution logging

#### Usage
```bash
# Install required packages
pip install dspy-ai asyncssh litellm

# Start Ollama and pull the LLaMA model
ollama pull llama3.2

# Run the solver
python dspy_bandit_ctf_solver.py
```

The tool saves progress in the following format:

```json
{
  "current_level": 1,
  "passwords": {
    "bandit0": "bandit0",
    "bandit1": "discovered_password"
  }
}
```