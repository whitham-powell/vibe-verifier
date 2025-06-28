"""Tests for security sanitizer."""

from pathlib import Path

from src.utils.security import SecuritySanitizer, get_safe_path, sanitize_results


class TestSecuritySanitizer:
    """Test security sanitizer functionality."""

    def test_sanitize_paths(self):
        """Test path sanitization."""
        sanitizer = SecuritySanitizer(redact_level="medium")

        # Test Unix paths
        assert sanitizer.sanitize_path("/home/johndoe/project") == "/home/USER/project"
        assert sanitizer.sanitize_path("/Users/janedoe/Documents") == "/home/USER/Documents"

        # Test Windows paths
        assert sanitizer.sanitize_path("C:\\Users\\johndoe\\project") == "C:\\Users\\USER\\project"

        # Test with actual home directory
        home_path = str(Path.home() / "test" / "file.py")
        sanitized = sanitizer.sanitize_path(home_path)
        assert str(Path.home()) not in sanitized
        assert sanitized.startswith("~") or "USER" in sanitized

    def test_sanitize_emails(self):
        """Test email sanitization."""
        # Low level - partial obfuscation
        sanitizer_low = SecuritySanitizer(redact_level="low")
        assert sanitizer_low.sanitize_email("john.doe@example.com") == "j***e@example.com"

        # Medium level - hash local part
        sanitizer_med = SecuritySanitizer(redact_level="medium")
        result = sanitizer_med.sanitize_email("john.doe@example.com")
        assert "@example.com" in result
        assert "john.doe" not in result

        # High level - full redaction
        sanitizer_high = SecuritySanitizer(redact_level="high")
        assert sanitizer_high.sanitize_email("john.doe@example.com") == "[EMAIL_REDACTED]"

    def test_sanitize_ip_addresses(self):
        """Test IP address sanitization."""
        # Low level - keep private IPs
        sanitizer_low = SecuritySanitizer(redact_level="low")
        assert sanitizer_low.sanitize_ip("192.168.1.100") == "192.168.1.100"
        assert sanitizer_low.sanitize_ip("8.8.8.8") == "8.8.8.8"  # Common DNS server, safe to keep
        assert sanitizer_low.sanitize_ip("93.184.216.34") == "93.184.XXX.XXX"  # Example public IP

        # Medium level - keep private IPs, partial redaction for public
        sanitizer_med = SecuritySanitizer(redact_level="medium")
        assert sanitizer_med.sanitize_ip("192.168.1.100") == "192.168.1.100"  # Private IP kept
        assert sanitizer_med.sanitize_ip("93.184.216.34") == "93.184.XXX.XXX"  # Public IP redacted

        # High level - full redaction
        sanitizer_high = SecuritySanitizer(redact_level="high")
        assert sanitizer_high.sanitize_ip("8.8.8.8") == "[IP_REDACTED]"

    def test_sanitize_secrets(self):
        """Test secret sanitization."""
        sanitizer = SecuritySanitizer()

        # API keys
        text = 'api_key="sk-1234567890abcdefghijklmnop"'
        assert "sk-1234567890" not in sanitizer.sanitize_secrets(text)
        assert "[REDACTED]" in sanitizer.sanitize_secrets(text)

        # AWS keys
        text = "AKIAIOSFODNN7EXAMPLE"
        assert "[AWS_ACCESS_KEY_REDACTED]" in sanitizer.sanitize_secrets(text)

        # SSH keys
        text = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAklOUpkDHrfHY17SbrmTIpy"
        assert "[SSH_KEY_REDACTED]" in sanitizer.sanitize_secrets(text)

        # URLs with credentials
        text = "https://user:password@example.com/path"
        result = sanitizer.sanitize_secrets(text)
        assert "password" not in result
        assert "[CREDENTIALS_REDACTED]" in result

    def test_sanitize_dict(self):
        """Test dictionary sanitization."""
        sanitizer = SecuritySanitizer(redact_level="medium")

        data = {
            "path": "/home/johndoe/project/file.py",
            "email": "john.doe@example.com",
            "config": {"api_key": "sk-secret123456789", "host": "192.168.1.100"},
            "count": 42,
            "enabled": True,
        }

        result = sanitizer.sanitize_dict(data)

        # Check sanitization
        assert "/home/johndoe" not in str(result)
        assert "john.doe@example.com" not in str(result)
        assert "sk-secret123456789" not in str(result)
        assert result["count"] == 42  # Numbers preserved
        assert result["enabled"] is True  # Booleans preserved

    def test_sanitize_report(self):
        """Test full report sanitization."""
        report = {
            "metadata": {"path": "/home/johndoe/projects/test", "author": "john.doe@company.com"},
            "results": [
                {"file": "/home/johndoe/projects/test/main.py", "issues": ["No issues found"]}
            ],
            "config": {"token": "github_pat_11EXAMPLE"},
        }

        sanitized = sanitize_results(report, redact_level="high")

        # Verify sanitization
        report_str = str(sanitized)
        assert "johndoe" not in report_str
        assert "john.doe@company.com" not in report_str
        assert "github_pat_11EXAMPLE" not in report_str
        assert "[EMAIL_REDACTED]" in report_str

    def test_get_safe_path(self):
        """Test safe path helper."""
        path = "/home/username/project/file.py"
        safe = get_safe_path(path)
        assert "username" not in safe
        assert "USER" in safe or safe.startswith("~")

    def test_hostname_sanitization(self):
        """Test hostname sanitization."""
        sanitizer = SecuritySanitizer(redact_level="medium")

        text = 'hostname="my-machine.local" machine=dev-laptop'
        result = sanitizer.sanitize_hostname(text)
        assert "my-machine.local" not in result
        assert "dev-laptop" not in result
        assert "[HOSTNAME]" in result

    def test_sanitize_mac_addresses(self):
        """Test MAC address sanitization."""
        # Low level - no redaction
        sanitizer_low = SecuritySanitizer(redact_level="low")
        assert sanitizer_low.sanitize_mac("00:11:22:33:44:55") == "00:11:22:33:44:55"

        # Medium level - partial redaction (keep vendor prefix)
        sanitizer_med = SecuritySanitizer(redact_level="medium")
        assert sanitizer_med.sanitize_mac("00:11:22:33:44:55") == "00:11:22:XX:XX:XX"
        assert sanitizer_med.sanitize_mac("00-11-22-33-44-55") == "00-11-22-XX-XX-XX"
        assert sanitizer_med.sanitize_mac("00:00:00:00:00:00") == "00:00:00:00:00:00"  # Safe MAC

        # High level - full redaction
        sanitizer_high = SecuritySanitizer(redact_level="high")
        assert sanitizer_high.sanitize_mac("00:11:22:33:44:55") == "[MAC_REDACTED]"
        assert (
            sanitizer_high.sanitize_mac("FF:FF:FF:FF:FF:FF") == "[MAC_REDACTED]"
        )  # Even safe MACs in high mode

    def test_preserve_structure(self):
        """Test that sanitization preserves data structure."""
        sanitizer = SecuritySanitizer()

        # Test nested structure
        data = {
            "list": [1, 2, {"nested": "value"}],
            "dict": {"key": "value"},
            "string": "text",
            "number": 123,
            "bool": False,
            "none": None,
        }

        result = sanitizer.sanitize_dict(data)

        # Structure should be preserved
        assert isinstance(result["list"], list)
        assert len(result["list"]) == 3
        assert isinstance(result["dict"], dict)
        assert result["number"] == 123
        assert result["bool"] is False
        assert result["none"] is None
