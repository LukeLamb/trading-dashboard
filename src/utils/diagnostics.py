"""
System Diagnostics and Debugging Tools for Trading Dashboard.

This module provides comprehensive diagnostic capabilities including:
- System diagnostic interface
- Network connectivity testing
- Configuration validation tools
- Performance profiling tools
- Health check diagnostics
- Debug mode utilities
"""

import asyncio
import json
import os
import time
import socket
import ssl
import subprocess
import platform
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import requests

    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from .logging import get_logger
from .config import get_config_manager

# Constants
SYSTEM_RESOURCES_NAME = "System Resources"
DEPENDENCIES_CHECK_NAME = "Dependencies Check"


class DiagnosticStatus(Enum):
    """Diagnostic test status."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"
    ERROR = "error"


class DiagnosticCategory(Enum):
    """Diagnostic category types."""

    SYSTEM = "system"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    DEPENDENCIES = "dependencies"
    SECURITY = "security"
    AGENTS = "agents"


@dataclass
class DiagnosticResult:
    """Individual diagnostic test result."""

    test_id: str
    name: str
    category: DiagnosticCategory
    status: DiagnosticStatus
    message: str
    details: Dict[str, Any]
    recommendations: List[str]
    execution_time: float
    timestamp: datetime


@dataclass
class SystemInfo:
    """System information."""

    platform: str
    platform_version: str
    python_version: str
    architecture: str
    cpu_count: int
    memory_total: str
    memory_available: str
    disk_space: Dict[str, str]
    network_interfaces: List[Dict[str, str]]
    environment_variables: Dict[str, str]


class NetworkDiagnostics:
    """Network connectivity and diagnostics."""

    def __init__(self):
        self.logger = get_logger()

    def test_internet_connectivity(self) -> DiagnosticResult:
        """Test basic internet connectivity."""
        start_time = time.time()

        try:
            # Test DNS resolution
            socket.gethostbyname("google.com")

            # Test HTTP connectivity if requests available
            if HAS_REQUESTS:
                response = requests.get("https://httpbin.org/status/200", timeout=10)
                if response.status_code == 200:
                    status = DiagnosticStatus.PASS
                    message = "Internet connectivity is working"
                else:
                    status = DiagnosticStatus.WARNING
                    message = f"HTTP request returned status {response.status_code}"
            else:
                status = DiagnosticStatus.PASS
                message = "DNS resolution working (HTTP test skipped - requests not available)"

            return DiagnosticResult(
                test_id="network_internet",
                name="Internet Connectivity",
                category=DiagnosticCategory.NETWORK,
                status=status,
                message=message,
                details={"dns_resolution": "OK"},
                recommendations=[],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id="network_internet",
                name="Internet Connectivity",
                category=DiagnosticCategory.NETWORK,
                status=DiagnosticStatus.FAIL,
                message=f"Internet connectivity test failed: {str(e)}",
                details={"error": str(e)},
                recommendations=[
                    "Check internet connection",
                    "Verify DNS settings",
                    "Check firewall configuration",
                ],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def test_port_connectivity(
        self, host: str, port: int, timeout: int = 5
    ) -> DiagnosticResult:
        """Test connectivity to specific host and port."""
        start_time = time.time()
        test_id = f"network_port_{host}_{port}"

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                status = DiagnosticStatus.PASS
                message = f"Successfully connected to {host}:{port}"
                recommendations = []
            else:
                status = DiagnosticStatus.FAIL
                message = f"Failed to connect to {host}:{port}"
                recommendations = [
                    f"Check if service is running on {host}:{port}",
                    "Verify firewall settings",
                    "Check network routing",
                ]

            return DiagnosticResult(
                test_id=test_id,
                name=f"Port Connectivity - {host}:{port}",
                category=DiagnosticCategory.NETWORK,
                status=status,
                message=message,
                details={"host": host, "port": port, "result_code": result},
                recommendations=recommendations,
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id=test_id,
                name=f"Port Connectivity - {host}:{port}",
                category=DiagnosticCategory.NETWORK,
                status=DiagnosticStatus.ERROR,
                message=f"Error testing connectivity: {str(e)}",
                details={"host": host, "port": port, "error": str(e)},
                recommendations=["Check network configuration"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def test_ssl_certificate(self, hostname: str, port: int = 443) -> DiagnosticResult:
        """Test SSL certificate validity."""
        start_time = time.time()
        test_id = f"network_ssl_{hostname}"

        try:
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    if not cert:
                        raise ValueError("No certificate found")

                    # Check certificate expiration
                    not_after_str = cert.get("notAfter")
                    if not not_after_str:
                        raise ValueError("Certificate expiration date not found")

                    not_after = datetime.strptime(
                        str(not_after_str), "%b %d %H:%M:%S %Y %Z"
                    )
                    days_until_expiry = (not_after - datetime.now()).days

                    if days_until_expiry > 30:
                        status = DiagnosticStatus.PASS
                        message = f"SSL certificate valid, expires in {days_until_expiry} days"
                        recommendations = []
                    elif days_until_expiry > 7:
                        status = DiagnosticStatus.WARNING
                        message = (
                            f"SSL certificate expires soon ({days_until_expiry} days)"
                        )
                        recommendations = ["Monitor certificate expiration"]
                    else:
                        status = DiagnosticStatus.FAIL
                        message = f"SSL certificate expires very soon ({days_until_expiry} days)"
                        recommendations = ["Renew SSL certificate immediately"]

                    # Safely extract certificate details
                    subject_dict = {}
                    issuer_dict = {}

                    subject = cert.get("subject", [])
                    if subject:
                        for item in subject:
                            if (
                                isinstance(item, tuple)
                                and len(item) > 0
                                and isinstance(item[0], tuple)
                                and len(item[0]) >= 2
                            ):
                                subject_dict[item[0][0]] = item[0][1]

                    issuer = cert.get("issuer", [])
                    if issuer:
                        for item in issuer:
                            if (
                                isinstance(item, tuple)
                                and len(item) > 0
                                and isinstance(item[0], tuple)
                                and len(item[0]) >= 2
                            ):
                                issuer_dict[item[0][0]] = item[0][1]

                    return DiagnosticResult(
                        test_id=test_id,
                        name=f"SSL Certificate - {hostname}",
                        category=DiagnosticCategory.SECURITY,
                        status=status,
                        message=message,
                        details={
                            "hostname": hostname,
                            "subject": subject_dict,
                            "issuer": issuer_dict,
                            "expires": str(not_after_str),
                            "days_until_expiry": days_until_expiry,
                        },
                        recommendations=recommendations,
                        execution_time=time.time() - start_time,
                        timestamp=datetime.now(),
                    )

        except Exception as e:
            return DiagnosticResult(
                test_id=test_id,
                name=f"SSL Certificate - {hostname}",
                category=DiagnosticCategory.SECURITY,
                status=DiagnosticStatus.ERROR,
                message=f"SSL certificate test failed: {str(e)}",
                details={"hostname": hostname, "error": str(e)},
                recommendations=["Check SSL configuration and connectivity"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )


class ConfigurationDiagnostics:
    """Configuration validation and diagnostics."""

    def __init__(self):
        self.logger = get_logger()

    def validate_configuration_files(self) -> DiagnosticResult:
        """Validate configuration files."""
        start_time = time.time()

        try:
            config_manager = get_config_manager()

            # Test configuration loading
            dashboard_config = config_manager.get_dashboard_config()
            logging_config = config_manager.get_logging_config()

            # Validate required fields
            issues = []
            recommendations = []

            # Dashboard validation
            if not dashboard_config.title:
                issues.append("Dashboard title is empty")
            if dashboard_config.port <= 0 or dashboard_config.port > 65535:
                issues.append(f"Invalid dashboard port: {dashboard_config.port}")

            # Logging validation
            if not Path(logging_config.file_path).parent.exists():
                issues.append(
                    f"Logging directory does not exist: {Path(logging_config.file_path).parent}"
                )
                recommendations.append("Create logging directory")

            # Agents validation - get individual agent configs
            enabled_agents = []
            try:
                market_data_config = config_manager.get_agent_config("market_data")
                if (
                    market_data_config
                    and hasattr(market_data_config, "enabled")
                    and market_data_config.enabled
                ):
                    enabled_agents.append("market_data")
            except Exception:
                pass

            if not enabled_agents:
                issues.append("No agents are enabled")
                recommendations.append("Enable at least one trading agent")

            status = DiagnosticStatus.PASS if not issues else DiagnosticStatus.WARNING
            message = (
                "Configuration validation passed"
                if not issues
                else f"Found {len(issues)} configuration issues"
            )

            return DiagnosticResult(
                test_id="config_validation",
                name="Configuration Validation",
                category=DiagnosticCategory.CONFIGURATION,
                status=status,
                message=message,
                details={
                    "issues": issues,
                    "enabled_agents": enabled_agents,
                    "dashboard_port": dashboard_config.port,
                    "log_file": logging_config.file_path,
                },
                recommendations=recommendations,
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id="config_validation",
                name="Configuration Validation",
                category=DiagnosticCategory.CONFIGURATION,
                status=DiagnosticStatus.ERROR,
                message=f"Configuration validation failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check configuration file syntax and structure"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def test_file_permissions(self) -> DiagnosticResult:
        """Test file system permissions."""
        start_time = time.time()

        try:
            issues = []
            recommendations = []

            # Test config directory
            config_dir = Path("config")
            if not config_dir.exists():
                issues.append("Config directory does not exist")
            elif not os.access(config_dir, os.R_OK):
                issues.append("Config directory is not readable")
                recommendations.append("Fix config directory permissions")

            # Test logs directory
            logs_dir = Path("logs")
            if not logs_dir.exists():
                try:
                    logs_dir.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    issues.append("Cannot create logs directory")
                    recommendations.append("Fix directory creation permissions")
            elif not os.access(logs_dir, os.W_OK):
                issues.append("Logs directory is not writable")
                recommendations.append("Fix logs directory write permissions")

            # Test data directory
            data_dir = Path("data")
            if data_dir.exists() and not os.access(data_dir, os.W_OK):
                issues.append("Data directory is not writable")
                recommendations.append("Fix data directory write permissions")

            status = DiagnosticStatus.PASS if not issues else DiagnosticStatus.WARNING
            message = (
                "File permissions OK"
                if not issues
                else f"Found {len(issues)} permission issues"
            )

            return DiagnosticResult(
                test_id="file_permissions",
                name="File Permissions",
                category=DiagnosticCategory.SYSTEM,
                status=status,
                message=message,
                details={"issues": issues},
                recommendations=recommendations,
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id="file_permissions",
                name="File Permissions",
                category=DiagnosticCategory.SYSTEM,
                status=DiagnosticStatus.ERROR,
                message=f"File permission test failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check file system permissions"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )


class PerformanceDiagnostics:
    """Performance monitoring and profiling."""

    def __init__(self):
        self.logger = get_logger()

    def check_system_resources(self) -> DiagnosticResult:
        """Check system resource usage."""
        start_time = time.time()

        try:
            if not HAS_PSUTIL:
                return DiagnosticResult(
                    test_id="system_resources",
                    name=SYSTEM_RESOURCES_NAME,
                    category=DiagnosticCategory.PERFORMANCE,
                    status=DiagnosticStatus.SKIP,
                    message="System resource check skipped (psutil not available)",
                    details={},
                    recommendations=["Install psutil for system monitoring"],
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now(),
                )

            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            issues = []
            recommendations = []

            # Check CPU usage
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
                recommendations.append("Investigate high CPU usage processes")
            elif cpu_percent > 70:
                issues.append(f"Elevated CPU usage: {cpu_percent:.1f}%")

            # Check memory usage
            memory_percent = memory.percent
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")
                recommendations.append("Free up memory or add more RAM")
            elif memory_percent > 75:
                issues.append(f"Elevated memory usage: {memory_percent:.1f}%")

            # Check disk usage
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > 95:
                issues.append(f"Very low disk space: {disk_percent:.1f}% used")
                recommendations.append("Free up disk space immediately")
            elif disk_percent > 85:
                issues.append(f"Low disk space: {disk_percent:.1f}% used")
                recommendations.append("Consider freeing up disk space")

            if cpu_percent > 90 or memory_percent > 90 or disk_percent > 95:
                status = DiagnosticStatus.FAIL
            elif cpu_percent > 70 or memory_percent > 75 or disk_percent > 85:
                status = DiagnosticStatus.WARNING
            else:
                status = DiagnosticStatus.PASS

            message = (
                "System resources OK"
                if not issues
                else f"Found {len(issues)} resource issues"
            )

            return DiagnosticResult(
                test_id="system_resources",
                name=SYSTEM_RESOURCES_NAME,
                category=DiagnosticCategory.PERFORMANCE,
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk_percent,
                    "disk_free_gb": disk.free / (1024**3),
                    "issues": issues,
                },
                recommendations=recommendations,
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id="system_resources",
                name=SYSTEM_RESOURCES_NAME,
                category=DiagnosticCategory.PERFORMANCE,
                status=DiagnosticStatus.ERROR,
                message=f"System resource check failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check system monitoring tools"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def performance_benchmark(self) -> DiagnosticResult:
        """Run basic performance benchmark."""
        start_time = time.time()

        try:
            # CPU benchmark - simple calculation
            cpu_start = time.time()
            result = sum(i * i for i in range(100000))
            cpu_time = time.time() - cpu_start

            # Memory benchmark - list operations
            memory_start = time.time()
            test_list = list(range(100000))
            test_list.sort()
            memory_time = time.time() - memory_start

            # File I/O benchmark - write/read test
            io_start = time.time()
            test_file = Path("logs/benchmark_test.tmp")
            test_data = "x" * 1000 * 1000  # 1MB

            # Write test
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_data)

            # Read test
            with open(test_file, "r", encoding="utf-8") as f:
                _ = f.read()  # Read but don't store

            # Cleanup
            test_file.unlink(missing_ok=True)
            io_time = time.time() - io_start

            # Evaluate performance
            issues = []
            recommendations = []

            if cpu_time > 0.1:  # 100ms for simple calculation
                issues.append(f"Slow CPU performance: {cpu_time*1000:.1f}ms")
                recommendations.append("Check CPU load and background processes")

            if memory_time > 0.05:  # 50ms for list operations
                issues.append(f"Slow memory operations: {memory_time*1000:.1f}ms")
                recommendations.append("Check memory usage and swap activity")

            if io_time > 0.5:  # 500ms for 1MB file operations
                issues.append(f"Slow file I/O: {io_time*1000:.1f}ms")
                recommendations.append("Check disk performance and available space")

            status = DiagnosticStatus.PASS if not issues else DiagnosticStatus.WARNING
            message = (
                "Performance benchmark completed"
                if not issues
                else "Performance issues detected"
            )

            return DiagnosticResult(
                test_id="performance_benchmark",
                name="Performance Benchmark",
                category=DiagnosticCategory.PERFORMANCE,
                status=status,
                message=message,
                details={
                    "cpu_time_ms": cpu_time * 1000,
                    "memory_time_ms": memory_time * 1000,
                    "io_time_ms": io_time * 1000,
                    "calculation_result": result,
                    "issues": issues,
                },
                recommendations=recommendations,
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id="performance_benchmark",
                name="Performance Benchmark",
                category=DiagnosticCategory.PERFORMANCE,
                status=DiagnosticStatus.ERROR,
                message=f"Performance benchmark failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check system stability and resources"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )


class SystemDiagnosticsManager:
    """Main system diagnostics coordinator."""

    def __init__(self):
        self.logger = get_logger()
        self.network_diagnostics = NetworkDiagnostics()
        self.config_diagnostics = ConfigurationDiagnostics()
        self.performance_diagnostics = PerformanceDiagnostics()
        self.test_history: List[DiagnosticResult] = []

    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Run complete system diagnostics."""
        self.logger.info("Starting full system diagnostics")
        start_time = time.time()

        results = []

        # Network tests
        results.append(self.network_diagnostics.test_internet_connectivity())

        # Test agent endpoints if configured
        try:
            config_manager = get_config_manager()

            # Test market data agent
            try:
                market_data_config = config_manager.get_agent_config("market_data")
                if (
                    market_data_config
                    and hasattr(market_data_config, "enabled")
                    and market_data_config.enabled
                    and hasattr(market_data_config, "url")
                ):
                    import urllib.parse

                    parsed = urllib.parse.urlparse(market_data_config.url)
                    results.append(
                        self.network_diagnostics.test_port_connectivity(
                            parsed.hostname or "localhost", parsed.port or 80
                        )
                    )
            except Exception:
                pass  # Skip if agent config not found

        except Exception as e:
            self.logger.error(f"Failed to test agent connectivity: {e}")

        # Configuration tests
        results.append(self.config_diagnostics.validate_configuration_files())
        results.append(self.config_diagnostics.test_file_permissions())

        # Performance tests
        results.append(self.performance_diagnostics.check_system_resources())
        results.append(self.performance_diagnostics.performance_benchmark())

        # Dependency checks
        results.append(self._check_dependencies())

        # System info
        system_info = self._gather_system_info()

        # Store results
        self.test_history.extend(results)

        # Generate summary
        total_tests = len(results)
        passed = len([r for r in results if r.status == DiagnosticStatus.PASS])
        failed = len([r for r in results if r.status == DiagnosticStatus.FAIL])
        warnings = len([r for r in results if r.status == DiagnosticStatus.WARNING])
        errors = len([r for r in results if r.status == DiagnosticStatus.ERROR])
        skipped = len([r for r in results if r.status == DiagnosticStatus.SKIP])

        overall_status = "HEALTHY"
        if failed > 0 or errors > 0:
            overall_status = "CRITICAL"
        elif warnings > 0:
            overall_status = "WARNING"

        summary = {
            "overall_status": overall_status,
            "execution_time": time.time() - start_time,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "errors": errors,
                "skipped": skipped,
            },
            "results": [asdict(r) for r in results],
            "system_info": asdict(system_info),
            "recommendations": self._compile_recommendations(results),
        }

        self.logger.info(
            f"Diagnostics completed: {overall_status} ({passed}/{total_tests} passed)"
        )
        return summary

    def _check_dependencies(self) -> DiagnosticResult:
        """Check Python dependencies."""
        start_time = time.time()

        try:
            try:
                import pkg_resources  # type: ignore
            except ImportError:
                return DiagnosticResult(
                    test_id="dependencies",
                    name=DEPENDENCIES_CHECK_NAME,
                    category=DiagnosticCategory.DEPENDENCIES,
                    status=DiagnosticStatus.SKIP,
                    message="pkg_resources not available",
                    details={},
                    recommendations=["Install setuptools for dependency checking"],
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now(),
                )

            # Read requirements.txt
            requirements_file = Path("requirements.txt")
            if not requirements_file.exists():
                return DiagnosticResult(
                    test_id="dependencies",
                    name=DEPENDENCIES_CHECK_NAME,
                    category=DiagnosticCategory.DEPENDENCIES,
                    status=DiagnosticStatus.WARNING,
                    message="requirements.txt not found",
                    details={},
                    recommendations=["Create requirements.txt file"],
                    execution_time=time.time() - start_time,
                    timestamp=datetime.now(),
                )

            # Parse requirements
            requirements = []
            with open(requirements_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        requirements.append(line)

            # Check each requirement
            missing = []
            outdated = []

            for req in requirements:
                try:
                    pkg_resources.require(req)
                except pkg_resources.DistributionNotFound:
                    missing.append(req)
                except pkg_resources.VersionConflict as e:
                    outdated.append(str(e))

            issues = []
            recommendations = []

            if missing:
                issues.extend([f"Missing: {pkg}" for pkg in missing])
                recommendations.append(
                    "Install missing packages: pip install -r requirements.txt"
                )

            if outdated:
                issues.extend([f"Version conflict: {pkg}" for pkg in outdated])
                recommendations.append("Update packages to resolve version conflicts")

            status = DiagnosticStatus.PASS if not issues else DiagnosticStatus.WARNING
            message = (
                "All dependencies satisfied"
                if not issues
                else f"Found {len(issues)} dependency issues"
            )

            return DiagnosticResult(
                test_id="dependencies",
                name=DEPENDENCIES_CHECK_NAME,
                category=DiagnosticCategory.DEPENDENCIES,
                status=status,
                message=message,
                details={
                    "total_requirements": len(requirements),
                    "missing": missing,
                    "version_conflicts": outdated,
                    "issues": issues,
                },
                recommendations=recommendations,
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

        except Exception as e:
            return DiagnosticResult(
                test_id="dependencies",
                name=DEPENDENCIES_CHECK_NAME,
                category=DiagnosticCategory.DEPENDENCIES,
                status=DiagnosticStatus.ERROR,
                message=f"Dependency check failed: {str(e)}",
                details={"error": str(e)},
                recommendations=["Check Python environment and package installation"],
                execution_time=time.time() - start_time,
                timestamp=datetime.now(),
            )

    def _gather_system_info(self) -> SystemInfo:
        """Gather comprehensive system information."""
        try:
            # Basic system info
            cpu_count_value = 1  # Default fallback
            if HAS_PSUTIL:
                cpu_count_value = psutil.cpu_count() or 1
            else:
                cpu_count_value = os.cpu_count() or 1

            system_info = SystemInfo(
                platform=platform.system(),
                platform_version=platform.version(),
                python_version=platform.python_version(),
                architecture=platform.architecture()[0],
                cpu_count=cpu_count_value,
                memory_total="N/A",
                memory_available="N/A",
                disk_space={},
                network_interfaces=[],
                environment_variables={},
            )

            # Memory info
            if HAS_PSUTIL:
                memory = psutil.virtual_memory()
                system_info.memory_total = f"{memory.total / (1024**3):.1f} GB"
                system_info.memory_available = f"{memory.available / (1024**3):.1f} GB"

                # Disk space
                disk = psutil.disk_usage(".")
                system_info.disk_space = {
                    "total": f"{disk.total / (1024**3):.1f} GB",
                    "used": f"{disk.used / (1024**3):.1f} GB",
                    "free": f"{disk.free / (1024**3):.1f} GB",
                }

                # Network interfaces
                for interface, addresses in psutil.net_if_addrs().items():
                    for addr in addresses:
                        if addr.family == socket.AF_INET:
                            system_info.network_interfaces.append(
                                {
                                    "interface": interface,
                                    "address": addr.address or "N/A",
                                    "netmask": addr.netmask or "N/A",
                                }
                            )

            # Environment variables (selected ones)
            env_vars = ["PATH", "PYTHONPATH", "HOME", "USER", "TEMP", "TMP"]
            for var in env_vars:
                if var in os.environ:
                    value = os.environ[var]
                    # Truncate long paths
                    if len(value) > 200:
                        value = value[:100] + "..." + value[-100:]
                    system_info.environment_variables[var] = value

            return system_info

        except Exception as e:
            self.logger.error(f"Failed to gather system info: {e}")
            return SystemInfo(
                platform="Unknown",
                platform_version="Unknown",
                python_version="Unknown",
                architecture="Unknown",
                cpu_count=0,
                memory_total="Unknown",
                memory_available="Unknown",
                disk_space={},
                network_interfaces=[],
                environment_variables={},
            )

    def _compile_recommendations(self, results: List[DiagnosticResult]) -> List[str]:
        """Compile all recommendations from diagnostic results."""
        recommendations = []
        for result in results:
            recommendations.extend(result.recommendations)

        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)

        return unique_recommendations

    def get_diagnostics_history(self, hours: int = 24) -> List[DiagnosticResult]:
        """Get recent diagnostics history."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [r for r in self.test_history if r.timestamp > cutoff]

    def clear_diagnostics_history(self) -> None:
        """Clear diagnostics history."""
        self.test_history.clear()


# Global diagnostics manager
_global_diagnostics: Optional[SystemDiagnosticsManager] = None


def get_diagnostics_manager() -> SystemDiagnosticsManager:
    """Get global diagnostics manager."""
    global _global_diagnostics
    if _global_diagnostics is None:
        _global_diagnostics = SystemDiagnosticsManager()
    return _global_diagnostics
