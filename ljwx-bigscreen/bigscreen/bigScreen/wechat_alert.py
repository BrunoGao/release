#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信告警模块 #微信实时告警功能
支持通用事件的微信告警发送
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class WeChatAlert:
    """微信告警类 #微信告警管理"""
    
    def __init__(self):
        self.app_id = os.getenv('WECHAT_APP_ID', '')
        self.app_secret = os.getenv('WECHAT_APP_SECRET', '')
        self.template_id = os.getenv('WECHAT_TEMPLATE_ID', '')
        self.user_openid = os.getenv('WECHAT_USER_OPENID', '')
        self.api_url = os.getenv('WECHAT_API_URL', 'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={ACCESS_TOKEN}')
        self.enabled = os.getenv('WECHAT_ALERT_ENABLED', 'true').lower() == 'true'
        self.access_token = None
        
    def get_access_token(self):
        """获取微信AccessToken #获取访问令牌"""
        if not self.app_id or not self.app_secret:
            print("⚠️ 微信配置不完整，无法获取AccessToken")
            return None
            
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
            response = requests.get(url, timeout=10)
            result = response.json()
            
            if 'access_token' in result:
                self.access_token = result['access_token']
                print(f"✅ 微信AccessToken获取成功")
                return self.access_token
            else:
                print(f"❌ 微信AccessToken获取失败: {result}")
                return None
                
        except Exception as e:
            print(f"❌ 获取微信AccessToken异常: {e}")
            return None
    
    def send_alert(self, alert_type, device_sn, alert_desc, severity_level, user_name, org_name):  # 修改: department_info -> org_name
        """发送微信告警 #发送微信告警消息"""
        if not self.enabled:
            print("⚠️ 微信告警未启用")
            return {'success': False, 'message': '微信告警未启用'}
        
        if not self.access_token:
            self.access_token = self.get_access_token()
            
        if not self.access_token:
            return {'success': False, 'message': '无法获取微信AccessToken'}
        
        try:
            # 构建告警消息
            severity_colors = {
                'critical': '#FF0000',  # 红色
                'high': '#FF6600',      # 橙色  
                'medium': '#FFCC00',    # 黄色
                'low': '#00CC00'        # 绿色
            }
            
            color = severity_colors.get(severity_level, '#FF6600')
            
            # 微信模板消息数据
            template_data = {
                "touser": self.user_openid,
                "template_id": self.template_id,
                "data": {
                    "first": {
                        "value": f"🚨 {alert_type}告警通知",
                        "color": color
                    },
                    "keyword1": {
                        "value": user_name,
                        "color": "#000000"
                    },
                    "keyword2": {
                        "value": alert_type,
                        "color": "#000000"
                    },
                    "keyword3": {
                        "value": severity_level,
                        "color": color
                    },
                    "keyword4": {
                        "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "color": "#000000"
                    },
                    "remark": {
                        "value": f"\n设备: {device_sn}\n部门: {org_name}\n详情: {alert_desc}",  # 修改: department_info -> org_name
                        "color": "#666666"
                    }
                }
            }
            
            # 发送微信消息
            url = self.api_url.format(ACCESS_TOKEN=self.access_token)
            response = requests.post(url, json=template_data, timeout=10)
            result = response.json()
            
            if result.get('errcode') == 0:
                print(f"✅ 微信告警发送成功: {alert_type}")
                return {'success': True, 'message': '微信告警发送成功', 'data': result}
            else:
                print(f"❌ 微信告警发送失败: {result}")
                return {'success': False, 'message': f"微信告警发送失败: {result.get('errmsg')}", 'data': result}
                
        except Exception as e:
            print(f"❌ 发送微信告警异常: {e}")
            return {'success': False, 'message': f'发送微信告警异常: {str(e)}'}

# 全局微信告警实例
wechat_alert = WeChatAlert()

def send_wechat_alert(alert_type, device_sn, alert_desc, severity_level, user_name, org_name):
    """发送微信告警 - 全局函数接口 #微信告警全局接口"""
    return wechat_alert.send_alert(alert_type, device_sn, alert_desc, severity_level, user_name, org_name) 