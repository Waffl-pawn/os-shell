#!/usr/bin/env python3
import os
import sys
import re

def eprint(msg: str):
    os.write(2, (msg + "\n").encode())

def get_prompt() -> str:
    # PS1 environment variable controls prompt; default "$ "
    return os.environ.get("PS1", "$ ")

def read_line() -> str | None:
    # Read one line from stdin (fd 0). Return None on EOF.
    try:
        line = sys.stdin.readline()
    except Exception:
        return None
    if line == "":
        return None
    return line.rstrip("\n")

def split_words(line: str) -> list[str]:
    # Simple whitespace split (we’ll improve later if needed)
    line = line.strip()
    if not line:
        return []
    return re.split(r"\s+", line)

def find_executable(cmd: str) -> str | None:
    # If user gave a path (contains /), don’t search PATH
    if "/" in cmd:
        return cmd if os.access(cmd, os.X_OK) else None

    path_env = os.environ.get("PATH", "")
    for d in path_env.split(":"):
        if d == "":
            d = "."
        candidate = os.path.join(d, cmd)
        if os.access(candidate, os.X_OK) and os.path.isfile(candidate):
            return candidate
    return None

def run_external(argv: list[str]) -> None:
    cmd = argv[0]
    exe = find_executable(cmd)
    if exe is None:
        # Required format: "lx: command not found"
        eprint(f"{cmd}: command not found")
        return

    pid = os.fork()
    if pid == 0:
        # Child
        try:
            os.execve(exe, argv, os.environ)
        except Exception:
            # If execve fails for some reason, exit non-zero
            os._exit(127)
    else:
        # Parent waits
        _, status = os.waitpid(pid, 0)
        if os.WIFEXITED(status):
            code = os.WEXITSTATUS(status)
            if code != 0:
                eprint(f"Program terminated with exit code {code}.")
        elif os.WIFSIGNALED(status):
            # optional: treat signals as non-zero
            sig = os.WTERMSIG(status)
            eprint(f"Program terminated by signal {sig}.")

def handle_builtin(argv: list[str]) -> bool:
    # Return True if handled (so caller shouldn’t exec)
    if not argv:
        return True

    if argv[0] == "exit":
        sys.exit(0)

    if argv[0] == "cd":
        # bash: cd with no args goes to HOME
        target = argv[1] if len(argv) > 1 else os.environ.get("HOME", "/")
        try:
            os.chdir(target)
        except Exception:
            eprint(f"cd: no such file or directory: {target}")
        return True

    return False

def main():
    while True:
        # Prompt (write to stdout)
        prompt = get_prompt()
        os.write(1, prompt.encode())

        line = read_line()
        if line is None:
            # EOF => exit, like bash in scripts
            break

        argv = split_words(line)
        if not argv:
            continue

        if handle_builtin(argv):
            continue

        run_external(argv)

if __name__ == "__main__":
    main()
