"""Tests for complexity analyzer module."""

from src.analyzers.complexity import ComplexityAnalyzer, LanguageDetector


class TestLanguageDetector:
    """Test language detection functionality."""

    def test_detect_python_project(self, sample_python_project):
        """Test detection of Python language."""
        detector = LanguageDetector(str(sample_python_project))
        result = detector.detect()

        assert result["primary_language"] == "Python"
        assert result["total_files"] > 0
        assert "Python" in result["languages"]
        assert result["languages"]["Python"]["count"] >= 2

    def test_detect_javascript_project(self, sample_javascript_project):
        """Test detection of JavaScript language."""
        detector = LanguageDetector(str(sample_javascript_project))
        result = detector.detect()

        assert result["primary_language"] == "JavaScript"
        assert "JavaScript" in result["languages"]
        assert result["languages"]["JavaScript"]["count"] >= 2

    def test_detect_multi_language_project(self, sample_multi_language_project):
        """Test detection of multiple languages."""
        detector = LanguageDetector(str(sample_multi_language_project))
        result = detector.detect()

        languages = result["languages"]
        assert "Python" in languages
        assert "Go" in languages
        assert "TypeScript" in languages
        assert result["total_files"] >= 3

    def test_empty_directory(self, temp_dir):
        """Test detection in empty directory."""
        detector = LanguageDetector(str(temp_dir))
        result = detector.detect()

        assert result["total_files"] == 0
        assert result["primary_language"] is None
        assert result["languages"] == {}


class TestComplexityAnalyzer:
    """Test complexity analysis functionality."""

    def test_analyze_python_project(self, sample_python_project):
        """Test complexity analysis of Python code."""
        analyzer = ComplexityAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Check summary
        assert "summary" in result
        assert result["summary"]["total_files"] >= 1
        assert result["summary"]["average_complexity"] >= 0  # Can be 0 for very simple code
        assert "complexity_distribution" in result["summary"]

        # Check file analysis
        assert "files" in result
        main_file_key = None
        for key in result["files"]:
            if "main.py" in key:
                main_file_key = key
                break

        assert main_file_key is not None
        file_metrics = result["files"][main_file_key]

        # Check metrics
        assert file_metrics["loc"] > 0
        assert file_metrics["lloc"] > 0
        assert "functions" in file_metrics

        # Check that complex_function has high complexity
        complex_func = None
        for func in file_metrics["functions"]:
            if func["name"] == "complex_function":
                complex_func = func
                break

        assert complex_func is not None
        assert complex_func["complexity"] > 5  # Should have high complexity

    def test_analyze_simple_function(self, temp_dir):
        """Test analysis of simple function."""
        test_file = temp_dir / "simple.py"
        test_file.write_text(
            '''
def simple_function(x):
    """A simple function."""
    return x + 1
'''
        )

        analyzer = ComplexityAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        assert result["summary"]["average_complexity"] <= 2

        # Check complexity distribution
        dist = result["summary"]["complexity_distribution"]
        assert dist["A (1-5)"] >= 1
        assert dist["F (41+)"] == 0

    def test_analyze_complex_function(self, temp_dir):
        """Test analysis of complex function."""
        test_file = temp_dir / "complex.py"
        test_file.write_text(
            '''
def very_complex_function(a, b, c, d, e, f):
    """An overly complex function."""
    result = 0
    for i in range(a):
        if i % 2 == 0:
            for j in range(b):
                if j % 3 == 0:
                    for k in range(c):
                        if k % 5 == 0:
                            if d > 0:
                                if e > 0:
                                    if f > 0:
                                        result += i * j * k
                                    else:
                                        result -= i * j * k
                                else:
                                    result += i + j + k
                            else:
                                result -= i - j - k
                        else:
                            result += 1
                else:
                    result -= 1
        else:
            result *= 2
    return result
'''
        )

        analyzer = ComplexityAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Should have high complexity
        assert result["summary"]["average_complexity"] > 10

        # Check that it's in high complexity category
        dist = result["summary"]["complexity_distribution"]
        assert (dist.get("D (21-30)", 0) + dist.get("E (31-40)", 0) + dist.get("F (41+)", 0)) > 0

    def test_maintainability_index(self, sample_python_project):
        """Test maintainability index calculation."""
        analyzer = ComplexityAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Check that maintainability index is calculated
        for _file_path, metrics in result["files"].items():
            if isinstance(metrics, dict) and "maintainability_index" in metrics:
                # MI should be between 0 and 100
                assert 0 <= metrics["maintainability_index"] <= 100

    def test_error_handling(self, temp_dir):
        """Test error handling for invalid Python files."""
        # Create a file with syntax error
        bad_file = temp_dir / "bad.py"
        bad_file.write_text(
            """
def broken_function(:
    this is not valid python
"""
        )

        analyzer = ComplexityAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Should handle the error gracefully
        assert "files" in result
        bad_file_key = None
        for key in result["files"]:
            if "bad.py" in key:
                bad_file_key = key
                break

        if bad_file_key:
            assert "error" in result["files"][bad_file_key]

    def test_empty_file(self, temp_dir):
        """Test analysis of empty file."""
        empty_file = temp_dir / "empty.py"
        empty_file.write_text("")

        analyzer = ComplexityAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Should handle empty files
        assert result["summary"]["total_files"] >= 1
        assert result["summary"]["total_loc"] == 0
