"""Formal verification module supporting multiple languages."""

import subprocess
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import tempfile
import shutil


class FormalVerifier:
    """Performs formal verification and property checking across multiple languages."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.results = {
            "contracts": {},
            "assertions": {},
            "properties": {},
            "proofs": {},
            "smt_checks": {}
        }
    
    def verify(self) -> Dict[str, Any]:
        """Run formal verification checks based on detected languages."""
        # Detect languages and verification capabilities
        self._detect_verification_targets()
        
        # Run language-specific verifiers
        self._verify_rust()
        self._verify_c_cpp()
        self._verify_java()
        self._verify_solidity()
        self._verify_python()
        self._verify_javascript()
        self._verify_go()
        
        # Run general SMT-based verification
        self._run_smt_verification()
        
        return self.results
    
    def _detect_verification_targets(self):
        """Detect which verification tools and approaches to use."""
        self.verification_targets = {
            "rust": self._check_rust_verification(),
            "c_cpp": self._check_c_cpp_verification(),
            "java": self._check_java_verification(),
            "solidity": self._check_solidity_verification(),
            "python": self._check_python_verification(),
            "javascript": self._check_javascript_verification(),
            "go": self._check_go_verification()
        }
    
    def _check_rust_verification(self) -> Dict[str, bool]:
        """Check available Rust verification tools."""
        return {
            "prusti": shutil.which("prusti") is not None,
            "kani": shutil.which("kani") is not None,
            "creusot": shutil.which("creusot") is not None,
            "miri": shutil.which("cargo-miri") is not None,
            "contracts": any(self.repo_path.rglob("*.rs"))
        }
    
    def _check_c_cpp_verification(self) -> Dict[str, bool]:
        """Check available C/C++ verification tools."""
        return {
            "cbmc": shutil.which("cbmc") is not None,
            "cppcheck": shutil.which("cppcheck") is not None,
            "frama_c": shutil.which("frama-c") is not None,
            "seahorn": shutil.which("seahorn") is not None,
            "files": any(self.repo_path.rglob("*.c")) or any(self.repo_path.rglob("*.cpp"))
        }
    
    def _check_java_verification(self) -> Dict[str, bool]:
        """Check available Java verification tools."""
        return {
            "openjml": shutil.which("openjml") is not None,
            "key": os.path.exists("/opt/key/key.jar"),
            "spotbugs": shutil.which("spotbugs") is not None,
            "files": any(self.repo_path.rglob("*.java"))
        }
    
    def _check_solidity_verification(self) -> Dict[str, bool]:
        """Check available Solidity verification tools."""
        return {
            "mythril": shutil.which("myth") is not None,
            "slither": shutil.which("slither") is not None,
            "manticore": shutil.which("manticore") is not None,
            "files": any(self.repo_path.rglob("*.sol"))
        }
    
    def _check_python_verification(self) -> Dict[str, bool]:
        """Check available Python verification tools."""
        return {
            "crosshair": shutil.which("crosshair") is not None,
            "hypothesis": True,  # Usually available via pip
            "contracts": True,  # PyContracts or similar
            "files": any(self.repo_path.rglob("*.py"))
        }
    
    def _check_javascript_verification(self) -> Dict[str, bool]:
        """Check available JavaScript/TypeScript verification tools."""
        return {
            "flow": shutil.which("flow") is not None,
            "typescript": shutil.which("tsc") is not None,
            "files": any(self.repo_path.rglob("*.js")) or any(self.repo_path.rglob("*.ts"))
        }
    
    def _check_go_verification(self) -> Dict[str, bool]:
        """Check available Go verification tools."""
        return {
            "staticcheck": shutil.which("staticcheck") is not None,
            "gosec": shutil.which("gosec") is not None,
            "files": any(self.repo_path.rglob("*.go"))
        }
    
    def _verify_rust(self):
        """Run Rust formal verification tools."""
        if not self.verification_targets["rust"]["files"]:
            return
        
        results = {}
        
        # Run Prusti if available
        if self.verification_targets["rust"]["prusti"]:
            try:
                result = subprocess.run(
                    ["cargo", "prusti"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                results["prusti"] = {
                    "status": "completed",
                    "output": result.stdout,
                    "errors": result.stderr,
                    "verified": result.returncode == 0
                }
            except Exception as e:
                results["prusti"] = {"status": "failed", "error": str(e)}
        
        # Run Kani if available
        if self.verification_targets["rust"]["kani"]:
            try:
                result = subprocess.run(
                    ["cargo", "kani"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                results["kani"] = {
                    "status": "completed",
                    "output": result.stdout,
                    "verified": result.returncode == 0
                }
            except Exception as e:
                results["kani"] = {"status": "failed", "error": str(e)}
        
        # Run Miri for undefined behavior detection
        if self.verification_targets["rust"]["miri"]:
            try:
                result = subprocess.run(
                    ["cargo", "+nightly", "miri", "test"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                results["miri"] = {
                    "status": "completed",
                    "output": result.stdout,
                    "ub_detected": "undefined behavior" in result.stderr.lower()
                }
            except Exception as e:
                results["miri"] = {"status": "failed", "error": str(e)}
        
        self.results["contracts"]["rust"] = results
    
    def _verify_c_cpp(self):
        """Run C/C++ formal verification tools."""
        if not self.verification_targets["c_cpp"]["files"]:
            return
        
        results = {}
        
        # Run CBMC (C Bounded Model Checker)
        if self.verification_targets["c_cpp"]["cbmc"]:
            c_files = list(self.repo_path.rglob("*.c"))
            cpp_files = list(self.repo_path.rglob("*.cpp"))
            
            for file in c_files + cpp_files:
                try:
                    result = subprocess.run(
                        ["cbmc", str(file), "--bounds-check", "--pointer-check", "--div-by-zero-check"],
                        capture_output=True,
                        text=True
                    )
                    
                    file_key = str(file.relative_to(self.repo_path))
                    results[file_key] = {
                        "tool": "cbmc",
                        "verified": "VERIFICATION SUCCESSFUL" in result.stdout,
                        "issues": self._parse_cbmc_output(result.stdout)
                    }
                except Exception as e:
                    results[str(file)] = {"status": "failed", "error": str(e)}
        
        # Run Frama-C if available
        if self.verification_targets["c_cpp"]["frama_c"]:
            for c_file in self.repo_path.rglob("*.c"):
                try:
                    result = subprocess.run(
                        ["frama-c", "-wp", "-wp-rte", str(c_file)],
                        capture_output=True,
                        text=True
                    )
                    
                    file_key = str(c_file.relative_to(self.repo_path))
                    if file_key not in results:
                        results[file_key] = {}
                    
                    results[file_key]["frama_c"] = {
                        "status": "completed",
                        "wp_proved": self._parse_frama_c_results(result.stdout)
                    }
                except Exception as e:
                    pass
        
        self.results["contracts"]["c_cpp"] = results
    
    def _verify_java(self):
        """Run Java formal verification tools."""
        if not self.verification_targets["java"]["files"]:
            return
        
        results = {}
        
        # Run OpenJML if available
        if self.verification_targets["java"]["openjml"]:
            java_files = list(self.repo_path.rglob("*.java"))
            
            for file in java_files:
                try:
                    result = subprocess.run(
                        ["openjml", "-check", str(file)],
                        capture_output=True,
                        text=True
                    )
                    
                    results[str(file.relative_to(self.repo_path))] = {
                        "tool": "openjml",
                        "verified": result.returncode == 0,
                        "warnings": self._parse_openjml_output(result.stdout)
                    }
                except Exception as e:
                    results[str(file)] = {"status": "failed", "error": str(e)}
        
        self.results["contracts"]["java"] = results
    
    def _verify_solidity(self):
        """Run Solidity smart contract verification."""
        if not self.verification_targets["solidity"]["files"]:
            return
        
        results = {}
        
        # Run Mythril
        if self.verification_targets["solidity"]["mythril"]:
            for sol_file in self.repo_path.rglob("*.sol"):
                try:
                    result = subprocess.run(
                        ["myth", "analyze", str(sol_file), "-o", "json"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.stdout:
                        results[str(sol_file.relative_to(self.repo_path))] = {
                            "mythril": json.loads(result.stdout)
                        }
                except Exception as e:
                    results[str(sol_file)] = {"mythril": {"status": "failed", "error": str(e)}}
        
        # Run Slither
        if self.verification_targets["solidity"]["slither"]:
            try:
                result = subprocess.run(
                    ["slither", str(self.repo_path), "--json", "-"],
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    results["slither"] = json.loads(result.stdout)
            except Exception as e:
                results["slither"] = {"status": "failed", "error": str(e)}
        
        self.results["contracts"]["solidity"] = results
    
    def _verify_python(self):
        """Run Python verification tools."""
        if not self.verification_targets["python"]["files"]:
            return
        
        results = {}
        
        # Run CrossHair if available
        if self.verification_targets["python"]["crosshair"]:
            py_files = list(self.repo_path.rglob("*.py"))
            
            for file in py_files:
                try:
                    result = subprocess.run(
                        ["crosshair", "check", str(file)],
                        capture_output=True,
                        text=True,
                        timeout=60  # Timeout after 1 minute
                    )
                    
                    results[str(file.relative_to(self.repo_path))] = {
                        "crosshair": {
                            "status": "completed",
                            "counterexamples": self._parse_crosshair_output(result.stdout)
                        }
                    }
                except Exception as e:
                    results[str(file)] = {"crosshair": {"status": "failed", "error": str(e)}}
        
        self.results["contracts"]["python"] = results
    
    def _verify_javascript(self):
        """Run JavaScript/TypeScript verification."""
        if not self.verification_targets["javascript"]["files"]:
            return
        
        results = {}
        
        # Run Flow type checker if available
        if self.verification_targets["javascript"]["flow"]:
            try:
                result = subprocess.run(
                    ["flow", "check", "--json"],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    results["flow"] = json.loads(result.stdout)
            except Exception as e:
                results["flow"] = {"status": "failed", "error": str(e)}
        
        self.results["contracts"]["javascript"] = results
    
    def _verify_go(self):
        """Run Go verification tools."""
        if not self.verification_targets["go"]["files"]:
            return
        
        results = {}
        
        # Run staticcheck
        if self.verification_targets["go"]["staticcheck"]:
            try:
                result = subprocess.run(
                    ["staticcheck", "-f", "json", "./..."],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                
                issues = []
                for line in result.stdout.split('\n'):
                    if line:
                        try:
                            issues.append(json.loads(line))
                        except:
                            pass
                
                results["staticcheck"] = {
                    "status": "completed",
                    "issues": issues
                }
            except Exception as e:
                results["staticcheck"] = {"status": "failed", "error": str(e)}
        
        # Run gosec
        if self.verification_targets["go"]["gosec"]:
            try:
                result = subprocess.run(
                    ["gosec", "-fmt", "json", "./..."],
                    cwd=str(self.repo_path),
                    capture_output=True,
                    text=True
                )
                
                if result.stdout:
                    results["gosec"] = json.loads(result.stdout)
            except Exception as e:
                results["gosec"] = {"status": "failed", "error": str(e)}
        
        self.results["contracts"]["go"] = results
    
    def _run_smt_verification(self):
        """Run SMT-based verification for assertions and properties."""
        # This would integrate with Z3, CVC4, or other SMT solvers
        # to verify custom properties and assertions
        pass
    
    def _parse_cbmc_output(self, output: str) -> List[Dict[str, Any]]:
        """Parse CBMC output for issues."""
        issues = []
        lines = output.split('\n')
        
        for i, line in enumerate(lines):
            if "VERIFICATION FAILED" in line or "assertion" in line:
                issues.append({
                    "type": "assertion_failure",
                    "line": line.strip(),
                    "context": lines[max(0, i-2):i+3]
                })
        
        return issues
    
    def _parse_frama_c_results(self, output: str) -> Dict[str, int]:
        """Parse Frama-C WP results."""
        proved = output.count("Proved")
        total = output.count("Goal")
        
        return {
            "proved": proved,
            "total": total,
            "percentage": (proved / total * 100) if total > 0 else 0
        }
    
    def _parse_openjml_output(self, output: str) -> List[str]:
        """Parse OpenJML warnings and errors."""
        warnings = []
        for line in output.split('\n'):
            if "warning:" in line or "error:" in line:
                warnings.append(line.strip())
        return warnings
    
    def _parse_crosshair_output(self, output: str) -> List[Dict[str, str]]:
        """Parse CrossHair counterexamples."""
        counterexamples = []
        lines = output.split('\n')
        
        current_example = None
        for line in lines:
            if "Counterexample found" in line:
                if current_example:
                    counterexamples.append(current_example)
                current_example = {"description": line}
            elif current_example and line.strip():
                if "inputs" not in current_example:
                    current_example["inputs"] = []
                current_example["inputs"].append(line.strip())
        
        if current_example:
            counterexamples.append(current_example)
        
        return counterexamples