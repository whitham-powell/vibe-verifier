"""Tests for universal test runner module."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET

from src.testers.test_runner import UniversalTestRunner


class TestUniversalTestRunner:
    """Test universal test runner functionality."""
    
    def test_discover_python_frameworks(self, sample_python_project):
        """Test discovery of Python test frameworks."""
        runner = UniversalTestRunner(str(sample_python_project))
        frameworks = runner._discover_test_frameworks()
        
        # Should discover pytest
        assert "python" in frameworks
        assert "pytest" in frameworks["python"]
        assert frameworks["python"]["pytest"]["detected"] is True
        
        # Should find test files
        assert len(frameworks["python"]["pytest"]["files"]) > 0
        assert any("test_main.py" in f for f in frameworks["python"]["pytest"]["files"])
    
    def test_discover_javascript_frameworks(self, sample_javascript_project):
        """Test discovery of JavaScript test frameworks."""
        runner = UniversalTestRunner(str(sample_javascript_project))
        frameworks = runner._discover_test_frameworks()
        
        # Should discover jest
        assert "javascript" in frameworks
        assert "jest" in frameworks["javascript"]
        assert frameworks["javascript"]["jest"]["detected"] is True
        
        # Should find package.json
        assert any("package.json" in f for f in frameworks["javascript"]["jest"]["files"])
    
    def test_discover_multi_language_frameworks(self, sample_multi_language_project):
        """Test discovery in multi-language project."""
        runner = UniversalTestRunner(str(sample_multi_language_project))
        frameworks = runner._discover_test_frameworks()
        
        # Should find multiple language test setups
        detected_languages = []
        for lang, fw_dict in frameworks.items():
            for fw, info in fw_dict.items():
                if info["detected"]:
                    detected_languages.append(lang)
                    break
        
        assert "go" in detected_languages  # Has test files
    
    @patch('subprocess.run')
    def test_run_pytest(self, mock_run, sample_python_project):
        """Test running pytest."""
        # Mock pytest JSON output
        mock_run.return_value = MagicMock(
            stdout=json.dumps({
                "summary": {
                    "total": 3,
                    "passed": 3,
                    "failed": 0,
                    "skipped": 0
                }
            }),
            stderr="",
            returncode=0
        )
        
        runner = UniversalTestRunner(str(sample_python_project))
        result = runner.run_tests()
        
        # Check summary
        assert result["summary"]["total_tests"] == 3
        assert result["summary"]["passed"] == 3
        assert result["summary"]["failed"] == 0
        assert result["summary"]["success_rate"] == 100.0
    
    @patch('subprocess.run')
    def test_run_jest(self, mock_run, sample_javascript_project):
        """Test running Jest tests."""
        # Mock Jest output
        mock_run.return_value = MagicMock(
            stdout=json.dumps({
                "numTotalTests": 3,
                "numPassedTests": 2,
                "numFailedTests": 1,
                "numPendingTests": 0
            }),
            stderr="",
            returncode=1
        )
        
        runner = UniversalTestRunner(str(sample_javascript_project))
        result = runner.run_tests()
        
        # Check results
        assert result["summary"]["total_tests"] == 3
        assert result["summary"]["passed"] == 2
        assert result["summary"]["failed"] == 1
        assert result["summary"]["success_rate"] == pytest.approx(66.67, rel=0.01)
    
    @patch('subprocess.run')
    def test_run_go_tests(self, mock_run, sample_multi_language_project):
        """Test running Go tests."""
        # Mock go test output
        mock_run.return_value = MagicMock(
            stdout="PASS\nok\texample.com/multiproject\t0.123s\n2 passed",
            stderr="",
            returncode=0
        )
        
        runner = UniversalTestRunner(str(sample_multi_language_project))
        result = runner.run_tests()
        
        # Should process Go test results
        assert result["summary"]["total_tests"] > 0
    
    def test_parse_stdout_results(self, temp_dir):
        """Test parsing test results from stdout."""
        runner = UniversalTestRunner(str(temp_dir))
        
        # Test pytest output parsing
        pytest_output = """
============ test session starts ============
collected 10 items

test_module.py::test_one PASSED
test_module.py::test_two PASSED
test_module.py::test_three FAILED

