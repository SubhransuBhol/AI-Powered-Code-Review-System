from github_review_service import (
    review_github_repository
)

result = review_github_repository(
    "https://github.com/SubhransuBhol/AI-Code-Reviewer-sample_project.git"
)

print(result)
