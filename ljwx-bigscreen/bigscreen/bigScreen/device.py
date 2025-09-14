from flask import request, jsonify
from datetime import datetime, timedelta
import re
import json
import time
import pytz  # 添加时区处理支持
from typing import List, Dict, Optional, Tuple
from .redis_helper import RedisHelper
from .models import db, DeviceInfo, UserInfo, CustomerConfig, UserOrg, OrgInfo, DeviceInfoHistory, Interface
from .device_batch_processor import get_batch_processor
import logging

logger = logging.getLogger(__name__)
redis = RedisHelper()

def get_all_device_data_optimized(orgId=None, userId=None, startDate=None, endDate=None, latest_only=False, page=1, pageSize=None, include_alerts=False):
    """
    统一的设备数据查询接口，支持分页和优化查询
    
    Args:
        orgId: 组织ID
        userId: 用户ID  
        startDate: 开始日期
        endDate: 结束日期
        latest_only: 是否只查询最新记录
        page: 页码
        pageSize: 每页大小
        include_alerts: 是否包含告警信息
    
    Returns:
        dict: 包含设备数据和分页信息的字典
    """
    try:
        import time
        from datetime import datetime, timedelta
        start_time = time.time()
        
        # 参数验证和缓存键构建
        page = max(1, int(page or 1))
        if pageSize is not None:
            pageSize = min(int(pageSize), 1000)
        else:
            pageSize = None
        mode = 'latest' if latest_only else 'range'
        cache_key = f"device_opt_v1:{orgId}:{userId}:{startDate}:{endDate}:{mode}:{page}:{pageSize}:{include_alerts}"
        
        # 缓存检查
        cached = redis.get_data(cache_key)
        if cached:
            result = json.loads(cached)
            result['performance'] = {'cached': True, 'response_time': round(time.time() - start_time, 3)}
            return result
        
        # 构建查询条件
        query = db.session.query(DeviceInfo).filter(DeviceInfo.is_deleted == False)
        
        if userId:
            # 单用户查询
            query = query.filter(DeviceInfo.user_id == userId)
            
        elif orgId:
            # 组织查询 - 获取组织下所有用户的设备
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(orgId)
            if not users:
                return {"success": True, "data": {"deviceData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
            
            user_ids = [int(user['id']) for user in users]
            query = query.filter(DeviceInfo.user_id.in_(user_ids))
            
        else:
            return {"success": False, "message": "缺少orgId或userId参数", "data": {"deviceData": [], "totalRecords": 0}}
        
        # 时间范围过滤
        if startDate:
            query = query.filter(DeviceInfo.update_time >= startDate)
        if endDate:
            query = query.filter(DeviceInfo.update_time <= endDate)
        
        # 统计总数
        total_count = query.count()
        
        # 排序
        query = query.order_by(DeviceInfo.update_time.desc())
        
        # 分页处理
        if pageSize is not None:
            offset = (page - 1) * pageSize
            query = query.offset(offset).limit(pageSize)
        
        if latest_only and not pageSize:
            query = query.limit(1)
        
        # 执行查询
        devices = query.all()
        
        # 格式化数据
        device_data_list = []
        for device in devices:
            # 获取用户信息（从sys_user表直接获取org_id和org_name，避免关联查询）
            user_info = UserInfo.query.filter_by(id=device.user_id).first() if device.user_id else None
            
            device_dict = {
                'id': device.id,
                'serial_number': device.serial_number,
                'device_name': device.device_name,
                'imei': device.imei,
                'battery_level': device.battery_level,
                'charging_status': device.charging_status,
                'wearable_status': device.wearable_status,
                'status': device.status,
                'update_time': device.update_time.strftime('%Y-%m-%d %H:%M:%S') if device.update_time else None,
                'voltage': device.voltage,
                'system_software_version': device.system_software_version,
                'wifi_address': device.wifi_address,
                'bluetooth_address': device.bluetooth_address,
                'ip_address': device.ip_address,
                'network_access_mode': device.network_access_mode,
                'customer_id': device.customer_id,
                'user_id': device.user_id,
                'org_id': user_info.org_id if user_info else device.org_id,  # 优先从sys_user获取
                'org_name': user_info.org_name if (user_info and hasattr(user_info, 'org_name')) else None,  # 从sys_user获取org_name
                'user_name': user_info.user_name if user_info else None
            }
            
            # 如果需要包含告警信息
            if include_alerts:
                device_dict['alerts'] = []  # 可以在此处添加设备相关告警
            
            device_data_list.append(device_dict)
        
        # 构建分页信息
        pagination = {
            'currentPage': page,
            'pageSize': pageSize,
            'totalCount': total_count,
            'totalPages': (total_count + pageSize - 1) // pageSize if pageSize else 1
        }
        
        # 构建结果
        result = {
            'success': True,
            'data': {
                'deviceData': device_data_list,
                'totalRecords': len(device_data_list),
                'pagination': pagination
            },
            'performance': {
                'cached': False,
                'response_time': round(time.time() - start_time, 3),
                'query_time': round(time.time() - start_time, 3)
            }
        }
        
        # 缓存结果
        redis.set_data(cache_key, json.dumps(result, default=str), 300)
        
        return result
        
    except Exception as e:
        logger.error(f"设备查询失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {'deviceData': [], 'totalRecords': 0}
        }

class DeviceService:
    """设备管理统一服务封装类 - 基于userId的查询和汇总"""
    
    def __init__(self):
        self.redis = redis
    
    def get_devices_by_common_params(self, customer_id: int = None, org_id: int = None, 
                                   user_id: int = None, start_date: str = None, 
                                   end_date: str = None, page: int = 1, 
                                   page_size: int = None, include_alerts: bool = False) -> Dict:
        """
        基于统一参数获取设备信息 - 整合现有get_all_device_data_optimized接口
        
        Args:
            customer_id: 客户ID (映射到orgId)
            org_id: 组织ID
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页大小
            include_alerts: 是否包含告警信息
            
        Returns:
            设备信息字典
        """
        try:
            # 参数映射和优先级处理
            if user_id:
                result = get_all_device_data_optimized(
                    orgId=None,
                    userId=user_id, 
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=False,
                    page=page,
                    pageSize=page_size,
                    include_alerts=include_alerts
                )
                logger.info(f"基于userId查询设备数据: user_id={user_id}")
                
            elif org_id:
                # 组织查询 - 获取组织下所有用户的设备
                result = get_all_device_data_optimized(
                    orgId=org_id,
                    userId=None,
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=False,
                    page=page,
                    pageSize=page_size,
                    include_alerts=include_alerts
                )
                logger.info(f"基于orgId查询设备数据: org_id={org_id}")
                
            elif customer_id:
                # 客户查询 - 将customer_id作为orgId处理
                result = get_all_device_data_optimized(
                    orgId=customer_id,
                    userId=None,
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=False,
                    page=page,
                    pageSize=page_size,
                    include_alerts=include_alerts
                )
                logger.info(f"基于customerId查询设备数据: customer_id={customer_id}")
                
            else:
                return {
                    'success': False,
                    'error': 'Missing required parameters: customer_id, org_id, or user_id',
                    'data': {'devices': [], 'total_count': 0}
                }
            
            # 统一返回格式，兼容新的服务接口
            if result.get('success', True):
                device_data = result.get('data', {}).get('deviceData', [])
                
                unified_result = {
                    'success': True,
                    'data': {
                        'devices': device_data,
                        'total_count': result.get('data', {}).get('totalRecords', len(device_data)),
                        'pagination': result.get('data', {}).get('pagination', {}),
                        'query_params': {
                            'customer_id': customer_id,
                            'org_id': org_id,
                            'user_id': user_id,
                            'start_date': start_date,
                            'end_date': end_date,
                            'page': page,
                            'page_size': page_size,
                            'include_alerts': include_alerts
                        }
                    },
                    'performance': result.get('performance', {}),
                    'from_cache': result.get('performance', {}).get('cached', False)
                }
                
                return unified_result
            else:
                return result
                
        except Exception as e:
            logger.error(f"设备查询失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'devices': [], 'total_count': 0}
            }
    
    def _get_devices_by_user_id(self, user_id: int, start_date: str = None, 
                               end_date: str = None) -> List[Dict]:
        """基于用户ID查询设备"""
        try:
            # 查询用户信息和设备信息
            query = db.session.query(
                DeviceInfo, UserInfo, OrgInfo
            ).join(
                UserInfo, DeviceInfo.user_id == UserInfo.id
            ).join(
                UserOrg, UserInfo.id == UserOrg.user_id
            ).join(
                OrgInfo, UserOrg.org_id == OrgInfo.id
            ).filter(
                DeviceInfo.user_id == user_id,
                DeviceInfo.is_deleted == False,
                UserInfo.is_deleted == False
            )
            
            # 时间范围过滤
            if start_date:
                query = query.filter(DeviceInfo.update_time >= start_date)
            if end_date:
                query = query.filter(DeviceInfo.update_time <= end_date)
            
            results = query.all()
            
            devices = []
            for device_info, user_info, org_info in results:
                devices.append(self._format_device_data(device_info, user_info, org_info))
            
            return devices
            
        except Exception as e:
            logger.error(f"基于用户ID查询设备失败: {e}")
            return []
    
    def _get_devices_by_org_id(self, org_id: int, customer_id: int = None,
                              start_date: str = None, end_date: str = None) -> List[Dict]:
        """基于组织ID查询设备"""
        try:
            # 获取组织下所有用户
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(org_id, customer_id)
            
            if not users:
                return []
            
            user_ids = [int(user['id']) for user in users]
            
            # 查询这些用户的设备
            query = db.session.query(
                DeviceInfo, UserInfo, OrgInfo
            ).join(
                UserInfo, DeviceInfo.user_id == UserInfo.id
            ).join(
                UserOrg, UserInfo.id == UserOrg.user_id
            ).join(
                OrgInfo, UserOrg.org_id == OrgInfo.id
            ).filter(
                DeviceInfo.user_id.in_(user_ids),
                DeviceInfo.is_deleted == False,
                UserInfo.is_deleted == False
            )
            
            # 时间范围过滤
            if start_date:
                query = query.filter(DeviceInfo.update_time >= start_date)
            if end_date:
                query = query.filter(DeviceInfo.update_time <= end_date)
            
            results = query.all()
            
            devices = []
            for device_info, user_info, org_info in results:
                devices.append(self._format_device_data(device_info, user_info, org_info))
            
            return devices
            
        except Exception as e:
            logger.error(f"基于组织ID查询设备失败: {e}")
            return []
    
    def _get_devices_by_customer_id(self, customer_id: int, start_date: str = None,
                                   end_date: str = None) -> List[Dict]:
        """基于客户ID查询设备"""
        try:
            query = db.session.query(
                DeviceInfo, UserInfo, OrgInfo
            ).join(
                UserInfo, DeviceInfo.user_id == UserInfo.id
            ).join(
                UserOrg, UserInfo.id == UserOrg.user_id
            ).join(
                OrgInfo, UserOrg.org_id == OrgInfo.id
            ).filter(
                DeviceInfo.customer_id == customer_id,
                DeviceInfo.is_deleted == False,
                UserInfo.is_deleted == False
            )
            
            # 时间范围过滤
            if start_date:
                query = query.filter(DeviceInfo.update_time >= start_date)
            if end_date:
                query = query.filter(DeviceInfo.update_time <= end_date)
            
            results = query.all()
            
            devices = []
            for device_info, user_info, org_info in results:
                devices.append(self._format_device_data(device_info, user_info, org_info))
            
            return devices
            
        except Exception as e:
            logger.error(f"基于客户ID查询设备失败: {e}")
            return []
    
    def _format_device_data(self, device_info: DeviceInfo, user_info: UserInfo, 
                           org_info: OrgInfo) -> Dict:
        """格式化设备数据"""
        return {
            'id': device_info.id,
            'serial_number': device_info.serial_number,
            'device_name': device_info.device_name,
            'model': device_info.model,
            'status': device_info.status,
            'battery_level': device_info.battery_level,
            'charging_status': device_info.charging_status,
            'wearable_status': device_info.wearable_status,
            'wifi_address': device_info.wifi_address,
            'bluetooth_address': device_info.bluetooth_address,
            'ip_address': device_info.ip_address,
            'update_time': device_info.update_time.strftime('%Y-%m-%d %H:%M:%S') if device_info.update_time else None,
            'customer_id': device_info.customer_id,
            'user_id': device_info.user_id,
            'org_id': device_info.org_id,
            'user_name': user_info.user_name,
            'real_name': user_info.real_name,
            'org_name': org_info.name
        }
    
    def get_device_statistics_by_common_params(self, customer_id: int = None, 
                                             org_id: int = None, user_id: int = None,
                                             start_date: str = None, end_date: str = None) -> Dict:
        """基于统一参数获取设备统计"""
        try:
            cache_key = f"device_stats_v2:{customer_id}:{org_id}:{user_id}:{start_date}:{end_date}"
            
            # 缓存检查
            cached = self.redis.get_data(cache_key)
            if cached:
                return json.loads(cached)
            
            # 获取设备数据
            devices_result = self.get_devices_by_common_params(
                customer_id, org_id, user_id, start_date, end_date
            )
            
            if not devices_result.get('success'):
                return devices_result
            
            devices = devices_result['data']['devices']
            
            # 计算统计数据
            total_devices = len(devices)
            online_devices = sum(1 for d in devices if d.get('status') == '1')
            battery_low_devices = sum(1 for d in devices if d.get('battery_level') and int(d['battery_level']) < 20)
            charging_devices = sum(1 for d in devices if d.get('charging_status') == '1')
            
            # 按组织统计
            org_stats = {}
            for device in devices:
                org_name = device.get('org_name', '未知组织')
                if org_name not in org_stats:
                    org_stats[org_name] = {
                        'total': 0,
                        'online': 0,
                        'battery_low': 0,
                        'charging': 0
                    }
                
                org_stats[org_name]['total'] += 1
                if device.get('status') == '1':
                    org_stats[org_name]['online'] += 1
                if device.get('battery_level') and int(device['battery_level']) < 20:
                    org_stats[org_name]['battery_low'] += 1
                if device.get('charging_status') == '1':
                    org_stats[org_name]['charging'] += 1
            
            result = {
                'success': True,
                'data': {
                    'overview': {
                        'total_devices': total_devices,
                        'online_devices': online_devices,
                        'offline_devices': total_devices - online_devices,
                        'battery_low_devices': battery_low_devices,
                        'charging_devices': charging_devices,
                        'online_rate': round(online_devices / total_devices * 100, 2) if total_devices > 0 else 0
                    },
                    'org_statistics': org_stats,
                    'query_params': {
                        'customer_id': customer_id,
                        'org_id': org_id,
                        'user_id': user_id,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            }
            
            # 缓存结果
            self.redis.set_data(cache_key, json.dumps(result, default=str), 180)
            
            return result
            
        except Exception as e:
            logger.error(f"设备统计计算失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'overview': {}, 'org_statistics': {}}
            }
    
    def get_device_alerts_by_common_params(self, customer_id: int = None,
                                         org_id: int = None, user_id: int = None,
                                         start_date: str = None, end_date: str = None) -> Dict:
        """基于统一参数获取设备告警信息"""
        try:
            cache_key = f"device_alerts_v2:{customer_id}:{org_id}:{user_id}:{start_date}:{end_date}"
            
            # 缓存检查
            cached = self.redis.get_data(cache_key)
            if cached:
                return json.loads(cached)
            
            # 获取设备数据
            devices_result = self.get_devices_by_common_params(
                customer_id, org_id, user_id, start_date, end_date
            )
            
            if not devices_result.get('success'):
                return devices_result
            
            devices = devices_result['data']['devices']
            
            alerts = []
            
            # 生成设备告警
            for device in devices:
                device_alerts = self._generate_device_alerts(device)
                alerts.extend(device_alerts)
            
            # 按告警级别分类
            alert_levels = {'high': 0, 'medium': 0, 'low': 0}
            for alert in alerts:
                level = alert.get('level', 'low')
                if level in alert_levels:
                    alert_levels[level] += 1
            
            result = {
                'success': True,
                'data': {
                    'alerts': alerts,
                    'total_alerts': len(alerts),
                    'alert_levels': alert_levels,
                    'query_params': {
                        'customer_id': customer_id,
                        'org_id': org_id,
                        'user_id': user_id,
                        'start_date': start_date,
                        'end_date': end_date
                    }
                }
            }
            
            # 缓存结果
            self.redis.set_data(cache_key, json.dumps(result, default=str), 120)
            
            return result
            
        except Exception as e:
            logger.error(f"设备告警查询失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'alerts': [], 'total_alerts': 0, 'alert_levels': {}}
            }
    
    def _generate_device_alerts(self, device: Dict) -> List[Dict]:
        """为单个设备生成告警"""
        alerts = []
        
        # 电池电量低告警
        if device.get('battery_level') and int(device['battery_level']) < 20:
            alerts.append({
                'type': 'battery_low',
                'level': 'high' if int(device['battery_level']) < 10 else 'medium',
                'message': f"设备 {device['device_name']} 电池电量过低: {device['battery_level']}%",
                'device_sn': device['serial_number'],
                'user_name': device['user_name'],
                'org_name': device['org_name'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 设备离线告警
        if device.get('status') != '1':
            alerts.append({
                'type': 'device_offline',
                'level': 'high',
                'message': f"设备 {device['device_name']} 离线",
                'device_sn': device['serial_number'],
                'user_name': device['user_name'],
                'org_name': device['org_name'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # 设备未佩戴告警
        if device.get('wearable_status') != '1':
            alerts.append({
                'type': 'not_wearing',
                'level': 'medium',
                'message': f"设备 {device['device_name']} 未佩戴",
                'device_sn': device['serial_number'],
                'user_name': device['user_name'],
                'org_name': device['org_name'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return alerts

# 全局实例
_device_service_instance = None

def get_unified_device_service() -> DeviceService:
    """获取统一设备服务实例"""
    global _device_service_instance
    if _device_service_instance is None:
        _device_service_instance = DeviceService()
    return _device_service_instance

# 向后兼容的函数，供现有代码使用
def get_devices_unified(customer_id: int = None, org_id: int = None, 
                       user_id: int = None, start_date: str = None, 
                       end_date: str = None, page: int = 1, 
                       page_size: int = None, include_alerts: bool = False) -> Dict:
    """统一的设备查询接口 - 整合现有get_all_device_data_optimized接口"""
    service = get_unified_device_service()
    return service.get_devices_by_common_params(
        customer_id, org_id, user_id, start_date, end_date, 
        page, page_size, include_alerts
    )

def get_device_statistics_unified(customer_id: int = None, org_id: int = None,
                                user_id: int = None, start_date: str = None,
                                end_date: str = None) -> Dict:
    """统一的设备统计接口"""
    service = get_unified_device_service()
    return service.get_device_statistics_by_common_params(customer_id, org_id, user_id, start_date, end_date)

def get_device_alerts_unified(customer_id: int = None, org_id: int = None,
                            user_id: int = None, start_date: str = None,
                            end_date: str = None) -> Dict:
    """统一的设备告警接口"""
    service = get_unified_device_service()
    return service.get_device_alerts_by_common_params(customer_id, org_id, user_id, start_date, end_date)

# 高并发设备信息上传接口 v1.0.34
def upload_device_info(device_info, app=None):
    """高并发设备信息上传 - 支持400-1000台设备同时上传，支持单个设备或设备列表"""
    print(f"📱 设备信息上传开始 - 数据类型: {type(device_info).__name__}")
    
    # 获取设备标识符用于日志记录
    def get_device_identifier(data):
        if isinstance(data, dict):
            return data.get('SerialNumber') or data.get('serial_number') or data.get('deviceSn') or 'unknown'
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return get_device_identifier(data[0])
        else:
            return 'unknown'
    
    def get_request_id(data):
        if isinstance(data, dict):
            return data.get('_request_id', 'unknown')
        elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return data[0].get('_request_id', 'unknown')
        else:
            return 'unknown'
    
    device_id = get_device_identifier(device_info)
    request_id = get_request_id(device_info)
    
    print(f"📱 设备信息上传开始 - 设备标识: {device_id}")
    
    # 对于只有一个设备的列表，我们可以选择直接处理单个设备以提高效率
    if isinstance(device_info, list) and len(device_info) == 1:
        print(f"📱 检测到单设备列表，优化为单设备处理: {device_id}")
        # 注意：这里我们仍然发送列表给批量处理器，让它处理
    
    print(f"📱 原始数据类型: {type(device_info).__name__}, 数据长度: {len(device_info) if isinstance(device_info, list) else 1}")
    
    try:
        # 快速提交到批量处理器，传递Flask应用上下文
        batch_processor = get_batch_processor(app)
        print(f"📱 批量处理器获取成功，队列状态: {batch_processor.get_queue_status() if hasattr(batch_processor, 'get_queue_status') else '未知'}")
        
        # 提交数据到批量处理队列
        success = batch_processor.submit(device_info)
        
        if success:
            print(f"📱 设备信息提交队列成功: {device_id}")
            return jsonify({
                "status": "success", 
                "message": "设备信息已接收，正在批量处理",
                "request_id": request_id
            })
        else:
            print(f"📱 队列满，降级到同步处理: {device_id}")
            # 队列满时的降级处理
            return upload_device_info_sync(device_info)
            
    except Exception as e:
        print(f"❌ 批量处理提交失败: {e}")
        print(f"❌ 异常详情: {type(e).__name__} - {str(e)}")
        import traceback
        print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
        # 异常时回退到同步处理
        return upload_device_info_sync(device_info)

# 同步处理设备信息(原有逻辑保留作为降级方案)
def upload_device_info_sync(device_info):
    """同步处理设备信息 - 降级方案，支持单个设备或设备列表"""
    
    # 提取顶级的客户信息参数
    customer_id = device_info.get("customer_id") if isinstance(device_info, dict) else None
    org_id = device_info.get("org_id") if isinstance(device_info, dict) else None
    user_id = device_info.get("user_id") if isinstance(device_info, dict) else None
    print(f"🔍 提取顶级客户信息: customer_id={customer_id}, org_id={org_id}, user_id={user_id}")
    
    # 处理单个设备的函数
    def process_single_device(single_device_info):
        """处理单个设备信息"""
        device_sn = single_device_info.get('SerialNumber') or single_device_info.get('serial_number') or single_device_info.get('deviceSn') or 'unknown'
        print(f"🔄 同步处理单个设备: {device_sn}")
        try:
            data = single_device_info.get("data", single_device_info)
            print(f"🔍 解析后的数据字段: {json.dumps(data, ensure_ascii=False, indent=2)}")
            
            system_software_version = data.get("System Software Version") or data.get("system_version")
            model = extract_model(system_software_version)
            wifi_address = data.get("Wifi Address") or data.get("wifi_address")
            bluetooth_address = data.get("Bluetooth Address") or data.get("bluetooth_address")
            ip_address = data.get("IP Address") or data.get("ip_address")
            ipv4_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', ip_address) if ip_address else None
            ip_address = ipv4_match.group(0) if ipv4_match else None
            network_access_mode = data.get("Network Access Mode") or data.get("network_mode")
            serial_number = data.get("SerialNumber") or data.get("serial_number")
            device_name = data.get("Device Name") or data.get("device_name")
            imei = data.get("IMEI") or data.get("imei")
            voltage = data.get("voltage") or 0
            wearable_status = data.get("wearState") or data.get("wear_state")
            status = data.get("status")
            timestamp = data.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 提取客户信息字段 - 优先使用顶级传递的参数，其次使用数据项中的参数
            customerId = customer_id or data.get("customer_id")
            orgId = org_id or data.get("org_id") 
            userId = user_id or data.get("user_id")
            
            print(f"🔍 解析的关键字段: serial_number={serial_number}, battery_level={data.get('batteryLevel')}, wearable_status={wearable_status}, charging_status={data.get('chargingStatus')}")
            print(f"🔍 客户信息: customerId={customerId}, orgId={orgId}, userId={userId}")
            
            if str(timestamp).isdigit() and len(str(timestamp))==13:
                # 将毫秒时间戳转换为北京时间
                beijing_tz = pytz.timezone('Asia/Shanghai')
                dt = datetime.fromtimestamp(int(timestamp)/1000, tz=beijing_tz)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            wearable_status = "WORN" if wearable_status and int(wearable_status) == 1 else "NOT_WORN"
            battery_level = normalize_battery_level(data.get("batteryLevel") or data.get("battery_level"))
            charging_status = data.get("chargingStatus") or data.get("charging_status")
            if charging_status in ["CHARGING", "ENABLE", "1", 1, True]:charging_status = "CHARGING"
            elif charging_status in ["NOT_CHARGING", "NONE", "0", 0, False]:charging_status = "NOT_CHARGING"
            else:charging_status = "UNKNOWN"
            is_deleted = 0
            
            # 如果没有直接传递用户信息，通过deviceSn查询获取（兼容旧版本）
            if not customerId or not orgId or not userId:
                print(f"🔍 客户信息不完整，通过deviceSn查询获取: customerId={customerId}, orgId={orgId}, userId={userId}")
                device_info_dict = fetch_user_info_by_deviceSn(serial_number)
                # 使用新版本返回的字典格式
                customerId = customerId or device_info_dict.get('customer_id')
                orgId = orgId or device_info_dict.get('org_id') 
                userId = userId or device_info_dict.get('user_id')
                print(f"🔍 补充后的客户信息: customerId={customerId}, orgId={orgId}, userId={userId}")

            print(f"✅ 准备保存设备信息: SN={serial_number}, 电池={battery_level}%, 佩戴状态={wearable_status}, 充电状态={charging_status}")
            save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, status, update_time, is_deleted, timestamp, voltage, customerId, orgId, userId)
            print(f"✅ 设备信息同步处理完成: {serial_number}")
            return {"status": "success", "message": f"设备 {serial_number} 信息已同步处理"}
        except Exception as e:
            print(f"❌ 同步处理设备信息失败: {device_sn} - {e}")
            import traceback
            print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
            return {"status": "error", "message": f"设备 {device_sn} 信息处理失败: {str(e)}"}
    
    # 主处理逻辑
    if isinstance(device_info, list):
        print(f"🔄 同步处理设备列表，设备数量: {len(device_info)}")
        results = []
        success_count = 0
        error_count = 0
        
        for single_device in device_info:
            result = process_single_device(single_device)
            results.append(result)
            if result["status"] == "success":
                success_count += 1
            else:
                error_count += 1
        
        print(f"📊 批量同步处理完成: 成功 {success_count}, 失败 {error_count}")
        return jsonify({
            "status": "success" if error_count == 0 else "partial_success",
            "message": f"批量处理完成: 成功 {success_count}, 失败 {error_count}",
            "results": results,
            "statistics": {
                "total": len(device_info),
                "success": success_count,
                "error": error_count
            }
        })
    else:
        # 处理单个设备
        result = process_single_device(device_info)
        if result["status"] == "success":
            return jsonify(result)
        else:
            return jsonify(result), 500

def save_device_info(system_software_version, wifi_address, bluetooth_address, ip_address, network_access_mode, serial_number, device_name, imei, battery_level, charging_status, wearable_status, status, update_time, is_deleted, timestamp, voltage, customerId=None, orgId=None, userId=None):
    print(f"💾 开始保存设备信息到数据库: SN={serial_number}")
    try:
        d=DeviceInfo.query.filter_by(serial_number=serial_number).first()# 查找设备#
        if not d:
            print(f"💾 创建新设备记录: {serial_number}")
            d=DeviceInfo(serial_number=serial_number)# 新建#
        else:
            print(f"💾 更新现有设备记录: {serial_number}")
        d.system_software_version=system_software_version;d.wifi_address=wifi_address;d.bluetooth_address=bluetooth_address;d.ip_address=ip_address;d.network_access_mode=network_access_mode;d.device_name=device_name;d.imei=imei;d.battery_level=battery_level;d.charging_status=charging_status;d.wearable_status=wearable_status;d.status=status;d.update_time=update_time;d.is_deleted=is_deleted;d.voltage=voltage;d.timestamp=timestamp;d.customer_id=customerId;d.org_id=orgId;d.user_id=userId# 字段赋值#
        db.session.add(d);db.session.commit()# 更新或插入DeviceInfo#
        print(f"✅ DeviceInfo表更新成功: {serial_number}")
        h=DeviceInfoHistory(serial_number=serial_number,system_software_version=system_software_version,ip_address=ip_address,network_access_mode=network_access_mode,battery_level=battery_level,charging_status=charging_status,wearable_status=wearable_status,status=status,update_time=update_time,is_deleted=is_deleted,voltage=voltage,timestamp=timestamp)# 新建历史#
        db.session.add(h);db.session.commit()# 插入DeviceInfoHistory#
        print(f"✅ DeviceInfoHistory表插入成功: {serial_number}")
        device_dict={k:v for k,v in d.to_dict().items() if v is not None}# 过滤None值#
        redis.hset_data(f"device_info:{serial_number}",device_dict)# 写入redis#
        print(f"✅ Redis写入成功: device_info:{serial_number}")
        redis.publish(f"device_info_channel:{serial_number}",serial_number)# 发布#
        print(f"✅ Redis发布成功: device_info_channel:{serial_number}")
    except Exception as e:
        print(f"❌ 数据库操作失败: {e}")
        import traceback
        print(f"❌ 完整异常堆栈: {traceback.format_exc()}")
        raise e  # 重新抛出异常让上层处理
    finally:
        print(f"💾 设备信息保存操作完成: {serial_number}")#

def normalize_battery_level(battery_level):
    if battery_level is None:
        return None
    try:
        # 统一转为字符串再处理
        value = str(battery_level).strip().replace('%', '')
        return int(value)
    except (ValueError, TypeError):
        return None
def extract_model(system_software_version):
    if not system_software_version:return None  # 处理None或空值#
    match = re.match(r"([A-Z]+-[A-Z]+\d+)", system_software_version)
    return match.group(1) if match else None  # 简化返回逻辑#

def fetch_device_info(serial_number):
    # Try to fetch from Redis
    device_info = redis.hgetall_data(f"device_info:{serial_number}")
    print("device_info in redis:", device_info)
    if device_info:
        print("Fetched from Redis")
        return device_info

    # If not found in Redis, fetch from MySQL
    device_info = DeviceInfo.query.filter_by(serial_number=serial_number).order_by(
                DeviceInfo.timestamp.desc()  # 按时间倒序排序
            ).first()
    print("device_info:", device_info)
    if device_info:
        print("Fetched from MySQL")
           # Delete existing data in Redis
        # Optionally, store the fetched data back to Redis for future requests
        redis.hset(f"device_info:{serial_number}", mapping=device_info.to_dict())
        return device_info.to_dict()

    # If not found in both, return None or an appropriate message
    print("Device info not found")
    return None

def fetch_user_info_by_deviceSn(deviceSn):
    """根据设备序列号获取完整的用户信息(customer_id, org_id, user_id)"""
    try:
        result = (
            db.session.query(UserInfo, UserOrg, OrgInfo)
            .select_from(UserInfo)
            .join(
                UserOrg,
                (UserInfo.id == UserOrg.user_id) & (UserOrg.is_deleted.is_(False))
            )
            .join(
                OrgInfo,
                (UserOrg.org_id == OrgInfo.id) & (OrgInfo.is_deleted.is_(False))
            )
            .filter(
                UserInfo.device_sn == deviceSn,
                UserInfo.is_deleted.is_(False)
            )
            .first()
        )
        
        print("fetch_user_info_by_deviceSn:result:", result)

        if not result:
            return {
                'customer_id': '0',
                'org_id': None,
                'user_id': None
            }

        user_info, user_org, org_info = result
        
        # 获取用户ID和直属组织ID
        user_id = user_info.id
        org_id = user_org.org_id
        
        # 处理祖先组织获取customer_id
        customer_id = str(org_info.id)  # 默认使用当前组织ID
        
        if org_info.ancestors:
            # 分割并查找第一个非零值作为customer_id
            ancestor_ids = org_info.ancestors.split(',')
            for ancestor_id in ancestor_ids:
                if ancestor_id and ancestor_id != '0':
                    customer_id = str(ancestor_id)
                    break
        
        return {
            'customer_id': customer_id,
            'org_id': org_id,
            'user_id': user_id
        }

    except Exception as e:
        print(f"Error in fetch_user_info_by_deviceSn: {e}")
        return {
            'customer_id': '0',
            'org_id': None,
            'user_id': None
        }

def fetch_customer_id_by_deviceSn(deviceSn):
    """根据设备序列号获取客户ID"""
    try:
        user_info = fetch_user_info_by_deviceSn(deviceSn)
        return user_info.get('customer_id', '0')
    except Exception as e:
        print(f"Error in fetch_customer_id_by_deviceSn: {e}")
        return '0'
def fetch_devices_by_orgIdAndUserId2(orgId, userId):
    print("fetch_devices_by_orgIdAndUserId:orgId:", orgId)
    print("fetch_devices_by_orgIdAndUserId:userId:", userId)
    if userId:
        user_list = db.session.query(UserInfo).filter_by(id=userId).first()
        user_serial_numbers = [user_list.device_sn]
    else:
        from .org import fetch_users_by_orgId
        user_list = fetch_users_by_orgId(orgId)
        user_serial_numbers = [user['device_sn'] for user in user_list if user.get('device_sn')]
    print("user_serial_numbers:", user_serial_numbers)
    
    if not user_serial_numbers:
        return {'devices': [], 'statistics': {}}
        
    # 修改查询顺序，先从DeviceInfo开始，然后按照数据关系逐步关联
    devices = db.session.query(
        DeviceInfo, 
        OrgInfo.name.label('department_name'),
        UserInfo.user_name
    ).join(
        UserInfo,
        (DeviceInfo.serial_number == UserInfo.device_sn) & 
        (UserInfo.is_deleted.is_(False))  # 添加用户未删除的条件
    ).join(
        UserOrg,
        (UserInfo.id == UserOrg.user_id) &
        (UserOrg.is_deleted.is_(False))  # 如果UserOrg有is_deleted字段
    ).join(
        OrgInfo,
        (UserOrg.org_id == OrgInfo.id) &
        (OrgInfo.is_deleted.is_(False))  # 如果OrgInfo有is_deleted字段
    ).filter(
        DeviceInfo.serial_number.in_(user_serial_numbers)
    ).distinct(
        DeviceInfo.id
    ).all()
 
    
    # 将 DeviceInfo 对象转换为字典
    devices_data = [{
        'id': device.DeviceInfo.id,
        'serial_number': device.DeviceInfo.serial_number,
        'department_name': device.department_name,
        'user_name': device.user_name,
        'charging_status': device.DeviceInfo.charging_status,
        'battery_level': device.DeviceInfo.battery_level,
        'wearable_status': device.DeviceInfo.wearable_status,
        'system_software_version': device.DeviceInfo.system_software_version,
        'bluetooth_address': device.DeviceInfo.bluetooth_address,
        'status': device.DeviceInfo.status,
        'timestamp': device.DeviceInfo.timestamp.strftime("%Y-%m-%d %H:%M:%S") if device.DeviceInfo.timestamp else None,
        'create_time': device.DeviceInfo.create_time.strftime("%Y-%m-%d %H:%M:%S") if device.DeviceInfo.create_time else None,
        'update_time': device.DeviceInfo.update_time.strftime("%Y-%m-%d %H:%M:%S") if device.DeviceInfo.update_time else None,
        'is_deleted': device.DeviceInfo.is_deleted
    } for device in devices]
    
    # 统计信息
    statistics = {
        'by_department': {},
        'by_charging_status': {},
        'by_wearable_status': {},
        'by_system_version': {},
        'by_status': {},
        'department_details': {}
    }
    
    # 按部门统计详细信息
    for device in devices:
        dept_name = device.department_name or 'Unknown'
        dev = device.DeviceInfo
        
        # 初始化部门统计
        if dept_name not in statistics['department_details']:
            statistics['department_details'][dept_name] = {
                'total': 0,
                'charging_status': {},
                'wearable_status': {},
                'system_versions': {},
                'status': {},
                'users': set()  # 添加用户统计
            }
        
        dept_stats = statistics['department_details'][dept_name]
        dept_stats['total'] += 1
        if device.user_name:
            dept_stats['users'].add(device.user_name)
        
        # 更新部门内各状态统计
        dept_stats['charging_status'][dev.charging_status] = dept_stats['charging_status'].get(dev.charging_status, 0) + 1
        dept_stats['wearable_status'][dev.wearable_status] = dept_stats['wearable_status'].get(dev.wearable_status, 0) + 1
        dept_stats['system_versions'][dev.system_software_version] = dept_stats['system_versions'].get(dev.system_software_version, 0) + 1
        dept_stats['status'][dev.status] = dept_stats['status'].get(dev.status, 0) + 1
        
        # 更新总体统计
        statistics['by_department'][dept_name] = statistics['by_department'].get(dept_name, 0) + 1
        statistics['by_charging_status'][dev.charging_status] = statistics['by_charging_status'].get(dev.charging_status, 0) + 1
        statistics['by_wearable_status'][dev.wearable_status] = statistics['by_wearable_status'].get(dev.wearable_status, 0) + 1
        statistics['by_system_version'][dev.system_software_version] = statistics['by_system_version'].get(dev.system_software_version, 0) + 1
        statistics['by_status'][dev.status] = statistics['by_status'].get(dev.status, 0) + 1
    
    # 将用户集合转换为计数
    for dept in statistics['department_details'].values():
        dept['user_count'] = len(dept['users'])
        del dept['users']  # 删除用户集合，只保留计数
    
    # 添加总计信息
    statistics['total_devices'] = len(devices_data)
    statistics['total_departments'] = len(statistics['by_department'])
    
    result = {
        'success': True,
        'data': {
            'devices': devices_data,
            'totalDevices': len(devices_data),
            'statistics': statistics,
            'departmentCount': statistics['total_departments'],
            'deviceStatusCount': statistics['by_status'],
            'deviceChargingCount': statistics['by_charging_status'],
            'deviceWearableCount': statistics['by_wearable_status'],
            'deviceSystemVersionCount': statistics['by_system_version'],
            'departmentDeviceCount': statistics['by_department'],
            'departmentDetails': statistics['department_details']
        }
    }
    return result
def fetch_devices_by_orgIdAndUserId(orgId, userId, customerId=None):
    """🚀 优化后的设备查询 - 直接使用用户表的组织字段，消除JOIN操作"""
    print("fetch_devices_by_orgIdAndUserId:orgId:", orgId)
    print("fetch_devices_by_orgIdAndUserId:userId:", userId)
    print("fetch_devices_by_orgIdAndUserId:customerId:", customerId)
    
    try:
        from .admin_helper import is_admin_user, filter_non_admin_users  # 导入admin判断工具
        
        device_serial_numbers = []
        user_device_mapping = {}  # 存储设备号到用户信息的映射
        org_ids = []  # 初始化org_ids变量，避免未定义错误
        
        if userId:
            # 检查是否为管理员用户
            if is_admin_user(userId):
                return {'devices': [], 'statistics': {}}
            
            # 🚀 优化：单用户模式 - 直接查询用户表，无需JOIN！
            user = UserInfo.query.filter_by(
                id=userId,
                is_deleted=False
            ).first()
            
            if user and user.device_sn:
                device_serial_numbers.append(user.device_sn)
                user_device_mapping[user.device_sn] = {
                    'user_id': user.id,
                    'user_name': user.user_name,
                    # 🎉 直接获取组织信息，无需JOIN！
                    'department_name': user.org_name or '未分配',
                    'org_id': user.org_id
                }
                # 为单用户模式设置org_ids
                if user.org_id:
                    org_ids = [user.org_id]
                
        elif orgId:
            # 🚀 优化：组织模式 - 直接通过org_id查询用户，无需关联表！
            from .org import get_org_descendants
            org_ids = get_org_descendants(orgId)  # 获取组织及其子组织ID列表
            
            # 🎉 直接查询用户表的org_id字段，消除JOIN操作！
            users = UserInfo.query.filter(
                UserInfo.org_id.in_(org_ids),
                UserInfo.is_deleted.is_(False),
                UserInfo.device_sn.isnot(None),
                UserInfo.device_sn != '',
                UserInfo.device_sn != '-'
            ).all()
            
            # 🎉 构建用户列表，直接使用用户表字段，无需额外查询！
            user_list = [{
                'id': user.id,
                'user_name': user.user_name,
                'device_sn': user.device_sn,
                # 🚀 直接访问组织名称，无需JOIN！
                'department_name': user.org_name or '未分配',
                'org_id': user.org_id
            } for user in users]
            
            # 过滤掉管理员用户
            filtered_users = filter_non_admin_users(user_list, 'id')
            
            for user in filtered_users:
                if user['device_sn']:
                    device_serial_numbers.append(user['device_sn'])
                    user_device_mapping[user['device_sn']] = {
                        'user_id': user['id'],
                        'user_name': user['user_name'],
                        'department_name': user['department_name'],
                        'org_id': user['org_id']
                    }
        
        # 如果没有找到任何设备序列号，返回空结果
        if not device_serial_numbers:
            return {
                'success': True,
                'data': {
                    'devices': [],
                    'totalDevices': 0,
                    'statistics': {},
                    'historyAnalysis': {},
                    'departmentCount': 0,
                    'deviceStatusCount': {},
                    'deviceChargingCount': {},
                    'deviceWearableCount': {},
                    'deviceSystemVersionCount': {},
                    'departmentDeviceCount': {},
                    'departmentDetails': {},
                    'batteryAnalysis': {},
                    'chartData': {}
                }
            }
        
        print(f"Found {len(device_serial_numbers)} device serial numbers: {device_serial_numbers}")
        
        # 通过设备序列号查询t_device_info表中的设备信息
        devices = db.session.query(DeviceInfo).filter(
            DeviceInfo.serial_number.in_(device_serial_numbers),
            DeviceInfo.is_deleted.is_(False)
        ).order_by(DeviceInfo.timestamp.desc()).all()
        
        print(f"Found {len(devices)} devices in t_device_info")
        
        # 获取customer_id用于状态判断 - 优先使用传入的customerId
        if customerId:
            customer_id = customerId
        else:
            customer_id=fetch_customer_id_by_deviceSn(device_serial_numbers[0]) if device_serial_numbers else '0' #获取customer_id#
        
        # 转换为字典格式，关联用户信息，动态判断状态
        devices_data = []
        for device in devices:
            user_info = user_device_mapping.get(device.serial_number, {
                'user_id': None,
                'user_name': '未绑定',
                'department_name': '未分配',
                'org_id': None
            })
            
            # 动态判断设备真实状态
            real_status=check_device_real_status(device.serial_number,customer_id) #检查真实状态#
            
            device_data = {
                'id': device.id,
                'serial_number': device.serial_number,
                'user_id': user_info['user_id'],
                'org_id': user_info['org_id'],
                'department_name': user_info['department_name'],
                'user_name': user_info['user_name'],
                'charging_status': device.charging_status,
                'battery_level': device.battery_level,
                'wearable_status': device.wearable_status,
                'system_software_version': device.system_software_version,
                'bluetooth_address': device.bluetooth_address,
                'status': real_status, # 使用动态判断的状态#
                'voltage': device.voltage,
                'ip_address': device.ip_address,
                'network_access_mode': device.network_access_mode,
                'device_name': device.device_name,
                'imei': device.imei,
                'timestamp': device.timestamp.strftime("%Y-%m-%d %H:%M:%S") if device.timestamp else None,
                'create_time': device.create_time.strftime("%Y-%m-%d %H:%M:%S") if device.create_time else None,
                'update_time': device.update_time.strftime("%Y-%m-%d %H:%M:%S") if device.update_time else None,
                'is_deleted': device.is_deleted
            }
            devices_data.append(device_data)
        
        # 生成统计信息
        statistics = generate_device_statistics_simple(devices_data)
        
        # 获取历史数据分析
        history_analysis = get_device_history_analysis([d['serial_number'] for d in devices_data])
        
        result = {
            'success': True,
            'data': {
                'devices': devices_data,
                'totalDevices': len(devices_data),
                'statistics': statistics,
                'historyAnalysis': history_analysis,
                'departmentCount': len(set(d['department_name'] for d in devices_data if d['department_name'] != '未分配')),
                'deviceStatusCount': statistics.get('by_status', {}),
                'deviceChargingCount': statistics.get('by_charging_status', {}),
                'deviceWearableCount': statistics.get('by_wearable_status', {}),
                'deviceSystemVersionCount': statistics.get('by_system_version', {}),
                'departmentDeviceCount': statistics.get('by_department', {}),
                'departmentDetails': statistics.get('department_details', {}),
                'batteryAnalysis': history_analysis.get('battery_analysis', {}),
                'chartData': generate_chart_data_simple(devices_data, history_analysis),
                'userDeviceMapping': user_device_mapping,  # 添加用户设备映射信息
                'queryInfo': {
                    'orgId': orgId,
                    'userId': userId,
                    'orgIds': org_ids if orgId else None,
                    'deviceSerialNumbers': device_serial_numbers
                }
            }
        }
        return result
        
    except Exception as e:
        print(f"Error in fetch_devices_by_orgIdAndUserId: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e), 'devices': [], 'statistics': {}}

def fetch_devices_by_customer_id(customer_id):
    # 获取 UserInfo 表中的序列号
    user_serial_numbers = db.session.query(UserInfo.device_sn).subquery()

    # 查询 DeviceInfo 表，并添加过滤条件
    devices = DeviceInfo.query.filter_by(customer_id=customer_id)\
        .filter(DeviceInfo.serial_number.in_(user_serial_numbers))\
        .all()
        
    print("devices:", devices)

     # Convert each DeviceInfo object to a dictionary
    devices_dict = [device.to_dict() for device in devices]

    return devices

def generate_device_stats(device_info):
    print("generate_device_stats:device_info:", device_info)

    try:
        # Convert the input dictionary to a list of device dictionaries
        device_list = list(device_info.values())

        # Calculate total number of devices
        total_devices = len(device_list)

        # Initialize dictionaries for counts
        device_status_counts = {}
        device_charging_counts = {}
        device_wearable_counts = {}
        device_os_counts = {}

        # Calculate counts for each category
        for device in device_list:
            # Count charging statuses
            device_status_counts[device['status']] = device_status_counts.get(device['status'], 0) + 1

            device_charging_counts[device['charging_status']] = device_charging_counts.get(device['charging_status'], 0) + 1

            # Count wearable statuses
            device_wearable_counts[device['wearable_status']] = device_wearable_counts.get(device['wearable_status'], 0) + 1
            
            # Count system software versions
            device_os_counts[device['system_software_version']] = device_os_counts.get(device['system_software_version'], 0) + 1
     

        # Return a raw dictionary, not a Flask Response
        return {
            'success': True,
            'devices': device_list,
            'totalDevices': total_devices,
            'deviceChargingCounts': device_charging_counts,
            'deviceWearableCounts': device_wearable_counts,
            'deviceOsCounts': device_os_counts,
            'deviceStatusCounts': device_status_counts
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'success': False, 'error': str(e)}  # Return raw error data
    
    
def gather_device_info(customer_id):

    print("customer_id:", customer_id)
    # Filter devices by customer_id
    devices = DeviceInfo.query.filter_by(customer_id=customer_id).all()

    # Initialize statistics
    system_software_versions = {}
    wearable_status_count = {'WORN': 0, 'NOT_WORN': 0}
    charging_status_count = {'CHARGING': 0, 'NOT_CHARGING': 0}
    assigned_devices_count = 0
    active_devices_count = 0  # Initialize active devices count
    total_devices_count = len(devices)  # Calculate total number of devices

    # Fetch the os_version for the customer
    customer_config = CustomerConfig.query.filter_by(id=customer_id).first()
    os_version = customer_config.os_version if customer_config else None
    print("os_version:", os_version)
    # Initialize the counter for devices with version equal to os_version
    matching_version_count = 0

    # Gather statistics
    for device in devices:
        # Count system software versions
        version = device.system_software_version
        print("version:", version)
        if version in system_software_versions:
            system_software_versions[version] += 1
        else:
            system_software_versions[version] = 1

        # Determine if an upgrade is needed
        if os_version and version != os_version:
            print(f"Device {device.serial_number} needs an upgrade from {version} to {os_version}")
        else:
            # Increment the counter if the version matches os_version
            matching_version_count += 1

        # Count wearable status
        if device.wearable_status in wearable_status_count:
            wearable_status_count[device.wearable_status] += 1

        # Count charging status
        if device.charging_status in charging_status_count:
            charging_status_count[device.charging_status] += 1

        # Check if the device is assigned to a user
        if UserInfo.query.filter_by(device_sn=device.serial_number).first():
            assigned_devices_count += 1

        # Check if the device is active
        if device.update_time and (datetime.now() - device.update_time).total_seconds() <= 600:
            active_devices_count += 1

    # Print or store the count of matching versions
    print(f"Number of devices with version matching os_version: {matching_version_count}")

    # Prepare the data to be stored in Redis
    device_info_data = {
        'system_software_versions': matching_version_count,
        'wearable_status_count': wearable_status_count,
        'charging_status_count': charging_status_count,
        'assigned_devices_count': assigned_devices_count,
        'active_devices_count': active_devices_count,  # Include active devices count
        'total_devices_count': total_devices_count  # Include total devices count
    }
    


    # Convert the data to JSON format
    device_info_json = json.dumps(device_info_data)

    # Store the JSON data in Redis with the key "device_info:{customer_id}"
    redis_key = f"device_info:{customer_id}"
    redis.hset(redis_key, mapping={str(device_info_data['id']): json.dumps(device_info_data) for device_info_data in device_info_data})
    redis.publish(f"device_info_channel:{customer_id}", device_info_json)

    # Return the gathered statistics
    return device_info_data

def fetch_user_org_by_deviceSn(deviceSn):
    """根据设备序列号获取绑定的用户ID和直属部门ID"""
    try:
        result = (
            db.session.query(UserInfo, UserOrg)
            .select_from(UserInfo)
            .join(
                UserOrg,
                (UserInfo.id == UserOrg.user_id) & (UserOrg.is_deleted.is_(False))
            )
            .filter(
                UserInfo.device_sn == deviceSn,
                UserInfo.is_deleted.is_(False)
            )
            .first()
        )
        
        if not result:
            return None, None
            
        user_info, user_org = result
        return user_info.id, user_org.org_id
        
    except Exception as e:
        print(f"Error in fetch_user_org_by_deviceSn: {e}")
        return None, None

def generate_device_statistics(devices):
    """生成设备统计信息"""
    statistics = {
        'by_department': {},
        'by_charging_status': {},
        'by_wearable_status': {},
        'by_system_version': {},
        'by_status': {},
        'department_details': {}
    }
    
    for device in devices:
        dept_name = device.department_name or '未分配'
        dev = device.DeviceInfo
        
        # 初始化部门统计
        if dept_name not in statistics['department_details']:
            statistics['department_details'][dept_name] = {
                'total': 0,
                'charging_status': {},
                'wearable_status': {},
                'system_versions': {},
                'status': {},
                'users': set(),
                'battery_stats': {'high': 0, 'medium': 0, 'low': 0}
            }
        
        dept_stats = statistics['department_details'][dept_name]
        dept_stats['total'] += 1
        if device.user_name and device.user_name != '未绑定':
            dept_stats['users'].add(device.user_name)
        
        # 电池统计
        try:
            battery = int(dev.battery_level) if dev.battery_level and dev.battery_level.isdigit() else 0
            if battery > 70: dept_stats['battery_stats']['high'] += 1
            elif battery > 30: dept_stats['battery_stats']['medium'] += 1
            else: dept_stats['battery_stats']['low'] += 1
        except: pass
        
        # 更新部门内各状态统计
        dept_stats['charging_status'][dev.charging_status] = dept_stats['charging_status'].get(dev.charging_status, 0) + 1
        dept_stats['wearable_status'][dev.wearable_status] = dept_stats['wearable_status'].get(dev.wearable_status, 0) + 1
        dept_stats['system_versions'][dev.system_software_version] = dept_stats['system_versions'].get(dev.system_software_version, 0) + 1
        dept_stats['status'][dev.status] = dept_stats['status'].get(dev.status, 0) + 1
        
        # 更新总体统计
        statistics['by_department'][dept_name] = statistics['by_department'].get(dept_name, 0) + 1
        statistics['by_charging_status'][dev.charging_status] = statistics['by_charging_status'].get(dev.charging_status, 0) + 1
        statistics['by_wearable_status'][dev.wearable_status] = statistics['by_wearable_status'].get(dev.wearable_status, 0) + 1
        statistics['by_system_version'][dev.system_software_version] = statistics['by_system_version'].get(dev.system_software_version, 0) + 1
        statistics['by_status'][dev.status] = statistics['by_status'].get(dev.status, 0) + 1
    
    # 将用户集合转换为计数
    for dept in statistics['department_details'].values():
        dept['user_count'] = len(dept['users'])
        del dept['users']
    
    return statistics

def get_device_history_analysis(serial_numbers, days=7):
    """获取设备历史数据分析"""
    if not serial_numbers:
        return {'battery_analysis': {}, 'trend_analysis': {}, 'alerts': []}
    
    try:
        from datetime import timedelta
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # 查询历史数据
        history_data = db.session.query(DeviceInfoHistory).filter(
            DeviceInfoHistory.serial_number.in_(serial_numbers),
            DeviceInfoHistory.timestamp >= start_time,
            DeviceInfoHistory.timestamp <= end_time
        ).order_by(DeviceInfoHistory.timestamp.desc()).all()
        
        # 电池分析
        battery_analysis = analyze_battery_trends(history_data)
        
        # 趋势分析
        trend_analysis = analyze_device_trends(history_data)
        
        # 生成告警
        alerts = generate_device_alerts(history_data, battery_analysis)
        
        return {
            'battery_analysis': battery_analysis,
            'trend_analysis': trend_analysis,
            'alerts': alerts,
            'data_points': len(history_data)
        }
        
    except Exception as e:
        print(f"Error in get_device_history_analysis: {e}")
        return {'battery_analysis': {}, 'trend_analysis': {}, 'alerts': []}

def analyze_battery_trends(history_data):
    """分析电池趋势"""
    battery_trends = {}
    device_battery_data = {}
    
    for record in history_data:
        sn = record.serial_number
        if sn not in device_battery_data:
            device_battery_data[sn] = []
        
        try:
            battery = int(record.battery_level) if record.battery_level and str(record.battery_level).isdigit() else None
            if battery is not None:
                device_battery_data[sn].append({
                    'timestamp': record.timestamp,
                    'battery': battery,
                    'charging': record.charging_status == 'CHARGING'
                })
        except: pass
    
    # 计算每个设备的电池趋势
    for sn, data in device_battery_data.items():
        if len(data) < 2: continue
        
        # 排序数据
        data.sort(key=lambda x: x['timestamp'])
        
        # 计算趋势
        batteries = [d['battery'] for d in data]
        if len(batteries) >= 2:
            # 计算电池消耗率
            time_diff = (data[-1]['timestamp'] - data[0]['timestamp']).total_seconds() / 3600  # 小时
            battery_diff = data[-1]['battery'] - data[0]['battery']
            
            consumption_rate = abs(battery_diff / time_diff) if time_diff > 0 else 0
            
            # 预测电池耗尽时间
            current_battery = data[-1]['battery']
            hours_remaining = current_battery / consumption_rate if consumption_rate > 0 else 0
            
            battery_trends[sn] = {
                'consumption_rate': round(consumption_rate, 2),
                'hours_remaining': round(hours_remaining, 1),
                'current_battery': current_battery,
                'trend': 'declining' if battery_diff < -10 else 'stable' if abs(battery_diff) <= 10 else 'increasing',
                'data_points': len(data)
            }
    
    return battery_trends

def analyze_device_trends(history_data):
    """分析设备使用趋势"""
    trends = {
        'wear_pattern': {},
        'charging_pattern': {},
        'status_changes': {},
        'daily_summary': {}
    }
    
    # 按设备分组
    device_data = {}
    for record in history_data:
        sn = record.serial_number
        if sn not in device_data:
            device_data[sn] = []
        device_data[sn].append(record)
    
    # 分析每个设备的趋势
    for sn, data in device_data.items():
        data.sort(key=lambda x: x.timestamp)
        
        # 佩戴模式分析
        wear_times = []
        charging_times = []
        
        for i, record in enumerate(data):
            hour = record.timestamp.hour
            
            if record.wearable_status == 'WORN':
                wear_times.append(hour)
            
            if record.charging_status == 'CHARGING':
                charging_times.append(hour)
        
        # 计算佩戴高峰时间
        if wear_times:
            from collections import Counter
            wear_counter = Counter(wear_times)
            peak_wear_hour = wear_counter.most_common(1)[0][0]
        else:
            peak_wear_hour = None
        
        # 计算充电高峰时间
        if charging_times:
            from collections import Counter
            charging_counter = Counter(charging_times)
            peak_charging_hour = charging_counter.most_common(1)[0][0]
        else:
            peak_charging_hour = None
        
        trends['wear_pattern'][sn] = {
            'peak_hour': peak_wear_hour,
            'total_wear_records': len(wear_times)
        }
        
        trends['charging_pattern'][sn] = {
            'peak_hour': peak_charging_hour,
            'total_charging_records': len(charging_times)
        }
    
    return trends

def generate_device_alerts(history_data, battery_analysis):
    """生成设备告警 - 优化版，减少无效告警"""
    alerts = []
    
    # 只有当有足够历史数据时才生成告警
    if not history_data or len(history_data) < 5:
        return alerts
    
    for sn, battery_info in battery_analysis.items():
        # 只对有有效数据点的设备生成告警
        if battery_info.get('data_points', 0) < 3:
            continue
            
        current_battery = battery_info.get('current_battery', 0)
        consumption_rate = battery_info.get('consumption_rate', 0)
        hours_remaining = battery_info.get('hours_remaining', 0)
        
        # 低电量告警 - 只在电量确实很低时触发
        if current_battery < 15 and current_battery > 0:
            alerts.append({
                'type': 'low_battery',
                'severity': 'high' if current_battery < 10 else 'medium',
                'device_sn': sn,
                'message': f"设备 {sn} 电量过低: {current_battery}%",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # 电池消耗过快告警 - 提高阈值，增加数据点要求
        if consumption_rate > 15 and battery_info.get('data_points', 0) >= 5:
            alerts.append({
                'type': 'high_consumption',
                'severity': 'medium',
                'device_sn': sn,
                'message': f"设备 {sn} 电池消耗过快: {consumption_rate}%/小时",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # 电池即将耗尽告警 - 只在真正紧急时触发
        if 0 < hours_remaining < 1 and current_battery < 20:
            alerts.append({
                'type': 'battery_depleting',
                'severity': 'high',
                'device_sn': sn,
                'message': f"设备 {sn} 电池将在 {hours_remaining} 小时内耗尽",
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    
    # 限制告警数量，只返回最重要的前5个
    return sorted(alerts, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}[x['severity']], reverse=True)[:5]

def generate_chart_data(devices_data, history_analysis):
    """生成图表数据"""
    chart_data = {
        'battery_distribution': {},
        'department_device_count': {},
        'status_pie_chart': {},
        'battery_trend_line': {},
        'charging_pattern': {},
        'wear_pattern': {},
        'device_model_distribution': {},
        'daily_activity': {}
    }
    
    # 电池分布
    battery_ranges = {'0-20': 0, '21-50': 0, '51-80': 0, '81-100': 0}
    for device in devices_data:
        try:
            battery = int(device['battery_level']) if device['battery_level'] and str(device['battery_level']).isdigit() else 0
            if battery <= 20: battery_ranges['0-20'] += 1
            elif battery <= 50: battery_ranges['21-50'] += 1
            elif battery <= 80: battery_ranges['51-80'] += 1
            else: battery_ranges['81-100'] += 1
        except: pass
    chart_data['battery_distribution'] = battery_ranges
    
    # 部门设备数量
    dept_count = {}
    for device in devices_data:
        dept = device['department_name']
        dept_count[dept] = dept_count.get(dept, 0) + 1
    chart_data['department_device_count'] = dept_count
    
    # 状态饼图
    status_count = {}
    for device in devices_data:
        status = device['status']
        status_count[status] = status_count.get(status, 0) + 1
    chart_data['status_pie_chart'] = status_count
    
    # 设备型号分布
    model_count = {}
    for device in devices_data:
        version = device['system_software_version'] or 'Unknown'
        model = version.split('CN')[0] if 'CN' in version else 'Unknown'
        model_count[model] = model_count.get(model, 0) + 1
    chart_data['device_model_distribution'] = model_count
    
    # 从历史分析中提取电池趋势数据
    if 'battery_analysis' in history_analysis:
        battery_trend_data = {}
        for sn, info in history_analysis['battery_analysis'].items():
            battery_trend_data[sn] = {
                'current': info['current_battery'],
                'rate': info['consumption_rate'],
                'remaining': info['hours_remaining']
            }
        chart_data['battery_trend_line'] = battery_trend_data
    
    return chart_data

def get_org_descendants(org_id):
    """获取组织及其所有子组织的ID列表（简化实现）"""
    try:
        # 简化实现：先返回当前组织ID，后续可以扩展为递归查询
        org_ids = [org_id]
        
        # 查询直接子组织
        child_orgs = db.session.query(OrgInfo.id).filter(
            OrgInfo.ancestors.like(f'%{org_id}%'),
            OrgInfo.is_deleted.is_(False)
        ).all()
        
        org_ids.extend([org[0] for org in child_orgs])
        return org_ids
        
    except Exception as e:
        print(f"Error in get_org_descendants: {e}")
        return [org_id]

def get_interface_call_interval(customer_id): # 获取接口调用间隔配置#
    try:i=db.session.query(Interface).filter(Interface.customer_id==customer_id,Interface.url.like('%upload_device_info%'),Interface.is_deleted.is_(False)).first();return i.call_interval if i else 300 # 默认5分钟#
    except Exception as e:print(f"获取接口配置失败:{e}");return 300 # 默认5分钟#

def check_device_real_status(device_sn,customer_id): # 检查设备真实在线状态#
    try:
        from datetime import datetime,timedelta
        i=get_interface_call_interval(customer_id);t=datetime.now()-timedelta(seconds=i);h=db.session.query(DeviceInfoHistory).filter(DeviceInfoHistory.serial_number==device_sn,DeviceInfoHistory.timestamp>=t,DeviceInfoHistory.is_deleted.is_(False)).first();status='ACTIVE' if h else 'INACTIVE';print(f"设备{device_sn}状态检查:customer_id={customer_id},interval={i}s,cutoff_time={t},history_found={bool(h)},status={status}");return status # 有历史记录为在线，否则离线#
    except Exception as e:print(f"检查设备状态失败:{e}");return 'INACTIVE' # 异常时返回离线#

def get_device_user_org_info(device_sn):
    """根据device_sn获取绑定用户的user_id和org_id(缓存10分钟)"""
    try:
        # Redis缓存key，10分钟有效期
        cache_key = f"device_user_org:{device_sn}"
        
        # 尝试从Redis获取缓存数据
        try:
            cached_data = redis.get(cache_key)
            if cached_data:
                import json
                user_org_info = json.loads(cached_data)
                print(f"从缓存获取设备用户组织信息，device_sn:{device_sn}")
                return user_org_info
        except Exception as e:
            print(f"设备用户组织信息缓存读取失败: {str(e)}")
        
        # 查询设备绑定的用户信息
        user_info = db.session.query(
            UserInfo.id.label('user_id'),
            UserInfo.user_name,
            UserOrg.org_id,
            OrgInfo.name.label('org_name')
        ).join(
            UserOrg, UserInfo.id == UserOrg.user_id
        ).join(
            OrgInfo, UserOrg.org_id == OrgInfo.id
        ).filter(
            UserInfo.device_sn == device_sn,
            UserInfo.is_deleted.is_(False),
            OrgInfo.is_deleted.is_(False)
        ).first()
        
        if user_info:
            result = {
                'success': True,
                'user_id': user_info.user_id,
                'user_name': user_info.user_name,
                'org_id': user_info.org_id,
                'org_name': user_info.org_name,
                'device_sn': device_sn
            }
        else:
            result = {
                'success': False,
                'user_id': None,
                'user_name': None,
                'org_id': None,
                'org_name': None,
                'device_sn': device_sn,
                'message': f'设备{device_sn}未绑定用户或用户信息不完整'
            }
        
        # 缓存结果到Redis(10分钟)
        try:
            import json
            cache_data = json.dumps(result, ensure_ascii=False)
            redis.setex(cache_key, 600, cache_data)  # 10分钟缓存
            print(f"设备用户组织信息已缓存到Redis，device_sn:{device_sn}")
        except Exception as e:
            print(f"设备用户组织信息缓存写入失败: {str(e)}")
        
        return result
        
    except Exception as e:
        print(f"获取设备用户组织信息失败: {str(e)}")
        return {
            'success': False,
            'user_id': None,
            'user_name': None,
            'org_id': None,
            'org_name': None,
            'device_sn': device_sn,
            'error': str(e)
        }

def generate_device_statistics_simple(devices_data):
    """生成设备统计信息-简化版"""
    statistics = {
        'by_department': {},
        'by_charging_status': {},
        'by_wearable_status': {},
        'by_system_version': {},
        'by_status': {},
        'department_details': {}
    }
    
    for device in devices_data:
        dept_name = device['department_name'] or '未分配'
        
        # 初始化部门统计
        if dept_name not in statistics['department_details']:
            statistics['department_details'][dept_name] = {
                'total': 0,
                'charging_status': {},
                'wearable_status': {},
                'system_versions': {},
                'status': {},
                'users': set(),
                'battery_stats': {'high': 0, 'medium': 0, 'low': 0}
            }
        
        dept_stats = statistics['department_details'][dept_name]
        dept_stats['total'] += 1
        if device['user_name'] and device['user_name'] != '未绑定':
            dept_stats['users'].add(device['user_name'])
        
        # 电池统计
        try:
            battery = int(device['battery_level']) if device['battery_level'] and str(device['battery_level']).isdigit() else 0
            if battery > 70: dept_stats['battery_stats']['high'] += 1
            elif battery > 30: dept_stats['battery_stats']['medium'] += 1
            else: dept_stats['battery_stats']['low'] += 1
        except: pass
        
        # 更新部门内各状态统计
        charging_status = device['charging_status'] or 'UNKNOWN'
        wearable_status = device['wearable_status'] or 'UNKNOWN'
        system_version = device['system_software_version'] or 'UNKNOWN'
        status = device['status'] or 'UNKNOWN'
        
        dept_stats['charging_status'][charging_status] = dept_stats['charging_status'].get(charging_status, 0) + 1
        dept_stats['wearable_status'][wearable_status] = dept_stats['wearable_status'].get(wearable_status, 0) + 1
        dept_stats['system_versions'][system_version] = dept_stats['system_versions'].get(system_version, 0) + 1
        dept_stats['status'][status] = dept_stats['status'].get(status, 0) + 1
        
        # 更新总体统计
        statistics['by_department'][dept_name] = statistics['by_department'].get(dept_name, 0) + 1
        statistics['by_charging_status'][charging_status] = statistics['by_charging_status'].get(charging_status, 0) + 1
        statistics['by_wearable_status'][wearable_status] = statistics['by_wearable_status'].get(wearable_status, 0) + 1
        statistics['by_system_version'][system_version] = statistics['by_system_version'].get(system_version, 0) + 1
        statistics['by_status'][status] = statistics['by_status'].get(status, 0) + 1
    
    # 将用户集合转换为计数
    for dept in statistics['department_details'].values():
        dept['user_count'] = len(dept['users'])
        del dept['users']
    
    return statistics

def generate_chart_data_simple(devices_data, history_analysis):
    """生成图表数据-简化版"""
    chart_data = {
        'battery_distribution': {},
        'department_device_count': {},
        'status_pie_chart': {},
        'battery_trend_line': {},
        'charging_pattern': {},
        'wear_pattern': {},
        'device_model_distribution': {},
        'daily_activity': {}
    }
    
    # 电池分布
    battery_ranges = {'0-20': 0, '21-50': 0, '51-80': 0, '81-100': 0}
    for device in devices_data:
        try:
            battery = int(device['battery_level']) if device['battery_level'] and str(device['battery_level']).isdigit() else 0
            if battery <= 20: battery_ranges['0-20'] += 1
            elif battery <= 50: battery_ranges['21-50'] += 1
            elif battery <= 80: battery_ranges['51-80'] += 1
            else: battery_ranges['81-100'] += 1
        except: pass
    chart_data['battery_distribution'] = battery_ranges
    
    # 部门设备数量
    dept_count = {}
    for device in devices_data:
        dept = device['department_name'] or '未分配'
        dept_count[dept] = dept_count.get(dept, 0) + 1
    chart_data['department_device_count'] = dept_count
    
    # 状态饼图
    status_count = {}
    for device in devices_data:
        status = device['status'] or 'UNKNOWN'
        status_count[status] = status_count.get(status, 0) + 1
    chart_data['status_pie_chart'] = status_count
    
    # 设备型号分布
    model_count = {}
    for device in devices_data:
        version = device['system_software_version'] or 'Unknown'
        model = version.split('CN')[0] if 'CN' in version else 'Unknown'
        model_count[model] = model_count.get(model, 0) + 1
    chart_data['device_model_distribution'] = model_count
    
    # 从历史分析中提取电池趋势数据
    if 'battery_analysis' in history_analysis:
        battery_trend_data = {}
        for sn, info in history_analysis['battery_analysis'].items():
            battery_trend_data[sn] = {
                'current': info.get('current_battery', 0),
                'rate': info.get('consumption_rate', 0),
                'remaining': info.get('hours_remaining', 0)
            }
        chart_data['battery_trend_line'] = battery_trend_data
    
    return chart_data

# 批量处理器管理和监控API v2.0 - 使用新的批处理器
def get_batch_processor_stats():
    """获取批量处理器统计信息"""
    try:
        batch_processor = get_batch_processor()
        stats = batch_processor.get_stats()
        
        return jsonify({
            "status": "success",
            "data": {
                "processed_total": stats.get('processed', 0),
                "failed_total": stats.get('failed', 0),
                "queued_current": stats.get('queued', 0),
                "queue_size": stats.get('queue_size', 0),
                "workers": stats.get('workers', 0),
                "running": stats.get('running', False),
                "processed_keys_count": stats.get('processed_keys_count', 0),
                "uptime_seconds": stats.get('uptime_seconds', 0),
                "processing_rate": stats.get('processing_rate', 0),
                "queue_usage": f"{(stats.get('queue_size', 0)/10000)*100:.1f}%"
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def restart_batch_processor():
    """重启批量处理器"""
    try:
        from .device_batch_processor import shutdown_batch_processor
        shutdown_batch_processor()
        
        # 重新获取批量处理器会自动启动新的实例  
        from flask import current_app
        batch_processor = get_batch_processor(current_app)
        
        return jsonify({
            "status": "success", 
            "message": "批量处理器已重启",
            "workers": batch_processor.max_workers
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def configure_batch_processor(batch_size=None, max_wait_time=None, max_workers=None):
    """动态配置批量处理器参数"""
    try:
        batch_processor = get_batch_processor()
        
        if batch_size is not None:
            batch_processor.batch_size = max(1, min(500, int(batch_size)))
        if max_wait_time is not None:
            batch_processor.max_wait_time = max(0.1, min(10.0, float(max_wait_time)))
        if max_workers is not None:
            # 动态调整工作线程数需要重启处理器
            new_workers = max(1, min(20, int(max_workers)))
            if new_workers != batch_processor.max_workers:
                batch_processor.max_workers = new_workers
                return restart_batch_processor()
                
        return jsonify({
            "status": "success",
            "message": "批量处理器配置已更新",
            "config": {
                "batch_size": batch_processor.batch_size,
                "max_wait_time": batch_processor.max_wait_time,
                "max_workers": batch_processor.max_workers
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def get_device_history_timeline(serial_number, limit=60): #获取设备历史时序数据
    """获取设备历史记录的时序数据，用于图表展示"""
    try:
        # 查询最近的历史记录，按时间倒序
        history_records = DeviceInfoHistory.query.filter_by(
            serial_number=serial_number,
            is_deleted=0
        ).order_by(DeviceInfoHistory.timestamp.desc()).limit(limit).all()
        
        if not history_records:
            return jsonify({"status": "success", "data": {"timeline": [], "message": "暂无历史数据"}})
        
        # 构建时序数据
        timeline_data = []
        for record in reversed(history_records):  # 反转以获得时间正序
            timeline_data.append({
                "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M:%S") if record.timestamp else "",
                "battery_level": record.battery_level or 0,
                "wearable_status": record.wearable_status or "UNKNOWN",
                "charging_status": record.charging_status or "UNKNOWN",
                "voltage": record.voltage or 0,
                "status": record.status or "UNKNOWN"
            })
        
        # 计算统计信息
        battery_levels = [r["battery_level"] for r in timeline_data if r["battery_level"] is not None]
        stats = {
            "total_records": len(timeline_data),
            "avg_battery": sum(battery_levels) / len(battery_levels) if battery_levels else 0,
            "min_battery": min(battery_levels) if battery_levels else 0,
            "max_battery": max(battery_levels) if battery_levels else 0,
            "worn_rate": len([r for r in timeline_data if r["wearable_status"] == "WORN"]) / len(timeline_data) * 100 if timeline_data else 0
        }
        
        return jsonify({
            "status": "success",
            "data": {
                "serial_number": serial_number,
                "timeline": timeline_data,
                "statistics": stats
            }
        })
        
    except Exception as e:
        print(f"获取设备历史记录失败: {e}")
        return jsonify({"status": "error", "message": f"获取历史记录失败: {str(e)}"})

def get_device_history_trends(org_id, user_id=None, days=7, metrics=['battery_level', 'wearable_status', 'charging_status']):
    """获取设备历史趋势数据，支持多种指标的时间序列分析"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import text, and_, or_
        
        # 获取设备列表
        devices_data = fetch_devices_by_orgIdAndUserId(org_id, user_id)
        if not devices_data or not devices_data.get('success'):
            return {"success": False, "message": "获取设备列表失败"}
        
        devices = devices_data['data']['devices']
        if not devices:
            return {"success": False, "message": "无设备数据"}
        
        device_sns = [device['serial_number'] for device in devices]
        
        # 智能时间范围计算 - 先找到数据的实际时间范围
        latest_data_sql = text("""
            SELECT MAX(timestamp) as latest_time, MIN(timestamp) as earliest_time 
            FROM t_device_info_history 
            WHERE serial_number IN :device_sns AND is_deleted = 0
        """)
        
        time_result = db.session.execute(latest_data_sql, {'device_sns': tuple(device_sns)}).first()
        
        if time_result and time_result.latest_time:
            # 使用数据的最新时间作为结束时间，往前推指定天数
            end_time = time_result.latest_time
            start_time = end_time - timedelta(days=days)
            print(f"📅 使用数据驱动时间范围: {start_time} ~ {end_time}")
        else:
            # 回退到当前时间
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            print(f"📅 使用默认时间范围: {start_time} ~ {end_time}")
        
        # 构建查询SQL
        sql = text("""
            SELECT 
                serial_number,
                timestamp,
                battery_level,
                wearable_status,
                charging_status,
                system_software_version,
                voltage,
                status
            FROM t_device_info_history 
            WHERE serial_number IN :device_sns 
                AND timestamp >= :start_time 
                AND timestamp <= :end_time
                AND is_deleted = 0
            ORDER BY serial_number, timestamp ASC
        """)
        
        # 执行查询
        result = db.session.execute(sql, {
            'device_sns': tuple(device_sns),
            'start_time': start_time,
            'end_time': end_time
        })
        
        # 处理查询结果
        history_data = {}
        row_count = 0
        for row in result:
            row_count += 1
            sn = row.serial_number
            if sn not in history_data:
                history_data[sn] = {
                    'timestamps': [],
                    'battery_level': [],
                    'wearable_status': [],
                    'charging_status': [],
                    'system_software_version': [],
                    'voltage': [],
                    'status': []
                }
            
            history_data[sn]['timestamps'].append(row.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            history_data[sn]['battery_level'].append(row.battery_level or 0)
            history_data[sn]['wearable_status'].append(row.wearable_status or 'UNKNOWN')
            history_data[sn]['charging_status'].append(row.charging_status or 'UNKNOWN')
            history_data[sn]['system_software_version'].append(row.system_software_version or 'Unknown')
            history_data[sn]['voltage'].append(row.voltage or 0)
            history_data[sn]['status'].append(row.status or 'UNKNOWN')
        
        print(f"📊 查询到 {row_count} 条历史记录，涉及 {len(history_data)} 个设备")
        
        # 如果没有数据，尝试扩大查询范围
        if not history_data and time_result and time_result.latest_time:
            print("⚠️ 指定时间范围无数据，尝试查询最近30天数据...")
            fallback_start = time_result.latest_time - timedelta(days=30)
            fallback_result = db.session.execute(sql, {
                'device_sns': tuple(device_sns),
                'start_time': fallback_start,
                'end_time': time_result.latest_time
            })
            
            for row in fallback_result:
                sn = row.serial_number
                if sn not in history_data:
                    history_data[sn] = {
                        'timestamps': [],
                        'battery_level': [],
                        'wearable_status': [],
                        'charging_status': [],
                        'system_software_version': [],
                        'voltage': [],
                        'status': []
                    }
                
                history_data[sn]['timestamps'].append(row.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                history_data[sn]['battery_level'].append(row.battery_level or 0)
                history_data[sn]['wearable_status'].append(row.wearable_status or 'UNKNOWN')
                history_data[sn]['charging_status'].append(row.charging_status or 'UNKNOWN')
                history_data[sn]['system_software_version'].append(row.system_software_version or 'Unknown')
                history_data[sn]['voltage'].append(row.voltage or 0)
                history_data[sn]['status'].append(row.status or 'UNKNOWN')
            
            if history_data:
                start_time = fallback_start
                print(f"✅ 回退查询成功，获得 {len(history_data)} 个设备的数据")
        
        # 生成趋势分析
        trends_analysis = analyze_device_trends_advanced(history_data, devices)
        
        return {
            "success": True,
            "data": {
                "time_range": {
                    "start": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "end": end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "days": days
                },
                "devices_count": len(device_sns),
                "history_data": history_data,
                "trends_analysis": trends_analysis,
                "chart_data": generate_trends_chart_data(history_data, trends_analysis)
            }
        }
        
    except Exception as e:
        print(f"获取设备历史趋势失败: {e}")
        return {"success": False, "message": f"获取历史趋势失败: {str(e)}"}

def analyze_device_trends_advanced(history_data, devices):
    """高级设备趋势分析"""
    analysis = {
        'battery_trends': {},
        'usage_patterns': {},
        'charging_patterns': {},
        'version_distribution': {},
        'status_stability': {},
        'predictions': {}
    }
    
    for sn, data in history_data.items():
        if not data['timestamps']:
            continue
            
        # 电池趋势分析
        battery_levels = data['battery_level']
        if battery_levels:
            analysis['battery_trends'][sn] = {
                'avg_battery': sum(battery_levels) / len(battery_levels),
                'min_battery': min(battery_levels),
                'max_battery': max(battery_levels),
                'battery_variance': calculate_variance(battery_levels),
                'consumption_rate': calculate_consumption_rate(battery_levels, data['timestamps']),
                'low_battery_events': len([b for b in battery_levels if b <= 20]),
                'critical_battery_events': len([b for b in battery_levels if b <= 10])
            }
        
        # 佩戴模式分析
        wear_statuses = data['wearable_status']
        if wear_statuses:
            worn_count = wear_statuses.count('WORN')
            total_count = len(wear_statuses)
            analysis['usage_patterns'][sn] = {
                'wear_rate': (worn_count / total_count * 100) if total_count > 0 else 0,
                'wear_sessions': count_status_sessions(wear_statuses, 'WORN'),
                'avg_wear_duration': calculate_avg_session_duration(wear_statuses, data['timestamps'], 'WORN'),
                'daily_wear_hours': estimate_daily_wear_hours(wear_statuses, data['timestamps'])
            }
        
        # 充电模式分析
        charging_statuses = data['charging_status']
        if charging_statuses:
            charging_count = charging_statuses.count('CHARGING')
            total_count = len(charging_statuses)
            analysis['charging_patterns'][sn] = {
                'charging_frequency': charging_count,
                'charging_rate': (charging_count / total_count * 100) if total_count > 0 else 0,
                'charging_sessions': count_status_sessions(charging_statuses, 'CHARGING'),
                'avg_charging_duration': calculate_avg_session_duration(charging_statuses, data['timestamps'], 'CHARGING')
            }
        
        # 系统版本分析
        versions = data['system_software_version']
        if versions:
            unique_versions = list(set(versions))
            analysis['version_distribution'][sn] = {
                'current_version': versions[-1] if versions else 'Unknown',
                'version_changes': len(unique_versions) - 1,
                'versions_used': unique_versions
            }
        
        # 状态稳定性分析
        statuses = data['status']
        if statuses:
            online_count = statuses.count('ACTIVE')
            total_count = len(statuses)
            analysis['status_stability'][sn] = {
                'uptime_rate': (online_count / total_count * 100) if total_count > 0 else 0,
                'connection_drops': count_status_changes(statuses, 'ACTIVE', 'INACTIVE'),
                'avg_uptime_duration': calculate_avg_session_duration(statuses, data['timestamps'], 'ACTIVE')
            }
    
    # 生成预测数据
    analysis['predictions'] = generate_device_predictions(analysis)
    
    return analysis

def calculate_variance(values):
    """计算方差"""
    if len(values) < 2:
        return 0
    mean = sum(values) / len(values)
    return sum((x - mean) ** 2 for x in values) / len(values)

def calculate_consumption_rate(battery_levels, timestamps):
    """计算电池消耗率 (%/小时)"""
    if len(battery_levels) < 2:
        return 0
    
    from datetime import datetime
    try:
        start_time = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
        time_diff_hours = (end_time - start_time).total_seconds() / 3600
        
        if time_diff_hours <= 0:
            return 0
            
        battery_diff = battery_levels[0] - battery_levels[-1]
        return battery_diff / time_diff_hours
    except:
        return 0

def count_status_sessions(statuses, target_status):
    """计算状态会话数"""
    if not statuses:
        return 0
    sessions = 0
    in_session = False
    for status in statuses:
        if status == target_status and not in_session:
            sessions += 1
            in_session = True
        elif status != target_status:
            in_session = False
    return sessions

def calculate_avg_session_duration(statuses, timestamps, target_status):
    """计算平均会话持续时间(分钟)"""
    if len(statuses) != len(timestamps):
        return 0
    
    from datetime import datetime
    sessions = []
    session_start = None
    
    for i, status in enumerate(statuses):
        try:
            current_time = datetime.strptime(timestamps[i], '%Y-%m-%d %H:%M:%S')
            
            if status == target_status and session_start is None:
                session_start = current_time
            elif status != target_status and session_start is not None:
                duration = (current_time - session_start).total_seconds() / 60
                sessions.append(duration)
                session_start = None
        except:
            continue
    
    return sum(sessions) / len(sessions) if sessions else 0

def estimate_daily_wear_hours(wear_statuses, timestamps):
    """估算每日佩戴小时数"""
    if not wear_statuses or not timestamps:
        return 0
    
    from datetime import datetime
    try:
        start_time = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
        total_days = max(1, (end_time - start_time).days)
        
        worn_count = wear_statuses.count('WORN')
        total_records = len(wear_statuses)
        
        # 假设每条记录代表5分钟的采样间隔
        wear_minutes = (worn_count / total_records) * len(timestamps) * 5
        daily_wear_hours = wear_minutes / 60 / total_days
        
        return min(24, daily_wear_hours)  # 最多24小时
    except:
        return 0

def count_status_changes(statuses, from_status, to_status):
    """计算状态变化次数"""
    changes = 0
    for i in range(1, len(statuses)):
        if statuses[i-1] == from_status and statuses[i] == to_status:
            changes += 1
    return changes

def generate_device_predictions(analysis):
    """生成设备预测数据"""
    predictions = {
        'battery_health_forecast': {},
        'maintenance_alerts': [],
        'usage_recommendations': [],
        'fleet_insights': {}
    }
    
    for sn, battery_data in analysis.get('battery_trends', {}).items():
        # 电池健康预测
        consumption_rate = battery_data.get('consumption_rate', 0)
        avg_battery = battery_data.get('avg_battery', 100)
        
        if consumption_rate > 0:
            estimated_life_hours = avg_battery / consumption_rate
            predictions['battery_health_forecast'][sn] = {
                'estimated_life_hours': round(estimated_life_hours, 2),
                'health_score': max(0, min(100, 100 - (consumption_rate * 10))),
                'replacement_needed': consumption_rate > 5,  # 每小时消耗超过5%
                'low_battery_risk': battery_data.get('low_battery_events', 0) > 5
            }
        
        # 维护建议
        if battery_data.get('critical_battery_events', 0) > 3:
            predictions['maintenance_alerts'].append({
                'device_sn': sn,
                'alert_type': 'battery_critical',
                'message': f'设备 {sn} 频繁出现电量过低，建议检查电池健康状况',
                'priority': 'high'
            })
    
    # 使用模式建议
    for sn, usage_data in analysis.get('usage_patterns', {}).items():
        wear_rate = usage_data.get('wear_rate', 0)
        if wear_rate < 30:
            predictions['usage_recommendations'].append({
                'device_sn': sn,
                'recommendation': f'设备 {sn} 佩戴率较低({wear_rate:.1f}%)，建议提醒用户增加佩戴时间',
                'category': 'usage_optimization'
            })
    
    return predictions

def generate_trends_chart_data(history_data, trends_analysis):
    """生成趋势图表数据"""
    from datetime import datetime, timedelta
    
    # 生成时间轴（最近7天，每小时一个点）
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    time_points = []
    current_time = start_time
    
    while current_time <= end_time:
        time_points.append(current_time.strftime('%m-%d %H:00'))
        current_time += timedelta(hours=1)
    
    chart_data = {
        'battery_level': {
            'dates': time_points,
            'avg_levels': [],
            'min_levels': [],
            'max_levels': []
        },
        'wearable_status': {
            'dates': time_points,
            'worn_count': [],
            'not_worn_count': []
        },
        'charging_status': {
            'dates': time_points,
            'charging_count': [],
            'not_charging_count': []
        },
        'uptime_trend': {
            'dates': time_points,
            'uptime_rates': []
        }
    }
    
    # 为每个时间点计算统计数据
    for i, time_point in enumerate(time_points):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        # 收集该小时内的所有数据
        hour_battery_levels = []
        hour_wear_worn = 0
        hour_wear_total = 0
        hour_charge_charging = 0
        hour_charge_total = 0
        hour_active_count = 0
        hour_total_devices = 0
        
        for sn, data in history_data.items():
            for j, timestamp_str in enumerate(data['timestamps']):
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                    if hour_start <= timestamp < hour_end:
                        # 电池数据
                        if data['battery_level'][j] is not None:
                            hour_battery_levels.append(data['battery_level'][j])
                        
                        # 佩戴状态
                        hour_wear_total += 1
                        if data['wearable_status'][j] == 'WORN':
                            hour_wear_worn += 1
                        
                        # 充电状态
                        hour_charge_total += 1
                        if data['charging_status'][j] == 'CHARGING':
                            hour_charge_charging += 1
                        
                        # 在线状态
                        hour_total_devices += 1
                        if data['status'][j] == 'ACTIVE':
                            hour_active_count += 1
                except:
                    continue
        
        # 计算该小时的统计值
        chart_data['battery_level']['avg_levels'].append(
            round(sum(hour_battery_levels) / len(hour_battery_levels), 1) if hour_battery_levels else 0
        )
        chart_data['battery_level']['min_levels'].append(
            min(hour_battery_levels) if hour_battery_levels else 0
        )
        chart_data['battery_level']['max_levels'].append(
            max(hour_battery_levels) if hour_battery_levels else 0
        )
        
        chart_data['wearable_status']['worn_count'].append(hour_wear_worn)
        chart_data['wearable_status']['not_worn_count'].append(hour_wear_total - hour_wear_worn)
        
        chart_data['charging_status']['charging_count'].append(hour_charge_charging)
        chart_data['charging_status']['not_charging_count'].append(hour_charge_total - hour_charge_charging)
        
        uptime_rate = (hour_active_count / hour_total_devices * 100) if hour_total_devices > 0 else 0
        chart_data['uptime_trend']['uptime_rates'].append(round(uptime_rate, 1))
    
    return chart_data

def get_device_battery_prediction(org_id, user_id=None, days=30):
    """获取设备电池预测数据"""
    try:
        from datetime import datetime, timedelta
        import numpy as np
        from sklearn.linear_model import LinearRegression
        
        # 获取历史趋势数据
        trends_data = get_device_history_trends(org_id, user_id, days)
        if not trends_data.get('success'):
            return trends_data
        
        history_data = trends_data['data']['history_data']
        predictions = {}
        
        for sn, data in history_data.items():
            if not data['battery_level'] or len(data['battery_level']) < 10:
                continue
            
            # 准备训练数据
            battery_levels = data['battery_level']
            timestamps = data['timestamps']
            
            # 预测未来电池趋势
            prediction_result = predict_battery_life(battery_levels, timestamps)
            if prediction_result:
                predictions[sn] = prediction_result
        
        # 生成预测图表数据
        chart_data = generate_battery_prediction_chart_data(predictions)
        
        return {
            "success": True,
            "data": {
                "predictions": predictions,
                "chart_data": chart_data,
                "summary": generate_prediction_summary(predictions),
                "recommendations": generate_fleet_recommendations(predictions)
            }
        }
        
    except Exception as e:
        print(f"电池预测失败: {e}")
        return {"success": False, "message": f"电池预测失败: {str(e)}"}

def predict_battery_life(battery_levels, timestamps):
    """预测电池寿命"""
    try:
        from datetime import datetime
        import numpy as np
        
        if len(battery_levels) < 5:
            return None
        
        # 转换时间戳为数值
        time_values = []
        for ts in timestamps:
            try:
                dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
                time_values.append(dt.timestamp())
            except:
                continue
        
        if len(time_values) != len(battery_levels):
            return None
        
        # 使用简单线性回归预测
        X = np.array(time_values).reshape(-1, 1)
        y = np.array(battery_levels)
        
        # 计算趋势
        if len(X) >= 2:
            slope = (y[-1] - y[0]) / (X[-1][0] - X[0][0]) * 3600  # 每小时变化率
            
            current_battery = battery_levels[-1]
            current_time = time_values[-1]
            
            # 预测未来7天的电池电量
            future_predictions = []
            future_dates = []
            
            for i in range(1, 8):  # 未来7天
                future_time = current_time + (i * 24 * 3600)  # 每天
                predicted_battery = max(0, current_battery + (slope * 24 * i))
                
                future_dt = datetime.fromtimestamp(future_time)
                future_dates.append(future_dt.strftime('%m-%d'))
                future_predictions.append(round(predicted_battery, 1))
            
            return {
                'current_battery': current_battery,
                'consumption_rate': abs(slope),
                'predicted_levels': future_predictions,
                'predicted_dates': future_dates,
                'days_until_empty': max(1, int(current_battery / abs(slope) / 24)) if slope < 0 else 999,
                'health_status': 'good' if abs(slope) < 2 else 'warning' if abs(slope) < 5 else 'critical'
            }
    
    except Exception as e:
        print(f"电池预测计算失败: {e}")
        return None

def generate_battery_prediction_chart_data(predictions):
    """生成电池预测图表数据"""
    if not predictions:
        return {
            'dates': [],
            'historical': [],
            'predicted': []
        }
    
    # 使用第一个设备的预测数据作为示例
    first_device = next(iter(predictions.values()))
    
    return {
        'dates': first_device.get('predicted_dates', []),
        'historical': [first_device.get('current_battery', 0)] * len(first_device.get('predicted_dates', [])),
        'predicted': first_device.get('predicted_levels', [])
    }

def generate_usage_forecast(device_data, forecast_days):
    """生成使用预测"""
    return {
        'forecast_days': forecast_days,
        'predicted_usage': [],
        'confidence_level': 0.8
    }

def generate_prediction_summary(predictions):
    """生成预测摘要"""
    if not predictions:
        return {
            'total_devices': 0,
            'healthy_devices': 0,
            'warning_devices': 0,
            'critical_devices': 0
        }
    
    total = len(predictions)
    healthy = sum(1 for p in predictions.values() if p.get('health_status') == 'good')
    warning = sum(1 for p in predictions.values() if p.get('health_status') == 'warning')
    critical = sum(1 for p in predictions.values() if p.get('health_status') == 'critical')
    
    return {
        'total_devices': total,
        'healthy_devices': healthy,
        'warning_devices': warning,
        'critical_devices': critical,
        'avg_days_until_empty': sum(p.get('days_until_empty', 0) for p in predictions.values()) / total if total > 0 else 0
    }

def generate_fleet_recommendations(predictions):
    """生成车队建议"""
    recommendations = []
    
    for sn, pred in predictions.items():
        if pred.get('health_status') == 'critical':
            recommendations.append({
                'device_sn': sn,
                'priority': 'high',
                'action': '立即更换电池',
                'reason': f'电池消耗率过高({pred.get("consumption_rate", 0):.2f}%/h)'
            })
        elif pred.get('days_until_empty', 999) < 3:
            recommendations.append({
                'device_sn': sn,
                'priority': 'medium',
                'action': '安排充电',
                'reason': f'预计{pred.get("days_until_empty")}天后电量耗尽'
            })
    
    return recommendations

def calculate_avg_session_duration(statuses, timestamps, target_status):
    """计算平均会话持续时间（分钟）"""
    if len(statuses) != len(timestamps):
        return 0
    
    from datetime import datetime
    sessions = []
    session_start = None
    
    for i, status in enumerate(statuses):
        try:
            current_time = datetime.strptime(timestamps[i], '%Y-%m-%d %H:%M:%S')
            
            if status == target_status and session_start is None:
                session_start = current_time
            elif status != target_status and session_start is not None:
                duration = (current_time - session_start).total_seconds() / 60
                sessions.append(duration)
                session_start = None
        except:
            continue
    
    return sum(sessions) / len(sessions) if sessions else 0

def estimate_daily_wear_hours(wear_statuses, timestamps):
    """估算日均佩戴小时数"""
    if not wear_statuses or not timestamps:
        return 0
    
    from datetime import datetime
    try:
        start_time = datetime.strptime(timestamps[0], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(timestamps[-1], '%Y-%m-%d %H:%M:%S')
        total_days = (end_time - start_time).days + 1
        
        worn_count = wear_statuses.count('WORN')
        total_records = len(wear_statuses)
        
        # 假设每条记录代表5分钟的采样间隔
        wear_minutes = (worn_count / total_records) * (len(timestamps) * 5)
        daily_wear_hours = (wear_minutes / 60) / total_days
        
        return round(daily_wear_hours, 2)
    except:
        return 0

def count_status_changes(statuses, from_status, to_status):
    """计算状态变化次数"""
    changes = 0
    for i in range(1, len(statuses)):
        if statuses[i-1] == from_status and statuses[i] == to_status:
            changes += 1
    return changes

def generate_device_predictions(analysis):
    """生成设备预测数据"""
    predictions = {
        'battery_health_forecast': {},
        'maintenance_recommendations': {},
        'usage_optimization': {}
    }
    
    for sn in analysis['battery_trends'].keys():
        battery_trend = analysis['battery_trends'].get(sn, {})
        usage_pattern = analysis['usage_patterns'].get(sn, {})
        charging_pattern = analysis['charging_patterns'].get(sn, {})
        
        # 电池健康预测
        consumption_rate = battery_trend.get('consumption_rate', 0)
        avg_battery = battery_trend.get('avg_battery', 0)
        
        if consumption_rate > 0:
            estimated_life_hours = avg_battery / consumption_rate
            predictions['battery_health_forecast'][sn] = {
                'estimated_remaining_hours': round(estimated_life_hours, 1),
                'health_status': 'good' if consumption_rate < 5 else 'warning' if consumption_rate < 10 else 'critical',
                'replacement_needed_in_days': round(estimated_life_hours / 24, 1) if estimated_life_hours < 168 else None
            }
        
        # 维护建议
        recommendations = []
        if battery_trend.get('low_battery_events', 0) > 5:
            recommendations.append('频繁低电量，建议优化充电策略')
        if usage_pattern.get('wear_rate', 0) < 50:
            recommendations.append('佩戴率偏低，建议提醒用户佩戴')
        if charging_pattern.get('charging_frequency', 0) > 10:
            recommendations.append('充电频率过高，检查电池健康')
        
        predictions['maintenance_recommendations'][sn] = recommendations
        
        # 使用优化建议
        optimizations = []
        daily_wear = usage_pattern.get('daily_wear_hours', 0)
        if daily_wear < 8:
            optimizations.append(f'建议增加佩戴时间至8小时/天（当前{daily_wear}小时）')
        if charging_pattern.get('avg_charging_duration', 0) > 120:
            optimizations.append('充电时间过长，建议检查充电器')
        
        predictions['usage_optimization'][sn] = optimizations
    
    return predictions

def generate_trends_chart_data(history_data, trends_analysis):
    """生成图表数据"""
    chart_data = {
        'battery_trend_line': {},
        'wear_status_timeline': {},
        'charging_pattern_chart': {},
        'status_uptime_chart': {},
        'device_health_radar': {},
        'prediction_forecast': {}
    }
    
    # 电池趋势线图数据
    for sn, data in history_data.items():
        if data['battery_level']:
            chart_data['battery_trend_line'][sn] = {
                'timestamps': data['timestamps'],
                'values': data['battery_level'],
                'trend': trends_analysis['battery_trends'].get(sn, {})
            }
    
    # 佩戴状态时间线
    for sn, data in history_data.items():
        if data['wearable_status']:
            # 转换状态为数值：WORN=1, NOT_WORN=0
            status_values = [1 if status == 'WORN' else 0 for status in data['wearable_status']]
            chart_data['wear_status_timeline'][sn] = {
                'timestamps': data['timestamps'],
                'values': status_values,
                'pattern': trends_analysis['usage_patterns'].get(sn, {})
            }
    
    # 充电模式图表
    for sn, data in history_data.items():
        if data['charging_status']:
            charging_values = [1 if status == 'CHARGING' else 0 for status in data['charging_status']]
            chart_data['charging_pattern_chart'][sn] = {
                'timestamps': data['timestamps'],
                'values': charging_values,
                'pattern': trends_analysis['charging_patterns'].get(sn, {})
            }
    
    # 设备在线率图表
    for sn, data in history_data.items():
        if data['status']:
            online_values = [1 if status == 'ACTIVE' else 0 for status in data['status']]
            chart_data['status_uptime_chart'][sn] = {
                'timestamps': data['timestamps'],
                'values': online_values,
                'stability': trends_analysis['status_stability'].get(sn, {})
            }
    
    # 设备健康雷达图
    for sn in history_data.keys():
        battery_trend = trends_analysis['battery_trends'].get(sn, {})
        usage_pattern = trends_analysis['usage_patterns'].get(sn, {})
        charging_pattern = trends_analysis['charging_patterns'].get(sn, {})
        status_stability = trends_analysis['status_stability'].get(sn, {})
        
        chart_data['device_health_radar'][sn] = {
            'battery_health': min(100, max(0, 100 - battery_trend.get('consumption_rate', 0) * 10)),
            'usage_efficiency': usage_pattern.get('wear_rate', 0),
            'charging_health': min(100, max(0, 100 - charging_pattern.get('charging_frequency', 0) * 5)),
            'connection_stability': status_stability.get('uptime_rate', 0),
            'overall_score': 0  # 将在前端计算
        }
    
    # 预测数据
    chart_data['prediction_forecast'] = trends_analysis.get('predictions', {})
    
    return chart_data

def get_device_battery_prediction(org_id, user_id=None, days=30):
    """获取设备电池使用预测"""
    try:
        # 获取历史趋势数据
        trends_data = get_device_history_trends(org_id, user_id, days)
        if not trends_data.get('success'):
            return trends_data
        
        history_data = trends_data['data']['history_data']
        predictions = {}
        
        for sn, data in history_data.items():
            if not data['battery_level'] or len(data['battery_level']) < 10:
                continue
            
            # 使用线性回归预测电池趋势
            battery_prediction = predict_battery_life(data['battery_level'], data['timestamps'])
            
            predictions[sn] = {
                'current_battery': data['battery_level'][-1] if data['battery_level'] else 0,
                'predicted_depletion_time': battery_prediction.get('depletion_hours', 0),
                'recommended_charge_time': battery_prediction.get('charge_recommendation', ''),
                'battery_health_score': battery_prediction.get('health_score', 0),
                'usage_forecast': generate_usage_forecast(data, 7)  # 7天预测
            }
        
        return {
            "success": True,
            "data": {
                "predictions": predictions,
                "summary": generate_prediction_summary(predictions),
                "recommendations": generate_fleet_recommendations(predictions)
            }
        }
        
    except Exception as e:
        print(f"电池预测分析失败: {e}")
        return {"success": False, "message": f"预测分析失败: {str(e)}"}

def predict_battery_life(battery_levels, timestamps):
    """预测电池寿命"""
    if len(battery_levels) < 2:
        return {'depletion_hours': 0, 'health_score': 0, 'charge_recommendation': '数据不足'}
    
    from datetime import datetime
    import numpy as np
    
    try:
        # 转换时间戳为数值
        time_values = []
        for ts in timestamps:
            dt = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
            time_values.append(dt.timestamp())
        
        # 简单线性回归
        x = np.array(time_values)
        y = np.array(battery_levels)
        
        # 计算斜率（电池消耗率）
        if len(x) > 1:
            slope = np.polyfit(x, y, 1)[0]  # 每秒电量变化
            
            current_battery = battery_levels[-1]
            current_time = time_values[-1]
            
            # 预测电量耗尽时间（小时）
            if slope < 0:
                depletion_seconds = current_battery / abs(slope)
                depletion_hours = depletion_seconds / 3600
            else:
                depletion_hours = float('inf')  # 电量在增加
            
            # 健康评分（基于消耗率）
            hourly_consumption = abs(slope) * 3600
            health_score = max(0, min(100, 100 - hourly_consumption * 10))
            
            # 充电建议
            if current_battery <= 20:
                charge_recommendation = '立即充电'
            elif depletion_hours <= 4:
                charge_recommendation = '建议在4小时内充电'
            elif depletion_hours <= 12:
                charge_recommendation = '建议在12小时内充电'
            else:
                charge_recommendation = '电量充足'
            
            return {
                'depletion_hours': round(depletion_hours, 1),
                'health_score': round(health_score, 1),
                'charge_recommendation': charge_recommendation,
                'consumption_rate_per_hour': round(hourly_consumption, 2)
            }
    except Exception as e:
        print(f"电池预测计算失败: {e}")
    
    return {'depletion_hours': 0, 'health_score': 0, 'charge_recommendation': '计算失败'}

def generate_usage_forecast(device_data, forecast_days):
    """生成使用预测"""
    if not device_data['wearable_status']:
        return {}
    
    # 计算历史佩戴模式
    wear_statuses = device_data['wearable_status']
    total_records = len(wear_statuses)
    worn_records = wear_statuses.count('WORN')
    wear_rate = (worn_records / total_records) if total_records > 0 else 0
    
    # 预测未来使用情况
    forecast = {
        'expected_daily_wear_hours': round(wear_rate * 24, 1),
        'expected_weekly_wear_hours': round(wear_rate * 24 * 7, 1),
        'usage_pattern': 'high' if wear_rate > 0.7 else 'medium' if wear_rate > 0.4 else 'low'
    }
    
    return forecast

def generate_prediction_summary(predictions):
    """生成预测摘要"""
    if not predictions:
        return {}
    
    total_devices = len(predictions)
    low_battery_devices = len([p for p in predictions.values() if p['current_battery'] <= 20])
    critical_devices = len([p for p in predictions.values() if p['predicted_depletion_time'] <= 4])
    
    avg_health_score = sum(p['battery_health_score'] for p in predictions.values()) / total_devices
    
    return {
        'total_devices': total_devices,
        'low_battery_count': low_battery_devices,
        'critical_battery_count': critical_devices,
        'average_health_score': round(avg_health_score, 1),
        'devices_need_attention': low_battery_devices + critical_devices
    }

def generate_fleet_recommendations(predictions):
    """生成车队级别的建议"""
    recommendations = []
    
    if not predictions:
        return recommendations
    
    # 分析整体情况
    total_devices = len(predictions)
    low_battery_count = len([p for p in predictions.values() if p['current_battery'] <= 20])
    critical_count = len([p for p in predictions.values() if p['predicted_depletion_time'] <= 4])
    
    if critical_count > 0:
        recommendations.append(f'紧急：{critical_count}台设备需要立即充电')
    
    if low_battery_count > total_devices * 0.3:
        recommendations.append('建议制定统一的充电计划，超过30%的设备电量偏低')
    
    # 健康评分分析
    health_scores = [p['battery_health_score'] for p in predictions.values()]
    avg_health = sum(health_scores) / len(health_scores)
    
    if avg_health < 70:
        recommendations.append('设备整体电池健康状况需要关注，建议进行维护检查')
    
    return recommendations


# =============================================================================
# 设备分析功能 (Device Analysis Functions)
# =============================================================================

def get_device_analysis_data(orgId, userId, timeRange='24h'):
    """设备分析数据接口，支持时间范围和趋势分析"""
    try:
        # 获取基础设备数据
        devices_result = fetch_devices_by_orgIdAndUserId(orgId, userId)
        devices = []
        
        if devices_result and isinstance(devices_result, dict):
            if 'devices' in devices_result:
                devices = devices_result['devices']
            elif 'data' in devices_result and isinstance(devices_result, dict):
                devices = devices_result['data'].get('devices', [])
        
        # 生成分析数据
        analysis_data = generate_device_analysis_data(devices, timeRange)
        
        return {
            'success': True,
            'data': analysis_data
        }, 200
        
    except Exception as e:
        logger.error(f"设备分析数据获取失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }, 500


def generate_device_analysis_data(devices, timeRange):
    """生成设备分析数据"""
    import random
    from datetime import datetime, timedelta
    
    # 基础统计
    total_devices = len(devices)
    online_devices = len([d for d in devices if d.get('status') == 'ACTIVE'])
    charging_devices = len([d for d in devices if d.get('charging_status') == 'CHARGING'])
    worn_devices = len([d for d in devices if d.get('wearable_status') == 'WORN'])
    low_battery_devices = len([d for d in devices if int(d.get('battery_level', 0)) <= 20])
    
    # 状态分布
    status_distribution = {
        'online': online_devices,
        'offline': total_devices - online_devices,
        'charging': charging_devices,
        'worn': worn_devices,
        'low_battery': low_battery_devices
    }
    
    # 电池统计
    battery_levels = [int(d.get('battery_level', 0)) for d in devices]
    battery_stats = {
        'average': sum(battery_levels) / len(battery_levels) if battery_levels else 0,
        'min': min(battery_levels) if battery_levels else 0,
        'max': max(battery_levels) if battery_levels else 100,
        'levels': battery_levels[:10]  # 只返回前10个设备的电池电量用于图表
    }
    
    # 生成趋势数据
    time_points = generate_time_points(timeRange)
    trends = {
        'timestamps': time_points,
        'online_trend': [online_devices + random.randint(-2, 2) for _ in time_points],
        'battery_trend': [battery_stats['average'] + random.randint(-5, 5) for _ in time_points],
        'activity_trend': [random.randint(50, 100) for _ in time_points]
    }
    
    # 设备型号统计
    model_stats = {}
    for device in devices:
        model = device.get('model', '未知型号')
        model_stats[model] = model_stats.get(model, 0) + 1
    
    # 健康评分分析
    health_analysis = analyze_device_health(devices)
    
    return {
        'summary': {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'online_percentage': round((online_devices / total_devices * 100) if total_devices > 0 else 0, 2),
            'low_battery_devices': low_battery_devices,
            'charging_devices': charging_devices,
            'worn_devices': worn_devices
        },
        'status_distribution': status_distribution,
        'battery_stats': battery_stats,
        'trends': trends,
        'model_stats': model_stats,
        'health_analysis': health_analysis,
        'time_range': timeRange,
        'last_updated': datetime.now().isoformat()
    }


def generate_time_points(timeRange):
    """生成时间点数据"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    time_points = []
    
    if timeRange == '1h':
        # 过去1小时，每5分钟一个点
        for i in range(12):
            time_points.append((now - timedelta(minutes=i*5)).strftime('%H:%M'))
    elif timeRange == '6h':
        # 过去6小时，每30分钟一个点
        for i in range(12):
            time_points.append((now - timedelta(minutes=i*30)).strftime('%H:%M'))
    elif timeRange == '24h':
        # 过去24小时，每2小时一个点
        for i in range(12):
            time_points.append((now - timedelta(hours=i*2)).strftime('%m-%d %H:%M'))
    elif timeRange == '7d':
        # 过去7天，每天一个点
        for i in range(7):
            time_points.append((now - timedelta(days=i)).strftime('%m-%d'))
    
    return list(reversed(time_points))


def analyze_device_health(devices):
    """分析设备健康状况"""
    if not devices:
        return {'score': 0, 'level': '无数据', 'recommendations': []}
    
    # 计算健康评分
    total_score = 0
    factors = 0
    
    # 电池健康评估
    battery_levels = [int(d.get('battery_level', 0)) for d in devices if d.get('battery_level')]
    if battery_levels:
        avg_battery = sum(battery_levels) / len(battery_levels)
        total_score += min(avg_battery / 50 * 100, 100)  # 50%以上电量为健康
        factors += 1
    
    # 在线率评估
    online_devices = len([d for d in devices if d.get('status') == 'ACTIVE'])
    online_rate = (online_devices / len(devices)) * 100
    total_score += online_rate
    factors += 1
    
    # 佩戴率评估
    worn_devices = len([d for d in devices if d.get('wearable_status') == 'WORN'])
    worn_rate = (worn_devices / len(devices)) * 100
    total_score += worn_rate
    factors += 1
    
    health_score = total_score / factors if factors > 0 else 0
    
    # 健康等级评估
    if health_score >= 90:
        level = '优秀'
    elif health_score >= 80:
        level = '良好'
    elif health_score >= 70:
        level = '一般'
    elif health_score >= 60:
        level = '较差'
    else:
        level = '很差'
    
    # 建议生成
    recommendations = []
    if health_score < 70:
        recommendations.append('设备整体健康状况需要关注')
    if online_rate < 80:
        recommendations.append('设备在线率偏低，请检查网络连接')
    if worn_rate < 60:
        recommendations.append('设备佩戴率偏低，建议提醒用户正确佩戴')
    if battery_levels and sum(battery_levels) / len(battery_levels) < 30:
        recommendations.append('设备电池电量普遍偏低，建议及时充电')
    
    return {
        'score': round(health_score, 2),
        'level': level,
        'recommendations': recommendations,
        'metrics': {
            'online_rate': round(online_rate, 2),
            'worn_rate': round(worn_rate, 2),
            'avg_battery': round(sum(battery_levels) / len(battery_levels), 2) if battery_levels else 0
        }
    }

