#!/usr/bin/env python3
"""Validate a GitHub token and install it into the personal Anubis namespace."""

import getpass
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


NAMESPACE = "anubis"
API_IMAGE_PREFIX = "192.168.1.8:30082/anubis/api:"


def run(command, *, input_data=None):
    return subprocess.run(
        command,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def main():
    token = getpass.getpass("GitHub personal access token (hidden): ").strip()
    if not token:
        print("No token entered.", file=sys.stderr)
        return 1

    request = Request(
        "https://api.github.com/user",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "Anubis-personal-setup",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            github_user = json.load(response)
    except HTTPError as error:
        print(f"GitHub rejected the token (HTTP {error.code}).", file=sys.stderr)
        return 1
    except URLError:
        print("Could not reach GitHub to validate the token.", file=sys.stderr)
        return 1

    login = github_user.get("login")
    if not login:
        print("GitHub did not return an account for this token.", file=sys.stderr)
        return 1

    check = run([
        "kubectl", "-n", NAMESPACE, "get", "deployment", "anubis-api",
        "-o", "jsonpath={.spec.template.spec.containers[0].image}",
    ])
    if check.returncode or not check.stdout.decode().startswith(API_IMAGE_PREFIX):
        print("The current Kubernetes context is not the personal Anubis cluster.", file=sys.stderr)
        return 1

    with tempfile.TemporaryDirectory(prefix="anubis-github-") as temp_dir:
        temp_path = Path(temp_dir)
        token_file = temp_path / "token"
        credentials_file = temp_path / "credentials"
        token_file.write_text(token)
        credentials_file.write_text(f"https://x-access-token:{quote(token, safe='')}@github.com\n")
        token_file.chmod(0o600)
        credentials_file.chmod(0o600)

        secret = run([
            "kubectl", "create", "secret", "generic", "git",
            "--namespace", NAMESPACE,
            f"--from-file=token={token_file}",
            f"--from-file=credentials={credentials_file}",
            "--dry-run=client", "-o", "yaml",
        ])
        if secret.returncode:
            print("Could not prepare the GitHub secret with kubectl.", file=sys.stderr)
            return 1
        applied = run(["kubectl", "apply", "-f", "-"], input_data=secret.stdout)
        if applied.returncode:
            print("Could not install the GitHub secret in Anubis.", file=sys.stderr)
            return 1

    api_workloads = [
        "anubis-api",
        "anubis-infra-poller",
        "anubis-pipeline-api",
        "anubis-pipeline-poller",
        "anubis-rpc-default",
        "anubis-rpc-regrade",
        "anubis-rpc-theia",
        "anubis-theia-poller",
    ]
    restart = run([
        "kubectl", "-n", NAMESPACE, "rollout", "restart",
        *(f"deployment/{name}" for name in api_workloads),
    ])
    if restart.returncode:
        print("The secret is installed, but the Anubis API restart failed.", file=sys.stderr)
        return 1
    for name in api_workloads:
        ready = run([
            "kubectl", "-n", NAMESPACE, "rollout", "status",
            f"deployment/{name}", "--timeout=180s",
        ])
        if ready.returncode:
            print(f"The secret is installed, but {name} did not become ready.", file=sys.stderr)
            return 1

    reaper = run([
        "kubectl", "-n", NAMESPACE, "patch", "cronjob/anubis-github-reaper",
        "--type=merge", "-p", '{"spec":{"suspend":false}}',
    ])
    if reaper.returncode:
        print("The API is ready, but GitHub polling could not be enabled.", file=sys.stderr)
        print("Apply the personal Helm profile, then rerun this script.", file=sys.stderr)
        return 1

    print(f"GitHub account {login} is validated and linked to the Anubis namespace.")
    print("Open Profile in Anubis and choose Link GitHub; stop and relaunch active IDEs to load Git credentials.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
