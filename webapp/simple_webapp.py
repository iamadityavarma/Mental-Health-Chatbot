from flask import Flask, render_template, request, jsonify, Response
import requests
import json
import time
import mlflow
import numpy as np
import psutil
import threading
import os
import sys
from datetime import datetime
import platform

# Fix Windows Unicode encoding issues
if sys.platform == "win32":
    import codecs
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Optional GPU monitoring
try:
    import GPUtil
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

app = Flask(__name__)

# Ollama endpoint configuration
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "therabot"

# AWS cost setup (example: g4dn.xlarge = ~$0.53/hour in us-east-1)
COST_PER_HOUR = 0.53  # change based on instance type
REQUESTS_PER_HOUR_EST = 100
COST_PER_REQUEST = COST_PER_HOUR / REQUESTS_PER_HOUR_EST

# Keep a rolling list of latencies to calculate p95 later
latency_log = []

# Device monitoring storage
device_metrics_log = []
system_performance_log = []

# Initialize system monitoring
class SystemMonitor:
    def __init__(self):
        self.cpu_baseline = psutil.cpu_percent(interval=1)
        self.memory_baseline = psutil.virtual_memory().percent
        self.process = psutil.Process(os.getpid())
        
    def get_system_metrics(self):
        """Collect comprehensive system metrics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get GPU info if available
        gpu_info = {}
        if GPU_AVAILABLE:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    gpu_info = {
                        'gpu_utilization': gpu.load * 100,
                        'gpu_memory_used': gpu.memoryUsed,
                        'gpu_memory_total': gpu.memoryTotal,
                        'gpu_temperature': gpu.temperature
                    }
                else:
                    gpu_info = {'gpu_available': False}
            except Exception:
                gpu_info = {'gpu_available': False}
        else:
            gpu_info = {'gpu_available': False}
            
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=0.1),
            'cpu_count': psutil.cpu_count(),
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'memory_total_gb': memory.total / (1024**3),
            'disk_usage_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0],
            'process_memory_mb': self.process.memory_info().rss / (1024**2),
            'process_cpu_percent': self.process.cpu_percent(),
            'platform': platform.system(),
            'platform_version': platform.version(),
            **gpu_info
        }
    
    def get_thermal_state(self):
        """Monitor thermal state and throttling"""
        try:
            # Linux thermal zones
            thermal_zones = []
            for i in range(10):  # Check first 10 thermal zones
                thermal_path = f"/sys/class/thermal/thermal_zone{i}/temp"
                if os.path.exists(thermal_path):
                    with open(thermal_path, 'r') as f:
                        temp = int(f.read().strip()) / 1000.0  # Convert to Celsius
                        thermal_zones.append(temp)
            
            return {
                'thermal_zones': thermal_zones,
                'max_temp': max(thermal_zones) if thermal_zones else 0,
                'avg_temp': np.mean(thermal_zones) if thermal_zones else 0
            }
        except:
            return {'thermal_monitoring': 'unavailable'}

# Initialize system monitor
system_monitor = SystemMonitor()

# Configure MLflow to use the same tracking URI as the MLflow server
mlflow.set_tracking_uri("http://localhost:8002")

# Start MLflow experiment
mlflow.set_experiment("therabot_serving_enhanced")

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        payload = {
            "model": MODEL_NAME,
            "prompt": user_message,
            "stream": True
        }

        def generate_stream():
            start_time = time.time()
            pre_metrics = system_monitor.get_system_metrics()
            thermal_start = system_monitor.get_thermal_state()
            tokens_generated = 0
            first_token_time = None
            
            try:
                response = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)

                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line.decode('utf-8'))
                                if 'response' in chunk:
                                    tokens_generated += 1
                                    if first_token_time is None:
                                        first_token_time = time.time()
                                    
                                    # Handle Unicode encoding issues in streaming response
                                    response_chunk = chunk['response']
                                    try:
                                        response_chunk = response_chunk.encode('utf-8', errors='replace').decode('utf-8')
                                    except (UnicodeEncodeError, UnicodeDecodeError):
                                        response_chunk = ''.join(char for char in response_chunk if ord(char) < 65536)
                                    
                                    yield f"data: {json.dumps({'chunk': response_chunk})}\n\n"
                                if chunk.get('done', False):
                                    # Comprehensive metrics logging
                                    end_time = time.time()
                                    duration = end_time - start_time
                                    post_metrics = system_monitor.get_system_metrics()
                                    thermal_end = system_monitor.get_thermal_state()
                                    
                                    # Calculate performance metrics
                                    tokens_per_second = tokens_generated / duration if duration > 0 else 0
                                    time_to_first_token = (first_token_time - start_time) if first_token_time else duration
                                    
                                    # Calculate resource utilization
                                    cpu_usage_delta = post_metrics['cpu_percent'] - pre_metrics['cpu_percent']
                                    memory_usage_delta = post_metrics['memory_percent'] - pre_metrics['memory_percent']
                                    
                                    latency_log.append(duration)
                                    
                                    with mlflow.start_run(run_name="enhanced_chat_request", nested=True):
                                        # Basic metrics
                                        mlflow.log_metric("latency_seconds", duration)
                                        mlflow.log_metric("cost_per_request", COST_PER_REQUEST)
                                        
                                        # Performance metrics
                                        mlflow.log_metric("tokens_generated", tokens_generated)
                                        mlflow.log_metric("tokens_per_second", tokens_per_second)
                                        mlflow.log_metric("time_to_first_token_ms", time_to_first_token * 1000)
                                        
                                        # System resource metrics
                                        mlflow.log_metric("cpu_usage_percent", post_metrics['cpu_percent'])
                                        mlflow.log_metric("cpu_usage_delta", cpu_usage_delta)
                                        mlflow.log_metric("memory_usage_percent", post_metrics['memory_percent'])
                                        mlflow.log_metric("memory_usage_delta", memory_usage_delta)
                                        mlflow.log_metric("process_memory_mb", post_metrics['process_memory_mb'])
                                        mlflow.log_metric("process_cpu_percent", post_metrics['process_cpu_percent'])
                                        
                                        # Thermal metrics
                                        if 'max_temp' in thermal_end:
                                            mlflow.log_metric("max_temperature_celsius", thermal_end['max_temp'])
                                            mlflow.log_metric("avg_temperature_celsius", thermal_end['avg_temp'])
                                        
                                        # GPU metrics if available
                                        if post_metrics.get('gpu_available', True):
                                            if 'gpu_utilization' in post_metrics:
                                                mlflow.log_metric("gpu_utilization_percent", post_metrics['gpu_utilization'])
                                                mlflow.log_metric("gpu_memory_used_mb", post_metrics['gpu_memory_used'])
                                                mlflow.log_metric("gpu_temperature_celsius", post_metrics['gpu_temperature'])
                                        
                                        # Tags
                                        mlflow.set_tag("phase", "serving")
                                        mlflow.set_tag("model_name", MODEL_NAME)
                                        mlflow.set_tag("platform", post_metrics['platform'])
                                        mlflow.set_tag("inference_type", "streaming")
                                        mlflow.set_tag("prompt_length", len(user_message))
                                    
                                    yield f"data: {json.dumps({'done': True})}\n\n"
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    yield f"data: {json.dumps({'error': f'Ollama error: {response.status_code}'})}\n\n"

            except requests.exceptions.RequestException as e:
                yield f"data: {json.dumps({'error': f'Connection error: {str(e)}'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': f'Server error: {str(e)}'})}\n\n"

        return Response(generate_stream(), mimetype='text/event-stream')

    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/chat-sync', methods=['POST'])
def chat_sync():
    try:
        user_message = request.json.get('message', '')

        if not user_message:
            return jsonify({'error': 'No message provided'}), 400

        payload = {
            "model": MODEL_NAME,
            "prompt": user_message,
            "stream": False
        }

        start_time = time.time()
        pre_metrics = system_monitor.get_system_metrics()
        thermal_start = system_monitor.get_thermal_state()
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)

        end_time = time.time()
        duration = end_time - start_time
        post_metrics = system_monitor.get_system_metrics()
        thermal_end = system_monitor.get_thermal_state()
        
        latency_log.append(duration)

        if response.status_code == 200:
            result = response.json()
            
            # Calculate resource utilization
            cpu_usage_delta = post_metrics['cpu_percent'] - pre_metrics['cpu_percent']
            memory_usage_delta = post_metrics['memory_percent'] - pre_metrics['memory_percent']
            
            # Estimate token count (rough approximation) with Unicode handling
            response_text = result.get('response', '')
            # Handle potential Unicode encoding issues
            try:
                response_text = response_text.encode('utf-8', errors='replace').decode('utf-8')
            except (UnicodeEncodeError, UnicodeDecodeError):
                # If encoding fails, remove problematic characters
                response_text = ''.join(char for char in response_text if ord(char) < 65536)
            
            estimated_tokens = len(response_text.split())
            tokens_per_second = estimated_tokens / duration if duration > 0 else 0

            # Enhanced MLflow logging
            with mlflow.start_run(run_name="enhanced_chat_sync", nested=True):
                # Basic metrics
                mlflow.log_metric("latency_seconds", duration)
                mlflow.log_metric("cost_per_request", COST_PER_REQUEST)
                
                # Performance metrics
                mlflow.log_metric("estimated_tokens", estimated_tokens)
                mlflow.log_metric("tokens_per_second", tokens_per_second)
                mlflow.log_metric("response_length_chars", len(response_text))
                
                # System resource metrics
                mlflow.log_metric("cpu_usage_percent", post_metrics['cpu_percent'])
                mlflow.log_metric("cpu_usage_delta", cpu_usage_delta)
                mlflow.log_metric("memory_usage_percent", post_metrics['memory_percent'])
                mlflow.log_metric("memory_usage_delta", memory_usage_delta)
                mlflow.log_metric("process_memory_mb", post_metrics['process_memory_mb'])
                mlflow.log_metric("process_cpu_percent", post_metrics['process_cpu_percent'])
                
                # Thermal metrics
                if 'max_temp' in thermal_end:
                    mlflow.log_metric("max_temperature_celsius", thermal_end['max_temp'])
                    mlflow.log_metric("avg_temperature_celsius", thermal_end['avg_temp'])
                
                # GPU metrics if available
                if post_metrics.get('gpu_available', True):
                    if 'gpu_utilization' in post_metrics:
                        mlflow.log_metric("gpu_utilization_percent", post_metrics['gpu_utilization'])
                        mlflow.log_metric("gpu_memory_used_mb", post_metrics['gpu_memory_used'])
                        mlflow.log_metric("gpu_temperature_celsius", post_metrics['gpu_temperature'])
                
                # Tags
                mlflow.set_tag("phase", "serving")
                mlflow.set_tag("model_name", MODEL_NAME)
                mlflow.set_tag("platform", post_metrics['platform'])
                mlflow.set_tag("inference_type", "synchronous")
                mlflow.set_tag("prompt_length", len(user_message))

            return jsonify({'response': response_text})
        else:
            return jsonify({'error': f'Ollama error: {response.status_code}'}), 500

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Endpoint to compute aggregate stats like P95 latency."""
    if not latency_log:
        return jsonify({'message': 'No requests logged yet'}), 200

    p95 = float(np.percentile(latency_log, 95))
    avg_latency = float(np.mean(latency_log))
    current_system_metrics = system_monitor.get_system_metrics()

    # Log aggregate metrics
    with mlflow.start_run(run_name="aggregate_metrics", nested=True):
        mlflow.log_metric("p95_latency_seconds", p95)
        mlflow.log_metric("avg_latency_seconds", avg_latency)
        mlflow.log_metric("total_requests", len(latency_log))
        mlflow.log_metric("current_cpu_percent", current_system_metrics['cpu_percent'])
        mlflow.log_metric("current_memory_percent", current_system_metrics['memory_percent'])

    return jsonify({
        'avg_latency': avg_latency,
        'p95_latency': p95,
        'cost_per_request': COST_PER_REQUEST,
        'total_requests': len(latency_log),
        'current_system_metrics': current_system_metrics
    })

