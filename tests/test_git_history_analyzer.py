"""Tests for Git history analyzer."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.analyzers.git_history import GitHistoryAnalyzer


class TestGitHistoryAnalyzer:
    """Test GitHistoryAnalyzer functionality."""

    def test_init_non_git_repo(self, temp_dir):
        """Test initialization with non-git directory."""
        analyzer = GitHistoryAnalyzer(str(temp_dir))
        assert analyzer.repo_path == Path(temp_dir)
        assert not analyzer.is_git_repo

    @patch("subprocess.run")
    def test_init_git_repo(self, mock_run, temp_dir):
        """Test initialization with git repository."""
        mock_run.return_value = MagicMock(returncode=0)
        analyzer = GitHistoryAnalyzer(str(temp_dir))
        assert analyzer.is_git_repo

    def test_analyze_non_git_repo(self, temp_dir):
        """Test analysis on non-git repository."""
        analyzer = GitHistoryAnalyzer(str(temp_dir))
        results = analyzer.analyze()

        assert results["is_git_repo"] is False
        assert results["analysis_skipped"] is True
        assert "error" in results

    @patch.object(GitHistoryAnalyzer, "_check_git_repo")
    @patch.object(GitHistoryAnalyzer, "_run_git_command")
    def test_analyze_git_repo(self, mock_git_cmd, mock_check_repo, temp_dir):
        """Test full analysis on git repository."""
        mock_check_repo.return_value = True

        # Mock various git commands
        def git_command_side_effect(cmd):
            if "branch --show-current" in cmd:
                return "main"
            elif "remote get-url" in cmd:
                return "https://github.com/test/repo.git"
            elif "rev-parse HEAD" in cmd:
                return "abc123def456"
            elif "rev-list --count" in cmd:
                return "100"
            elif cmd == ["git", "log", "--reverse", "--format=%at", "-1"]:
                return str(int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp()))
            elif cmd == ["git", "log", "--format=%at", "-1"]:
                return str(int(datetime(2024, 1, 1, tzinfo=timezone.utc).timestamp()))
            elif "shortlog" in cmd:
                return "50\tJohn Doe\n30\tJane Smith\n20\tBob Johnson"
            elif "tag -l" in cmd:
                return "v1.2.3\nv1.2.2\nv1.2.1\nv1.2.0"
            return ""

        mock_git_cmd.side_effect = git_command_side_effect

        analyzer = GitHistoryAnalyzer(str(temp_dir))
        results = analyzer.analyze()

        assert results["is_git_repo"] is True
        assert "repository_info" in results
        assert "commit_history" in results
        assert "insights" in results
        assert "verification_issues" in results

    @patch.object(GitHistoryAnalyzer, "_run_git_command")
    def test_repository_info(self, mock_git_cmd, temp_dir):
        """Test repository information extraction."""
        mock_git_cmd.side_effect = [
            "main",  # current branch
            "https://github.com/test/repo.git",  # remote URL
            "abc123",  # HEAD commit
            "1609459200",  # first commit timestamp
            "1672531200",  # last commit timestamp
            "500",  # total commits
        ]

        analyzer = GitHistoryAnalyzer(str(temp_dir))
        analyzer.is_git_repo = True
        info = analyzer._get_repository_info()

        assert info["current_branch"] == "main"
        assert info["remote_url"] == "https://github.com/test/repo.git"
        assert info["total_commits"] == 500
        assert info["repo_age_days"] == 730  # 2 years

    def test_analyze_commit_patterns(self, temp_dir):
        """Test commit message pattern analysis."""
        analyzer = GitHistoryAnalyzer(str(temp_dir))

        messages = [
            "feat: add new feature",
            "fix: resolve bug in parser",
            "docs: update README",
            "refactor: restructure modules",
            "test: add unit tests",
            "feat!: breaking change in API",
        ]

        patterns = analyzer._analyze_commit_patterns(messages)

        assert (
            patterns["features"] == 3
        )  # "feat:", "feat!", and "test: add" all match feature keywords
        assert patterns["fixes"] == 1
        assert patterns["documentation"] == 1
        assert patterns["refactoring"] == 1
        assert patterns["tests"] == 1
        assert patterns["breaking_changes"] == 1

    @patch.object(GitHistoryAnalyzer, "_run_git_command")
    def test_analyze_contributors(self, mock_git_cmd, temp_dir):
        """Test contributor analysis."""
        mock_git_cmd.side_effect = [
            "100\tAlice Developer\n50\tBob Coder\n25\tCharlie Contributor",  # shortlog
            "Alice Developer\t100\tcore/main.py",  # file ownership for critical files
        ]

        analyzer = GitHistoryAnalyzer(str(temp_dir))
        analyzer.is_git_repo = True
        contributors = analyzer._analyze_contributors()

        assert contributors["total_contributors"] == 3
        assert contributors["bus_factor"] == 3  # All three have > 10% (100/175, 50/175, 25/175)
        assert contributors["contributors"][0]["name"] == "Alice Developer"
        assert contributors["contributors"][0]["commits"] == 100

    def test_check_semver_compliance(self, temp_dir):
        """Test semantic versioning compliance check."""
        analyzer = GitHistoryAnalyzer(str(temp_dir))

        # Good semver tags
        good_tags = ["v1.0.0", "v1.1.0", "v1.1.1", "v2.0.0-alpha", "v2.0.0"]
        assert analyzer._check_semver_compliance(good_tags) is True

        # Mixed tags
        mixed_tags = ["v1.0.0", "release-2", "1.1", "v1.2.0", "latest"]
        assert analyzer._check_semver_compliance(mixed_tags) is False

    @patch.object(GitHistoryAnalyzer, "_run_git_command")
    def test_analyze_documentation_sync(self, mock_git_cmd, temp_dir):
        """Test documentation synchronization analysis."""
        # Create some test files
        (temp_dir / "README.md").touch()
        (temp_dir / "docs").mkdir()
        (temp_dir / "docs" / "api.md").touch()

        # Set up a mock that returns the proper values for each call
        readme_timestamp = str(int((datetime.now(timezone.utc).timestamp() - 86400 * 60)))
        api_timestamp = str(int((datetime.now(timezone.utc).timestamp() - 86400 * 90)))

        def side_effect(cmd):
            # Check what git command is being run
            if "--format=%at" in cmd and any(doc in str(cmd) for doc in ["README.md", "api.md"]):
                # This is for getting doc file timestamps
                if "README.md" in str(cmd):
                    return readme_timestamp
                elif "api.md" in str(cmd):
                    return api_timestamp
            elif "--name-only" in cmd:
                # This is for getting code changes
                return "file1.py\nfile2.py\nfile3.py\n" * 5
            return None

        mock_git_cmd.side_effect = side_effect

        analyzer = GitHistoryAnalyzer(str(temp_dir))
        analyzer.is_git_repo = True
        doc_sync = analyzer._analyze_documentation_sync()

        assert doc_sync["documentation_files"] >= 2
        assert len(doc_sync["potentially_outdated_docs"]) > 0

    @patch.object(GitHistoryAnalyzer, "_run_git_command")
    def test_generate_insights(self, mock_git_cmd, temp_dir):
        """Test insight generation."""
        analyzer = GitHistoryAnalyzer(str(temp_dir))

        results = {
            "repository_info": {"repo_age_days": 30},
            "commit_history": {
                "commit_patterns": {
                    "features": 5,
                    "fixes": 20,
                    "breaking_changes": 10,
                }
            },
            "contributor_analysis": {"bus_factor": 1},
            "stability_analysis": {
                "high_churn_files": [{"file": f"file{i}.py", "changes": 10} for i in range(10)]
            },
        }

        insights = analyzer._generate_insights(results)

        # Should have warnings about young repo, quality issues, stability
        assert len(insights) >= 4
        assert any(i["category"] == "maturity" for i in insights)
        assert any(i["category"] == "quality" for i in insights)
        assert any(i["category"] == "stability" for i in insights)

    @patch.object(GitHistoryAnalyzer, "_run_git_command")
    def test_error_handling(self, mock_git_cmd, temp_dir):
        """Test error handling in git commands."""
        # Mock the _run_git_command to always return None (simulating git errors)
        mock_git_cmd.return_value = None

        analyzer = GitHistoryAnalyzer(str(temp_dir))
        analyzer.is_git_repo = True

        info = analyzer._get_repository_info()
        assert info["current_branch"] is None
        assert info["total_commits"] == 0
