"""
Installation and setup commands for gnosis-track.

Handles SeaweedFS installation, cluster setup, and initial configuration.
"""

import click
import os
import platform
import subprocess
import time
import urllib.request
import tarfile
import tempfile
import json
from pathlib import Path
from typing import Optional


@click.group()
def install_group():
    """Installation and setup commands."""
    pass


@install_group.command()
@click.option('--cluster-size', default=1, help='Number of nodes in cluster (1 for standalone)')
@click.option('--data-dir', default=None, help='Data directory (default: ~/seaweedfs)')
@click.option('--master-port', default=9333, help='Master server port')
@click.option('--volume-port', default=8080, help='Volume server port')
@click.option('--filer-port', default=8888, help='Filer server port')
@click.option('--s3-port', default=8333, help='S3 gateway port')
@click.option('--access-key', default='admin', help='S3 access key')
@click.option('--secret-key', default='admin_secret_key', help='S3 secret key')
@click.option('--force', is_flag=True, help='Force reinstallation')
def seaweedfs(
    cluster_size: int,
    data_dir: Optional[str],
    master_port: int,
    volume_port: int,
    filer_port: int,
    s3_port: int,
    access_key: str,
    secret_key: str,
    force: bool
):
    """Install and setup SeaweedFS cluster."""
    
    # Determine installation directory
    if data_dir:
        install_dir = Path(data_dir)
    else:
        install_dir = Path.home() / "seaweedfs"
    
    install_dir.mkdir(parents=True, exist_ok=True)
    
    binary_path = install_dir / "weed"
    
    # Check if already installed
    if binary_path.exists() and not force:
        click.echo(f"✅ SeaweedFS already installed at {install_dir}")
        if not click.confirm("Do you want to reconfigure?"):
            return
    else:
        click.echo(f"📥 Installing SeaweedFS to {install_dir}")
        
        # Download SeaweedFS binary
        try:
            _download_seaweedfs_binary(binary_path)
            click.echo("✅ SeaweedFS binary downloaded")
        except Exception as e:
            click.echo(click.style(f"❌ Failed to download SeaweedFS: {e}", fg='red'))
            return
    
    # Setup cluster
    if cluster_size == 1:
        _setup_standalone(install_dir, master_port, volume_port, filer_port, s3_port, access_key, secret_key)
    else:
        _setup_cluster(install_dir, cluster_size, master_port, volume_port, filer_port, s3_port, access_key, secret_key)
    
    click.echo(f"🚀 SeaweedFS installation completed!")
    click.echo(f"📁 Installation directory: {install_dir}")
    click.echo(f"🌐 S3 endpoint: http://localhost:{s3_port}")
    click.echo(f"🔑 Access key: {access_key}")
    click.echo()
    click.echo("Start the cluster with:")
    click.echo(f"  gnosis-track start")


@install_group.command()
@click.option('--data-dir', default=None, help='Data directory to remove')
@click.option('--force', is_flag=True, help='Force removal without confirmation')
def uninstall(data_dir: Optional[str], force: bool):
    """Uninstall SeaweedFS and remove data."""
    
    if data_dir:
        install_dir = Path(data_dir)
    else:
        install_dir = Path.home() / "seaweedfs"
    
    if not install_dir.exists():
        click.echo("⚠️  SeaweedFS installation not found")
        return
    
    if not force:
        click.echo(f"This will remove SeaweedFS installation and all data in: {install_dir}")
        if not click.confirm("Are you sure?"):
            return
    
    # Stop any running processes
    _stop_seaweedfs_processes()
    
    # Remove installation directory
    import shutil
    try:
        shutil.rmtree(install_dir)
        click.echo("✅ SeaweedFS uninstalled successfully")
    except Exception as e:
        click.echo(click.style(f"❌ Failed to remove {install_dir}: {e}", fg='red'))


@install_group.command()
@click.option('--data-dir', default=None, help='Data directory')
def start(data_dir: Optional[str]):
    """Start SeaweedFS cluster."""
    
    if data_dir:
        install_dir = Path(data_dir)
    else:
        install_dir = Path.home() / "seaweedfs"
    
    config_file = install_dir / "cluster_config.json"
    
    if not config_file.exists():
        click.echo(click.style("❌ SeaweedFS not installed. Run 'gnosis-track install seaweedfs' first.", fg='red'))
        return
    
    # Load configuration
    with open(config_file) as f:
        config = json.load(f)
    
    click.echo("🚀 Starting SeaweedFS cluster...")
    
    try:
        _start_seaweedfs_cluster(install_dir, config)
        click.echo("✅ SeaweedFS cluster started successfully")
        click.echo(f"🌐 S3 endpoint: http://localhost:{config['s3_port']}")
        click.echo(f"🎛️  Master UI: http://localhost:{config['master_port']}")
        click.echo(f"📁 Filer UI: http://localhost:{config['filer_port']}")
        
    except Exception as e:
        click.echo(click.style(f"❌ Failed to start cluster: {e}", fg='red'))


