"""CI-provider-independent structural and distribution contract checks."""
import subprocess
import sys


def main():
    for command in [[sys.executable,'-m','unittest','discover','-s','tests','-v'],[sys.executable,'-m','harnessctl','check','--ci']]:
        result = subprocess.run(command,check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__=='__main__':
    raise SystemExit(main())
