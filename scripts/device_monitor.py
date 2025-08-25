#!/usr/bin/env python3
"""
Advanced Device Monitoring Script for TheraBot
Collects comprehensive device metrics and performance analytics
"""

import time
import json
import requests
import psutil
import numpy as np
import mlflow
from datetime import datetime, timedelta
import logging
import threading
import queue
import os
import platform

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeviceMonitor:
    def __init__(self, webapp_url="http://localhost:8000", monitoring_interval=10):
        self.webapp_url = webapp_url
        self.monitoring_interval = monitoring_interval
        self.metrics_queue = queue.Queue()
        self.running = False
        self.start_time = time.time()
        
        # Initialize MLflow
        mlflow.set_experiment("device_monitoring")
        
        # Performance tracking
        self.battery_history = []
        self.performance_history = []
        self.thermal_history = []
        
    def start_monitoring(self):
        """Start continuous device monitoring"""
        self.running = True
        logger.info("Starting device monitoring...")
        
        # Start monitoring threads
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        
        monitor_thread.start()
        analysis_thread.start()
        
        return monitor_thread, analysis_thread
    
    def stop_monitoring(self):
        """Stop device monitoring"""
        self.running = False
        logger.info("Stopping device monitoring...")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                metrics = self._collect_comprehensive_metrics()
                self.metrics_queue.put(metrics)
                
                # Send metrics to webapp if available
                self._send_metrics_to_webapp(metrics)
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)
    
    def _analysis_loop(self):
        """Analyze metrics and detect issues"""
        while self.running:
            try:
                # Process queued metrics
                batch_metrics = []
                while not self.metrics_queue.empty():
                    try:
                        batch_metrics.append(self.metrics_queue.get_nowait())
                    except queue.Empty:
                        break
                
                if batch_metrics:
                    self._analyze_metrics_batch(batch_metrics)
                
                time.sleep(30)  # Analyze every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                time.sleep(30)
    
    def _collect_comprehensive_metrics(self):
        """Collect comprehensive device metrics"""
        timestamp = datetime.now()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Battery metrics (if available)
        battery_info = self._get_battery_info()
        
        # Thermal metrics
        thermal_info = self._get_thermal_info()
        
        # Process-specific metrics
        process_info = self._get_process_metrics()
        
        # Performance metrics
        performance_metrics = self._calculate_performance_metrics()
        
        metrics = {
            'timestamp': timestamp.isoformat(),
            'epoch_time': time.time(),
            
            # System metrics
            'cpu_percent': cpu_percent,
            'cpu_count': psutil.cpu_count(),
            'memory_percent': memory.percent,
            'memory_used_gb': memory.used / (1024**3),
            'memory_available_gb': memory.available / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_percent': disk.percent,
            'disk_used_gb': disk.used / (1024**3),
            'disk_free_gb': disk.free / (1024**3),
            
            # Network metrics
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv,
            'network_packets_sent': network.packets_sent,
            'network_packets_recv': network.packets_recv,
            
            # System load
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            
            # Platform info
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            
            # Battery info
            **battery_info,
            
            # Thermal info
            **thermal_info,
            
            # Process metrics
            **process_info,
            
            # Performance metrics
            **performance_metrics
        }
        
        return metrics
    
    def _get_battery_info(self):
        """Get battery information if available"""
        try:
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    return {
                        'battery_percent': battery.percent,
                        'battery_plugged': battery.power_plugged,
                        'battery_time_left': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else -1
                    }
            
            # Alternative battery detection for different platforms
            return self._get_platform_specific_battery()
            
        except Exception as e:
            logger.debug(f"Battery info not available: {e}")
            return {'battery_available': False}
    
    def _get_platform_specific_battery(self):
        """Platform-specific battery detection"""
        try:
            if platform.system() == "Linux":
                # Try reading from /sys/class/power_supply/
                battery_path = "/sys/class/power_supply/BAT0"
                if os.path.exists(battery_path):
                    with open(f"{battery_path}/capacity", 'r') as f:
                        capacity = int(f.read().strip())
                    with open(f"{battery_path}/status", 'r') as f:
                        status = f.read().strip()
                    
                    return {
                        'battery_percent': capacity,
                        'battery_status': status,
                        'battery_plugged': status in ['Charging', 'Full']
                    }
            
            elif platform.system() == "Windows":
                # Windows battery info via WMI (requires pywin32)
                try:
                    import win32com.client
                    c = win32com.client.Dispatch("WbemScripting.SWbemLocator")
                    wmi = c.ConnectServer(".", "root\cimv2")
                    
                    for battery in wmi.ExecQuery("Select * from Win32_Battery"):
                        return {
                            'battery_percent': int(battery.EstimatedChargeRemaining),
                            'battery_status': battery.BatteryStatus,
                            'battery_plugged': battery.BatteryStatus in [2, 6, 7, 8, 9]  # Charging states
                        }
                except ImportError:
                    logger.debug("pywin32 not available for Windows battery detection")
            
        except Exception as e:
            logger.debug(f"Platform-specific battery detection failed: {e}")
        
        return {'battery_available': False}
    
    def _get_thermal_info(self):
        """Get thermal information"""
        try:
            thermal_data = {}
            
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    all_temps = []
                    for sensor_name, sensors in temps.items():
                        for sensor in sensors:
                            all_temps.append(sensor.current)
                            thermal_data[f'temp_{sensor_name}_{sensor.label}'] = sensor.current
                    
                    if all_temps:
                        thermal_data.update({
                            'max_temperature': max(all_temps),
                            'avg_temperature': np.mean(all_temps),
                            'min_temperature': min(all_temps)
                        })
            
            # Linux-specific thermal zones
            if platform.system() == "Linux":
                linux_temps = self._get_linux_thermal_zones()
                thermal_data.update(linux_temps)
            
            return thermal_data if thermal_data else {'thermal_available': False}
            
        except Exception as e:
            logger.debug(f"Thermal info not available: {e}")
            return {'thermal_available': False}
    
    def _get_linux_thermal_zones(self):
        """Get Linux thermal zone temperatures"""
        thermal_data = {}
        try:
            for i in range(20):  # Check up to 20 thermal zones
                thermal_path = f"/sys/class/thermal/thermal_zone{i}/temp"
                type_path = f"/sys/class/thermal/thermal_zone{i}/type"
                
                if os.path.exists(thermal_path):
                    with open(thermal_path, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0  # Convert to Celsius
                    
                    zone_type = "unknown"
                    if os.path.exists(type_path):
                        with open(type_path, 'r') as f:
                            zone_type = f.read().strip()
                    
                    thermal_data[f'thermal_zone_{i}_{zone_type}'] = temp
        except Exception as e:
            logger.debug(f"Linux thermal zones not available: {e}")
        
        return thermal_data
    
    def _get_process_metrics(self):
        """Get process-specific metrics"""
        try:
            # Find Ollama and Python processes
            ollama_processes = []
            python_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if 'ollama' in proc_info['name'].lower():
                        ollama_processes.append(proc_info)
                    elif 'python' in proc_info['name'].lower():
                        python_processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            process_metrics = {
                'ollama_process_count': len(ollama_processes),
                'python_process_count': len(python_processes)
            }
            
            # Aggregate Ollama metrics
            if ollama_processes:
                ollama_cpu = sum(p.get('cpu_percent', 0) for p in ollama_processes)
                ollama_memory = sum(p.get('memory_percent', 0) for p in ollama_processes)
                process_metrics.update({
                    'ollama_cpu_percent': ollama_cpu,
                    'ollama_memory_percent': ollama_memory
                })
            
            return process_metrics
            
        except Exception as e:
            logger.debug(f"Process metrics not available: {e}")
            return {'process_metrics_available': False}
    
    def _calculate_performance_metrics(self):
        """Calculate performance and efficiency metrics"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        metrics = {
            'monitor_uptime_seconds': uptime,
            'monitor_uptime_hours': uptime / 3600
        }
        
        # Calculate performance trends if we have history
        if len(self.performance_history) > 1:
            recent_cpu = [m['cpu_percent'] for m in self.performance_history[-10:]]
            recent_memory = [m['memory_percent'] for m in self.performance_history[-10:]]
            
            metrics.update({
                'cpu_trend_avg': np.mean(recent_cpu),
                'cpu_trend_std': np.std(recent_cpu),
                'memory_trend_avg': np.mean(recent_memory),
                'memory_trend_std': np.std(recent_memory)
            })
        
        return metrics
    
    def _send_metrics_to_webapp(self, metrics):
        """Send metrics to webapp endpoint"""
        try:
            # Format metrics for webapp
            webapp_metrics = {
                'timestamp': metrics['timestamp'],
                'cpu_usage': metrics['cpu_percent'],
                'memory_usage': metrics['memory_used_gb'] * 1024,  # Convert to MB
                'battery_level': metrics.get('battery_percent', 0),
                'battery_temp': 0,  # Would need specific sensor
                'thermal_state': metrics.get('max_temperature', 0),
                'device_model': f"{metrics['platform']} {metrics['architecture']}",
                'os_version': metrics['platform_version'],
                'ram_gb': metrics['memory_total_gb'],
                'cpu_cores': metrics['cpu_count']
            }
            
            response = requests.post(
                f"{self.webapp_url}/device-metrics",
                json=webapp_metrics,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug("Metrics sent to webapp successfully")
            else:
                logger.warning(f"Failed to send metrics to webapp: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.debug(f"Could not send metrics to webapp: {e}")
        except Exception as e:
            logger.error(f"Error sending metrics to webapp: {e}")
    
    def _analyze_metrics_batch(self, batch_metrics):
        """Analyze a batch of metrics for issues and trends"""
        try:
            if not batch_metrics:
                return
            
            # Store in history
            self.performance_history.extend(batch_metrics)
            
            # Keep only recent history (last 100 entries)
            if len(self.performance_history) > 100:
                self.performance_history = self.performance_history[-100:]
            
            # Detect performance issues
            issues = self._detect_performance_issues(batch_metrics)
            
            # Log to MLflow
            self._log_analysis_to_mlflow(batch_metrics, issues)
            
            if issues:
                logger.warning(f"Performance issues detected: {issues}")
            
        except Exception as e:
            logger.error(f"Error analyzing metrics batch: {e}")
    
    def _detect_performance_issues(self, metrics_batch):
        """Detect performance issues from metrics"""
        issues = []
        
        for metrics in metrics_batch:
            # High CPU usage
            if metrics['cpu_percent'] > 90:
                issues.append(f"Critical CPU usage: {metrics['cpu_percent']:.1f}%")
            elif metrics['cpu_percent'] > 80:
                issues.append(f"High CPU usage: {metrics['cpu_percent']:.1f}%")
            
            # High memory usage
            if metrics['memory_percent'] > 95:
                issues.append(f"Critical memory usage: {metrics['memory_percent']:.1f}%")
            elif metrics['memory_percent'] > 85:
                issues.append(f"High memory usage: {metrics['memory_percent']:.1f}%")
            
            # Low disk space
            if metrics['disk_percent'] > 95:
                issues.append(f"Critical disk usage: {metrics['disk_percent']:.1f}%")
            
            # High temperature
            max_temp = metrics.get('max_temperature', 0)
            if max_temp > 85:
                issues.append(f"High temperature: {max_temp:.1f}°C")
            
            # Low battery
            battery_percent = metrics.get('battery_percent', 100)
            if battery_percent < 20 and not metrics.get('battery_plugged', True):
                issues.append(f"Low battery: {battery_percent}%")
        
        return list(set(issues))  # Remove duplicates
    
    def _log_analysis_to_mlflow(self, metrics_batch, issues):
        """Log analysis results to MLflow"""
        try:
            with mlflow.start_run(run_name="device_analysis", nested=True):
                # Aggregate metrics
                avg_cpu = np.mean([m['cpu_percent'] for m in metrics_batch])
                avg_memory = np.mean([m['memory_percent'] for m in metrics_batch])
                max_temp = max([m.get('max_temperature', 0) for m in metrics_batch])
                
                # Log aggregated metrics
                mlflow.log_metric("avg_cpu_percent", avg_cpu)
                mlflow.log_metric("avg_memory_percent", avg_memory)
                mlflow.log_metric("max_temperature", max_temp)
                mlflow.log_metric("issues_count", len(issues))
                mlflow.log_metric("batch_size", len(metrics_batch))
                
                # Log issues as tags
                for i, issue in enumerate(issues[:5]):  # Log up to 5 issues
                    mlflow.set_tag(f"issue_{i}", issue)
                
                # System info
                if metrics_batch:
                    sample_metrics = metrics_batch[0]
                    mlflow.set_tag("platform", sample_metrics['platform'])
                    mlflow.set_tag("architecture", sample_metrics['architecture'])
                    mlflow.set_tag("cpu_cores", sample_metrics['cpu_count'])
                    mlflow.set_tag("total_memory_gb", sample_metrics['memory_total_gb'])
                
        except Exception as e:
            logger.error(f"Error logging to MLflow: {e}")
    
    def get_performance_report(self):
        """Generate a comprehensive performance report"""
        if not self.performance_history:
            return {"message": "No performance data available"}
        
        recent_metrics = self.performance_history[-20:]  # Last 20 entries
        
        # Calculate statistics
        cpu_values = [m['cpu_percent'] for m in recent_metrics]
        memory_values = [m['memory_percent'] for m in recent_metrics]
        temps = [m.get('max_temperature', 0) for m in recent_metrics if m.get('max_temperature', 0) > 0]
        
        report = {
            'monitoring_duration_hours': (time.time() - self.start_time) / 3600,
            'total_samples': len(self.performance_history),
            'recent_samples': len(recent_metrics),
            
            'cpu_stats': {
                'avg': np.mean(cpu_values),
                'max': np.max(cpu_values),
                'min': np.min(cpu_values),
                'std': np.std(cpu_values)
            },
            
            'memory_stats': {
                'avg': np.mean(memory_values),
                'max': np.max(memory_values),
                'min': np.min(memory_values),
                'std': np.std(memory_values)
            },
            
            'thermal_stats': {
                'avg': np.mean(temps) if temps else 0,
                'max': np.max(temps) if temps else 0,
                'samples': len(temps)
            },
            
            'recent_issues': self._detect_performance_issues(recent_metrics),
            'recommendations': self._generate_recommendations(recent_metrics)
        }
        
        return report
    
    def _generate_recommendations(self, recent_metrics):
        """Generate performance recommendations"""
        recommendations = []
        
        avg_cpu = np.mean([m['cpu_percent'] for m in recent_metrics])
        avg_memory = np.mean([m['memory_percent'] for m in recent_metrics])
        
        if avg_cpu > 80:
            recommendations.append("Consider reducing workload or optimizing CPU-intensive operations")
        
        if avg_memory > 85:
            recommendations.append("Monitor memory usage and consider increasing available RAM")
        
        temps = [m.get('max_temperature', 0) for m in recent_metrics if m.get('max_temperature', 0) > 0]
        if temps and np.mean(temps) > 75:
            recommendations.append("Monitor thermal conditions and ensure adequate cooling")
        
        if not recommendations:
            recommendations.append("System performance appears optimal")
        
        return recommendations

def main():
    """Main function to run device monitoring"""
    monitor = DeviceMonitor()
    
    try:
        logger.info("Starting TheraBot Device Monitor...")
        monitor_thread, analysis_thread = monitor.start_monitoring()
        
        # Keep running until interrupted
        while True:
            time.sleep(60)
            
            # Print periodic status
            report = monitor.get_performance_report()
            logger.info(f"Monitoring status - CPU avg: {report['cpu_stats']['avg']:.1f}%, "
                       f"Memory avg: {report['memory_stats']['avg']:.1f}%, "
                       f"Samples: {report['total_samples']}")
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    finally:
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()

