"""
Web server for gnosis-track UI.

Provides Flask-based web interface for log viewing and management.
"""

import os
import json
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS
from datetime import datetime
from typing import Dict, Any, List, Optional

from gnosis_track.core.config_manager import ConfigManager
from gnosis_track.core.seaweed_client import SeaweedClient
from gnosis_track.core.bucket_manager import BucketManager
from gnosis_track.core.auth_manager import AuthManager
from gnosis_track.logging.log_streamer import LogStreamer


def create_app(config_path: Optional[str] = None) -> Flask:
    """
    Create Flask application.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    app.secret_key = os.urandom(24)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Load configuration
    config_manager = ConfigManager(config_path)
    config = config_manager.get_config()
    
    # Initialize components
    seaweed_config = config.seaweedfs
    endpoint_url = f"{'https' if seaweed_config.use_ssl else 'http'}://{seaweed_config.s3_endpoint}"
    
    seaweed_client = SeaweedClient(
        endpoint_url=endpoint_url,
        access_key=seaweed_config.access_key,
        secret_key=seaweed_config.secret_key,
        use_ssl=seaweed_config.use_ssl,
        verify_ssl=seaweed_config.verify_ssl,
        timeout=seaweed_config.timeout,
        max_retries=seaweed_config.max_retries
    )
    
    bucket_manager = BucketManager(
        seaweed_client,
        default_encryption=config.security.encryption_enabled
    )
    
    auth_manager = AuthManager(
        jwt_secret=config.security.jwt_secret or 'default-secret-change-me',
        token_expiry_hours=24
    )
    
    log_streamer = LogStreamer(
        seaweed_client, 
        config.logging.bucket_name
    )
    
    @app.route('/')
    def index():
        """Main dashboard."""
        if config.ui.auth_required:
            if 'token' not in session:
                return redirect(url_for('login'))
        
        return render_template('index.html')
    
    @app.route('/app.js')
    def serve_js():
        """Serve the JavaScript file."""
        return app.send_static_file('app.js')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            token = auth_manager.authenticate(username, password)
            if token:
                session['token'] = token
                return redirect(url_for('index'))
            else:
                return render_template('login.html', error='Invalid credentials')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        """User logout."""
        session.pop('token', None)
        return redirect(url_for('login'))
    
    @app.route('/api/validators')
    def api_validators():
        """Get list of validators."""
        try:
            bucket_name = config.logging.bucket_name
            objects = seaweed_client.list_objects(bucket_name)
            
            validators = set()
            for obj in objects:
                parts = obj['Key'].split('/')
                if parts[0].startswith('validator_'):
                    uid = parts[0].replace('validator_', '')
                    validators.add(int(uid))
            
            return jsonify(sorted(list(validators)))
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/validators/<int:validator_uid>/runs')
    def api_validator_runs(validator_uid: int):
        """Get runs for a validator."""
        try:
            bucket_name = config.logging.bucket_name
            prefix = f"validator_{validator_uid}/"
            objects = seaweed_client.list_objects(bucket_name, prefix=prefix)
            
            runs = set()
            for obj in objects:
                parts = obj['Key'].split('/')
                if len(parts) >= 2:
                    runs.add(parts[1])
            
            return jsonify(sorted(list(runs)))
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/validators/<int:validator_uid>/logs')
    def api_validator_logs(validator_uid: int):
        """Get logs for a validator."""
        try:
            run_id = request.args.get('run_id')
            limit = int(request.args.get('limit', 100))
            level_filter = request.args.get('level')
            
            logs = log_streamer._fetch_all_logs(
                validator_uid, run_id, level_filter, limit
            )
            
            return jsonify({
                'validator_uid': validator_uid,
                'run_id': run_id,
                'logs': logs,
                'total': len(logs)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/validators/<int:validator_uid>/latest')
    def api_validator_latest_logs(validator_uid: int):
        """Get latest logs for a validator."""
        try:
            limit = int(request.args.get('limit', 100))
            level_filter = request.args.get('level')
            
            # Get the latest run first
            runs = log_streamer.get_runs(validator_uid)
            if not runs:
                return jsonify({
                    'validator_uid': validator_uid,
                    'run_id': 'latest',
                    'logs': [],
                    'total': 0,
                    'error': 'No runs found'
                })
            
            latest_run = runs[0]  # Most recent run
            logs = log_streamer._fetch_all_logs(
                validator_uid, latest_run, level_filter, limit
            )
            
            return jsonify({
                'validator_uid': validator_uid,
                'run_id': 'latest',
                'logs': logs,
                'total': len(logs)
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/validators/<int:validator_uid>/config')
    def api_validator_config(validator_uid: int):
        """Get validator configuration."""
        try:
            run_id = request.args.get('run_id')
            
            # Get the latest run if not specified
            if not run_id:
                runs = log_streamer.get_runs(validator_uid)
                if runs:
                    run_id = runs[0]
                else:
                    return jsonify({'error': 'No runs found'}), 404
            
            config_data = log_streamer.get_run_config(validator_uid, run_id)
            if config_data:
                return jsonify(config_data)
            else:
                return jsonify({'error': 'Config not found'}), 404
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/health')
    def api_health():
        """Health check endpoint."""
        try:
            # Check SeaweedFS connection
            health_check = seaweed_client.health_check()
            
            return jsonify({
                'status': 'healthy' if health_check else 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'seaweedfs': health_check,
                'version': '1.0.0'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/metrics')
    def api_metrics():
        """Get system metrics."""
        try:
            bucket_name = config.logging.bucket_name
            
            # Get bucket statistics
            objects = seaweed_client.list_objects(bucket_name)
            
            total_objects = len(objects)
            total_size = sum(obj.get('Size', 0) for obj in objects)
            
            # Count validators
            validators = set()
            for obj in objects:
                parts = obj['Key'].split('/')
                if parts[0].startswith('validator_'):
                    validators.add(parts[0])
            
            return jsonify({
                'total_objects': total_objects,
                'total_size_bytes': total_size,
                'total_validators': len(validators),
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('error.html', error='Page not found'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('error.html', error='Internal server error'), 500
    
    return app


def run_server(host: str = 'localhost', port: int = 8080, debug: bool = False):
    """
    Run the Flask development server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    app = create_app()
    app.run(host=host, port=port, debug=debug)


def main(config=None):
    """
    Main entry point for UI server.
    
    Args:
        config: Configuration object (optional)
    """
    if config:
        app = create_app()
        app.run(
            host=config.ui.host,
            port=config.ui.port,
            debug=config.ui.debug
        )
    else:
        run_server()


if __name__ == '__main__':
    run_server()