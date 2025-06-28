"""Tests for report generator module."""

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from src.reporters.report_generator import ReportGenerator, SummaryReporter


class TestReportGenerator:
    """Test report generation functionality."""

    @pytest.fixture
    def sample_analysis_results(self):
        """Create sample analysis results for testing."""
        return {
            "complexity": {
                "summary": {
                    "total_files": 5,
                    "average_complexity": 8.5,
                    "total_loc": 500,
                    "total_lloc": 350,
                    "complexity_distribution": {
                        "A (1-5)": 10,
                        "B (6-10)": 5,
                        "C (11-20)": 2,
                        "D (21-30)": 1,
                        "E (31-40)": 0,
                        "F (41+)": 0,
                    },
                },
                "files": {
                    "main.py": {
                        "total_complexity": 15,
                        "loc": 100,
                        "functions": [{"name": "complex_func", "complexity": 12, "lineno": 10}],
                    }
                },
            },
            "verification": {
                "security": {
                    "bandit": {
                        "status": "completed",
                        "results": [
                            {
                                "filename": "test.py",
                                "line_number": 5,
                                "issue_severity": "HIGH",
                                "issue_confidence": "HIGH",
                                "issue_text": "Hardcoded password",
                                "test_id": "B105",
                            }
                        ],
                        "metrics": {"SEVERITY.HIGH": 1},
                    },
                    "secrets": {
                        "found": 2,
                        "details": [
                            {"file": "config.py", "type": "api_key"},
                            {"file": ".env", "type": "password"},
                        ],
                    },
                },
                "type_checking": {"mypy": {"status": "completed", "total_issues": 3}},
            },
            "tests": {
                "summary": {
                    "total_tests": 20,
                    "passed": 18,
                    "failed": 2,
                    "skipped": 0,
                    "success_rate": 90.0,
                    "frameworks_used": ["python_pytest", "javascript_jest"],
                },
                "coverage": {"python": ["coverage.xml", ".coverage"]},
            },
        }

    def test_generate_all_formats(self, sample_analysis_results, temp_dir):
        """Test generation of all report formats."""
        generator = ReportGenerator(str(temp_dir))

        results = generator.generate_report(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
            "/test/repo",
            "all",
        )

        # Should generate all formats
        assert "markdown" in results
        assert "html" in results
        assert "json" in results
        assert "pdf" in results
        assert "verification_steps" in results

        # Check files exist
        for _format_type, path in results.items():
            assert Path(path).exists()

    def test_calculate_health_score(self, sample_analysis_results):
        """Test health score calculation."""
        generator = ReportGenerator()

        score = generator._calculate_health_score(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
        )

        # Score should be between 0 and 100
        assert 0 <= score <= 100

        # With 90% test success rate and some issues, score should be reasonable
        assert 50 <= score <= 90

    def test_identify_critical_issues(self, sample_analysis_results):
        """Test identification of critical issues."""
        generator = ReportGenerator()

        issues = generator._identify_critical_issues(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
        )

        # Should identify various issue types
        issue_types = [issue["type"] for issue in issues]

        assert "security_vulnerability" in issue_types
        assert "hardcoded_secret" in issue_types
        assert "test_failures" in issue_types
        assert "type_errors" in issue_types

        # Check severity levels
        assert any(issue["severity"] == "critical" for issue in issues)
        assert any(issue["severity"] == "high" for issue in issues)

    def test_generate_recommendations(self, sample_analysis_results):
        """Test recommendation generation."""
        generator = ReportGenerator()

        recommendations = generator._generate_recommendations(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
        )

        # Should generate various recommendations
        assert len(recommendations) > 0

        categories = [rec["category"] for rec in recommendations]
        priorities = [rec["priority"] for rec in recommendations]

        # Should have different categories
        assert "Security" in categories

        # Should have different priorities
        assert "high" in priorities

    def test_markdown_report_generation(self, sample_analysis_results, temp_dir):
        """Test Markdown report generation."""
        generator = ReportGenerator(str(temp_dir))

        report_data = generator._prepare_report_data(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
            "/test/repo",
        )

        md_file = generator._generate_markdown_report(report_data)

        # Check file exists and contains expected content
        assert md_file.exists()
        content = md_file.read_text()

        assert "# Code Analysis Report" in content
        assert "Health Score" in content
        assert "Critical Issues" in content
        assert "Recommendations" in content
        assert "90.0%" in content  # Success rate

    def test_html_report_generation(self, sample_analysis_results, temp_dir):
        """Test HTML report generation."""
        generator = ReportGenerator(str(temp_dir))

        report_data = generator._prepare_report_data(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
            "/test/repo",
        )

        html_file = generator._generate_html_report(report_data)

        # Check file exists and contains HTML
        assert html_file.exists()
        content = html_file.read_text()

        assert "<!DOCTYPE html>" in content
        assert "<html>" in content
        assert "Health Score" in content
        assert 'class="critical"' in content

    def test_json_report_generation(self, sample_analysis_results, temp_dir):
        """Test JSON report generation."""
        generator = ReportGenerator(str(temp_dir))

        report_data = generator._prepare_report_data(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
            "/test/repo",
        )

        json_file = generator._generate_json_report(report_data)

        # Check file exists and is valid JSON
        assert json_file.exists()

        with open(json_file, "r") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "summary" in data
        assert "critical_issues" in data
        assert data["summary"]["health_score"] > 0

    def test_verification_steps_generation(self, sample_analysis_results, temp_dir):
        """Test verification steps document generation."""
        generator = ReportGenerator(str(temp_dir))

        report_data = generator._prepare_report_data(
            sample_analysis_results["complexity"],
            sample_analysis_results["verification"],
            sample_analysis_results["tests"],
            "/test/repo",
        )

        steps_file = generator._generate_verification_steps(report_data)

        # Check file exists and contains verification instructions
        assert steps_file.exists()
        content = steps_file.read_text()

        assert "# Verification Steps" in content
        assert "How to Verify Our Findings" in content
        assert "```bash" in content  # Should have code examples

    def test_empty_results_handling(self, temp_dir):
        """Test handling of empty or minimal results."""
        generator = ReportGenerator(str(temp_dir))

        empty_results: Dict[str, Any] = {"summary": {}, "files": {}}

        # Should handle empty results gracefully
        report_data = generator._prepare_report_data(empty_results, {}, {}, "/test/repo")

        assert report_data["summary"]["health_score"] >= 0
        assert report_data["summary"]["critical_issues_count"] == 0

    def test_get_languages_detection(self):
        """Test language detection from file extensions."""
        generator = ReportGenerator()

        complexity_results: Dict[str, Any] = {
            "files": {
                "main.py": {},
                "app.js": {},
                "server.ts": {},
                "Main.java": {},
                "program.go": {},
            }
        }

        languages = generator._get_languages(complexity_results)

        assert "Python" in languages
        assert "JavaScript" in languages
        assert "TypeScript" in languages
        assert "Java" in languages
        assert "Go" in languages


