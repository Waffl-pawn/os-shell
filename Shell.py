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

def parse_redirects(line: str):
    argv = split_words(line)
    in_file = None
    out_file = None

    if ">" in line:
        left, right = line.split(">", 1)
        argv = split_words(left)
        out_file = right.strip()

    if "<" in line:
        left, right = line.split("<", 1)
        argv = split_words(left)
        in_file = right.strip()

    return argv, in_file, out_file

def run_external(argv: list[str], in_file=None, out_file=None) -> None:
    command = argv[0]
    execute = find_executable(command)
    if execute is None:
        osprint(f"{command}: command not found :(")
        return
    
    pid = os.fork()
    if pid == 0:
        #Child
        try:
            if in_file is not None:
                fd = os.open(in_file, os.O_RDONLY)
                os.dup2(fd, 0)
                os.close(fd)

            if out_file is not None:
                fd = os.open(out_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
                os.dup2(fd, 1)
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

def run_pipe(left_argv, right_argv):
    if not left_argv or not right_argv:
        return

    pr, pw = os.pipe()

    pid1 = os.fork()
    if pid1 == 0:
        # LEFT child: stdout -> pipe write end
        exe1 = find_executable(left_argv[0])
        if exe1 is None:
            osprint(f"{left_argv[0]}: command not found")
            os._exit(127)

        os.dup2(pw, 1)
        os.close(pr)
        os.close(pw)

        try:
            os.execve(exe1, left_argv, os.environ)
        except Exception:
            os._exit(127)

    pid2 = os.fork()
    if pid2 == 0:
        # RIGHT child: stdin <- pipe read end
        exe2 = find_executable(right_argv[0])
        if exe2 is None:
            osprint(f"{right_argv[0]}: command not found")
            os._exit(127)

        os.dup2(pr, 0)
        os.close(pw)
        os.close(pr)

        try:
            os.execve(exe2, right_argv, os.environ)
        except Exception:
            os._exit(127)

    # PARENT
    os.close(pr)
    os.close(pw)
    os.waitpid(pid1, 0)
    os.waitpid(pid2, 0)

    
def main():
    while True:

        #get prompt
        prompt = os.environ.get("PS1", "\(*_*)/ ")
        os.write(1, prompt.encode())

        line = sys.stdin.readline()
        if line == "":
            break
        line = line.rstrip("\n")

        #detecting pipes
        if "|" in line:
            left, right = line.split("|", 1)
            left_argv = split_words(left)
            right_argv = split_words(right)
            run_pipe(left_argv, right_argv)
            continue

        argv, in_file, out_file = parse_redirects(line)
        
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

        run_external(sys.argv, in_file, out_file)
        
    if __name__ == "__main__":
        main()
        




if __name__ == "__main__":
    main()