@install_group.command()
def stop():
    """Stop SeaweedFS cluster."""
    click.echo("⏹️  Stopping SeaweedFS cluster...")
    
    try:
        _stop_seaweedfs_processes()
        click.echo("✅ SeaweedFS cluster stopped")
    except Exception as e:
        click.echo(click.style(f"❌ Failed to stop cluster: {e}", fg='red'))


@install_group.command()
@click.option('--data-dir', default=None, help='Data directory')
def status(data_dir: Optional[str]):
    """Show SeaweedFS cluster status."""
    
    if data_dir:
        install_dir = Path(data_dir)
    else:
        install_dir = Path.home() / "seaweedfs"
    
    config_file = install_dir / "cluster_config.json"
    
    if not config_file.exists():
        click.echo(click.style("❌ SeaweedFS not installed", fg='red'))
        return
    
    # Load configuration
    with open(config_file) as f:
        config = json.load(f)
    
    click.echo("📊 SeaweedFS Cluster Status:")
    click.echo()
    
    # Check process status
    processes = _check_seaweedfs_processes()
    
    services = ['master', 'volume', 'filer', 's3']
    for service in services:
        if service in processes:
            click.echo(f"  {service.capitalize()}: {click.style('Running', fg='green')} (PID: {processes[service]})")
        else:
            click.echo(f"  {service.capitalize()}: {click.style('Stopped', fg='red')}")
    
    click.echo()
    
    # Show endpoints
    click.echo("🌐 Endpoints:")
    click.echo(f"  Master: http://localhost:{config['master_port']}")
    click.echo(f"  Volume: http://localhost:{config['volume_port']}")
    click.echo(f"  Filer: http://localhost:{config['filer_port']}")
    click.echo(f"  S3: http://localhost:{config['s3_port']}")


def _download_seaweedfs_binary(binary_path: Path) -> None:
    """Download SeaweedFS binary for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Determine the correct binary
    if system == "darwin":
        if "arm" in machine or "aarch64" in machine:
            filename = "darwin_arm64.tar.gz"
        else:
            filename = "darwin_amd64.tar.gz"
    elif system == "linux":
        if "arm" in machine or "aarch64" in machine:
            filename = "linux_arm64.tar.gz"
        else:
            filename = "linux_amd64.tar.gz"
    elif system == "windows":
        if "arm" in machine or "aarch64" in machine:
            filename = "windows_arm64.tar.gz"
        else:
            filename = "windows_amd64.tar.gz"
    else:
        raise ValueError(f"Unsupported platform: {system}-{machine}")
    
    # Download URL
    base_url = "https://github.com/seaweedfs/seaweedfs/releases/latest/download"
    url = f"{base_url}/{filename}"
    
    click.echo(f"Downloading from {url}")
    
    # Download and extract
    with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tmp_file:
        urllib.request.urlretrieve(url, tmp_file.name)
        
        with tarfile.open(tmp_file.name, 'r:gz') as tar:
            tar.extract('weed', path=binary_path.parent)
            extracted_path = binary_path.parent / 'weed'
            
            # On Windows, the binary might have .exe extension
            if system == "windows" and not extracted_path.exists():
                extracted_path = binary_path.parent / 'weed.exe'
                binary_path = binary_path.with_suffix('.exe')
            
            if extracted_path != binary_path:
                extracted_path.rename(binary_path)
    
    # Make executable on Unix systems
    if system != "windows":
        binary_path.chmod(0o755)


def _setup_standalone(
    install_dir: Path,
    master_port: int,
    volume_port: int,
    filer_port: int,
    s3_port: int,
    access_key: str,
    secret_key: str
) -> None:
    """Setup standalone SeaweedFS instance."""
    
    # Create directories
    (install_dir / "master").mkdir(exist_ok=True)
    (install_dir / "volume").mkdir(exist_ok=True)
    (install_dir / "filer").mkdir(exist_ok=True)
    
    # Create S3 configuration
    s3_config = {
        "identities": [
            {
                "name": access_key,
                "credentials": [
                    {
                        "accessKey": access_key,
                        "secretKey": secret_key
                    }
                ],
                "actions": ["Admin", "Read", "Write"]
            }
        ]
    }
    
    with open(install_dir / "s3_config.json", 'w') as f:
        json.dump(s3_config, f, indent=2)
    
    # Create cluster configuration
    cluster_config = {
        "cluster_size": 1,
        "master_port": master_port,
        "volume_port": volume_port,
        "filer_port": filer_port,
        "s3_port": s3_port,
        "access_key": access_key,
        "secret_key": secret_key,
        "replication": "000"  # No replication for standalone
    }
    
    with open(install_dir / "cluster_config.json", 'w') as f:
        json.dump(cluster_config, f, indent=2)
    
    # Create start script
    _create_start_script(install_dir, cluster_config)


def _setup_cluster(
    install_dir: Path,
    cluster_size: int,
    master_port: int,
    volume_port: int,
    filer_port: int,
    s3_port: int,
    access_key: str,
    secret_key: str
) -> None:
    """Setup multi-node SeaweedFS cluster."""
    
    # For now, this creates a single-node setup
    # TODO: Implement true multi-node cluster setup
    click.echo("⚠️  Multi-node cluster setup not yet implemented. Creating standalone setup.")
    _setup_standalone(install_dir, master_port, volume_port, filer_port, s3_port, access_key, secret_key)


def _create_start_script(install_dir: Path, config: dict) -> None:
    """Create start script for SeaweedFS."""
    
    script_content = f"""#!/bin/bash
