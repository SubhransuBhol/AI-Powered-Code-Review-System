from git import Repo
import os
import time

def clone_repository(
    repo_url
):

    clone_path = (
        f"../uploads/github_repo_{int(time.time())}"
    )

    Repo.clone_from(
        repo_url,
        clone_path
    )

    return clone_path