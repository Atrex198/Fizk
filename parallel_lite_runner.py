#!/usr/bin/env python3
"""
Parallel Lite ZKP-FL Runner
============================

Runs multiple lite FL configurations simultaneously with real-time progress tracking.
Each configuration runs in a separate process with progress displayed in a dashboard.

Usage:
    python parallel_lite_runner.py
    
Author: ZKP-FL Team
"""

import asyncio
import subprocess
import sys
import os
import json
import time
import signal
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import threading
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


@dataclass
class LiteConfig:
    """Configuration for a single lite FL run"""
    name: str
    num_clients: int = 2
    num_rounds: int = 1
    local_epochs: int = 1
    batch_size: int = 64
    learning_rate: float = 0.001
    security_level: int = 128
    srs_size: int = 64
    
    def to_env(self) -> Dict[str, str]:
        """Convert to environment variables"""
        return {
            'ZKP_FL_LITE_MODE': 'true',
            'ZKP_FL_NUM_CLIENTS': str(self.num_clients),
            'ZKP_FL_NUM_ROUNDS': str(self.num_rounds),
            'ZKP_FL_LOCAL_EPOCHS': str(self.local_epochs),
            'ZKP_FL_BATCH_SIZE': str(self.batch_size),
            'ZKP_FL_LEARNING_RATE': str(self.learning_rate),
            'ZKP_FL_SECURITY_LEVEL': str(self.security_level),
            'ZKP_FL_SRS_SIZE': str(self.srs_size),
        }


@dataclass
class RunProgress:
    """Track progress of a single run"""
    config_name: str
    status: str = "pending"  # pending, running, completed, failed
    current_round: int = 0
    total_rounds: int = 0
    current_client: int = 0
    total_clients: int = 0
    phase: str = "initializing"
    accuracy: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0
    run_dir: str = ""
    error: str = ""
    log_lines: List[str] = field(default_factory=list)


# Define 6 different lite configurations to run in parallel
LITE_CONFIGS = [
    LiteConfig(
        name="Quick-2x1",
        num_clients=2,
        num_rounds=1,
        local_epochs=1,
        learning_rate=0.001,
    ),
    LiteConfig(
        name="Standard-2x2",
        num_clients=2,
        num_rounds=2,
        local_epochs=2,
        learning_rate=0.001,
    ),
    LiteConfig(
        name="Extended-2x3",
        num_clients=2,
        num_rounds=3,
        local_epochs=2,
        learning_rate=0.001,
    ),
    LiteConfig(
        name="MultiClient-3x2",
        num_clients=3,
        num_rounds=2,
        local_epochs=2,
        learning_rate=0.001,
    ),
    LiteConfig(
        name="DeepTrain-2x2x3",
        num_clients=2,
        num_rounds=2,
        local_epochs=3,
        learning_rate=0.0005,
    ),
    LiteConfig(
        name="FullScale-3x3",
        num_clients=3,
        num_rounds=3,
        local_epochs=2,
        learning_rate=0.001,
    ),
]


