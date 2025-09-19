"""
API v1 路由模块
"""

from . import auth, alert, health, device, dashboard, main_bigscreen, personal_bigscreen, message

__all__ = [
    "auth",
    "alert",
    "health", 
    "device",
    "dashboard",
    "main_bigscreen",
    "personal_bigscreen",
    "message"
]