"""
Log viewing and management commands for gnosis-track.
"""

import click
import json
import sys
from typing import Optional


@click.group()
def logs_group():
    """Log viewing and management commands."""
    pass


@logs_group.command()
@click.option('--validator-uid', required=True, type=int, help='Validator UID to stream logs for')
@click.option('--run-id', help='Specific run ID (default: latest)')
@click.option('--follow', '-f', is_flag=True, help='Follow logs like tail -f')
@click.option('--level', type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'SUCCESS']), 
              help='Filter by log level')
@click.option('--limit', default=100, help='Number of recent logs to show')
@click.pass_context
def stream(ctx, validator_uid: int, run_id: Optional[str], follow: bool, level: Optional[str], limit: int):
    """Stream logs for a validator."""
    
    # For now, show a placeholder - this would integrate with the actual log streaming
    click.echo(f"🔄 Streaming logs for validator {validator_uid}")
    if run_id:
        click.echo(f"   Run ID: {run_id}")
    else:
        click.echo(f"   Run ID: latest")
    
    if level:
        click.echo(f"   Level filter: {level}")
    
    if follow:
        click.echo("   Following mode: Press Ctrl+C to stop")
    
    click.echo("=" * 60)
    
    # This would integrate with the actual SeaweedFS log streaming
    # For now, show example output
    example_logs = [
        {"timestamp": "2025-01-26T10:30:15.123Z", "level": "INFO", "message": "Validator started successfully"},
        {"timestamp": "2025-01-26T10:30:16.456Z", "level": "INFO", "message": "Connected to network, netuid=1"},
        {"timestamp": "2025-01-26T10:30:17.789Z", "level": "DEBUG", "message": "Processing batch 1 with 32 samples"},
        {"timestamp": "2025-01-26T10:30:18.012Z", "level": "WARNING", "message": "High memory usage detected: 85%"},
        {"timestamp": "2025-01-26T10:30:19.345Z", "level": "INFO", "message": "Batch completed, accuracy: 0.94"},
    ]
    
    for log in example_logs:
        level_colors = {
            'ERROR': 'red',
            'WARNING': 'yellow', 
            'INFO': 'green',
            'DEBUG': 'blue',
            'TRACE': 'magenta',
            'SUCCESS': 'cyan'
        }
        
        if level and log['level'] != level:
            continue
            
        color = level_colors.get(log['level'], 'white')
        timestamp = log['timestamp'][:19].replace('T', ' ')
        
        level_formatted = f"{log['level']:>8}"
        click.echo(f"{timestamp} | {click.style(level_formatted, fg=color)} | {log['message']}")
    
    if follow:
        click.echo("\n⏹️  Log streaming stopped")


@logs_group.command()
@click.option('--validator-uid', type=int, help='Validator UID')
@click.option('--run-id', help='Specific run ID')
@click.option('--format', 'output_format', type=click.Choice(['json', 'csv', 'txt']), 
              default='json', help='Export format')
@click.option('--output', '-o', type=click.Path(), help='Output file (default: stdout)')
@click.option('--level', type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'SUCCESS']),
              help='Filter by log level')
@click.option('--since', help='Export logs since timestamp (ISO format)')
@click.option('--limit', default=1000, help='Maximum number of logs to export')
@click.pass_context
def export(ctx, validator_uid: Optional[int], run_id: Optional[str], output_format: str, 
           output: Optional[str], level: Optional[str], since: Optional[str], limit: int):
    """Export logs to file."""
    
    if not validator_uid:
        click.echo(click.style("❌ Validator UID is required for export", fg='red'))
        sys.exit(1)
    
    click.echo(f"📤 Exporting logs for validator {validator_uid}")
    click.echo(f"   Format: {output_format.upper()}")
    click.echo(f"   Limit: {limit} logs")
    
    if level:
        click.echo(f"   Level filter: {level}")
    if since:
        click.echo(f"   Since: {since}")
    
    # Example export data
    export_data = {
        "meta": {
            "validator_uid": validator_uid,
            "run_id": run_id or "latest",
            "exported_at": "2025-01-26T10:30:20.000Z",
            "total_logs": 150,
            "format": output_format
        },
        "logs": [
            {
                "timestamp": "2025-01-26T10:30:15.123Z",
                "level": "INFO", 
                "message": "Validator started successfully"
            },
            {
                "timestamp": "2025-01-26T10:30:16.456Z",
                "level": "INFO",
                "message": "Connected to network, netuid=1"
            }
        ]
    }
    
    # Generate output
    if output_format == 'json':
        content = json.dumps(export_data, indent=2)
    elif output_format == 'csv':
        content = "timestamp,level,message\n"
        for log in export_data['logs']:
            content += f"{log['timestamp']},{log['level']},\"{log['message']}\"\n"
    else:  # txt
        content = f"# Validator {validator_uid} Logs Export\n"
        content += f"# Generated: {export_data['meta']['exported_at']}\n\n"
        for log in export_data['logs']:
            content += f"{log['timestamp']} | {log['level']:>8} | {log['message']}\n"
    
    # Output to file or stdout
    if output:
        with open(output, 'w') as f:
            f.write(content)
        click.echo(f"✅ Exported to {output}")
    else:
        click.echo(content)


