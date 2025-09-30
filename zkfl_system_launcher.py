#!/usr/bin/env python3
"""
ZK-FL System Launcher
Launches both the configuration portal and production dashboard
"""

import asyncio
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

class ZKFLSystemLauncher:
    """Manages the complete ZK-FL system startup"""
    
    def __init__(self):
        self.processes = []
        
    def start_config_website(self):
        """Start the configuration website"""
        print("🔧 Starting ZK-FL Configuration Portal...")
        
        cmd = [sys.executable, "zkfl_config_website.py", "--host", "localhost", "--port", "8081"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )
        
        self.processes.append(("Config Portal", process))
        print("✅ Configuration Portal starting on http://localhost:8081")
        
    def start_production_dashboard(self):
        """Start the production dashboard"""
        print("📊 Starting ZK-FL Production Dashboard...")
        
        cmd = [sys.executable, "production_dashboard.py", "--host", "localhost", "--port", "8080"]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path.cwd()
        )
        
        self.processes.append(("Production Dashboard", process))
        print("✅ Production Dashboard starting on http://localhost:8080")
        
    def open_browsers(self):
        """Open browser tabs for both interfaces"""
        print("🌐 Opening browser interfaces...")
        
        time.sleep(3)  # Wait for servers to start
        
        try:
            webbrowser.open("http://localhost:8081")  # Config portal
            time.sleep(1)
            webbrowser.open("http://localhost:8080")  # Dashboard
            print("✅ Browser tabs opened")
        except Exception as e:
            print(f"⚠️ Could not open browsers automatically: {e}")
            print("💡 Manually open:")
            print("   • Configuration Portal: http://localhost:8081")
            print("   • Production Dashboard: http://localhost:8080")
            
    def show_system_info(self):
        """Display system information"""
        info = """
🚀 ZK-FL System Successfully Launched!
=====================================

📍 Access Points:
   • Configuration Portal: http://localhost:8081
   • Production Dashboard: http://localhost:8080

🔧 Configuration Portal Features:
   • Interactive parameter tweaking
   • Real-time validation
   • Export/Import configurations
   • Live sync with dashboard

📊 Production Dashboard Features:
   • Real-time FL monitoring
   • Performance visualization
   • Circuit optimization tracking
   • System health metrics

🎮 Getting Started:
   1. Use Configuration Portal to adjust parameters
   2. Monitor real-time changes in Dashboard
   3. Start FL simulations from Dashboard
   4. Export configurations for production

⚡ Key Parameters You Can Tweak:
   • Number of clients and rounds
   • Learning rates and batch sizes
   • Circuit optimization settings
   • Non-IID data distribution
   • Security and performance tuning

🛑 To Stop: Press Ctrl+C
        """
        print(info)
        
    def wait_for_shutdown(self):
        """Wait for user to stop the system"""
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down ZK-FL System...")
            self.cleanup()
            
    def cleanup(self):
        """Clean up all processes"""
        print("🧹 Cleaning up processes...")
        
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔥 {name} forcefully stopped")
            except Exception as e:
                print(f"⚠️ Error stopping {name}: {e}")
                
        print("✅ ZK-FL System shutdown complete")
        
    def run_system_demo(self):
        """Run a quick system demonstration"""
        print("🎬 Running ZK-FL System Demo...")
        print("=" * 40)
        
        # Start services
        self.start_config_website()
        self.start_production_dashboard()
        
        # Wait for startup
        print("⏳ Waiting for services to initialize...")
        time.sleep(5)
        
        # Open browsers
        self.open_browsers()
        
        # Show info
        self.show_system_info()
        
        # Wait for shutdown
        self.wait_for_shutdown()

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ZK-FL System Launcher")
    parser.add_argument("--demo", action="store_true", help="Run interactive demo")
    parser.add_argument("--config-only", action="store_true", help="Start config portal only")
    parser.add_argument("--dashboard-only", action="store_true", help="Start dashboard only")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    launcher = ZKFLSystemLauncher()
    
    try:
        if args.demo:
            launcher.run_system_demo()
        elif args.config_only:
            print("🔧 Starting Configuration Portal only...")
            launcher.start_config_website()
            if not args.no_browser:
                time.sleep(3)
                webbrowser.open("http://localhost:8081")
            print("🔧 Configuration Portal running at http://localhost:8081")
            launcher.wait_for_shutdown()
        elif args.dashboard_only:
            print("📊 Starting Production Dashboard only...")
            launcher.start_production_dashboard()
            if not args.no_browser:
                time.sleep(3)
                webbrowser.open("http://localhost:8080")
            print("📊 Production Dashboard running at http://localhost:8080")
            launcher.wait_for_shutdown()
        else:
            # Default: start both
            print("🚀 Starting Complete ZK-FL System...")
            launcher.start_config_website()
            launcher.start_production_dashboard()
            
            if not args.no_browser:
                launcher.open_browsers()
                
            launcher.show_system_info()
            launcher.wait_for_shutdown()
            
    except KeyboardInterrupt:
        print("\n🛑 System startup interrupted")
        launcher.cleanup()
    except Exception as e:
        print(f"❌ System error: {e}")
        launcher.cleanup()

if __name__ == "__main__":
    main()