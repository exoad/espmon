"""Everything that runs without the board: compiles each Kira project, runs the host tests, and with --mutants also runs
the mutation checks (tests/mutants.py). Exit 0 only when every step passes.

    .venv/Scripts/python tests/check.py
    .venv/Scripts/python tests/check.py --mutants
"""
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
KIRA = os.path.join(ROOT, "vendor", "kira", "build", "install", "kira", "bin", "kira.bat")
PY = os.path.join(ROOT, ".venv", "Scripts", "python.exe")
PROJECTS = ["esp32", "tests", "espmon", "hwtest", "examples"]


def step(title, args, cwd):
    print(f"== {title}")
    ran = subprocess.run(args, cwd=cwd, capture_output=True, text=True)
    output = ran.stdout + ran.stderr
    errors = [line for line in output.splitlines() if " error:" in line or "Report #" in line]
    if ran.returncode != 0 or errors:
        print(output[-2000:])
        print(f"   FAILED ({ran.returncode})")
        return False
    print("   ok")
    return True


def main(argv):
    ok = True
    for name in PROJECTS:
        ok = step(f"compile {name}", [KIRA, "--target", "py"], os.path.join(ROOT, name)) and ok
    ok = step("host tests", [PY, os.path.join(ROOT, "tests", "esp32_test_kira.py")], ROOT) and ok
    if "--mutants" in argv:
        ok = step("mutation tests", [PY, os.path.join(ROOT, "tests", "mutants.py")], ROOT) and ok
    print("all checks passed" if ok else "some checks failed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
