"""
System Monitor Module
Handles system monitoring and information gathering using psutil.
"""

import psutil
import platform
import time
from datetime import datetime
from typing import Dict, List, Any

class SystemMonitor:
    """
    Monitors system resources and provides system information.
    """
    
    def __init__(self):
        self.start_time = time.time()
    
    def get_current_time(self) -> str:
        """
        Get current timestamp as formatted string.
        
        Returns:
            str: Current timestamp
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get comprehensive system information.
        
        Returns:
            Dict containing system information
        """
        try:
            # Basic system info
            system_info = {
                'platform': {
                    'system': platform.system(),
                    'platform': platform.platform(),
                    'machine': platform.machine(),
                    'processor': platform.processor(),
                    'python_version': platform.python_version(),
                },
                'cpu': self.get_cpu_info(),
                'memory': self.get_memory_info(),
                'disk': self.get_disk_info(),
                'network': self.get_network_info(),
                'processes': self.get_process_info(),
                'uptime': self.get_uptime(),
                'timestamp': self.get_current_time()
            }
            
            return system_info
            
        except Exception as e:
            return {
                'error': f'Failed to get system info: {str(e)}',
                'timestamp': self.get_current_time()
            }
    
    def get_cpu_info(self) -> Dict[str, Any]:
        """
        Get CPU information and usage.
        
        Returns:
            Dict containing CPU information
        """
        try:
            cpu_info = {
                'count_logical': psutil.cpu_count(logical=True),
                'count_physical': psutil.cpu_count(logical=False),
                'usage_percent': psutil.cpu_percent(interval=1),
                'usage_per_cpu': psutil.cpu_percent(interval=1, percpu=True),
                'frequency': None,
                'load_average': None
            }
            
            # Get CPU frequency if available
            try:
                freq = psutil.cpu_freq()
                if freq:
                    cpu_info['frequency'] = {
                        'current': freq.current,
                        'min': freq.min,
                        'max': freq.max
                    }
            except:
                pass
            
            # Get load average if available (Unix systems)
            try:
                if hasattr(psutil, 'getloadavg'):
                    cpu_info['load_average'] = psutil.getloadavg()
            except:
                pass
            
            return cpu_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_memory_info(self) -> Dict[str, Any]:
        """
        Get memory information and usage.
        
        Returns:
            Dict containing memory information
        """
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            memory_info = {
                'virtual': {
                    'total': virtual_mem.total,
                    'available': virtual_mem.available,
                    'used': virtual_mem.used,
                    'free': virtual_mem.free,
                    'percent': virtual_mem.percent,
                    'total_gb': round(virtual_mem.total / (1024**3), 2),
                    'used_gb': round(virtual_mem.used / (1024**3), 2),
                    'available_gb': round(virtual_mem.available / (1024**3), 2)
                },
                'swap': {
                    'total': swap_mem.total,
                    'used': swap_mem.used,
                    'free': swap_mem.free,
                    'percent': swap_mem.percent,
                    'total_gb': round(swap_mem.total / (1024**3), 2),
                    'used_gb': round(swap_mem.used / (1024**3), 2)
                }
            }
            
            return memory_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_disk_info(self) -> Dict[str, Any]:
        """
        Get disk information and usage.
        
        Returns:
            Dict containing disk information
        """
        try:
            disk_info = {
                'partitions': [],
                'io_counters': None
            }
            
            # Get disk partitions
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    partition_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': (usage.used / usage.total) * 100,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2)
                    }
                    disk_info['partitions'].append(partition_info)
                except PermissionError:
                    # Skip partitions we can't access
                    continue
            
            # Get disk I/O counters
            try:
                io_counters = psutil.disk_io_counters()
                if io_counters:
                    disk_info['io_counters'] = {
                        'read_count': io_counters.read_count,
                        'write_count': io_counters.write_count,
                        'read_bytes': io_counters.read_bytes,
                        'write_bytes': io_counters.write_bytes,
                        'read_time': io_counters.read_time,
                        'write_time': io_counters.write_time
                    }
            except:
                pass
            
            return disk_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_info(self) -> Dict[str, Any]:
        """
        Get network information and statistics.
        
        Returns:
            Dict containing network information
        """
        try:
            network_info = {
                'interfaces': {},
                'io_counters': None,
                'connections': None
            }
            
            # Get network interfaces
            interfaces = psutil.net_if_addrs()
            for interface_name, addresses in interfaces.items():
                interface_info = {
                    'addresses': []
                }
                
                for addr in addresses:
                    addr_info = {
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask,
                        'broadcast': addr.broadcast
                    }
                    interface_info['addresses'].append(addr_info)
                
                network_info['interfaces'][interface_name] = interface_info
            
            # Get network I/O counters
            try:
                io_counters = psutil.net_io_counters()
                if io_counters:
                    network_info['io_counters'] = {
                        'bytes_sent': io_counters.bytes_sent,
                        'bytes_recv': io_counters.bytes_recv,
                        'packets_sent': io_counters.packets_sent,
                        'packets_recv': io_counters.packets_recv,
                        'errin': io_counters.errin,
                        'errout': io_counters.errout,
                        'dropin': io_counters.dropin,
                        'dropout': io_counters.dropout
                    }
            except:
                pass
            
            # Get connection count
            try:
                connections = psutil.net_connections()
                network_info['connections'] = len(connections)
            except:
                pass
            
            return network_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_process_info(self) -> Dict[str, Any]:
        """
        Get process information.
        
        Returns:
            Dict containing process information
        """
        try:
            processes = []
            total_processes = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    total_processes += 1
                    
                    # Only include top processes to avoid overwhelming output
                    if len(processes) < 10:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_percent': round(proc_info['memory_percent'], 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            
            process_info = {
                'total_count': total_processes,
                'top_processes': processes[:10],
                'current_process': {
                    'pid': psutil.Process().pid,
                    'cpu_percent': psutil.Process().cpu_percent(),
                    'memory_percent': psutil.Process().memory_percent()
                }
            }
            
            return process_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_uptime(self) -> Dict[str, Any]:
        """
        Get system uptime information.
        
        Returns:
            Dict containing uptime information
        """
        try:
            boot_time = psutil.boot_time()
            current_time = time.time()
            uptime_seconds = current_time - boot_time
            
            # Calculate uptime components
            days = int(uptime_seconds // (24 * 3600))
            hours = int((uptime_seconds % (24 * 3600)) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            seconds = int(uptime_seconds % 60)
            
            uptime_info = {
                'boot_time': datetime.fromtimestamp(boot_time).strftime('%Y-%m-%d %H:%M:%S'),
                'uptime_seconds': uptime_seconds,
                'uptime_formatted': f"{days}d {hours}h {minutes}m {seconds}s",
                'days': days,
                'hours': hours,
                'minutes': minutes,
                'seconds': seconds
            }
            
            return uptime_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_quick_stats(self) -> Dict[str, Any]:
        """
        Get quick system statistics for frequent monitoring.
        
        Returns:
            Dict containing quick system stats
        """
        try:
            stats = {
                'cpu_percent': psutil.cpu_percent(interval=0.1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids()),
                'timestamp': self.get_current_time()
            }
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes into human-readable format.
        
        Args:
            bytes_value (int): Number of bytes
            
        Returns:
            str: Formatted string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
    
    def get_system_summary(self) -> str:
        """
        Get a formatted system summary string.
        
        Returns:
            str: Formatted system summary
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            summary = f"""System Summary ({self.get_current_time()}):
CPU Usage: {cpu_percent}%
Memory: {memory.percent}% used ({self.format_bytes(memory.used)} / {self.format_bytes(memory.total)})
Disk: {(disk.used / disk.total * 100):.1f}% used ({self.format_bytes(disk.used)} / {self.format_bytes(disk.total)})
Processes: {len(psutil.pids())}
Uptime: {self.get_uptime()['uptime_formatted']}"""
            
            return summary
            
        except Exception as e:
            return f"Error getting system summary: {str(e)}"