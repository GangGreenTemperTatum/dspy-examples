import dspy
import asyncio
import asyncssh
import time
from typing import Dict, List, Optional
import re
import json
import os
import litellm
import requests
import html
import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

# Configure DSPy with local model
litellm.drop_params = True
lm = dspy.LM('ollama/llama3.2', api_base='http://localhost:11434')
dspy.configure(lm=lm)

console = Console()
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=console, markup=True)]
)
log = logging.getLogger("bandit_solver")

def get_bandit_level_description(level: int) -> str:
    """Fetch the level goal from OverTheWire website"""
    try:
        search = r"Level Goal</h2>(.+)<h2"
        response = requests.get(f"https://overthewire.org/wargames/bandit/bandit{level}.html")
        response.raise_for_status()
        goal: str = re.findall(search, response.text, re.DOTALL)[0]
        goal = goal.replace("<p>", "").replace("</p>", "").strip()
        return html.unescape(re.sub("<.*?>", "", goal))
    except Exception as e:
        return f"Failed to fetch level description: {e}"

class FindPasswordModule(dspy.Module):
    """Helper module to identify passwords in command output"""
    def forward(self, output: str) -> Optional[str]:
        """Extracts password-like strings from command output"""
        # Simple password pattern for bandit games
        matches = re.findall(r'[a-zA-Z0-9]{32}', output)
        return matches[0] if matches else None

class CTFSignature(dspy.Signature):
    """Analyzes CTF challenge context and suggests commands"""
    level = dspy.InputField(desc="Current CTF level number")
    banner = dspy.InputField(desc="Initial connection banner and challenge goal description")
    current_output = dspy.InputField(desc="Current terminal output from last command")
    history = dspy.InputField(desc="Previously executed commands and their outputs")
    failed_attempts = dspy.InputField(desc="Commands that did not work and why")
    next_command = dspy.OutputField(desc="Next command to execute based on context")
    reasoning = dspy.OutputField(desc="Explanation of why this command should help solve the challenge")
    expected_output = dspy.OutputField(desc="What we expect to find that would indicate success")

    def __init__(self):
        super().__init__()

