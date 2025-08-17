#!/usr/bin/env python3
"""
Performance Monitoring Deployment Script for WingmanMatch
Safely integrates performance monitoring into existing FastAPI application
"""

import os
import shutil
from datetime import datetime

def backup_existing_files():
    """Create backup of existing files before modification"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_performance_migration_{timestamp}"
    
    print(f"📁 Creating backup directory: {backup_dir}")
    os.makedirs(backup_dir, exist_ok=True)
    
    # Backup main.py
    if os.path.exists("src/main.py"):
        shutil.copy2("src/main.py", f"{backup_dir}/main.py.backup")
        print("✅ Backed up src/main.py")
    
    # Backup config.py
    if os.path.exists("src/config.py"):
        shutil.copy2("src/config.py", f"{backup_dir}/config.py.backup")
        print("✅ Backed up src/config.py")
    
    return backup_dir

def integrate_performance_monitoring():
    """Integrate performance monitoring into main.py"""
    print("🔧 Integrating performance monitoring into main.py...")
    
    # Read the new main file with performance monitoring
    with open("src/main_with_performance.py", "r") as f:
        new_main_content = f.read()
    
    # Get existing imports and endpoints from original main.py
    print("📖 Reading existing main.py content...")
    
    existing_endpoints = []
    with open("src/main.py", "r") as f:
        lines = f.readlines()
        
    # Find endpoints to preserve (look for @app routes)
    in_endpoint = False
    current_endpoint = []
    
    for line in lines:
        if line.strip().startswith("@app."):
            if current_endpoint:
                existing_endpoints.append("".join(current_endpoint))
            current_endpoint = [line]
            in_endpoint = True
        elif in_endpoint:
            current_endpoint.append(line)
            # End of function (next decorator or class/function definition)
            if line.strip().startswith(("@", "class ", "def ")) and not line.strip().startswith("@app."):
                existing_endpoints.append("".join(current_endpoint))
                current_endpoint = []
                in_endpoint = False
    
    # Add final endpoint if exists
    if current_endpoint:
        existing_endpoints.append("".join(current_endpoint))
    
    print(f"📋 Found {len(existing_endpoints)} existing endpoints to preserve")
    
    # Create integrated main.py
    integrated_content = new_main_content
    
    # Add existing endpoints that aren't already in the new file
    for endpoint in existing_endpoints:
        # Skip endpoints that are already in the new file
        if any(skip in endpoint for skip in ["/health", "root()", "test_performance"]):
            continue
        
        # Add the endpoint
        integrated_content += "\n" + endpoint
    
    # Write integrated main.py
    with open("src/main.py", "w") as f:
        f.write(integrated_content)
    
    print("✅ Successfully integrated performance monitoring into main.py")

def create_environment_template():
    """Create environment variable template for performance monitoring"""
    template_content = """
# Performance Monitoring Configuration (add to your .env file)
ENABLE_PERFORMANCE_MONITORING=true
ENABLE_CONNECTION_POOLING=true
ENABLE_PERFORMANCE_ALERTS=true
PERFORMANCE_ALERT_EMAIL=admin@wingmanmatch.com
DATABASE_POOL_SIZE=20
METRICS_RETENTION_HOURS=24
SLACK_WEBHOOK_URL=  # Optional: Add your Slack webhook URL for alerts

# Optional: Redis URL for metrics storage (if not already configured)
# REDIS_URL=redis://localhost:6379
"""
    
    with open("performance_monitoring.env.template", "w") as f:
        f.write(template_content)
    
    print("📝 Created performance_monitoring.env.template")
    print("   Add these variables to your .env file or environment")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing required dependencies...")
    
    try:
        import subprocess
        result = subprocess.run(
            ["pip", "install", "asyncpg==0.29.0", "aiohttp==3.9.1"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print(f"⚠️  Warning: Failed to install dependencies: {result.stderr}")
            print("   Please run manually: pip install asyncpg==0.29.0 aiohttp==3.9.1")
    except Exception as e:
        print(f"⚠️  Warning: Could not install dependencies automatically: {e}")
        print("   Please run manually: pip install asyncpg==0.29.0 aiohttp==3.9.1")

def validate_deployment():
    """Validate the deployment by checking files exist"""
    required_files = [
        "src/db/connection_pool.py",
        "src/middleware/performance_middleware.py",
        "src/observability/metrics_collector.py",
        "src/observability/alert_system.py",
        "src/observability/health_monitor.py",
        "src/api/performance_endpoints.py"
    ]
    
    print("🔍 Validating deployment...")
    
    all_files_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_files_exist = False
    
    if all_files_exist:
        print("🎉 All performance monitoring files are in place!")
        return True
    else:
        print("⚠️  Some files are missing. Performance monitoring may not work correctly.")
        return False

def main():
    """Main deployment function"""
    print("🚀 WingmanMatch Performance Monitoring Deployment")
    print("=" * 60)
    
    try:
        # Step 1: Backup existing files
        backup_dir = backup_existing_files()
        
        # Step 2: Validate all required files exist
        if not validate_deployment():
            print("❌ Deployment validation failed. Please check missing files.")
            return
        
        # Step 3: Install dependencies
        install_dependencies()
        
        # Step 4: Integrate performance monitoring
        integrate_performance_monitoring()
        
        # Step 5: Create environment template
        create_environment_template()
        
        print("\n" + "=" * 60)
        print("🎉 PERFORMANCE MONITORING DEPLOYMENT COMPLETE!")
        print("=" * 60)
        
        print("\n📋 Next Steps:")
        print("1. Add performance monitoring environment variables to your .env file")
        print("2. Restart your FastAPI server")
        print("3. Test the new endpoints:")
        print("   - http://localhost:8000/api/performance/dashboard")
        print("   - http://localhost:8000/api/performance/health/status")
        print("4. Run the test script: python test_performance_monitoring.py")
        
        print(f"\n📁 Backup created at: {backup_dir}")
        print("   (Restore from backup if issues occur)")
        
        print("\n🔗 New Performance Monitoring Endpoints:")
        endpoints = [
            "/api/performance/metrics/realtime",
            "/api/performance/metrics/summary",
            "/api/performance/health/status",
            "/api/performance/alerts/active",
            "/api/performance/dashboard"
        ]
        for endpoint in endpoints:
            print(f"   - {endpoint}")
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print("Please check the error and try again, or restore from backup.")

if __name__ == "__main__":
    main()