class TestSummaryReporter:
    """Test console summary reporter."""

    def test_generate_console_summary(self):
        """Test console summary generation."""
        complexity = {
            "summary": {
                "total_files": 10,
                "total_loc": 1000,
                "average_complexity": 7.5,
                "complexity_distribution": {"A (1-5)": 20, "B (6-10)": 10, "C (11-20)": 5},
            }
        }

        verification = {
            "security": {"bandit": {"results": [1, 2, 3]}, "secrets": {"found": 1}},  # 3 issues
            "type_checking": {"mypy": {"total_issues": 5}},
        }

        tests = {"summary": {"total_tests": 50, "passed": 45, "failed": 5, "success_rate": 90.0}}

        summary = SummaryReporter.generate_console_summary(complexity, verification, tests)

        # Check summary contains expected sections
        assert "COMPLEXITY ANALYSIS" in summary
        assert "TEST ANALYSIS" in summary
        assert "SECURITY ANALYSIS" in summary
        assert "TYPE CHECKING" in summary

        # Check specific values
        assert "10" in summary  # files
        assert "1000" in summary  # lines
        assert "7.5" in summary  # complexity
        assert "50" in summary  # total tests
        assert "45" in summary  # passed tests
        assert "90.0%" in summary  # success rate

    def test_console_summary_no_tests(self):
        """Test console summary when no tests are found."""
        summary = SummaryReporter.generate_console_summary(
            {"summary": {}}, {}, {"summary": {"total_tests": 0}}
        )

        assert "No tests found!" in summary
