"""
FL System Launcher - Start FL server and multiple clients
Demonstrates the complete FL+MLP system with ZKP integration
"""

import asyncio
import subprocess
import time
import logging
import signal
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FLSystemLauncher:
    """Launcher for complete FL system"""
    
    def __init__(self):
        self.processes = []
        self.server_process = None
    
    def start_server(self):
        """Start the FL server"""
        logger.info("Starting FL server...")
        
        cmd = [sys.executable, "fl_server.py"]
        self.server_process = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(self.server_process)
        logger.info(f"FL server started with PID {self.server_process.pid}")
        
        # Give server time to start
        time.sleep(3)
    
    def start_client(self, client_id: str, data_fraction: float = 0.1):
        """Start a single FL client"""
        logger.info(f"Starting client {client_id}...")
        
        cmd = [sys.executable, "fl_client.py", client_id, str(data_fraction)]
        process = subprocess.Popen(
            cmd,
            cwd=Path.cwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        self.processes.append(process)
        logger.info(f"Client {client_id} started with PID {process.pid}")
    
    def start_multiple_clients(self, num_clients: int = 3, base_data_fraction: float = 0.1):
        """Start multiple FL clients with different data distributions"""
        for i in range(num_clients):
            client_id = f"client_{i+1}"
            # Vary data fraction slightly for each client
            data_fraction = base_data_fraction * (0.8 + 0.4 * i / max(1, num_clients-1))
            self.start_client(client_id, data_fraction)
            time.sleep(2)  # Stagger client starts
    
    def monitor_processes(self):
        """Monitor running processes and display output"""
        logger.info("Monitoring FL system processes...")
        
        try:
            while True:
                # Check if server is still running
                if self.server_process and self.server_process.poll() is not None:
                    logger.error("FL server has stopped")
                    break
                
                # Check clients
                active_clients = 0
                for process in self.processes[1:]:  # Skip server process
                    if process.poll() is None:
                        active_clients += 1
                
                if active_clients == 0:
                    logger.info("All clients have finished")
                    break
                
                logger.info(f"FL system running: server + {active_clients} clients")
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.shutdown()
    
    def shutdown(self):
        """Shutdown all processes"""
        logger.info("Shutting down FL system...")
        
        for process in self.processes:
            if process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
        
        logger.info("All processes shut down")
    
    def run_fl_demo(self, num_clients: int = 3, duration_minutes: int = 10):
        """Run a complete FL demonstration"""
        logger.info(f"Starting FL demo with {num_clients} clients for {duration_minutes} minutes")
        
        try:
            # Start server
            self.start_server()
            
            # Start clients
            self.start_multiple_clients(num_clients)
            
            # Monitor for specified duration
            start_time = time.time()
            while time.time() - start_time < duration_minutes * 60:
                active_processes = sum(1 for p in self.processes if p.poll() is None)
                logger.info(f"FL demo running: {active_processes} active processes")
                time.sleep(30)
            
            logger.info("FL demo duration completed")
            
        except KeyboardInterrupt:
            logger.info("FL demo interrupted")
        finally:
            self.shutdown()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal")
    sys.exit(0)

def main():
    """Main launcher function"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    launcher = FLSystemLauncher()
    
    try:
        # Run FL demonstration
        launcher.run_fl_demo(num_clients=3, duration_minutes=5)
    except Exception as e:
        logger.error(f"Error in FL system: {e}")
    finally:
        launcher.shutdown()

if __name__ == "__main__":
    main()