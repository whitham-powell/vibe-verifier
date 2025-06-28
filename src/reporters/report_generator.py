"""Comprehensive report generation module."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
from fpdf import FPDF


class ReportGenerator:
    """Generates human-readable reports from analysis results."""

    def __init__(self, results_dir: Optional[str] = None):
        """Initialize the ReportGenerator.

        Args:
            results_dir: Optional directory path for saving reports.
        """
        self.results_dir = Path(results_dir) if results_dir else Path.cwd() / "reports"
        self.results_dir.mkdir(exist_ok=True)

        # Set up Jinja2 environment
        self.jinja_env = jinja2.Environment(loader=jinja2.DictLoader(self._get_templates()))

    def generate_report(
        self,
        complexity_results: Dict[str, Any],
        verification_results: Dict[str, Any],
        test_results: Dict[str, Any],
        repo_path: str,
        output_format: str = "all",
    ) -> Dict[str, str]:
        """Generate comprehensive report in multiple formats."""
        # Prepare report data
        report_data = self._prepare_report_data(
            complexity_results, verification_results, test_results, repo_path
        )

        # Generate reports in different formats
        generated_files = {}

        if output_format in ["all", "markdown"]:
            md_file = self._generate_markdown_report(report_data)
            generated_files["markdown"] = str(md_file)

        if output_format in ["all", "html"]:
            html_file = self._generate_html_report(report_data)
            generated_files["html"] = str(html_file)

        if output_format in ["all", "json"]:
            json_file = self._generate_json_report(report_data)
            generated_files["json"] = str(json_file)

        if output_format in ["all", "pdf"]:
            pdf_file = self._generate_pdf_report(report_data)
            generated_files["pdf"] = str(pdf_file)

        # Generate verification steps
        steps_file = self._generate_verification_steps(report_data)
        generated_files["verification_steps"] = str(steps_file)

        return generated_files

    def _prepare_report_data(
        self,
        complexity: Dict[str, Any],
        verification: Dict[str, Any],
        tests: Dict[str, Any],
        repo_path: str,
    ) -> Dict[str, Any]:
        """Prepare and structure report data."""
        timestamp = datetime.now().isoformat()
        repo_name = Path(repo_path).name

        # Calculate overall health score
        health_score = self._calculate_health_score(complexity, verification, tests)

        # Identify critical issues
        critical_issues = self._identify_critical_issues(complexity, verification, tests)

        # Generate recommendations
        recommendations = self._generate_recommendations(complexity, verification, tests)

        return {
            "metadata": {
                "repository": repo_name,
                "path": repo_path,
                "timestamp": timestamp,
                "analysis_version": "1.0.0",
            },
            "summary": {
                "health_score": health_score,
                "critical_issues_count": len(critical_issues),
                "total_files_analyzed": complexity.get("summary", {}).get("total_files", 0),
                "languages_detected": self._get_languages(complexity),
                "test_coverage_available": bool(tests.get("coverage", {})),
                "formal_verification_performed": bool(verification.get("contracts", {})),
            },
            "complexity_analysis": self._format_complexity_results(complexity),
            "verification_analysis": self._format_verification_results(verification),
            "test_analysis": self._format_test_results(tests),
            "critical_issues": critical_issues,
            "recommendations": recommendations,
            "detailed_findings": self._compile_detailed_findings(complexity, verification, tests),
        }

    def _calculate_health_score(
        self, complexity: Dict[str, Any], verification: Dict[str, Any], tests: Dict[str, Any]
    ) -> float:
        """Calculate overall repository health score (0-100)."""
        score = 100.0

        # Complexity factors
        avg_complexity = complexity.get("summary", {}).get("average_complexity", 0)
        if avg_complexity > 10:
            score -= min(20, (avg_complexity - 10) * 2)

        complexity_dist = complexity.get("summary", {}).get("complexity_distribution", {})
        high_complexity = complexity_dist.get("E (31-40)", 0) + complexity_dist.get("F (41+)", 0)
        if high_complexity > 0:
            score -= min(15, high_complexity * 3)

        # Test factors
        test_summary = tests.get("summary", {})
        if test_summary:
            success_rate = test_summary.get("success_rate", 0)
            score -= (100 - success_rate) * 0.3
        else:
            score -= 20  # No tests found

        # Verification factors
        security_issues = 0
        for lang_results in verification.get("security", {}).values():
            if isinstance(lang_results, dict):
                security_issues += len(lang_results.get("results", []))

        if security_issues > 0:
            score -= min(25, security_issues * 2)

        return max(0, score)

    def _identify_critical_issues(
        self, complexity: Dict[str, Any], verification: Dict[str, Any], tests: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify critical issues that need immediate attention."""
        critical_issues = []

        # High complexity functions
        for file_path, metrics in complexity.get("files", {}).items():
            if isinstance(metrics, dict) and "functions" in metrics:
                for func in metrics["functions"]:
                    if func.get("complexity", 0) > 20:
                        critical_issues.append(
                            {
                                "type": "high_complexity",
                                "severity": "high",
                                "location": f"{file_path}:{func.get('lineno', 'unknown')}",
                                "description": (
                                    f"Function '{func.get('name')}' has complexity "
                                    f"{func.get('complexity')} (threshold: 20)"
                                ),
                                "recommendation": "Refactor this function to reduce complexity",
                            }
                        )

        # Security vulnerabilities
        security_results = verification.get("security", {})

        # Check bandit results
        bandit_results = security_results.get("bandit", {}).get("results", [])
        for issue in bandit_results:
            if issue.get("issue_severity", "").upper() in ["HIGH", "MEDIUM"]:
                critical_issues.append(
                    {
                        "type": "security_vulnerability",
                        "severity": issue.get("issue_severity", "unknown").lower(),
                        "location": f"{issue.get('filename')}:{issue.get('line_number')}",
                        "description": issue.get("issue_text", "Security issue detected"),
                        "recommendation": "Review and fix this security vulnerability",
                    }
                )

        # Check for secrets
        secrets = security_results.get("secrets", {})
        if secrets.get("found", 0) > 0:
            for secret in secrets.get("details", []):
                critical_issues.append(
                    {
                        "type": "hardcoded_secret",
                        "severity": "critical",
                        "location": secret.get("file", "unknown"),
                        "description": f"Potential {secret.get('type', 'secret')} found",
                        "recommendation": (
                            "Remove hardcoded secrets and use environment variables "
                            "or secret management systems"
                        ),
                    }
                )

        # Failed tests
        test_summary = tests.get("summary", {})
        if test_summary.get("failed", 0) > 0:
            critical_issues.append(
                {
                    "type": "test_failures",
                    "severity": "high",
                    "location": "test suite",
                    "description": f"{test_summary.get('failed')} tests are failing",
                    "recommendation": "Fix failing tests to ensure code reliability",
                }
            )

        # Type checking errors
        type_errors = verification.get("type_checking", {})
        for tool, results in type_errors.items():
            if isinstance(results, dict) and results.get("total_issues", 0) > 0:
                critical_issues.append(
                    {
                        "type": "type_errors",
                        "severity": "medium",
                        "location": f"{tool} type checking",
                        "description": f"{results.get('total_issues')} type errors found",
                        "recommendation": "Fix type errors to improve code reliability",
                    }
                )

        return critical_issues

    def _generate_recommendations(
        self, complexity: Dict[str, Any], verification: Dict[str, Any], tests: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # Test coverage recommendations
        if not tests.get("discovered_frameworks"):
            recommendations.append(
                {
                    "category": "Testing",
                    "priority": "high",
                    "recommendation": (
                        "No test framework detected. Implement unit tests to ensure "
                        "code reliability."
                    ),
                    "action": (
                        "Set up a testing framework appropriate for your language "
                        "(pytest, jest, JUnit, etc.)"
                    ),
                }
            )
        elif tests.get("summary", {}).get("total_tests", 0) < 10:
            recommendations.append(
                {
                    "category": "Testing",
                    "priority": "medium",
                    "recommendation": "Low test count detected. Increase test coverage.",
                    "action": (
                        "Write more comprehensive tests covering edge cases and "
                        "main functionality"
                    ),
                }
            )

        # Complexity recommendations
        avg_complexity = complexity.get("summary", {}).get("average_complexity", 0)
        if avg_complexity > 15:
            recommendations.append(
                {
                    "category": "Code Quality",
                    "priority": "high",
                    "recommendation": "High average code complexity detected.",
                    "action": "Refactor complex functions, extract methods, and simplify logic",
                }
            )

        # Security recommendations
        if not verification.get("security"):
            recommendations.append(
                {
                    "category": "Security",
                    "priority": "high",
                    "recommendation": "No security analysis performed.",
                    "action": (
                        "Run security scanning tools (bandit, gosec, etc.) appropriate "
                        "for your language"
                    ),
                }
            )

        # Documentation recommendations
        missing_docs = sum(
            1
            for f in complexity.get("files", {}).values()
            if isinstance(f, dict) and f.get("comments", 0) < f.get("sloc", 1) * 0.1
        )
        if missing_docs > 5:
            recommendations.append(
                {
                    "category": "Documentation",
                    "priority": "medium",
                    "recommendation": "Many files lack sufficient documentation.",
                    "action": "Add docstrings and comments to improve code maintainability",
                }
            )

        # CI/CD recommendations
        ci_files = [
            ".github/workflows",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".travis.yml",
            "azure-pipelines.yml",
        ]
        has_ci = any(
            (Path(complexity.get("metadata", {}).get("path", ".")) / ci).exists() for ci in ci_files
        )
        if not has_ci:
            recommendations.append(
                {
                    "category": "DevOps",
                    "priority": "medium",
                    "recommendation": "No CI/CD configuration detected.",
                    "action": "Set up continuous integration to automatically run tests and checks",
                }
            )

        return recommendations

    def _format_complexity_results(self, complexity: Dict) -> Dict[str, Any]:
        """Format complexity results for reporting."""
        summary = complexity.get("summary", {})

        # Get top complex files
        complex_files = []
        for file_path, metrics in complexity.get("files", {}).items():
            if isinstance(metrics, dict) and "total_complexity" in metrics:
                complex_files.append(
                    {
                        "file": file_path,
                        "complexity": metrics["total_complexity"],
                        "loc": metrics.get("loc", 0),
                        "functions": len(metrics.get("functions", [])),
                    }
                )

        complex_files.sort(key=lambda x: x["complexity"], reverse=True)

        return {
            "summary": summary,
            "top_complex_files": complex_files[:10],
            "complexity_distribution": summary.get("complexity_distribution", {}),
            "metrics": {
                "total_lines": summary.get("total_loc", 0),
                "logical_lines": summary.get("total_lloc", 0),
                "average_complexity": summary.get("average_complexity", 0),
                "files_analyzed": summary.get("total_files", 0),
            },
        }

    def _format_verification_results(self, verification: Dict[str, Any]) -> Dict[str, Any]:
        """Format verification results for reporting."""
        formatted: Dict[str, Dict[str, Any]] = {
            "contracts_verified": {},
            "security_summary": {},
            "type_checking_summary": {},
            "static_analysis_summary": {},
        }

        # Summarize contract verification
        for lang, results in verification.get("contracts", {}).items():
            if results:
                formatted["contracts_verified"][lang] = {
                    "tools_used": list(results.keys()),
                    "files_analyzed": len([k for k, v in results.items() if isinstance(v, dict)]),
                }

        # Summarize security findings
        security = verification.get("security", {})
        if "bandit" in security:
            bandit = security["bandit"]
            if isinstance(bandit, dict) and "metrics" in bandit:
                formatted["security_summary"]["bandit"] = bandit["metrics"]

        if "secrets" in security:
            secrets = security["secrets"]
            formatted["security_summary"]["secrets"] = {
                "found": secrets.get("found", 0),
                "types": [s.get("type") for s in secrets.get("details", [])],
            }

        # Summarize type checking
        for tool, results in verification.get("type_checking", {}).items():
            if isinstance(results, dict):
                formatted["type_checking_summary"][tool] = {
                    "total_issues": results.get("total_issues", 0),
                    "status": results.get("status", "unknown"),
                }

        # Summarize linting
        for tool, results in verification.get("linting", {}).items():
            if isinstance(results, dict):
                formatted["static_analysis_summary"][tool] = {
                    "total_issues": results.get("total_issues", 0),
                    "status": results.get("status", "unknown"),
                }

        return formatted

    def _format_test_results(self, tests: Dict) -> Dict[str, Any]:
        """Format test results for reporting."""
        summary = tests.get("summary", {})

        formatted = {
            "summary": summary,
            "frameworks_detected": tests.get("discovered_frameworks", {}),
            "test_results_by_framework": {},
            "coverage_available": bool(tests.get("coverage", {})),
        }

        # Summarize results by framework
        for framework, results in tests.get("test_results", {}).items():
            if isinstance(results, dict) and "summary" in results:
                formatted["test_results_by_framework"][framework] = results["summary"]

        return formatted

    def _compile_detailed_findings(
        self, complexity: Dict[str, Any], verification: Dict[str, Any], tests: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Compile detailed findings for verification steps."""
        findings: Dict[str, List[Dict[str, Any]]] = {
            "complexity_issues": [],
            "security_issues": [],
            "test_failures": [],
            "type_errors": [],
            "verification_failures": [],
        }

        # Complexity issues
        for file_path, metrics in complexity.get("files", {}).items():
            if isinstance(metrics, dict) and "functions" in metrics:
                for func in metrics["functions"]:
                    if func.get("complexity", 0) > 10:
                        findings["complexity_issues"].append(
                            {
                                "file": file_path,
                                "function": func.get("name"),
                                "line": func.get("lineno"),
                                "complexity": func.get("complexity"),
                                "rank": func.get("rank"),
                            }
                        )

        # Security issues
        bandit_results = verification.get("security", {}).get("bandit", {}).get("results", [])
        for issue in bandit_results:
            findings["security_issues"].append(
                {
                    "file": issue.get("filename"),
                    "line": issue.get("line_number"),
                    "severity": issue.get("issue_severity"),
                    "confidence": issue.get("issue_confidence"),
                    "text": issue.get("issue_text"),
                    "test_id": issue.get("test_id"),
                }
            )

        # Test failures
        for _framework, results in tests.get("test_results", {}).items():
            if isinstance(results, dict):
                # Extract failed tests from structured results
                if "structured_results" in results:
                    # This would need framework-specific parsing
                    pass

        return findings

    def _get_languages(self, complexity: Dict) -> List[str]:
        """Extract detected languages from complexity analysis."""
        # This would be populated by the language detector
        # For now, return based on file extensions
        languages = set()
        for file_path in complexity.get("files", {}).keys():
            ext = Path(file_path).suffix
            if ext == ".py":
                languages.add("Python")
            elif ext in [".js", ".jsx"]:
                languages.add("JavaScript")
            elif ext in [".ts", ".tsx"]:
                languages.add("TypeScript")
            elif ext == ".java":
                languages.add("Java")
            elif ext in [".c", ".cpp", ".cc", ".cxx"]:
                languages.add("C/C++")
            elif ext == ".go":
                languages.add("Go")
            elif ext == ".rs":
                languages.add("Rust")
            elif ext == ".cs":
                languages.add("C#")

        return sorted(list(languages))

    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate Markdown report."""
        template = self.jinja_env.get_template("markdown_report")
        content = template.render(**report_data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report_data['metadata']['repository']}_{timestamp}.md"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def _generate_html_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate HTML report."""
        template = self.jinja_env.get_template("html_report")
        content = template.render(**report_data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report_data['metadata']['repository']}_{timestamp}.html"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def _generate_json_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate JSON report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report_data['metadata']['repository']}_{timestamp}.json"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        return filepath

    def _generate_pdf_report(self, report_data: Dict[str, Any]) -> Path:
        """Generate PDF report."""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        # Title
        pdf.set_font("Arial", "B", 20)
        pdf.cell(
            0,
            10,
            f"Code Analysis Report: {report_data['metadata']['repository']}",
            ln=True,
            align="C",
        )
        pdf.ln(10)

        # Summary
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Executive Summary", ln=True)
        pdf.set_font("Arial", size=12)

        summary = report_data["summary"]
        pdf.cell(0, 10, f"Health Score: {summary['health_score']:.1f}/100", ln=True)
        pdf.cell(0, 10, f"Critical Issues: {summary['critical_issues_count']}", ln=True)
        pdf.cell(0, 10, f"Languages: {', '.join(summary['languages_detected'])}", ln=True)
        pdf.ln(10)

        # Critical Issues
        if report_data["critical_issues"]:
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, "Critical Issues", ln=True)
            pdf.set_font("Arial", size=11)

            for issue in report_data["critical_issues"][:10]:
                pdf.multi_cell(
                    0, 8, f"• [{issue['severity'].upper()}] {issue['description']}", align="L"
                )
                pdf.ln(2)

        # Recommendations
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Recommendations", ln=True)
        pdf.set_font("Arial", size=11)

        for rec in report_data["recommendations"]:
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f"{rec['category']} ({rec['priority']})", ln=True)
            pdf.set_font("Arial", size=11)
            pdf.multi_cell(0, 6, rec["recommendation"], align="L")
            pdf.multi_cell(0, 6, f"Action: {rec['action']}", align="L")
            pdf.ln(5)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{report_data['metadata']['repository']}_{timestamp}.pdf"
        filepath = self.results_dir / filename

        pdf.output(str(filepath))

        return filepath

    def _generate_verification_steps(self, report_data: Dict[str, Any]) -> Path:
        """Generate detailed verification steps document."""
        template = self.jinja_env.get_template("verification_steps")
        content = template.render(**report_data)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"verification_steps_{report_data['metadata']['repository']}_{timestamp}.md"
        filepath = self.results_dir / filename

        with open(filepath, "w") as f:
            f.write(content)

        return filepath

    def _get_templates(self) -> Dict[str, str]:
        """Return Jinja2 templates."""
        return {
            "markdown_report": """# Code Analysis Report: {{ metadata.repository }}

Generated: {{ metadata.timestamp }}

## Executive Summary

- **Health Score**: {{ "%.1f"|format(summary.health_score) }}/100
- **Critical Issues**: {{ summary.critical_issues_count }}
- **Files Analyzed**: {{ summary.total_files_analyzed }}
- **Languages**: {{ summary.languages_detected|join(', ') }}

## Complexity Analysis

### Summary
- **Total Files**: {{ complexity_analysis.metrics.files_analyzed }}
- **Total Lines**: {{ complexity_analysis.metrics.total_lines }}
- **Average Complexity**: {{ "%.2f"|format(complexity_analysis.metrics.average_complexity) }}

### Complexity Distribution
{% for range, count in complexity_analysis.complexity_distribution.items() %}
- {{ range }}: {{ count }} functions
{% endfor %}

### Most Complex Files
{% for file in complexity_analysis.top_complex_files[:5] %}
{{ loop.index }}. `{{ file.file }}` - Complexity: {{ file.complexity }}
{% endfor %}

## Verification Analysis

### Security Summary
{% if verification_analysis.security_summary %}
{% for tool, results in verification_analysis.security_summary.items() %}
- **{{ tool }}**: {{ results }}
{% endfor %}
{% endif %}

### Type Checking Summary
{% for tool, results in verification_analysis.type_checking_summary.items() %}
- **{{ tool }}**: {{ results.total_issues }} issues ({{ results.status }})
{% endfor %}

## Test Analysis

### Summary
- **Total Tests**: {{ test_analysis.summary.total_tests }}
- **Passed**: {{ test_analysis.summary.passed }}
- **Failed**: {{ test_analysis.summary.failed }}
- **Success Rate**: {{ "%.1f"|format(test_analysis.summary.success_rate) }}%

### Frameworks Detected
{{ test_analysis.summary.frameworks_used|join(', ') }}

## Critical Issues

{% for issue in critical_issues %}
### {{ loop.index }}. {{ issue.type|replace('_', ' ')|title }}
- **Severity**: {{ issue.severity }}
- **Location**: `{{ issue.location }}`
- **Description**: {{ issue.description }}
- **Recommendation**: {{ issue.recommendation }}
{% endfor %}

## Recommendations

{% for rec in recommendations %}
### {{ rec.category }} (Priority: {{ rec.priority }})
**{{ rec.recommendation }}**

Action: {{ rec.action }}
{% endfor %}
""",
            "html_report": """<!DOCTYPE html>
<html>
<head>
    <title>Code Analysis Report: {{ metadata.repository }}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
        h1, h2, h3 { color: #333; }
        .summary { background: #f4f4f4; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .critical { color: #d32f2f; }
        .high { color: #f57c00; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .score { font-size: 48px; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Code Analysis Report: {{ metadata.repository }}</h1>
    <p>Generated: {{ metadata.timestamp }}</p>

    <div class="summary">
        <h2>Executive Summary</h2>
        <div class="metric">
            <div class="score">{{ "%.1f"|format(summary.health_score) }}</div>
            <div>Health Score</div>
        </div>
        <div class="metric">
            <div class="score critical">{{ summary.critical_issues_count }}</div>
            <div>Critical Issues</div>
        </div>
    </div>

    <h2>Languages Detected</h2>
    <p>{{ summary.languages_detected|join(', ') }}</p>

    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Metric</th>
            <th>Value</th>
        </tr>
        <tr>
            <td>Total Tests</td>
            <td>{{ test_analysis.summary.total_tests }}</td>
        </tr>
        <tr>
            <td>Passed</td>
            <td>{{ test_analysis.summary.passed }}</td>
        </tr>
        <tr>
            <td>Failed</td>
            <td class="high">{{ test_analysis.summary.failed }}</td>
        </tr>
        <tr>
            <td>Success Rate</td>
            <td>{{ "%.1f"|format(test_analysis.summary.success_rate) }}%</td>
        </tr>
    </table>

    <h2>Critical Issues</h2>
    {% for issue in critical_issues %}
    <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #d32f2f;
         background: #ffebee;">
        <h3>{{ issue.type|replace('_', ' ')|title }}</h3>
        <p><strong>Severity:</strong>
           <span class="{{ issue.severity }}">{{ issue.severity|upper }}</span></p>
        <p><strong>Location:</strong> <code>{{ issue.location }}</code></p>
        <p>{{ issue.description }}</p>
        <p><em>{{ issue.recommendation }}</em></p>
    </div>
    {% endfor %}

    <h2>Recommendations</h2>
    {% for rec in recommendations %}
    <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #2196f3;
         background: #e3f2fd;">
        <h3>{{ rec.category }}</h3>
        <p><strong>Priority:</strong> {{ rec.priority }}</p>
        <p>{{ rec.recommendation }}</p>
        <p><strong>Action:</strong> {{ rec.action }}</p>
    </div>
    {% endfor %}
</body>
</html>""",
            "verification_steps": """# Verification Steps for {{ metadata.repository }}

Generated: {{ metadata.timestamp }}

## How to Verify Our Findings

This document provides step-by-step instructions to independently verify the analysis results.

### 1. Complexity Analysis Verification

To verify the complexity metrics:

```bash
# Python projects
pip install radon
radon cc -s {{ metadata.path }} --total-average

# JavaScript projects
npm install -g complexity-report
cr --format json {{ metadata.path }}
```

### 2. Security Analysis Verification

{% if 'Python' in summary.languages_detected %}
#### Python Security Checks
```bash
# Install and run bandit
pip install bandit
bandit -r {{ metadata.path }} -f json

# Check for secrets
pip install truffleHog
trufflehog filesystem {{ metadata.path }}
```
{% endif %}

{% if 'JavaScript' in summary.languages_detected or 'TypeScript' in summary.languages_detected %}
#### JavaScript/TypeScript Security Checks
```bash
# Install and run ESLint with security plugin
npm install -g eslint eslint-plugin-security
eslint {{ metadata.path }} --ext .js,.ts

# Run npm audit
cd {{ metadata.path }}
npm audit
```
{% endif %}

{% if 'Go' in summary.languages_detected %}
#### Go Security Checks
```bash
# Install and run gosec
go install github.com/securego/gosec/v2/cmd/gosec@latest
gosec ./...

# Run staticcheck
go install honnef.co/go/tools/cmd/staticcheck@latest
staticcheck ./...
```
{% endif %}

### 3. Test Execution Verification

{% for framework, detected in test_analysis.frameworks_detected.items() %}
{% if detected %}
#### {{ framework|title }} Tests
```bash
# Run {{ framework }} tests
{% if framework == 'python' %}
{% for fw, info in detected.items() %}
{% if info.detected %}
# {{ fw }} detected
{{ info.command|join(' ')|replace('{output}', 'test_results.json') }}
{% endif %}
{% endfor %}
{% endif %}
```
{% endif %}
{% endfor %}

### 4. Type Checking Verification

{% if 'Python' in summary.languages_detected %}
#### Python Type Checking
```bash
pip install mypy
mypy {{ metadata.path }}
```
{% endif %}

{% if 'TypeScript' in summary.languages_detected %}
#### TypeScript Type Checking
```bash
cd {{ metadata.path }}
npx tsc --noEmit
```
{% endif %}

### 5. Critical Issues Verification

{% for issue in critical_issues[:5] %}
#### {{ loop.index }}. {{ issue.type|replace('_', ' ')|title }}

**File**: `{{ issue.location }}`

To verify this issue:
```bash
# Open the file and check line
{% if 'complexity' in issue.type %}
# Check complexity with radon
radon cc {{ issue.location.split(':')[0] }} -s
{% elif 'security' in issue.type %}
# Run security scan on specific file
bandit {{ issue.location.split(':')[0] }}
{% elif 'test' in issue.type %}
# Run tests to see failures
pytest -v  # or appropriate test command
{% endif %}
```

{% endfor %}

### 6. Manual Code Review

For comprehensive verification, perform manual code review focusing on:

1. **High Complexity Areas**
   {% for file in complexity_analysis.top_complex_files[:3] %}
   - `{{ file.file }}` (Complexity: {{ file.complexity }})
   {% endfor %}

2. **Security Hotspots**
   - Authentication and authorization logic
   - Input validation and sanitization
   - Cryptographic operations
   - File and network operations

3. **Test Coverage Gaps**
   - Uncovered critical paths
   - Edge cases
   - Error handling

### 7. Automated Verification Script

Save this as `verify_analysis.sh`:

```bash
#!/bin/bash
REPO_PATH="{{ metadata.path }}"

echo "Starting verification of analysis results..."

# Detect languages
echo "Detecting languages..."
find "$REPO_PATH" -name "*.py" | head -1 && HAS_PYTHON=1
find "$REPO_PATH" -name "*.js" -o -name "*.ts" | head -1 && HAS_JS=1
find "$REPO_PATH" -name "*.go" | head -1 && HAS_GO=1

# Run appropriate tools
if [ "$HAS_PYTHON" ]; then
    echo "Running Python analysis..."
    which radon && radon cc "$REPO_PATH" -s --total-average
    which bandit && bandit -r "$REPO_PATH"
    which mypy && mypy "$REPO_PATH"
fi

if [ "$HAS_JS" ]; then
    echo "Running JavaScript analysis..."
    which eslint && eslint "$REPO_PATH"
    cd "$REPO_PATH" && npm audit
fi

if [ "$HAS_GO" ]; then
    echo "Running Go analysis..."
    cd "$REPO_PATH"
    which gosec && gosec ./...
    which staticcheck && staticcheck ./...
    go test ./...
fi

echo "Verification complete!"
```

Make it executable and run:
```bash
chmod +x verify_analysis.sh
./verify_analysis.sh
```

## Understanding the Results

### Complexity Scores
- **A (1-5)**: Simple, easy to understand
- **B (6-10)**: More complex, but manageable
- **C (11-20)**: Complex, consider refactoring
- **D (21-30)**: Very complex, refactoring recommended
- **E (31-40)**: Extremely complex, refactoring strongly recommended
- **F (41+)**: Untestable, refactoring required

### Security Severity Levels
- **Critical**: Immediate action required
- **High**: Should be fixed soon
- **Medium**: Should be reviewed and fixed
- **Low**: Minor issues, fix when convenient

### Test Success Rates
- **90-100%**: Excellent
- **80-90%**: Good
- **70-80%**: Needs improvement
- **Below 70%**: Critical attention needed

## Next Steps

1. Address critical issues first
2. Improve test coverage for uncovered code
3. Refactor high-complexity functions
4. Set up CI/CD to run these checks automatically
5. Establish code quality gates

For questions about these results, consult your team's security and quality guidelines.
""",
        }


