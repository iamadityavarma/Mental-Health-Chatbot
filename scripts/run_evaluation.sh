#!/bin/bash

# TheraBot Evaluation Runner Script
set -e

echo "🧪 TheraBot Model Evaluation Suite"
echo "=================================="

# Check if webapp is running
echo "🔍 Checking if TheraBot webapp is running..."
if curl -f http://localhost:8000 > /dev/null 2>&1; then
    echo " TheraBot webapp is running"
else
    echo "❌ TheraBot webapp is not running at http://localhost:8000"
    echo "Please start the webapp first:"
    echo "  cd webapp && python simple_webapp.py"
    echo "  Or: docker-compose up -d"
    exit 1
fi

# Install evaluation dependencies
echo "📦 Installing evaluation dependencies..."
pip install -r scripts/requirements-eval.txt

# Create results directory
RESULTS_DIR="evaluation_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "📊 Starting evaluation tests..."

# 1. Quick performance test
echo " Running quick performance evaluation..."
python scripts/evaluate_model.py \
    --url http://localhost:8000 \
    --requests 20 \
    --concurrent 2 \
    --save-mlflow \
    > "$RESULTS_DIR/quick_evaluation.log" 2>&1

if [ $? -eq 0 ]; then
    echo " Quick evaluation completed successfully"
else
    echo "❌ Quick evaluation failed - check $RESULTS_DIR/quick_evaluation.log"
fi

# 2. Crisis detection test
echo "🚨 Running crisis detection evaluation..."
python scripts/evaluate_model.py \
    --url http://localhost:8000 \
    --requests 10 \
    --concurrent 1 \
    --crisis-test \
    --save-mlflow \
    > "$RESULTS_DIR/crisis_evaluation.log" 2>&1

if [ $? -eq 0 ]; then
    echo " Crisis detection evaluation completed successfully"
else
    echo "❌ Crisis detection evaluation failed - check $RESULTS_DIR/crisis_evaluation.log"
fi

# 3. Comprehensive benchmark (optional, takes longer)
read -p "🏁 Run comprehensive benchmark suite? This takes 10-15 minutes (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Running comprehensive benchmark suite..."
    python scripts/benchmark_suite.py \
        --url http://localhost:8000 \
        --max-concurrent 6 \
        > "$RESULTS_DIR/benchmark.log" 2>&1
    
    if [ $? -eq 0 ]; then
        echo " Comprehensive benchmark completed successfully"
    else
        echo "❌ Comprehensive benchmark failed - check $RESULTS_DIR/benchmark.log"
    fi
fi

# 4. Generate summary
echo "📋 Generating evaluation summary..."

cat > "$RESULTS_DIR/evaluation_summary.md" << EOF
# TheraBot Evaluation Summary

**Date:** $(date)
**Webapp URL:** http://localhost:5000

## Tests Completed

###  Quick Performance Test
- **Status:** $([ -f therabot_evaluation_*.json ] && echo " Completed" || echo "❌ Failed")
- **Metrics:** P95 latency, tokens/sec, cost per request
- **Log:** quick_evaluation.log

### 🚨 Crisis Detection Test  
- **Status:** $([ -f therabot_evaluation_*_crisis.json ] && echo " Completed" || echo "❌ Failed")
- **Metrics:** Detection accuracy, precision, recall, F1 score
- **Log:** crisis_evaluation.log

### 🏁 Comprehensive Benchmark
- **Status:** $([ -d benchmark_results_* ] && echo " Completed" || echo "⏭️ Skipped")
- **Features:** Domain analysis, scaling tests, visualizations
- **Log:** benchmark.log

## Quick Results

EOF

# Extract key metrics from latest evaluation file
LATEST_EVAL=$(ls -t therabot_evaluation_*.json 2>/dev/null | head -1)
if [ -f "$LATEST_EVAL" ]; then
    echo "### Key Performance Metrics" >> "$RESULTS_DIR/evaluation_summary.md"
    echo '```json' >> "$RESULTS_DIR/evaluation_summary.md"
    python -c "
import json
try:
    with open('$LATEST_EVAL', 'r') as f:
        data = json.load(f)
    
    metrics = {
        'P95 Latency (ms)': data.get('p95_latency_ms', 'N/A'),
        'Avg Cost per Request (USD)': data.get('avg_cost_per_request_usd', 'N/A'),
        'Tokens per Second': data.get('avg_tokens_per_second', 'N/A'),
        'Total Tokens Generated': data.get('total_tokens_generated', 'N/A'),
        'Requests per Second': data.get('requests_per_second', 'N/A')
    }
    
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f'{key}: {value:.3f}')
        else:
            print(f'{key}: {value}')
            
except Exception as e:
    print(f'Error reading evaluation file: {e}')
" >> "$RESULTS_DIR/evaluation_summary.md"
    echo '```' >> "$RESULTS_DIR/evaluation_summary.md"
fi

echo "" >> "$RESULTS_DIR/evaluation_summary.md"
echo "## Files Generated" >> "$RESULTS_DIR/evaluation_summary.md"
echo "" >> "$RESULTS_DIR/evaluation_summary.md"
ls -la therabot_evaluation_*.json benchmark_results_*/ 2>/dev/null | while read line; do
    echo "- $line" >> "$RESULTS_DIR/evaluation_summary.md"
done

# Move generated files to results directory
mv therabot_evaluation_*.json "$RESULTS_DIR/" 2>/dev/null || true
mv benchmark_results_*/ "$RESULTS_DIR/" 2>/dev/null || true

echo "🎉 Evaluation complete!"
echo ""
echo "📁 Results saved to: $RESULTS_DIR/"
echo "📊 View summary: $RESULTS_DIR/evaluation_summary.md"

# Open MLflow UI if available
if command -v mlflow &> /dev/null; then
    echo "🔬 MLflow tracking data available. Start MLflow UI with:"
    echo "   mlflow ui --backend-store-uri sqlite:///mlruns.db"
fi

echo ""
echo "🏆 Evaluation Summary:"
echo "======================"
cat "$RESULTS_DIR/evaluation_summary.md"