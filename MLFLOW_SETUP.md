# MLflow Multi-Server Setup for Interview Demo

##  **Overview**
This setup demonstrates a complete MLflow tracking infrastructure with separate servers for training and serving phases, showcasing end-to-end ML lifecycle management.

##  **Three-Server Architecture**

### 1. **TheraBot Webapp** - Port 8000
- **URL**: http://localhost:8000
- **Purpose**: Production chat interface with real-time metrics
- **Features**: 
  - Modern streaming chat UI
  - Real-time system monitoring
  - Unicode-safe text handling
  - Crisis detection protocols

### 2. **Serving MLflow** - Port 8002  
- **URL**: http://localhost:8002
- **Purpose**: Real-time production serving metrics
- **Backend**: SQLite database (`mlflow.db`)
- **Experiment**: `therabot_serving_enhanced`
- **Metrics Tracked**:
  -  Latency (P95: 10.87s)
  -  Cost per request ($0.0053)
  -  System resources (CPU, Memory, GPU)
  -  Thermal monitoring
  -  Tokens per second (5.38 TPS)
  -  Response quality metrics

### 3. **Training MLflow** - Port 8003
- **URL**: http://localhost:8003  
- **Purpose**: Training and model evaluation metrics
- **Backend**: File-based (`mlruns/` directory)
- **Experiments**: 
  - `therabot_ondevice_comparison` (Model comparison study)
  - `therabot_serving` (Previous serving experiments)
  - `Default` (Initial experiments)

##  **Training Metrics Dashboard (Port 8003)**

### **Rich Training Metrics**:
```json
{
  "avg_latency_ms": 3815.58,
  "avg_memory_mb": 12.10,
  "bleu_score": 0.0148,
  "disk_size_mb": 1259.88,
  "energy_per_token_mj": 0.0179,
  "estimated_power_mw": 377.96,
  "memory_efficiency": 1.74,
  "model_size_mb": 1259.88,
  "p95_latency_ms": 3866.80,
  "peak_memory_mb": 12.11,
  "perplexity": 25.0,
  "tokens_per_second": 21.09
}
```

### **Model Parameters Tracked**:
- **Model Type**: GGUF (INT8 quantized)
- **Precision**: INT8 quantization  
- **Model Size**: 1.26 GB
- **Model Path**: Artifact tracking

### **Quality & Efficiency Metrics**:
- **BLEU Score**: 0.0148 (response quality)
- **Perplexity**: 25.0 (model confidence)
- **Memory Efficiency**: 1.74 tokens/MB
- **Energy per Token**: 0.0179 mJ (sustainability metrics)
- **Power Consumption**: 377.96 mW average

##  **Data Flow Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Training      │    │   TheraBot       │    │   Serving       │
│   Notebooks     │───▶│   Webapp         │───▶│   MLflow        │
│                 │    │   (Port 8000)    │    │   (Port 8002)   │
│   MLflow        │    │                  │    │                 │
│   (Port 8003)   │    │   Real-time      │    │   SQLite DB     │
│                 │    │   Metrics        │    │   Live Tracking │
│   File-based    │    │   Collection     │    │                 │
│   mlruns/       │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

##  **Interview Demo Flow**

### **1. Training Phase (Port 8003)**
- Show comprehensive model training metrics
- Demonstrate model comparison studies  
- Display energy efficiency analysis
- Show quantization impact analysis

### **2. Serving Phase (Port 8002)**
- Live chat interaction with real-time metrics
- System health monitoring
- Cost analysis and resource tracking
- Performance optimization recommendations

### **3. Production Chat (Port 8000)**
- Beautiful user interface
- Real-time streaming responses
- Crisis detection and safety protocols
- Unicode handling and error resilience

##  **Key Metrics Comparison**

| Metric | Training | Serving | Improvement |
|--------|----------|---------|-------------|
| **Latency** | 3.8s | 10.9s | Inference overhead |
| **Memory** | 12.1 MB | 139.9 MB | Full system load |
| **TPS** | 21.1 | 5.38 | Real-world vs benchmark |
| **Model Size** | 1.26 GB | 1.26 GB | Consistent |
| **Cost/Request** | N/A | $0.0053 | Production cost |

##  **Interview Talking Points**

### **MLOps Excellence**:
1. **Separate Concerns**: Training vs Serving metrics isolation
2. **Multi-Environment**: File-based vs Database backends  
3. **Real-time Monitoring**: Live system health tracking
4. **Comprehensive Metrics**: 20+ metrics per inference
5. **Cost Optimization**: Real-time cost per request tracking

### **Technical Architecture**:
1. **Scalable Design**: Multiple MLflow servers for different phases
2. **Production-Ready**: Unicode handling, error resilience  
3. **Resource Monitoring**: CPU, Memory, GPU, Thermal tracking
4. **Quality Assurance**: BLEU scores, perplexity, safety checks

### **Business Value**:
1. **Cost Efficiency**: $0.0053 vs $0.02 for commercial APIs (74% savings)
2. **Performance**: 21 TPS training vs 5.38 TPS production (realistic metrics)
3. **Sustainability**: Energy consumption tracking (0.0179 mJ/token)
4. **Quality**: Comprehensive evaluation pipeline

##  **Access URLs**

- **Chat Interface**: http://localhost:8000
- **Serving Metrics**: http://localhost:8002  
- **Training Metrics**: http://localhost:8003

##  **Why This Setup Impresses**

1. **Complete ML Lifecycle**: Training → Evaluation → Deployment → Monitoring
2. **Production-Grade**: Real-time metrics, error handling, cost tracking
3. **Scalable Architecture**: Multi-server setup ready for enterprise
4. **Comprehensive Monitoring**: System health, performance, quality, cost
5. **Research & Production**: Both academic metrics and business KPIs

This demonstrates not just technical skills, but understanding of the complete ML product lifecycle from research to production deployment! 
