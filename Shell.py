#! /usr/bin/env python3
import os
import sys
import re

def osprint(msg: str):
    os.write(2, (msg + "\n").encode())

def spit_words(line: str) -> list[str]:
    line = line.strip()
    if not line:
        return []
    return re.split(r"\s+", line)

def find_executable(command: str) -> str | None:
    if "/" in command:
        if os.access(command, os.X_OK):
            return command
        else:
            return None
        
    path_env = os.environ.get("PATH", "")
    for d in path_env.split(":"):
        if d == "":
            d = "."
        operation = os.path.join(d, command)
        if os.access(operation, os.X_OK) and os.path.isfile(operation):
            return operation
    return None

def run_external(argv: list[str]) -> None:
    command = argv[0]
    execute = find_executable(command)
    if execute is None:
        osprint(f"{command}: command not found :(")
        return

def main():
    while True:

        #get prompt
        prompt = os.environ.get("PS1", "\(*_*)/ ")
        os.write(1, prompt.encode())

        line = sys.stdin.readline()
        if line =="":
            line = None
        line = line.rstrip("\n")

        argv = spit_words(line)
        if not argv:
            continue

        if argv[0] == "exit":
            sys.exit()

        if argv[0] == "cd":
            target = argv[1] if len(argv) > 1 else os.environ.get("HOME","/")
            try:
                os.chdir(target)
            except Exception:
                osprint(f"cd: no such file or directory: {target}")
            continue

        run_external(argv)
        
        




if __name__ == "__main__":
    main()