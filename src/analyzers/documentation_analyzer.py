"""Documentation analysis and claim verification module."""

import re
import os
import ast
import json
import yaml
import toml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import markdown
from bs4 import BeautifulSoup


@dataclass
class Claim:
    """Represents a claim made in documentation."""
    text: str
    source_file: str
    line_number: int
    claim_type: str  # feature, performance, security, api, behavior
    confidence: float
    context: str = ""
    verifiable: bool = True
    verification_method: str = ""
    related_code: List[str] = field(default_factory=list)


class DocumentationAnalyzer:
    """Analyzes documentation to extract and verify claims."""
    
    # Patterns for identifying claims
    CLAIM_PATTERNS = {
        "feature": [
            r"(?i)(supports?|provides?|enables?|allows?|implements?|offers?)\s+(.+)",
            r"(?i)(can|will|does)\s+(.+)",
            r"(?i)(feature[s]?|functionality|capability)[:]\s*(.+)",
        ],
        "performance": [
            r"(?i)(fast|quick|efficient|optimized|performance)\s+(.+)",
            r"(?i)(\d+[x]?\s*faster|slower)\s+than\s+(.+)",
            r"(?i)(handles?|processes?|supports?)\s+(\d+\s*(?:requests?|operations?|items?))",
            r"(?i)(latency|throughput|response time)[:]\s*(.+)",
        ],
        "security": [
            r"(?i)(secure|encrypted|authenticated|authorized|protected)\s+(.+)",
            r"(?i)(prevents?|blocks?|validates?|sanitizes?)\s+(.+)",
            r"(?i)(vulnerability|threat|attack|exploit)\s+(.+)",
        ],
        "api": [
            r"(?i)(api|endpoint|method|function|class)\s*[:]\s*(.+)",
            r"(?i)(returns?|accepts?|expects?|requires?)\s+(.+)",
            r"(?i)(parameter[s]?|argument[s]?|input[s]?|output[s]?)[:]\s*(.+)",
        ],
        "behavior": [
            r"(?i)(always|never|must|should|shall)\s+(.+)",
            r"(?i)(guaranteed|ensures?|maintains?)\s+(.+)",
            r"(?i)(default[s]?\s+to|behavior[s]?|action[s]?)[:]\s*(.+)",
        ]
    }
    
    # Documentation file patterns
    DOC_PATTERNS = [
        "README*", "readme*",
        "DOCUMENTATION*", "documentation*",
        "GUIDE*", "guide*",
        "MANUAL*", "manual*",
        "API*", "api*",
        "*.md", "*.rst", "*.txt",
        "docs/**/*", "doc/**/*",
        "wiki/**/*"
    ]
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.claims: List[Claim] = []
        self.documentation_files: List[Path] = []
        self.code_references: Dict[str, List[str]] = {}
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze documentation and extract verifiable claims."""
        # Find all documentation files
        self._find_documentation_files()
        
        # Extract claims from each file
        for doc_file in self.documentation_files:
            self._extract_claims_from_file(doc_file)
        
        # Analyze code references in documentation
        self._analyze_code_references()
        
        # Correlate claims with actual code
        self._correlate_claims_with_code()
        
        # Generate verification strategies
        self._generate_verification_strategies()
        
        return self._compile_results()
    
    def _find_documentation_files(self):
        """Find all documentation files in the repository."""
        for pattern in self.DOC_PATTERNS:
            if "**" in pattern:
                matches = list(self.repo_path.rglob(pattern.replace("**/*", "*")))
            else:
                matches = list(self.repo_path.glob(pattern))
            
            for match in matches:
                if match.is_file() and match not in self.documentation_files:
                    # Skip binary files and common non-documentation files
                    if match.suffix not in ['.pyc', '.class', '.o', '.so', '.dll', '.exe']:
                        self.documentation_files.append(match)
        
        # Also check for docstrings in source files
        self._find_inline_documentation()
    
    def _find_inline_documentation(self):
        """Find inline documentation (docstrings, comments) in source files."""
        # Python docstrings
        for py_file in self.repo_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                        docstring = ast.get_docstring(node)
                        if docstring:
                            # Create a virtual documentation entry
                            self._extract_claims_from_text(
                                docstring, 
                                str(py_file), 
                                getattr(node, 'lineno', 0),
                                "docstring"
                            )
            except:
                pass
        
        # TODO: Add support for other languages' inline documentation
    
    def _extract_claims_from_file(self, file_path: Path):
        """Extract claims from a documentation file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse based on file type
            if file_path.suffix == '.md':
                self._extract_from_markdown(content, str(file_path))
            elif file_path.suffix == '.rst':
                self._extract_from_rst(content, str(file_path))
            else:
                self._extract_from_text(content, str(file_path))
                
        except Exception as e:
            pass
    
    def _extract_from_markdown(self, content: str, source_file: str):
        """Extract claims from Markdown content."""
        # Parse markdown
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract text by sections
        current_section = "General"
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'p', 'li', 'code']):
            if element.name in ['h1', 'h2', 'h3']:
                current_section = element.get_text()
            else:
                text = element.get_text()
                if text.strip():
                    self._extract_claims_from_text(
                        text, 
                        source_file, 
                        0,  # Line number would need more sophisticated parsing
                        current_section
                    )
        
        # Also extract from code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', content, re.DOTALL)
        for i, code_block in enumerate(code_blocks):
            self._analyze_code_example(code_block, source_file, f"code_block_{i}")
    
    def _extract_from_rst(self, content: str, source_file: str):
        """Extract claims from reStructuredText content."""
        # Simple RST parsing (would need sphinx for full parsing)
        lines = content.split('\n')
        current_section = "General"
        
        for i, line in enumerate(lines):
            # Detect section headers
            if i < len(lines) - 1 and lines[i+1].strip() and all(c in '=-~' for c in lines[i+1].strip()):
                current_section = line.strip()
            elif line.strip():
                self._extract_claims_from_text(line, source_file, i+1, current_section)
    
    def _extract_from_text(self, content: str, source_file: str):
        """Extract claims from plain text content."""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                self._extract_claims_from_text(line, source_file, i+1, "General")
    
    def _extract_claims_from_text(self, text: str, source_file: str, line_number: int, context: str):
        """Extract claims from a text snippet using patterns."""
        for claim_type, patterns in self.CLAIM_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    claim_text = match[1] if isinstance(match, tuple) else match
                    
                    # Calculate confidence based on claim characteristics
                    confidence = self._calculate_claim_confidence(claim_text, claim_type)
                    
                    claim = Claim(
                        text=claim_text.strip(),
                        source_file=source_file,
                        line_number=line_number,
                        claim_type=claim_type,
                        confidence=confidence,
                        context=context
                    )
                    
                    self.claims.append(claim)
    
    def _calculate_claim_confidence(self, text: str, claim_type: str) -> float:
        """Calculate confidence score for a claim."""
        confidence = 0.5  # Base confidence
        
        # Adjust based on claim specificity
        if any(word in text.lower() for word in ['always', 'never', 'guaranteed', 'must']):
            confidence += 0.2
        
        if any(word in text.lower() for word in ['may', 'might', 'possibly', 'sometimes']):
            confidence -= 0.2
        
        # Adjust based on quantifiable metrics
        if re.search(r'\d+', text):
            confidence += 0.1
        
        # Adjust based on claim type
        if claim_type == "api":
            confidence += 0.1  # API claims are usually more verifiable
        elif claim_type == "performance":
            confidence += 0.05  # Performance claims need benchmarks
        
        return min(max(confidence, 0.0), 1.0)
    
    def _analyze_code_references(self):
        """Analyze code references mentioned in documentation."""
        for doc_file in self.documentation_files:
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find function/class references
                func_refs = re.findall(r'`(\w+\.\w+|\w+\(\))`', content)
                class_refs = re.findall(r'`class\s+(\w+)`|`(\w+)\s+class`', content)
                file_refs = re.findall(r'`([/\w]+\.\w+)`', content)
                
                for ref in func_refs + [c for refs in class_refs for c in refs if c] + file_refs:
                    if ref:
                        if str(doc_file) not in self.code_references:
                            self.code_references[str(doc_file)] = []
                        self.code_references[str(doc_file)].append(ref)
                        
            except:
                pass
    
    def _analyze_code_example(self, code: str, source_file: str, example_id: str):
        """Analyze code examples in documentation for implicit claims."""
        # Look for function calls, class instantiations, etc.
        # These represent implicit claims about API behavior
        
        # Simple pattern matching for common code patterns
        function_calls = re.findall(r'(\w+)\s*\([^)]*\)', code)
        class_instantiations = re.findall(r'(\w+)\s*\([^)]*\)\s*(?:;|$)', code)
        method_calls = re.findall(r'(\w+)\.(\w+)\s*\([^)]*\)', code)
        
        for func in function_calls:
            claim = Claim(
                text=f"Function '{func}' exists and can be called",
                source_file=source_file,
                line_number=0,
                claim_type="api",
                confidence=0.8,
                context=f"code_example_{example_id}"
            )
            self.claims.append(claim)
        
        for obj, method in method_calls:
            claim = Claim(
                text=f"Object '{obj}' has method '{method}'",
                source_file=source_file,
                line_number=0,
                claim_type="api",
                confidence=0.8,
                context=f"code_example_{example_id}"
            )
            self.claims.append(claim)
    
    def _correlate_claims_with_code(self):
        """Correlate documentation claims with actual code implementation."""
        # For each claim, try to find related code
        for claim in self.claims:
            if claim.claim_type == "api":
                # Look for function/class definitions
                self._find_api_implementation(claim)
            elif claim.claim_type == "feature":
                # Look for feature-related code
                self._find_feature_implementation(claim)
            elif claim.claim_type == "security":
                # Look for security-related code
                self._find_security_implementation(claim)
    
    def _find_api_implementation(self, claim: Claim):
        """Find API implementations mentioned in claims."""
        # Extract potential function/class names from claim
        potential_names = re.findall(r'\b(\w+)\b', claim.text)
        
        for name in potential_names:
            # Search for function/class definitions
            # This is simplified - real implementation would use AST
            for ext in ['.py', '.js', '.java', '.cpp', '.go']:
                for code_file in self.repo_path.rglob(f"*{ext}"):
                    try:
                        with open(code_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Simple pattern matching (language-specific patterns needed)
                        if ext == '.py':
                            if re.search(rf'def\s+{name}\s*\(', content) or \
                               re.search(rf'class\s+{name}\s*[\(:]', content):
                                claim.related_code.append(str(code_file))
                        elif ext in ['.js', '.ts']:
                            if re.search(rf'function\s+{name}\s*\(', content) or \
                               re.search(rf'class\s+{name}\s*\{{', content):
                                claim.related_code.append(str(code_file))
                                
                    except:
                        pass
    
    def _find_feature_implementation(self, claim: Claim):
        """Find feature implementations based on keywords."""
        # Extract keywords from claim
        keywords = [word.lower() for word in re.findall(r'\b(\w{4,})\b', claim.text) 
                   if word.lower() not in ['that', 'this', 'with', 'from', 'have']]
        
        # Search for files containing these keywords
        for keyword in keywords[:3]:  # Limit to top 3 keywords
            for code_file in self.repo_path.rglob("*"):
                if code_file.is_file() and code_file.suffix in ['.py', '.js', '.java', '.cpp', '.go']:
                    try:
                        with open(code_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if keyword in content.lower():
                            claim.related_code.append(str(code_file))
                            break
                    except:
                        pass
    
    def _find_security_implementation(self, claim: Claim):
        """Find security-related implementations."""
        security_keywords = [
            'auth', 'encrypt', 'decrypt', 'validate', 'sanitize', 
            'token', 'password', 'hash', 'salt', 'verify', 'secure'
        ]
        
        # Look for security-related code
        for keyword in security_keywords:
            if keyword in claim.text.lower():
                for code_file in self.repo_path.rglob("*"):
                    if code_file.is_file() and code_file.suffix in ['.py', '.js', '.java', '.cpp', '.go']:
                        try:
                            with open(code_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            if keyword in content.lower():
                                claim.related_code.append(str(code_file))
                                break
                        except:
                            pass
    
    def _generate_verification_strategies(self):
        """Generate verification strategies for each claim."""
        for claim in self.claims:
            if claim.claim_type == "api":
                claim.verification_method = "unit_test"
                claim.verifiable = True
            elif claim.claim_type == "performance":
                claim.verification_method = "benchmark"
                claim.verifiable = True
            elif claim.claim_type == "security":
                claim.verification_method = "security_test"
                claim.verifiable = True
            elif claim.claim_type == "feature":
                claim.verification_method = "integration_test"
                claim.verifiable = len(claim.related_code) > 0
            elif claim.claim_type == "behavior":
                claim.verification_method = "property_test"
                claim.verifiable = len(claim.related_code) > 0
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile analysis results."""
        # Group claims by type and source
        claims_by_type = {}
        claims_by_source = {}
        
        for claim in self.claims:
            # By type
            if claim.claim_type not in claims_by_type:
                claims_by_type[claim.claim_type] = []
            claims_by_type[claim.claim_type].append({
                "text": claim.text,
                "source": claim.source_file,
                "confidence": claim.confidence,
                "verifiable": claim.verifiable,
                "verification_method": claim.verification_method,
                "related_code": claim.related_code
            })
            
            # By source
            if claim.source_file not in claims_by_source:
                claims_by_source[claim.source_file] = []
            claims_by_source[claim.source_file].append({
                "text": claim.text,
                "type": claim.claim_type,
                "confidence": claim.confidence
            })
        
        # Calculate statistics
        total_claims = len(self.claims)
        verifiable_claims = sum(1 for c in self.claims if c.verifiable)
        high_confidence_claims = sum(1 for c in self.claims if c.confidence >= 0.7)
        
        return {
            "summary": {
                "total_claims": total_claims,
                "verifiable_claims": verifiable_claims,
                "verification_rate": (verifiable_claims / total_claims * 100) if total_claims > 0 else 0,
                "high_confidence_claims": high_confidence_claims,
                "documentation_files": len(self.documentation_files),
                "code_references_found": sum(len(refs) for refs in self.code_references.values())
            },
            "claims_by_type": claims_by_type,
            "claims_by_source": claims_by_source,
            "documentation_files": [str(f.relative_to(self.repo_path)) for f in self.documentation_files],
            "code_references": self.code_references,
            "verification_recommendations": self._generate_verification_recommendations()
        }
    
    def _generate_verification_recommendations(self) -> List[Dict[str, Any]]:
        """Generate specific recommendations for verifying claims."""
        recommendations = []
        
        # Group claims by verification method
        verification_groups = {}
        for claim in self.claims:
            if claim.verifiable:
                method = claim.verification_method
                if method not in verification_groups:
                    verification_groups[method] = []
                verification_groups[method].append(claim)
        
        # Generate recommendations for each group
        for method, claims in verification_groups.items():
            if method == "unit_test":
                recommendations.append({
                    "type": "unit_testing",
                    "priority": "high",
                    "description": f"Write unit tests for {len(claims)} API claims",
                    "examples": [c.text for c in claims[:3]],
                    "suggested_approach": "Create test cases that verify each function/method exists and behaves as documented"
                })
            elif method == "benchmark":
                recommendations.append({
                    "type": "performance_testing",
                    "priority": "medium",
                    "description": f"Create benchmarks for {len(claims)} performance claims",
                    "examples": [c.text for c in claims[:3]],
                    "suggested_approach": "Implement performance tests to measure and verify performance claims"
                })
            elif method == "security_test":
                recommendations.append({
                    "type": "security_testing",
                    "priority": "high",
                    "description": f"Verify {len(claims)} security claims",
                    "examples": [c.text for c in claims[:3]],
                    "suggested_approach": "Create security test cases and use security analysis tools"
                })
            elif method == "integration_test":
                recommendations.append({
                    "type": "integration_testing",
                    "priority": "medium",
                    "description": f"Create integration tests for {len(claims)} feature claims",
                    "examples": [c.text for c in claims[:3]],
                    "suggested_approach": "Write end-to-end tests that verify feature functionality"
                })
        
        # Add recommendation for unverifiable claims
        unverifiable = [c for c in self.claims if not c.verifiable]
        if unverifiable:
            recommendations.append({
                "type": "documentation_review",
                "priority": "low",
                "description": f"Review {len(unverifiable)} claims that couldn't be automatically verified",
                "examples": [c.text for c in unverifiable[:3]],
                "suggested_approach": "Manually review these claims and update documentation or add verification methods"
            })
        
        return recommendations


class ClaimVerifier:
    """Verifies documentation claims against actual implementation."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.verification_results = []
    
    def verify_claims(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify a list of claims against the codebase."""
        results = {
            "verified": [],
            "failed": [],
            "inconclusive": [],
            "summary": {}
        }
        
        for claim in claims:
            result = self._verify_single_claim(claim)
            
            if result["status"] == "verified":
                results["verified"].append(result)
            elif result["status"] == "failed":
                results["failed"].append(result)
            else:
                results["inconclusive"].append(result)
            
            self.verification_results.append(result)
        
        # Generate summary
        total = len(claims)
        results["summary"] = {
            "total_claims": total,
            "verified": len(results["verified"]),
            "failed": len(results["failed"]),
            "inconclusive": len(results["inconclusive"]),
            "verification_rate": (len(results["verified"]) / total * 100) if total > 0 else 0
        }
        
        return results
    
    def _verify_single_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single claim."""
        result = {
            "claim": claim["text"],
            "type": claim.get("type", "unknown"),
            "status": "inconclusive",
            "evidence": [],
            "confidence": 0.0
        }
        
        # Dispatch to appropriate verification method
        if claim.get("verification_method") == "unit_test":
            self._verify_api_claim(claim, result)
        elif claim.get("verification_method") == "benchmark":
            self._verify_performance_claim(claim, result)
        elif claim.get("verification_method") == "security_test":
            self._verify_security_claim(claim, result)
        else:
            self._verify_general_claim(claim, result)
        
        return result
    
    def _verify_api_claim(self, claim: Dict[str, Any], result: Dict[str, Any]):
        """Verify API-related claims."""
        # Check if related code exists
        if claim.get("related_code"):
            result["evidence"].append(f"Found implementation in {len(claim['related_code'])} files")
            result["status"] = "verified"
            result["confidence"] = 0.8
        else:
            result["status"] = "failed"
            result["evidence"].append("No implementation found for claimed API")
            result["confidence"] = 0.9
    
    def _verify_performance_claim(self, claim: Dict[str, Any], result: Dict[str, Any]):
        """Verify performance claims."""
        # Look for benchmarks or performance tests
        benchmark_patterns = ["benchmark", "perf", "performance", "bench"]
        
        for pattern in benchmark_patterns:
            for test_file in self.repo_path.rglob(f"*{pattern}*"):
                if test_file.is_file():
                    result["evidence"].append(f"Found potential benchmark: {test_file}")
                    result["status"] = "inconclusive"
                    result["confidence"] = 0.5
                    return
        
        result["status"] = "inconclusive"
        result["evidence"].append("No benchmarks found to verify performance claim")
        result["confidence"] = 0.3
    
    def _verify_security_claim(self, claim: Dict[str, Any], result: Dict[str, Any]):
        """Verify security claims."""
        # This would integrate with security analysis results
        result["status"] = "inconclusive"
        result["evidence"].append("Security verification requires dedicated security analysis")
        result["confidence"] = 0.4
    
    def _verify_general_claim(self, claim: Dict[str, Any], result: Dict[str, Any]):
        """Verify general claims."""
        if claim.get("related_code"):
            result["status"] = "inconclusive"
            result["evidence"].append(f"Found related code in {len(claim['related_code'])} files")
            result["confidence"] = 0.5
        else:
            result["status"] = "inconclusive"
            result["evidence"].append("Unable to automatically verify this claim")
            result["confidence"] = 0.2