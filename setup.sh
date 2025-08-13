#!/bin/bash
# WingmanMatch Quick Setup Script

echo "🚀 Setting up WingmanMatch development environment..."

# Check if required tools are installed
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 18+ first."
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python not found. Please install Python 3.10+ first."
    exit 1
fi

# Check Supabase CLI
if ! command -v supabase &> /dev/null; then
    echo "📦 Installing Supabase CLI..."
    npm install -g supabase
fi

echo "✅ Prerequisites checked"

# Install dependencies
echo "📦 Installing dependencies..."
npm install
pip install -r requirements.txt

# Setup environment file
if [ ! -f ".env" ]; then
    echo "📝 Creating environment file..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your actual values before starting!"
else
    echo "✅ Environment file already exists"
fi

# Check if Supabase is initialized
if [ ! -f "supabase/config.toml" ]; then
    echo "🗄️  Initializing Supabase..."
    supabase init
fi

echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env with your Supabase and Anthropic API keys"
echo "2. Run 'supabase start' (for local) OR 'supabase link --project-ref your-ref' (for cloud)"
echo "3. Run 'supabase db reset' to apply migrations"
echo "4. Run 'uvicorn src.main:app --reload --port 8000' (backend)"
echo "5. Run 'npm run dev' (frontend)"
echo "6. Visit http://localhost:3000/profile-setup to test!"

# Make executable
chmod +x setup.sh