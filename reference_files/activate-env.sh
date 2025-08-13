#!/bin/bash
# Fridays at Four Environment Activation Script
# Usage: source activate-env.sh

echo "🚀 Activating Fridays at Four development environment..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Conda not found. Please install Miniconda or Anaconda first."
    return 1
fi

# Initialize conda for bash/zsh if needed
if [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "🔧 Initializing conda for shell..."
    eval "$(conda shell.bash hook)" 2>/dev/null || eval "$(conda shell.zsh hook)" 2>/dev/null
fi

# Check if faf environment exists
if conda env list | grep -q "^faf "; then
    echo "✅ Found 'faf' conda environment"
    
    # Activate the environment
    conda activate faf
    
    if [[ "$CONDA_DEFAULT_ENV" == "faf" ]]; then
        echo "🎯 Environment activated successfully: faf"
        echo "🐍 Python: $(which python)"
        echo "📦 Python version: $(python --version)"
        echo "📍 Current directory: $(pwd)"
        
        # Test critical imports
        echo "🧪 Testing critical imports..."
        python -c "
import sys
try:
    from supabase import create_client
    print('  ✅ Supabase import works')
except ImportError as e:
    print(f'  ❌ Supabase import failed: {e}')
    sys.exit(1)

try:
    from fastapi import FastAPI
    print('  ✅ FastAPI import works')
except ImportError as e:
    print(f'  ❌ FastAPI import failed: {e}')
    sys.exit(1)

try:
    import uvicorn
    print('  ✅ Uvicorn import works')
except ImportError as e:
    print(f'  ❌ Uvicorn import failed: {e}')
    sys.exit(1)

print('  🎉 All critical imports successful!')
"
        
        if [[ $? -eq 0 ]]; then
            echo ""
            echo "💡 Environment ready! You can now run:"
            echo "   python test_simple_chat_handler.py    # Test SimpleChatHandler"
            echo "   python -m pytest test-suite/ -v       # Run full test suite"
            echo "   python src/main.py                     # Start dev server"
            echo "   uvicorn src.main:app --reload          # Start with auto-reload"
            echo ""
        else
            echo "❌ Import tests failed. Try reinstalling dependencies:"
            echo "   pip install -r requirements.txt"
            return 1
        fi
    else
        echo "❌ Failed to activate 'faf' environment"
        echo "Current environment: $CONDA_DEFAULT_ENV"
        return 1
    fi
else
    echo "❌ 'faf' conda environment not found!"
    echo "📋 Available environments:"
    conda env list
    echo ""
    echo "💡 To create the environment, run:"
    echo "   conda create -n faf python=3.11"
    echo "   conda activate faf"
    echo "   pip install -r requirements.txt"
    return 1
fi

# Add helpful aliases for this session
alias faf-test="python test_simple_chat_handler.py"
alias faf-server="python src/main.py"
alias faf-dev="uvicorn src.main:app --reload"
alias faf-pytest="python -m pytest test-suite/ -v"

echo "🔧 Session aliases added:"
echo "   faf-test    # Run SimpleChatHandler test"
echo "   faf-server  # Start server"
echo "   faf-dev     # Start with auto-reload"
echo "   faf-pytest  # Run test suite" 