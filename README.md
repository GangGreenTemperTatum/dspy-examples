# DSPy Examples

This repository contains practical examples of using DSPy for AI-powered code analysis and security evaluation.

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
