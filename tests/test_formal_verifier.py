"""Tests for formal verifier module."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.verifiers.formal_verifier import FormalVerifier


class TestFormalVerifier:
    """Test formal verification functionality."""
    
    def test_detect_verification_targets(self, sample_multi_language_project):
        """Test detection of verification targets."""
        verifier = FormalVerifier(str(sample_multi_language_project))
        verifier._detect_verification_targets()
        
        targets = verifier.verification_targets
        
        # Should detect languages
        assert "rust" in targets
        assert "c_cpp" in targets
        assert "java" in targets
        assert "python" in targets
        assert "go" in targets
        
        # Should detect files
        assert targets["python"]["files"] is True
        assert targets["go"]["files"] is True
    
    @patch('shutil.which')
    def test_check_tool_availability(self, mock_which, temp_dir):
        """Test checking for available verification tools."""
        # Mock tool availability
        def which_side_effect(tool):
            available_tools = ["prusti", "cbmc", "mypy", "gosec"]
            return f"/usr/bin/{tool}" if tool in available_tools else None
        
        mock_which.side_effect = which_side_effect
        
        verifier = FormalVerifier(str(temp_dir))
        
        # Check Rust tools
        rust_tools = verifier._check_rust_verification()
        assert rust_tools["prusti"] is True
        assert rust_tools["kani"] is False
        
        # Check C/C++ tools
        c_tools = verifier._check_c_cpp_verification()
        assert c_tools["cbmc"] is True
        assert c_tools["frama_c"] is False
    
    def test_verify_empty_project(self, temp_dir):
        """Test verification on empty project."""
        verifier = FormalVerifier(str(temp_dir))
        result = verifier.verify()
        
        # Should return empty results for empty project
        assert "contracts" in result
        assert "assertions" in result
        assert "properties" in result
        assert "proofs" in result
        assert "smt_checks" in result
    
    @patch('subprocess.run')
    def test_verify_rust_project(self, mock_run, temp_dir):
        """Test Rust verification."""
        # Create a Rust file
        rust_file = temp_dir / "main.rs"
        rust_file.write_text('''
fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_add() {
        assert_eq!(add(2, 3), 5);
    }
}
''')
        
        # Mock subprocess results
        mock_run.return_value = MagicMock(
            stdout="VERIFICATION SUCCESSFUL",
            stderr="",
            returncode=0
        )
        
        verifier = FormalVerifier(str(temp_dir))
        verifier.verification_targets = {
            "rust": {"prusti": True, "files": True}
        }
        
        verifier._verify_rust()
        
        # Check that Rust verification was attempted
        assert mock_run.called
    
    @patch('subprocess.run')
    def test_verify_c_project(self, mock_run, temp_dir):
        """Test C/C++ verification."""
        # Create a C file
        c_file = temp_dir / "main.c"
        c_file.write_text('''
#include <assert.h>

int divide(int a, int b) {
    assert(b != 0);
    return a / b;
}
''')
        
        # Mock CBMC output
        mock_run.return_value = MagicMock(
            stdout="VERIFICATION FAILED\nassertion at line 5",
            stderr="",
            returncode=1
        )
        
        verifier = FormalVerifier(str(temp_dir))
        verifier.verification_targets = {
            "c_cpp": {"cbmc": True, "files": True}
        }
        
        verifier._verify_c_cpp()
        
        assert mock_run.called
    
    def test_parse_cbmc_output(self, temp_dir):
        """Test parsing CBMC output."""
        verifier = FormalVerifier(str(temp_dir))
        
        output = """
CBMC version 5.12
Parsing main.c
VERIFICATION FAILED
assertion at line 10: FAILURE
division by zero at line 15: FAILURE
"""
        
        issues = verifier._parse_cbmc_output(output)
        
        assert len(issues) == 2
        assert any("assertion" in issue["type"] for issue in issues)
        assert any("line 10" in issue["line"] for issue in issues)
    
    def test_parse_frama_c_results(self, temp_dir):
        """Test parsing Frama-C results."""
        verifier = FormalVerifier(str(temp_dir))
        
        output = """
[wp] Proved: 5
[wp] Failed: 2
[wp] Total: 7
"""
        
        results = verifier._parse_frama_c_results(output)
        
        assert results["proved"] == 5
        assert results["total"] == 7
        assert results["percentage"] == pytest.approx(71.43, rel=0.01)
    
    @patch('subprocess.run')
    def test_verify_python_crosshair(self, mock_run, sample_python_project):
        """Test Python verification with CrossHair."""
        # Mock CrossHair output
        mock_run.return_value = MagicMock(
            stdout="""
Counterexample found for calculate_sum
  inputs: a=-9223372036854775808, b=-1
  expected: returns int
  actual: OverflowError
""",
            stderr="",
            returncode=1
        )
        
        verifier = FormalVerifier(str(sample_python_project))
        verifier.verification_targets = {
            "python": {"crosshair": True, "files": True}
        }
        
        verifier._verify_python()
        
        assert mock_run.called
    
    def test_parse_crosshair_output(self, temp_dir):
        """Test parsing CrossHair output."""
        verifier = FormalVerifier(str(temp_dir))
        
        output = """
Counterexample found for function1
  inputs: x=0, y=-1
  expected: returns positive
  actual: returns negative

Counterexample found for function2
  inputs: data=None
  expected: no exception
  actual: AttributeError
"""
        
        counterexamples = verifier._parse_crosshair_output(output)
        
        assert len(counterexamples) == 2
        assert counterexamples[0]["description"] == "Counterexample found for function1"
        assert len(counterexamples[0]["inputs"]) > 0
    
    @patch('subprocess.run')
    def test_verify_go_project(self, mock_run, sample_multi_language_project):
        """Test Go verification."""
        # Mock gosec output
        mock_run.return_value = MagicMock(
            stdout='{"Issues": [{"severity": "HIGH", "confidence": "HIGH", "details": "Weak crypto"}]}',
            stderr="",
            returncode=0
        )
        
        verifier = FormalVerifier(str(sample_multi_language_project))
        verifier.verification_targets = {
            "go": {"gosec": True, "files": True}
        }
        
        verifier._verify_go()
        
        assert mock_run.called
    
    def test_comprehensive_verification(self, sample_multi_language_project):
        """Test running verification on multi-language project."""
        with patch('subprocess.run') as mock_run:
            # Mock various tool outputs
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="",
                returncode=0
            )
            
            verifier = FormalVerifier(str(sample_multi_language_project))
            result = verifier.verify()
            
            # Should have results structure
            assert "contracts" in result
            assert "assertions" in result
            assert "properties" in result
            assert "proofs" in result
            assert "smt_checks" in result