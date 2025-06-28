"""Tests for static analyzer module."""

import ast

from src.verifiers.static_analyzer import ASTAnalyzer, StaticAnalyzer


class TestStaticAnalyzer:
    """Test static analysis functionality."""

    def test_analyze_python_project(self, sample_python_project, mock_subprocess_run):
        """Test static analysis of Python project."""
        analyzer = StaticAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Check structure
        assert "python" in result
        assert "security" in result
        assert "type_checking" in result
        assert "linting" in result

        # Check pylint results
        assert "pylint" in result["linting"]
        pylint_result = result["linting"]["pylint"]
        assert pylint_result["status"] == "completed"
        assert "messages" in pylint_result

        # Check mypy results
        assert "mypy" in result["type_checking"]
        mypy_result = result["type_checking"]["mypy"]
        assert mypy_result["status"] == "completed"
        assert mypy_result["total_issues"] > 0

        # Check bandit results
        assert "bandit" in result["security"]
        bandit_result = result["security"]["bandit"]
        assert bandit_result["status"] == "completed"
        assert "metrics" in bandit_result

    def test_ast_analysis(self, temp_dir):
        """Test custom AST analysis."""
        # Create test file with various issues
        test_file = temp_dir / "test_ast.py"
        test_file.write_text(
            '''
def function_with_too_many_args(a, b, c, d, e, f, g):
    """This function has too many arguments."""
    return a + b + c + d + e + f + g

def function_without_docstring():
    return 42

class ClassWithoutDocstring:
    def method(self):
        pass

def function_with_bare_except():
    try:
        risky_operation()
    except:  # bare except
        pass
'''
        )

        analyzer = StaticAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Check AST analysis results
        assert "ast_analysis" in result["python"]
        ast_result = result["python"]["ast_analysis"]
        assert ast_result["status"] == "completed"
        assert ast_result["total_issues"] > 0

        # Check for specific issues
        issues = ast_result["issues"]
        issue_types = [issue["type"] for issue in issues]

        assert "too_many_arguments" in issue_types
        assert "missing_docstring" in issue_types
        assert "bare_except" in issue_types

    def test_security_analysis(self, temp_dir, mock_subprocess_run):
        """Test security analysis features."""
        # Create file with potential security issues
        test_file = temp_dir / "security_test.py"
        test_file.write_text(
            """
import os

# Potential hardcoded secret
API_KEY = "sk-1234567890abcdef1234567890abcdef"
password = "admin123"

def unsafe_query(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query
"""
        )

        analyzer = StaticAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Check secrets detection
        assert "secrets" in result["security"]
        secrets_result = result["security"]["secrets"]
        assert secrets_result["status"] == "completed"
        assert secrets_result["found"] > 0

    def test_javascript_analysis(self, sample_javascript_project, mock_subprocess_run):
        """Test JavaScript static analysis."""
        analyzer = StaticAnalyzer(str(sample_javascript_project))
        result = analyzer.analyze()

        # Should run ESLint for JavaScript
        assert "eslint" in result["linting"]
        eslint_result = result["linting"]["eslint"]
        assert eslint_result["status"] == "completed"

    def test_multi_language_analysis(self, sample_multi_language_project, mock_subprocess_run):
        """Test analysis of multi-language project."""
        analyzer = StaticAnalyzer(str(sample_multi_language_project))
        result = analyzer.analyze()

        # Should analyze multiple languages
        assert len(result) > 0

        # Python analysis should be present
        if "ast_analysis" in result["python"]:
            assert result["python"]["ast_analysis"]["status"] == "completed"

    def test_dependency_checking(self, sample_python_project, mock_subprocess_run):
        """Test dependency vulnerability checking."""
        analyzer = StaticAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Should check dependencies
        assert "dependencies" in result["security"]

    def test_error_handling(self, temp_dir):
        """Test error handling in static analysis."""
        # Create invalid Python file
        bad_file = temp_dir / "bad.py"
        bad_file.write_text("This is not valid Python code!")

        analyzer = StaticAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Should handle errors gracefully
        assert "python" in result
        if "ast_analysis" in result["python"]:
            ast_result = result["python"]["ast_analysis"]
            assert ast_result["status"] == "completed"
            # Should have parse error
            assert any(issue["type"] == "parse_error" for issue in ast_result["issues"])


class TestASTAnalyzer:
    """Test AST analyzer functionality."""

    def test_function_analysis(self):
        """Test function analysis."""
        analyzer = ASTAnalyzer("test.py")

        # Test function with too many arguments
        import ast

        code = '''
def complex_function(a, b, c, d, e, f, g, h):
    """A function with many arguments."""
    pass
'''
        tree = ast.parse(code)
        analyzer.visit(tree)

        assert len(analyzer.issues) > 0
        assert any(issue["type"] == "too_many_arguments" for issue in analyzer.issues)

    def test_missing_docstring_detection(self):
        """Test detection of missing docstrings."""
        analyzer = ASTAnalyzer("test.py")

        code = """
def no_docstring():
    return 42

class NoDocstring:
    pass
"""
        tree = ast.parse(code)
        analyzer.visit(tree)

        docstring_issues = [i for i in analyzer.issues if i["type"] == "missing_docstring"]
        assert len(docstring_issues) == 2  # One for function, one for class

    def test_bare_except_detection(self):
        """Test detection of bare except clauses."""
        analyzer = ASTAnalyzer("test.py")

        code = """
try:
    risky_operation()
except:
    pass

try:
    another_operation()
except Exception:
    pass
"""
        tree = ast.parse(code)
        analyzer.visit(tree)

        bare_except_issues = [i for i in analyzer.issues if i["type"] == "bare_except"]
        assert len(bare_except_issues) == 1  # Only the first one is bare
