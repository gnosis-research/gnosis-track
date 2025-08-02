"""
Log formatting utilities for gnosis-track.

Provides various log formatting options for export and display.
"""

import json
import csv
import io
from datetime import datetime
from typing import Dict, Any, List, Optional, Union


class LogFormatter:
    """
    Log formatting utilities for different output formats.
    
    Supports JSON, CSV, plain text, and structured formats
    with customizable styling and filtering.
    """
    
    def __init__(self):
        """Initialize log formatter."""
        self.level_colors = {
            "ERROR": "\033[91m",    # Red
            "WARNING": "\033[93m",  # Yellow
            "INFO": "\033[92m",     # Green
            "DEBUG": "\033[94m",    # Blue
            "TRACE": "\033[95m",    # Magenta
            "SUCCESS": "\033[96m"   # Cyan
        }
        self.reset_color = "\033[0m"
    
    def format_logs(
        self,
        logs: List[Dict[str, Any]],
        format_type: str = "json",
        include_metadata: bool = True,
        color_output: bool = False,
        validator_uid: Optional[int] = None,
        run_id: Optional[str] = None
    ) -> str:
        """
        Format logs in the specified format.
        
        Args:
            logs: List of log entries
            format_type: Output format (json, csv, txt, structured)
            include_metadata: Include metadata in output
            color_output: Use ANSI color codes for terminal output
            validator_uid: Validator UID for metadata
            run_id: Run ID for metadata
            
        Returns:
            Formatted log string
        """
        if format_type == "json":
            return self.format_as_json(logs, include_metadata, validator_uid, run_id)
        elif format_type == "csv":
            return self.format_as_csv(logs, include_metadata)
        elif format_type == "txt":
            return self.format_as_text(logs, include_metadata, color_output, validator_uid, run_id)
        elif format_type == "structured":
            return self.format_as_structured(logs, color_output)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def format_as_json(
        self,
        logs: List[Dict[str, Any]],
        include_metadata: bool = True,
        validator_uid: Optional[int] = None,
        run_id: Optional[str] = None
    ) -> str:
        """Format logs as JSON."""
        if include_metadata:
            output = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "total_logs": len(logs),
                    "format": "json"
                },
                "logs": logs
            }
            
            if validator_uid is not None:
                output["metadata"]["validator_uid"] = validator_uid
            if run_id:
                output["metadata"]["run_id"] = run_id
                
            return json.dumps(output, indent=2, default=str)
        else:
            return json.dumps(logs, indent=2, default=str)
    
    def format_as_csv(
        self,
        logs: List[Dict[str, Any]],
        include_metadata: bool = True
    ) -> str:
        """Format logs as CSV."""
        output = io.StringIO()
        
        if include_metadata and logs:
            # Add metadata as comments
            output.write(f"# Exported at: {datetime.now().isoformat()}\n")
            output.write(f"# Total logs: {len(logs)}\n")
            output.write(f"# Format: CSV\n")
            output.write("\n")
        
        if not logs:
            return output.getvalue()
        
        # Determine all possible fields
        all_fields = set()
        for log in logs:
            all_fields.update(log.keys())
        
        # Common fields first, then others
        common_fields = ["timestamp", "level", "message", "run_id", "step"]
        field_order = []
        
        for field in common_fields:
            if field in all_fields:
                field_order.append(field)
                all_fields.remove(field)
        
        # Add remaining fields
        field_order.extend(sorted(all_fields))
        
        # Write CSV
        writer = csv.DictWriter(output, fieldnames=field_order, extrasaction='ignore')
        writer.writeheader()
        
        for log in logs:
            # Flatten nested objects for CSV
            flattened_log = self._flatten_dict(log)
            writer.writerow(flattened_log)
        
        return output.getvalue()
    
    def format_as_text(
        self,
        logs: List[Dict[str, Any]],
        include_metadata: bool = True,
        color_output: bool = False,
        validator_uid: Optional[int] = None,
        run_id: Optional[str] = None
    ) -> str:
        """Format logs as plain text."""
        lines = []
        
        if include_metadata:
            lines.append("# Validator Logs")
            lines.append(f"# Generated: {datetime.now().isoformat()}")
            lines.append(f"# Total logs: {len(logs)}")
            
            if validator_uid is not None:
                lines.append(f"# Validator UID: {validator_uid}")
            if run_id:
                lines.append(f"# Run ID: {run_id}")
            
            lines.append("")
        
        for log in logs:
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'INFO')
            message = log.get('message', '')
            
            # Format timestamp
            formatted_time = self._format_timestamp(timestamp)
            
            # Apply color if requested
            if color_output:
                color = self.level_colors.get(level, "")
                reset = self.reset_color
                level_colored = f"{color}{level:>8}{reset}"
            else:
                level_colored = f"{level:>8}"
            
            lines.append(f"{formatted_time} | {level_colored} | {message}")
        
        return '\n'.join(lines)
    
    def format_as_structured(
        self,
        logs: List[Dict[str, Any]],
        color_output: bool = False
    ) -> str:
        """Format logs as structured, human-readable text."""
        lines = []
        
        for i, log in enumerate(logs):
            if i > 0:
                lines.append("")  # Separator between log entries
            
            # Header line
            timestamp = log.get('timestamp', '')
            level = log.get('level', 'INFO')
            
            formatted_time = self._format_timestamp(timestamp)
            
            if color_output:
                color = self.level_colors.get(level, "")
                reset = self.reset_color
                header = f"[{formatted_time}] {color}{level}{reset}"
            else:
                header = f"[{formatted_time}] {level}"
            
            lines.append(header)
            
            # Main message
            message = log.get('message', '')
            if message:
                lines.append(f"  Message: {message}")
            
            # Additional fields
            skip_fields = {'timestamp', 'level', 'message'}
            for key, value in log.items():
                if key not in skip_fields:
                    if isinstance(value, (dict, list)):
                        lines.append(f"  {key.title()}: {json.dumps(value, default=str)}")
                    else:
                        lines.append(f"  {key.title()}: {value}")
        
        return '\n'.join(lines)
    
    def format_single_log(
        self,
        log: Dict[str, Any],
        format_type: str = "structured",
        color_output: bool = False
    ) -> str:
        """Format a single log entry."""
        return self.format_logs([log], format_type, False, color_output)
    
    def filter_logs(
        self,
        logs: List[Dict[str, Any]],
        level_filter: Optional[str] = None,
        message_filter: Optional[str] = None,
        time_filter: Optional[Dict[str, str]] = None,
        field_filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter logs based on various criteria.
        
        Args:
            logs: List of log entries
            level_filter: Filter by log level
            message_filter: Filter by message content (substring match)
            time_filter: Filter by time range (start_time, end_time)
            field_filters: Filter by arbitrary fields
            
        Returns:
            Filtered log entries
        """
        filtered_logs = logs.copy()
        
        # Level filter
        if level_filter:
            filtered_logs = [log for log in filtered_logs if log.get('level') == level_filter]
        
        # Message filter
        if message_filter:
            message_lower = message_filter.lower()
            filtered_logs = [
                log for log in filtered_logs
                if message_lower in log.get('message', '').lower()
            ]
        
        # Time filter
        if time_filter:
            start_time = time_filter.get('start_time')
            end_time = time_filter.get('end_time')
            
            if start_time or end_time:
                filtered_logs = [
                    log for log in filtered_logs
                    if self._time_in_range(log.get('timestamp'), start_time, end_time)
                ]
        
        # Field filters
        if field_filters:
            for field, value in field_filters.items():
                filtered_logs = [
                    log for log in filtered_logs
                    if log.get(field) == value
                ]
        
        return filtered_logs
    
    def summarize_logs(self, logs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a summary of log entries.
        
        Args:
            logs: List of log entries
            
        Returns:
            Summary statistics
        """
        if not logs:
            return {"total": 0, "levels": {}, "time_range": None}
        
        # Count by level
        level_counts = {}
        for log in logs:
            level = log.get('level', 'UNKNOWN')
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # Time range
        timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
        timestamps = [t for t in timestamps if t]  # Remove None/empty
        
        time_range = None
        if timestamps:
            timestamps.sort()
            time_range = {
                "start": timestamps[0],
                "end": timestamps[-1]
            }
        
        # Common messages
        message_counts = {}
        for log in logs:
            message = log.get('message', '')
            if message:
                # Count first 50 characters for grouping
                message_key = message[:50]
                message_counts[message_key] = message_counts.get(message_key, 0) + 1
        
        # Top messages
        top_messages = sorted(
            message_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "total": len(logs),
            "levels": level_counts,
            "time_range": time_range,
            "top_messages": top_messages
        }
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, str]:
        """Flatten nested dictionary for CSV output."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Convert list to string representation
                items.append((new_key, json.dumps(v, default=str)))
            else:
                items.append((new_key, str(v)))
        
        return dict(items)
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp string for display."""
        if not timestamp:
            return ""
        
        try:
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds
        except:
            # Return original if parsing fails
            return timestamp
    
    def _time_in_range(
        self,
        timestamp: Optional[str],
        start_time: Optional[str],
        end_time: Optional[str]
    ) -> bool:
        """Check if timestamp is within the specified range."""
        if not timestamp:
            return False
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if dt < start_dt:
                    return False
            
            if end_time:
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                if dt > end_dt:
                    return False
            
            return True
            
        except:
            return False