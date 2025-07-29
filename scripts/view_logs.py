#!/usr/bin/env python3
"""
Log Viewer Script for Talktor
Provides easy access to view and analyze log files
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.append(str(backend_path))

from core.log_utils import list_log_files, get_latest_log_file, tail_log_file, search_logs
import argparse


def main():
    parser = argparse.ArgumentParser(description="Talktor Log Viewer")
    parser.add_argument("--list", "-l", action="store_true", help="List all log files")
    parser.add_argument("--tail", "-t", type=int, default=50, help="Show last N lines of latest log")
    parser.add_argument("--service", "-s", type=str, help="Filter by service name")
    parser.add_argument("--search", type=str, help="Search for term in logs")
    parser.add_argument("--file", "-f", type=str, help="Specific log file to view")
    parser.add_argument("--follow", action="store_true", help="Follow log file (like tail -f)")
    
    args = parser.parse_args()
    
    # Change to backend directory for relative paths
    os.chdir(backend_path)
    
    if args.list:
        print("📁 Talktor Log Files")
        print("=" * 60)
        
        log_files = list_log_files()
        if not log_files:
            print("No log files found.")
            return
        
        for log_file in log_files:
            print(f"🗂️  {log_file['filename']}")
            print(f"   Service: {log_file['service']}")
            print(f"   Size: {log_file['size_mb']} MB")
            print(f"   Created: {log_file['timestamp']}")
            print()
    
    elif args.search:
        print(f"🔍 Searching for '{args.search}' in logs")
        print("=" * 60)
        
        results = search_logs(args.search, args.service)
        if not results:
            print("No matches found.")
            return
        
        for result in results:
            print(f"📄 {result['file']} (line {result['line_number']})")
            print(f"   {result['content']}")
            print()
    
    elif args.file:
        print(f"📄 Viewing log file: {args.file}")
        print("=" * 60)
        
        if args.follow:
            # Simple follow implementation
            import time
            try:
                with open(args.file, 'r') as f:
                    # Go to end of file
                    f.seek(0, 2)
                    print("Following log file... (Ctrl+C to stop)")
                    while True:
                        line = f.readline()
                        if line:
                            print(line.rstrip())
                        else:
                            time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopped following log file.")
        else:
            lines = tail_log_file(args.file, args.tail)
            for line in lines:
                print(line.rstrip())
    
    else:
        # Default: show latest log
        latest = get_latest_log_file(args.service)
        if not latest:
            print("No log files found.")
            return
        
        print(f"📄 Latest log file: {latest}")
        print("=" * 60)
        
        if args.follow:
            # Follow the latest log
            import time
            try:
                with open(latest, 'r') as f:
                    # Show last few lines first
                    lines = tail_log_file(latest, 10)
                    for line in lines:
                        print(line.rstrip())
                    
                    # Go to end and follow
                    f.seek(0, 2)
                    print("\nFollowing log file... (Ctrl+C to stop)")
                    while True:
                        line = f.readline()
                        if line:
                            print(line.rstrip())
                        else:
                            time.sleep(0.1)
            except KeyboardInterrupt:
                print("\nStopped following log file.")
        else:
            lines = tail_log_file(latest, args.tail)
            for line in lines:
                print(line.rstrip())


if __name__ == "__main__":
    main()