============ 2 passed, 1 failed in 0.5s ============
"""
        
        summary = runner._parse_stdout_results(pytest_output, "pytest")
        assert summary["passed"] == 2
        assert summary["failed"] == 1
        
        # Test Jest output parsing
        jest_output = """
Test Suites: 2 passed, 2 total
Tests:       5 passed, 5 total
Snapshots:   0 total
Time:        3.456s
"""
        
        summary = runner._parse_stdout_results(jest_output, "jest")
        assert summary["passed"] == 5
        assert summary["total"] == 5
        
        # Test go test output parsing
        go_output = """
--- PASS: TestFunction1 (0.00s)
--- PASS: TestFunction2 (0.01s)
--- FAIL: TestFunction3 (0.00s)
FAIL
exit status 1
FAIL\texample.com/package\t0.123s
"""
        
        summary = runner._parse_stdout_results(go_output, "gotest")
        assert summary["passed"] == 2
        assert summary["failed"] == 1
    
    def test_parse_junit_xml(self, temp_dir):
        """Test parsing JUnit XML results."""
        # Create sample JUnit XML
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="TestSuite" tests="4" failures="1" errors="0" skipped="1" time="2.5">
    <testcase name="test1" classname="TestClass" time="0.5"/>
    <testcase name="test2" classname="TestClass" time="0.3">
        <failure message="AssertionError">Expected true but was false</failure>
    </testcase>
    <testcase name="test3" classname="TestClass" time="0.1">
        <skipped message="Not implemented yet"/>
    </testcase>
    <testcase name="test4" classname="TestClass" time="1.6"/>
</testsuite>'''
        
        xml_file = temp_dir / "test-results.xml"
        xml_file.write_text(xml_content)
        
        runner = UniversalTestRunner(str(temp_dir))
        result = runner._parse_junit_xml(xml_file)
        
        assert result["total"] == 4
        assert result["passed"] == 2
        assert result["failed"] == 1
        assert result["skipped"] == 1
        assert result["time"] == 2.5
    
    def test_coverage_detection(self, temp_dir):
        """Test detection of coverage files."""
        # Create coverage files
        (temp_dir / "coverage.xml").touch()
        (temp_dir / ".coverage").touch()
        coverage_dir = temp_dir / "htmlcov"
        coverage_dir.mkdir()
        
        runner = UniversalTestRunner(str(temp_dir))
        runner._check_coverage()
        
        assert "python" in runner.results["coverage"]
        assert len(runner.results["coverage"]["python"]) >= 2
    
    @patch('subprocess.run')
    def test_framework_not_found(self, mock_run, temp_dir):
        """Test handling when no test framework is found."""
        mock_run.return_value = MagicMock(
            stdout="",
            stderr="command not found",
            returncode=127
        )
        
        runner = UniversalTestRunner(str(temp_dir))
        result = runner.run_tests()
        
        assert result["summary"]["total_tests"] == 0
        assert result["summary"]["success_rate"] == 0
    
    @patch('subprocess.run')
    def test_test_execution_timeout(self, mock_run, temp_dir):
        """Test handling of test execution timeout."""
        import subprocess
        
        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=300)
        
        runner = UniversalTestRunner(str(temp_dir))
        # Create a fake framework detection
        runner.results["discovered_frameworks"] = {
            "python": {"pytest": {"detected": True, "command": ["pytest"]}}
        }
        
        result = runner.run_tests()
        
        # Should handle timeout gracefully
        assert "test_results" in result
    
    def test_extract_summary_different_frameworks(self, temp_dir):
        """Test summary extraction for different test frameworks."""
        runner = UniversalTestRunner(str(temp_dir))
        
        # Test pytest summary extraction
        pytest_results = {
            "summary": {
                "total": 10,
                "passed": 8,
                "failed": 1,
                "skipped": 1
            }
        }
        
        summary = runner._extract_summary(pytest_results, "pytest")
        assert summary["total"] == 10
        assert summary["passed"] == 8
        
        # Test jest summary extraction
        jest_results = {
            "numTotalTests": 20,
            "numPassedTests": 18,
            "numFailedTests": 2,
            "numPendingTests": 0
        }
        
        summary = runner._extract_summary(jest_results, "jest")
        assert summary["total"] == 20
        assert summary["passed"] == 18
        assert summary["failed"] == 2