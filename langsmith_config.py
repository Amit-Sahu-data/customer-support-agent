# langsmith_config.py
# This file sets up LangSmith observability
# LangSmith traces every agent call automatically once this is loaded

import os
from dotenv import load_dotenv

load_dotenv()

# --------------------------------------------------
# Why we set these as environment variables:
# LangSmith reads these automatically in the background
# No extra code needed anywhere else in the project
# Just import this file once at the start of any file
# --------------------------------------------------

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "customer-support-agent")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

def verify_langsmith():
    """
    Call this once at startup to confirm LangSmith is connected.
    Prints status so you know tracing is active.
    """
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project = os.getenv("LANGCHAIN_PROJECT", "")

    if not api_key:
        print("WARNING: LANGCHAIN_API_KEY not set — tracing disabled")
        return False

    if not api_key.startswith("lsv2"):
        print("WARNING: LANGCHAIN_API_KEY looks incorrect — should start with lsv2")
        return False

    print(f"LangSmith tracing ACTIVE")
    print(f"Project: {project}")
    print(f"Dashboard: https://smith.langchain.com")
    return True

if __name__ == "__main__":
    verify_langsmith()