class CTFSolver(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(CTFSignature)
        self.attempt_history = {}
        self.password_finder = FindPasswordModule()
        self.current_level = 0
        self.console = Console()

    def forward(self, level: int, banner: str, current_output: str, history: List[str]):
        # Get failed attempts for this level
        failed_attempts = self.attempt_history.get(level, [])

        # Format history with outputs
        formatted_history = "\n".join([
            f"Command: {cmd}\nOutput: {out}"
            for cmd, out in history[-5:]
        ])

        # Enhance the context by highlighting important parts
        enhanced_banner = (
            f"CURRENT LEVEL: {level}\n"
            f"CHALLENGE GOAL:\n{banner}\n"
            f"CURRENT DIRECTORY CONTENTS:\n{current_output}\n"
            f"PREVIOUS ATTEMPTS:\n{formatted_history}\n"
            f"FAILED COMMANDS:\n{chr(10).join(failed_attempts)}"
        )

        try:
            self.console.print("[cyan]Model Input Context:[/]")
            self.console.print(Panel(enhanced_banner, title="Context Being Sent to Model"))

            result = self.predictor(
                level=level,
                banner=enhanced_banner,
                current_output=current_output,
                history=formatted_history,
                failed_attempts="\n".join(failed_attempts)
            )

            # Handle response and validate command
            if not isinstance(result, dict) and hasattr(result, '_asdict'):
                result = result._asdict()

            # Validate the command makes sense for the context
            command = result['next_command']
            if not self._is_valid_command(command, level, banner):
                self.console.print(f"[yellow]Warning: Command '{command}' might not be relevant for this level[/]")
                # Fall back to basic file reading for level 1
                if level == 1:
                    return dspy.Prediction(
                        next_command="cat readme",
                        reasoning="The password is explicitly stated to be in the 'readme' file",
                        expected_output="A 32-character password string"
                    )

            return dspy.Prediction(**result)

        except Exception as e:
            self.console.print(f"[red]Error in model prediction: {e}[/]")
            # Provide smart fallbacks based on level
            if level == 1:
                return dspy.Prediction(
                    next_command="cat readme",
                    reasoning="Falling back to reading the readme file as specified in challenge",
                    expected_output="Password string"
                )
            return dspy.Prediction(
                next_command="ls -la",
                reasoning="Error occurred, starting with basic recon",
                expected_output="Directory listing"
            )

    def _is_valid_command(self, command: str, level: int, banner: str) -> bool:
        """Validate if the command makes sense for the current level"""
        if level == 1 and 'readme' not in command and 'cat' not in command:
            return False
        if any(dangerous in command for dangerous in ['rm', 'mv', '>', '>>']):
            return False
        return True

class BanditGame:
    def __init__(self, hostname: str = "bandit.labs.overthewire.org", port: int = 2220):
        self.hostname = hostname
        self.port = port
        self.conn = None
        self.current_level = 0
        self.solver = CTFSolver()
        self.progress_file = "ctf_progress.json"
        self.command_history = []
        self.level_goals = {}
        self.load_progress()
        self.console = Console()

    def load_progress(self):
        """Load saved progress and passwords"""
        try:
            with open(self.progress_file, 'r') as f:
                self.progress = json.load(f)
        except FileNotFoundError:
            self.progress = {
                'current_level': 0,
                'passwords': {'bandit0': 'bandit0'}  # Starting password
            }
            self.save_progress()

    def save_progress(self):
        """Save current progress and passwords"""
        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    async def get_level_info(self) -> str:
        """Get challenge information from initial connection"""
        try:
            if self.current_level == 0:
                return "Level 0: Connect using SSH with username bandit0 and password bandit0"

            # Get level goal if not cached
            if self.current_level not in self.level_goals:
                self.level_goals[self.current_level] = get_bandit_level_description(self.current_level)

            # Print challenge description in a nice panel
            self.console.print(Panel(
                self.level_goals[self.current_level],
                title=f"[bold cyan]Level {self.current_level} Challenge Description[/]",
                border_style="cyan"
            ))

            banner = await self.execute_command("cat /etc/motd 2>/dev/null; cat readme* 2>/dev/null")

            banner = f"{banner}\n\nLevel Goal:\n{self.level_goals[self.current_level]}"

            # Try to find relevant files for the level
            find_cmd = (
                "find . -type f -readable ! -executable -size -10M 2>/dev/null || "
                "ls -la; find . -name readme* 2>/dev/null; find . -name level* 2>/dev/null"
            )
            hints = await self.execute_command(find_cmd)

            return f"{banner}\n\nAvailable files:\n{hints}"
        except Exception as e:
            log.error(f"Error getting level info: {e}")
            return f"Error getting level info: {e}"

    async def connect(self, level: int) -> bool:
        """Connect to specific bandit level using asyncssh"""
        try:
            username = f"bandit{level}"
            if level == 0:
                password = "bandit0"  # First level always uses this password
            else:
                password = self.progress['passwords'].get(username)

            if not password:
                print(f"No password found for level {level}")
                return False

            print(f"Connecting to {self.hostname}:{self.port} as {username}")
            self.conn = await asyncssh.connect(
                self.hostname,
                self.port,
                username=username,
                password=password,
                known_hosts=None
            )
            self.current_level = level
            return True
        except asyncssh.Error as e:
            print(f"Connection error: {e}")
            return False

    async def execute_command(self, command: str) -> str:
        """Execute command asynchronously and return output"""
        try:
            result = await self.conn.run(command)
            output = result.stdout + result.stderr
            # Store command and output together
            self.command_history.append((command, output))
            return output
        except asyncssh.Error as e:
            error_msg = f"Error executing command: {e}"
            self.command_history.append((command, error_msg))
            return error_msg

    async def find_password_for_level(self, level: int, output: str) -> Optional[str]:
        """Find password based on level-specific patterns with validation"""
        if level == 0:
            return "bandit0"

        # Basic password validation
        def is_valid_password(pwd: str) -> bool:
            return len(pwd) == 32 and '/' not in pwd

        cleaned_output = re.sub(r'\s+', ' ', output).strip()

        matches = re.findall(r'[a-zA-Z0-9]{32}', cleaned_output)
        valid_matches = [m for m in matches if is_valid_password(m)]

        if valid_matches:
            return valid_matches[0]
        return None

    async def solve_level(self):
        """Attempt to solve current level asynchronously"""
        if not self.conn:
            if not await self.connect(self.current_level):
                return False

        if self.current_level == 0:
            self.progress['current_level'] = 1
            return True

        banner = await self.get_level_info()
        log.info(f"[bold green]Starting Level {self.current_level}[/]")

        output = await self.execute_command("pwd; ls -la; whoami; id")
        attempts = 0
        max_attempts = 10

        while attempts < max_attempts:
            result = self.solver(
                level=self.current_level,
                banner=banner,
                current_output=output,
                history=self.command_history[-5:]  # Last 5 attempts with outputs
            )

            self.console.print(Panel(
                f"[yellow]Reasoning:[/] {result.reasoning}\n\n"
                f"[green]Executing:[/] {result.next_command}\n\n"
                f"[cyan]Expecting:[/] {result.expected_output}",
                title=f"[bold]Attempt {attempts + 1}/{max_attempts}[/]",
                border_style="blue"
            ))

            output = await self.execute_command(result.next_command)
            log.debug(f"Command output: {output[:200]}...")

            password = await self.find_password_for_level(self.current_level, output)

            if password:
                if len(password) == 32 and '/' not in password:
                    next_level = self.current_level + 1
                    self.console.print(f"[bold green]Found valid password: {password}[/]")
                    self.progress['passwords'][f"bandit{next_level}"] = password
                    self.save_progress()
                    return True
                else:
                    log.warning(f"Invalid password pattern found: {password}")

            attempts += 1
            await asyncio.sleep(1)

        log.error(f"Failed to solve level {self.current_level} after {max_attempts} attempts")
        return False

async def main():
    game = BanditGame()

    try:
        while True:
            console.print(f"\n[blue]Attempting level {game.current_level}[/]")
            if await game.solve_level():
                console.print(f"[green]Completed level {game.current_level}![/]")
                game.current_level += 1
                game.progress['current_level'] = game.current_level
                game.save_progress()
            else:
                console.print(f"[red]Failed to solve level {game.current_level}[/]")
                break
    except KeyboardInterrupt:
        console.print("[yellow]\nSaving progress and exiting...[/]")
        game.save_progress()
    finally:
        if game.conn:
            game.conn.close()

if __name__ == "__main__":
    asyncio.run(main())
