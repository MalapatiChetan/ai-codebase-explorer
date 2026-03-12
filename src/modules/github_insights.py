"""GitHub repository and user insights backed only by the GitHub REST API."""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from src.utils.config import settings

logger = logging.getLogger(__name__)


class GitHubInsightsError(Exception):
    """Raised when GitHub insights cannot be retrieved."""


class GitHubInsightsService:
    """Fetch repository and user insights from the GitHub REST API."""

    API_BASE = "https://api.github.com"

    def __init__(self) -> None:
        self.session = requests.Session()
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-codebase-explainer",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"
        self.session.headers.update(headers)

    def get_repository_insights(self, repo_url: str, contribution_username: Optional[str] = None) -> Dict[str, Any]:
        owner, repo = self._parse_repo_url(repo_url)
        return self.get_repository_insights_by_name(owner, repo, contribution_username)

    def get_repository_insights_by_name(
        self,
        owner: str,
        repo: str,
        contribution_username: Optional[str] = None,
    ) -> Dict[str, Any]:
        repository = self._get_required_json(f"/repos/{owner}/{repo}")
        contributors = self._get_optional_json(f"/repos/{owner}/{repo}/contributors", default=[])
        languages = self._get_optional_json(f"/repos/{owner}/{repo}/languages", default={})
        commit_activity, commit_pending = self._get_stats_json(
            f"/repos/{owner}/{repo}/stats/commit_activity",
            default=[],
        )
        code_frequency, code_pending = self._get_stats_json(
            f"/repos/{owner}/{repo}/stats/code_frequency",
            default=[],
        )

        total_language_bytes = sum(languages.values()) or 0
        language_breakdown = [
            {
                "name": language,
                "bytes": byte_count,
                "percentage": round((byte_count / total_language_bytes) * 100, 1) if total_language_bytes else 0,
            }
            for language, byte_count in sorted(languages.items(), key=lambda item: item[1], reverse=True)
        ]

        contributor_list = [
            {
                "login": contributor.get("login"),
                "avatar_url": contributor.get("avatar_url"),
                "html_url": contributor.get("html_url"),
                "contributions": contributor.get("contributions", 0),
            }
            for contributor in contributors[:10]
        ]

        contribution_summary = None
        if contribution_username and repository.get("owner", {}).get("login", "").lower() == contribution_username.lower():
            contribution_summary = self._get_user_contribution_summary(
                owner,
                repo,
                contribution_username,
                contributors,
            )

        return {
            "owner": owner,
            "repo": repo,
            "repository": {
                "name": repository.get("name"),
                "full_name": repository.get("full_name"),
                "description": repository.get("description"),
                "html_url": repository.get("html_url"),
                "updated_at": repository.get("updated_at"),
                "created_at": repository.get("created_at"),
            },
            "stats": {
                "stars": repository.get("stargazers_count", 0),
                "forks": repository.get("forks_count", 0),
                "watchers": repository.get("subscribers_count", repository.get("watchers_count", 0)),
                "open_issues": repository.get("open_issues_count", 0),
            },
            "contributors": contributor_list,
            "languages": language_breakdown,
            "commit_activity": {
                "pending": commit_pending,
                "weeks": commit_activity,
            },
            "code_frequency": {
                "pending": code_pending,
                "weeks": code_frequency,
            },
            "contribution_summary": contribution_summary,
        }

    def get_user_overview(self, username: str) -> Dict[str, Any]:
        if not username.strip():
            raise GitHubInsightsError("GitHub username cannot be empty.")

        profile = self._get_required_json(f"/users/{username}")
        repositories = self.list_user_repositories(username)
        language_totals = self._aggregate_user_languages(repositories)
        total_language_bytes = sum(language_totals.values()) or 0
        languages = [
            {
                "name": language,
                "bytes": byte_count,
                "percentage": round((byte_count / total_language_bytes) * 100, 1) if total_language_bytes else 0,
            }
            for language, byte_count in sorted(language_totals.items(), key=lambda item: item[1], reverse=True)
        ]
        most_starred_repo = max(repositories, key=lambda item: item.get("stargazers_count", 0), default=None)
        most_used_language = languages[0]["name"] if languages else None

        return {
            "profile": {
                "login": profile.get("login"),
                "name": profile.get("name"),
                "avatar_url": profile.get("avatar_url"),
                "html_url": profile.get("html_url"),
                "bio": profile.get("bio"),
                "followers": profile.get("followers", 0),
                "following": profile.get("following", 0),
                "public_repos": profile.get("public_repos", 0),
                "created_at": profile.get("created_at"),
            },
            "summary": {
                "total_repositories": len(repositories),
                "most_used_language": most_used_language,
                "most_starred_repository": {
                    "name": most_starred_repo.get("name"),
                    "stars": most_starred_repo.get("stargazers_count", 0),
                } if most_starred_repo else None,
            },
            "languages": languages,
        }

    def list_user_repositories(self, username: str) -> List[Dict[str, Any]]:
        if not username.strip():
            raise GitHubInsightsError("GitHub username cannot be empty.")

        repositories = self._get_required_json(f"/users/{username}/repos?sort=updated&per_page=30")
        if not isinstance(repositories, list):
            raise GitHubInsightsError("Unexpected GitHub response while fetching repositories.")

        return [
            {
                "name": repository.get("name"),
                "full_name": repository.get("full_name"),
                "html_url": repository.get("html_url"),
                "description": repository.get("description"),
                "stargazers_count": repository.get("stargazers_count", 0),
                "language": repository.get("language"),
                "updated_at": repository.get("updated_at"),
                "owner": repository.get("owner", {}).get("login"),
            }
            for repository in repositories
        ]

    def _aggregate_user_languages(self, repositories: List[Dict[str, Any]]) -> Dict[str, int]:
        totals: Dict[str, int] = defaultdict(int)
        for repository in repositories:
            owner = repository.get("owner")
            name = repository.get("name")
            if not owner or not name:
                continue
            language_payload = self._get_optional_json(f"/repos/{owner}/{name}/languages", default={})
            if isinstance(language_payload, dict):
                for language, byte_count in language_payload.items():
                    totals[language] += int(byte_count)
        return dict(totals)

    def _get_user_contribution_summary(
        self,
        owner: str,
        repo: str,
        username: str,
        contributors: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        matching_contributor = next(
            (contributor for contributor in contributors if contributor.get("login", "").lower() == username.lower()),
            None,
        )
        if not matching_contributor:
            return None

        total_contributions = sum(contributor.get("contributions", 0) for contributor in contributors) or 1
        commits = self._get_optional_json(f"/repos/{owner}/{repo}/commits?author={username}&per_page=100", default=[])
        dates = []
        if isinstance(commits, list):
            for commit in commits:
                commit_date = commit.get("commit", {}).get("author", {}).get("date")
                if commit_date:
                    dates.append(commit_date)

        return {
            "login": username,
            "commits": matching_contributor.get("contributions", 0),
            "percentage": round((matching_contributor.get("contributions", 0) / total_contributions) * 100, 1),
            "active_period": {
                "start": min(dates) if dates else None,
                "end": max(dates) if dates else None,
            },
        }

    def _parse_repo_url(self, repo_url: str) -> Tuple[str, str]:
        parsed = urlparse(repo_url)
        if parsed.netloc != "github.com":
            raise GitHubInsightsError("Only GitHub repositories are supported for insights.")

        parts = [part for part in parsed.path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise GitHubInsightsError("Could not determine owner and repository from the GitHub URL.")

        return parts[0], parts[1].removesuffix(".git")

    def _get_required_json(self, path: str) -> Any:
        status_code, payload = self._request_json(path)
        if status_code >= 400:
            message = payload.get("message") if isinstance(payload, dict) else "GitHub API request failed"
            raise GitHubInsightsError(message)
        return payload

    def _get_optional_json(self, path: str, default: Any) -> Any:
        status_code, payload = self._request_json(path)
        if status_code >= 400:
            logger.warning("GitHub insights request failed for %s: %s", path, payload)
            return default
        return payload

    def _get_stats_json(self, path: str, default: Any) -> Tuple[Any, bool]:
        status_code, payload = self._request_json(path)
        if status_code == 202:
            return default, True
        if status_code >= 400:
            logger.warning("GitHub stats request failed for %s: %s", path, payload)
            return default, False
        return payload, False

    def _request_json(self, path: str) -> Tuple[int, Any]:
        try:
            response = self.session.get(f"{self.API_BASE}{path}", timeout=20)
            if response.status_code == 204:
                return response.status_code, {}
            return response.status_code, response.json()
        except requests.RequestException as exc:
            raise GitHubInsightsError(f"GitHub API request failed: {exc}") from exc
