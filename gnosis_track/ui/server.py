"""
FastAPI server for gnosis-track UI.

High-performance web interface for log viewing and management with automatic API docs.
"""

import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from gnosis_track.core.config_manager import ConfigManager
from gnosis_track.core.seaweed_client import SeaweedClient
from gnosis_track.core.bucket_manager import BucketManager
from gnosis_track.core.auth_manager import AuthManager
from gnosis_track.core.token_manager import TokenManager
from gnosis_track.logging.log_streamer import LogStreamer


# Pydantic models for API responses
class LogEntry(BaseModel):
    """Single log entry"""
    timestamp: str
    level: str
    message: str
    validator_uid: Optional[int] = None

class LogsResponse(BaseModel):
    """Logs response"""
    validator_uid: int
    run_id: str
    logs: List[LogEntry]
    total: int

class S3Credentials(BaseModel):
    """S3 credentials for validator"""
    endpoint_url: str
    access_key: str
    secret_key: str
    bucket_name: str
    region: str

class TokenRequest(BaseModel):
    """API token request"""
    api_key: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    minio_connected: bool
    timestamp: str

class ValidatorConfig(BaseModel):
    """Validator configuration"""
    run_info: Dict[str, Any]


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """
    Create FastAPI application.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        FastAPI application instance
    """
    app = FastAPI(
        title="Gnosis Track API",
        description="Open Source Centralized Logging for AI Validators",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
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
    
    token_manager = TokenManager()
    
    log_streamer = LogStreamer(
        seaweed_client, 
        config.logging.bucket_name
    )
    
    # Static files and templates - use absolute paths
    import pkg_resources
    try:
        # Try to get package resource paths
        template_dir = pkg_resources.resource_filename('gnosis_track', 'ui/templates')
        static_dir = pkg_resources.resource_filename('gnosis_track', 'ui/static')
    except:
        # Fallback to relative paths
        template_dir = "gnosis_track/ui/templates"
        static_dir = "gnosis_track/ui/static"
    
    templates = Jinja2Templates(directory=template_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    
    # Health check endpoint
    @app.get("/health", response_model=HealthResponse, tags=["System"])
    async def health_check():
        """Check if the API and SeaweedFS are running"""
        try:
            # Test SeaweedFS connection
            seaweed_client.list_buckets()
            minio_connected = True
        except Exception:
            minio_connected = False
        
        return HealthResponse(
            status="healthy" if minio_connected else "degraded",
            minio_connected=minio_connected,
            timestamp=datetime.now().isoformat()
        )
    
    # Web UI routes
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def home(request: Request):
        """Serve the main UI page"""
        return templates.TemplateResponse("index.html", {"request": request})
    
    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        """Return empty favicon to prevent 404 errors"""
        return HTMLResponse(content="", status_code=204)
    
    # API routes
    @app.get("/api/validators", 
             response_model=List[int],
             summary="List validators",
             description="Get list of all validators with logs",
             tags=["Validators"])
    async def list_validators():
        """Get list of all validators that have logs"""
        try:
            validators = log_streamer.get_validators()
            return validators
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/validators/{validator_uid}/runs", 
             response_model=List[str],
             summary="Get validator runs",
             description="Get list of all runs for a specific validator",
             tags=["Validators"])
    async def get_validator_runs(validator_uid: int):
        """Get all runs for a validator"""
        try:
            runs = log_streamer.get_runs(validator_uid)
            return runs
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/validators/{validator_uid}/logs",
             response_model=LogsResponse,
             summary="Get validator logs", 
             description="Get logs for a specific validator run",
             tags=["Validators"])
    async def get_validator_logs(
        validator_uid: int,
        run_id: Optional[str] = Query(None),
        limit: int = Query(100, ge=1, le=50000),
        level: Optional[str] = Query(None)
    ):
        """Get logs for a validator"""
        try:
            # Get the latest run first
            runs = log_streamer.get_runs(validator_uid)
            if not runs:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No runs found for validator {validator_uid}"
                )
            
            latest_run = runs[0]  # Most recent run
            logs = log_streamer._fetch_all_logs(
                validator_uid, latest_run, level, limit
            )
            
            return LogsResponse(
                validator_uid=validator_uid,
                run_id=latest_run,
                logs=[LogEntry(**log) for log in logs],
                total=len(logs)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/validators/{validator_uid}/latest",
             response_model=LogsResponse,
             summary="Get latest validator logs",
             description="Get latest logs for a validator",
             tags=["Validators"])
    async def get_latest_validator_logs(
        validator_uid: int,
        limit: int = Query(100, ge=1, le=50000),
        level: Optional[str] = Query(None),
        since: Optional[str] = Query(None)
    ):
        """Get latest logs for a validator"""
        try:
            runs = log_streamer.get_runs(validator_uid)
            if not runs:
                raise HTTPException(
                    status_code=404,
                    detail=f"No runs found for validator {validator_uid}"
                )
            
            latest_run = runs[0]
            logs = log_streamer._fetch_all_logs(
                validator_uid, latest_run, level, limit
            )
            
            return LogsResponse(
                validator_uid=validator_uid,
                run_id=latest_run,
                logs=[LogEntry(**log) for log in logs],
                total=len(logs)
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/validators/{validator_uid}/config",
             response_model=ValidatorConfig,
             summary="Get validator config",
             description="Get configuration for a validator run",
             tags=["Validators"])
    async def get_validator_config(
        validator_uid: int,
        run_id: Optional[str] = Query(None)
    ):
        """Get validator configuration"""
        try:
            if not run_id:
                runs = log_streamer.get_runs(validator_uid)
                if not runs:
                    raise HTTPException(
                        status_code=404,
                        detail=f"No runs found for validator {validator_uid}"
                    )
                run_id = runs[0]
            
            config_data = log_streamer.get_run_config(validator_uid, run_id)
            if config_data:
                return ValidatorConfig(run_info=config_data)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Config not found for validator {validator_uid}, run {run_id}"
                )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/auth/s3-credentials",
              response_model=S3Credentials,
              summary="Get S3 credentials",
              description="Exchange API token for S3 upload credentials",
              tags=["Authentication"])
    async def get_s3_credentials(token_request: TokenRequest):
        """Get S3 credentials using API token"""
        try:
            # Verify the API token
            project = token_manager.verify_token(token_request.api_key)
            if not project:
                raise HTTPException(status_code=401, detail="Invalid API token")
            
            # Return S3 credentials
            return S3Credentials(
                endpoint_url=endpoint_url,
                access_key=seaweed_config.access_key,
                secret_key=seaweed_config.secret_key,
                bucket_name=config.logging.bucket_name,
                region="us-east-1"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    return app


def main(config=None):
    """Main entry point for FastAPI server"""
    # Handle both CLI call with config and direct call
    if config is None:
        # Called directly, parse command line arguments
        import argparse
        
        parser = argparse.ArgumentParser(description='Gnosis Track FastAPI Server')
        parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
        parser.add_argument('--port', type=int, default=8081, help='Port to bind to')
        parser.add_argument('--config', help='Path to config file')
        parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
        parser.add_argument('--auth-required', action='store_true', help='Enable authentication')
        
        args = parser.parse_args()
        
        app = create_app(args.config)
        host = args.host
        port = args.port
        reload = args.reload
        auth_required = args.auth_required
    else:
        # Called from CLI with config object
        app = create_app()
        # Use config object values
        host = getattr(config.ui, 'host', '127.0.0.1')
        port = getattr(config.ui, 'port', 8081)
        reload = getattr(config.ui, 'debug', False)
        auth_required = getattr(config.ui, 'auth_required', False)
    
    print("🚀 Starting Gnosis-Track FastAPI server...")
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 API Docs: http://{host}:{port}/docs")
    print(f"📖 ReDoc: http://{host}:{port}/redoc")
    print(f"🔐 Auth: {'Required' if auth_required else 'Disabled'}")
    print(f"🔧 Debug: {reload}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload
    )


if __name__ == "__main__":
    main()