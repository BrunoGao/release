# -*- coding: utf-8 -*-
"""
LJWX告警Webhook处理模块
接收Prometheus/Alertmanager告警并发送微信通知
"""
from flask import Blueprint, request, jsonify
import json
import requests
import logging
from datetime import datetime
from config import WECHAT_ALERT_ENABLED, WECHAT_API_URL, WECHAT_USER_OPENID, WECHAT_TEMPLATE_ID

# 创建蓝图
alert_webhook_bp = Blueprint('alert_webhook', __name__)

# 配置日志
logger = logging.getLogger('alert_webhook')

def send_wechat_alert(alert_data, severity='warning'):
    """发送微信告警通知"""
    if not WECHAT_ALERT_ENABLED:
        logger.info('微信告警未启用，跳过发送')
        return False
        
    try:
        # 构建微信消息内容
        alert_name = alert_data.get('alertname', '未知告警')
        instance = alert_data.get('instance', '未知实例')
        summary = alert_data.get('summary', '系统告警')
        description = alert_data.get('description', '请检查系统状态')
        
        # 根据严重程度设置颜色和图标
        severity_config = {
            'critical': {'color': '#FF0000', 'icon': '🚨', 'level': '严重'},
            'warning': {'color': '#FFA500', 'icon': '⚠️', 'level': '警告'},
            'info': {'color': '#0066CC', 'icon': 'ℹ️', 'level': '信息'}
        }
        
        config = severity_config.get(severity, severity_config['warning'])
        
        # 微信模板消息内容
        message_data = {
            'touser': WECHAT_USER_OPENID,
            'template_id': WECHAT_TEMPLATE_ID,
            'data': {
                'first': {
                    'value': f"{config['icon']} LJWX系统告警通知",
                    'color': config['color']
                },
                'keyword1': {
                    'value': alert_name,
                    'color': '#000000'
                },
                'keyword2': {
                    'value': config['level'],
                    'color': config['color']
                },
                'keyword3': {
                    'value': instance,
                    'color': '#000000'
                },
                'keyword4': {
                    'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'color': '#000000'
                },
                'remark': {
                    'value': f"\n{summary}\n{description}",
                    'color': '#666666'
                }
            }
        }
        
        # 发送微信消息
        response = requests.post(
            WECHAT_API_URL,
            json=message_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('errcode') == 0:
                logger.info(f'微信告警发送成功: {alert_name}')
                return True
            else:
                logger.error(f'微信告警发送失败: {result}')
                return False
        else:
            logger.error(f'微信API调用失败: {response.status_code}')
            return False
            
    except Exception as e:
        logger.error(f'发送微信告警时出错: {e}')
        return False

@alert_webhook_bp.route('/api/alerts/webhook', methods=['POST'])
def handle_alert_webhook():
    """处理通用告警webhook"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的JSON数据'}), 400
            
        alerts = data.get('alerts', [])
        logger.info(f'收到 {len(alerts)} 个告警')
        
        success_count = 0
        for alert in alerts:
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            # 构建告警数据
            alert_data = {
                'alertname': labels.get('alertname', '未知告警'),
                'instance': labels.get('instance', '未知实例'),
                'service': labels.get('service', '未知服务'),
                'severity': labels.get('severity', 'warning'),
                'summary': annotations.get('summary', '系统告警'),
                'description': annotations.get('description', '请检查系统状态'),
                'status': alert.get('status', 'firing')
            }
            
            # 发送微信告警
            if send_wechat_alert(alert_data, alert_data['severity']):
                success_count += 1
                
        return jsonify({
            'message': f'处理完成，成功发送 {success_count}/{len(alerts)} 个告警',
            'success_count': success_count,
            'total_count': len(alerts)
        })
        
    except Exception as e:
        logger.error(f'处理告警webhook时出错: {e}')
        return jsonify({'error': str(e)}), 500

@alert_webhook_bp.route('/api/alerts/webhook/critical', methods=['POST'])
def handle_critical_alert():
    """处理严重告警"""
    try:
        data = request.get_json()
        alerts = data.get('alerts', [])
        
        logger.warning(f'收到 {len(alerts)} 个严重告警')
        
        success_count = 0
        for alert in alerts:
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            alert_data = {
                'alertname': labels.get('alertname', '严重告警'),
                'instance': labels.get('instance', '未知实例'),
                'summary': annotations.get('summary', '系统严重告警'),
                'description': annotations.get('description', '系统出现严重问题，请立即处理')
            }
            
            if send_wechat_alert(alert_data, 'critical'):
                success_count += 1
                
        return jsonify({
            'message': f'严重告警处理完成，成功发送 {success_count}/{len(alerts)} 个',
            'success_count': success_count
        })
        
    except Exception as e:
        logger.error(f'处理严重告警时出错: {e}')
        return jsonify({'error': str(e)}), 500

@alert_webhook_bp.route('/api/alerts/webhook/warning', methods=['POST'])
def handle_warning_alert():
    """处理警告告警"""
    return handle_alert_webhook()

@alert_webhook_bp.route('/api/alerts/webhook/info', methods=['POST'])
def handle_info_alert():
    """处理信息告警"""
    try:
        data = request.get_json()
        alerts = data.get('alerts', [])
        
        logger.info(f'收到 {len(alerts)} 个信息告警')
        
        # 信息告警可以选择性发送微信通知
        success_count = 0
        for alert in alerts:
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            alert_data = {
                'alertname': labels.get('alertname', '信息告警'),
                'instance': labels.get('instance', '未知实例'),
                'summary': annotations.get('summary', '系统信息'),
                'description': annotations.get('description', '系统状态信息')
            }
            
            if send_wechat_alert(alert_data, 'info'):
                success_count += 1
                
        return jsonify({
            'message': f'信息告警处理完成，成功发送 {success_count}/{len(alerts)} 个',
            'success_count': success_count
        })
        
    except Exception as e:
        logger.error(f'处理信息告警时出错: {e}')
        return jsonify({'error': str(e)}), 500

@alert_webhook_bp.route('/api/alerts/test', methods=['POST'])
def test_alert():
    """测试告警功能"""
    try:
        test_alert_data = {
            'alertname': '测试告警',
            'instance': 'localhost:8001',
            'summary': '这是一个测试告警',
            'description': '用于验证告警系统是否正常工作'
        }
        
        if send_wechat_alert(test_alert_data, 'warning'):
            return jsonify({'message': '测试告警发送成功'})
        else:
            return jsonify({'error': '测试告警发送失败'}), 500
            
    except Exception as e:
        logger.error(f'测试告警时出错: {e}')
        return jsonify({'error': str(e)}), 500 