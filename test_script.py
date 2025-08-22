#!/usr/bin/env python3
"""
Test script to create files in input directory
"""

import time
import sys
from pathlib import Path
from file_processor import FileCreator, Config
from concurrent.futures import ThreadPoolExecutor

def create_multiple_test_files(count: int = 1, interval: float = 2.0):
    """Create multiple test files with specified interval"""
    print(f"Creating {count} test files with {interval}s interval...")
    
    if interval == 0:
        # Create all files simultaneously if no interval
        with ThreadPoolExecutor(max_workers=5) as executor:
            jobs = list(executor.map(FileCreator.create_test_file, range(1, count + 1)))
        print(f"Created {count} files simultaneously")
    else:
        # Create files sequentially with interval
        for i in range(1, count + 1):
            filepath = FileCreator.create_test_file(i)
            if filepath:
                print(f"Created: {filepath.name}")
            else:
                print(f"Failed to create file {i}")
            
            if i < count:  # Don't sleep after the last file
                time.sleep(interval)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python test_script.py <number_of_files> [interval_seconds]")
        print("Example: python test_script.py 5 1.5")
        sys.exit(1)
    
    try:
        count = int(sys.argv[1])
        interval = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
        
        if count <= 0:
            print("Number of files must be positive")
            sys.exit(1)
        
        create_multiple_test_files(count, interval)
        print(f"Finished creating {count} test files")
        
    except ValueError:
        print("Invalid arguments. Please provide numbers.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main() 
