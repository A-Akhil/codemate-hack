"""
Security Manager Module
Handles security validation, input sanitization, and command safety checks.
"""

import re
import os
import time
import hashlib
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import ipaddress

class SecurityManager:
    """
    Manages security validation and protection for the web terminal.
    """
    
    def __init__(self):
        # Rate limiting storage
        self.rate_limit_storage = {}  # {ip: [timestamps]}
        self.max_requests_per_minute = 60
        self.max_requests_per_hour = 500
        
        # Command execution limits
        self.max_command_length = 1000
        self.max_output_length = 100000  # 100KB
        
        # Blocked IPs (can be expanded to use database)
        self.blocked_ips: Set[str] = set()
        
        # Suspicious activity tracking
        self.suspicious_activity = {}  # {ip: {'count': int, 'last_seen': datetime}}
        
        # Define dangerous command patterns
        self.dangerous_patterns = [
            # System manipulation
            r'sudo\s+',
            r'su\s+',
            r'passwd\s+',
            r'useradd\s+',
            r'userdel\s+',
            r'usermod\s+',
            r'groupadd\s+',
            r'groupdel\s+',
            
            # File system dangers
            r'rm\s+-rf\s+/',
            r'rm\s+-rf\s+\*',
            r'rm\s+-rf\s+~',
            r'format\s+',
            r'fdisk\s+',
            r'mkfs\s+',
            r'dd\s+if=.*of=/dev/',
            
            # Network and system access
            r'ssh\s+',
            r'scp\s+',
            r'rsync\s+.*:',
            r'nc\s+.*-e',
            r'netcat\s+.*-e',
            r'telnet\s+',
            r'ftp\s+',
            
            # Process manipulation
            r'kill\s+-9\s+1',
            r'killall\s+-9',
            r'pkill\s+',
            
            # System services
            r'systemctl\s+',
            r'service\s+',
            r'init\s+',
            r'shutdown\s+',
            r'reboot\s+',
            r'halt\s+',
            
            # Package management (potentially dangerous)
            r'apt\s+install\s+',
            r'apt-get\s+install\s+',
            r'yum\s+install\s+',
            r'rpm\s+-i',
            r'dpkg\s+-i',
            
            # Code execution
            r'python\s+-c\s+',
            r'perl\s+-e\s+',
            r'ruby\s+-e\s+',
            r'node\s+-e\s+',
            r'eval\s+',
            r'exec\s+',
            
            # Redirection and piping that could be dangerous
            r'>\s*/dev/null',
            r'>\s*/dev/zero',
            r'>\s*/proc/',
            r'>\s*/sys/',
            r'\|\s*sh\s*$',
            r'\|\s*bash\s*$',
            r'\|\s*zsh\s*$',
            
            # Command substitution
            r'`.*`',
            r'\$\(',
            r'\$\{',
            
            # Environment manipulation
            r'export\s+PATH=',
            r'export\s+LD_PRELOAD=',
            r'export\s+LD_LIBRARY_PATH=',
            
            # Cron and scheduled tasks
            r'crontab\s+',
            r'\bat\s+',
            r'batch\s+',
            
            # Database operations (if MySQL/PostgreSQL clients available)
            r'mysql\s+.*-e',
            r'psql\s+.*-c',
            
            # Compression with potential for zip bombs
            r'zip\s+.*-r.*/',
            r'tar\s+.*--exclude=',
        ]
        
        # Define path traversal patterns
        self.path_traversal_patterns = [
            r'\.\./+',
            r'/\.\./+',
            r'\\\.\.\\+',
            r'%2e%2e%2f',
            r'%2e%2e/',
            r'..%2f',
            r'%2e%2e%5c'
        ]
        
        # Define allowed file extensions for reading
        self.allowed_read_extensions = {
            '.txt', '.log', '.json', '.xml', '.yaml', '.yml', '.csv',
            '.md', '.rst', '.cfg', '.conf', '.ini', '.properties'
        }
        
        # Define maximum file sizes for operations
        self.max_file_size = 10 * 1024 * 1024  # 10MB
    
    def validate_input(self, user_input: str, client_ip: str = None) -> Dict[str, Any]:
        """
        Validate user input for security threats.
        
        Args:
            user_input (str): User input to validate
            client_ip (str): Client IP address for rate limiting
            
        Returns:
            Dict containing validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'blocked': False
        }
        
        try:
            # Check if IP is blocked
            if client_ip and self._is_ip_blocked(client_ip):
                validation_result.update({
                    'valid': False,
                    'blocked': True,
                    'errors': ['IP address is blocked']
                })
                return validation_result
            
            # Rate limiting check
            if client_ip:
                rate_limit_result = self._check_rate_limit(client_ip)
                if not rate_limit_result['allowed']:
                    validation_result.update({
                        'valid': False,
                        'errors': [f"Rate limit exceeded: {rate_limit_result['message']}"]
                    })
                    return validation_result
            
            # Input length check
            if len(user_input) > self.max_command_length:
                validation_result.update({
                    'valid': False,
                    'errors': [f'Input too long (max {self.max_command_length} characters)']
                })
                return validation_result
            
            # Check for dangerous patterns
            dangerous_found = self._check_dangerous_patterns(user_input)
            if dangerous_found:
                validation_result['warnings'].extend(dangerous_found)
                # Block dangerous commands
                validation_result['valid'] = False
                validation_result['errors'].append('Potentially dangerous command detected')
                
                # Track suspicious activity
                if client_ip:
                    self._track_suspicious_activity(client_ip, 'dangerous_command', user_input)
            
            # Check for path traversal attempts
            traversal_found = self._check_path_traversal(user_input)
            if traversal_found:
                validation_result['warnings'].extend(traversal_found)
                validation_result['valid'] = False
                validation_result['errors'].append('Path traversal attempt detected')
                
                if client_ip:
                    self._track_suspicious_activity(client_ip, 'path_traversal', user_input)
            
            # Check for injection attempts
            injection_found = self._check_injection_attempts(user_input)
            if injection_found:
                validation_result['warnings'].extend(injection_found)
                validation_result['valid'] = False
                validation_result['errors'].append('Code injection attempt detected')
                
                if client_ip:
                    self._track_suspicious_activity(client_ip, 'injection_attempt', user_input)
            
            # Sanitize input
            sanitized_input = self._sanitize_input(user_input)
            validation_result['sanitized_input'] = sanitized_input
            
        except Exception as e:
            validation_result.update({
                'valid': False,
                'errors': [f'Validation error: {str(e)}']
            })
        
        return validation_result
    
    def _check_rate_limit(self, client_ip: str) -> Dict[str, Any]:
        """
        Check if client IP is within rate limits.
        
        Args:
            client_ip (str): Client IP address
            
        Returns:
            Dict containing rate limit check results
        """
        current_time = time.time()
        
        # Initialize IP tracking if not exists
        if client_ip not in self.rate_limit_storage:
            self.rate_limit_storage[client_ip] = []
        
        # Clean old timestamps (older than 1 hour)
        hour_ago = current_time - 3600
        self.rate_limit_storage[client_ip] = [
            timestamp for timestamp in self.rate_limit_storage[client_ip]
            if timestamp > hour_ago
        ]
        
        # Check hourly limit
        if len(self.rate_limit_storage[client_ip]) >= self.max_requests_per_hour:
            return {
                'allowed': False,
                'message': f'Hourly limit of {self.max_requests_per_hour} requests exceeded'
            }
        
        # Check per-minute limit
        minute_ago = current_time - 60
        recent_requests = [
            timestamp for timestamp in self.rate_limit_storage[client_ip]
            if timestamp > minute_ago
        ]
        
        if len(recent_requests) >= self.max_requests_per_minute:
            return {
                'allowed': False,
                'message': f'Per-minute limit of {self.max_requests_per_minute} requests exceeded'
            }
        
        # Add current timestamp
        self.rate_limit_storage[client_ip].append(current_time)
        
        return {
            'allowed': True,
            'remaining_hourly': self.max_requests_per_hour - len(self.rate_limit_storage[client_ip]),
            'remaining_minute': self.max_requests_per_minute - len(recent_requests) - 1
        }
    
    def _check_dangerous_patterns(self, user_input: str) -> List[str]:
        """
        Check for dangerous command patterns.
        
        Args:
            user_input (str): Input to check
            
        Returns:
            List of found dangerous patterns
        """
        found_patterns = []
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                found_patterns.append(f'Dangerous pattern: {pattern}')
        
        return found_patterns
    
    def _check_path_traversal(self, user_input: str) -> List[str]:
        """
        Check for path traversal attempts.
        
        Args:
            user_input (str): Input to check
            
        Returns:
            List of found path traversal patterns
        """
        found_patterns = []
        
        for pattern in self.path_traversal_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                found_patterns.append(f'Path traversal pattern: {pattern}')
        
        return found_patterns
    
    def _check_injection_attempts(self, user_input: str) -> List[str]:
        """
        Check for code injection attempts.
        
        Args:
            user_input (str): Input to check
            
        Returns:
            List of found injection patterns
        """
        found_patterns = []
        
        # Check for common injection patterns
        injection_patterns = [
            r';.*rm\s+',
            r'&&.*rm\s+',
            r'\|\|.*rm\s+',
            r';.*wget\s+',
            r'&&.*wget\s+',
            r';.*curl\s+',
            r'&&.*curl\s+',
            r';.*python\s+',
            r'&&.*python\s+',
            r';.*sh\s+',
            r'&&.*sh\s+',
            r';.*bash\s+',
            r'&&.*bash\s+',
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                found_patterns.append(f'Injection pattern: {pattern}')
        
        return found_patterns
    
    def _sanitize_input(self, user_input: str) -> str:
        """
        Sanitize user input to prevent basic attacks.
        
        Args:
            user_input (str): Input to sanitize
            
        Returns:
            str: Sanitized input
        """
        # Remove or escape potentially dangerous characters
        sanitized = user_input.strip()
        
        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')
        
        # Remove ANSI escape sequences
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        sanitized = ansi_escape.sub('', sanitized)
        
        # Limit to printable ASCII characters (with some exceptions for international text)
        sanitized = ''.join(char for char in sanitized if char.isprintable() or char in ['\t', '\n'])
        
        return sanitized
    
    def _is_ip_blocked(self, client_ip: str) -> bool:
        """
        Check if an IP address is blocked.
        
        Args:
            client_ip (str): IP address to check
            
        Returns:
            bool: True if IP is blocked
        """
        return client_ip in self.blocked_ips
    
    def _track_suspicious_activity(self, client_ip: str, activity_type: str, details: str):
        """
        Track suspicious activity for an IP address.
        
        Args:
            client_ip (str): IP address
            activity_type (str): Type of suspicious activity
            details (str): Details of the activity
        """
        if client_ip not in self.suspicious_activity:
            self.suspicious_activity[client_ip] = {
                'count': 0,
                'activities': [],
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        
        self.suspicious_activity[client_ip]['count'] += 1
        self.suspicious_activity[client_ip]['last_seen'] = datetime.now()
        self.suspicious_activity[client_ip]['activities'].append({
            'type': activity_type,
            'details': details[:200],  # Limit details length
            'timestamp': datetime.now()
        })
        
        # Auto-block IP if too many suspicious activities
        if self.suspicious_activity[client_ip]['count'] >= 5:
            self.blocked_ips.add(client_ip)
    
    def validate_file_operation(self, file_path: str, operation: str) -> Dict[str, Any]:
        """
        Validate file operations for security.
        
        Args:
            file_path (str): Path to file
            operation (str): Type of operation (read, write, delete, etc.)
            
        Returns:
            Dict containing validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Normalize path
            normalized_path = os.path.normpath(file_path)
            
            # Check for path traversal
            if '..' in normalized_path or normalized_path.startswith('/'):
                validation_result.update({
                    'valid': False,
                    'errors': ['Path traversal or absolute path not allowed']
                })
                return validation_result
            
            # Check file extension for read operations
            if operation == 'read':
                file_ext = os.path.splitext(normalized_path)[1].lower()
                if file_ext and file_ext not in self.allowed_read_extensions:
                    validation_result['warnings'].append(f'Reading {file_ext} files may not be safe')
            
            # Check file size if file exists
            if os.path.exists(normalized_path):
                file_size = os.path.getsize(normalized_path)
                if file_size > self.max_file_size:
                    validation_result.update({
                        'valid': False,
                        'errors': [f'File too large ({file_size} bytes, max {self.max_file_size})']
                    })
                    return validation_result
            
            # Additional checks for write operations
            if operation in ['write', 'delete']:
                # Ensure we're not trying to modify system files
                system_dirs = ['/bin', '/sbin', '/usr', '/etc', '/boot', '/sys', '/proc']
                for sys_dir in system_dirs:
                    if normalized_path.startswith(sys_dir):
                        validation_result.update({
                            'valid': False,
                            'errors': [f'Cannot modify files in system directory: {sys_dir}']
                        })
                        return validation_result
            
        except Exception as e:
            validation_result.update({
                'valid': False,
                'errors': [f'File validation error: {str(e)}']
            })
        
        return validation_result
    
    def validate_network_operation(self, target: str, operation: str) -> Dict[str, Any]:
        """
        Validate network operations for security.
        
        Args:
            target (str): Network target (IP, domain, URL)
            operation (str): Type of operation (ping, curl, etc.)
            
        Returns:
            Dict containing validation results
        """
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        try:
            # Check for private/internal IP addresses
            if self._is_internal_ip(target):
                validation_result['warnings'].append('Target appears to be internal/private IP')
            
            # Check for localhost access
            if target.lower() in ['localhost', '127.0.0.1', '::1']:
                validation_result['warnings'].append('Localhost access detected')
            
            # Validate URL format for web requests
            if operation in ['curl', 'wget']:
                if not (target.startswith('http://') or target.startswith('https://')):
                    validation_result.update({
                        'valid': False,
                        'errors': ['Invalid URL format - must start with http:// or https://']
                    })
                    return validation_result
                
                # Check for suspicious URLs
                suspicious_patterns = [
                    r'javascript:',
                    r'data:',
                    r'file:',
                    r'ftp:',
                ]
                
                for pattern in suspicious_patterns:
                    if re.search(pattern, target, re.IGNORECASE):
                        validation_result.update({
                            'valid': False,
                            'errors': [f'Suspicious URL scheme detected: {pattern}']
                        })
                        return validation_result
        
        except Exception as e:
            validation_result.update({
                'valid': False,
                'errors': [f'Network validation error: {str(e)}']
            })
        
        return validation_result
    
    def _is_internal_ip(self, target: str) -> bool:
        """
        Check if target is an internal/private IP address.
        
        Args:
            target (str): IP address or hostname
            
        Returns:
            bool: True if internal IP
        """
        try:
            # Try to parse as IP address
            ip = ipaddress.ip_address(target)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except ValueError:
            # Not a valid IP address, assume it's a hostname
            return False
    
    def get_security_report(self) -> Dict[str, Any]:
        """
        Get a security report of current status.
        
        Returns:
            Dict containing security statistics
        """
        current_time = datetime.now()
        
        # Clean old rate limit data
        hour_ago = time.time() - 3600
        active_ips = 0
        total_requests = 0
        
        for ip, timestamps in self.rate_limit_storage.items():
            recent_timestamps = [t for t in timestamps if t > hour_ago]
            if recent_timestamps:
                active_ips += 1
                total_requests += len(recent_timestamps)
        
        # Count recent suspicious activities
        recent_suspicious = 0
        for ip, data in self.suspicious_activity.items():
            if (current_time - data['last_seen']).total_seconds() < 3600:
                recent_suspicious += 1
        
        return {
            'timestamp': current_time.isoformat(),
            'blocked_ips': len(self.blocked_ips),
            'active_ips_last_hour': active_ips,
            'total_requests_last_hour': total_requests,
            'suspicious_ips_last_hour': recent_suspicious,
            'rate_limits': {
                'max_per_minute': self.max_requests_per_minute,
                'max_per_hour': self.max_requests_per_hour
            },
            'file_limits': {
                'max_file_size': self.max_file_size,
                'max_command_length': self.max_command_length,
                'max_output_length': self.max_output_length
            }
        }
    
    def block_ip(self, ip_address: str, reason: str = 'Manual block'):
        """
        Manually block an IP address.
        
        Args:
            ip_address (str): IP address to block
            reason (str): Reason for blocking
        """
        self.blocked_ips.add(ip_address)
        
        # Track this as a security event
        if ip_address not in self.suspicious_activity:
            self.suspicious_activity[ip_address] = {
                'count': 0,
                'activities': [],
                'first_seen': datetime.now(),
                'last_seen': datetime.now()
            }
        
        self.suspicious_activity[ip_address]['activities'].append({
            'type': 'manual_block',
            'details': reason,
            'timestamp': datetime.now()
        })
    
    def unblock_ip(self, ip_address: str):
        """
        Unblock an IP address.
        
        Args:
            ip_address (str): IP address to unblock
        """
        self.blocked_ips.discard(ip_address)