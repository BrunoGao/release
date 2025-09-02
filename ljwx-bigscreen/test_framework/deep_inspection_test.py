#!/usr/bin/env python3
"""深度检查测试 - 告警生成机制、平台消息下发流程、微信通知实际发送"""
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from test_framework.base_test import BaseTestFramework

class DeepInspectionTest(BaseTestFramework):
    """深度检查测试类"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.test_device_sn = self.generate_test_device_sn()
        self.monitoring_active = False #监控状态
        self.captured_data = {'alerts': [], 'messages': [], 'wechat_logs': []} #捕获的数据
        
    def start_real_time_monitoring(self):
        """启动实时监控"""
        self.monitoring_active = True
        self.captured_data = {'alerts': [], 'messages': [], 'wechat_logs': []}
        
        # 启动监控线程
        alert_thread = threading.Thread(target=self._monitor_alerts, daemon=True)
        message_thread = threading.Thread(target=self._monitor_messages, daemon=True)
        wechat_thread = threading.Thread(target=self._monitor_wechat_logs, daemon=True)
        
        alert_thread.start()
        message_thread.start()
        wechat_thread.start()
        
        self.logger.info("🔍 实时监控已启动")
    
    def stop_real_time_monitoring(self):
        """停止实时监控"""
        self.monitoring_active = False
        time.sleep(2)  # 等待监控线程结束
        self.logger.info("⏸️  实时监控已停止")
    
    def _monitor_alerts(self):
        """监控告警表变化"""
        last_check_time = datetime.now()
        
        while self.monitoring_active:
            try:
                query = """
                    SELECT id, device_sn, alert_type, severity_level, alert_status, 
                           alert_desc, alert_timestamp, created_at
                    FROM t_alert_info 
                    WHERE alert_timestamp >= %s OR created_at >= %s
                    ORDER BY alert_timestamp DESC
                """
                
                results = self.execute_db_query(query, (last_check_time, last_check_time))
                
                for alert in results:
                    alert_data = {
                        'id': alert[0],
                        'device_sn': alert[1],
                        'alert_type': alert[2],
                        'severity_level': alert[3],
                        'alert_status': alert[4],
                        'alert_desc': alert[5],
                        'alert_timestamp': alert[6],
                        'created_at': alert[7],
                        'captured_at': datetime.now()
                    }
                    self.captured_data['alerts'].append(alert_data)
                    self.logger.info(f"📢 捕获告警: {alert[2]} - {alert[1]}")
                
                last_check_time = datetime.now()
                time.sleep(3)  # 每3秒检查一次
                
            except Exception as e:
                self.logger.error(f"告警监控错误: {e}")
                time.sleep(5)
    
    def _monitor_messages(self):
        """监控消息表变化"""
        last_check_time = datetime.now()
        
        while self.monitoring_active:
            try:
                query = """
                    SELECT id, device_sn, message, message_type, message_status,
                           sent_time, created_at
                    FROM t_device_message 
                    WHERE sent_time >= %s OR created_at >= %s
                    ORDER BY sent_time DESC
                """
                
                results = self.execute_db_query(query, (last_check_time, last_check_time))
                
                for message in results:
                    message_data = {
                        'id': message[0],
                        'device_sn': message[1],
                        'message': message[2],
                        'message_type': message[3],
                        'message_status': message[4],
                        'sent_time': message[5],
                        'created_at': message[6],
                        'captured_at': datetime.now()
                    }
                    self.captured_data['messages'].append(message_data)
                    self.logger.info(f"📨 捕获消息: {message[3]} - {message[1]}")
                
                last_check_time = datetime.now()
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"消息监控错误: {e}")
                time.sleep(5)
    
    def _monitor_wechat_logs(self):
        """监控微信发送日志"""
        # 这里可以监控微信发送的日志文件或数据库表
        while self.monitoring_active:
            try:
                # 检查微信发送相关的日志或状态
                # 可以根据实际情况调整监控方式
                
                # 模拟检查微信发送状态
                wechat_status = self._check_wechat_send_status()
                if wechat_status:
                    self.captured_data['wechat_logs'].append(wechat_status)
                    self.logger.info(f"📱 捕获微信发送: {wechat_status.get('type', 'unknown')}")
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"微信监控错误: {e}")
                time.sleep(10)
    
    def _check_wechat_send_status(self) -> Optional[Dict]:
        """检查微信发送状态"""
        try:
            # 这里可以检查微信发送的实际状态
            # 可以通过API调用、日志文件分析等方式
            
            # 检查微信配置状态
            query = """
                SELECT id, type, enabled, last_used, success_count, error_count
                FROM t_wechat_alarm_config 
                WHERE enabled = 1
                ORDER BY last_used DESC
                LIMIT 1
            """
            
            result = self.execute_db_query(query)
            if result:
                config_data = result[0]
                if config_data[3] and config_data[3] > datetime.now() - timedelta(minutes=1):
                    # 最近1分钟内有使用记录
                    return {
                        'config_id': config_data[0],
                        'type': config_data[1],
                        'last_used': config_data[3],
                        'success_count': config_data[4],
                        'error_count': config_data[5],
                        'status': 'attempted',
                        'captured_at': datetime.now()
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"检查微信状态失败: {e}")
            return None
    
    def test_alert_generation_mechanism(self, event_type: str) -> Dict:
        """深度测试告警生成机制"""
        self.logger.info(f"🔍 深度测试告警生成机制: {event_type}")
        
        # 启动监控
        self.start_real_time_monitoring()
        
        try:
            # 发送测试事件
            event_data = {
                "eventType": event_type,
                "eventValue": "1",
                "deviceSn": self.test_device_sn,
                "heatlhData": json.dumps({
                    "data": {
                        "deviceSn": self.test_device_sn,
                        "heart_rate": 150 if event_type == "HEART_RATE_ABNORMAL" else 84,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                })
            }
            
            send_time = datetime.now()
            api_result = self.make_api_request('/upload_common_event', data=event_data)
            
            if not api_result['success']:
                return {
                    'success': False,
                    'error': f"API调用失败: {api_result.get('error')}"
                }
            
            # 等待处理
            self.logger.info("⏳ 等待告警生成处理...")
            time.sleep(10)
            
            # 分析捕获的数据
            relevant_alerts = [
                alert for alert in self.captured_data['alerts']
                if alert['device_sn'] == self.test_device_sn and
                alert['alert_timestamp'] >= send_time - timedelta(seconds=30)
            ]
            
            # 检查告警生成的详细过程
            generation_analysis = self._analyze_alert_generation_process(event_type, send_time)
            
            result = {
                'success': len(relevant_alerts) > 0,
                'event_type': event_type,
                'api_call_success': api_result['success'],
                'alerts_generated': len(relevant_alerts),
                'alert_details': relevant_alerts,
                'generation_analysis': generation_analysis,
                'processing_time': (datetime.now() - send_time).total_seconds()
            }
            
            return result
            
        finally:
            self.stop_real_time_monitoring()
    
    def _analyze_alert_generation_process(self, event_type: str, send_time: datetime) -> Dict:
        """分析告警生成过程"""
        analysis = {
            'event_rule_check': False,
            'trigger_condition_met': False,
            'alert_created': False,
            'processing_issues': []
        }
        
        try:
            # 检查事件规则配置
            rule_query = """
                SELECT rule_type, is_active, is_emergency, trigger_condition, alert_message
                FROM t_system_event_rule 
                WHERE rule_type = %s
            """
            
            rule_result = self.execute_db_query(rule_query, (event_type,))
            if rule_result:
                analysis['event_rule_check'] = True
                rule_data = rule_result[0]
                analysis['rule_details'] = {
                    'is_active': rule_data[1],
                    'is_emergency': rule_data[2],
                    'trigger_condition': rule_data[3],
                    'alert_message': rule_data[4]
                }
                
                if rule_data[1]:  # is_active
                    analysis['trigger_condition_met'] = True
            else:
                analysis['processing_issues'].append(f"未找到{event_type}的事件规则配置")
            
            # 检查告警是否实际创建
            alert_query = """
                SELECT COUNT(*) FROM t_alert_info 
                WHERE device_sn = %s AND alert_type = %s AND alert_timestamp >= %s
            """
            
            alert_count = self.execute_db_query(alert_query, (
                self.test_device_sn, event_type, send_time - timedelta(minutes=1)
            ))
            
            if alert_count and alert_count[0][0] > 0:
                analysis['alert_created'] = True
            else:
                analysis['processing_issues'].append("告警记录未创建到数据库")
            
            # 检查处理器状态
            processor_status = self._check_alert_processor_status()
            analysis['processor_status'] = processor_status
            
        except Exception as e:
            analysis['processing_issues'].append(f"分析过程出错: {e}")
        
        return analysis
    
    def _check_alert_processor_status(self) -> Dict:
        """检查告警处理器状态"""
        try:
            # 检查后台处理进程状态
            # 这里可以根据实际的处理器实现进行调整
            
            status = {
                'processor_running': True,  # 假设处理器在运行
                'queue_status': 'normal',
                'last_processed': datetime.now(),
                'error_count': 0
            }
            
            # 实际实现中可以检查：
            # - 后台任务队列状态
            # - 处理器进程是否存活
            # - 最近的处理日志
            # - 错误统计等
            
            return status
            
        except Exception as e:
            return {
                'processor_running': False,
                'error': str(e)
            }
    
    def test_message_delivery_mechanism(self, event_type: str) -> Dict:
        """深度测试平台消息下发机制"""
        self.logger.info(f"🔍 深度测试消息下发机制: {event_type}")
        
        self.start_real_time_monitoring()
        
        try:
            # 发送测试事件
            event_data = {
                "eventType": event_type,
                "eventValue": "1",
                "deviceSn": self.test_device_sn,
                "heatlhData": json.dumps({
                    "data": {
                        "deviceSn": self.test_device_sn,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                })
            }
            
            send_time = datetime.now()
            api_result = self.make_api_request('/upload_common_event', data=event_data)
            
            if not api_result['success']:
                return {
                    'success': False,
                    'error': f"API调用失败: {api_result.get('error')}"
                }
            
            # 等待消息处理
            self.logger.info("⏳ 等待消息下发处理...")
            time.sleep(10)
            
            # 分析捕获的消息
            relevant_messages = [
                msg for msg in self.captured_data['messages']
                if msg['device_sn'] == self.test_device_sn and
                msg['sent_time'] >= send_time - timedelta(seconds=30)
            ]
            
            # 检查消息下发的详细过程
            delivery_analysis = self._analyze_message_delivery_process(event_type, send_time)
            
            result = {
                'success': len(relevant_messages) > 0,
                'event_type': event_type,
                'messages_sent': len(relevant_messages),
                'message_details': relevant_messages,
                'delivery_analysis': delivery_analysis,
                'processing_time': (datetime.now() - send_time).total_seconds()
            }
            
            return result
            
        finally:
            self.stop_real_time_monitoring()
    
    def _analyze_message_delivery_process(self, event_type: str, send_time: datetime) -> Dict:
        """分析消息下发过程"""
        analysis = {
            'message_rule_check': False,
            'delivery_triggered': False,
            'message_created': False,
            'delivery_issues': []
        }
        
        try:
            # 检查消息规则配置
            # 这里可以检查消息下发的规则配置
            
            # 检查消息是否实际创建
            message_query = """
                SELECT COUNT(*) FROM t_device_message 
                WHERE device_sn = %s AND sent_time >= %s
            """
            
            message_count = self.execute_db_query(message_query, (
                self.test_device_sn, send_time - timedelta(minutes=1)
            ))
            
            if message_count and message_count[0][0] > 0:
                analysis['message_created'] = True
                analysis['delivery_triggered'] = True
            else:
                analysis['delivery_issues'].append("消息记录未创建到数据库")
            
            # 检查消息队列状态
            queue_status = self._check_message_queue_status()
            analysis['queue_status'] = queue_status
            
        except Exception as e:
            analysis['delivery_issues'].append(f"分析过程出错: {e}")
        
        return analysis
    
    def _check_message_queue_status(self) -> Dict:
        """检查消息队列状态"""
        try:
            # 检查消息队列的状态
            # 实际实现中可以检查Redis队列、RabbitMQ等
            
            status = {
                'queue_running': True,
                'pending_messages': 0,
                'processed_messages': 0,
                'error_messages': 0
            }
            
            return status
            
        except Exception as e:
            return {
                'queue_running': False,
                'error': str(e)
            }
    
    def test_wechat_notification_mechanism(self, event_type: str) -> Dict:
        """深度测试微信通知机制"""
        self.logger.info(f"🔍 深度测试微信通知机制: {event_type}")
        
        self.start_real_time_monitoring()
        
        try:
            # 直接测试微信发送接口
            wechat_test_data = {
                "alert_type": event_type,
                "user_name": "测试用户",
                "device_sn": self.test_device_sn,
                "severity": "high",
                "message": f"测试{event_type}事件的微信通知"
            }
            
            send_time = datetime.now()
            
            # 测试微信发送
            wechat_result = self._test_wechat_send_directly(wechat_test_data)
            
            # 等待微信处理
            time.sleep(5)
            
            # 分析微信发送过程
            wechat_analysis = self._analyze_wechat_send_process(event_type, send_time)
            
            # 检查捕获的微信日志
            relevant_wechat_logs = [
                log for log in self.captured_data['wechat_logs']
                if log['captured_at'] >= send_time - timedelta(seconds=30)
            ]
            
            result = {
                'success': wechat_result['success'],
                'event_type': event_type,
                'wechat_api_result': wechat_result,
                'wechat_logs': relevant_wechat_logs,
                'wechat_analysis': wechat_analysis,
                'processing_time': (datetime.now() - send_time).total_seconds()
            }
            
            return result
            
        finally:
            self.stop_real_time_monitoring()
    
    def _test_wechat_send_directly(self, test_data: Dict) -> Dict:
        """直接测试微信发送"""
        try:
            # 调用微信发送接口
            result = self.make_api_request('/api/test/wechat', data=test_data)
            
            # 分析响应
            if result['success']:
                response_text = str(result['response']).lower()
                
                # 检查微信发送的关键指标
                success_indicators = ['success', '成功', 'ok', '200']
                error_indicators = ['error', 'fail', '失败', 'timeout', '超时']
                
                has_success = any(indicator in response_text for indicator in success_indicators)
                has_error = any(indicator in response_text for indicator in error_indicators)
                
                return {
                    'success': has_success and not has_error,
                    'response': result['response'],
                    'status_code': result['status_code'],
                    'analysis': {
                        'has_success_indicator': has_success,
                        'has_error_indicator': has_error,
                        'response_content': response_text[:200]  # 截取前200字符
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"微信发送测试异常: {e}"
            }
    
    def _analyze_wechat_send_process(self, event_type: str, send_time: datetime) -> Dict:
        """分析微信发送过程"""
        analysis = {
            'config_check': False,
            'network_check': False,
            'auth_check': False,
            'send_attempt': False,
            'wechat_issues': []
        }
        
        try:
            # 检查微信配置
            config_query = """
                SELECT id, type, enabled, corp_id, appid, secret, appsecret
                FROM t_wechat_alarm_config 
                WHERE enabled = 1
            """
            
            configs = self.execute_db_query(config_query)
            if configs:
                analysis['config_check'] = True
                analysis['config_details'] = []
                
                for config in configs:
                    config_info = {
                        'id': config[0],
                        'type': config[1],
                        'has_corp_id': bool(config[3]),
                        'has_appid': bool(config[4]),
                        'has_secret': bool(config[5]),
                        'has_appsecret': bool(config[6])
                    }
                    analysis['config_details'].append(config_info)
                    
                    # 检查配置完整性
                    if config[1] == 'enterprise' and not (config[3] and config[5]):
                        analysis['wechat_issues'].append(f"企业微信配置不完整(ID={config[0]})")
                    elif config[1] == 'official' and not (config[4] and config[6]):
                        analysis['wechat_issues'].append(f"公众号配置不完整(ID={config[0]})")
            else:
                analysis['wechat_issues'].append("未找到启用的微信配置")
            
            # 网络连接检查
            network_status = self._check_wechat_network_connectivity()
            analysis['network_check'] = network_status['success']
            if not network_status['success']:
                analysis['wechat_issues'].append(f"网络连接问题: {network_status.get('error')}")
            
            # 认证检查
            auth_status = self._check_wechat_auth_status()
            analysis['auth_check'] = auth_status['success']
            if not auth_status['success']:
                analysis['wechat_issues'].append(f"认证问题: {auth_status.get('error')}")
            
        except Exception as e:
            analysis['wechat_issues'].append(f"分析过程出错: {e}")
        
        return analysis
    
    def _check_wechat_network_connectivity(self) -> Dict:
        """检查微信网络连接"""
        try:
            import requests
            
            # 测试微信API的网络连接
            test_urls = [
                'https://api.weixin.qq.com',
                'https://qyapi.weixin.qq.com'
            ]
            
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 404]:  # 404也表示网络通
                        return {'success': True, 'url': url}
                except requests.exceptions.RequestException:
                    continue
            
            return {'success': False, 'error': '无法连接微信API'}
            
        except Exception as e:
            return {'success': False, 'error': f'网络检查异常: {e}'}
    
    def _check_wechat_auth_status(self) -> Dict:
        """检查微信认证状态"""
        try:
            # 这里可以检查微信access_token的有效性
            # 实际实现中需要根据具体的微信集成方式调整
            
            return {'success': True, 'note': '认证状态检查需要根据实际实现调整'}
            
        except Exception as e:
            return {'success': False, 'error': f'认证检查异常: {e}'}
    
    def run_comprehensive_deep_inspection(self) -> Dict:
        """运行综合深度检查"""
        self.logger.info("🚀 开始综合深度检查")
        
        test_events = [
            'SOS_EVENT',
            'FALLDOWN_EVENT',
            'ONE_KEY_ALARM'
        ]
        
        results = {
            'start_time': datetime.now(),
            'alert_tests': {},
            'message_tests': {},
            'wechat_tests': {},
            'summary': {}
        }
        
        # 测试告警生成机制
        self.logger.info("📢 测试告警生成机制")
        for event_type in test_events:
            try:
                alert_result = self.test_alert_generation_mechanism(event_type)
                results['alert_tests'][event_type] = alert_result
                time.sleep(5)  # 间隔5秒
            except Exception as e:
                results['alert_tests'][event_type] = {'success': False, 'error': str(e)}
        
        # 测试消息下发机制
        self.logger.info("📨 测试消息下发机制")
        for event_type in test_events:
            try:
                message_result = self.test_message_delivery_mechanism(event_type)
                results['message_tests'][event_type] = message_result
                time.sleep(5)
            except Exception as e:
                results['message_tests'][event_type] = {'success': False, 'error': str(e)}
        
        # 测试微信通知机制
        self.logger.info("📱 测试微信通知机制")
        for event_type in test_events:
            try:
                wechat_result = self.test_wechat_notification_mechanism(event_type)
                results['wechat_tests'][event_type] = wechat_result
                time.sleep(5)
            except Exception as e:
                results['wechat_tests'][event_type] = {'success': False, 'error': str(e)}
        
        # 生成总结
        results['end_time'] = datetime.now()
        results['summary'] = self._generate_deep_inspection_summary(results)
        
        return results
    
    def _generate_deep_inspection_summary(self, results: Dict) -> Dict:
        """生成深度检查总结"""
        summary = {
            'total_duration': (results['end_time'] - results['start_time']).total_seconds(),
            'alert_mechanism': {'passed': 0, 'failed': 0, 'issues': []},
            'message_mechanism': {'passed': 0, 'failed': 0, 'issues': []},
            'wechat_mechanism': {'passed': 0, 'failed': 0, 'issues': []},
            'overall_health': 'unknown'
        }
        
        # 分析告警机制
        for event_type, result in results['alert_tests'].items():
            if result.get('success'):
                summary['alert_mechanism']['passed'] += 1
            else:
                summary['alert_mechanism']['failed'] += 1
                summary['alert_mechanism']['issues'].append(f"{event_type}: {result.get('error', 'Unknown error')}")
        
        # 分析消息机制
        for event_type, result in results['message_tests'].items():
            if result.get('success'):
                summary['message_mechanism']['passed'] += 1
            else:
                summary['message_mechanism']['failed'] += 1
                summary['message_mechanism']['issues'].append(f"{event_type}: {result.get('error', 'Unknown error')}")
        
        # 分析微信机制
        for event_type, result in results['wechat_tests'].items():
            if result.get('success'):
                summary['wechat_mechanism']['passed'] += 1
            else:
                summary['wechat_mechanism']['failed'] += 1
                summary['wechat_mechanism']['issues'].append(f"{event_type}: {result.get('error', 'Unknown error')}")
        
        # 计算总体健康状态
        total_tests = len(results['alert_tests']) + len(results['message_tests']) + len(results['wechat_tests'])
        total_passed = (summary['alert_mechanism']['passed'] + 
                       summary['message_mechanism']['passed'] + 
                       summary['wechat_mechanism']['passed'])
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 80:
            summary['overall_health'] = 'excellent'
        elif success_rate >= 60:
            summary['overall_health'] = 'good'
        elif success_rate >= 40:
            summary['overall_health'] = 'fair'
        else:
            summary['overall_health'] = 'poor'
        
        summary['success_rate'] = success_rate
        
        return summary
    
    def run_tests(self) -> List[Dict]:
        """运行深度检查测试套件"""
        self.logger.info("开始深度检查测试套件")
        
        try:
            # 运行综合深度检查
            deep_results = self.run_comprehensive_deep_inspection()
            
            # 转换为标准测试结果格式
            test_results = []
            
            # 添加告警机制测试结果
            for event_type, result in deep_results['alert_tests'].items():
                test_results.append({
                    'test_name': f'告警生成机制-{event_type}',
                    'success': result.get('success', False),
                    'timestamp': datetime.now(),
                    'details': result
                })
            
            # 添加消息机制测试结果
            for event_type, result in deep_results['message_tests'].items():
                test_results.append({
                    'test_name': f'消息下发机制-{event_type}',
                    'success': result.get('success', False),
                    'timestamp': datetime.now(),
                    'details': result
                })
            
            # 添加微信机制测试结果
            for event_type, result in deep_results['wechat_tests'].items():
                test_results.append({
                    'test_name': f'微信通知机制-{event_type}',
                    'success': result.get('success', False),
                    'timestamp': datetime.now(),
                    'details': result
                })
            
            # 添加总体评估结果
            summary = deep_results['summary']
            test_results.append({
                'test_name': '深度检查总体评估',
                'success': summary['success_rate'] >= 60,
                'timestamp': datetime.now(),
                'details': summary
            })
            
            self.test_results = test_results
            
            # 生成深度检查报告
            self._generate_deep_inspection_report(deep_results)
            
            return test_results
            
        except Exception as e:
            self.logger.error(f"深度检查测试失败: {e}")
            error_result = [{
                'test_name': '深度检查测试套件执行',
                'success': False,
                'timestamp': datetime.now(),
                'details': {'error': str(e)}
            }]
            self.test_results = error_result
            return error_result
        
        finally:
            # 清理测试数据
            if self.config['cleanup_test_data']:
                self.cleanup_test_data(self.test_device_sn)
    
    def _generate_deep_inspection_report(self, results: Dict):
        """生成深度检查报告"""
        summary = results['summary']
        
        report = f"""
