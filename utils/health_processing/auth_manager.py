#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
认证管理器
处理ljwx-boot系统的登录认证

@Author: bruno.gao <gaojunivas@gmail.com>
@ProjectName: ljwx-boot
@CreateTime: 2025-01-26
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional

class AuthManager:
    """认证管理器"""
    
    def __init__(self, auth_url: str, username: str, password: str, timeout: int = 30):
        self.auth_url = auth_url
        self.username = username
        self.password = password
        self.timeout = timeout
        self.token = None
        self.token_expires = None
        self.session = requests.Session()
        
        # 设置日志
        self.logger = logging.getLogger(f"{__name__}.AuthManager")
        
    def login(self) -> bool:
        """执行登录获取token"""
        try:
            self.logger.info(f"🔐 开始登录认证: {self.auth_url}")
            
            login_data = {
                "userName": self.username,
                "password": self.password
            }
            
            response = self.session.post(
                self.auth_url,
                json=login_data,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            self.logger.debug(f"登录请求状态码: {response.status_code}")
            self.logger.debug(f"登录响应头: {dict(response.headers)}")
            
            response.raise_for_status()
            
            result = response.json()
            self.logger.debug(f"登录响应内容: {result}")
            
            if result.get('code') == 200:
                data = result.get('data', {})
                self.token = data.get('token') or data.get('accessToken')
                
                if self.token:
                    # 设置token过期时间（默认2小时）
                    self.token_expires = datetime.now() + timedelta(hours=2)
                    
                    # 更新session的Authorization头
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.token}'
                    })
                    
                    self.logger.info(f"✅ 登录成功，token已获取")
                    self.logger.debug(f"Token: {self.token[:20]}...")
                    return True
                else:
                    self.logger.error(f"❌ 登录响应中未找到token: {result}")
                    return False
            else:
                error_msg = result.get('message') or result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 登录失败: {error_msg}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ 登录请求失败: {str(e)}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ 登录响应解析失败: {str(e)}")
            self.logger.debug(f"响应内容: {response.text if 'response' in locals() else 'N/A'}")
            return False
        except Exception as e:
            self.logger.error(f"❌ 登录过程异常: {str(e)}")
            return False
    
    def is_token_valid(self) -> bool:
        """检查token是否有效"""
        if not self.token:
            return False
        
        if not self.token_expires:
            return True  # 如果没有设置过期时间，假设有效
        
        return datetime.now() < self.token_expires
    
    def ensure_authenticated(self) -> bool:
        """确保已认证，如果token过期则重新登录"""
        if self.is_token_valid():
            self.logger.debug("✅ Token仍然有效")
            return True
        
        self.logger.info("🔄 Token已过期或不存在，重新登录")
        return self.login()
    
    def get_authenticated_session(self) -> Optional[requests.Session]:
        """获取已认证的session"""
        if self.ensure_authenticated():
            return self.session
        return None
    
    def get_token(self) -> Optional[str]:
        """获取当前有效的token"""
        if self.ensure_authenticated():
            return self.token
        return None
    
    def logout(self):
        """登出（清理本地认证信息）"""
        self.token = None
        self.token_expires = None
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        self.logger.info("🔓 已登出，认证信息已清理")

def create_auth_manager(config: Dict) -> Optional[AuthManager]:
    """从配置创建认证管理器"""
    ljwx_config = config.get('ljwx_boot', {})
    
    auth_url = ljwx_config.get('auth_url')
    username = ljwx_config.get('username')
    password = ljwx_config.get('password')
    timeout = ljwx_config.get('timeout', 30)
    
    if not all([auth_url, username, password]):
        logging.getLogger(__name__).warning("⚠️ 认证配置不完整，跳过认证")
        return None
    
    return AuthManager(auth_url, username, password, timeout)

def test_auth_manager():
    """测试认证管理器"""
    import json
    
    # 加载配置
    try:
        with open('health_processing_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ 无法加载配置文件: {e}")
        return False
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 创建认证管理器
    auth_manager = create_auth_manager(config)
    if not auth_manager:
        print("❌ 无法创建认证管理器")
        return False
    
    # 测试登录
    if auth_manager.login():
        print("✅ 认证测试成功")
        print(f"Token: {auth_manager.get_token()[:20]}...")
        
        # 测试获取已认证的session
        session = auth_manager.get_authenticated_session()
        if session:
            print("✅ 已认证的session获取成功")
        
        auth_manager.logout()
        return True
    else:
        print("❌ 认证测试失败")
        return False

if __name__ == "__main__":
    test_auth_manager()