class SummaryReporter:
    """Generates quick summary reports for console output."""

    @staticmethod
    def generate_console_summary(
        complexity: Dict[str, Any], verification: Dict[str, Any], tests: Dict[str, Any]
    ) -> str:
        """Generate a concise summary for console output."""
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("VIBE VERIFIER ANALYSIS SUMMARY")
        lines.append("=" * 60)

        # Complexity summary
        lines.append("\n📊 COMPLEXITY ANALYSIS")
        summary = complexity.get("summary", {})
        lines.append(f"  Files analyzed: {summary.get('total_files', 0)}")
        lines.append(f"  Total lines: {summary.get('total_loc', 0)}")
        lines.append(f"  Average complexity: {summary.get('average_complexity', 0):.2f}")

        # Show complexity distribution
        dist = summary.get("complexity_distribution", {})
        if dist:
            lines.append("  Complexity distribution:")
            for level, count in dist.items():
                if count > 0:
                    lines.append(f"    {level}: {count} functions")

        # Test summary
        lines.append("\n🧪 TEST ANALYSIS")
        test_summary = tests.get("summary", {})
        if test_summary.get("total_tests", 0) > 0:
            lines.append(f"  Total tests: {test_summary.get('total_tests', 0)}")
            lines.append(f"  Passed: {test_summary.get('passed', 0)} ✓")
            lines.append(f"  Failed: {test_summary.get('failed', 0)} ✗")
            lines.append(f"  Success rate: {test_summary.get('success_rate', 0):.1f}%")
        else:
            lines.append("  ⚠️  No tests found!")

        # Security summary
        lines.append("\n🔒 SECURITY ANALYSIS")
        security = verification.get("security", {})

        if "bandit" in security:
            bandit = security["bandit"]
            if isinstance(bandit, dict) and "results" in bandit:
                lines.append(f"  Security issues found: {len(bandit['results'])}")

        if "secrets" in security:
            secrets = security["secrets"]
            if secrets.get("found", 0) > 0:
                lines.append(f"  ⚠️  Potential secrets found: {secrets['found']}")

        # Type checking summary
        type_checking = verification.get("type_checking", {})
        if type_checking:
            lines.append("\n📝 TYPE CHECKING")
            for tool, results in type_checking.items():
                if isinstance(results, dict):
                    lines.append(f"  {tool}: {results.get('total_issues', 0)} issues")

        lines.append("\n" + "=" * 60)
        lines.append("Full reports generated in ./reports/")
        lines.append("=" * 60 + "\n")

        return "\n".join(lines)
