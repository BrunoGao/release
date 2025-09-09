import json
from flask import request, jsonify
from .models import DeviceMessage, DeviceMessageDetail, db, DeviceInfo, UserInfo, UserOrg, OrgInfo
from .redis_helper import RedisHelper
from datetime import datetime, timedelta
from .org import fetch_departments_by_orgId
from typing import List, Dict, Optional, Tuple
import logging

# 导入日志配置
try:
    from .logging_config import device_logger
except ImportError:
    device_logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
redis = RedisHelper()

def get_all_message_data_optimized(orgId=None, userId=None, startDate=None, endDate=None, latest_only=False, page=1, pageSize=None, message_type=None, include_details=False):
    """
    统一的消息数据查询接口，支持分页和优化查询
    
    Args:
        orgId: 组织ID
        userId: 用户ID  
        startDate: 开始日期
        endDate: 结束日期
        latest_only: 是否只查询最新记录
        page: 页码
        pageSize: 每页大小
        message_type: 消息类型
        include_details: 是否包含详细信息
    
    Returns:
        dict: 包含消息数据和分页信息的字典
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
        cache_key = f"message_opt_v1:{orgId}:{userId}:{startDate}:{endDate}:{mode}:{page}:{pageSize}:{message_type}:{include_details}"
        
        # 缓存检查
        cached = redis.get_data(cache_key)
        if cached:
            result = json.loads(cached)
            result['performance'] = {'cached': True, 'response_time': round(time.time() - start_time, 3)}
            return result
        
        # 构建查询条件
        query = db.session.query(
            DeviceMessage.id,
            DeviceMessage.message,
            DeviceMessage.message_type,
            DeviceMessage.sender_type,
            DeviceMessage.receiver_type,
            DeviceMessage.message_status,
            DeviceMessage.send_time,
            DeviceMessage.received_time,
            DeviceMessage.user_id,
            DeviceMessage.org_id,
            DeviceMessage.responded_number,
            DeviceMessage.total_number,
            UserInfo.user_name,
            OrgInfo.name.label('org_name')
        ).outerjoin(
            UserInfo, DeviceMessage.user_id == UserInfo.id
        ).outerjoin(
            OrgInfo, DeviceMessage.org_id == OrgInfo.id
        ).filter(
            DeviceMessage.is_deleted == False
        )
        
        if userId:
            # 单用户查询 - 包括个人消息和发给组织的群发消息
            from .admin_helper import is_admin_user
            if is_admin_user(userId):
                return {"success": True, "data": {"messageData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
            
            # 🚀 优化：直接从用户表获取组织ID，无需关联表查询！
            user_info = UserInfo.query.filter_by(id=userId).first()
            if user_info and user_info.org_id:
                org_id = user_info.org_id
                # 获取组织及其所有上级组织的ID
                org_info = OrgInfo.query.filter_by(id=org_id).first()
                if org_info and org_info.ancestors:
                    ancestor_org_ids = [int(id) for id in org_info.ancestors.split(',') if id != '0']
                    ancestor_org_ids.append(org_id)
                else:
                    ancestor_org_ids = [org_id] if org_id else []
                
                # 查询用户个人消息和公告消息
                query = query.filter(
                    db.or_(
                        DeviceMessage.user_id == userId,  # 个人消息
                        db.and_(DeviceMessage.org_id.in_(ancestor_org_ids), DeviceMessage.user_id.is_(None))  # 公告消息
                    )
                )
            else:
                # 如果用户没有组织关联，只查个人消息
                query = query.filter(DeviceMessage.user_id == userId)
                
        elif orgId:
            # 组织查询 - 获取组织下所有用户的消息
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(orgId)
            if not users:
                return {"success": True, "data": {"messageData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
            
            user_ids = [int(user['id']) for user in users]
            
            # 获取所有相关组织ID（包括子部门）
            departments_response = fetch_departments_by_orgId(orgId)
            subordinate_org_ids = []
            if departments_response['success'] and departments_response['data']:
                def extract_department_ids(departments):
                    dept_ids = []
                    for dept in departments:
                        dept_ids.append(int(dept['id']))
                        if 'children' in dept and dept['children']:
                            dept_ids.extend(extract_department_ids(dept['children']))
                    return dept_ids
                subordinate_org_ids = extract_department_ids(departments_response['data'])
            
            all_org_ids = list(set([orgId] + subordinate_org_ids))
            
            # 查询用户消息和群发消息
            query = query.filter(
                db.or_(
                    DeviceMessage.user_id.in_(user_ids),  # 用户消息
                    db.and_(DeviceMessage.org_id.in_(all_org_ids), DeviceMessage.user_id.is_(None))  # 群发消息
                )
            )
            
        else:
            return {"success": False, "message": "缺少orgId或userId参数", "data": {"messageData": [], "totalRecords": 0}}
        
        # 时间范围过滤
        if startDate:
            query = query.filter(DeviceMessage.send_time >= startDate)
        if endDate:
            query = query.filter(DeviceMessage.send_time <= endDate)
        
        # 消息类型过滤
        if message_type:
            query = query.filter(DeviceMessage.message_type == message_type)
        
        # 统计总数
        total_count = query.count()
        
        # 排序
        query = query.order_by(DeviceMessage.send_time.desc())
        
        # 分页处理
        if pageSize is not None:
            offset = (page - 1) * pageSize
            query = query.offset(offset).limit(pageSize)
        
        if latest_only and not pageSize:
            query = query.limit(1)
        
        # 执行查询
        messages = query.all()
        
        # 格式化数据
        message_data_list = []
        for message in messages:
            message_dict = {
                'id': message.id,
                'message': message.message,
                'message_type': message.message_type,
                'sender_type': message.sender_type,
                'receiver_type': message.receiver_type,
                'message_status': message.message_status,
                'send_time': message.send_time.strftime('%Y-%m-%d %H:%M:%S') if message.send_time else None,
                'received_time': message.received_time.strftime('%Y-%m-%d %H:%M:%S') if message.received_time else None,
                'user_id': message.user_id,
                'org_id': message.org_id,
                'responded_number': message.responded_number or 0,
                'total_number': message.total_number or 0,
                'user_name': message.user_name,
                'org_name': message.org_name,
                'dept_name': message.org_name,  # 兼容字段
                'dept_id': message.org_id
            }
            
            # 如果需要包含详细信息
            if include_details:
                message_dict['details'] = []  # 可以在此处添加消息相关详细信息
            
            message_data_list.append(message_dict)
        
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
                'messageData': message_data_list,
                'totalRecords': len(message_data_list),
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
        logger.error(f"消息查询失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': {'messageData': [], 'totalRecords': 0}
        }

class MessageService:
    """消息管理统一服务封装类 - 基于userId的查询和汇总"""
    
    def __init__(self):
        self.redis = redis
    
    def get_messages_by_common_params(self, customer_id: int = None, org_id: int = None,
                                    user_id: int = None, start_date: str = None, 
                                    end_date: str = None, message_type: str = None,
                                    page: int = 1, page_size: int = None,
                                    latest_only: bool = False, include_details: bool = False) -> Dict:
        """
        基于统一参数获取消息信息 - 整合现有get_all_message_data_optimized接口
        
        Args:
            customer_id: 客户ID (映射到orgId)
            org_id: 组织ID
            user_id: 用户ID
            start_date: 开始日期
            end_date: 结束日期
            message_type: 消息类型
            page: 页码
            page_size: 每页大小
            latest_only: 是否只查询最新记录
            include_details: 是否包含详细信息
            
        Returns:
            消息信息字典
        """
        try:
            # 参数映射和优先级处理
            if user_id:
                result = get_all_message_data_optimized(
                    orgId=None,
                    userId=user_id, 
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=latest_only,
                    page=page,
                    pageSize=page_size,
                    message_type=message_type,
                    include_details=include_details
                )
                logger.info(f"基于userId查询消息数据: user_id={user_id}")
                
            elif org_id:
                # 组织查询 - 获取组织下所有用户的消息
                result = get_all_message_data_optimized(
                    orgId=org_id,
                    userId=None,
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=latest_only,
                    page=page,
                    pageSize=page_size,
                    message_type=message_type,
                    include_details=include_details
                )
                logger.info(f"基于orgId查询消息数据: org_id={org_id}")
                
            elif customer_id:
                # 客户查询 - 将customer_id作为orgId处理
                result = get_all_message_data_optimized(
                    orgId=customer_id,
                    userId=None,
                    startDate=start_date,
                    endDate=end_date,
                    latest_only=latest_only,
                    page=page,
                    pageSize=page_size,
                    message_type=message_type,
                    include_details=include_details
                )
                logger.info(f"基于customerId查询消息数据: customer_id={customer_id}")
                
            else:
                return {
                    'success': False,
                    'error': 'Missing required parameters: customer_id, org_id, or user_id',
                    'data': {'messages': [], 'total_count': 0}
                }
            
            # 统一返回格式，兼容新的服务接口
            if result.get('success', True):
                message_data = result.get('data', {}).get('messageData', [])
                
                unified_result = {
                    'success': True,
                    'data': {
                        'messages': message_data,
                        'total_count': result.get('data', {}).get('totalRecords', len(message_data)),
                        'pagination': result.get('data', {}).get('pagination', {}),
                        'query_params': {
                            'customer_id': customer_id,
                            'org_id': org_id,
                            'user_id': user_id,
                            'start_date': start_date,
                            'end_date': end_date,
                            'message_type': message_type,
                            'page': page,
                            'page_size': page_size,
                            'latest_only': latest_only,
                            'include_details': include_details
                        }
                    },
                    'performance': result.get('performance', {}),
                    'from_cache': result.get('performance', {}).get('cached', False)
                }
                
                return unified_result
            else:
                return result
                
        except Exception as e:
            logger.error(f"消息查询失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'messages': [], 'total_count': 0}
            }
    
    def _get_messages_by_user_id(self, user_id: int, start_date: str = None,
                                end_date: str = None, message_type: str = None) -> List[Dict]:
        """基于用户ID查询消息"""
        try:
            # 查询用户相关的消息
            query = db.session.query(
                DeviceMessage.id,
                DeviceMessage.message,
                DeviceMessage.message_type,
                DeviceMessage.sender_type,
                DeviceMessage.receiver_type,
                DeviceMessage.message_status,
                DeviceMessage.send_time,
                DeviceMessage.received_time,
                DeviceMessage.user_id,
                DeviceMessage.org_id,
                DeviceMessage.responded_number,
                DeviceMessage.total_number,
                UserInfo.user_name,
                OrgInfo.name.label('org_name')
            ).outerjoin(
                UserInfo, DeviceMessage.user_id == UserInfo.id
            ).outerjoin(
                OrgInfo, DeviceMessage.org_id == OrgInfo.id
            ).filter(
                DeviceMessage.user_id == user_id
            )
            
            # 时间范围过滤
            if start_date:
                query = query.filter(DeviceMessage.send_time >= start_date)
            if end_date:
                query = query.filter(DeviceMessage.send_time <= end_date)
            if message_type:
                query = query.filter(DeviceMessage.message_type == message_type)
            
            results = query.order_by(DeviceMessage.send_time.desc()).all()
            
            messages = []
            for result in results:
                messages.append(self._format_message_data(result))
            
            return messages
            
        except Exception as e:
            logger.error(f"基于用户ID查询消息失败: {e}")
            return []
    
    def _get_messages_by_org_id(self, org_id: int, customer_id: int = None,
                               start_date: str = None, end_date: str = None,
                               message_type: str = None) -> List[Dict]:
        """基于组织ID查询消息"""
        try:
            # 获取组织下所有用户
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(org_id, customer_id)
            
            if not users:
                # 没有用户时，查询发送给组织的群发消息
                query = db.session.query(
                    DeviceMessage.id,
                    DeviceMessage.message,
                    DeviceMessage.message_type,
                    DeviceMessage.sender_type,
                    DeviceMessage.receiver_type,
                    DeviceMessage.message_status,
                    DeviceMessage.send_time,
                    DeviceMessage.received_time,
                    DeviceMessage.user_id,
                    DeviceMessage.org_id,
                    DeviceMessage.responded_number,
                    DeviceMessage.total_number,
                    UserInfo.user_name,
                    OrgInfo.name.label('org_name')
                ).outerjoin(
                    UserInfo, DeviceMessage.user_id == UserInfo.id
                ).outerjoin(
                    OrgInfo, DeviceMessage.org_id == OrgInfo.id
                ).filter(
                    DeviceMessage.org_id == org_id,
                    DeviceMessage.user_id.is_(None)  # 群发消息
                )
            else:
                user_ids = [int(user['id']) for user in users]
                
                # 查询用户消息和群发消息
                query = db.session.query(
                    DeviceMessage.id,
                    DeviceMessage.message,
                    DeviceMessage.message_type,
                    DeviceMessage.sender_type,
                    DeviceMessage.receiver_type,
                    DeviceMessage.message_status,
                    DeviceMessage.send_time,
                    DeviceMessage.received_time,
                    DeviceMessage.user_id,
                    DeviceMessage.org_id,
                    DeviceMessage.responded_number,
                    DeviceMessage.total_number,
                    UserInfo.user_name,
                    OrgInfo.name.label('org_name')
                ).outerjoin(
                    UserInfo, DeviceMessage.user_id == UserInfo.id
                ).outerjoin(
                    OrgInfo, DeviceMessage.org_id == OrgInfo.id
                ).filter(
                    db.or_(
                        DeviceMessage.user_id.in_(user_ids),
                        db.and_(DeviceMessage.org_id == org_id, DeviceMessage.user_id.is_(None))
                    )
                )
            
            # 时间范围过滤
            if start_date:
                query = query.filter(DeviceMessage.send_time >= start_date)
            if end_date:
                query = query.filter(DeviceMessage.send_time <= end_date)
            if message_type:
                query = query.filter(DeviceMessage.message_type == message_type)
            
            results = query.order_by(DeviceMessage.send_time.desc()).all()
            
            messages = []
            for result in results:
                messages.append(self._format_message_data(result))
            
            return messages
            
        except Exception as e:
            logger.error(f"基于组织ID查询消息失败: {e}")
            return []
    
    def _get_messages_by_customer_id(self, customer_id: int, start_date: str = None,
                                    end_date: str = None, message_type: str = None) -> List[Dict]:
        """基于客户ID查询消息"""
        try:
            # 通过用户表的customer_id查询
            query = db.session.query(
                DeviceMessage.id,
                DeviceMessage.message,
                DeviceMessage.message_type,
                DeviceMessage.sender_type,
                DeviceMessage.receiver_type,
                DeviceMessage.message_status,
                DeviceMessage.send_time,
                DeviceMessage.received_time,
                DeviceMessage.user_id,
                DeviceMessage.org_id,
                DeviceMessage.responded_number,
                DeviceMessage.total_number,
                UserInfo.user_name,
                OrgInfo.name.label('org_name')
            ).outerjoin(
                UserInfo, DeviceMessage.user_id == UserInfo.id
            ).outerjoin(
                OrgInfo, DeviceMessage.org_id == OrgInfo.id
            ).filter(
                db.or_(
                    UserInfo.customer_id == customer_id,
                    db.and_(DeviceMessage.user_id.is_(None), OrgInfo.customer_id == customer_id)
                )
            )
            
            # 时间范围过滤
            if start_date:
                query = query.filter(DeviceMessage.send_time >= start_date)
            if end_date:
                query = query.filter(DeviceMessage.send_time <= end_date)
            if message_type:
                query = query.filter(DeviceMessage.message_type == message_type)
            
            results = query.order_by(DeviceMessage.send_time.desc()).all()
            
            messages = []
            for result in results:
                messages.append(self._format_message_data(result))
            
            return messages
            
        except Exception as e:
            logger.error(f"基于客户ID查询消息失败: {e}")
            return []
    
    def _format_message_data(self, result) -> Dict:
        """格式化消息数据"""
        return {
            'id': result.id,
            'message': result.message,
            'message_type': result.message_type,
            'sender_type': result.sender_type,
            'receiver_type': result.receiver_type,
            'message_status': result.message_status,
            'send_time': result.send_time.strftime('%Y-%m-%d %H:%M:%S') if result.send_time else None,
            'received_time': result.received_time.strftime('%Y-%m-%d %H:%M:%S') if result.received_time else None,
            'user_id': result.user_id,
            'org_id': result.org_id,
            'responded_number': result.responded_number or 0,
            'total_number': result.total_number or 0,
            'user_name': result.user_name,
            'org_name': result.org_name
        }
    
    def get_message_statistics_by_common_params(self, customer_id: int = None,
                                               org_id: int = None, user_id: int = None,
                                               start_date: str = None, end_date: str = None) -> Dict:
        """基于统一参数获取消息统计"""
        try:
            cache_key = f"message_stats_v2:{customer_id}:{org_id}:{user_id}:{start_date}:{end_date}"
            
            # 缓存检查
            cached = self.redis.get_data(cache_key)
            if cached:
                return json.loads(cached)
            
            # 获取消息数据
            messages_result = self.get_messages_by_common_params(
                customer_id, org_id, user_id, start_date, end_date
            )
            
            if not messages_result.get('success'):
                return messages_result
            
            messages = messages_result['data']['messages']
            
            # 计算统计数据
            total_messages = len(messages)
            type_stats = {}
            status_stats = {'pending': 0, 'sent': 0, 'received': 0, 'responded': 0}
            response_stats = {'total_sent': 0, 'total_responded': 0}
            
            for message in messages:
                # 消息类型统计
                msg_type = message.get('message_type', 'unknown')
                if msg_type not in type_stats:
                    type_stats[msg_type] = 0
                type_stats[msg_type] += 1
                
                # 消息状态统计
                status = message.get('message_status', 'pending')
                if status in status_stats:
                    status_stats[status] += 1
                
                # 响应统计
                total_num = message.get('total_number', 0)
                responded_num = message.get('responded_number', 0)
                response_stats['total_sent'] += total_num
                response_stats['total_responded'] += responded_num
            
            # 按组织统计
            org_stats = {}
            for message in messages:
                org_name = message.get('org_name', '未知组织')
                if org_name not in org_stats:
                    org_stats[org_name] = {
                        'total': 0,
                        'pending': 0,
                        'responded': 0,
                        'response_rate': 0
                    }
                
                org_stats[org_name]['total'] += 1
                status = message.get('message_status', 'pending')
                if status == 'pending':
                    org_stats[org_name]['pending'] += 1
                elif status in ['responded', 'received']:
                    org_stats[org_name]['responded'] += 1
            
            # 计算响应率
            for org_name in org_stats:
                total = org_stats[org_name]['total']
                responded = org_stats[org_name]['responded']
                org_stats[org_name]['response_rate'] = round(responded / total * 100, 2) if total > 0 else 0
            
            result = {
                'success': True,
                'data': {
                    'overview': {
                        'total_messages': total_messages,
                        'type_stats': type_stats,
                        'status_stats': status_stats,
                        'response_stats': response_stats,
                        'overall_response_rate': round(response_stats['total_responded'] / response_stats['total_sent'] * 100, 2) if response_stats['total_sent'] > 0 else 0
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
            logger.error(f"消息统计计算失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': {'overview': {}, 'org_statistics': {}}
            }

# 全局实例
_message_service_instance = None

def get_unified_message_service() -> MessageService:
    """获取统一消息服务实例"""
    global _message_service_instance
    if _message_service_instance is None:
        _message_service_instance = MessageService()
    return _message_service_instance

# 向后兼容的函数，供现有代码使用
def get_messages_unified(customer_id: int = None, org_id: int = None,
                        user_id: int = None, start_date: str = None,
                        end_date: str = None, message_type: str = None,
                        page: int = 1, page_size: int = None,
                        latest_only: bool = False, include_details: bool = False) -> Dict:
    """统一的消息查询接口 - 整合现有get_all_message_data_optimized接口"""
    service = get_unified_message_service()
    return service.get_messages_by_common_params(
        customer_id, org_id, user_id, start_date, end_date, message_type,
        page, page_size, latest_only, include_details
    )

def get_message_statistics_unified(customer_id: int = None, org_id: int = None,
                                  user_id: int = None, start_date: str = None,
                                  end_date: str = None) -> Dict:
    """统一的消息统计接口"""
    service = get_unified_message_service()
    return service.get_message_statistics_by_common_params(customer_id, org_id, user_id, start_date, end_date)
def send_message(data):
    print("DeviceMessage:send_message", data)

    # Check if all required fields are present
    required_fields = ['department_id','message_id', 'message', 'device_sn', 'received_time', 'user_id']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # Check if message_id is present to update the existing message
    message_id = data.get('message_id')
    
    print("message_id:", message_id)
    if message_id:
        message = DeviceMessage.query.get(message_id)
        print("message:", message)
        if message:
            # 检查 message.user_id 是否为空
            if message.user_id is None:
                # 群发消息
                print("群发消息")
                # 检查是否已存在该设备的响应
                existing_detail = DeviceMessageDetail.query.filter_by(
                    message_id=message_id,
                    device_sn=data['device_sn']
                ).first()
                
                print("existing_detail:", existing_detail)

                if not existing_detail:
                    # 插入 DeviceMessageDetail
                    message_detail = DeviceMessageDetail(
                        message_id=message_id,
                        device_sn=data['device_sn'],
                        message=data['message'],
                        message_type=data['message_type'],
                        sender_type=data.get('sender_type', 'device'),
                        receiver_type=data.get('receiver_type', 'platform'),
                        message_status=data['message_status'] 
                    )
                    db.session.add(message_detail)
                    
                    # 增加响应计数
                    message.responded_number = message.responded_number + 1
                 
            else:
                # 个人消息
                print("个人消息")
                # 查询 user_id 对应的 device_sn
                user = UserInfo.query.filter_by(id=message.user_id, is_deleted=0).first()
                
                if user and user.device_sn == data['device_sn']:
                    # 更新消息状态
                    message.message_status = '2'  # 已响应
                    
                    # 插入 DeviceMessageDetail
                    existing_detail = DeviceMessageDetail.query.filter_by(
                        message_id=message_id,
                        device_sn=data['device_sn']
                    ).first()
                    
                    if not existing_detail:
                        message_detail = DeviceMessageDetail(
                            message_id=message_id,
                            device_sn=data['device_sn'],
                            message=data['message'],
                            message_type=data['message_type'],
                            sender_type=data.get('sender_type', 'device'),
                            receiver_type=data.get('receiver_type', 'platform'),
                            message_status='2'  # 已响应
                        )
                        db.session.add(message_detail)
            message.received_time = data['received_time'] # 更新DeviceMessage的received_time
            
            db.session.commit()
            return jsonify({"status": "success", "message": "数据已接收并处理", "id": message.id}), 200
        else:
            return jsonify({"status": "error", "message": "Message not found"}), 404
    else:
        print("数据有误，手表回复了不存在的消息")
        return jsonify({"status": "error", "message": "数据有误，手表回复了不存在的消息"}), 400
    
def received_messages(device_sn):
    # 1. 查询 device_sn 对应的 userId
    user = UserInfo.query.filter_by(device_sn=device_sn, is_deleted=0).first()
    if not user:
        return {"success": False, "error": "未找到对应的用户"}

    user_id = user.id

    # 2. 调用 fetch_messages_by_orgIdAndUserId 获取原始返回
    resp = fetch_messages_by_orgIdAndUserId(orgId=None, userId=user_id)
    if not resp.get("success"):
        return {"success": False, "error": "获取消息失败"}

    raw_data = resp.get("data")

    # 3. 兼容两种 data 结构：dict 包含 messages，或直接是列表
    if isinstance(raw_data, dict):
        msgs = raw_data.get("messages", [])
        container = raw_data
    elif isinstance(raw_data, list):
        msgs = raw_data
        container = {"messages": msgs}
    else:
        msgs = []
        container = {"messages": []}

    # 4. 过滤：去掉 message_status 为 "2" 或 "responded" 的消息，以及 message_id 和 device_sn 存在于 DeviceMessageDetail 中的消息
    filtered = [
        m for m in msgs
        if m.get("message_status") not in ("2", "responded") and not DeviceMessageDetail.query.filter_by(message_id=m.get("message_id"), device_sn=device_sn).first()
    ]

    # 5. 把过滤后的列表放回 container["messages"]
    container["messages"] = filtered

    # 6. 返回时包装到 data.messages 下
    return {
        "success": True,
        "data": container
    }
    

def send_message_bak(data):
    print("DeviceMessage:send_message", data)

    # Check if all required fields are present
    required_fields = ['device_sn','id', 'message', 'message_type', 'sender_type', 'receiver_type']
    if not all(field in data for field in required_fields):
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # Check if message_id is present to update the existing message
    message_id = data.get('id')
    
    print("message_id:", message_id)
    if message_id:
        message = DeviceMessage.query.get(message_id)
        print("message:", message)
        if message:
            if message.device_sn == 'all':
                print("message.device_sn:", message.device_sn)
                # Check if the message detail already exists
                existing_detail = DeviceMessageDetail.query.filter_by(
                    message_id=message_id,
                    device_sn=data['device_sn']
                ).first()

                if not existing_detail:
                    # Insert into DeviceMessageDetail if it doesn't exist
                    message_detail = DeviceMessageDetail(
                        message_id=message_id,
                        device_sn=data['device_sn'],
                        message=data['message'],
                        message_type=data['message_type'],
                        sender_type=data['sender_type'],
                        receiver_type=data['receiver_type'],
                        message_status=data['message_status']
                    )
                    db.session.add(message_detail)
                    print("message.responded_number:", message.responded_number)
                    message.responded_number = message.responded_number + 1
            else:
                message.device_sn = data['device_sn']
                message.message = data['message']
                message.message_type = data['message_type']
                message.sender_type = data['sender_type']
                message.receiver_type = data['receiver_type']
                message.message_status = data['message_status']

                # Convert sent_time and received_time to MySQL compatible format
                sent_time_str = data.get('sent_time')
                received_time_str = data.get('received_time')
                if sent_time_str:
                    message.sent_time = datetime.strptime(sent_time_str, '%a, %d %b %Y %H:%M:%S GMT')
                if received_time_str:
                    message.received_time = datetime.fromisoformat(received_time_str.replace('Z', '+00:00'))

            db.session.commit()
            return jsonify({"status": "success", "message": "数据已接收并处理", "id": message.id}), 200
        else:
            return jsonify({"status": "error", "message": "Message not found"}), 404
    else:
        # Create a new message if message_id is not provided
        message = DeviceMessage(
            device_sn=data['device_sn'],
            message=data['message'],
            message_type=data['message_type'],
            sender_type=data['sender_type'],
            receiver_type=data['receiver_type'],
            message_status=data['message_status']
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({"status": "success", "message": "数据已接收并处理", "message_id": message.id}), 201    
def received_messages_bak(device_sn):
    # Modify the query to filter by device_sn or 'all' and check for non-existence in DeviceMessageDetail
    messages = DeviceMessage.query.filter(
        ((DeviceMessage.device_sn == device_sn) | 
         ((DeviceMessage.device_sn == 'all')  & 
          ~DeviceMessageDetail.query.filter_by(
              device_sn=device_sn, 
              message_id=DeviceMessage.id
          ).exists())),
        DeviceMessage.message_status == 'pending' or DeviceMessage.message_status == '1'
    ).all()
    
    messages_data = [{
        'id': str(m.id),  # Convert id to string
        'device_sn': m.device_sn,
        'message': m.message,
        'message_type': m.message_type,
        'sender_type': m.sender_type,
        'receiver_type': m.receiver_type,
        'message_status': m.message_status,
        'sent_time': m.sent_time,
        'received_time': m.received_time
    } for m in messages]
    
    # Wrap the list of messages in a dictionary
    response_data = {
        'success': True,
        'messages': messages_data
    }
    
    return jsonify(response_data), 200
    
def generate_message_stats(message_info):
    #print("generate_alert_stats:alert_info:", alert_info)

    try:
        # Calculate total number of messages
        total_messages = len(message_info)

        # Initialize dictionaries for counts
        message_status_counts = {}
        message_type_counts = {}

        # Calculate counts for each category
        for message in message_info:
            # Count alert statuses
            message_status_counts[message['message_status']] = message_status_counts.get(message['message_status'], 0) + 1

            # Count alert types
            message_type_counts[message['message_type']] = message_type_counts.get(message['message_type'], 0) + 1

        # Calculate total number of unique alert types
        unique_message_types = len(message_type_counts)
        print("unique_message_types:", unique_message_types)
        print("message_status_counts:", message_status_counts)
        print("message_type_counts:", message_type_counts)

        # Return a raw dictionary, not a Flask Response
        return {
            'success': True,
            'messages': message_info,
            'totalMessages': total_messages,
            'uniqueMessageTypes': unique_message_types,
            'messageStatusCounts': message_status_counts,
            'messageTypeCounts': message_type_counts,
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'success': False, 'error': str(e)}  # Return raw error data
    
def fetch_messages(deviceSn, messageType, customerId):
    print("deviceSn:", deviceSn)
    print("messageType:", messageType)
    print("customerId:", customerId)
    print("fetch_alerts:deviceSn:", deviceSn)
    from .user import get_user_info
    user_info = get_user_info(deviceSn)
    print("fetch_alerts:user_info:", user_info)
    if user_info:
        user_dict = json.loads(user_info)
        userId = user_dict.get('user_id')
        return fetch_messages_by_orgIdAndUserId(orgId=None, userId=userId,messageType=messageType)
    else:
        return jsonify({"error": "User not found"}), 404

    try:
        if deviceSn is None:
            subquery = db.session.query(DeviceInfo.serial_number).filter(DeviceInfo.customer_id == customerId).subquery()
            print("subquery:", subquery)
            messages = DeviceMessage.query.filter(DeviceMessage.device_sn.in_(subquery)).all()
        else:
            if messageType is None:
                messages = DeviceMessage.query.filter_by(device_sn=deviceSn).all()
            else:
                messages = DeviceMessage.query.filter_by(device_sn=deviceSn, message_type=messageType).all()
        
        print("messages:", messages)
        messages_data = [{
            'id': message.id,
            'device_sn': message.device_sn,
            'message': message.message,
            'message_type': message.message_type,
            'message_status': message.message_status,
            'sent_time': message.sent_time.strftime("%Y-%m-%d %H:%M:%S") if message.sent_time else None,
            'received_time': message.received_time.strftime("%Y-%m-%d %H:%M:%S") if message.received_time else None
        } for message in messages]
        
        # Calculate total number of alerts
        total_messages = len(messages)

        # Calculate total number of unique alert types
        unique_message_types = len(set(message.message_type for message in messages))

        # Calculate statistics for message_type and message_status
        message_type_count = {}
        message_status_count = {}

        for message in messages:
            message_type_count[message.message_type] = message_type_count.get(message.message_type, 0) + 1
            message_status_count[message.message_status] = message_status_count.get(message.message_status, 0) + 1

        response_data = {
            'success': True,
            'messages': messages_data,
            'totalMessages': total_messages,
            'uniqueMessageTypes': unique_message_types,
            'messageTypeCount': message_type_count,
            'messageStatusCount': message_status_count
        }
        print("response_data:", response_data)

        # Store all messages for the same deviceSn in a single Redis hash
       
        # Publish the message data
        messages_data_json = json.dumps(messages_data)
        print("messages_data_json:", messages_data_json)
        if len(messages_data_json) > 0:  # Check if alerts_data_json is not empty
            mapping = {str(message['id']): json.dumps(message) for message in messages_data}
            if mapping:  # Ensure mapping is not empty
                if deviceSn is None:
                    redis.hset(f"message_info:all", mapping=mapping)
                    redis.publish("message_info_channel", messages_data_json)
                else:
                    redis.hset(f"message_info:{deviceSn}", mapping=mapping)
                    redis.publish(f"message_info_channel:{deviceSn}", messages_data_json)

        return jsonify(response_data)  # Pass the dictionary directly
    except Exception as e:
        print("Error:", e)
        return jsonify({'success': False, 'error': str(e)}), 500

def fetch_messages_by_orgIdAndUserId(orgId, userId=None, messageType=None):
    """
    获取消息列表
    :param orgId: 组织ID
    :param userId: 用户ID，可选
    :param messageType: 消息类型，可选
    """
    try:
        from .admin_helper import is_admin_user  # 导入admin判断函数
        
        #print(f"DEBUG: fetch_messages_by_orgIdAndUserId - orgId: {orgId}, userId: {userId}, messageType: {messageType}")
        result_list = []
        seen_message_ids = set()

        def extract_department_ids(departments):
            """递归提取所有部门ID"""
            dept_ids = []
            for dept in departments:
                dept_ids.append(int(dept['id']))
                if 'children' in dept and dept['children']:
                    dept_ids.extend(extract_department_ids(dept['children']))
            return dept_ids

        # 基础查询
        base_query = db.session.query(
            DeviceMessage.id,
            DeviceMessage.message,
            DeviceMessage.message_type,
            DeviceMessage.message_status,
            DeviceMessage.sent_time,
            DeviceMessage.received_time,
            DeviceMessage.org_id,  # 修改: department_info -> org_id
            DeviceMessage.sender_type,
            DeviceMessage.receiver_type,
            UserInfo.id.label('user_id'),
            UserInfo.user_name,
            UserInfo.device_sn
        ).outerjoin(
            UserInfo,
            DeviceMessage.user_id == UserInfo.id
        ).filter(
            DeviceMessage.is_deleted.is_(False)
        ).order_by(DeviceMessage.sent_time.desc())

        if messageType:
            base_query = base_query.filter(DeviceMessage.message_type == messageType)

        # 如果提供了userId
        if userId:
            # 检查是否为管理员用户
            if is_admin_user(userId):
                return {
                    'success': True,
                    'data': {
                        'messages': [],
                        'totalMessages': 0,
                        'messageTypeCount': {},
                        'messageStatusCount': {},
                        'departmentStats': {},
                        'orgId': str(orgId) if orgId else None
                    }
                }
            
            #print(f"DEBUG: 查询用户 {userId} 的消息")
            # 🚀 优化：直接从用户表获取组织ID，无需关联表查询！
            user_info = UserInfo.query.filter_by(id=userId).first()
            print(f"DEBUG: user_info 查询结果: {user_info}")
            
            if not user_info:
                raise Exception(f"User {userId} not found")
            
            # 🎉 直接使用用户表的org_id字段！
            org_id = user_info.org_id
            if not org_id:
                # 如果用户表中没有org_id，尝试使用传入的orgId
                org_id = int(orgId) if orgId else None
                if not org_id:
                    raise Exception("User organization not found and no orgId provided")
            
            print(f"DEBUG: 从用户表直接获取org_id: {org_id}")
            
            # 1. 获取用户个人消息
            personal_messages = base_query.filter(DeviceMessage.user_id == userId).all()
            #print(f"DEBUG: 用户个人消息数量: {len(personal_messages)}")
            
            # 2. 🔧 修复: 简化用户组织消息查询，直接基于org_id查询
            print(f"🔍 查询用户组织org_id={org_id}的公告消息")
            
            # 直接查询用户所在组织的公告消息
            announcement_messages = base_query.filter(
                DeviceMessage.org_id == str(org_id),  # 直接匹配org_id
                DeviceMessage.user_id == None  # 公告消息没有user_id
            ).all()
            
            print(f"📊 用户组织公告消息: {len(announcement_messages)} 条")

        else:
            # 如果只提供了orgId
            if not orgId:
                raise Exception("Either userId or orgId must be provided")

            # 🔧 修复: 简化消息查询逻辑，直接基于orgId查询，不依赖ancestors字段
            print(f"🔍 直接查询orgId={orgId}的消息")
            
            # 1. 直接查询指定orgId的消息（公告和个人消息）
            all_messages = base_query.filter(
                DeviceMessage.org_id == str(orgId)  # 直接匹配org_id
            ).all()
            
            print(f"📊 查询到 {len(all_messages)} 条消息，orgId={orgId}")
            
            # 2. 获取子部门消息（如果需要包含子部门）
            try:
                departments_response = fetch_departments_by_orgId(orgId)
                subordinate_org_ids = []
                if departments_response.get('success') and departments_response.get('data'):
                    subordinate_org_ids = extract_department_ids(departments_response['data'])
                    if subordinate_org_ids:
                        sub_messages = base_query.filter(
                            DeviceMessage.org_id.in_([str(id) for id in subordinate_org_ids])
                        ).all()
                        all_messages.extend(sub_messages)
                        print(f"📊 包含子部门消息，总计 {len(all_messages)} 条")
            except Exception as e:
                print(f"⚠️ 获取子部门消息失败: {e}")
            
            # 3. 分离公告消息和个人消息
            announcement_messages = [msg for msg in all_messages if not msg.user_id]
            personal_messages = [msg for msg in all_messages if msg.user_id]
            
            print(f"📊 公告消息: {len(announcement_messages)} 条，个人消息: {len(personal_messages)} 条")

        # 🚀 优化：批量预加载组织信息，消除N+1查询问题！
        def get_org_info_batch(messages):
            """批量获取组织信息，避免N+1查询"""
            org_ids = list(set(str(msg.org_id) for msg in messages if msg.org_id))
            if not org_ids:
                return {}
            
            orgs = OrgInfo.query.filter(OrgInfo.id.in_(org_ids)).all()
            return {str(org.id): org.name for org in orgs}
        
        # 处理消息并添加到结果列表
        def process_messages(messages, is_public=False):
            # 🎉 批量预加载组织信息，一次查询解决所有消息的组织名称！
            org_info_cache = get_org_info_batch(messages)
            
            for msg in messages:
                #print("process_messages.sg:", msg)
                if msg.id not in seen_message_ids:
                    status = msg.message_status
                    if userId and status == '1':
                        user_info = UserInfo.query.filter_by(id=userId).first()
                        device_sn = user_info.device_sn
                        existing_detail = DeviceMessageDetail.query.filter_by(
                            message_id=msg.id,
                            device_sn=device_sn
                        ).first()
                        #print("process_messages.existing_detail:", existing_detail)
                        if existing_detail:
                            # 如果存在，则更新received_time
                            status = '2'
                    seen_message_ids.add(msg.id)
                    dept_id = str(msg.org_id)  # 修改: department_info -> org_id
                    # 🎉 从缓存中获取组织名称，无需每次查询数据库！
                    dept_name = org_info_cache.get(dept_id, 'Unknown Department')
                    message_dict = {
                        'department_name': dept_name,
                        'department_id': dept_id,
                        'message_id': str(msg.id),
                        'device_sn': msg.device_sn,
                        'user_id': str(msg.user_id) if msg.user_id else None,
                        'user_name': msg.user_name,
                        'message': msg.message,
                        'message_type': msg.message_type,
                        'message_status': status,
                        'sent_time': msg.sent_time.strftime("%Y-%m-%d %H:%M:%S") if msg.sent_time else None,
                        'received_time': msg.received_time.strftime("%Y-%m-%d %H:%M:%S") if msg.received_time else None,
                        'sender_type': msg.sender_type,
                        'receiver_type': msg.receiver_type,
                        'is_public': is_public
                    }
                    result_list.append(message_dict)

        # 处理所有获取到的消息
        if userId:
            process_messages(personal_messages, False)
            process_messages(announcement_messages, True)
        else:
            process_messages(announcement_messages, True)
            process_messages(personal_messages, False)

        # 计算统计信息
        total_messages = len(result_list)
        message_type_count = {}
        message_status_count = {}
        department_message_count = {}
        
        for msg in result_list:
            dept_name = msg['department_name']
            department_message_count[dept_name] = department_message_count.get(dept_name, 0) + 1
            message_type_count[msg['message_type']] = message_type_count.get(msg['message_type'], 0) + 1
            message_status_count[msg['message_status']] = message_status_count.get(msg['message_status'], 0) + 1

        print(f"DEBUG: 最终处理的消息总数: {total_messages}")
        print(f"DEBUG: 消息类型统计: {message_type_count}")
        print(f"DEBUG: 消息状态统计: {message_status_count}")
        print(f"DEBUG: 部门消息统计: {department_message_count}")
        
        response_data = {
            'success': True,
            'data': {
                'messages': result_list,
                'totalMessages': total_messages,
                'publicMessagesCount': len([msg for msg in result_list if msg['is_public']]),
                'personalMessagesCount': len([msg for msg in result_list if not msg['is_public']]),
                'uniqueMessageTypes': len(message_type_count),
                'departmentMessageCount': department_message_count,
                'messageTypeCount': message_type_count,
                'messageStatusCount': message_status_count,
                'departments': list(department_message_count.keys()),
                'user_id': str(userId) if userId else None
            }
        }

        # 缓存到Redis
        if result_list:
            cache_key = f"department_user_messages:{orgId}:{userId}"
            mapping = {msg['message_id']: json.dumps(msg) for msg in result_list}
            redis.hset(cache_key, mapping=mapping)
            redis.publish(f"{cache_key}_channel", json.dumps(result_list))

        return response_data

    except Exception as e:
        print("Error in fetch_messages_by_orgIdAndUserId:", str(e))
        return {
            'success': False,
            'error': str(e)
        }


def get_user_message(deviceSn):
    if not deviceSn:
        print("Error: deviceSn is None")
        return None

    # Query the DeviceMessage table to get messages for the given deviceSn
    messages = DeviceMessage.query.filter_by(device_sn=deviceSn).all()
    
    # Convert the messages to a list of dictionaries
    message_list = [{
        'message': message.message,
        'message_type': message.message_type,
        'message_status': message.message_status,
        'sent_time': message.sent_time.strftime("%Y-%m-%d %H:%M:%S") if message.sent_time else None,
        'received_time': message.received_time.strftime("%Y-%m-%d %H:%M:%S") if message.received_time else None
    } for message in messages]
    
    # Convert the message list to a JSON string
    message_json = json.dumps(message_list)
    print("message_json", message_json)
    
    if message_json is None:
        print("Error: message_json is None")
        return None
    
    # Check the type of the key and delete if necessary
    if redis.exists(f"message_info:{deviceSn}"):
        if redis.type(f"message_info:{deviceSn}") != b'hash':
            redis.delete(f"message_info:{deviceSn}")
    
    # Store the JSON string in Redis as a single field
    redis.set(f"message_info:{deviceSn}", message_json)
    
    redis.publish(f"message_info_channel:{deviceSn}", message_json) 
    
    return message_json


# =============================================================================
# 设备消息管理功能 (Device Message Management Functions)
# =============================================================================

def save_device_message_data(data):
    """保存设备消息数据"""
    try:
        print("save_message::data", data)

        # 创建新的消息记录
        new_message = DeviceMessage(
            message=data.get('message'),
            message_type=data.get('message_type'),
            sender_type=data.get('sender_type'),
            receiver_type=data.get('receiver_type'),
            message_status=data.get('message_status'),
            org_id=data.get('org_id') or data.get('department_info'),  # 修改: department_info -> org_id, 向后兼容
            user_id=data.get('user_id'),
            sent_time=datetime.now()
        )

        db.session.add(new_message)
        db.session.commit()

        return {
            'success': True,
            'message': '消息发送成功'
        }, 200
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'发送消息失败: {str(e)}'
        }, 500


def send_device_message_data(data):
    """发送设备消息数据"""
    try:
        # 记录消息发送日志
        device_logger.info('设备消息发送', extra={
            'message_type': data.get('message_type'),
            'receiver_type': data.get('receiver_type'),
            'user_id': data.get('user_id'),
            'data_count': 1
        })
        
        return send_message(data)
    except Exception as e:
        device_logger.error('设备消息发送失败', extra={'error': str(e)}, exc_info=True)
        raise


def receive_device_messages_data(deviceSn):
    """接收设备消息数据"""
    try:
        # 记录消息接收日志
        device_logger.info('设备消息查询', extra={'device_sn': deviceSn})
        
        result = received_messages(deviceSn)
        
        # 记录查询结果
        if hasattr(result, 'get_json'):
            result_data = result.get_json()
            if isinstance(result_data, dict) and 'data' in result_data:
                message_count = len(result_data['data']) if isinstance(result_data['data'], list) else 1
                device_logger.info('设备消息查询完成', extra={'device_sn': deviceSn, 'message_count': message_count})
        
        return result
    except Exception as e:
        device_logger.error('设备消息查询失败', extra={'device_sn': deviceSn, 'error': str(e)}, exc_info=True)
        raise

