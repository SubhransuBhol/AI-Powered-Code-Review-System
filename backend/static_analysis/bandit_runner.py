import subprocess
import json


def run_bandit(file_path):

    result = subprocess.run(
        [
            "bandit",
            "-f",
            "json",
            file_path
        ],
        capture_output=True,
        text=True
    )

    if not result.stdout:
        return []

    try:

        data = json.loads(result.stdout)

        findings = []

        for issue in data.get(
            "results",
            []
        ):

            findings.append(
                f"[{issue['test_id']}] {issue['issue_text']}"
            )

        return findings

    except Exception:

        return []