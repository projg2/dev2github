import requests
from typing import Generator


class CodebergAPI:
    def __init__(self, owner: str, repo: str, token: str):
        self.owner = owner
        self.repo = repo
        self.token = token

    def __enter__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {self.token}",
                "Content-Type": "application/json",
            }
        )
        self.session.hooks = {
            "response": lambda r, *args, **kwargs: r.raise_for_status()
        }
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.session.close()

    @property
    def repos_baseurl(self) -> str:
        return f"https://codeberg.org/api/v1/repos/{self.owner}/{self.repo}"

    @property
    def orgs_baseurl(self) -> str:
        return f"https://codeberg.org/api/v1/orgs"

    def pulls(self) -> Generator[None, dict, None]:
        next_url = f"{self.repos_baseurl}/pulls?state=open"
        while True:
            r = self.session.get(next_url)
            yield from r.json()
            x = r.links.get("next")
            if not x:
                break
            next_url = x["url"]

    def set_pr_title(self, pr_id: int, title: str) -> None:
        self.session.patch(
            f"{self.repos_baseurl}/pulls/{pr_id}", json={"title": title}
        )

    def add_pr_labels(self, pr_id: int, labels: list[int]) -> None:
        self.session.patch(
            f"{self.repos_baseurl}/pulls/{pr_id}", json=({"labels": labels})
        )

    def labels(self) -> list[dict]:
        return self.session.get(f"{self.repos_baseurl}/labels").json()

    def commits(self, pr_id: int) -> list[dict]:
        return self.session.get(f"{self.repos_baseurl}/pulls/{pr_id}/commits").json()

    def files(self, pr_id: int) -> list[dict]:
        return self.session.get(f"{self.repos_baseurl}/pulls/{pr_id}/files").json()

    def get_reviews(self, pr_id: int) -> list[dict]:
        return self.session.get(f"{self.repos_baseurl}/pulls/{pr_id}/reviews").json()

    def create_review(self, pr_id: int, comment: str) -> None:
        # Does not appear to be possible to simply post comments
        # https://codeberg.org/api/swagger#/repository/repoCreatePullReview
        self.session.post(
            f"{self.repos_baseurl}/pulls/{pr_id}/reviews",
            json={
                "body": comment,
            },
        )

    def delete_review(self, pr_id: int, review_id: int) -> None:
        self.session.delete(f"{self.repos_baseurl}/pulls/{pr_id}/reviews/{review_id}")

    def teams(self, org: str) -> Generator[None, dict, None]:
        next_url = f"{self.orgs_baseurl}/{org}/teams"
        while True:
            r = self.session.get(next_url)
            t = r.json()
            import json; print(json.dumps(t, indent=2))
            yield from t
            x = r.links.get("next")
            if not x:
                break
            next_url = x["url"]
