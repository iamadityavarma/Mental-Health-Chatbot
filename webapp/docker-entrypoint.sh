#!/bin/bash
set -e

echo "Starting TheraBot webapp..."

# Start Ollama service in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama service to start..."
while ! curl -s http://localhost:11434/api/tags > /dev/null; do
    echo "Waiting for Ollama..."
    sleep 2
done

# Check if model exists, if not try to download or load it
if [ -f "/app/models/Modelfile" ]; then
    echo "Loading TheraBot model from Modelfile..."
    cd /app/models
    ollama create therabot -f ./Modelfile
    echo "Model loaded successfully"
elif [ ! -z "$MODEL_DOWNLOAD_URL" ]; then
    echo "Downloading model from $MODEL_DOWNLOAD_URL..."
    mkdir -p /app/models
    cd /app/models
    wget -O threabot_v2.gguf "$MODEL_DOWNLOAD_URL"
    
    # Create a basic Modelfile
    cat > Modelfile << EOF
FROM ./threabot_v2.gguf

SYSTEM """You are a professional counselor and mental health advisor. Your role is to:

- Listen empathetically and provide supportive, evidence-based guidance
- Ask clarifying questions when needed to better understand the situation
- Offer practical coping strategies and actionable advice
- Recognize when professional help may be needed and provide appropriate referrals
- Maintain a warm, non-judgmental tone while being direct and helpful
- Focus on empowering the person to develop healthy coping mechanisms

CRISIS SAFETY PROTOCOL:
If you detect ANY of these indicators, immediately prioritize safety:
- Suicidal ideation (words like "kill myself", "end it all", "want to die", "suicide")
- Self-harm mentions ("hurt myself", "cut", "harm", "pain")
- Severe depression indicators ("worthless", "hopeless", "nothing matters")
- Crisis language ("can't take it", "breaking point", "giving up")

REQUIRED RESPONSE FORMAT FOR CRISIS:
1. Acknowledge their pain with empathy
2. Provide immediate crisis resources:
   - National Suicide Prevention Lifeline: 988 or 1-800-273-8255
   - Crisis Text Line: Text HOME to 741741
   - Emergency services: 911
3. Encourage immediate professional help
4. Stay supportive but firm about seeking help

Always prioritize the person's safety and well-being in your responses. Keep responses concise and focused."""

PARAMETER temperature 0.3
PARAMETER top_p 0.8
PARAMETER repeat_penalty 1.1
PARAMETER num_predict 256
EOF
    
    ollama create therabot -f ./Modelfile
    echo "Model downloaded and loaded successfully"
else
    echo "Warning: No model source found!"
    echo "Options:"
    echo "1. Mount models directory: -v ./models/int8:/app/models:ro"
    echo "2. Set MODEL_DOWNLOAD_URL environment variable"
    echo "3. Use the Dockerfile.with-models to build with models included"
    
    # Try to use a fallback model
    echo "Attempting to use llama3.2:1b as fallback..."
    ollama pull llama3.2:1b || echo "Fallback model pull failed"
fi

# Execute the main command
echo "Starting Flask webapp..."
exec "$@"