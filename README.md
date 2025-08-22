# File Processing System


## Features

- **Automated file processing**: Monitors input directory and processes files automatically
- **Concurrent processing**: Uses threading with configurable worker count
- **File safety**: Implements file locking and atomic operations
- **Metadata tracking**: Creates .meta files with processing status
- **Error handling**: Comprehensive error handling with status tracking
- **Graceful shutdown**: Clean shutdown with Ctrl+C

## Requirements

- Python 3.7+
- watchdog library for file system monitoring

## Installation
1. Create python env
```bash
python3 -m venv env
source env/bin/activate 
``` 
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Start the File Processing System

```bash
python file_processor.py
```

This will:
- Start the file processing system
- Create one test file automatically
- Monitor the `input/` directory for new .txt files
- Process files and move them to `processed/` directory

### Create Test Files

Use the test script to create multiple files:

```bash
# Create 5 files with no delay
python test_script.py 5 0

# Create 10 files at 0.5-second intervals
python test_script.py 10 0.5
```

## Directory Structure

After running, `input` and `processed` dir will be created:

```
.
├── input/          # Input directory (monitored)
├── processed/      # Completed files moved here
├── file_processor.py
├── test_script.py
└── requirements.txt
```

### Challenge!
When we create 5 files with the test script `python test_script.py 5 0` only one file gets created, There's a race condition and thats the first challenge.

## File Processing Flow

1. **File Creation**: Test script creates timestamped .txt files in `input/`
2. **Detection**: File watcher detects new files
3. **Metadata**: Creates .meta file with "processing" status
4. **Processing**: Reads content, converts to uppercase, saves as .processed file
5. **Completion**: Updates metadata to "completed", moves all files to `processed/`
6. **Cleanup**: Deletes .meta file after successful processing

## Configuration

Edit the `Config` class in `file_processor.py`:

```python
class Config:
    INPUT_DIR = "input"
    PROCESSED_DIR = "processed"
    FILE_CONTENT = "test-content"
    POLLING_INTERVAL = 1.0
    MAX_CONCURRENT_PROCESSES = 3
    FILE_EXTENSION = ".txt"
```

## File Types

- **Original files**: `test_YYYYMMDD_HHMMSS_mmm.txt`
- **Processed files**: `test_YYYYMMDD_HHMMSS_mmm.processed`
- **Metadata files**: `test_YYYYMMDD_HHMMSS_mmm.meta` (temporary)

## Metadata Format

```json
{
  "status": "processing|completed|failed",
  "last_updated": "2024-01-15T10:30:00.123456",
  "original_filename": "test_20240115_103000_123.txt",
  "error_message": "optional error details"
}
```


## Testing

1. Start the processor: `python file_processor.py`
2. In another terminal, create test files: `python test_script.py 3`
3. Watch the logs and check the `processed/` directory

## Stopping

Press `Ctrl+C` to gracefully shutdown the system. All workers will finish current tasks before stopping. 
