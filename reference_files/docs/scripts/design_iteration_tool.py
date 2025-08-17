#!/usr/bin/env python3
"""
Design Iteration Tool for Fridays at Four
==========================================

A development tool that helps with visual design iteration by:
1. Starting local development servers (frontend/backend)
2. Taking screenshots of different pages/states
3. Enabling comparison between iterations
4. Saving screenshots with timestamps for version tracking

Usage:
    python scripts/design_iteration_tool.py --init                    # Initial setup
    python scripts/design_iteration_tool.py --screenshot              # Take screenshots
    python scripts/design_iteration_tool.py --compare                 # Compare iterations
    python scripts/design_iteration_tool.py --serve                   # Start servers and open browser
"""

import os
import sys
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
import json
import webbrowser
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install")

class DesignIterationTool:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).absolute()
        self.screenshots_dir = self.project_root / "design_iterations"
        self.config_file = self.screenshots_dir / "config.json"
        self.backend_port = 8000
        self.frontend_port = 3000
        self.backend_url = f"http://localhost:{self.backend_port}"
        self.frontend_url = f"http://localhost:{self.frontend_port}"
        
        # Default pages to screenshot
        self.default_pages = [
            {"name": "landing", "url": "/", "description": "Landing page"},
            {"name": "chat", "url": "/chat", "description": "Chat interface"},
            {"name": "onboarding", "url": "/onboarding", "description": "Onboarding flow"},
            {"name": "dashboard", "url": "/dashboard", "description": "User dashboard"},
        ]
        
        self.ensure_directories()
    
    def ensure_directories(self):
        """Create necessary directories for screenshots and config"""
        self.screenshots_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different iterations
        for subdir in ["iterations", "comparisons", "current"]:
            (self.screenshots_dir / subdir).mkdir(exist_ok=True)
    
    def load_config(self) -> Dict:
        """Load configuration from config file"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        
        # Default config
        default_config = {
            "pages": self.default_pages,
            "viewport": {"width": 1920, "height": 1080},
            "mobile_viewport": {"width": 375, "height": 667},
            "delay_before_screenshot": 2000,  # ms
            "iterations": []
        }
        
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict):
        """Save configuration to config file"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def check_servers_running(self) -> Dict[str, bool]:
        """Check if backend and frontend servers are running"""
        import urllib.request
        
        status = {"backend": False, "frontend": False}
        
        # Check backend
        try:
            urllib.request.urlopen(f"{self.backend_url}/health", timeout=2)
            status["backend"] = True
        except:
            pass
        
        # Check frontend
        try:
            urllib.request.urlopen(self.frontend_url, timeout=2)
            status["frontend"] = True
        except:
            pass
        
        return status
    
    def start_backend(self) -> Optional[subprocess.Popen]:
        """Start the FastAPI backend server"""
        print("🚀 Starting backend server...")
        
        # Change to project root and start FastAPI
        backend_cmd = [
            sys.executable, "-m", "uvicorn", 
            "src.main:app", 
            "--host", "0.0.0.0", 
            "--port", str(self.backend_port),
            "--reload"
        ]
        
        try:
            process = subprocess.Popen(
                backend_cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a bit for server to start
            time.sleep(3)
            
            # Check if it's running
            status = self.check_servers_running()
            if status["backend"]:
                print(f"✅ Backend running at {self.backend_url}")
                return process
            else:
                print("❌ Backend failed to start")
                return None
                
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return None
    
    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Start the Next.js frontend server"""
        print("🚀 Starting frontend server...")
        
        # Look for frontend directory
        possible_frontend_dirs = [
            self.project_root / "frontend",
            self.project_root / "client", 
            self.project_root / "web",
            self.project_root  # If package.json is in root
        ]
        
        frontend_dir = None
        for dir_path in possible_frontend_dirs:
            if (dir_path / "package.json").exists():
                frontend_dir = dir_path
                break
        
        if not frontend_dir:
            print("❌ No frontend directory found (looking for package.json)")
            return None
        
        # Start Next.js dev server
        frontend_cmd = ["npm", "run", "dev"]
        
        try:
            # Set environment variable for backend URL
            env = os.environ.copy()
            env["NEXT_PUBLIC_BACKEND_API_URL"] = self.backend_url
            
            process = subprocess.Popen(
                frontend_cmd,
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for frontend to start
            print("⏳ Waiting for frontend to start...")
            for _ in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                status = self.check_servers_running()
                if status["frontend"]:
                    print(f"✅ Frontend running at {self.frontend_url}")
                    return process
            
            print("❌ Frontend failed to start within 30 seconds")
            return None
            
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return None
    
    def take_screenshots(self, iteration_name: Optional[str] = None) -> bool:
        """Take screenshots of all configured pages"""
        if not PLAYWRIGHT_AVAILABLE:
            print("❌ Playwright not available. Cannot take screenshots.")
            return False
        
        config = self.load_config()
        
        if not iteration_name:
            iteration_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"📸 Taking screenshots for iteration: {iteration_name}")
        
        # Create iteration directory
        iteration_dir = self.screenshots_dir / "iterations" / iteration_name
        iteration_dir.mkdir(parents=True, exist_ok=True)
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            
            # Desktop screenshots
            desktop_context = browser.new_context(
                viewport=config["viewport"]
            )
            desktop_page = desktop_context.new_page()
            
            # Mobile screenshots  
            mobile_context = browser.new_context(
                viewport=config["mobile_viewport"]
            )
            mobile_page = mobile_context.new_page()
            
            screenshots_taken = []
            
            for page_config in config["pages"]:
                page_name = page_config["name"]
                page_url = self.frontend_url + page_config["url"]
                
                print(f"  📱 Capturing {page_name}...")
                
                try:
                    # Desktop screenshot
                    desktop_page.goto(page_url)
                    desktop_page.wait_for_timeout(config["delay_before_screenshot"])
                    desktop_screenshot = iteration_dir / f"{page_name}_desktop.png"
                    desktop_page.screenshot(path=str(desktop_screenshot), full_page=True)
                    
                    # Mobile screenshot
                    mobile_page.goto(page_url)
                    mobile_page.wait_for_timeout(config["delay_before_screenshot"])
                    mobile_screenshot = iteration_dir / f"{page_name}_mobile.png"
                    mobile_page.screenshot(path=str(mobile_screenshot), full_page=True)
                    
                    screenshots_taken.extend([desktop_screenshot, mobile_screenshot])
                    print(f"    ✅ {page_name} (desktop & mobile)")
                    
                except Exception as e:
                    print(f"    ❌ Failed to capture {page_name}: {e}")
            
            browser.close()
        
        # Update config with this iteration
        config["iterations"].append({
            "name": iteration_name,
            "timestamp": datetime.now().isoformat(),
            "screenshots": len(screenshots_taken),
            "pages": [p["name"] for p in config["pages"]]
        })
        self.save_config(config)
        
        # Copy to 'current' for easy access
        current_dir = self.screenshots_dir / "current"
        for screenshot in screenshots_taken:
            import shutil
            shutil.copy2(screenshot, current_dir / screenshot.name)
        
        print(f"✅ Screenshots saved to: {iteration_dir}")
        print(f"📁 Current screenshots: {current_dir}")
        
        return True
    
    def list_iterations(self):
        """List all available iterations"""
        config = self.load_config()
        
        if not config["iterations"]:
            print("📭 No iterations found yet. Run with --screenshot to create your first iteration.")
            return
        
        print("📚 Available iterations:")
        for iteration in config["iterations"]:
            print(f"  • {iteration['name']} - {iteration['timestamp']} ({iteration['screenshots']} screenshots)")
    
    def serve_and_open(self):
        """Start servers and open browser for development"""
        print("🎨 Starting design iteration mode...")
        
        # Check current status
        status = self.check_servers_running()
        
        backend_process = None
        frontend_process = None
        
        try:
            # Start backend if not running
            if not status["backend"]:
                backend_process = self.start_backend()
                if not backend_process:
                    return False
            else:
                print(f"✅ Backend already running at {self.backend_url}")
            
            # Start frontend if not running  
            if not status["frontend"]:
                frontend_process = self.start_frontend()
                if not frontend_process:
                    return False
            else:
                print(f"✅ Frontend already running at {self.frontend_url}")
            
            # Open browser
            print(f"🌐 Opening browser to {self.frontend_url}")
            webbrowser.open(self.frontend_url)
            
            print("\n🎨 Design iteration mode active!")
            print("💡 Tips:")
            print("  • Make your code changes")
            print("  • Run 'python scripts/design_iteration_tool.py --screenshot' to capture current state")
            print("  • Use --compare to see differences between iterations")
            print("  • Press Ctrl+C to stop servers")
            
            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping servers...")
                
        finally:
            # Clean up processes
            if backend_process:
                backend_process.terminate()
            if frontend_process:
                frontend_process.terminate()
    
    def init_setup(self):
        """Initialize the design iteration tool"""
        print("🔧 Initializing Design Iteration Tool...")
        
        # Create config and directories
        config = self.load_config()
        
        print(f"✅ Created directories in: {self.screenshots_dir}")
        print(f"✅ Config file: {self.config_file}")
        
        # Install playwright if not available
        if not PLAYWRIGHT_AVAILABLE:
            print("\n📦 Installing Playwright...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
                subprocess.check_call([sys.executable, "-m", "playwright", "install"])
                print("✅ Playwright installed successfully")
            except subprocess.CalledProcessError:
                print("❌ Failed to install Playwright. Please install manually:")
                print("   pip install playwright && playwright install")
                return False
        
        print("\n🎉 Setup complete!")
        print("\n🚀 Next steps:")
        print("  1. Run: python scripts/design_iteration_tool.py --serve")
        print("  2. Make your design changes") 
        print("  3. Run: python scripts/design_iteration_tool.py --screenshot")
        print("  4. Repeat and compare iterations!")
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Design Iteration Tool for Visual Development")
    parser.add_argument("--init", action="store_true", help="Initialize the tool and install dependencies")
    parser.add_argument("--screenshot", help="Take screenshots (optional iteration name)")
    parser.add_argument("--serve", action="store_true", help="Start servers and open browser for development")
    parser.add_argument("--list", action="store_true", help="List all iterations")
    parser.add_argument("--compare", nargs=2, metavar=("iter1", "iter2"), help="Compare two iterations")
    
    args = parser.parse_args()
    
    tool = DesignIterationTool()
    
    if args.init:
        tool.init_setup()
    elif args.screenshot is not None:
        iteration_name = args.screenshot if args.screenshot else None
        tool.take_screenshots(iteration_name)
    elif args.serve:
        tool.serve_and_open()
    elif args.list:
        tool.list_iterations()
    elif args.compare:
        print(f"🔍 Comparison feature coming soon! Will compare {args.compare[0]} vs {args.compare[1]}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 