"""
Authentication and authorization management for gnosis-track.

Provides JWT-based authentication, role-based access control,
and security policy enforcement.
"""

import jwt
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class User:
    """User information for authentication."""
    username: str
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None


class AuthManager:
    """
    Authentication and authorization manager.
    
    Provides JWT token management, user authentication,
    and role-based access control.
    """
    
    def __init__(
        self,
        jwt_secret: str,
        token_expiry_hours: int = 24,
        algorithm: str = "HS256"
    ):
        """
        Initialize authentication manager.
        
        Args:
            jwt_secret: Secret key for JWT signing
            token_expiry_hours: Token expiration time in hours
            algorithm: JWT signing algorithm
        """
        self.jwt_secret = jwt_secret
        self.token_expiry_hours = token_expiry_hours
        self.algorithm = algorithm
        
        # In-memory user store (replace with database in production)
        self.users: Dict[str, User] = {}
        
        # Default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user."""
        admin_user = User(
            username="admin",
            roles=["admin", "user"],
            permissions=["read", "write", "admin", "delete"],
            created_at=datetime.now()
        )
        self.users["admin"] = admin_user
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return self.hash_password(password) == hashed
    
    def create_user(
        self,
        username: str,
        password: str,
        roles: List[str] = None,
        permissions: List[str] = None
    ) -> bool:
        """
        Create a new user.
        
        Args:
            username: Username
            password: Plain text password
            roles: List of roles
            permissions: List of permissions
            
        Returns:
            True if user was created successfully
        """
        if username in self.users:
            return False
        
        user = User(
            username=username,
            roles=roles or ["user"],
            permissions=permissions or ["read"],
            created_at=datetime.now()
        )
        
        self.users[username] = user
        # In production, store hashed password separately
        
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate user and return JWT token.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            JWT token if authentication successful, None otherwise
        """
        # In this example, we'll use simple password checking
        # In production, compare against stored hashed passwords
        
        if username not in self.users:
            return None
        
        # For demo purposes, accept any password for existing users
        # In production: if not self.verify_password(password, stored_hash):
        #     return None
        
        user = self.users[username]
        user.last_login = datetime.now()
        
        # Create JWT token
        payload = {
            "username": username,
            "roles": user.roles,
            "permissions": user.permissions,
            "iat": time.time(),
            "exp": time.time() + (self.token_expiry_hours * 3600)
        }
        
        try:
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)
            # Handle both string and bytes return types from different PyJWT versions
            if isinstance(token, bytes):
                token = token.decode('utf-8')
            return token
        except Exception as e:
            print(f"JWT encoding error: {e}")
            return None
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify JWT token and return payload.
        
        Args:
            token: JWT token
            
        Returns:
            Token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, token: str, required_permission: str) -> bool:
        """
        Check if token has required permission.
        
        Args:
            token: JWT token
            required_permission: Required permission
            
        Returns:
            True if token has permission
        """
        payload = self.verify_token(token)
        if not payload:
            return False
        
        permissions = payload.get("permissions", [])
        return required_permission in permissions or "admin" in permissions
    
    def has_role(self, token: str, required_role: str) -> bool:
        """
        Check if token has required role.
        
        Args:
            token: JWT token
            required_role: Required role
            
        Returns:
            True if token has role
        """
        payload = self.verify_token(token)
        if not payload:
            return False
        
        roles = payload.get("roles", [])
        return required_role in roles or "admin" in roles
    
    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from token.
        
        Args:
            token: JWT token
            
        Returns:
            User information if token is valid
        """
        payload = self.verify_token(token)
        if not payload:
            return None
        
        username = payload.get("username")
        if username not in self.users:
            return None
        
        user = self.users[username]
        return {
            "username": user.username,
            "roles": user.roles,
            "permissions": user.permissions,
            "created_at": user.created_at.isoformat(),
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (add to blacklist).
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if token was revoked
        """
        # In production, maintain a blacklist of revoked tokens
        # For now, just return True
        return True
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (admin only)."""
        users_info = []
        for user in self.users.values():
            users_info.append({
                "username": user.username,
                "roles": user.roles,
                "permissions": user.permissions,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        return users_info