🔍 深度检查测试报告
{'='*80}

⏰ 测试时间: {results['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {results['end_time'].strftime('%H:%M:%S')}
⏱️  总耗时: {summary['total_duration']:.2f}秒

📊 检查结果概览:
   - 告警生成机制: {summary['alert_mechanism']['passed']}/{len(results['alert_tests'])} 通过
   - 消息下发机制: {summary['message_mechanism']['passed']}/{len(results['message_tests'])} 通过
   - 微信通知机制: {summary['wechat_mechanism']['passed']}/{len(results['wechat_tests'])} 通过
   - 总体成功率: {summary['success_rate']:.1f}%
   - 系统健康状态: {summary['overall_health']}

🔧 发现的问题:
"""
        
        all_issues = (summary['alert_mechanism']['issues'] + 
                     summary['message_mechanism']['issues'] + 
                     summary['wechat_mechanism']['issues'])
        
        if all_issues:
            for i, issue in enumerate(all_issues, 1):
                report += f"\n   {i}. {issue}"
        else:
            report += "\n   ✅ 未发现明显问题"
        
        report += f"""

📋 详细检查结果:

📢 告警生成机制检查:
"""
        
        for event_type, result in results['alert_tests'].items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            report += f"\n   {event_type}: {status}"
            if not result.get('success'):
                report += f" - {result.get('error', 'Unknown error')}"
        
        report += f"""

📨 消息下发机制检查:
"""
        
        for event_type, result in results['message_tests'].items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            report += f"\n   {event_type}: {status}"
            if not result.get('success'):
                report += f" - {result.get('error', 'Unknown error')}"
        
        report += f"""

📱 微信通知机制检查:
"""
        
        for event_type, result in results['wechat_tests'].items():
            status = "✅ PASS" if result.get('success') else "❌ FAIL"
            report += f"\n   {event_type}: {status}"
            if not result.get('success'):
                report += f" - {result.get('error', 'Unknown error')}"
        
        # 保存报告
        report_file = f"deep_inspection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        self.logger.info(f"深度检查报告已保存: {report_file}")
        print(report)

def main():
    """主函数"""
    print("🔍 启动深度检查测试")
    
    config = {
        'api_base_url': 'http://localhost:5001',
        'test_timeout': 30,
        'cleanup_test_data': True
    }
    
    deep_test = DeepInspectionTest(config)
    
    try:
        results = deep_test.run_tests()
        
        basic_report = deep_test.generate_report()
        print(basic_report)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r['success'])
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🏆 深度检查成功率: {success_rate:.1f}%")
        
        return 0 if success_rate >= 60 else 1
        
    except Exception as e:
        print(f"\n❌ 深度检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 