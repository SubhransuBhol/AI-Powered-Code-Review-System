from static_analysis.bandit_runner import run_bandit

results = run_bandit(
    "../sample_project/database.py"
)

print("Findings:", len(results))

for finding in results:
    print(finding)