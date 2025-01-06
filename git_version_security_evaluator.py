import dspy
import json
from typing import Dict, List
import os
from datetime import datetime
import litellm
from github import Github, GithubException
from base64 import b64decode

# Enable LiteLLM parameter dropping and configure DSPy
litellm.drop_params = True
lm = dspy.LM('ollama/qwen2.5-coder', api_base='http://localhost:11434')
dspy.configure(lm=lm)

# Configure GitHub API
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("Please set GITHUB_TOKEN environment variable")
gh = Github(GITHUB_TOKEN)

def get_available_tags(repo) -> List[str]:
    """Get list of available tags for a repository"""
    try:
        return [tag.name for tag in repo.get_tags()]
    except GithubException as e:
        print(f"Error fetching tags: {e}")
        return []

def get_default_example() -> tuple:
    """Returns default example repository and tags"""
    return (
        "GangGreenTemperTatum/DOMspy",  # Default repo
        "v0.0.1",                       # First release
        "v0.0.2"                        # Second release
    )

class SecurityDiffSignature(dspy.Signature):
    """Evaluates code diffs for security vulnerabilities"""
    diff = dspy.InputField(desc="Code diff to evaluate")
    file_path = dspy.InputField(desc="Path of the changed file")
    commit_msg = dspy.InputField(desc="Commit message")
    security_analysis = dspy.OutputField(desc="Detailed security analysis of the changes")
    risk_level = dspy.OutputField(desc="HIGH/MEDIUM/LOW risk assessment")
    vulnerabilities = dspy.OutputField(desc="List of potential vulnerabilities introduced")
    recommendations = dspy.OutputField(desc="Security recommendations for the changes")

class GitHubDiffEvaluator(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SecurityDiffSignature)

    def forward(self, repo_name: str, commit_sha: str, diff: str, commit_message: str):
        return self.predictor(
            repo_name=repo_name,
            commit_sha=commit_sha,
            diff=diff,
            commit_message=commit_message
        )

def analyze_release_diff(repo_name: str, base_tag: str, head_tag: str) -> Dict:
    """Analyze security implications of changes between two releases"""
    try:
        os.makedirs('output/github_diffs', exist_ok=True)
        output_file = f"output/github_diffs/{repo_name.replace('/', '_')}_{base_tag}_to_{head_tag}.jsonl"

        print(f"Fetching repository {repo_name}...")
        repo = gh.get_repo(repo_name)

        # Get available tags
        available_tags = get_available_tags(repo)
        if not available_tags:
            print("No tags found in repository.")
            print(f"Available releases: https://github.com/{repo_name}/releases")
            return None

        print("\nAvailable tags:")
        for tag in available_tags:
            print(f"  - {tag}")

        # Validate tags exist
        if base_tag not in available_tags:
            print(f"\nError: Base tag '{base_tag}' not found.")
            print(f"Please choose from available tags above.")
            return None
        if head_tag not in available_tags:
            print(f"\nError: Head tag '{head_tag}' not found.")
            print(f"Please choose from available tags above.")
            return None

        print(f"\nComparing {base_tag} to {head_tag}...")
        try:
            comparison = repo.compare(base_tag, head_tag)
            # Convert PaginatedList to list and get count
            commits = list(comparison.commits)
            commit_count = len(commits)
        except GithubException as e:
            if e.status == 404:
                print(f"Error: Tags not found. Ensure both {base_tag} and {head_tag} exist.")
                return None
            raise

        evaluator = dspy.ChainOfThought(SecurityDiffSignature)
        analysis_results = []

        print(f"Analyzing {commit_count} commits...")
        for commit in commits:
            try:
                # Get the full commit object to access files
                full_commit = repo.get_commit(commit.sha)
                for file in full_commit.files:
                    if not file.patch:  # Skip if no diff available
                        continue

                    result = evaluator(
                        diff=file.patch,
                        file_path=file.filename,
                        commit_msg=full_commit.commit.message
                    )

                    analysis = {
                        'sha': commit.sha,
                        'author': commit.author.login if commit.author else 'Unknown',
                        'date': commit.commit.author.date.isoformat(),
                        'file_path': file.filename,
                        'security_analysis': result.security_analysis,
                        'risk_level': result.risk_level,
                        'vulnerabilities': result.vulnerabilities,
                        'recommendations': result.recommendations,
                        'changes': {
                            'additions': file.additions,
                            'deletions': file.deletions,
                            'changes': file.changes
                        }
                    }

                    with open(output_file, 'a') as f:
                        f.write(json.dumps(analysis) + '\n')

                    analysis_results.append(analysis)

                    if result.risk_level == 'HIGH':
                        print(f"\n⚠️  High risk change in {file.filename}")
                        print(f"Vulnerabilities: {result.vulnerabilities}")

            except GithubException as e:
                if e.status == 403:  # Rate limit exceeded
                    print(f"Rate limit exceeded. Waiting for reset...")
                    from time import sleep
                    sleep(60)  # Wait a minute before retrying
                    continue
                print(f"Error analyzing commit {commit.sha[:8]}: {e}")
                continue

        return {
            'repo': repo_name,
            'base': base_tag,
            'head': head_tag,
            'commits_analyzed': commit_count,
            'output_file': output_file,
            'results': analysis_results
        }

    except Exception as e:
        print(f"Error analyzing repo {repo_name}: {e}")
        print(f"Error details: {str(e)}")  # Add more error details
        return None

if __name__ == "__main__":
    DEFAULT_REPO, DEFAULT_BASE, DEFAULT_HEAD = get_default_example()

    # Get repository and tags from user input, use defaults if empty
    REPO = input(f"Enter repository (press Enter for default '{DEFAULT_REPO}'): ").strip() or DEFAULT_REPO

    try:
        repo = gh.get_repo(REPO)
        tags = get_available_tags(repo)

        if tags:
            print("\nAvailable tags:")
            for tag in tags:
                print(f"  - {tag}")

            BASE_TAG = input(f"Enter base version/tag (press Enter for '{DEFAULT_BASE}'): ").strip() or DEFAULT_BASE
            HEAD_TAG = input(f"Enter head version/tag (press Enter for '{DEFAULT_HEAD}'): ").strip() or DEFAULT_HEAD
        else:
            print(f"\nUsing default tags: {DEFAULT_BASE} -> {DEFAULT_HEAD}")
            BASE_TAG = DEFAULT_BASE
            HEAD_TAG = DEFAULT_HEAD

        results = analyze_release_diff(REPO, BASE_TAG, HEAD_TAG)

        if results:
            print("\nAnalysis Summary:")
            print(f"Repository: {results['repo']}")
            print(f"Commits Analyzed: {results['commits_analyzed']}")
            print(f"Results saved to: {results['output_file']}")

            # Show summary of high-risk changes
            high_risk = [r for r in results['results'] if r['risk_level'] == 'HIGH']
            if high_risk:
                print(f"\nFound {len(high_risk)} high-risk changes!")
                for risk in high_risk:
                    print(f"\nFile: {risk['file_path']}")
                    print(f"Author: {risk['author']}")
                    print(f"Changes: +{risk['changes']['additions']} -{risk['changes']['deletions']}")
                    print(f"Vulnerabilities: {risk['vulnerabilities']}")
                    print(f"Recommendations: {risk['recommendations']}")

    except GithubException as e:
        print(f"Error accessing repository: {e}")
        print("Please check the repository name and your access permissions.")
