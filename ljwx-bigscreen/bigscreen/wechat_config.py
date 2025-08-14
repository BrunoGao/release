#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信告警配置管理模块
支持从环境变量动态读取微信配置，避免硬编码
客户可通过修改.env文件或Docker环境变量进行配置
支持普通微信和企业微信两种配置
"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Optional, Tuple

# 加载环境变量
load_dotenv()

class WeChatAlertConfig:
    """微信告警配置管理类"""
    
    def __init__(self):
        """初始化微信配置"""
        self.app_id = os.getenv('WECHAT_APP_ID', '')
        self.app_secret = os.getenv('WECHAT_APP_SECRET', '')
        self.template_id = os.getenv('WECHAT_TEMPLATE_ID', '')
        self.user_openid = os.getenv('WECHAT_USER_OPENID', '')
        self.api_url = os.getenv('WECHAT_API_URL', 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}')
        self.enabled = os.getenv('WECHAT_ALERT_ENABLED', 'true').lower() == 'true'
        self.access_token = ""
        self._last_error_time = 0 # 上次错误输出时间
        self._error_suppress_interval = 1800 # 错误抑制间隔30分钟
    
    def is_enabled(self) -> bool:
        """检查微信告警是否启用"""
        return self.enabled
    
    def is_configured(self) -> Tuple[bool, str]:
        """检查微信配置是否完整"""
        missing = []
        if not self.app_id:
            missing.append('WECHAT_APP_ID')
        if not self.app_secret:
            missing.append('WECHAT_APP_SECRET')
        if not self.template_id:
            missing.append('WECHAT_TEMPLATE_ID')
        if not self.user_openid:
            missing.append('WECHAT_USER_OPENID')
        
        if missing:
            return False, f"缺少配置: {', '.join(missing)}"
        return True, "配置完整"
    
    def _should_suppress_error(self) -> bool:
        """检查是否应该抑制错误输出"""
        import time
        current_time = time.time()
        if current_time - self._last_error_time < self._error_suppress_interval:
            return True
        self._last_error_time = current_time
        return False
    
    def get_access_token(self, silent: bool = False) -> Optional[str]:
        """获取微信AccessToken"""
        if not self.is_enabled():
            if not silent and not self._should_suppress_error():
                print("微信告警已禁用")
            return None
        
        configured, msg = self.is_configured()
        if not configured:
            if not silent and not self._should_suppress_error():
                print(f"微信配置不完整: {msg}")
            return None
        
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if "access_token" in data:
                self.access_token = data["access_token"]
                if not silent:
                    print(f"微信AccessToken获取成功，有效期: {data.get('expires_in', 7200)}秒")
                return self.access_token
            else:
                if not silent and not self._should_suppress_error():
                    print(f"微信AccessToken获取失败: {data}")
                return None
        except Exception as e:
            if not silent and not self._should_suppress_error():
                print(f"微信AccessToken请求异常: {e}")
            return None
    
    def send_alert(self, alert_type: str, user_name: str, severity_level: str, user_openid: str = None) -> Dict:
        """发送微信告警消息"""
        if not self.is_enabled():
            return {"success": False, "message": "微信告警已禁用"}
        
        configured, msg = self.is_configured()
        if not configured:
            return {"success": False, "message": f"微信配置不完整: {msg}"}
        
        token = self.get_access_token()
        if not token:
            return {"success": False, "message": "无法获取AccessToken"}
        
        target_openid = user_openid or self.user_openid
        
        try:
            url = self.api_url.format(ACCESS_TOKEN=token)
            
            template_data = {
                "first": {"value": f"【{severity_level}】{alert_type}"},
                "keyword1": {"value": user_name},
                "keyword2": {"value": alert_type},
                "keyword3": {"value": severity_level},
                "remark": {"value": "请及时处理相关告警信息"}
            }
            
            data = {
                "touser": target_openid,
                "template_id": self.template_id,
                "data": template_data
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {"success": True, "message": "微信告警发送成功", "data": result}
            else:
                return {"success": False, "message": f"微信发送失败: {result.get('errmsg')}", "data": result}
                
        except Exception as e:
            return {"success": False, "message": f"微信发送异常: {str(e)}"}
    
    def test_config(self) -> Dict:
        """测试微信配置"""
        result = {
            "enabled": self.is_enabled(),
            "config_check": {},
            "token_test": {}
        }
        
        # 配置检查
        configured, msg = self.is_configured()
        result["config_check"] = {
            "success": configured,
            "message": msg
        }
        
        # Token测试
        if configured and result["enabled"]:
            token = self.get_access_token()
            result["token_test"] = {
                "success": token is not None,
                "message": "AccessToken获取成功" if token else "AccessToken获取失败"
            }
        else:
            result["token_test"] = {
                "success": False,
                "message": "配置不完整或未启用，跳过Token测试"
            }
        
        return result
    
    def get_env_template(self) -> str:
        """获取环境变量配置模板"""
        return """
# ==================== 微信告警配置 ====================
# 微信公众号APP ID
WECHAT_APP_ID=your_app_id_here
# 微信公众号APP SECRET
WECHAT_APP_SECRET=your_app_secret_here
# 微信模板消息ID
WECHAT_TEMPLATE_ID=your_template_id_here
# 微信用户OpenID(接收告警的用户)
WECHAT_USER_OPENID=your_openid_here
# 微信API接口地址(一般不需要修改)
WECHAT_API_URL=https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}
# 是否启用微信告警(true/false)
WECHAT_ALERT_ENABLED=true
"""

class CorpWeChatAlertConfig:
    """企业微信告警配置管理类"""
    
    def __init__(self):
        """初始化企业微信配置"""
        self.corp_id = os.getenv('CORP_ID', '')
        self.corp_secret = os.getenv('CORP_SECRET', '')
        self.agent_id = int(os.getenv('CORP_AGENT_ID', '0')) if os.getenv('CORP_AGENT_ID') else 0
        self.api_url = os.getenv('CORP_API_URL', 'https://qyapi.weixin.qq.com')
        self.enabled = os.getenv('CORP_WECHAT_ENABLED', 'true').lower() == 'true'
        self.touser = os.getenv('CORP_WECHAT_TOUSER', '@all')
        self.access_token = ""
        self._last_error_time = 0 # 上次错误输出时间
        self._error_suppress_interval = 1800 # 错误抑制间隔30分钟
    
    def is_enabled(self) -> bool:
        """检查企业微信告警是否启用"""
        return self.enabled
    
    def is_configured(self) -> Tuple[bool, str]:
        """检查企业微信配置是否完整"""
        missing = []
        if not self.corp_id:
            missing.append('CORP_ID')
        if not self.corp_secret:
            missing.append('CORP_SECRET')
        if not self.agent_id:
            missing.append('CORP_AGENT_ID')
        
        if missing:
            return False, f"缺少配置: {', '.join(missing)}"
        return True, "配置完整"
    
    def _should_suppress_error(self) -> bool:
        """检查是否应该抑制错误输出"""
        import time
        current_time = time.time()
        if current_time - self._last_error_time < self._error_suppress_interval:
            return True
        self._last_error_time = current_time
        return False
    
    def get_access_token(self, silent: bool = False) -> Optional[str]:
        """获取企业微信AccessToken"""
        if not self.is_enabled():
            if not silent and not self._should_suppress_error():
                print("企业微信告警已禁用")
            return None
        
        configured, msg = self.is_configured()
        if not configured:
            if not silent and not self._should_suppress_error():
                print(f"企业微信配置不完整: {msg}")
            return None
        
        try:
            url = f"{self.api_url}/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data["access_token"]
                if not silent:
                    print(f"企业微信AccessToken获取成功，有效期: {data.get('expires_in', 7200)}秒")
                return self.access_token
            else:
                if not silent and not self._should_suppress_error():
                    print(f"企业微信AccessToken获取失败: {data}")
                return None
        except Exception as e:
            if not silent and not self._should_suppress_error():
                print(f"企业微信AccessToken请求异常: {e}")
            return None
    
    def send_alert(self, alert_type: str, user_name: str, severity_level: str, time_str: str = None) -> Dict:
        """发送企业微信告警消息"""
        if not self.is_enabled():
            return {"success": False, "message": "企业微信告警已禁用"}
        
        configured, msg = self.is_configured()
        if not configured:
            return {"success": False, "message": f"企业微信配置不完整: {msg}"}
        
        token = self.get_access_token()
        if not token:
            return {"success": False, "message": "无法获取AccessToken"}
        
        if not time_str:
            from datetime import datetime
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            url = f"{self.api_url}/cgi-bin/message/send?access_token={token}"
            
            markdown_template = f"""\
🚨 **<font color="warning">人员告警通知</font>**
> **告警类型：** <font color="comment">{alert_type}</font>  
> **告警人员：** <font color="comment">{user_name}</font>  
> **告警等级：** <font color="red">{severity_level}</font>  
> **告警时间：** <font color="comment">{time_str}</font>  
"""
            
            data = {
                "touser": self.touser,
                "msgtype": "markdown",
                "agentid": self.agent_id,
                "markdown": {
                    "content": markdown_template
                }
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                return {"success": True, "message": "企业微信告警发送成功", "data": result}
            else:
                return {"success": False, "message": f"企业微信发送失败: {result.get('errmsg')}", "data": result}
                
        except Exception as e:
            return {"success": False, "message": f"企业微信发送异常: {str(e)}"}
    
    def test_config(self) -> Dict:
        """测试企业微信配置"""
        result = {
            "enabled": self.is_enabled(),
            "config_check": {},
            "token_test": {}
        }
        
        # 配置检查
        configured, msg = self.is_configured()
        result["config_check"] = {
            "success": configured,
            "message": msg
        }
        
        # Token测试
        if configured and result["enabled"]:
            token = self.get_access_token()
            result["token_test"] = {
                "success": token is not None,
                "message": "AccessToken获取成功" if token else "AccessToken获取失败"
            }
        else:
            result["token_test"] = {
                "success": False,
                "message": "配置不完整或未启用，跳过Token测试"
            }
        
        return result
    
    def get_env_template(self) -> str:
        """获取企业微信环境变量配置模板"""
        return """
# ==================== 企业微信配置 ====================
# 企业微信企业ID
CORP_ID=your_corp_id_here
# 企业微信应用Secret
CORP_SECRET=your_corp_secret_here
# 企业微信应用AgentID
CORP_AGENT_ID=your_agent_id_here
# 企业微信API地址(一般不需要修改)
CORP_API_URL=https://qyapi.weixin.qq.com
# 是否启用企业微信告警(true/false)
CORP_WECHAT_ENABLED=true
# 企业微信消息接收用户(默认@all为全员)
CORP_WECHAT_TOUSER=@all
"""

def get_wechat_config() -> WeChatAlertConfig:
    """获取微信配置单例"""
    if not hasattr(get_wechat_config, '_instance'):
        get_wechat_config._instance = WeChatAlertConfig()
    return get_wechat_config._instance

def get_corp_wechat_config() -> CorpWeChatAlertConfig:
    """获取企业微信配置单例"""
    if not hasattr(get_corp_wechat_config, '_instance'):
        get_corp_wechat_config._instance = CorpWeChatAlertConfig()
    return get_corp_wechat_config._instance

def get_unified_wechat_config() -> Dict:
    """获取统一的微信配置信息"""
    wechat_config = get_wechat_config()
    corp_wechat_config = get_corp_wechat_config()
    
    return {
        'wechat': {
            'enabled': wechat_config.is_enabled(),
            'configured': wechat_config.is_configured()[0],
            'type': '公众号'
        },
        'corp_wechat': {
            'enabled': corp_wechat_config.is_enabled(),
            'configured': corp_wechat_config.is_configured()[0],
            'type': '企业微信'
        }
    }

# 测试功能
if __name__ == "__main__":
    print("🔧 微信配置管理模块测试")
    print("=" * 50)
    
    # 测试普通微信
    print("📱 测试普通微信配置:")
    wechat = get_wechat_config()
    wechat_test = wechat.test_config()
    print(f"  启用状态: {wechat_test['enabled']}")
    print(f"  配置状态: {wechat_test['config_check']['message']}")
    print(f"  Token测试: {wechat_test['token_test']['message']}")
    
    print("\n🏢 测试企业微信配置:")
    corp_wechat = get_corp_wechat_config()
    corp_test = corp_wechat.test_config()
    print(f"  启用状态: {corp_test['enabled']}")
    print(f"  配置状态: {corp_test['config_check']['message']}")
    print(f"  Token测试: {corp_test['token_test']['message']}")
    
    print("\n📊 统一配置信息:")
    unified = get_unified_wechat_config()
    for key, config in unified.items():
        print(f"  {config['type']}: 启用={config['enabled']}, 配置完整={config['configured']}")
    
    print("\n✅ 测试完成") 