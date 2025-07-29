"""
Log utilities for Talktor backend
Provides helper functions for log management and analysis
"""
import os
import glob
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


def list_log_files(log_directory: str = "logs") -> List[Dict[str, str]]:
    """
    List all log files in the log directory with metadata
    
    Args:
        log_directory: Directory containing log files
        
    Returns:
        List of dictionaries with log file information
    """
    log_dir = Path(log_directory)
    if not log_dir.exists():
        return []
    
    log_files = []
    for log_file in log_dir.glob("*.log"):
        stat = log_file.stat()
        
        # Parse timestamp and service from filename
        filename = log_file.stem
        parts = filename.split("_", 1)
        
        if len(parts) >= 2:
            timestamp_str = parts[0]
            service_name = parts[1]
            
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except ValueError:
                timestamp = datetime.fromtimestamp(stat.st_mtime)
        else:
            timestamp = datetime.fromtimestamp(stat.st_mtime)
            service_name = filename
        
        log_files.append({
            "filepath": str(log_file),
            "filename": log_file.name,
            "service": service_name,
            "timestamp": timestamp.isoformat(),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    # Sort by timestamp (newest first)
    log_files.sort(key=lambda x: x["timestamp"], reverse=True)
    return log_files


def get_latest_log_file(service_name: Optional[str] = None, log_directory: str = "logs") -> Optional[str]:
    """
    Get the path to the latest log file, optionally filtered by service
    
    Args:
        service_name: Optional service name to filter by
        log_directory: Directory containing log files
        
    Returns:
        Path to the latest log file or None if not found
    """
    log_files = list_log_files(log_directory)
    
    if service_name:
        log_files = [f for f in log_files if f["service"] == service_name]
    
    if log_files:
        return log_files[0]["filepath"]
    
    return None


def tail_log_file(filepath: str, lines: int = 50) -> List[str]:
    """
    Get the last N lines from a log file
    
    Args:
        filepath: Path to the log file
        lines: Number of lines to return
        
    Returns:
        List of log lines
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines
    except Exception as e:
        return [f"Error reading log file: {e}"]


def cleanup_old_logs(log_directory: str = "logs", days_to_keep: int = 7) -> int:
    """
    Remove log files older than specified days
    
    Args:
        log_directory: Directory containing log files
        days_to_keep: Number of days to keep logs
        
    Returns:
        Number of files deleted
    """
    log_dir = Path(log_directory)
    if not log_dir.exists():
        return 0
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    deleted_count = 0
    
    for log_file in log_dir.glob("*.log"):
        stat = log_file.stat()
        file_date = datetime.fromtimestamp(stat.st_mtime)
        
        if file_date < cutoff_date:
            try:
                log_file.unlink()
                deleted_count += 1
            except Exception:
                pass  # Ignore errors when deleting
    
    return deleted_count


def search_logs(search_term: str, service_name: Optional[str] = None, 
                log_directory: str = "logs", max_results: int = 100) -> List[Dict[str, str]]:
    """
    Search for a term across log files
    
    Args:
        search_term: Term to search for
        service_name: Optional service name to filter by
        log_directory: Directory containing log files
        max_results: Maximum number of results to return
        
    Returns:
        List of matching log entries with context
    """
    log_files = list_log_files(log_directory)
    
    if service_name:
        log_files = [f for f in log_files if f["service"] == service_name]
    
    results = []
    
    for log_file in log_files:
        if len(results) >= max_results:
            break
            
        try:
            with open(log_file["filepath"], 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if search_term.lower() in line.lower():
                        results.append({
                            "file": log_file["filename"],
                            "service": log_file["service"],
                            "line_number": line_num,
                            "content": line.strip(),
                            "timestamp": log_file["timestamp"]
                        })
                        
                        if len(results) >= max_results:
                            break
        except Exception:
            continue  # Skip files that can't be read
    
    return results


if __name__ == "__main__":
    # Demo script
    print("📁 Talktor Log Management Utility")
    print("=" * 50)
    
    # List all log files
    log_files = list_log_files()
    print(f"\n📋 Found {len(log_files)} log files:")
    
    for log_file in log_files[:10]:  # Show first 10
        print(f"  🗂️  {log_file['filename']} ({log_file['size_mb']} MB)")
        print(f"      Service: {log_file['service']}")
        print(f"      Created: {log_file['timestamp']}")
        print()
    
    # Show latest log
    latest = get_latest_log_file()
    if latest:
        print(f"\n📄 Latest log file: {latest}")
        print("\n📝 Last 10 lines:")
        lines = tail_log_file(latest, 10)
        for line in lines:
            print(f"    {line.rstrip()}")
