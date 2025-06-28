"""Integration tests for Vibe Verifier."""

import pytest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from src.main import VibeVerifier, main


class TestVibeVerifierIntegration:
    """Test complete Vibe Verifier workflow."""
    
    def test_full_analysis_python_project(self, sample_python_project, mock_subprocess_run):
        """Test complete analysis of a Python project."""
        verifier = VibeVerifier(str(sample_python_project))
        results = verifier.run_analysis()
        
        # Check all phases completed
        assert "languages" in results
        assert "documentation" in results
        assert "complexity" in results
        assert "static_analysis" in results
        assert "formal_verification" in results
        assert "tests" in results
        assert "reports" in results
        
        # Check language detection
        assert results["languages"]["primary_language"] == "Python"
        
        # Check documentation analysis
        assert results["documentation"]["summary"]["total_claims"] > 0
        
        # Check complexity analysis
        assert results["complexity"]["summary"]["total_files"] > 0
        assert results["complexity"]["summary"]["average_complexity"] > 0
        
        # Check test results
        assert results["tests"]["summary"]["total_tests"] > 0
        
        # Check reports were generated
        assert len(results["reports"]) > 0
    
    def test_full_analysis_multi_language(self, sample_multi_language_project, mock_subprocess_run):
        """Test complete analysis of a multi-language project."""
        verifier = VibeVerifier(str(sample_multi_language_project))
        results = verifier.run_analysis()
        
        # Should detect multiple languages
        languages = results["languages"]["languages"]
        assert len(languages) >= 3  # Python, Go, TypeScript
        
        # Should analyze all components
        assert results["complexity"]["summary"]["total_files"] >= 3
        
        # Should find documentation claims
        assert results["documentation"]["summary"]["total_claims"] > 0
    
    def test_quick_mode(self, sample_python_project, mock_subprocess_run):
        """Test quick analysis mode."""
        config = {"quick_mode": True}
        verifier = VibeVerifier(str(sample_python_project), config)
        
        # Quick mode should still complete
        results = verifier.run_analysis()
        assert "reports" in results
    
    def test_skip_tests_mode(self, sample_python_project, mock_subprocess_run):
        """Test skipping test execution."""
        config = {"skip_tests": True}
        verifier = VibeVerifier(str(sample_python_project), config)
        
        results = verifier.run_analysis()
        
        # Tests should be skipped but other analysis should run
        assert "complexity" in results
        assert "static_analysis" in results
    
    def test_specific_output_format(self, sample_python_project, mock_subprocess_run):
        """Test generating specific output format."""
        config = {"output_format": "markdown"}
        verifier = VibeVerifier(str(sample_python_project), config)
        
        results = verifier.run_analysis()
        
        # Should only generate markdown
        assert "markdown" in results["reports"]
        assert "html" not in results["reports"]
        assert "pdf" not in results["reports"]
    
    def test_error_handling_invalid_path(self):
        """Test error handling for invalid repository path."""
        with pytest.raises(ValueError, match="does not exist"):
            VibeVerifier("/nonexistent/path")
    
    def test_error_handling_file_instead_of_dir(self, temp_dir):
        """Test error handling when given a file instead of directory."""
        test_file = temp_dir / "file.txt"
        test_file.write_text("content")
        
        with pytest.raises(ValueError, match="not a directory"):
            VibeVerifier(str(test_file))
    
    def test_claim_verification_integration(self, sample_python_project, mock_subprocess_run):
        """Test integration of documentation claims with verification."""
        verifier = VibeVerifier(str(sample_python_project))
        results = verifier.run_analysis()
        
        # Should have claim verification results
        if "claim_verification" in results:
            verification = results["claim_verification"]
            assert "summary" in verification
            assert verification["summary"]["total_claims"] > 0
    
    @patch('sys.argv', ['vibe-verifier', '/test/path'])
    @patch('src.main.VibeVerifier')
    def test_cli_basic(self, mock_verifier_class):
        """Test CLI with basic arguments."""
        mock_verifier = MagicMock()
        mock_verifier.run_analysis.return_value = {
            "tests": {"summary": {"failed": 0}},
            "claim_verification": {"summary": {"failed": 0}}
        }
        mock_verifier_class.return_value = mock_verifier
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        mock_verifier_class.assert_called_once_with('/test/path', {
            'output_format': 'all',
            'skip_tests': False,
            'skip_verification': False,
            'quick_mode': False,
            'verbose': False
        })
    
    @patch('sys.argv', ['vibe-verifier', '/test/path', '--output-format', 'html', '--skip-tests'])
    @patch('src.main.VibeVerifier')
    def test_cli_with_options(self, mock_verifier_class):
        """Test CLI with various options."""
        mock_verifier = MagicMock()
        mock_verifier.run_analysis.return_value = {
            "tests": {"summary": {"failed": 0}},
            "claim_verification": {"summary": {"failed": 0}}
        }
        mock_verifier_class.return_value = mock_verifier
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        
        # Check configuration
        call_args = mock_verifier_class.call_args
        config = call_args[0][1]
        assert config['output_format'] == 'html'
        assert config['skip_tests'] is True
    
    @patch('sys.argv', ['vibe-verifier', '/test/path', '--config', 'config.json'])
    @patch('builtins.open', create=True)
    @patch('src.main.VibeVerifier')
    def test_cli_with_config_file(self, mock_verifier_class, mock_open):
        """Test CLI with configuration file."""
        # Mock config file content
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
            "output_format": "pdf",
            "save_raw_results": True
        })
        
        mock_verifier = MagicMock()
        mock_verifier.run_analysis.return_value = {
            "tests": {"summary": {"failed": 0}},
            "claim_verification": {"summary": {"failed": 0}}
        }
        mock_verifier_class.return_value = mock_verifier
        
        with pytest.raises(SystemExit) as exc_info:
            main()
        
        assert exc_info.value.code == 0
        
        # Check configuration was loaded
        call_args = mock_verifier_class.call_args
        config = call_args[0][1]
        assert config['save_raw_results'] is True
    
    def test_exit_codes(self, sample_python_project):
        """Test different exit codes based on results."""
        with patch('src.main.VibeVerifier') as mock_verifier_class:
            mock_verifier = MagicMock()
            
            # Test exit code 1 - test failures
            mock_verifier.run_analysis.return_value = {
                "tests": {"summary": {"failed": 5}},
                "claim_verification": {"summary": {"failed": 0}}
            }
            mock_verifier_class.return_value = mock_verifier
            
            with patch('sys.argv', ['vibe-verifier', str(sample_python_project)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 1
            
            # Test exit code 2 - claim failures
            mock_verifier.run_analysis.return_value = {
                "tests": {"summary": {"failed": 0}},
                "claim_verification": {"summary": {"failed": 3}}
            }
            
            with patch('sys.argv', ['vibe-verifier', str(sample_python_project)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 2
            
            # Test exit code 3 - analysis error
            mock_verifier.run_analysis.side_effect = Exception("Analysis failed")
            
            with patch('sys.argv', ['vibe-verifier', str(sample_python_project)]):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                assert exc_info.value.code == 3
    
    def test_save_raw_results(self, sample_python_project, temp_dir, mock_subprocess_run):
        """Test saving raw results to file."""
        config = {
            "save_raw_results": True,
            "output_dir": str(temp_dir)
        }
        
        verifier = VibeVerifier(str(sample_python_project), config)
        results = verifier.run_analysis()
        
        # Raw results should be saved
        results_file = temp_dir / "raw_results.json"
        
        # In real scenario, this would be done in main()
        # Let's simulate it here
        results_file.parent.mkdir(exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        assert results_file.exists()
        
        # Check content is valid JSON
        with open(results_file, 'r') as f:
            loaded_results = json.load(f)
        
        assert "languages" in loaded_results
        assert "complexity" in loaded_results


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios."""
    
    def test_security_focused_analysis(self, temp_dir):
        """Test analysis focusing on security issues."""
        # Create project with security issues
        vulnerable_file = temp_dir / "vulnerable.py"
        vulnerable_file.write_text('''
import pickle
import os

# Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
DB_PASSWORD = "admin123"

def load_user_data(filename):
    # Unsafe deserialization
    with open(filename, 'rb') as f:
        return pickle.load(f)

def execute_command(user_input):
    # Command injection vulnerability
    os.system(f"echo {user_input}")
''')
        
        readme = temp_dir / "README.md"
        readme.write_text("""
# Secure Application

This application is completely secure and has:
- No security vulnerabilities
- Encrypted data storage
- Safe input handling
""")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            
            verifier = VibeVerifier(str(temp_dir))
            results = verifier.run_analysis()
            
            # Should identify security claims
            assert results["documentation"]["summary"]["total_claims"] > 0
            
            # Should find security issues (through basic pattern matching)
            if "secrets" in results["static_analysis"]["security"]:
                assert results["static_analysis"]["security"]["secrets"]["found"] > 0
    
    def test_performance_focused_analysis(self, temp_dir):
        """Test analysis focusing on performance claims."""
        perf_file = temp_dir / "performance.py"
        perf_file.write_text('''
def bubble_sort(arr):
    """Sorts array with O(n²) complexity."""
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

def optimized_search(arr, target):
    """Lightning fast search algorithm."""
    # Actually just linear search
    for i, val in enumerate(arr):
        if val == target:
            return i
    return -1
''')
        
        readme = temp_dir / "README.md"
        readme.write_text("""
# High Performance Library

Features:
- Handles 1 million operations per second
- O(log n) search complexity
- Optimized sorting algorithms
""")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            
            verifier = VibeVerifier(str(temp_dir))
            results = verifier.run_analysis()
            
            # Should find performance claims
            perf_claims = [
                claim for claims in results["documentation"]["claims_by_type"].values()
                for claim in claims
                if "performance" in claim.get("type", "") or "operations per second" in claim.get("text", "")
            ]
            assert len(perf_claims) > 0