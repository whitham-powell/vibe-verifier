"""Static analysis and verification module."""

import ast
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil


class StaticAnalyzer:
    """Performs static analysis using various tools."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results = {
            "python": {},
            "security": {},
            "type_checking": {},
            "linting": {}
        }
    
    def analyze(self) -> Dict[str, Any]:
        """Run comprehensive static analysis on the repository."""
        # Detect primary language
        from ..analyzers.complexity import LanguageDetector
        detector = LanguageDetector(str(self.repo_path))
        lang_info = detector.detect()
        
        primary_lang = lang_info.get("primary_language", "Unknown")
        
        if primary_lang == "Python":
            self._analyze_python()
        elif primary_lang == "JavaScript" or primary_lang == "TypeScript":
            self._analyze_javascript()
        
        # Run security analysis (language agnostic)
        self._run_security_analysis()
        
        return self.results
    
    def _analyze_python(self):
        """Run Python-specific static analysis."""
        # Run pylint
        self._run_pylint()
        
        # Run mypy for type checking
        self._run_mypy()
        
        # Run bandit for security
        self._run_bandit()
        
        # Custom AST analysis
        self._run_ast_analysis()
    
    def _run_pylint(self):
        """Run pylint analysis."""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", str(self.repo_path)],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                messages = json.loads(result.stdout)
                # Group messages by type
                grouped = {}
                for msg in messages:
                    msg_type = msg.get("type", "unknown")
                    if msg_type not in grouped:
                        grouped[msg_type] = []
                    grouped[msg_type].append({
                        "file": msg.get("path"),
                        "line": msg.get("line"),
                        "column": msg.get("column"),
                        "message": msg.get("message"),
                        "symbol": msg.get("symbol")
                    })
                
                self.results["linting"]["pylint"] = {
                    "status": "completed",
                    "messages": grouped,
                    "total_issues": len(messages)
                }
            else:
                self.results["linting"]["pylint"] = {
                    "status": "completed",
                    "messages": {},
                    "total_issues": 0
                }
                
        except Exception as e:
            self.results["linting"]["pylint"] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _run_mypy(self):
        """Run mypy type checking."""
        try:
            result = subprocess.run(
                ["mypy", "--json-report", "-", str(self.repo_path)],
                capture_output=True,
                text=True
            )
            
            # Parse mypy output
            issues = []
            for line in result.stdout.split('\n'):
                if line and ':' in line:
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        issues.append({
                            "file": parts[0],
                            "line": parts[1],
                            "type": parts[2].strip(),
                            "message": parts[3].strip()
                        })
            
            self.results["type_checking"]["mypy"] = {
                "status": "completed",
                "issues": issues,
                "total_issues": len(issues)
            }
            
        except Exception as e:
            self.results["type_checking"]["mypy"] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _run_bandit(self):
        """Run bandit security analysis."""
        try:
            result = subprocess.run(
                ["bandit", "-r", "-f", "json", str(self.repo_path)],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                report = json.loads(result.stdout)
                self.results["security"]["bandit"] = {
                    "status": "completed",
                    "metrics": report.get("metrics", {}),
                    "results": report.get("results", [])
                }
            else:
                self.results["security"]["bandit"] = {
                    "status": "completed",
                    "metrics": {},
                    "results": []
                }
                
        except Exception as e:
            self.results["security"]["bandit"] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _run_ast_analysis(self):
        """Run custom AST-based analysis."""
        issues = []
        
        for py_file in self.repo_path.rglob("*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                analyzer = ASTAnalyzer(str(py_file))
                analyzer.visit(tree)
                
                if analyzer.issues:
                    issues.extend(analyzer.issues)
                    
            except Exception as e:
                issues.append({
                    "file": str(py_file),
                    "type": "parse_error",
                    "message": str(e)
                })
        
        self.results["python"]["ast_analysis"] = {
            "status": "completed",
            "issues": issues,
            "total_issues": len(issues)
        }
    
    def _analyze_javascript(self):
        """Run JavaScript/TypeScript static analysis."""
        # Check for eslint
        self._run_eslint()
        
        # Check for tsc (TypeScript compiler)
        if (self.repo_path / "tsconfig.json").exists():
            self._run_tsc()
    
    def _run_eslint(self):
        """Run ESLint analysis."""
        try:
            result = subprocess.run(
                ["eslint", "--format=json", str(self.repo_path)],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                reports = json.loads(result.stdout)
                total_issues = sum(len(r.get("messages", [])) for r in reports)
                
                self.results["linting"]["eslint"] = {
                    "status": "completed",
                    "reports": reports,
                    "total_issues": total_issues
                }
            else:
                self.results["linting"]["eslint"] = {
                    "status": "completed",
                    "reports": [],
                    "total_issues": 0
                }
                
        except Exception as e:
            self.results["linting"]["eslint"] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _run_tsc(self):
        """Run TypeScript compiler checks."""
        try:
            result = subprocess.run(
                ["tsc", "--noEmit", "--pretty", "false"],
                cwd=str(self.repo_path),
                capture_output=True,
                text=True
            )
            
            issues = []
            for line in result.stdout.split('\n'):
                if line and '(' in line and ')' in line:
                    issues.append(line.strip())
            
            self.results["type_checking"]["tsc"] = {
                "status": "completed",
                "issues": issues,
                "total_issues": len(issues)
            }
            
        except Exception as e:
            self.results["type_checking"]["tsc"] = {
                "status": "failed",
                "error": str(e)
            }
    
    def _run_security_analysis(self):
        """Run general security analysis tools."""
        # Check for secrets
        self._check_secrets()
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_secrets(self):
        """Check for hardcoded secrets."""
        try:
            # Use truffleHog or similar
            result = subprocess.run(
                ["trufflehog", "filesystem", str(self.repo_path), "--json"],
                capture_output=True,
                text=True
            )
            
            secrets = []
            for line in result.stdout.split('\n'):
                if line:
                    try:
                        secret = json.loads(line)
                        secrets.append(secret)
                    except:
                        pass
            
            self.results["security"]["secrets"] = {
                "status": "completed",
                "found": len(secrets),
                "details": secrets[:10]  # Limit to first 10
            }
            
        except Exception as e:
            # Fallback to basic pattern matching
            self._basic_secret_scan()
    
    def _basic_secret_scan(self):
        """Basic pattern matching for secrets."""
        import re
        
        patterns = {
            "api_key": r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
            "password": r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"]([^'\"]+)['\"]",
            "token": r"(?i)(token|auth)\s*[:=]\s*['\"]?([a-zA-Z0-9_-]{20,})['\"]?",
            "aws": r"(?i)(aws[_-]?access[_-]?key[_-]?id|aws[_-]?secret[_-]?access[_-]?key)\s*[:=]\s*['\"]?([a-zA-Z0-9/+=]{20,})['\"]?"
        }
        
        findings = []
        
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.java', '.env', '.config', '.conf')):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for pattern_name, pattern in patterns.items():
                            matches = re.findall(pattern, content)
                            if matches:
                                findings.append({
                                    "file": str(file_path.relative_to(self.repo_path)),
                                    "type": pattern_name,
                                    "count": len(matches)
                                })
                    except:
                        pass
        
        self.results["security"]["secrets"] = {
            "status": "completed",
            "found": len(findings),
            "details": findings
        }
    
    def _check_dependencies(self):
        """Check for vulnerable dependencies."""
        results = {}
        
        # Check Python dependencies
        if (self.repo_path / "requirements.txt").exists():
            try:
                result = subprocess.run(
                    ["safety", "check", "--json"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    results["python"] = json.loads(result.stdout)
            except:
                pass
        
        # Check npm dependencies
        if (self.repo_path / "package.json").exists():
            try:
                result = subprocess.run(
                    ["npm", "audit", "--json"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                if result.stdout:
                    results["npm"] = json.loads(result.stdout)
            except:
                pass
        
        self.results["security"]["dependencies"] = results


class ASTAnalyzer(ast.NodeVisitor):
    """Custom AST analyzer for Python code issues."""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.issues = []
    
    def visit_FunctionDef(self, node):
        # Check for too many arguments
        if len(node.args.args) > 5:
            self.issues.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "too_many_arguments",
                "message": f"Function '{node.name}' has {len(node.args.args)} arguments (max recommended: 5)"
            })
        
        # Check for missing docstring
        if not ast.get_docstring(node):
            self.issues.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "missing_docstring",
                "message": f"Function '{node.name}' is missing a docstring"
            })
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        # Check for missing docstring
        if not ast.get_docstring(node):
            self.issues.append({
                "file": self.filename,
                "line": node.lineno,
                "type": "missing_docstring",
                "message": f"Class '{node.name}' is missing a docstring"
            })
        
        self.generic_visit(node)
    
    def visit_Try(self, node):
        # Check for bare except
        for handler in node.handlers:
            if handler.type is None:
                self.issues.append({
                    "file": self.filename,
                    "line": handler.lineno,
                    "type": "bare_except",
                    "message": "Bare except clause found (catches all exceptions)"
                })
        
        self.generic_visit(node)