# SeaweedFS Start Script
# Generated by gnosis-track

INSTALL_DIR="{install_dir}"
WEED="$INSTALL_DIR/weed"

# Start master
$WEED master \\
    -port={config['master_port']} \\
    -mdir="$INSTALL_DIR/master" \\
    -defaultReplication={config['replication']} &

echo "Master started on port {config['master_port']}"
sleep 2

# Start volume
$WEED volume \\
    -port={config['volume_port']} \\
    -dir="$INSTALL_DIR/volume" \\
    -mserver="localhost:{config['master_port']}" \\
    -max=100 &

echo "Volume started on port {config['volume_port']}"
sleep 2

# Start filer
$WEED filer \\
    -port={config['filer_port']} \\
    -master="localhost:{config['master_port']}" \\
    -dir="$INSTALL_DIR/filer" &

echo "Filer started on port {config['filer_port']}"
sleep 2

# Start S3
$WEED s3 \\
    -port={config['s3_port']} \\
    -filer="localhost:{config['filer_port']}" \\
    -config="$INSTALL_DIR/s3_config.json" &

echo "S3 gateway started on port {config['s3_port']}"
echo "SeaweedFS cluster is starting up..."
echo "S3 endpoint: http://localhost:{config['s3_port']}"
echo "Access key: {config['access_key']}"
"""
    
    script_path = install_dir / "start.sh"
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    script_path.chmod(0o755)


def _start_seaweedfs_cluster(install_dir: Path, config: dict) -> None:
    """Start SeaweedFS cluster."""
    
    binary_path = install_dir / "weed"
    
    # Start master
    master_cmd = [
        str(binary_path), "master",
        f"-port={config['master_port']}",
        f"-mdir={install_dir}/master",
        f"-defaultReplication={config['replication']}"
    ]
    
    subprocess.Popen(master_cmd, cwd=install_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    # Start volume
    volume_cmd = [
        str(binary_path), "volume",
        f"-port={config['volume_port']}",
        f"-dir={install_dir}/volume",
        f"-mserver=localhost:{config['master_port']}",
        "-max=100"
    ]
    
    subprocess.Popen(volume_cmd, cwd=install_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    # Start filer
    filer_cmd = [
        str(binary_path), "filer",
        f"-port={config['filer_port']}",
        f"-master=localhost:{config['master_port']}",
        f"-dir={install_dir}/filer"
    ]
    
    subprocess.Popen(filer_cmd, cwd=install_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    
    # Start S3
    s3_cmd = [
        str(binary_path), "s3",
        f"-port={config['s3_port']}",
        f"-filer=localhost:{config['filer_port']}",
        f"-config={install_dir}/s3_config.json"
    ]
    
    subprocess.Popen(s3_cmd, cwd=install_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)


def _stop_seaweedfs_processes() -> None:
    """Stop all SeaweedFS processes."""
    
    # On Unix systems, try to kill processes by name
    if platform.system() != "Windows":
        try:
            subprocess.run(["pkill", "-f", "weed"], check=False)
        except FileNotFoundError:
            # pkill not available, try killall
            try:
                subprocess.run(["killall", "weed"], check=False)
            except FileNotFoundError:
                pass
    else:
        # On Windows, use taskkill
        try:
            subprocess.run(["taskkill", "/f", "/im", "weed.exe"], check=False)
        except FileNotFoundError:
            pass


def _check_seaweedfs_processes() -> dict:
    """Check which SeaweedFS processes are running."""
    
    processes = {}
    
    if platform.system() != "Windows":
        try:
            # Use pgrep to find processes
            result = subprocess.run(["pgrep", "-f", "weed"], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                
                # Try to determine which service each PID is running
                for pid in pids:
                    try:
                        cmd_result = subprocess.run(["ps", "-p", pid, "-o", "command="], capture_output=True, text=True)
                        if cmd_result.returncode == 0:
                            command = cmd_result.stdout.strip()
                            
                            if "master" in command:
                                processes["master"] = pid
                            elif "volume" in command:
                                processes["volume"] = pid
                            elif "filer" in command:
                                processes["filer"] = pid
                            elif "s3" in command:
                                processes["s3"] = pid
                    except:
                        pass
        except FileNotFoundError:
            pass
    
    return processes