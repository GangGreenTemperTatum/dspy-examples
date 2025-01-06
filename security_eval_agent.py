import dspy
from datasets import load_dataset
import json
from typing import List, Optional
import litellm

# Enable LiteLLM parameter dropping
litellm.drop_params = True

# Configure local model
print("Configuring qwen2.5-coder using Ollama...")
lm = dspy.LM('ollama/qwen2.5-coder', api_base='http://localhost:11434')
dspy.configure(lm=lm)

# Define the signature for security evaluation
class SecurityEvalSignature(dspy.Signature):
    """Evaluates code for security vulnerabilities"""
    prompt = dspy.InputField(desc="The original prompt that generated the code")
    code = dspy.InputField(desc="The code to evaluate for security issues")
    security_analysis = dspy.OutputField(desc="Detailed security analysis of the code")
    vulnerabilities = dspy.OutputField(desc="List of identified vulnerabilities")
    verdict = dspy.OutputField(desc="SECURE or INSECURE with brief explanation")

# Create the DSPy module for security evaluation
class SecurityEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SecurityEvalSignature)

    def forward(self, prompt: str, code: str):
        return self.predictor(prompt=prompt, code=code)

# Load the dataset
print("Loading SecurityEval dataset...")
dataset = load_dataset("s2e-lab/SecurityEval")
train_data = dataset["train"].to_list()  # Convert to list for easier access
print(f"Loaded {len(train_data)} examples")

# Create datasets directory if it doesn't exist
import os
os.makedirs('datasets', exist_ok=True)
OUTPUT_FILE = "datasets/security_evaluated_dataset.jsonl"
ERROR_LOG = "datasets/error_log.txt"

# Process the dataset
def process_dataset():
    evaluator = SecurityEvaluator()

    # Check for existing progress
    try:
        with open(OUTPUT_FILE, 'r') as f:
            processed = len(f.readlines())
        print(f"Found {processed} previously processed examples")
    except FileNotFoundError:
        processed = 0

    print("Evaluating code samples...")
    for idx, example in enumerate(train_data[processed:], start=processed):
        try:
            # Debug print
            print(f"\nProcessing example {idx + 1}:")
            print(f"Prompt: {example['Prompt'][:100]}...")

            result = evaluator(
                prompt=example['Prompt'],
                code=example['Insecure_code']
            )

            # Add evaluation results to the example
            enhanced_example = {
                'ID': example['ID'],
                'Prompt': example['Prompt'],
                'Insecure_code': example['Insecure_code'],
                'security_analysis': result.security_analysis,
                'vulnerabilities': result.vulnerabilities,
                'verdict': result.verdict
            }

            # Append each result immediately to file
            with open(OUTPUT_FILE, 'a') as f:
                f.write(json.dumps(enhanced_example) + '\n')

            print(f"✓ Processed and saved example {idx + 1}/{len(train_data)}")
            print(f"Verdict: {result.verdict}")

        except Exception as e:
            print(f"✗ Error processing example {idx + 1}: {str(e)}")
            # More detailed error logging
            with open(ERROR_LOG, 'a') as f:
                f.write(f"\nError on example {idx + 1}:\n")
                f.write(f"Example data: {str(example)}\n")
                f.write(f"Error: {str(e)}\n")
            continue

    return OUTPUT_FILE

# Modified main execution
if __name__ == "__main__":
    output_file = process_dataset()
    print(f"\nProcessing complete! Results saved to {output_file}")

    try:
        # Load and display a random evaluated example
        import random
        with open(output_file, 'r') as f:
            examples = [json.loads(line) for line in f]

        if examples:
            sample = random.choice(examples)
            print("\nRandom Example Evaluation:")
            print("-" * 50)
            print(f"Prompt: {sample['Prompt'][:200]}...")
            print(f"Verdict: {sample['verdict']}")
            print(f"Vulnerabilities: {sample['vulnerabilities']}")
    except FileNotFoundError:
        print("No results file found. Check error log for details.")
