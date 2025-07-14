# run_with_env.py
from dotenv import load_dotenv
import os
import subprocess

load_dotenv()  # Loads from .env into environment variables

env = os.environ.copy()

print("✅ Injecting JIRA env:")
print(f"JIRA_URL={env.get('JIRA_URL')}")
print(f"JIRA_USERNAME={env.get('JIRA_USERNAME')}")

subprocess.run([
    "uvx", "mcp-atlassian",
    "--transport", "streamable-http",
    "--port", "9000"
], env=env)