class ProgressTracker:
    """Track and display progress of all parallel runs"""
    
    def __init__(self, configs: List[LiteConfig]):
        self.configs = configs
        self.progress: Dict[str, RunProgress] = {
            cfg.name: RunProgress(
                config_name=cfg.name,
                total_rounds=cfg.num_rounds,
                total_clients=cfg.num_clients,
            )
            for cfg in configs
        }
        self.lock = threading.Lock()
        self.running = True
        
    def update(self, config_name: str, **kwargs):
        """Update progress for a specific config"""
        with self.lock:
            if config_name in self.progress:
                for key, value in kwargs.items():
                    if hasattr(self.progress[config_name], key):
                        setattr(self.progress[config_name], key, value)
    
    def add_log(self, config_name: str, line: str):
        """Add a log line for a specific config"""
        with self.lock:
            if config_name in self.progress:
                self.progress[config_name].log_lines.append(line)
                # Keep only last 5 lines
                if len(self.progress[config_name].log_lines) > 5:
                    self.progress[config_name].log_lines.pop(0)
                    
                # Parse progress from log line
                self._parse_log_line(config_name, line)
    
    def _parse_log_line(self, config_name: str, line: str):
        """Parse log line to extract progress info"""
        prog = self.progress[config_name]
        
        # Detect round progress
        if "Starting round" in line:
            try:
                parts = line.split("round")[1].split("/")
                prog.current_round = int(parts[0].strip())
                prog.phase = f"Round {prog.current_round}/{prog.total_rounds}"
            except:
                pass
        
        # Detect client training
        if "Client" in line and "training" in line.lower():
            prog.phase = "Training clients"
            
        # Detect proof generation
        if "proof" in line.lower() and "generat" in line.lower():
            prog.phase = "Generating proofs"
            
        # Detect aggregation
        if "aggregat" in line.lower():
            prog.phase = "Aggregating"
            
        # Detect accuracy
        if "accuracy" in line.lower():
            try:
                # Try to extract accuracy value
                import re
                match = re.search(r'accuracy[:\s]+([0-9.]+)', line.lower())
                if match:
                    prog.accuracy = float(match.group(1))
            except:
                pass
                
        # Detect completion
        if "completed" in line.lower() or "finished" in line.lower():
            if "round" in line.lower():
                prog.phase = "Round completed"
            elif "training" in line.lower():
                prog.status = "completed"
                prog.phase = "Completed"
    
    def get_status_icon(self, status: str) -> str:
        """Get icon for status"""
        icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
        }
        return icons.get(status, "❓")
    
    def get_progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """Generate a progress bar"""
        if total == 0:
            return "─" * width
        
        filled = int((current / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar
    
    def format_time(self, seconds: float) -> str:
        """Format time duration"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            mins = seconds // 60
            secs = seconds % 60
            return f"{mins:.0f}m {secs:.0f}s"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours:.0f}h {mins:.0f}m"
    
    def render(self) -> str:
        """Render the progress dashboard"""
        lines = []
        
        # Header
        lines.append("")
        lines.append(f"{Colors.BOLD}{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.ENDC}")
        lines.append(f"{Colors.BOLD}{Colors.CYAN}║{'ZKP-FL Parallel Lite Runner':^78}║{Colors.ENDC}")
        lines.append(f"{Colors.BOLD}{Colors.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.ENDC}")
        lines.append("")
        
        # Stats summary
        completed = sum(1 for p in self.progress.values() if p.status == "completed")
        running = sum(1 for p in self.progress.values() if p.status == "running")
        failed = sum(1 for p in self.progress.values() if p.status == "failed")
        pending = sum(1 for p in self.progress.values() if p.status == "pending")
        
        lines.append(f"  {Colors.GREEN}✅ Completed: {completed}{Colors.ENDC}  "
                    f"{Colors.YELLOW}🔄 Running: {running}{Colors.ENDC}  "
                    f"{Colors.RED}❌ Failed: {failed}{Colors.ENDC}  "
                    f"{Colors.DIM}⏳ Pending: {pending}{Colors.ENDC}")
        lines.append("")
        lines.append(f"  {'─' * 76}")
        lines.append("")
        
        # Individual run progress
        for config in self.configs:
            prog = self.progress[config.name]
            
            # Status icon and name
            icon = self.get_status_icon(prog.status)
            
            # Color based on status
            if prog.status == "completed":
                color = Colors.GREEN
            elif prog.status == "failed":
                color = Colors.RED
            elif prog.status == "running":
                color = Colors.YELLOW
            else:
                color = Colors.DIM
            
            # Config info
            config_info = f"{config.num_clients}C×{config.num_rounds}R×{config.local_epochs}E"
            
            # Progress bar
            if prog.total_rounds > 0:
                progress_bar = self.get_progress_bar(prog.current_round, prog.total_rounds)
                progress_pct = (prog.current_round / prog.total_rounds) * 100
            else:
                progress_bar = self.get_progress_bar(0, 1)
                progress_pct = 0
            
            # Time info
            if prog.start_time > 0:
                if prog.end_time > 0:
                    elapsed = prog.end_time - prog.start_time
                else:
                    elapsed = time.time() - prog.start_time
                time_str = self.format_time(elapsed)
            else:
                time_str = "--"
            
            # Accuracy
            if prog.accuracy > 0:
                acc_str = f"{prog.accuracy*100:.1f}%"
            else:
                acc_str = "--"
            
            # Main line
            lines.append(f"  {icon} {color}{config.name:<16}{Colors.ENDC} "
                        f"[{config_info:^12}] "
                        f"{progress_bar} {progress_pct:5.1f}%  "
                        f"⏱ {time_str:>8}  "
                        f"📊 {acc_str:>6}")
            
            # Phase info
            if prog.status == "running":
                lines.append(f"     {Colors.DIM}└─ {prog.phase}{Colors.ENDC}")
            elif prog.status == "failed" and prog.error:
                lines.append(f"     {Colors.RED}└─ Error: {prog.error[:60]}{Colors.ENDC}")
            
        lines.append("")
        lines.append(f"  {'─' * 76}")
        lines.append(f"  {Colors.DIM}Press Ctrl+C to stop all runs{Colors.ENDC}")
        lines.append("")
        
        return "\n".join(lines)
    
    def display_loop(self):
        """Continuously update the display"""
        while self.running:
            # Clear screen and move cursor to top
            print("\033[2J\033[H", end="")
            print(self.render())
            time.sleep(0.5)


def run_single_config(config: LiteConfig, tracker: ProgressTracker) -> Dict:
    """Run a single FL configuration and track progress"""
    
    tracker.update(config.name, status="running", start_time=time.time())
    
    # Set up environment
    env = os.environ.copy()
    env.update(config.to_env())
    
    # Run the production script
    script_path = Path(__file__).parent / "production_zkp_fl_real.py"
    
    try:
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        # Read output line by line
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            line = line.strip()
            if line:
                tracker.add_log(config.name, line)
                
                # Check for run directory
                if "Run directory:" in line:
                    run_dir = line.split(":")[-1].strip()
                    tracker.update(config.name, run_dir=run_dir)
                
                # Check for final accuracy
                if "Final Accuracy:" in line or "final_accuracy" in line:
                    try:
                        import re
                        match = re.search(r'([0-9.]+)', line.split(":")[-1])
                        if match:
                            acc = float(match.group(1))
                            if acc < 1:  # Already decimal
                                tracker.update(config.name, accuracy=acc)
                            else:  # Percentage
                                tracker.update(config.name, accuracy=acc/100)
                    except:
                        pass
        
        process.wait()
        
        if process.returncode == 0:
            tracker.update(
                config.name,
                status="completed",
                phase="Completed",
                end_time=time.time(),
                current_round=config.num_rounds,
            )
            return {"success": True, "config": config.name}
        else:
            tracker.update(
                config.name,
                status="failed",
                phase="Failed",
                end_time=time.time(),
                error=f"Exit code: {process.returncode}",
            )
            return {"success": False, "config": config.name, "error": f"Exit code: {process.returncode}"}
            
    except Exception as e:
        tracker.update(
            config.name,
            status="failed",
            phase="Failed",
            end_time=time.time(),
            error=str(e),
        )
        return {"success": False, "config": config.name, "error": str(e)}


def run_config_wrapper(args):
    """Wrapper for multiprocessing"""
    config, tracker = args
    return run_single_config(config, tracker)


def main():
    print(f"\n{Colors.BOLD}{Colors.CYAN}🚀 Starting Parallel Lite ZKP-FL Runner{Colors.ENDC}\n")
    print(f"Running {len(LITE_CONFIGS)} configurations in parallel...\n")
    
    # Create progress tracker
    tracker = ProgressTracker(LITE_CONFIGS)
    
    # Start display thread
    display_thread = threading.Thread(target=tracker.display_loop, daemon=True)
    display_thread.start()
    
    # Use ThreadPoolExecutor for parallel execution with shared tracker
    from concurrent.futures import ThreadPoolExecutor
    
    results = []
    
    try:
        with ThreadPoolExecutor(max_workers=len(LITE_CONFIGS)) as executor:
            futures = {
                executor.submit(run_single_config, config, tracker): config
                for config in LITE_CONFIGS
            }
            
            for future in as_completed(futures):
                config = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        "success": False,
                        "config": config.name,
                        "error": str(e)
                    })
    
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}⚠️  Stopping all runs...{Colors.ENDC}\n")
        tracker.running = False
        return
    
    # Stop display
    tracker.running = False
    time.sleep(0.6)
    
    # Print final summary
    print("\033[2J\033[H", end="")
    print(f"\n{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}                    FINAL RESULTS SUMMARY                       {Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}\n")
    
    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]
    
    print(f"  {Colors.GREEN}✅ Successful: {len(successful)}{Colors.ENDC}")
    print(f"  {Colors.RED}❌ Failed: {len(failed)}{Colors.ENDC}\n")
    
    if successful:
        print(f"  {Colors.GREEN}Successful Runs:{Colors.ENDC}")
        for r in successful:
            prog = tracker.progress[r["config"]]
            elapsed = prog.end_time - prog.start_time
            acc = prog.accuracy * 100 if prog.accuracy > 0 else 0
            print(f"    • {r['config']}: {acc:.1f}% accuracy in {tracker.format_time(elapsed)}")
            if prog.run_dir:
                print(f"      {Colors.DIM}└─ {prog.run_dir}{Colors.ENDC}")
    
    if failed:
        print(f"\n  {Colors.RED}Failed Runs:{Colors.ENDC}")
        for r in failed:
            print(f"    • {r['config']}: {r.get('error', 'Unknown error')}")
    
    print(f"\n{Colors.CYAN}═══════════════════════════════════════════════════════════════{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
