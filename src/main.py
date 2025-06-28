"""Main entry point for Vibe Verifier."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .analyzers.complexity import ComplexityAnalyzer, LanguageDetector
from .analyzers.documentation_analyzer import ClaimVerifier, DocumentationAnalyzer
from .analyzers.git_history import GitHistoryAnalyzer
from .reporters.report_generator import ReportGenerator, SummaryReporter
from .testers.test_runner import UniversalTestRunner
from .utils.security import get_safe_path, sanitize_results
from .verifiers.formal_verifier import FormalVerifier
from .verifiers.static_analyzer import StaticAnalyzer


class VibeVerifier:
    """Main orchestrator for code verification."""

    def __init__(self, repo_path: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the VibeVerifier.

        Args:
            repo_path: Path to the repository to analyze.
            config: Optional configuration dictionary.
        """
        self.repo_path = Path(repo_path).resolve()
        self.config = config or {}
        self.results: Dict[str, Any] = {}

        # Validate repository exists
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        if not self.repo_path.is_dir():
            raise ValueError(f"Path is not a directory: {repo_path}")

    def run_analysis(self) -> Dict[str, Any]:
        """Run complete analysis pipeline."""
        display_path = (
            get_safe_path(self.repo_path) if self.config.get("sanitize", True) else self.repo_path
        )
        print(f"\n🔍 Starting Vibe Verifier analysis for: {display_path}")
        print("=" * 60)

        # Phase 0: Git History Analysis (if applicable)
        print("\n🔍 Phase 0: Git History Analysis")
        git_analyzer = GitHistoryAnalyzer(str(self.repo_path))
        git_results = git_analyzer.analyze()
        self.results["git_history"] = git_results

        if git_results.get("is_git_repo"):
            repo_info = git_results.get("repository_info", {})
            print(f"  Repository age: {repo_info.get('repo_age_days', 0)} days")
            print(f"  Total commits: {repo_info.get('total_commits', 0)}")
            contributors = git_results.get("contributor_analysis", {})
            print(f"  Contributors: {contributors.get('total_contributors', 0)}")

            # Display key insights
            insights = git_results.get("insights", [])
            if insights:
                print("  Key insights:")
                for insight in insights[:3]:  # Show top 3 insights
                    print(f"    - {insight['message']}")
        else:
            print("  Not a git repository - skipping git history analysis")

        # Phase 1: Language Detection
        print("\n📊 Phase 1: Language Detection")
        detector = LanguageDetector(str(self.repo_path))
        language_info = detector.detect()
        self.results["languages"] = language_info
        print(f"  Primary language: {language_info.get('primary_language', 'Unknown')}")
        print(f"  Total files: {language_info.get('total_files', 0)}")

        # Phase 2: Documentation Analysis
        print("\n📚 Phase 2: Documentation Analysis")
        doc_analyzer = DocumentationAnalyzer(str(self.repo_path))
        doc_results = doc_analyzer.analyze()
        self.results["documentation"] = doc_results
        print(f"  Documentation files found: {doc_results['summary']['documentation_files']}")
        print(f"  Total claims extracted: {doc_results['summary']['total_claims']}")
        print(f"  Verifiable claims: {doc_results['summary']['verifiable_claims']}")

        # Phase 3: Complexity Analysis
        print("\n📈 Phase 3: Complexity Analysis")
        complexity_analyzer = ComplexityAnalyzer(str(self.repo_path))
        complexity_results = complexity_analyzer.analyze()
        self.results["complexity"] = complexity_results
        print(f"  Files analyzed: {complexity_results['summary']['total_files']}")
        avg_complexity = complexity_results["summary"]["average_complexity"]
        print(f"  Average complexity: {avg_complexity:.2f}")

        # Phase 4: Static Analysis & Verification
        print("\n🔒 Phase 4: Static Analysis & Verification")
        static_analyzer = StaticAnalyzer(str(self.repo_path))
        static_results = static_analyzer.analyze()
        self.results["static_analysis"] = static_results

        # Count issues
        total_issues = 0
        for category in ["linting", "type_checking", "security"]:
            for _, results in static_results.get(category, {}).items():
                if isinstance(results, dict) and "total_issues" in results:
                    total_issues += results["total_issues"]
        print(f"  Total static analysis issues: {total_issues}")

        # Phase 5: Formal Verification
        print("\n✓ Phase 5: Formal Verification")
        formal_verifier = FormalVerifier(str(self.repo_path))
        verification_results = formal_verifier.verify()
        self.results["formal_verification"] = verification_results

        # Count verified contracts
        verified_count = 0
        for _, contracts in verification_results.get("contracts", {}).items():
            if contracts:
                verified_count += len(contracts)
        print(f"  Formal verification checks performed: {verified_count}")

        # Phase 6: Test Discovery & Execution
        print("\n🧪 Phase 6: Test Discovery & Execution")
        test_runner = UniversalTestRunner(str(self.repo_path))
        test_results = test_runner.run_tests()
        self.results["tests"] = test_results

        summary = test_results.get("summary", {})
        print(f"  Test frameworks found: {len(summary.get('frameworks_used', []))}")
        print(f"  Total tests: {summary.get('total_tests', 0)}")
        if summary.get("total_tests", 0) > 0:
            print(f"  Success rate: {summary.get('success_rate', 0):.1f}%")

        # Phase 7: Claim Verification
        print("\n🎯 Phase 7: Claim Verification")
        claim_verifier = ClaimVerifier(str(self.repo_path))

        # Get claims from documentation analysis
        all_claims = []
        for claim_type, claims in doc_results.get("claims_by_type", {}).items():
            for claim in claims:
                claim["type"] = claim_type
                all_claims.append(claim)

        if all_claims:
            verification_results = claim_verifier.verify_claims(all_claims)
            self.results["claim_verification"] = verification_results
            print(f"  Claims verified: {verification_results['summary']['verified']}")
            print(f"  Claims failed: {verification_results['summary']['failed']}")
            print(f"  Claims inconclusive: {verification_results['summary']['inconclusive']}")
        else:
            print("  No claims to verify")

        # Phase 8: Report Generation
        print("\n📝 Phase 8: Report Generation")
        report_generator = ReportGenerator(
            results_dir=self.config.get("output_dir"),
            sanitize=self.config.get("sanitize", True),
            redact_level=self.config.get("redact_level", "medium"),
        )
        generated_reports = report_generator.generate_report(
            complexity_results,
            {**static_results, **verification_results},
            test_results,
            str(self.repo_path),
            self.config.get("output_format", "all"),
            git_results,
        )
        self.results["reports"] = generated_reports

        print("  Generated reports:")
        for format_type, path in generated_reports.items():
            display_path = get_safe_path(path) if self.config.get("sanitize", True) else path
            print(f"    - {format_type}: {display_path}")

        # Print summary
        print("\n" + "=" * 60)
        summary_text = SummaryReporter.generate_console_summary(
            complexity_results, {**static_results, **verification_results}, test_results
        )
        print(summary_text)

        return self.results


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Vibe Verifier - Comprehensive code analysis and verification tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vibe-verifier /path/to/repo
  vibe-verifier /path/to/repo --output-format html
  vibe-verifier /path/to/repo --config config.json
  vibe-verifier /path/to/repo --skip-tests --quick
        """,
    )

    parser.add_argument("repo_path", help="Path to the repository to analyze")

    parser.add_argument(
        "--output-format",
        choices=["all", "markdown", "html", "json", "pdf"],
        default="all",
        help="Output format for reports (default: all)",
    )

    parser.add_argument("--config", help="Path to configuration file (JSON)")

    parser.add_argument("--skip-tests", action="store_true", help="Skip test execution phase")

    parser.add_argument(
        "--skip-verification", action="store_true", help="Skip formal verification phase"
    )

    parser.add_argument(
        "--quick", action="store_true", help="Quick analysis (skip time-consuming checks)"
    )

    parser.add_argument("--output-dir", help="Directory to save reports (default: ./reports)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--no-sanitize",
        action="store_true",
        help="Disable sanitization of sensitive information in reports",
    )

    parser.add_argument(
        "--redact-level",
        choices=["low", "medium", "high"],
        default="medium",
        help="Level of redaction for sensitive info (default: medium)",
    )

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        try:
            with open(args.config, "r") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Error loading config file: {e}")
            sys.exit(1)

    # Override config with CLI arguments
    config["output_format"] = args.output_format
    config["skip_tests"] = args.skip_tests
    config["skip_verification"] = args.skip_verification
    config["quick_mode"] = args.quick
    config["verbose"] = args.verbose
    config["sanitize"] = not args.no_sanitize
    config["redact_level"] = args.redact_level

    if args.output_dir:
        config["output_dir"] = args.output_dir

    # Run analysis
    try:
        verifier = VibeVerifier(args.repo_path, config)
        results = verifier.run_analysis()

        # Save full results if requested
        if config.get("save_raw_results", False):
            results_file = Path(config.get("output_dir", "reports")) / "raw_results.json"
            results_file.parent.mkdir(exist_ok=True)

            # Sanitize results before saving if enabled
            save_results = results
            if config.get("sanitize", True):
                save_results = sanitize_results(results, config.get("redact_level", "medium"))

            with open(results_file, "w") as f:
                json.dump(save_results, f, indent=2, default=str)

            safe_path = (
                get_safe_path(results_file) if config.get("sanitize", True) else results_file
            )
            print(f"\nRaw results saved to: {safe_path}")

        # Exit with appropriate code
        if results.get("tests", {}).get("summary", {}).get("failed", 0) > 0:
            sys.exit(1)  # Tests failed
        elif results.get("claim_verification", {}).get("summary", {}).get("failed", 0) > 0:
            sys.exit(2)  # Claims failed verification
        else:
            sys.exit(0)  # Success

    except Exception as e:
        print(f"\n❌ Error: {e}")
        if config.get("verbose"):
            import traceback

            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
