from utils.github_cloner import clone_repository

repo = clone_repository(
    "https://github.com/pallets/flask.git"
)

print(repo)
