# TheraBot - AI Therapeutic Assistant

A comprehensive AI-powered therapeutic chatbot with web interface, Android app, and MLflow evaluation system.

## Project Structure

```
TheraBot/
├── webapp/                     # Web Application
│   ├── simple_webapp.py       # Flask web server with streaming
│   ├── templates/             
│   │   └── chat.html         # Modern chat interface
│   └── requirements.txt       # Python dependencies
├── models/                     # AI Models
│   ├── int8/                  # Quantized models for inference
│   │   ├── Modelfile         # Ollama model configuration
│   │   ├── therabot_int8.gguf # Original model
│   │   └── threabot_v2.gguf   # Updated model (currently used)
│   ├── fp32/                  # Full precision models
│   └── llm_merged/            # Merged LLM models
├── android_bot/               # Android Application
│   └── android/              # Complete Android project
├── notebooks/                 # Jupyter Notebooks
│   ├── training.ipynb        # Model training pipeline
│   ├── model_evaluation.ipynb # Model evaluation
│   ├── model_optimization_colab.ipynb # Optimization
│   └── therabot_with_lora.ipynb # LoRA training
├── mlruns/                    # MLflow experiment tracking
└── DEPLOYMENT_GUIDE.md       # Deployment instructions
```

## Quick Start

### Web Application
```bash
cd webapp
pip install -r requirements.txt
python simple_webapp.py
# Open http://localhost:8000
```

### Prerequisites
- Python 3.8+
- Ollama installed
- Model loaded: `ollama create therabot -f models/int8/Modelfile`

## Features

- **Modern Web Interface**: Beautiful, responsive chat UI with streaming responses
- **Safety Features**: Crisis detection with automatic resource provision
- **Android App**: Native mobile application with offline inference
- **Model Training**: Complete training pipeline with evaluation
- **Experiment Tracking**: MLflow integration for model metrics

## Model Safety

The model includes comprehensive safety protocols:
- Crisis keyword detection (suicide, self-harm, etc.)
- Automatic crisis resource provision
- Professional help referrals
- Safety-first response prioritization

## Development

- **Web**: Flask with Server-Sent Events for real-time streaming
- **Mobile**: Android with llama.cpp integration
- **ML**: PyTorch with HuggingFace transformers
- **Tracking**: MLflow for experiment management

## License & Ethics

This project is designed for therapeutic support and educational purposes. Always encourage users to seek professional help when needed.