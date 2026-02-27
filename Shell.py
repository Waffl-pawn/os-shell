#! /usr/bin/env python3
import os
import sys
import re

def osprint(msg: str):
    os.write(2, (msg + "\n").encode())

def split_words(line: str) -> list[str]:
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

def parse_redirect_out(line: str):
    # returns (argv, out_file or None)
    if ">" or "<" not in line:
        return split_words(line), None

    if ">" in line:
        left, right = line.split(">", 1)
        argv = split_words(left)
        out_file = right.strip()
        if out_file == "":
            return argv, None  # treat as no redirect (or print error to stderr)
    
    if "<" in line:
        
    return argv, out_file

def run_external(argv: list[str], out_file: str | None = None) -> None:
    command = argv[0]
    execute = find_executable(command)
    if execute is None:
        osprint(f"{command}: command not found :(")
        return
    
    pid = os.fork()
    if pid == 0:
        #Child
        try:
            if out_file is not None:
                fd = os.open(out_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                os.dup2(fd, 1)     # stdout -> file
                os.close(fd)
            os.execve(execute, argv, os.environ)
        except Exception:
            os._exit(127)
    else:
        #parent waits
        _, status = os.waitpid(pid, 0)
        if os.WIFEXITED(status):
            code = os.WEXITSTATUS(status)
            if code != 0:
                osprint(f"Program terminated with exit code {code}.")
        elif os.WIFSIGNALED(status):
            sig = os.WTERMSIG(status)
            osprint(f"Program terminated by singal {sig}.")

def main():
    while True:

        #get prompt
        prompt = os.environ.get("PS1", "\(*_*)/ ")
        os.write(1, prompt.encode())

        line = sys.stdin.readline()
        if line =="":
            line = None
        line = line.rstrip("\n")

        argv, outputFile = parse_redirect_out(line)
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

        run_external(argv, outputFile)
        
    if __name__ == "__main__":
        main()
        




if __name__ == "__main__":
    main()