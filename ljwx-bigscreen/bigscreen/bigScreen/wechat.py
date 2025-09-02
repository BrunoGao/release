import requests
from datetime import datetime
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到Python路径以导入配置
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import CORP_ID, CORP_SECRET, CORP_AGENT_ID, CORP_API_URL, CORP_WECHAT_ENABLED, CORP_WECHAT_TOUSER

class CorpWeChatConfig:
    """企业微信配置管理类"""
    
    def __init__(self):
        """初始化企业微信配置"""
        self.corp_id = CORP_ID
        self.corp_secret = CORP_SECRET
        self.agent_id = CORP_AGENT_ID
        self.api_url = CORP_API_URL
        self.enabled = CORP_WECHAT_ENABLED
        self.touser = CORP_WECHAT_TOUSER
        self.access_token = ""
    
    def is_enabled(self) -> bool:
        """检查企业微信告警是否启用"""
        return self.enabled
    
    def is_configured(self) -> tuple:
        """检查企业微信配置是否完整"""
        missing = []
        if not self.corp_id: missing.append('CORP_ID')
        if not self.corp_secret: missing.append('CORP_SECRET')
        if not self.agent_id: missing.append('CORP_AGENT_ID')
        
        if missing:
            return False, f"缺少配置: {', '.join(missing)}"
        return True, "配置完整"
    
    def get_access_token(self) -> str:
        """获取企业微信AccessToken"""
        if not self.is_enabled():
            print("企业微信告警已禁用")
            return ""
        
        configured, msg = self.is_configured()
        if not configured:
            print(f"企业微信配置不完整: {msg}")
            return ""
        
        try:
            url = f"{self.api_url}/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.corp_secret}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if data.get("errcode") == 0:
                self.access_token = data["access_token"]
                print(f"企业微信AccessToken获取成功")
                return self.access_token
            else:
                print(f"企业微信AccessToken获取失败: {data.get('errmsg')}")
                return ""
        except Exception as e:
            print(f"企业微信AccessToken请求异常: {e}")
            return ""
    
    def send_alert(self, alert_type: str, user_name: str, severity: str, time_str: str = None) -> dict:
        """发送企业微信告警消息"""
        if not self.is_enabled():
            return {"success": False, "message": "企业微信告警已禁用"}
        
        configured, msg = self.is_configured()
        if not configured:
            return {"success": False, "message": f"企业微信配置不完整: {msg}"}
        
        token = self.get_access_token()
        if not token:
            return {"success": False, "message": "无法获取AccessToken"}
        
        if time_str is None:
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            url = f"{self.api_url}/cgi-bin/message/send?access_token={token}"
            
            markdown_template = f"""\
🚨 **<font color="warning">人员告警通知</font>**
> **告警类型：** <font color="comment">{alert_type}</font>  
> **告警人员：** <font color="comment">{user_name}</font>  
> **告警等级：** <font color="red">{severity}</font>  
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

# 创建全局配置实例
corp_wechat_config = CorpWeChatConfig()

# 兼容原有接口的函数封装
def get_access_token():
    """获取企业微信AccessToken - 兼容原有接口"""
    return corp_wechat_config.get_access_token()

def send_message(alert_type, user_name, severity, time_str=None):
    """发送告警消息 - 兼容原有接口"""
    result = corp_wechat_config.send_alert(alert_type, user_name, severity, time_str)
    return result.get('data', result)

def send_message1(content):
    """发送简单消息 - 兼容原有接口"""
    if not corp_wechat_config.is_enabled():
        return {"errcode": 1, "errmsg": "企业微信告警已禁用"}
    
    token = get_access_token()
    if not token:
        return {"errcode": 1, "errmsg": "无法获取AccessToken"}
    
    url = f"{corp_wechat_config.api_url}/cgi-bin/message/send?access_token={token}"
    
    data = {
        "touser": corp_wechat_config.touser,
        "msgtype": "markdown",
        "agentid": corp_wechat_config.agent_id,
        "markdown": {
            "content": f"📢 **告警通知**\n> {content}\n> 🕒 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        }
    }
    
    response = requests.post(url, json=data)
    return response.json()

def send_message_table(device_id="Watch_001", temp="41.5°C", threshold="38°C", time_str="2025-03-26 10:00"):
    """发送表格消息 - 兼容原有接口"""
    if not corp_wechat_config.is_enabled():
        return {"errcode": 1, "errmsg": "企业微信告警已禁用"}
    
    token = get_access_token()
    if not token:
        return {"errcode": 1, "errmsg": "无法获取AccessToken"}
    
    url = f"{corp_wechat_config.api_url}/cgi-bin/message/send?access_token={token}"

    markdown_template = f"""\
🔥 **<font color="warning">健康监测告警</font>**

| 项目 | 内容 |
|------|------|
| **设备编号** | `{device_id}` |
| **当前温度** | <font color="red">{temp}</font> |
| **阈值范围** | {threshold} 以下 |
| **时间** | {time_str} |

请尽快处理相关异常情况！
"""
    data = {
        "touser": corp_wechat_config.touser,
        "msgtype": "markdown",
        "agentid": corp_wechat_config.agent_id,
        "markdown": {
            "content": markdown_template
        }
    }
    response = requests.post(url, json=data)
    return response.json()

def send_message_with_action(device_id="Watch_001", temp="41.5°C", threshold="38°C", time_str="2025-03-26 10:00"):
    """发送带操作链接的消息 - 兼容原有接口"""
    if not corp_wechat_config.is_enabled():
        return {"errcode": 1, "errmsg": "企业微信告警已禁用"}
    
    token = get_access_token()
    if not token:
        return {"errcode": 1, "errmsg": "无法获取AccessToken"}
    
    url = f"{corp_wechat_config.api_url}/cgi-bin/message/send?access_token={token}"

    # 你服务器上的处理确认链接，例如记录处理操作
    confirm_url = f"https://www.heguang-tech.cn/api/confirm_alert?device={device_id}&temp={temp}"

    markdown_template = f"""\
🚨 **<font color="warning">健康监测告警</font>**

> **设备编号：** `{device_id}`  
> **当前温度：** <font color="red">{temp}</font>  
> **阈值范围：** {threshold} 以下  
> **告警时间：** {time_str}

📍请点击以下链接进行确认处理：

👉 [<font color="info">我已处理</font>]({confirm_url})
"""

    data = {
        "touser": corp_wechat_config.touser,
        "msgtype": "markdown",
        "agentid": corp_wechat_config.agent_id,
        "markdown": {
            "content": markdown_template
        }
    }

    response = requests.post(url, json=data)
    return response.json()