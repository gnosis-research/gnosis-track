"""
Log streaming utilities for gnosis-track.

Provides real-time log streaming and monitoring capabilities.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable

from gnosis_track.core.seaweed_client import SeaweedClient


class LogStreamer:
    """
    Real-time log streaming from SeaweedFS storage.
    
    Provides functionality to stream logs in real-time, similar to 'tail -f',
    with filtering and formatting capabilities.
    """
    
    def __init__(self, seaweed_client: SeaweedClient, bucket_name: str):
        """
        Initialize log streamer.
        
        Args:
            seaweed_client: SeaweedFS client instance
            bucket_name: Bucket containing logs
        """
        self.client = seaweed_client
        self.bucket_name = bucket_name
        self.seen_files: set = set()
        self.last_check_time = datetime.now()
    
    def get_validators(self) -> List[int]:
        """
        Get list of validator UIDs that have logs.
        
        Returns:
            List of validator UIDs
        """
        try:
            objects = self.client.list_objects(self.bucket_name)
            validators = set()
            
            for obj in objects:
                key_parts = obj['Key'].split('/')
                if key_parts[0].startswith('validator_'):
                    try:
                        uid = int(key_parts[0].replace('validator_', ''))
                        validators.add(uid)
                    except ValueError:
                        continue
            
            return sorted(list(validators))
            
        except Exception as e:
            print(f"Failed to get validators: {e}")
            return []
    
    def get_runs(self, validator_uid: int) -> List[str]:
        """
        Get list of runs for a validator.
        
        Args:
            validator_uid: Validator UID
            
        Returns:
            List of run IDs
        """
        try:
            prefix = f"validator_{validator_uid}/"
            # Use list_prefixes to get run directories directly
            run_prefixes = self.client.list_prefixes(self.bucket_name, prefix=prefix)
            
            runs = []
            for run_prefix in run_prefixes:
                # Extract run ID from prefix like "validator_200/2025-08-02_04-15-38/"
                parts = run_prefix.rstrip('/').split('/')
                if len(parts) >= 2:
                    run_id = parts[1]
                    if not run_id.startswith('.'):
                        runs.append(run_id)
            
            return sorted(runs, reverse=True)  # Most recent first
            
        except Exception as e:
            print(f"Failed to get runs for validator {validator_uid}: {e}")
            return []
    
    def stream_logs(
        self,
        validator_uid: int,
        run_id: Optional[str] = None,
        follow: bool = False,
        level_filter: Optional[str] = None,
        callback: Optional[Callable] = None
    ) -> None:
        """
        Stream logs for a validator.
        
        Args:
            validator_uid: Validator UID to stream logs for
            run_id: Specific run ID (None for latest)
            follow: Continue streaming new logs
            level_filter: Filter by log level
            callback: Function to call for each log entry
        """
        if run_id is None:
            run_id = self._get_latest_run(validator_uid)
            if not run_id:
                print(f"No runs found for validator {validator_uid}")
                return
        
        print(f"Streaming logs for validator {validator_uid}, run {run_id}")
        if follow:
            print("Following mode - Press Ctrl+C to stop")
        
        while True:
            try:
                new_logs = self._fetch_new_logs(validator_uid, run_id, level_filter)
                
                for log_entry in new_logs:
                    if callback:
                        callback(log_entry)
                    else:
                        self._print_log_entry(log_entry)
                
                if not follow:
                    break
                
                time.sleep(2)  # Check for new logs every 2 seconds
                
            except KeyboardInterrupt:
                print("\nStreaming stopped")
                break
            except Exception as e:
                print(f"Error streaming logs: {e}")
                if not follow:
                    break
                time.sleep(5)  # Wait before retrying
    
    def _get_latest_run(self, validator_uid: int) -> Optional[str]:
        """Get the latest run ID for a validator."""
        try:
            prefix = f"validator_{validator_uid}/"
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            
            runs = set()
            for obj in objects:
                # Extract run ID from object path
                parts = obj['Key'].split('/')
                if len(parts) >= 2:
                    runs.add(parts[1])
            
            if runs:
                return sorted(runs)[-1]  # Return latest run
            return None
            
        except Exception as e:
            print(f"Error getting latest run: {e}")
            return None
    
    def _fetch_new_logs(
        self,
        validator_uid: int,
        run_id: str,
        level_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fetch new log entries since last check."""
        try:
            prefix = f"validator_{validator_uid}/{run_id}/"
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            
            new_logs = []
            log_files = []
            
            # Find log files
            for obj in objects:
                if obj['Key'].startswith(prefix + "logs_") and obj['Key'].endswith(".json"):
                    log_files.append(obj['Key'])
            
            # Sort by timestamp in filename
            log_files.sort()
            
            # Process new files
            for log_file in log_files:
                if log_file not in self.seen_files:
                    self.seen_files.add(log_file)
                    file_logs = self._process_log_file(log_file, level_filter)
                    new_logs.extend(file_logs)
            
            return new_logs
            
        except Exception as e:
            print(f"Error fetching logs: {e}")
            return []
    
    def _process_log_file(
        self,
        log_file: str,
        level_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Process a single log file and return log entries."""
        try:
            log_data = self.client.get_object(self.bucket_name, log_file)
            log_json = json.loads(log_data.decode('utf-8'))
            
            logs = log_json.get('logs', [])
            
            # Filter by level if specified
            if level_filter:
                logs = [log for log in logs if log.get('level') == level_filter]
            
            return logs
            
        except Exception as e:
            print(f"Error processing log file {log_file}: {e}")
            return []
    
    def _print_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Print a log entry in a formatted way."""
        timestamp = log_entry.get('timestamp', '')
        level = log_entry.get('level', 'INFO')
        message = log_entry.get('message', '')
        
        # Format timestamp
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        except:
            formatted_time = timestamp
        
        # Color coding for levels (basic terminal colors)
        colors = {
            "ERROR": "\033[91m",    # Red
            "WARNING": "\033[93m",  # Yellow
            "INFO": "\033[92m",     # Green
            "DEBUG": "\033[94m",    # Blue
            "TRACE": "\033[95m",    # Magenta
            "SUCCESS": "\033[96m"   # Cyan
        }
        reset = "\033[0m"
        
        color = colors.get(level, "")
        
        print(f"{formatted_time} | {color}{level:>8}{reset} | {message}")
    
    def export_logs(
        self,
        validator_uid: int,
        run_id: Optional[str] = None,
        format_type: str = "json",
        output_file: Optional[str] = None,
        level_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Export logs to a file or return as string.
        
        Args:
            validator_uid: Validator UID
            run_id: Run ID (None for latest)
            format_type: Export format (json, csv, txt)
            output_file: Output file path (None to return string)
            level_filter: Filter by log level
            limit: Maximum number of logs to export
            
        Returns:
            Exported data as string if output_file is None
        """
        if run_id is None:
            run_id = self._get_latest_run(validator_uid)
            if not run_id:
                raise ValueError(f"No runs found for validator {validator_uid}")
        
        # Fetch all logs for the run
        all_logs = self._fetch_all_logs(validator_uid, run_id, level_filter, limit)
        
        # Format according to requested type
        if format_type == "json":
            content = self._format_json(all_logs, validator_uid, run_id)
        elif format_type == "csv":
            content = self._format_csv(all_logs)
        elif format_type == "txt":
            content = self._format_txt(all_logs)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Write to file or return string
        if output_file:
            with open(output_file, 'w') as f:
                f.write(content)
            return f"Exported {len(all_logs)} logs to {output_file}"
        else:
            return content
    
    def _fetch_all_logs(
        self,
        validator_uid: int,
        run_id: str,
        level_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch all logs for a run."""
        try:
            prefix = f"validator_{validator_uid}/{run_id}/"
            objects = self.client.list_objects(self.bucket_name, prefix=prefix)
            
            all_logs = []
            log_files = []
            
            # Find all log files
            for obj in objects:
                if obj['Key'].startswith(prefix + "logs_") and obj['Key'].endswith(".json"):
                    log_files.append(obj['Key'])
            
            # Sort by timestamp
            log_files.sort()
            
            # Process all files
            for log_file in log_files:
                file_logs = self._process_log_file(log_file, level_filter)
                all_logs.extend(file_logs)
            
            # Sort by timestamp
            all_logs.sort(key=lambda x: x.get('timestamp', ''))
            
            # Apply limit
            if limit:
                all_logs = all_logs[-limit:]
            
            return all_logs
            
        except Exception as e:
            print(f"Error fetching all logs: {e}")
            return []
    
    def _format_json(self, logs: List[Dict[str, Any]], validator_uid: int, run_id: str) -> str:
        """Format logs as JSON."""
        export_data = {
            "meta": {
                "validator_uid": validator_uid,
                "run_id": run_id,
                "exported_at": datetime.now().isoformat(),
                "total_logs": len(logs)
            },
            "logs": logs
        }
        return json.dumps(export_data, indent=2)
    
    def _format_csv(self, logs: List[Dict[str, Any]]) -> str:
        """Format logs as CSV."""
        lines = ["timestamp,level,message"]
        
        for log in logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', '')
            message = log.get('message', '').replace('"', '""')  # Escape quotes
            
            lines.append(f'"{timestamp}","{level}","{message}"')
        
        return '\n'.join(lines)
    
    def _format_txt(self, logs: List[Dict[str, Any]]) -> str:
        """Format logs as plain text."""
        lines = [
            "# Validator Logs Export",
            f"# Generated: {datetime.now().isoformat()}",
            f"# Total logs: {len(logs)}",
            ""
        ]
        
        for log in logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'INFO')
            message = log.get('message', '')
            
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                formatted_time = timestamp
            
            lines.append(f"{formatted_time} | {level:>8} | {message}")
        
        return '\n'.join(lines)
    
    def get_run_config(self, validator_uid: int, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration data for a specific validator run.
        
        Args:
            validator_uid: Validator UID
            run_id: Run ID
            
        Returns:
            Config data dictionary or None if not found
        """
        try:
            config_key = f"validator_{validator_uid}/{run_id}/config.json"
            
            # Check if config exists
            if not self.client.object_exists(self.bucket_name, config_key):
                return None
            
            # Get config data
            config_data = self.client.get_object(self.bucket_name, config_key)
            return json.loads(config_data.decode('utf-8'))
            
        except Exception as e:
            print(f"Failed to get run config for validator {validator_uid}, run {run_id}: {e}")
            return None