"""Verifies model adapter import contracts without calls to an AI provider."""
from __future__ import annotations
import json
import importlib.metadata

def check():
    from tinytroupe.agent import TinyPerson
    from tinytroupe.environment import TinyWorld
    from mem0 import Memory
    from crewai import Agent, Task, Crew, Process
    symbols = (TinyPerson,TinyWorld,Memory,Agent,Task,Crew,Process)
    if not all(callable(s) or isinstance(s, type) for s in symbols):
        raise RuntimeError("An expected model adapter class is unavailable")
    versions={}
    for package in ("tinytroupe","mem0ai","crewai"):
        try:
            versions[package]=importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package]="git_source_or_no_package_metadata"
    return {"model_adapter_imports":"PASS","versions":versions,"live_model_calls":0,
            "publish_to_whatsapp":False}

if __name__=="__main__":
    print(json.dumps(check(),ensure_ascii=False,indent=2))
