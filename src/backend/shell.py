
import subprocess


def sh(cmd, timeout=600):
    print(f"[RUNNING] {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Command timed out after {timeout}s")
        raise

    if result.returncode != 0:
        print(f"[ERROR] Command failed with exit code {result.returncode}")
        print(result.stderr[-1500:])
        raise RuntimeError("Command failed")

    print("[SUCCESS] Command completed")
    return result.stdout.strip()
