"""Git history analyzer for extracting insights about code evolution and documentation."""

import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class GitHistoryAnalyzer:
    """Analyzes git history to verify documentation claims and track code evolution."""

    def __init__(self, repo_path: str):
        """Initialize the GitHistoryAnalyzer.

        Args:
            repo_path: Path to the git repository to analyze.
        """
        self.repo_path = Path(repo_path)
        self.is_git_repo = self._check_git_repo()

    def _check_git_repo(self) -> bool:
        """Check if the directory is a git repository."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            return False

    def analyze(self) -> Dict[str, Any]:
        """Run comprehensive git history analysis."""
        if not self.is_git_repo:
            return {
                "error": "Not a git repository",
                "is_git_repo": False,
                "analysis_skipped": True,
            }

        results = {
            "is_git_repo": True,
            "repository_info": self._get_repository_info(),
            "commit_history": self._analyze_commit_history(),
            "file_history": self._analyze_file_history(),
            "documentation_sync": self._analyze_documentation_sync(),
            "contributor_analysis": self._analyze_contributors(),
            "stability_analysis": self._analyze_code_stability(),
            "feature_timeline": self._analyze_feature_timeline(),
            "version_analysis": self._analyze_versions(),
        }

        # Add insights and recommendations
        results["insights"] = self._generate_insights(results)
        results["verification_issues"] = self._identify_verification_issues(results)

        return results

    def _get_repository_info(self) -> Dict[str, Any]:
        """Get basic repository information."""
        info = {
            "current_branch": self._run_git_command(["git", "branch", "--show-current"]),
            "remote_url": self._run_git_command(["git", "remote", "get-url", "origin"]),
            "last_commit": self._run_git_command(["git", "rev-parse", "HEAD"]),
            "repo_age_days": 0,
            "total_commits": 0,
        }

        # Get first and last commit dates
        first_commit = self._run_git_command(["git", "log", "--reverse", "--format=%at", "-1"])
        last_commit = self._run_git_command(["git", "log", "--format=%at", "-1"])

        if first_commit and last_commit:
            first_date = datetime.fromtimestamp(int(first_commit), tz=timezone.utc)
            last_date = datetime.fromtimestamp(int(last_commit), tz=timezone.utc)
            info["repo_age_days"] = (last_date - first_date).days
            info["first_commit_date"] = first_date.isoformat()
            info["last_commit_date"] = last_date.isoformat()

        # Get total number of commits
        commit_count = self._run_git_command(["git", "rev-list", "--count", "HEAD"])
        if commit_count:
            info["total_commits"] = int(commit_count)

        return info

    def _analyze_commit_history(self) -> Dict[str, Any]:
        """Analyze commit patterns and frequency."""
        # Get commit data for the last year
        one_year_ago = datetime.now(timezone.utc).timestamp() - (365 * 24 * 60 * 60)

        commit_log = self._run_git_command(
            [
                "git",
                "log",
                "--since",
                str(int(one_year_ago)),
                "--format=%H|%at|%an|%ae|%s",
                "--no-merges",
            ]
        )

        if not commit_log:
            return {}

        commits_by_month: Dict[str, int] = defaultdict(int)
        commits_by_author: Dict[str, int] = defaultdict(int)
        commit_messages = []

        for line in commit_log.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 4)
            if len(parts) < 5:
                continue

            commit_hash, timestamp, author_name, author_email, message = parts

            # Group by month
            date = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            month_key = date.strftime("%Y-%m")
            commits_by_month[month_key] += 1

            # Group by author
            commits_by_author[author_name] += 1

            # Collect commit messages for pattern analysis
            commit_messages.append(message.lower())

        # Analyze commit message patterns
        commit_patterns = self._analyze_commit_patterns(commit_messages)

        return {
            "commits_by_month": dict(commits_by_month),
            "commits_by_author": dict(commits_by_author),
            "commit_patterns": commit_patterns,
            "average_commits_per_month": (
                sum(commits_by_month.values()) / len(commits_by_month) if commits_by_month else 0
            ),
        }

    def _analyze_commit_patterns(self, messages: List[str]) -> Dict[str, int]:
        """Analyze patterns in commit messages."""
        patterns = {
            "features": 0,
            "fixes": 0,
            "documentation": 0,
            "refactoring": 0,
            "tests": 0,
            "breaking_changes": 0,
        }

        feature_keywords = r"\b(feat|feature|add|implement|new)\b"
        fix_keywords = r"\b(fix|bug|patch|resolve|solved)\b"
        doc_keywords = r"\b(doc|docs|documentation|readme)\b"
        refactor_keywords = r"\b(refactor|restructure|reorganize|cleanup)\b"
        test_keywords = r"\b(test|tests|testing|spec)\b"
        breaking_keywords = r"(\b(breaking|break|incompatible|major)\b|!:)"

        for msg in messages:
            if re.search(feature_keywords, msg):
                patterns["features"] += 1
            if re.search(fix_keywords, msg):
                patterns["fixes"] += 1
            if re.search(doc_keywords, msg):
                patterns["documentation"] += 1
            if re.search(refactor_keywords, msg):
                patterns["refactoring"] += 1
            if re.search(test_keywords, msg):
                patterns["tests"] += 1
            if re.search(breaking_keywords, msg):
                patterns["breaking_changes"] += 1

        return patterns

    def _analyze_file_history(self) -> Dict[str, Any]:
        """Analyze file modification patterns."""
        # Get file change frequency
        file_changes = self._run_git_command(
            ["git", "log", "--format=", "--name-only", "--since", "1 year ago"]
        )

        if not file_changes:
            return {}

        file_change_count: Dict[str, int] = defaultdict(int)
        for filename in file_changes.strip().split("\n"):
            if filename:
                file_change_count[filename] += 1

        # Sort by most changed
        most_changed = sorted(file_change_count.items(), key=lambda x: x[1], reverse=True)[:20]

        # Get recently added files
        recent_files = self._run_git_command(
            [
                "git",
                "log",
                "--diff-filter=A",
                "--format=%at|%n",
                "--name-only",
                "--since",
                "3 months ago",
            ]
        )

        recently_added = []
        if recent_files:
            lines = recent_files.strip().split("\n")
            i = 0
            while i < len(lines):
                if "|" in lines[i]:
                    timestamp = lines[i].split("|")[0]
                    i += 1
                    while i < len(lines) and lines[i] and "|" not in lines[i]:
                        recently_added.append(
                            {
                                "file": lines[i],
                                "added_at": datetime.fromtimestamp(
                                    int(timestamp), tz=timezone.utc
                                ).isoformat(),
                            }
                        )
                        i += 1
                else:
                    i += 1

        return {
            "most_changed_files": [{"file": f, "changes": c} for f, c in most_changed],
            "recently_added_files": recently_added[:10],
            "total_files_changed": len(file_change_count),
        }

    def _analyze_documentation_sync(self) -> Dict[str, Any]:
        """Analyze how well documentation is synchronized with code changes."""
        # Find documentation files
        doc_patterns = ["*.md", "*.rst", "*.txt", "docs/*", "README*", "CHANGELOG*"]
        doc_files: List[str] = []

        for pattern in doc_patterns:
            doc_files.extend(
                str(f.relative_to(self.repo_path))
                for f in self.repo_path.rglob(pattern)
                if f.is_file()
            )

        # Get last modification dates for docs
        doc_updates = {}
        for doc_file in doc_files:
            last_update = self._run_git_command(
                ["git", "log", "-1", "--format=%at", "--", doc_file]
            )
            if last_update:
                doc_updates[doc_file] = datetime.fromtimestamp(int(last_update), tz=timezone.utc)

        # Find code files that changed after their related docs
        outdated_docs = []

        # Get all code changes in the last 6 months
        code_changes = self._run_git_command(
            [
                "git",
                "log",
                "--since",
                "6 months ago",
                "--format=%at",
                "--name-only",
                "--",
                "*.py",
                "*.js",
                "*.java",
                "*.go",
                "*.rs",
                "*.cpp",
                "*.c",
            ]
        )

        if code_changes and doc_updates:
            # Simple heuristic: README should be updated if significant code changes
            readme_files = [f for f in doc_updates.keys() if "readme" in f.lower()]
            if readme_files and code_changes.count("\n") > 10:
                readme_date = max(doc_updates[f] for f in readme_files)
                days_behind = (datetime.now(timezone.utc) - readme_date).days
                if days_behind > 30:
                    outdated_docs.append(
                        {
                            "file": readme_files[0],
                            "days_since_update": days_behind,
                            "recommendation": "README may be outdated given recent code changes",
                        }
                    )

        return {
            "documentation_files": len(doc_files),
            "last_doc_updates": {
                k: v.isoformat()
                for k, v in sorted(doc_updates.items(), key=lambda x: x[1], reverse=True)[:10]
            },
            "potentially_outdated_docs": outdated_docs,
        }

    def _analyze_contributors(self) -> Dict[str, Any]:
        """Analyze contributor patterns and expertise."""
        # Get contributor statistics
        contributors = self._run_git_command(
            ["git", "shortlog", "-sn", "--no-merges", "--since", "1 year ago"]
        )

        if not contributors:
            return {}

        contributor_stats: List[Dict[str, Any]] = []
        for line in contributors.strip().split("\n"):
            if line:
                parts = line.strip().split("\t", 1)
                if len(parts) == 2:
                    commits, name = parts
                    contributor_stats.append(
                        {
                            "name": name,
                            "commits": int(commits),
                        }
                    )

        # Get file ownership (who edited what most)
        file_ownership = self._analyze_file_ownership()

        # Calculate bus factor (how many contributors have > 10% of commits)
        total_commits = sum(c["commits"] for c in contributor_stats)
        bus_factor = (
            len([c for c in contributor_stats if c["commits"] / total_commits > 0.1])
            if total_commits > 0
            else 0
        )

        return {
            "contributors": contributor_stats[:20],
            "total_contributors": len(contributor_stats),
            "bus_factor": bus_factor,
            "file_ownership": file_ownership,
        }

    def _analyze_file_ownership(self) -> List[Dict[str, Any]]:
        """Determine primary maintainers for key files."""
        # Focus on important files
        important_patterns = [
            "README*",
            "setup.py",
            "pyproject.toml",
            "package.json",
            "Makefile",
            "CMakeLists.txt",
            "*.config.*",
            "src/main.*",
        ]

        ownership = []
        for pattern in important_patterns:
            for file_path in self.repo_path.rglob(pattern):
                if file_path.is_file():
                    rel_path = str(file_path.relative_to(self.repo_path))

                    # Get contributors for this file
                    contributors = self._run_git_command(["git", "shortlog", "-sn", "--", rel_path])

                    if contributors:
                        top_contributor = contributors.strip().split("\n")[0]
                        if "\t" in top_contributor:
                            commits, name = top_contributor.split("\t", 1)
                            ownership.append(
                                {
                                    "file": rel_path,
                                    "primary_maintainer": name,
                                    "commits": int(commits),
                                }
                            )

        return ownership[:10]

    def _analyze_code_stability(self) -> Dict[str, Any]:
        """Analyze code stability metrics."""
        # Files with high churn (changed frequently)
        churn_data = self._run_git_command(
            ["git", "log", "--format=", "--name-only", "--since", "6 months ago"]
        )

        if not churn_data:
            return {}

        file_churn: Dict[str, int] = defaultdict(int)
        for filename in churn_data.strip().split("\n"):
            if filename and not filename.startswith("."):
                file_churn[filename] += 1

        high_churn_files = [
            {"file": f, "changes": c}
            for f, c in sorted(file_churn.items(), key=lambda x: x[1], reverse=True)
            if c > 5
        ][:10]

        # Find potentially abandoned code (no changes in long time)
        all_files = self._run_git_command(["git", "ls-files"])
        abandoned_files: List[Dict[str, Any]] = []

        if all_files:
            for filename in all_files.strip().split("\n")[:100]:  # Check first 100 files
                if filename and filename.endswith((".py", ".js", ".java", ".go")):
                    last_change = self._run_git_command(
                        ["git", "log", "-1", "--format=%at", "--", filename]
                    )
                    if last_change:
                        days_old = (datetime.now(timezone.utc).timestamp() - int(last_change)) / (
                            24 * 60 * 60
                        )
                        if days_old > 365:  # Not touched in a year
                            abandoned_files.append(
                                {
                                    "file": filename,
                                    "days_since_change": int(days_old),
                                }
                            )

        return {
            "high_churn_files": high_churn_files,
            "potentially_abandoned_files": sorted(
                abandoned_files, key=lambda x: x["days_since_change"], reverse=True
            )[:10],
        }

    def _analyze_feature_timeline(self) -> Dict[str, Any]:
        """Analyze when features were added based on commit messages."""
        # Look for feature commits
        feature_commits = self._run_git_command(
            [
                "git",
                "log",
                "--grep",
                "feat\\|feature\\|add\\|implement",
                "-i",
                "--format=%at|%s",
                "--since",
                "1 year ago",
            ]
        )

        if not feature_commits:
            return {}

        features = []
        for line in feature_commits.strip().split("\n")[:50]:  # Last 50 features
            if "|" in line:
                timestamp, message = line.split("|", 1)
                features.append(
                    {
                        "date": datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat(),
                        "feature": message,
                    }
                )

        return {
            "recent_features": features[:20],
            "features_per_month": self._count_features_per_month(features),
        }

    def _count_features_per_month(self, features: List[Dict[str, str]]) -> Dict[str, int]:
        """Count features added per month."""
        features_by_month: Dict[str, int] = defaultdict(int)

        for feature in features:
            date = datetime.fromisoformat(feature["date"].replace("Z", "+00:00"))
            month_key = date.strftime("%Y-%m")
            features_by_month[month_key] += 1

        return dict(features_by_month)

    def _analyze_versions(self) -> Dict[str, Any]:
        """Analyze version tags and releases."""
        # Get all tags
        tags = self._run_git_command(["git", "tag", "-l", "--sort=-version:refname"])

        if not tags:
            return {"has_versions": False}

        tag_list = tags.strip().split("\n")
        version_info: Dict[str, Any] = {
            "has_versions": True,
            "total_versions": len(tag_list),
            "latest_version": tag_list[0] if tag_list else None,
            "versions": [],
        }

        # Get details for recent versions
        for tag in tag_list[:10]:  # Last 10 versions
            if tag:
                tag_info = self._run_git_command(["git", "log", "-1", "--format=%at|%s", tag])
                if tag_info and "|" in tag_info:
                    timestamp, message = tag_info.split("|", 1)
                    versions_list = version_info.get("versions", [])
                    if isinstance(versions_list, list):
                        versions_list.append(
                            {
                                "version": tag,
                                "date": datetime.fromtimestamp(
                                    int(timestamp), tz=timezone.utc
                                ).isoformat(),
                                "message": message,
                            }
                        )

        # Check semantic versioning compliance
        version_info["follows_semver"] = self._check_semver_compliance(tag_list)

        return version_info

    def _check_semver_compliance(self, tags: List[str]) -> bool:
        """Check if tags follow semantic versioning."""
        if not tags:
            return False

        semver_pattern = r"^v?\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
        compliant_count = sum(1 for tag in tags if re.match(semver_pattern, tag))

        return compliant_count / len(tags) > 0.8  # 80% compliance

    def _generate_insights(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate insights from the analysis results."""
        insights = []

        # Repository age and activity
        repo_info = results.get("repository_info", {})
        if repo_info.get("repo_age_days", 0) < 90:
            insights.append(
                {
                    "type": "warning",
                    "category": "maturity",
                    "message": (
                        "This is a young repository (< 90 days old). " "Features may be unstable."
                    ),
                }
            )

        # Commit patterns
        commit_history = results.get("commit_history", {})
        if commit_history:
            patterns = commit_history.get("commit_patterns", {})
            if patterns.get("fixes", 0) > patterns.get("features", 0) * 2:
                insights.append(
                    {
                        "type": "warning",
                        "category": "quality",
                        "message": (
                            "High ratio of bug fixes to features may " "indicate quality issues."
                        ),
                    }
                )

            if patterns.get("breaking_changes", 0) > 5:
                insights.append(
                    {
                        "type": "warning",
                        "category": "stability",
                        "message": "Multiple breaking changes detected. API may be unstable.",
                    }
                )

        # Documentation sync
        doc_sync = results.get("documentation_sync", {})
        if doc_sync.get("potentially_outdated_docs"):
            insights.append(
                {
                    "type": "warning",
                    "category": "documentation",
                    "message": (
                        "Some documentation appears outdated compared " "to recent code changes."
                    ),
                }
            )

        # Bus factor
        contributors = results.get("contributor_analysis", {})
        if contributors.get("bus_factor", 0) < 3:
            insights.append(
                {
                    "type": "info",
                    "category": "sustainability",
                    "message": (
                        f"Low bus factor ({contributors.get('bus_factor', 0)}). "
                        "Project depends heavily on few contributors."
                    ),
                }
            )

        # Code stability
        stability = results.get("stability_analysis", {})
        if len(stability.get("high_churn_files", [])) > 5:
            insights.append(
                {
                    "type": "warning",
                    "category": "stability",
                    "message": (
                        "Several files have high change frequency, "
                        "indicating potential instability."
                    ),
                }
            )

        return insights

    def _identify_verification_issues(self, results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify specific verification issues from git history."""
        issues = []

        # Check for features without tests
        commit_patterns = results.get("commit_history", {}).get("commit_patterns", {})
        if commit_patterns:
            feature_to_test_ratio = commit_patterns.get("features", 0) / commit_patterns.get(
                "tests", 1
            )
            if feature_to_test_ratio > 3:
                issues.append(
                    {
                        "severity": "medium",
                        "type": "missing_tests",
                        "description": "Many features added without corresponding tests",
                        "evidence": f"Feature commits: {commit_patterns.get('features', 0)}, "
                        f"Test commits: {commit_patterns.get('tests', 0)}",
                    }
                )

        # Check for undocumented features
        doc_sync = results.get("documentation_sync", {})
        feature_timeline = results.get("feature_timeline", {})

        if (
            feature_timeline.get("recent_features")
            and len(doc_sync.get("potentially_outdated_docs", [])) > 0
        ):
            issues.append(
                {
                    "severity": "medium",
                    "type": "outdated_documentation",
                    "description": "Recent features may not be properly documented",
                    "evidence": "Documentation hasn't been updated recently despite new features",
                }
            )

        # Check version consistency
        version_info = results.get("version_analysis", {})
        if version_info.get("has_versions") and not version_info.get("follows_semver"):
            issues.append(
                {
                    "severity": "low",
                    "type": "versioning_inconsistency",
                    "description": "Version tags don't follow semantic versioning",
                    "evidence": "Inconsistent version tag format detected",
                }
            )

        return issues

    def _run_git_command(self, cmd: List[str]) -> Optional[str]:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            return None