@logs_group.command()
@click.option('--validator-uid', type=int, help='Validator UID')
@click.pass_context  
def runs(ctx, validator_uid: Optional[int]):
    """List available log runs."""
    
    if validator_uid:
        click.echo(f"📋 Log runs for validator {validator_uid}:")
    else:
        click.echo("📋 All log runs:")
    
    click.echo()
    
    # Example runs data
    example_runs = [
        {
            "validator_uid": 0,
            "run_id": "2025-01-26_10-30-15", 
            "start_time": "2025-01-26T10:30:15Z",
            "duration": "2h 15m",
            "status": "active",
            "logs_count": 1543
        },
        {
            "validator_uid": 0,
            "run_id": "2025-01-25_08-15-22",
            "start_time": "2025-01-25T08:15:22Z", 
            "duration": "8h 45m",
            "status": "completed",
            "logs_count": 5672
        },
        {
            "validator_uid": 1,
            "run_id": "2025-01-26_09-45-33",
            "start_time": "2025-01-26T09:45:33Z",
            "duration": "3h 2m", 
            "status": "active",
            "logs_count": 2134
        }
    ]
    
    for run in example_runs:
        if validator_uid and run['validator_uid'] != validator_uid:
            continue
            
        status_color = 'green' if run['status'] == 'active' else 'blue'
        status_icon = "🔄" if run['status'] == 'active' else "✅"
        
        click.echo(f"  {status_icon} Validator {run['validator_uid']} - {run['run_id']}")
        click.echo(f"     Started: {run['start_time']}")
        click.echo(f"     Duration: {run['duration']}")
        click.echo(f"     Status: {click.style(run['status'], fg=status_color)}")
        click.echo(f"     Logs: {run['logs_count']:,}")
        click.echo()


@logs_group.command()
@click.option('--validator-uid', required=True, type=int, help='Validator UID')
@click.option('--run-id', help='Specific run ID (default: latest)')
@click.pass_context
def summary(ctx, validator_uid: int, run_id: Optional[str]):
    """Show summary for a logging run."""
    
    click.echo(f"📊 Run Summary - Validator {validator_uid}")
    if run_id:
        click.echo(f"Run ID: {run_id}")
    else:
        click.echo("Run ID: latest")
    
    click.echo()
    
    # Example summary data
    summary = {
        "run_id": run_id or "2025-01-26_10-30-15",
        "validator_uid": validator_uid,
        "start_time": "2025-01-26T10:30:15Z",
        "end_time": "2025-01-26T12:45:30Z",
        "duration_minutes": 135,
        "total_logs": 1543,
        "log_levels": {
            "ERROR": 5,
            "WARNING": 23,
            "INFO": 1245,
            "DEBUG": 234,
            "SUCCESS": 36
        },
        "metrics_logged": 78,
        "storage_size_mb": 15.7
    }
    
    click.echo(f"Start time: {summary['start_time']}")
    click.echo(f"End time: {summary['end_time']}")
    click.echo(f"Duration: {summary['duration_minutes']} minutes")
    click.echo(f"Storage size: {summary['storage_size_mb']} MB")
    click.echo()
    
    click.echo("📈 Log Statistics:")
    click.echo(f"  Total logs: {summary['total_logs']:,}")
    click.echo(f"  Metrics logged: {summary['metrics_logged']}")
    click.echo()
    
    click.echo("📊 Log Levels:")
    for level, count in summary['log_levels'].items():
        percentage = (count / summary['total_logs']) * 100
        click.echo(f"  {level:>8}: {count:,} ({percentage:.1f}%)")


@logs_group.command()
@click.argument('search_term')
@click.option('--validator-uid', type=int, help='Validator UID to search in')
@click.option('--run-id', help='Specific run ID')
@click.option('--level', type=click.Choice(['ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'SUCCESS']),
              help='Filter by log level')
@click.option('--limit', default=50, help='Maximum results to show')
@click.pass_context
def search(ctx, search_term: str, validator_uid: Optional[int], run_id: Optional[str], 
           level: Optional[str], limit: int):
    """Search logs for specific terms."""
    
    click.echo(f"🔍 Searching for: '{search_term}'")
    if validator_uid:
        click.echo(f"   Validator: {validator_uid}")
    if run_id:
        click.echo(f"   Run: {run_id}")
    if level:
        click.echo(f"   Level: {level}")
    
    click.echo(f"   Limit: {limit} results")
    click.echo("=" * 60)
    
    # Example search results
    results = [
        {
            "timestamp": "2025-01-26T10:32:15.123Z",
            "level": "ERROR",
            "message": f"Connection failed: {search_term} not found",
            "validator_uid": 0,
            "run_id": "2025-01-26_10-30-15"
        },
        {
            "timestamp": "2025-01-26T10:35:22.456Z", 
            "level": "INFO",
            "message": f"Processing {search_term} completed successfully",
            "validator_uid": 0,
            "run_id": "2025-01-26_10-30-15"
        }
    ]
    
    if not results:
        click.echo("No results found")
        return
    
    for i, result in enumerate(results[:limit], 1):
        if level and result['level'] != level:
            continue
        if validator_uid and result['validator_uid'] != validator_uid:
            continue
            
        level_colors = {
            'ERROR': 'red',
            'WARNING': 'yellow',
            'INFO': 'green', 
            'DEBUG': 'blue',
            'TRACE': 'magenta',
            'SUCCESS': 'cyan'
        }
        
        color = level_colors.get(result['level'], 'white')
        timestamp = result['timestamp'][:19].replace('T', ' ')
        
        # Highlight search term in message
        message = result['message'].replace(search_term, click.style(search_term, bg='yellow', fg='black'))
        
        level_formatted = f"{result['level']:>8}"
        click.echo(f"{i:>3}. {timestamp} | {click.style(level_formatted, fg=color)} | {message}")
        click.echo(f"     Validator {result['validator_uid']}, Run: {result['run_id']}")
        click.echo()
    
    click.echo(f"Found {len(results)} results (showing {min(len(results), limit)})")