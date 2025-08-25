@echo off
REM TheraBot Evaluation Runner Script for Windows
setlocal enabledelayedexpansion

echo 🧪 TheraBot Model Evaluation Suite
echo ==================================

REM Check if webapp is running
echo 🔍 Checking if TheraBot webapp is running...
curl -f http://localhost:8000 >nul 2>&1
if errorlevel 1 (
    echo ❌ TheraBot webapp is not running at http://localhost:8000
    echo Please start the webapp first:
    echo   cd webapp ^&^& python simple_webapp.py
    echo   Or: docker-compose up -d
    exit /b 1
) else (
    echo ✅ TheraBot webapp is running
)

REM Install evaluation dependencies
echo 📦 Installing evaluation dependencies...
pip install -r scripts\requirements-eval.txt

REM Create results directory
for /f "tokens=2 delims==" %%a in ('"wmic OS Get localdatetime /value"') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "RESULTS_DIR=evaluation_results_%YYYY%%MM%%DD%_%HH%%Min%%Sec%"
mkdir "%RESULTS_DIR%"

echo 📊 Starting evaluation tests...

REM 1. Quick performance test
echo ⚡ Running quick performance evaluation...
python scripts\evaluate_model.py ^
    --url http://localhost:8000 ^
    --requests 20 ^
    --concurrent 2 ^
    --save-mlflow ^
    > "%RESULTS_DIR%\quick_evaluation.log" 2>&1

if errorlevel 1 (
    echo ❌ Quick evaluation failed - check %RESULTS_DIR%\quick_evaluation.log
) else (
    echo ✅ Quick evaluation completed successfully
)

REM 2. Crisis detection test
echo 🚨 Running crisis detection evaluation...
python scripts\evaluate_model.py ^
    --url http://localhost:8000 ^
    --requests 10 ^
    --concurrent 1 ^
    --crisis-test ^
    --save-mlflow ^
    > "%RESULTS_DIR%\crisis_evaluation.log" 2>&1

if errorlevel 1 (
    echo ❌ Crisis detection evaluation failed - check %RESULTS_DIR%\crisis_evaluation.log
) else (
    echo ✅ Crisis detection evaluation completed successfully
)

REM 3. Comprehensive benchmark (optional)
set /p COMPREHENSIVE="🏁 Run comprehensive benchmark suite? This takes 10-15 minutes (y/N): "
if /i "%COMPREHENSIVE%"=="y" (
    echo 🚀 Running comprehensive benchmark suite...
    python scripts\benchmark_suite.py ^
        --url http://localhost:8000 ^
        --max-concurrent 6 ^
        > "%RESULTS_DIR%\benchmark.log" 2>&1
    
    if errorlevel 1 (
        echo ❌ Comprehensive benchmark failed - check %RESULTS_DIR%\benchmark.log
    ) else (
        echo ✅ Comprehensive benchmark completed successfully
    )
)

REM 4. Generate summary
echo 📋 Generating evaluation summary...

echo # TheraBot Evaluation Summary > "%RESULTS_DIR%\evaluation_summary.md"
echo. >> "%RESULTS_DIR%\evaluation_summary.md"
echo **Date:** %date% %time% >> "%RESULTS_DIR%\evaluation_summary.md"
echo **Webapp URL:** http://localhost:8000 >> "%RESULTS_DIR%\evaluation_summary.md"
echo. >> "%RESULTS_DIR%\evaluation_summary.md"
echo ## Tests Completed >> "%RESULTS_DIR%\evaluation_summary.md"
echo. >> "%RESULTS_DIR%\evaluation_summary.md"

REM Move generated files to results directory
if exist therabot_evaluation_*.json (
    move therabot_evaluation_*.json "%RESULTS_DIR%\" >nul 2>&1
)
if exist benchmark_results_* (
    move benchmark_results_* "%RESULTS_DIR%\" >nul 2>&1
)

echo 🎉 Evaluation complete!
echo.
echo 📁 Results saved to: %RESULTS_DIR%\
echo 📊 View summary: %RESULTS_DIR%\evaluation_summary.md

REM Check if MLflow is available
mlflow --version >nul 2>&1
if not errorlevel 1 (
    echo 🔬 MLflow tracking data available. Start MLflow UI with:
    echo    mlflow ui --backend-store-uri sqlite:///mlruns.db
)

pause