"""Code complexity analysis module."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from radon.raw import analyze


class ComplexityAnalyzer:
    """Analyzes code complexity metrics for Python files."""

    def __init__(self, repo_path: str):
        """Initialize the ComplexityAnalyzer.

        Args:
            repo_path: Path to the repository to analyze.
        """
        self.repo_path = Path(repo_path)
        self.results: Dict[str, Any] = {"files": {}, "summary": {}}

    def analyze(self) -> Dict[str, Any]:
        """Analyze complexity metrics for all Python files in the repository."""
        python_files = self._find_python_files()

        total_complexity = 0
        total_loc = 0
        total_lloc = 0
        complexity_scores = []

        for file_path in python_files:
            try:
                metrics = self._analyze_file(file_path)
                if metrics:
                    self.results["files"][str(file_path)] = metrics
                    total_complexity += metrics["total_complexity"]
                    total_loc += metrics["loc"]
                    total_lloc += metrics["lloc"]
                    complexity_scores.extend(metrics["complexity_scores"])
            except Exception as e:
                self.results["files"][str(file_path)] = {"error": str(e), "status": "failed"}

        # Calculate summary statistics
        self.results["summary"] = {
            "total_files": len(python_files),
            "total_complexity": total_complexity,
            "average_complexity": total_complexity / len(python_files) if python_files else 0,
            "total_loc": total_loc,
            "total_lloc": total_lloc,
            "complexity_distribution": self._calculate_complexity_distribution(complexity_scores),
        }

        return self.results

    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the repository."""
        python_files = []
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    # Skip virtual environments and common exclusions
                    if not any(
                        part in file_path.parts for part in ["venv", "env", "__pycache__", ".git"]
                    ):
                        python_files.append(file_path)
        return python_files

    def _analyze_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single Python file for complexity metrics."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get raw metrics
            raw_metrics = analyze(content)

            # Get cyclomatic complexity
            cc_results = radon_cc.cc_visit(content, file_path.name)

            # Get maintainability index
            mi = radon_metrics.mi_visit(content, True)

            # Extract complexity scores
            complexity_scores = []
            function_complexities = []

            for item in cc_results:
                complexity_scores.append(item.complexity)
                function_complexities.append(
                    {
                        "name": item.name,
                        "type": item.type,
                        "complexity": item.complexity,
                        "rank": radon_cc.cc_rank(item.complexity),
                        "lineno": item.lineno,
                    }
                )

            return {
                "loc": raw_metrics.loc,
                "lloc": raw_metrics.lloc,
                "sloc": raw_metrics.sloc,
                "comments": raw_metrics.comments,
                "blank": raw_metrics.blank,
                "total_complexity": sum(complexity_scores),
                "average_complexity": (
                    sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0
                ),
                "maintainability_index": mi,
                "functions": function_complexities,
                "complexity_scores": complexity_scores,
            }

        except (OSError, SyntaxError):
            return None

    def _calculate_complexity_distribution(self, scores: List[int]) -> Dict[str, int]:
        """Calculate distribution of complexity scores."""
        distribution = {
            "A (1-5)": 0,
            "B (6-10)": 0,
            "C (11-20)": 0,
            "D (21-30)": 0,
            "E (31-40)": 0,
            "F (41+)": 0,
        }

        for score in scores:
            if score <= 5:
                distribution["A (1-5)"] += 1
            elif score <= 10:
                distribution["B (6-10)"] += 1
            elif score <= 20:
                distribution["C (11-20)"] += 1
            elif score <= 30:
                distribution["D (21-30)"] += 1
            elif score <= 40:
                distribution["E (31-40)"] += 1
            else:
                distribution["F (41+)"] += 1

        return distribution


class LanguageDetector:
    """Detects programming languages used in a repository."""

    LANGUAGE_EXTENSIONS = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".r": "R",
        ".m": "MATLAB",
        ".jl": "Julia",
        ".lua": "Lua",
        ".pl": "Perl",
        ".sh": "Shell",
        ".ps1": "PowerShell",
    }

    def __init__(self, repo_path: str):
        """Initialize the LanguageDetector.

        Args:
            repo_path: Path to the repository to analyze.
        """
        self.repo_path = Path(repo_path)

    def detect(self) -> Dict[str, Any]:
        """Detect languages used in the repository."""
        language_stats: Dict[str, Dict[str, Any]] = {}
        total_files = 0

        for root, _, files in os.walk(self.repo_path):
            for file in files:
                file_path = Path(root) / file
                # Skip common exclusions
                if any(
                    part in file_path.parts
                    for part in ["venv", "env", "__pycache__", ".git", "node_modules"]
                ):
                    continue

                ext = file_path.suffix.lower()
                if ext in self.LANGUAGE_EXTENSIONS:
                    lang = self.LANGUAGE_EXTENSIONS[ext]
                    if lang not in language_stats:
                        language_stats[lang] = {"count": 0, "files": []}
                    language_stats[lang]["count"] += 1
                    language_stats[lang]["files"].append(str(file_path.relative_to(self.repo_path)))
                    total_files += 1

        # Calculate percentages
        for lang in language_stats:
            language_stats[lang]["percentage"] = (
                (language_stats[lang]["count"] / total_files * 100) if total_files > 0 else 0
            )

        return {
            "languages": language_stats,
            "total_files": total_files,
            "primary_language": (
                max(language_stats.keys(), key=lambda k: language_stats[k]["count"])
                if language_stats
                else None
            ),
        }
