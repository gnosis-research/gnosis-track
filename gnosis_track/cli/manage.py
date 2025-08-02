"""
Bucket and storage management commands for gnosis-track.
"""

import click
import sys
from typing import Optional


@click.group()
def manage_group():
    """Bucket and storage management commands."""
    pass


@manage_group.command()
@click.argument('bucket_name')
@click.option('--encryption/--no-encryption', default=True, help='Enable encryption')
@click.option('--replication', default='001', help='Replication setting (e.g., 001, 110)')
@click.option('--lifecycle-days', type=int, help='Days after which objects are archived')
@click.option('--description', help='Bucket description')
@click.pass_context
def create(ctx, bucket_name: str, encryption: bool, replication: str, lifecycle_days: Optional[int], description: Optional[str]):
    """Create a new bucket."""
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
        
        bucket_manager = BucketManager(client, default_encryption=encryption)
        
        # Create bucket
        tags = {"created_by": "gnosis-track-cli"}
        if description:
            tags["description"] = description
        
        bucket_manager.ensure_bucket(
            bucket_name=bucket_name,
            replication=replication,
            encryption=encryption,
            lifecycle_days=lifecycle_days,
            tags=tags,
            description=description
        )
        
        click.echo(f"✅ Created bucket: {bucket_name}")
        if encryption:
            click.echo(f"   🔒 Encryption: AES256-GCM")
        click.echo(f"   📋 Replication: {replication}")
        if lifecycle_days:
            click.echo(f"   📅 Lifecycle: {lifecycle_days} days")
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to create bucket: {e}", fg='red'))
        sys.exit(1)


@manage_group.command()
@click.option('--include-stats', is_flag=True, help='Include object statistics')
@click.pass_context
def list(ctx, include_stats: bool):
    """List all buckets."""
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
        buckets = bucket_manager.list_buckets(include_stats=include_stats)
        
        if not buckets:
            click.echo("No buckets found")
            return
        
        click.echo("📦 Buckets:")
        for bucket in buckets:
            name = bucket['name']
            created = bucket['creation_date'].strftime('%Y-%m-%d %H:%M:%S')
            
            click.echo(f"  {name}")
            click.echo(f"    Created: {created}")
            
            if include_stats:
                objects = bucket.get('object_count', 0)
                size_mb = bucket.get('total_size_mb', 0)
                click.echo(f"    Objects: {objects:,}")
                click.echo(f"    Size: {size_mb:.1f} MB")
            
            # Show configuration if available
            if 'encryption' in bucket:
                encryption_icon = "🔒" if bucket['encryption'] else "🔓"
                click.echo(f"    {encryption_icon} Encryption: {bucket['encryption']}")
            
            if 'replication' in bucket:
                click.echo(f"    📋 Replication: {bucket['replication']}")
            
            click.echo()
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to list buckets: {e}", fg='red'))
        sys.exit(1)


@manage_group.command()
@click.argument('bucket_name')
@click.pass_context
def stats(ctx, bucket_name: str):
    """Show detailed statistics for a bucket."""
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
        
        # Get bucket health and stats
        health = bucket_manager.get_bucket_health(bucket_name)
        config_info = bucket_manager.get_bucket_config(bucket_name)
        
        click.echo(f"📊 Bucket Statistics: {bucket_name}")
        click.echo()
        
        # Health status
        status_color = 'green' if health['status'] == 'healthy' else 'red'
        click.echo(f"Status: {click.style(health['status'], fg=status_color)}")
        
        if 'object_count' in health:
            click.echo(f"Objects: {health['object_count']:,}")
        if 'total_size_bytes' in health:
            size_mb = health['total_size_bytes'] / (1024 * 1024)
            click.echo(f"Size: {size_mb:.1f} MB ({health['total_size_bytes']:,} bytes)")
        
        if 'response_time_ms' in health:
            click.echo(f"Response time: {health['response_time_ms']}ms")
        
        # Configuration
        if config_info:
            click.echo("\n🔧 Configuration:")
            if 'encryption' in config_info:
                encryption_icon = "🔒" if config_info['encryption'] else "🔓"
                click.echo(f"  {encryption_icon} Encryption: {config_info['encryption']}")
            if 'replication' in config_info:
                click.echo(f"  📋 Replication: {config_info['replication']}")
            if 'created_at' in config_info:
                click.echo(f"  📅 Created: {config_info['created_at']}")
            if 'description' in config_info:
                click.echo(f"  📝 Description: {config_info['description']}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to get bucket stats: {e}", fg='red'))
        sys.exit(1)


@manage_group.command()
@click.argument('bucket_name')
@click.option('--force', is_flag=True, help='Force deletion without confirmation')
@click.option('--backup/--no-backup', default=True, help='Backup objects before deletion')
@click.pass_context
def delete(ctx, bucket_name: str, force: bool, backup: bool):
    """Delete a bucket and optionally backup its contents."""
    from gnosis_track.core.seaweed_client import SeaweedClient
    from gnosis_track.core.bucket_manager import BucketManager
    
    config = ctx.obj['config']
    
    if not force:
        click.echo(f"⚠️  This will delete bucket '{bucket_name}' and all its contents.")
        if not click.confirm("Are you sure?"):
            return
    
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
        
        # Delete bucket
        bucket_manager.delete_bucket(
            bucket_name=bucket_name,
            force=True,
            backup_objects=backup
        )
        
        click.echo(f"✅ Deleted bucket: {bucket_name}")
        if backup:
            click.echo("📦 Objects backed up before deletion")
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to delete bucket: {e}", fg='red'))
        sys.exit(1)


@manage_group.command()
@click.argument('bucket_name')
@click.option('--days', required=True, type=int, help='Delete objects older than N days')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.option('--prefix', default='', help='Only consider objects with this prefix')
@click.pass_context
def cleanup(ctx, bucket_name: str, days: int, dry_run: bool, prefix: str):
    """Clean up old objects in a bucket."""
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
        
        # Cleanup old objects
        result = bucket_manager.cleanup_old_objects(
            bucket_name=bucket_name,
            days=days,
            dry_run=dry_run,
            prefix=prefix
        )
        
        action = "Would delete" if dry_run else "Deleted"
        click.echo(f"🧹 {action} {result['objects_found']} objects older than {days} days")
        
        if result['total_size_bytes'] > 0:
            size_mb = result['total_size_bytes'] / (1024 * 1024)
            click.echo(f"   Total size: {size_mb:.1f} MB")
        
        if dry_run and result['objects_found'] > 0:
            click.echo("   Run without --dry-run to actually delete these objects")
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to cleanup bucket: {e}", fg='red'))
        sys.exit(1)