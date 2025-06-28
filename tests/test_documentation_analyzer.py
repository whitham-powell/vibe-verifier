"""Tests for documentation analyzer module."""

from src.analyzers.documentation_analyzer import ClaimVerifier, DocumentationAnalyzer


class TestDocumentationAnalyzer:
    """Test documentation analysis functionality."""

    def test_find_documentation_files(self, sample_python_project):
        """Test finding documentation files."""
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        analyzer._find_documentation_files()

        # Should find README.md
        readme_found = any("README.md" in str(f) for f in analyzer.documentation_files)
        assert readme_found
        assert len(analyzer.documentation_files) >= 1

    def test_extract_claims_from_readme(self, sample_python_project):
        """Test extracting claims from README."""
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        assert result["summary"]["total_claims"] > 0
        assert result["summary"]["documentation_files"] >= 1

        # Check for specific claim types
        claims_by_type = result["claims_by_type"]
        assert len(claims_by_type) > 0

        # Should find performance claims
        if "performance" in claims_by_type:
            perf_claims = claims_by_type["performance"]
            assert any("1000 operations per second" in claim["text"] for claim in perf_claims)

        # Should find feature claims
        if "feature" in claims_by_type:
            feature_claims = claims_by_type["feature"]
            assert len(feature_claims) > 0

    def test_extract_api_claims(self, sample_python_project):
        """Test extraction of API claims."""
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Should find API claims from code examples
        if "api" in result["claims_by_type"]:
            api_claims = result["claims_by_type"]["api"]
            assert any("calculate_sum" in claim["text"] for claim in api_claims)

    def test_extract_security_claims(self, sample_multi_language_project):
        """Test extraction of security claims."""
        analyzer = DocumentationAnalyzer(str(sample_multi_language_project))
        result = analyzer.analyze()

        # Should find security claims
        if "security" in result["claims_by_type"]:
            security_claims = result["claims_by_type"]["security"]
            assert len(security_claims) > 0
            assert any("SQL injection" in claim["text"] for claim in security_claims)

    def test_verify_claim_confidence(self, temp_dir):
        """Test claim confidence calculation."""
        readme = temp_dir / "README.md"
        readme.write_text(
            """
# Test Project

- This function always returns the correct result
- The API may sometimes fail under heavy load
- Performance is guaranteed to be O(1)
- Possibly handles edge cases
"""
        )

        analyzer = DocumentationAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Claims with "always" or "guaranteed" should have higher confidence
        high_confidence_claims = []
        low_confidence_claims = []

        for _claim_type, claims in result["claims_by_type"].items():
            for claim in claims:
                if claim["confidence"] >= 0.7:
                    high_confidence_claims.append(claim)
                elif claim["confidence"] <= 0.3:
                    low_confidence_claims.append(claim)

        # Should have different confidence levels
        assert len(high_confidence_claims) > 0
        assert any(
            "always" in claim["text"] or "guaranteed" in claim["text"]
            for claim in high_confidence_claims
        )

    def test_correlate_claims_with_code(self, sample_python_project):
        """Test correlating documentation claims with code."""
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Should find related code for API claims
        for _claim_type, claims in result["claims_by_type"].items():
            for claim in claims:
                if "calculate_sum" in claim["text"] and claim["verifiable"]:
                    assert len(claim["related_code"]) > 0
                    assert any("main.py" in code for code in claim["related_code"])

    def test_parse_docstrings(self, sample_python_project):
        """Test extraction of claims from docstrings."""
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        # Should find claims from docstrings
        docstring_claims = []
        for source, claims in result["claims_by_source"].items():
            if "main.py" in source:
                docstring_claims.extend(claims)

        assert len(docstring_claims) > 0
        assert any("returns the correct sum" in claim["text"] for claim in docstring_claims)

    def test_verification_recommendations(self, sample_python_project):
        """Test generation of verification recommendations."""
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        result = analyzer.analyze()

        recommendations = result["verification_recommendations"]
        assert len(recommendations) > 0

        # Should have different types of recommendations
        rec_types = [r["type"] for r in recommendations]
        assert any(
            t in rec_types
            for t in [
                "unit_testing",
                "performance_testing",
                "security_testing",
                "integration_testing",
            ]
        )

    def test_code_example_analysis(self, temp_dir):
        """Test analysis of code examples in documentation."""
        readme = temp_dir / "README.md"
        readme.write_text(
            """
# API Documentation

## Usage

```python
result = calculate(10, 20)
obj = Calculator()
obj.process(data)
```

The above code demonstrates the API usage.
"""
        )

        analyzer = DocumentationAnalyzer(str(temp_dir))
        result = analyzer.analyze()

        # Should extract implicit API claims from code examples
        api_claims = result["claims_by_type"].get("api", [])
        assert len(api_claims) > 0
        assert any("calculate" in claim["text"] for claim in api_claims)
        assert any("Calculator" in claim["text"] for claim in api_claims)


class TestClaimVerifier:
    """Test claim verification functionality."""

    def test_verify_api_claims(self, sample_python_project):
        """Test verification of API claims."""
        # First analyze documentation
        analyzer = DocumentationAnalyzer(str(sample_python_project))
        doc_result = analyzer.analyze()

        # Extract claims
        all_claims = []
        for claim_type, claims in doc_result["claims_by_type"].items():
            for claim in claims:
                claim["type"] = claim_type
                all_claims.append(claim)

        # Verify claims
        verifier = ClaimVerifier(str(sample_python_project))
        result = verifier.verify_claims(all_claims)

        assert "summary" in result
        assert result["summary"]["total_claims"] == len(all_claims)

        # API claims with related code should be verified
        assert len(result["verified"]) > 0

    def test_verify_failed_claims(self, temp_dir):
        """Test verification of claims that should fail."""
        # Create README with false claims
        readme = temp_dir / "README.md"
        readme.write_text(
            """
# Test Project

- The `nonexistent_function` provides fast computation
- The `MissingClass` handles all edge cases
"""
        )

        analyzer = DocumentationAnalyzer(str(temp_dir))
        doc_result = analyzer.analyze()

        claims = []
        for claim_type, type_claims in doc_result["claims_by_type"].items():
            for claim in type_claims:
                claim["type"] = claim_type
                claims.append(claim)

        verifier = ClaimVerifier(str(temp_dir))
        result = verifier.verify_claims(claims)

        # Should have failed verifications
        assert len(result["failed"]) > 0

    def test_verify_inconclusive_claims(self, temp_dir):
        """Test claims that cannot be automatically verified."""
        readme = temp_dir / "README.md"
        readme.write_text(
            """
# Test Project

- Provides excellent user experience
- Has beautiful UI design
- Easy to use and intuitive
"""
        )

        analyzer = DocumentationAnalyzer(str(temp_dir))
        doc_result = analyzer.analyze()

        claims = []
        for claim_type, type_claims in doc_result["claims_by_type"].items():
            for claim in type_claims:
                claim["type"] = claim_type
                claims.append(claim)

        verifier = ClaimVerifier(str(temp_dir))
        result = verifier.verify_claims(claims)

        # Should have inconclusive results for subjective claims
        assert len(result["inconclusive"]) > 0

    def test_empty_claims_list(self, temp_dir):
        """Test verification with no claims."""
        verifier = ClaimVerifier(str(temp_dir))
        result = verifier.verify_claims([])

        assert result["summary"]["total_claims"] == 0
        assert result["summary"]["verification_rate"] == 0
        assert len(result["verified"]) == 0
        assert len(result["failed"]) == 0
        assert len(result["inconclusive"]) == 0
