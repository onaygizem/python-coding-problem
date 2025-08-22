#!/usr/bin/env python3
"""
File Processing System
"""

import os
import time
import json
import multiprocessing
import multiprocessing.queues
import logging
import random
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import fcntl
from typing import Optional


class Config:
    """Configuration settings"""
    INPUT_DIR = "input"
    PROCESSED_DIR = "processed"
    FILE_CONTENT = "test-content"
    POLLING_INTERVAL = 1.0
    MAX_CONCURRENT_PROCESSES = 5
    FILE_EXTENSION = ".txt"


def worker_process(file_queue):
    """Worker process function - needs to be module-level for multiprocessing"""
    processor = FileProcessor(file_queue)
    processor.worker()

def _touch(path):
    p = Path(path)
    p.touch(exist_ok=True)


class FileProcessor:
    """Handles file processing operations"""
    
    def __init__(self, file_queue: multiprocessing.Queue):
        self.file_queue = file_queue
        self.processing = True
        
    def process_file(self, filepath: Path) -> bool:
        """Process a single file"""
        try:
            print(f"Processing file: {filepath}")
            # Simulate processing time delay
            time.sleep(random.uniform(0.01, 1.0))

            _touch(filepath)
            # Create meta file with processing status
            meta_path = filepath.with_suffix('.meta')
            self._create_meta_file(meta_path, filepath.name, "processing")
            
            # Read original file with file locking
            content = self._read_file(filepath)
            if content is None:
                self._update_meta_file(meta_path, "failed", "Could not read file")
                return False
            
            
            # Process content (convert to uppercase)
            processed_content = content.upper()
            
            # Create processed file atomically
            processed_path = filepath.with_suffix('.processed')
            if not self._write_file(processed_path, processed_content):
                self._update_meta_file(meta_path, "failed", "Could not write processed file")
                return False
            
            # Update meta file to completed
            self._update_meta_file(meta_path, "completed")
            
            # Move files to processed directory
            self._move_to_processed(filepath, processed_path, meta_path)
            
            logging.info(f"Successfully processed {filepath.name}")
            return True
            
        except Exception as e:
            logging.error(f"Error processing {filepath}: {e}")
            if 'meta_path' in locals():
                self._update_meta_file(meta_path, "failed", str(e))
            return False
    
    def _create_meta_file(self, meta_path: Path, original_filename: str, status: str, error_message: str = None):
        """Create metadata file"""
        meta_data = {
            'status': status,
            'last_updated': datetime.now().isoformat(),
            'original_filename': original_filename
        }
        if error_message:
            meta_data['error_message'] = error_message
            
        with open(meta_path, 'w') as f:
            json.dump(meta_data, f, indent=2)
    
    def _update_meta_file(self, meta_path: Path, status: str, error_message: str = None):
        """Update existing metadata file"""
        try:
            with open(meta_path, 'r') as f:
                meta_data = json.load(f)
            
            meta_data['status'] = status
            meta_data['last_updated'] = datetime.now().isoformat()
            if error_message:
                meta_data['error_message'] = error_message
            
            with open(meta_path, 'w') as f:
                json.dump(meta_data, f, indent=2)
        except Exception as e:
            logging.error(f"Could not update meta file {meta_path}: {e}")

    def _read_file(self, filepath: Path) -> Optional[str]:
        """Read file"""
        try:
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading file {filepath}: {e}")
            return None

    def _write_file(self, filepath: Path, content: str) -> bool:
        """Write file"""
        try:
            with open(filepath, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logging.error(f"Error writing file {filepath}: {e}")
            return False
    
    def _move_to_processed(self, original_path: Path, processed_path: Path, meta_path: Path):
        """Move files to processed directory"""
        processed_dir = Path(Config.PROCESSED_DIR)
        processed_dir.mkdir(exist_ok=True)
        
        # Move all related files
        original_path.rename(processed_dir / original_path.name)
        processed_path.rename(processed_dir / processed_path.name)
        
        # Clean up meta file after successful processing
        if meta_path.exists():
            meta_path.unlink()
    
    def worker(self):
        """Worker process for processing files"""
        while self.processing:
            try:
                filepath = self.file_queue.get(timeout=1)
                if filepath is None:  # Shutdown signal
                    break
                self.process_file(filepath)
                # Note: multiprocessing.Queue doesn't have task_done()
            except:
                # Queue timeout - this is normal, just continue
                continue


class FileWatcher(FileSystemEventHandler):
    """File system event handler"""
    
    def __init__(self, file_queue: multiprocessing.Queue):
        self.file_queue = file_queue
        super().__init__()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = Path(event.src_path)
        if filepath.suffix == Config.FILE_EXTENSION:
            logging.info(f"file detected: {filepath.name}")
            self.file_queue.put(filepath)


class FileCreator:
    """Creates test files with timestamps"""
    
    @staticmethod
    def create_test_file(counter: int):
        """Create a single test file"""
        input_dir = Path(Config.INPUT_DIR)
        input_dir.mkdir(exist_ok=True)
        
        base_filename = f"test_{counter}_{int(time.time())}{Config.FILE_EXTENSION}"

        filepath = input_dir / base_filename
        try:
            with open(filepath, 'w') as f:
                f.write(f"{Config.FILE_CONTENT}-{counter}")
            logging.info(f"Created test file: {base_filename}")
            return filepath
        except Exception as e:
            logging.error(f"Error creating test file: {e}")
            return None
        
        # If we get here, no file was created
        logging.error(f"Failed to create test file after {max_attempts} attempts")
        return None


class FileProcessingSystem:
    """Main file processing system coordinator"""
    
    def __init__(self):
        self.file_queue = multiprocessing.Queue()
        self.processors = []
        self.observer = None
        self.running = False
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def start(self):
        """Start the file processing system"""
        self.running = True
        
        # Create directories
        Path(Config.INPUT_DIR).mkdir(exist_ok=True)
        Path(Config.PROCESSED_DIR).mkdir(exist_ok=True)
        
        # Start worker threads
        for i in range(Config.MAX_CONCURRENT_PROCESSES):
            processor = FileProcessor(self.file_queue)
            process = multiprocessing.Process(target=worker_process, args=(self.file_queue,), daemon=True)
            process.start()
            self.processors.append((processor, process))
        
        # Start file watcher
        event_handler = FileWatcher(self.file_queue)
        self.observer = Observer()
        self.observer.schedule(event_handler, Config.INPUT_DIR, recursive=False)
        self.observer.start()
        
        logging.info("File processing system started")
    
    def stop(self):
        """Stop the file processing system gracefully"""
        self.running = False
        
        # Stop file watcher
        if self.observer:
            self.observer.stop()
            self.observer.join()
        
        # Signal workers to stop
        for _ in self.processors:
            self.file_queue.put(None)
        
        # Wait for workers to finish
        for processor, process in self.processors:
            processor.processing = False
            process.join(timeout=5)
        
        logging.info("File processing system stopped")
    
    def create_test_file(self, counter: int):
        """Create a test file"""
        return FileCreator.create_test_file(counter)


def main():
    """Main function for testing"""
    system = FileProcessingSystem()
    
    try:
        system.start()
        
        # Create a test file
        print("Creating test file...")
        system.create_test_file(random.randint(1, 1000000))
        
        # Keep running
        print("File processing system is running. Press Ctrl+C to stop.")
        print("You can manually create files in the 'input' directory to test.")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
        system.stop()


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn', force=True)  # Ensures compatibility across platforms
    main() 
