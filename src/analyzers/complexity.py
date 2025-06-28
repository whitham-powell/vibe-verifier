"""Code complexity analysis module."""

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import radon.complexity as radon_cc
import radon.metrics as radon_metrics
from radon.raw import analyze


class ComplexityAnalyzer:
    """Analyzes code complexity metrics for multiple programming languages."""

    def __init__(self, repo_path: str):
        """Initialize the ComplexityAnalyzer.

        Args:
            repo_path: Path to the repository to analyze.
        """
        self.repo_path = Path(repo_path)
        self.results: Dict[str, Any] = {"files": {}, "summary": {}, "by_language": {}}
        self.language_detector = LanguageDetector(repo_path)

    def analyze(self) -> Dict[str, Any]:
        """Analyze complexity metrics for all supported files in the repository."""
        # Detect languages in the repository
        language_info = self.language_detector.detect()

        total_complexity = 0
        total_loc = 0
        total_files_analyzed = 0
        all_complexity_scores = []

        # Analyze Python files with Radon (built-in)
        if "Python" in language_info.get("languages", {}):
            python_results = self._analyze_python_files()
            self.results["by_language"]["Python"] = python_results
            total_complexity += python_results.get("total_complexity", 0)
            total_loc += python_results.get("total_loc", 0)
            total_files_analyzed += python_results.get("files_analyzed", 0)
            all_complexity_scores.extend(python_results.get("complexity_scores", []))

        # Analyze JavaScript/TypeScript with external tools
        if any(lang in language_info.get("languages", {}) for lang in ["JavaScript", "TypeScript"]):
            js_results = self._analyze_javascript_files()
            self.results["by_language"]["JavaScript/TypeScript"] = js_results
            total_complexity += js_results.get("total_complexity", 0)
            total_loc += js_results.get("total_loc", 0)
            total_files_analyzed += js_results.get("files_analyzed", 0)
            all_complexity_scores.extend(js_results.get("complexity_scores", []))

        # Analyze Go files
        if "Go" in language_info.get("languages", {}):
            go_results = self._analyze_go_files()
            self.results["by_language"]["Go"] = go_results
            total_complexity += go_results.get("total_complexity", 0)
            total_loc += go_results.get("total_loc", 0)
            total_files_analyzed += go_results.get("files_analyzed", 0)
            all_complexity_scores.extend(go_results.get("complexity_scores", []))

        # Analyze Java files
        if "Java" in language_info.get("languages", {}):
            java_results = self._analyze_java_files()
            self.results["by_language"]["Java"] = java_results
            total_complexity += java_results.get("total_complexity", 0)
            total_loc += java_results.get("total_loc", 0)
            total_files_analyzed += java_results.get("files_analyzed", 0)
            all_complexity_scores.extend(java_results.get("complexity_scores", []))

        # Calculate overall summary
        self.results["summary"] = {
            "total_files": total_files_analyzed,
            "total_complexity": total_complexity,
            "average_complexity": total_complexity / total_files_analyzed
            if total_files_analyzed
            else 0,
            "total_loc": total_loc,
            "complexity_distribution": self._calculate_complexity_distribution(
                all_complexity_scores
            ),
            "languages_analyzed": list(self.results["by_language"].keys()),
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

    def _analyze_python_files(self) -> Dict[str, Any]:
        """Analyze complexity for all Python files."""
        python_files = self._find_python_files()

        total_complexity = 0
        total_loc = 0
        total_lloc = 0
        complexity_scores = []
        files_analyzed = 0

        for file_path in python_files:
            try:
                metrics = self._analyze_python_file(file_path)
                if metrics:
                    self.results["files"][str(file_path)] = metrics
                    total_complexity += metrics["total_complexity"]
                    total_loc += metrics["loc"]
                    total_lloc += metrics["lloc"]
                    complexity_scores.extend(metrics["complexity_scores"])
                    files_analyzed += 1
            except Exception as e:
                self.results["files"][str(file_path)] = {"error": str(e), "status": "failed"}

        return {
            "total_complexity": total_complexity,
            "total_loc": total_loc,
            "total_lloc": total_lloc,
            "complexity_scores": complexity_scores,
            "files_analyzed": files_analyzed,
        }

    def _analyze_python_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single Python file for complexity metrics."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get raw metrics
            raw_metrics = analyze(content)

            # Get cyclomatic complexity
            cc_results = radon_cc.cc_visit(content)

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

    def _analyze_javascript_files(self) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript files using external tools."""
        results = {
            "total_complexity": 0,
            "total_loc": 0,
            "complexity_scores": [],
            "files_analyzed": 0,
            "tool_used": None,
            "tool_available": False,
        }

        # Try different JavaScript complexity tools
        if shutil.which("es6-plato"):
            results["tool_used"] = "es6-plato"
            results["tool_available"] = True
            # Placeholder for plato analysis
            return self._basic_js_analysis()
        elif shutil.which("complexity-report"):
            results["tool_used"] = "complexity-report"
            results["tool_available"] = True
            # Placeholder for complexity-report
            return self._basic_js_analysis()
        elif shutil.which("eslint"):
            # ESLint with complexity rule can provide basic complexity
            results["tool_used"] = "eslint"
            results["tool_available"] = True
            return self._run_eslint_complexity()
        else:
            # Fallback to counting lines and basic analysis
            return self._basic_js_analysis()

    def _run_eslint_complexity(self) -> Dict[str, Any]:
        """Run ESLint to get complexity information."""
        try:
            # Create a temporary ESLint config with complexity rule
            eslint_config = {
                "rules": {"complexity": ["error", 0]},  # Report all complexity
                "parserOptions": {"ecmaVersion": 2021, "sourceType": "module"},
            }

            config_path = self.repo_path / ".eslintrc.temp.json"
            with open(config_path, "w") as f:
                json.dump(eslint_config, f)

            cmd = [
                "eslint",
                ".",
                "--ext",
                ".js,.jsx,.ts,.tsx",
                "--config",
                str(config_path),
                "--format",
                "json",
                "--no-inline-config",
            ]

            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, timeout=60
            )

            # Clean up temp config
            config_path.unlink(missing_ok=True)

            if result.stdout:
                return self._parse_eslint_output(result.stdout)

        except Exception:
            pass

        return self._basic_js_analysis()

    def _parse_eslint_output(self, output: str) -> Dict[str, Any]:
        """Parse ESLint JSON output for complexity information."""
        try:
            data = json.loads(output)
            total_complexity = 0
            total_loc = 0
            complexity_scores = []
            files_analyzed = 0

            for file_result in data:
                if file_result.get("messages"):
                    file_path = file_result["filePath"]

                    # Count lines
                    if os.path.exists(file_path):
                        with open(file_path, "r") as f:
                            loc = len(f.readlines())
                            total_loc += loc

                    # Extract complexity from messages
                    for msg in file_result["messages"]:
                        if "complexity" in msg.get("ruleId", ""):
                            # Extract complexity number from message
                            match = re.search(r"complexity of (\d+)", msg.get("message", ""))
                            if match:
                                complexity = int(match.group(1))
                                total_complexity += complexity
                                complexity_scores.append(complexity)

                    files_analyzed += 1

                    # Store in results
                    self.results["files"][file_path] = {"complexity": total_complexity, "loc": loc}

            return {
                "total_complexity": total_complexity,
                "total_loc": total_loc,
                "complexity_scores": complexity_scores,
                "files_analyzed": files_analyzed,
            }
        except Exception:
            return self._basic_js_analysis()

    def _basic_js_analysis(self) -> Dict[str, Any]:
        """Provide basic JavaScript analysis when no tools are available."""
        js_extensions = [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]
        total_loc = 0
        files_analyzed = 0

        for ext in js_extensions:
            for file_path in self.repo_path.rglob(f"*{ext}"):
                if any(
                    part in file_path.parts for part in ["node_modules", ".git", "dist", "build"]
                ):
                    continue

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                        loc = len([line for line in lines if line.strip()])
                        total_loc += loc
                        files_analyzed += 1

                        self.results["files"][str(file_path)] = {
                            "loc": loc,
                            "language": "JavaScript/TypeScript",
                        }
                except Exception:
                    continue

        return {
            "total_complexity": 0,  # Can't calculate without tools
            "total_loc": total_loc,
            "complexity_scores": [],
            "files_analyzed": files_analyzed,
            "note": "Complexity analysis requires external tools "
            "(eslint, complexity-report, or es6-plato)",
        }

    def _analyze_go_files(self) -> Dict[str, Any]:
        """Analyze Go files using gocyclo or other tools."""
        # results variable removed as it was unused

        if shutil.which("gocyclo"):
            return self._run_gocyclo()
        else:
            return self._basic_go_analysis()

    def _run_gocyclo(self) -> Dict[str, Any]:
        """Run gocyclo for Go complexity analysis."""
        try:
            cmd = ["gocyclo", "-top", "1000", "."]
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0 and result.stdout:
                return self._parse_gocyclo_output(result.stdout)

        except Exception:
            pass

        return self._basic_go_analysis()

    def _parse_gocyclo_output(self, output: str) -> Dict[str, Any]:
        """Parse gocyclo output."""
        total_complexity = 0
        complexity_scores = []
        files_analyzed = set()

        for line in output.strip().split("\n"):
            if line:
                # Format: "complexity package function file:line:column"
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        complexity = int(parts[0])
                        file_info = parts[-1]
                        file_path = file_info.split(":")[0]

                        total_complexity += complexity
                        complexity_scores.append(complexity)
                        files_analyzed.add(file_path)

                        # Store file-level aggregated complexity
                        if file_path not in self.results["files"]:
                            self.results["files"][file_path] = {"complexity": 0, "functions": []}

                        self.results["files"][file_path]["complexity"] += complexity
                        self.results["files"][file_path]["functions"].append(
                            {"name": parts[2], "complexity": complexity}
                        )

                    except (ValueError, IndexError):
                        continue

        # Count LOC for Go files
        total_loc = 0
        for file_path in files_analyzed:
            try:
                with open(file_path, "r") as f:
                    loc = len([line for line in f.readlines() if line.strip()])
                    total_loc += loc
                    if file_path in self.results["files"]:
                        self.results["files"][file_path]["loc"] = loc
            except Exception:
                continue

        return {
            "total_complexity": total_complexity,
            "total_loc": total_loc,
            "complexity_scores": complexity_scores,
            "files_analyzed": len(files_analyzed),
        }

    def _basic_go_analysis(self) -> Dict[str, Any]:
        """Provide basic Go analysis when tools aren't available."""
        total_loc = 0
        files_analyzed = 0

        for file_path in self.repo_path.rglob("*.go"):
            if any(part in file_path.parts for part in ["vendor", ".git"]):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    loc = len(
                        [
                            line
                            for line in lines
                            if line.strip() and not line.strip().startswith("//")
                        ]
                    )
                    total_loc += loc
                    files_analyzed += 1

                    self.results["files"][str(file_path)] = {"loc": loc, "language": "Go"}
            except Exception:
                continue

        return {
            "total_complexity": 0,
            "total_loc": total_loc,
            "complexity_scores": [],
            "files_analyzed": files_analyzed,
            "note": "Complexity analysis requires gocyclo tool",
        }

    def _analyze_java_files(self) -> Dict[str, Any]:
        """Analyze Java files for complexity."""
        if shutil.which("checkstyle"):
            return self._run_checkstyle_complexity()
        elif shutil.which("pmd"):
            # Placeholder for PMD
            return self._basic_java_analysis()
        else:
            return self._basic_java_analysis()

    def _run_checkstyle_complexity(self) -> Dict[str, Any]:
        """Run Checkstyle for Java complexity."""
        # Checkstyle needs a config file with CyclomaticComplexity check
        config_xml = """<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
          "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
          "https://checkstyle.org/dtds/configuration_1_3.dtd">
<module name="Checker">
  <module name="TreeWalker">
    <module name="CyclomaticComplexity">
      <property name="max" value="0"/>
    </module>
  </module>
</module>"""

        try:
            config_path = self.repo_path / "checkstyle-complexity.xml"
            with open(config_path, "w") as f:
                f.write(config_xml)

            cmd = ["checkstyle", "-c", str(config_path), "-f", "xml", "**/*.java"]
            result = subprocess.run(
                cmd, cwd=self.repo_path, capture_output=True, text=True, timeout=60
            )

            config_path.unlink(missing_ok=True)

            if result.stdout:
                # Placeholder for checkstyle parser
                return self._basic_java_analysis()

        except Exception:
            pass

        return self._basic_java_analysis()

    def _basic_java_analysis(self) -> Dict[str, Any]:
        """Provide basic Java analysis."""
        total_loc = 0
        files_analyzed = 0

        for file_path in self.repo_path.rglob("*.java"):
            if any(part in file_path.parts for part in ["target", "build", ".git"]):
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    loc = len(
                        [
                            line
                            for line in lines
                            if line.strip() and not line.strip().startswith("//")
                        ]
                    )
                    total_loc += loc
                    files_analyzed += 1

                    self.results["files"][str(file_path)] = {"loc": loc, "language": "Java"}
            except Exception:
                continue

        return {
            "total_complexity": 0,
            "total_loc": total_loc,
            "complexity_scores": [],
            "files_analyzed": files_analyzed,
            "note": "Complexity analysis requires checkstyle or pmd",
        }


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
