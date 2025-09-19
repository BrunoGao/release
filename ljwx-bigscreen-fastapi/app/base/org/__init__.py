"""
组织架构基础模块
提供组织结构管理功能
"""

from .models import Organization, Department, Position
from .service import OrganizationService
from .tree import OrgTreeBuilder
from .permissions import OrgPermissionManager

__all__ = [
    "Organization",
    "Department", 
    "Position",
    "OrganizationService",
    "OrgTreeBuilder",
    "OrgPermissionManager"
]