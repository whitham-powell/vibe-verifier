"""Universal test discovery and execution module for multiple languages."""

import json
import os
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional


class UniversalTestRunner:
    """Discovers and runs tests across multiple programming languages and frameworks."""

    # Test framework patterns and commands
    TEST_FRAMEWORKS = {
        "python": {
            "pytest": {
                "indicators": ["pytest.ini", "conftest.py", "test_*.py", "*_test.py"],
                "command": ["pytest", "--json-report", "--json-report-file={output}", "-v"],
                "config_files": ["pytest.ini", "setup.cfg", "tox.ini", "pyproject.toml"],
            },
            "unittest": {
                "indicators": ["test*.py"],
                "command": ["python", "-m", "unittest", "discover", "-v"],
                "config_files": [],
            },
            "nose": {
                "indicators": ["nose.cfg", ".noserc"],
                "command": ["nosetests", "--with-json", "--json-file={output}"],
                "config_files": ["nose.cfg", ".noserc"],
            },
            "doctest": {
                "indicators": ["*.py"],
                "command": ["python", "-m", "doctest", "-v"],
                "config_files": [],
            },
        },
        "javascript": {
            "jest": {
                "indicators": ["jest.config.js", "jest.config.json", "package.json"],
                "command": ["npm", "test", "--", "--json", "--outputFile={output}"],
                "config_files": ["jest.config.js", "jest.config.json"],
            },
            "mocha": {
                "indicators": ["mocha.opts", ".mocharc.js", ".mocharc.json"],
                "command": [
                    "npm",
                    "test",
                    "--",
                    "--reporter",
                    "json",
                    "--reporter-options",
                    "output={output}",
                ],
                "config_files": ["mocha.opts", ".mocharc.js", ".mocharc.json"],
            },
            "jasmine": {
                "indicators": ["jasmine.json", "spec/"],
                "command": ["npm", "test"],
                "config_files": ["jasmine.json"],
            },
            "vitest": {
                "indicators": ["vitest.config.js", "vitest.config.ts"],
                "command": ["npm", "test", "--", "--reporter=json", "--outputFile={output}"],
                "config_files": ["vitest.config.js", "vitest.config.ts"],
            },
        },
        "typescript": {
            "jest": {
                "indicators": ["jest.config.ts", "tsconfig.json"],
                "command": ["npm", "test", "--", "--json", "--outputFile={output}"],
                "config_files": ["jest.config.ts"],
            },
            "vitest": {
                "indicators": ["vitest.config.ts"],
                "command": ["npm", "test", "--", "--reporter=json", "--outputFile={output}"],
                "config_files": ["vitest.config.ts"],
            },
        },
        "java": {
            "junit": {
                "indicators": ["pom.xml", "build.gradle", "src/test/java/"],
                "command": ["mvn", "test", "-Dmaven.test.failure.ignore=true"],
                "config_files": ["pom.xml"],
            },
            "gradle": {
                "indicators": ["build.gradle", "build.gradle.kts"],
                "command": ["gradle", "test", "--continue"],
                "config_files": ["build.gradle", "build.gradle.kts"],
            },
            "testng": {
                "indicators": ["testng.xml"],
                "command": ["mvn", "test", "-Dtestng.dtd.http=true"],
                "config_files": ["testng.xml"],
            },
        },
        "csharp": {
            "nunit": {
                "indicators": ["*.csproj", "nunit.framework"],
                "command": ["dotnet", "test", "--logger:trx"],
                "config_files": ["*.csproj"],
            },
            "xunit": {
                "indicators": ["xunit.runner.json"],
                "command": ["dotnet", "test", "--logger:trx"],
                "config_files": ["xunit.runner.json"],
            },
            "mstest": {
                "indicators": ["*.testsettings"],
                "command": ["dotnet", "test", "--logger:trx"],
                "config_files": ["*.testsettings"],
            },
        },
        "go": {
            "gotest": {
                "indicators": ["*_test.go", "go.mod"],
                "command": ["go", "test", "-json", "./..."],
                "config_files": ["go.mod"],
            },
            "ginkgo": {
                "indicators": ["*_suite_test.go"],
                "command": ["ginkgo", "-r", "--json-report=report.json"],
                "config_files": [],
            },
        },
        "rust": {
            "cargo": {
                "indicators": ["Cargo.toml", "tests/"],
                "command": ["cargo", "test", "--", "--format=json"],
                "config_files": ["Cargo.toml"],
            }
        },
        "ruby": {
            "rspec": {
                "indicators": ["spec/", ".rspec", "spec_helper.rb"],
                "command": ["rspec", "--format", "json", "--out", "{output}"],
                "config_files": [".rspec"],
            },
            "minitest": {
                "indicators": ["test/", "test_helper.rb"],
                "command": ["rake", "test"],
                "config_files": ["Rakefile"],
            },
        },
        "php": {
            "phpunit": {
                "indicators": ["phpunit.xml", "phpunit.xml.dist"],
                "command": ["phpunit", "--log-junit", "{output}"],
                "config_files": ["phpunit.xml", "phpunit.xml.dist"],
            },
            "pest": {
                "indicators": ["pest.php"],
                "command": ["pest", "--compact"],
                "config_files": [],
            },
        },
        "cpp": {
            "gtest": {
                "indicators": ["CMakeLists.txt", "test/", "tests/"],
                "command": ["ctest", "--output-on-failure", "-T", "Test"],
                "config_files": ["CMakeLists.txt"],
            },
            "catch2": {
                "indicators": ["catch.hpp", "catch2/"],
                "command": ["./test_executable", "-r", "json"],
                "config_files": [],
            },
        },
        "swift": {
            "xctest": {
                "indicators": ["Package.swift", "Tests/"],
                "command": ["swift", "test"],
                "config_files": ["Package.swift"],
            }
        },
        "kotlin": {
            "junit": {
                "indicators": ["build.gradle.kts", "src/test/kotlin/"],
                "command": ["gradle", "test"],
                "config_files": ["build.gradle.kts"],
            }
        },
        "scala": {
            "scalatest": {
                "indicators": ["build.sbt", "src/test/scala/"],
                "command": ["sbt", "test"],
                "config_files": ["build.sbt"],
            }
        },
    }

    def __init__(self, repo_path: str):
        """Initialize the UniversalTestRunner.

        Args:
            repo_path: Path to the repository to analyze.
        """
        self.repo_path = Path(repo_path)
        self.results: Dict[str, Dict[str, Any]] = {
            "discovered_frameworks": {},
            "test_results": {},
            "coverage": {},
            "summary": {},
        }

    def run_tests(self) -> Dict[str, Any]:
        """Discover and run all tests in the repository."""
        # Discover test frameworks
        frameworks = self._discover_test_frameworks()
        self.results["discovered_frameworks"] = frameworks

        # Run tests for each discovered framework
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0

        for language, framework_info in frameworks.items():
            for framework, info in framework_info.items():
                if info["detected"]:
                    test_result = self._run_framework_tests(language, framework, info)

                    if test_result:
                        self.results["test_results"][f"{language}_{framework}"] = test_result

                        # Update totals
                        if "summary" in test_result:
                            total_tests += test_result["summary"].get("total", 0)
                            total_passed += test_result["summary"].get("passed", 0)
                            total_failed += test_result["summary"].get("failed", 0)
                            total_skipped += test_result["summary"].get("skipped", 0)

        # Check for coverage tools
        self._check_coverage()

        # Generate summary
        self.results["summary"] = {
            "total_tests": total_tests,
            "passed": total_passed,
            "failed": total_failed,
            "skipped": total_skipped,
            "success_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
            "frameworks_used": [
                f"{lang}_{fw}"
                for lang, fws in frameworks.items()
                for fw, info in fws.items()
                if info["detected"]
            ],
        }

        return self.results

    def _discover_test_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Discover which test frameworks are present in the repository."""
        discovered: Dict[str, Dict[str, Any]] = {}

        for language, frameworks in self.TEST_FRAMEWORKS.items():
            discovered[language] = {}

            if isinstance(frameworks, dict):
                for framework, config in frameworks.items():
                    detected = False
                    detected_files = []

                    # Check for indicator files
                    for indicator in config["indicators"]:
                        if "*" in indicator:
                            # Handle glob patterns
                            matches = list(self.repo_path.rglob(indicator))
                            if matches:
                                detected = True
                                detected_files.extend(
                                    [str(m.relative_to(self.repo_path)) for m in matches[:5]]
                                )
                        else:
                            # Check for specific files
                            if (self.repo_path / indicator).exists():
                                detected = True
                                detected_files.append(indicator)

                    # Additional checks for package.json
                    if (
                        language in ["javascript", "typescript"]
                        and (self.repo_path / "package.json").exists()
                    ):
                        try:
                            with open(self.repo_path / "package.json", "r") as f:
                                package_json = json.load(f)

                            # Check devDependencies and dependencies
                            deps = {
                                **package_json.get("devDependencies", {}),
                                **package_json.get("dependencies", {}),
                            }

                            if framework in deps or f"@types/{framework}" in deps:
                                detected = True
                                detected_files.append("package.json")
                        except (OSError, json.JSONDecodeError):
                            pass

                    discovered[language][framework] = {
                        "detected": detected,
                        "files": detected_files,
                        "command": config["command"],
                        "config_files": config["config_files"],
                    }

        return discovered

    def _run_framework_tests(
        self, language: str, framework: str, info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Run tests for a specific framework."""
        try:
            # Prepare output file for results
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as output_file:
                output_path = output_file.name

            # Prepare command
            command = info["command"].copy()
            command = [arg.replace("{output}", output_path) for arg in command]

            # Special handling for different frameworks
            result = self._execute_test_command(language, framework, command)

            # Parse results based on framework
            test_results = self._parse_test_results(language, framework, result, output_path)

            # Clean up
            try:
                os.unlink(output_path)
            except OSError:
                pass

            return test_results

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "framework": framework,
                "language": language,
            }

    def _execute_test_command(
        self, language: str, framework: str, command: List[str]
    ) -> subprocess.CompletedProcess:
        """Execute test command with proper environment setup."""
        env = os.environ.copy()

        # Language-specific environment setup
        if language == "python":
            # Ensure Python path includes current directory
            env["PYTHONPATH"] = str(self.repo_path) + os.pathsep + env.get("PYTHONPATH", "")

        elif language in ["javascript", "typescript"]:
            # Check if node_modules exists
            if not (self.repo_path / "node_modules").exists():
                # Try to install dependencies first
                subprocess.run(["npm", "install"], cwd=str(self.repo_path), capture_output=True)

        elif language == "java":
            # Set JAVA_HOME if not set
            if "JAVA_HOME" not in env:
                java_home = self._find_java_home()
                if java_home:
                    env["JAVA_HOME"] = java_home

        # Run the test command
        result = subprocess.run(
            command,
            cwd=str(self.repo_path),
            capture_output=True,
            text=True,
            env=env,
            timeout=300,  # 5 minute timeout
        )

        return result

    def _parse_test_results(
        self, language: str, framework: str, result: subprocess.CompletedProcess, output_path: str
    ) -> Dict[str, Any]:
        """Parse test results based on framework output format."""
        test_data: Dict[str, Any] = {
            "framework": framework,
            "language": language,
            "exit_code": result.returncode,
            "stdout": result.stdout[-5000:]
            if len(result.stdout) > 5000
            else result.stdout,  # Limit output
            "stderr": result.stderr[-5000:] if len(result.stderr) > 5000 else result.stderr,
        }

        # Try to parse structured output
        if os.path.exists(output_path):
            try:
                with open(output_path, "r") as f:
                    structured_results = json.load(f)
                test_data["structured_results"] = structured_results
                test_data["summary"] = self._extract_summary(structured_results, framework)
            except (OSError, json.JSONDecodeError):
                # Fall back to parsing stdout
                test_data["summary"] = self._parse_stdout_results(result.stdout, framework)
        else:
            # Parse stdout for results
            test_data["summary"] = self._parse_stdout_results(result.stdout, framework)

        # Check for XML results (JUnit format)
        xml_files = list(self.repo_path.rglob("**/TEST-*.xml")) + list(
            self.repo_path.rglob("**/test-results/*.xml")
        )
        if xml_files:
            test_data["junit_results"] = self._parse_junit_xml(xml_files[0])

        return test_data

    def _extract_summary(self, results: Any, framework: str) -> Dict[str, int]:
        """Extract test summary from structured results."""
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

        # Framework-specific parsing
        if framework == "pytest":
            if "summary" in results:
                summary["total"] = results["summary"].get("total", 0)
                summary["passed"] = results["summary"].get("passed", 0)
                summary["failed"] = results["summary"].get("failed", 0)
                summary["skipped"] = results["summary"].get("skipped", 0)

        elif framework == "jest":
            if "numTotalTests" in results:
                summary["total"] = results.get("numTotalTests", 0)
                summary["passed"] = results.get("numPassedTests", 0)
                summary["failed"] = results.get("numFailedTests", 0)
                summary["skipped"] = results.get("numPendingTests", 0)

        elif framework == "gotest":
            # Parse Go test JSON output
            if isinstance(results, list):
                for event in results:
                    if event.get("Action") == "pass":
                        summary["passed"] += 1
                    elif event.get("Action") == "fail":
                        summary["failed"] += 1
                summary["total"] = summary["passed"] + summary["failed"]

        return summary

    def _parse_stdout_results(self, stdout: str, framework: str) -> Dict[str, int]:
        """Parse test results from stdout when structured output is not available."""
        summary = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

        # Common patterns
        patterns = {
            "pytest": [r"(\d+) passed", r"(\d+) failed", r"(\d+) skipped", r"(\d+) error"],
            "jest": [
                r"Tests:\s+(\d+) passed",
                r"Tests:\s+(\d+) failed",
                r"Tests:\s+(\d+) skipped",
                r"Tests:\s+(\d+) total",
            ],
            "mocha": [r"(\d+) passing", r"(\d+) failing", r"(\d+) pending"],
            "gotest": [r"PASS:\s+(\d+)", r"FAIL:\s+(\d+)", r"ok\s+\S+\s+[\d.]+s"],
            "cargo": [r"test result: ok. (\d+) passed", r"(\d+) failed", r"(\d+) ignored"],
        }

        # Apply patterns
        if framework in patterns:
            for pattern in patterns[framework]:
                matches = re.findall(pattern, stdout, re.MULTILINE | re.IGNORECASE)
                if matches:
                    # Update summary based on pattern
                    if "passed" in pattern or "passing" in pattern:
                        summary["passed"] = int(matches[0]) if matches else 0
                    elif "failed" in pattern or "failing" in pattern:
                        summary["failed"] = int(matches[0]) if matches else 0
                    elif "skipped" in pattern or "pending" in pattern or "ignored" in pattern:
                        summary["skipped"] = int(matches[0]) if matches else 0
                    elif "total" in pattern:
                        summary["total"] = int(matches[0]) if matches else 0

        # Calculate total if not found
        if summary["total"] == 0:
            summary["total"] = summary["passed"] + summary["failed"] + summary["skipped"]

        return summary

    def _parse_junit_xml(self, xml_path: Path) -> Dict[str, Any]:
        """Parse JUnit XML test results."""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            # Handle both testsuite and testsuites root
            if root.tag == "testsuites":
                testsuites = root.findall("testsuite")
            else:
                testsuites = [root]

            results: Dict[str, Any] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "errors": 0,
                "time": 0.0,
                "suites": [],
            }

            for testsuite in testsuites:
                suite_data = {
                    "name": testsuite.get("name", "Unknown"),
                    "tests": int(testsuite.get("tests", 0)),
                    "failures": int(testsuite.get("failures", 0)),
                    "errors": int(testsuite.get("errors", 0)),
                    "skipped": int(testsuite.get("skipped", 0)),
                    "time": float(testsuite.get("time", 0)),
                }

                results["total"] += suite_data["tests"]
                results["failed"] += suite_data["failures"]
                results["errors"] += suite_data["errors"]
                results["skipped"] += suite_data["skipped"]
                results["time"] += suite_data["time"]

                results["suites"].append(suite_data)

            results["passed"] = (
                results["total"] - results["failed"] - results["errors"] - results["skipped"]
            )

            return results

        except (OSError, ET.ParseError) as e:
            return {"error": str(e)}

    def _check_coverage(self) -> None:
        """Check for code coverage tools and results."""
        coverage_tools: Dict[str, List[str]] = {
            "python": ["coverage.xml", ".coverage", "htmlcov/"],
            "javascript": ["coverage/", "lcov.info", "coverage-final.json"],
            "java": ["target/site/jacoco/", "build/reports/jacoco/"],
            "go": ["coverage.out", "coverage.html"],
            "csharp": ["TestResults/*/coverage.cobertura.xml"],
            "rust": ["tarpaulin-report.xml", "lcov.info"],
        }

        for language, patterns in coverage_tools.items():
            for pattern in patterns:
                matches = list(self.repo_path.rglob(pattern))
                if matches:
                    if language not in self.results["coverage"]:
                        self.results["coverage"][language] = []

                    self.results["coverage"][language].extend(
                        [str(m.relative_to(self.repo_path)) for m in matches[:5]]
                    )

    def _find_java_home(self) -> Optional[str]:
        """Try to find JAVA_HOME."""
        # Common locations
        common_paths = [
            "/usr/lib/jvm/default-java",
            "/usr/lib/jvm/java-11-openjdk-amd64",
            "/usr/lib/jvm/java-8-openjdk-amd64",
            "/Library/Java/JavaVirtualMachines/*/Contents/Home",
        ]

        for path in common_paths:
            if Path(path).exists():
                return path

        # Try using which
        try:
            result = subprocess.run(["which", "java"], capture_output=True, text=True)
            if result.returncode == 0:
                java_path = Path(result.stdout.strip())
                # Navigate up to find JAVA_HOME
                return str(java_path.parent.parent)
        except subprocess.SubprocessError:
            pass

        return None
