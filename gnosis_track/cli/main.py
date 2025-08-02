#!/usr/bin/env python3
"""
Main CLI entry point for gnosis-track.

Provides commands for installation, management, monitoring, and migration.
"""

import click
import sys
from pathlib import Path
from typing import Optional

from gnosis_track import __version__
from gnosis_track.core.config_manager import ConfigManager
from gnosis_track.cli.install import install_group
from gnosis_track.cli.manage import manage_group
from gnosis_track.cli.logs import logs_group


@click.group()
@click.version_option(version=__version__)
@click.option(
    '--config', '-c',
    type=click.Path(exists=True, path_type=Path),
    help='Configuration file path'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.pass_context
def cli(ctx, config: Optional[Path], verbose: bool):
    """
    Gnosis-Track - Secure distributed object storage and logging with SeaweedFS.
    
    A modern, high-performance replacement for MinIO-based logging systems.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Load configuration
    config_manager = ConfigManager(config_file=config)
    ctx.obj['config'] = config_manager.get_config()
    ctx.obj['config_manager'] = config_manager
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo(f"Gnosis-Track v{__version__}")
        if config:
            click.echo(f"Using config: {config}")


@cli.command()
@click.pass_context
def health(ctx):
    """Check system health and connectivity."""
    from gnosis_track.core.seaweed_client import SeaweedClient
    
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    try:
        # Test SeaweedFS connection
        seaweed_config = config.seaweedfs
        endpoint_url = f"{'https' if seaweed_config.use_ssl else 'http'}://{seaweed_config.s3_endpoint}"
        
        client = SeaweedClient(
            endpoint_url=endpoint_url,
            access_key=seaweed_config.access_key,
            secret_key=seaweed_config.secret_key,
            use_ssl=seaweed_config.use_ssl,
            verify_ssl=seaweed_config.verify_ssl,
        )
        
        health_result = client.health_check()
        
        if health_result['status'] == 'healthy':
            click.echo(click.style("✅ SeaweedFS: Healthy", fg='green'))
            if verbose:
                click.echo(f"   Endpoint: {health_result['endpoint']}")
                click.echo(f"   Response time: {health_result['response_time_ms']}ms")
                click.echo(f"   Buckets: {health_result.get('buckets_count', 0)}")
        else:
            click.echo(click.style("❌ SeaweedFS: Unhealthy", fg='red'))
            if verbose and 'error' in health_result:
                click.echo(f"   Error: {health_result['error']}")
        
        # Test bucket access if logging is configured
        if config.logging.bucket_name:
            try:
                from gnosis_track.core.bucket_manager import BucketManager
                bucket_manager = BucketManager(client)
                bucket_health = bucket_manager.get_bucket_health(config.logging.bucket_name)
                
                if bucket_health['status'] == 'healthy':
                    click.echo(click.style(f"✅ Bucket '{config.logging.bucket_name}': Healthy", fg='green'))
                elif bucket_health['status'] == 'not_found':
                    click.echo(click.style(f"⚠️  Bucket '{config.logging.bucket_name}': Not found", fg='yellow'))
                else:
                    click.echo(click.style(f"❌ Bucket '{config.logging.bucket_name}': {bucket_health['status']}", fg='red'))
                
                if verbose:
                    click.echo(f"   Objects: {bucket_health.get('object_count', 0)}")
                    click.echo(f"   Size: {bucket_health.get('total_size_bytes', 0)} bytes")
                    
            except Exception as e:
                click.echo(click.style(f"❌ Bucket check failed: {e}", fg='red'))
        
    except Exception as e:
        click.echo(click.style(f"❌ Health check failed: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.pass_context
def config(ctx):
    """Show current configuration."""
    config_manager = ctx.obj['config_manager']
    config = ctx.obj['config']
    
    click.echo("📋 Current Configuration:")
    click.echo()
    
    # SeaweedFS configuration
    click.echo(click.style("SeaweedFS:", fg='blue', bold=True))
    click.echo(f"  Endpoint: {config.seaweedfs.s3_endpoint}")
    click.echo(f"  SSL: {config.seaweedfs.use_ssl}")
    click.echo(f"  Auto-start local: {config.seaweedfs.auto_start_local}")
    click.echo()
    
    # Security configuration
    click.echo(click.style("Security:", fg='blue', bold=True))
    click.echo(f"  Encryption: {config.security.encryption_enabled}")
    click.echo(f"  Algorithm: {config.security.encryption_algorithm}")
    click.echo(f"  TLS: {config.security.tls_enabled}")
    click.echo()
    
    # Logging configuration
    click.echo(click.style("Logging:", fg='blue', bold=True))
    click.echo(f"  Bucket: {config.logging.bucket_name}")
    click.echo(f"  Project: {config.logging.project_name}")
    click.echo(f"  Retention: {config.logging.retention_days} days")
    click.echo(f"  Compression: {config.logging.compression_enabled}")
    click.echo()
    
    # UI configuration
    click.echo(click.style("UI:", fg='blue', bold=True))
    click.echo(f"  Host: {config.ui.host}")
    click.echo(f"  Port: {config.ui.port}")
    click.echo(f"  Auth required: {config.ui.auth_required}")
    click.echo()


@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['yaml', 'json']), default='yaml', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file (default: stdout)')
@click.pass_context
def config_export(ctx, output_format: str, output: Optional[str]):
    """Export current configuration to file."""
    config_manager = ctx.obj['config_manager']
    
    if output:
        config_manager.save_config(output, output_format)
        click.echo(f"✅ Configuration exported to {output}")
    else:
        # Print to stdout
        if output_format == 'yaml':
            import yaml
            click.echo(yaml.dump(config_manager.get_config().dict(), default_flow_style=False, indent=2))
        else:
            import json
            click.echo(json.dumps(config_manager.get_config().dict(), indent=2))


@cli.command()
@click.pass_context
def env_example(ctx):
    """Generate example .env file."""
    config_manager = ctx.obj['config_manager']
    click.echo(config_manager.get_env_example())


@cli.command()
@click.option('--host', default=None, help='UI server host')
@click.option('--port', default=None, type=int, help='UI server port')
@click.option('--auth-required', is_flag=True, help='Require authentication')
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.pass_context
def ui(ctx, host: Optional[str], port: Optional[int], auth_required: bool, debug: bool):
    """Start the web UI server."""
    try:
        from gnosis_track.ui.server import main as ui_main
        
        # Override config with CLI options
        config = ctx.obj['config']
        if host:
            config.ui.host = host
        if port:
            config.ui.port = port
        if auth_required:
            config.ui.auth_required = True
        if debug:
            config.ui.debug = True
        
        click.echo(f"🚀 Starting Gnosis-Track UI server...")
        click.echo(f"📍 Server: http://{config.ui.host}:{config.ui.port}")
        click.echo(f"🔧 Debug: {config.ui.debug}")
        click.echo(f"🔐 Auth: {config.ui.auth_required}")
        click.echo()
        
        ui_main(config)
        
    except ImportError:
        click.echo(click.style("❌ UI dependencies not installed. Install with: pip install 'gnosis-track[ui]'", fg='red'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"❌ Failed to start UI server: {e}", fg='red'))
        sys.exit(1)


@cli.command()
@click.pass_context
def metrics(ctx):
    """Show system metrics."""
    from gnosis_track.core.seaweed_client import SeaweedClient
    from gnosis_track.core.bucket_manager import BucketManager
    
    config = ctx.obj['config']
    
    try:
        # Create client
        seaweed_config = config.seaweedfs
        endpoint_url = f"{'https' if seaweed_config.use_ssl else 'http'}://{seaweed_config.s3_endpoint}"
        
        client = SeaweedClient(
            endpoint_url=endpoint_url,
            access_key=seaweed_config.access_key,
            secret_key=seaweed_config.secret_key,
            use_ssl=seaweed_config.use_ssl,
        )
        
        bucket_manager = BucketManager(client)
        
        # Get cluster metrics
        health = client.health_check()
        buckets = bucket_manager.list_buckets(include_stats=True)
        
        click.echo("📊 System Metrics:")
        click.echo()
        
        # Cluster health
        click.echo(click.style("Cluster Health:", fg='blue', bold=True))
        status_color = 'green' if health['status'] == 'healthy' else 'red'
        click.echo(f"  Status: {click.style(health['status'], fg=status_color)}")
        click.echo(f"  Response time: {health['response_time_ms']}ms")
        click.echo()
        
        # Bucket statistics
        click.echo(click.style("Bucket Statistics:", fg='blue', bold=True))
        total_objects = 0
        total_size = 0
        
        for bucket in buckets:
            object_count = bucket.get('object_count', 0)
            size_mb = bucket.get('total_size_mb', 0)
            total_objects += object_count
            total_size += size_mb
            
            click.echo(f"  {bucket['name']}: {object_count} objects, {size_mb:.1f} MB")
        
        click.echo()
        click.echo(f"  Total: {total_objects} objects, {total_size:.1f} MB")
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to get metrics: {e}", fg='red'))
        sys.exit(1)


# Add command groups
cli.add_command(install_group, name='install')
cli.add_command(manage_group, name='bucket')
cli.add_command(logs_group, name='logs')


def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n⏹️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red'))
        sys.exit(1)


if __name__ == '__main__':
    main()