@app.route('/device-metrics', methods=['POST'])
def log_device_metrics():
    """Endpoint for Android app or external devices to send metrics"""
    try:
        metrics = request.json
        device_metrics_log.append(metrics)
        
        with mlflow.start_run(run_name="device_metrics", nested=True):
            # Battery metrics
            mlflow.log_metric("battery_level", metrics.get('battery_level', 0))
            mlflow.log_metric("battery_temp_celsius", metrics.get('battery_temp', 0))
            mlflow.log_metric("power_consumption_mw", metrics.get('power_consumption', 0))
            mlflow.log_metric("is_charging", 1 if metrics.get('is_charging', False) else 0)
            
            # Performance metrics
            mlflow.log_metric("device_cpu_usage_percent", metrics.get('cpu_usage', 0))
            mlflow.log_metric("device_memory_usage_mb", metrics.get('memory_usage', 0))
            mlflow.log_metric("device_thermal_state", metrics.get('thermal_state', 0))
            mlflow.log_metric("device_network_strength", metrics.get('network_strength', 0))
            
            # Model performance
            mlflow.log_metric("device_tokens_per_second", metrics.get('tokens_per_second', 0))
            mlflow.log_metric("device_ttft_ms", metrics.get('ttft', 0))
            mlflow.log_metric("device_model_load_time_ms", metrics.get('model_load_time', 0))
            mlflow.log_metric("device_inference_time_ms", metrics.get('inference_time', 0))
            
            # Quality metrics
            mlflow.log_metric("response_coherence_score", metrics.get('coherence_score', 0))
            mlflow.log_metric("safety_filter_triggered", 1 if metrics.get('safety_triggered', False) else 0)
            
            # Device info
            mlflow.set_tag("device_model", metrics.get('device_model', 'unknown'))
            mlflow.set_tag("device_os_version", metrics.get('os_version', 'unknown'))
            mlflow.set_tag("app_version", metrics.get('app_version', 'unknown'))
            mlflow.set_tag("device_ram_gb", metrics.get('ram_gb', 'unknown'))
            mlflow.set_tag("device_cpu_cores", metrics.get('cpu_cores', 'unknown'))
            
        return jsonify({'status': 'success', 'metrics_logged': len(device_metrics_log)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/system-status', methods=['GET'])
def system_status():
    """Real-time system status endpoint"""
    try:
        current_metrics = system_monitor.get_system_metrics()
        thermal_state = system_monitor.get_thermal_state()
        
        # Calculate system health score
        health_score = calculate_system_health(current_metrics, thermal_state)
        
        return jsonify({
            'timestamp': current_metrics['timestamp'],
            'system_health_score': health_score,
            'system_metrics': current_metrics,
            'thermal_state': thermal_state,
            'active_requests': len(latency_log),
            'ollama_status': check_ollama_status()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/performance-dashboard', methods=['GET'])
def performance_dashboard():
    """Comprehensive performance dashboard data"""
    try:
        if not latency_log:
            return jsonify({'message': 'No performance data available yet'}), 200
            
        # Calculate performance statistics
        latencies = np.array(latency_log)
        performance_stats = {
            'latency_stats': {
                'mean': float(np.mean(latencies)),
                'median': float(np.median(latencies)),
                'p95': float(np.percentile(latencies, 95)),
                'p99': float(np.percentile(latencies, 99)),
                'min': float(np.min(latencies)),
                'max': float(np.max(latencies)),
                'std': float(np.std(latencies))
            },
            'request_stats': {
                'total_requests': len(latency_log),
                'requests_last_hour': count_recent_requests(3600),
                'requests_last_minute': count_recent_requests(60),
                'avg_requests_per_minute': len(latency_log) / max(1, (time.time() - get_start_time()) / 60)
            },
            'system_status': system_monitor.get_system_metrics(),
            'device_metrics_summary': summarize_device_metrics(),
            'recommendations': get_performance_recommendations()
        }
        
        return jsonify(performance_stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calculate_system_health(metrics, thermal):
    """Calculate overall system health score (0-100)"""
    health_score = 100
    
    # CPU health (penalty for high usage)
    if metrics['cpu_percent'] > 80:
        health_score -= 20
    elif metrics['cpu_percent'] > 60:
        health_score -= 10
        
    # Memory health
    if metrics['memory_percent'] > 90:
        health_score -= 25
    elif metrics['memory_percent'] > 80:
        health_score -= 15
        
    # Thermal health
    if 'max_temp' in thermal and thermal['max_temp'] > 0:
        if thermal['max_temp'] > 85:
            health_score -= 30
        elif thermal['max_temp'] > 75:
            health_score -= 15
            
    # Disk health
    if metrics['disk_usage_percent'] > 95:
        health_score -= 10
        
    return max(0, health_score)

def check_ollama_status():
    """Check if Ollama is responsive"""
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        return {'status': 'healthy', 'version': response.json().get('version', 'unknown')}
    except:
        return {'status': 'unhealthy', 'error': 'Ollama not responding'}

def count_recent_requests(seconds):
    """Count requests in the last N seconds"""
    # This is a simplified implementation
    # In production, you'd want to track timestamps
    return len(latency_log)

def get_start_time():
    """Get application start time"""
    # This is a placeholder - you'd track this properly
    return time.time() - 3600

def summarize_device_metrics():
    """Summarize device metrics if any were logged"""
    if not device_metrics_log:
        return {'message': 'No device metrics available'}
        
    # Calculate averages and trends
    battery_levels = [m.get('battery_level', 0) for m in device_metrics_log[-10:]]
    cpu_usage = [m.get('cpu_usage', 0) for m in device_metrics_log[-10:]]
    
    return {
        'recent_battery_trend': float(np.mean(battery_levels)) if battery_levels else 0,
        'recent_cpu_trend': float(np.mean(cpu_usage)) if cpu_usage else 0,
        'total_device_reports': len(device_metrics_log)
    }

def get_performance_recommendations():
    """Generate performance recommendations based on metrics"""
    recommendations = []
    current_metrics = system_monitor.get_system_metrics()
    
    if current_metrics['cpu_percent'] > 80:
        recommendations.append("High CPU usage detected. Consider reducing concurrent requests.")
        
    if current_metrics['memory_percent'] > 85:
        recommendations.append("High memory usage. Consider restarting the service or reducing model context size.")
        
    if current_metrics.get('gpu_utilization', 0) > 90:
        recommendations.append("GPU utilization high. Monitor for thermal throttling.")
        
    if not recommendations:
        recommendations.append("System performance looks healthy.")
        
    return recommendations

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
