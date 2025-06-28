"""Security utilities for sanitizing and obfuscating sensitive information."""

import hashlib
import os
import re
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class SecuritySanitizer:
    """Sanitizes and obfuscates potentially sensitive information from reports."""

    # Patterns for sensitive information
    PATTERNS = {
        # File paths with usernames
        "user_paths": re.compile(r"/(?:home|Users)/([^/]+)/", re.IGNORECASE),
        "windows_paths": re.compile(r"C:\\Users\\([^\\]+)\\", re.IGNORECASE),
        # Email addresses
        "emails": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        # IP addresses (IPv4)
        "ipv4": re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
        # MAC addresses
        "mac": re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"),
        # Common API key patterns
        "api_keys": re.compile(
            r'(?:["\']?)(?:api[_-]?key|token|secret)["\']?\s*[:=]\s*'
            r'["\']?([a-zA-Z0-9_\-]{10,})["\']?',
            re.IGNORECASE,
        ),
        "standalone_secrets": re.compile(
            r"\b(sk-[a-zA-Z0-9_\-]{10,}|pk_[a-zA-Z0-9_\-]{10,}|[a-zA-Z0-9]{32,})\b"
        ),
        # SSH keys
        "ssh_keys": re.compile(r"ssh-(?:rsa|dss|ed25519) [A-Za-z0-9+/=]+"),
        # AWS keys
        "aws_access": re.compile(r"AKIA[0-9A-Z]{16}"),
        "aws_secret": re.compile(
            r"(?:aws_secret_access_key|aws_secret_key|secret_key)\s*=\s*[A-Za-z0-9/+=]{40}",
            re.IGNORECASE,
        ),
        # GitHub tokens
        "github_token": re.compile(r"gh[ps]_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]+"),
        # URLs with potential credentials
        "url_creds": re.compile(r"(?:https?|ftp)://[^:]+:[^@]+@[^/]+"),
        # Machine names/hostnames
        "hostnames": re.compile(
            r'(?:hostname|machine|computer)["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.]+)["\']?',
            re.IGNORECASE,
        ),
    }

    def __init__(self, redact_level: str = "medium"):
        """Initialize the sanitizer.

        Args:
            redact_level: Level of redaction - "low", "medium", or "high"
        """
        self.redact_level = redact_level
        self._username: Optional[str] = None
        self._hostname: Optional[str] = None
        self._home_dir: Optional[str] = None

    def _get_system_info(self) -> None:
        """Get system information to redact."""
        if self._username is None:
            try:
                self._username = os.getenv("USER") or os.getenv("USERNAME")
                self._hostname = socket.gethostname()
                self._home_dir = str(Path.home())
            except Exception:
                # If we can't get system info, that's okay
                self._username = ""
                self._hostname = ""
                self._home_dir = ""

    def sanitize_path(self, path: str) -> str:
        """Sanitize file paths to remove user-specific information."""
        self._get_system_info()

        # Replace home directory with generic placeholder
        if self._home_dir and self._home_dir in path:
            path = path.replace(self._home_dir, "~")

        # Replace username in paths
        if self._username:
            path = re.sub(f"/(?:home|Users)/{re.escape(self._username)}/", "/home/USER/", path)
            path = re.sub(
                f"C:\\\\Users\\\\{re.escape(self._username)}\\\\", r"C:\\Users\\USER\\", path
            )

        # Use regex patterns as fallback
        path = self.PATTERNS["user_paths"].sub("/home/USER/", path)
        path = self.PATTERNS["windows_paths"].sub(r"C:\\Users\\USER\\", path)

        return path

    def sanitize_email(self, text: str) -> str:
        """Replace email addresses with hashed versions."""

        def hash_email(match) -> str:
            email = match.group()
            if self.redact_level == "high":
                return "[EMAIL_REDACTED]"
            elif self.redact_level == "medium":
                # Keep domain, hash local part
                local, domain = email.split("@")
                hashed = hashlib.sha256(local.encode()).hexdigest()[:8]
                return f"{hashed}@{domain}"
            else:
                # Just obfuscate slightly
                parts = email.split("@")
                if len(parts) == 2:
                    local = parts[0]
                    if len(local) > 2:
                        return f"{local[0]}***{local[-1]}@{parts[1]}"
            return email

        return self.PATTERNS["emails"].sub(hash_email, text)

    def sanitize_ip(self, text: str) -> str:
        """Sanitize IP addresses."""

        def replace_ip(match) -> str:
            ip = match.group()
            # Common test/example IPs that are safe to keep (except in high mode)
            safe_ips = ["127.0.0.1", "0.0.0.0", "255.255.255.255", "8.8.8.8", "1.1.1.1"]
            if ip in safe_ips and self.redact_level != "high":
                return ip

            # Don't sanitize localhost or private IPs in low/medium mode
            if self.redact_level in ["low", "medium"]:
                if ip.startswith(("127.", "192.168.", "10.", "172.")):
                    return ip

            if self.redact_level == "high":
                return "[IP_REDACTED]"
            else:
                # Partially redact public IPs
                parts = ip.split(".")
                if len(parts) == 4:
                    return f"{parts[0]}.{parts[1]}.XXX.XXX"
            return ip

        return self.PATTERNS["ipv4"].sub(replace_ip, text)

    def sanitize_mac(self, text: str) -> str:
        """Sanitize MAC addresses."""

        def replace_mac(match) -> str:
            mac = match.group()
            # Common test/documentation MACs that are safe to keep (except in high mode)
            safe_macs = [
                "00:00:00:00:00:00",
                "FF:FF:FF:FF:FF:FF",
                "00-00-00-00-00-00",
                "ff-ff-ff-ff-ff-ff",
            ]
            if mac.upper() in [m.upper() for m in safe_macs] and self.redact_level != "high":
                return mac

            if self.redact_level == "high":
                return "[MAC_REDACTED]"
            elif self.redact_level == "medium":
                # Keep vendor prefix (first 3 octets), redact device ID
                parts = mac.split(":") if ":" in mac else mac.split("-")
                sep = ":" if ":" in mac else "-"
                if len(parts) == 6:
                    return f"{parts[0]}{sep}{parts[1]}{sep}{parts[2]}{sep}XX{sep}XX{sep}XX"
            return mac

        return self.PATTERNS["mac"].sub(replace_mac, text)

    def sanitize_secrets(self, text: str) -> str:
        """Remove API keys, tokens, and other secrets."""

        # API keys
        def replace_api_key(match) -> str:
            full_match = match.group()
            # Find the delimiter (: or =)
            if "=" in full_match:
                key_part = full_match.split("=")[0]
                return f"{key_part}=[REDACTED]"
            else:
                key_part = full_match.split(":")[0]
                return f'{key_part}: "[REDACTED]"'

        text = self.PATTERNS["api_keys"].sub(replace_api_key, text)

        # SSH keys (before standalone secrets to take precedence)
        text = self.PATTERNS["ssh_keys"].sub("[SSH_KEY_REDACTED]", text)

        # Standalone secrets that look like API keys
        text = self.PATTERNS["standalone_secrets"].sub("[SECRET_REDACTED]", text)

        # GitHub tokens
        text = self.PATTERNS["github_token"].sub("[GITHUB_TOKEN_REDACTED]", text)

        # AWS keys
        text = self.PATTERNS["aws_access"].sub("[AWS_ACCESS_KEY_REDACTED]", text)

        def replace_aws_secret(match) -> str:
            full_match = match.group()
            if "=" in full_match:
                key_part = full_match.split("=")[0]
                return f"{key_part}=[AWS_SECRET_REDACTED]"
            else:
                key_part = full_match.split(":")[0]
                return f'{key_part}: "[AWS_SECRET_REDACTED]"'

        text = self.PATTERNS["aws_secret"].sub(replace_aws_secret, text)

        # URLs with credentials
        text = self.PATTERNS["url_creds"].sub(
            lambda m: re.sub(r"://[^@]+@", "://[CREDENTIALS_REDACTED]@", m.group()), text
        )

        return text

    def sanitize_hostname(self, text: str) -> str:
        """Sanitize machine names and hostnames."""
        self._get_system_info()

        # Replace actual hostname if we know it
        if self._hostname:
            text = text.replace(self._hostname, "[HOSTNAME]")

        # Replace hostname patterns
        if self.redact_level != "low":

            def replace_hostname(match) -> str:
                full_match = match.group()
                # Extract the key part (hostname, machine, etc)
                if "=" in full_match:
                    key_part = full_match.split("=")[0]
                    return f'{key_part}="[HOSTNAME]"'
                elif ":" in full_match:
                    key_part = full_match.split(":")[0]
                    return f'{key_part}: "[HOSTNAME]"'
                else:
                    return "[HOSTNAME]"

            text = self.PATTERNS["hostnames"].sub(replace_hostname, text)

        return text

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize a dictionary."""
        sanitized: Dict[str, Any] = {}

        for key, value in data.items():
            # Sanitize the key itself
            sanitized_key = self.sanitize_text(str(key)) if isinstance(key, str) else key

            # Sanitize the value based on type
            if isinstance(value, dict):
                sanitized[sanitized_key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[sanitized_key] = self.sanitize_list(value)
            elif isinstance(value, str):
                sanitized[sanitized_key] = self.sanitize_text(value)
            elif isinstance(value, (int, float, bool, type(None))):
                sanitized[sanitized_key] = value
            else:
                # Convert to string and sanitize
                sanitized[sanitized_key] = self.sanitize_text(str(value))

        return sanitized

    def sanitize_list(self, data: List[Any]) -> List[Any]:
        """Recursively sanitize a list."""
        sanitized: List[Any] = []

        for item in data:
            if isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item))
            elif isinstance(item, str):
                sanitized.append(self.sanitize_text(item))
            elif isinstance(item, (int, float, bool, type(None))):
                sanitized.append(item)
            else:
                sanitized.append(self.sanitize_text(str(item)))

        return sanitized

    def sanitize_text(self, text: str) -> str:
        """Sanitize a text string by applying all sanitization rules."""
        if not text:
            return text

        # Apply sanitizations in order of importance
        text = self.sanitize_secrets(text)  # First remove secrets
        text = self.sanitize_path(text)  # Then paths
        text = self.sanitize_email(text)  # Then emails
        text = self.sanitize_ip(text)  # Then IPs
        text = self.sanitize_mac(text)  # Then MACs
        text = self.sanitize_hostname(text)  # Finally hostnames

        return text

    def sanitize_report(self, report_data: Union[Dict, List, str]) -> Union[Dict, List, str]:
        """Sanitize an entire report structure."""
        if isinstance(report_data, dict):
            return self.sanitize_dict(report_data)
        elif isinstance(report_data, list):
            return self.sanitize_list(report_data)
        else:  # isinstance(report_data, str)
            return self.sanitize_text(report_data)


def get_safe_path(path: Union[str, Path]) -> str:
    """Get a sanitized version of a file path for display."""
    sanitizer = SecuritySanitizer(redact_level="medium")
    return sanitizer.sanitize_path(str(path))


def sanitize_results(results: Dict[str, Any], redact_level: str = "medium") -> Dict[str, Any]:
    """Sanitize analysis results before saving or displaying."""
    sanitizer = SecuritySanitizer(redact_level=redact_level)
    # We know results is a dict, so the return will be a dict
    sanitized = sanitizer.sanitize_report(results)
    assert isinstance(sanitized, dict)  # Type narrowing for mypy
    return sanitized
