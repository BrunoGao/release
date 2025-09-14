import json
from flask import request, jsonify
from .models import DeviceMessage, DeviceMessageDetail, DeviceMessageV2, DeviceMessageDetailV2, db, DeviceInfo, UserInfo, UserOrg, OrgInfo
from .redis_helper import RedisHelper
from datetime import datetime, timedelta
from .org import fetch_departments_by_orgId
from typing import List, Dict, Optional, Tuple
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from functools import wraps

# 导入日志配置
try:
    from .logging_config import device_logger
except ImportError:
    device_logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
redis = RedisHelper()

# 导入修复后的V2组件
try:
    from services.message_service_v2_fixed import MessageServiceV2Fixed, MessageServiceConfig
    from models.message_v2_fixed_model import (
        TDeviceMessageV2Fixed, MessageTypeEnum, MessageStatusEnum, 
        DeliveryStatusEnum, UrgencyEnum
    )
    from core.distributed_transaction_manager import (
        DistributedTransactionManager, TransactionStep
    )
    from monitoring.message_monitoring import (
        MessageSystemMetrics, monitor_api_request, monitor_database_query
    )
    V2_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"V2组件未可用，回退到V1实现: {e}")
    V2_COMPONENTS_AVAILABLE = False

# 线程池用于并发操作
executor = ThreadPoolExecutor(max_workers=10)

# 表版本检测和切换
def check_table_version():
    """检查数据库中存在哪个版本的消息表"""
    try:
        # 检查 V2 表是否存在
        db.session.execute(db.text("SELECT 1 FROM t_device_message_v2 LIMIT 1"))
        return 'v2'
    except Exception as e:
        logger.debug(f"V2表不存在，使用V1表: {e}")
        return 'v1'

def get_message_model():
    """获取当前应使用的消息模型"""
    version = check_table_version()
    if version == 'v2':
        return DeviceMessageV2, DeviceMessageDetailV2
    return DeviceMessage, DeviceMessageDetail

def get_unified_message_query(orgId=None, userId=None, startDate=None, endDate=None, message_type=None):
    """
    创建统一的消息查询，自动适配V1和V2表结构
    
    Args:
        orgId: 组织ID
        userId: 用户ID  
        startDate: 开始日期
        endDate: 结束日期
        message_type: 消息类型
    
    Returns:
        sqlalchemy query object
    """
    MessageModel, MessageDetailModel = get_message_model()
    table_version = check_table_version()
    
    if table_version == 'v2':
        # V2表查询逻辑
        base_query = db.session.query(
            MessageModel.id,
            MessageModel.message,
            MessageModel.message_type,
            MessageModel.sender_type,
            MessageModel.receiver_type,
            MessageModel.message_status,
            MessageModel.sent_time,
            MessageModel.received_time,
            MessageModel.acknowledged_time,
            MessageModel.user_id,
            MessageModel.department_id.label('org_id'),  # V2表使用department_id
            MessageModel.acknowledged_count.label('responded_number'),
            MessageModel.target_user_count.label('total_number'),
            UserInfo.user_name,
            OrgInfo.name.label('org_name')
        ).outerjoin(
            UserInfo, MessageModel.user_id == UserInfo.id
        ).outerjoin(
            OrgInfo, MessageModel.department_id == OrgInfo.id
        ).filter(
            MessageModel.is_deleted == False
        )
        
        # V2表的时间字段映射
        time_field = MessageModel.sent_time
        
        if userId:
            # V2表的用户查询
            user_info = UserInfo.query.filter_by(id=userId).first()
            if user_info and user_info.org_id:
                org_id = user_info.org_id
                base_query = base_query.filter(
                    db.or_(
                        MessageModel.user_id == userId,  # 个人消息
                        db.and_(MessageModel.department_id == org_id, MessageModel.receiver_type == 'department')  # 部门消息
                    )
                )
            else:
                base_query = base_query.filter(MessageModel.user_id == userId)
                
        elif orgId:
            # V2表的组织查询
            base_query = base_query.filter(
                db.or_(
                    MessageModel.department_id == orgId,  # 直接部门消息
                    db.and_(MessageModel.receiver_type == 'broadcast')  # 广播消息
                )
            )
    else:
        # V1表查询逻辑（保持原有逻辑）
        base_query = db.session.query(
            MessageModel.id,
            MessageModel.message,
            MessageModel.message_type,
            MessageModel.sender_type,
            MessageModel.receiver_type,
            MessageModel.message_status,
            MessageModel.sent_time,
            MessageModel.received_time,
            MessageModel.user_id,
            MessageModel.org_id,
            MessageModel.responded_number,
            db.literal(0).label('total_number'),  # V1表没有total_number字段
            UserInfo.user_name,
            OrgInfo.name.label('org_name')
        ).outerjoin(
            UserInfo, MessageModel.user_id == UserInfo.id
        ).outerjoin(
            OrgInfo, MessageModel.org_id == OrgInfo.id
        ).filter(
            MessageModel.is_deleted == False
        )
        
        # V1表的时间字段映射
        time_field = MessageModel.sent_time
        
        if userId:
            # V1表的用户查询逻辑
            user_info = UserInfo.query.filter_by(id=userId).first()
            if user_info and user_info.org_id:
                org_id = user_info.org_id
                org_info = OrgInfo.query.filter_by(id=org_id).first()
                if org_info and org_info.ancestors:
                    ancestor_org_ids = [int(id) for id in org_info.ancestors.split(',') if id != '0']
                    ancestor_org_ids.append(org_id)
                else:
                    ancestor_org_ids = [org_id] if org_id else []
                
                base_query = base_query.filter(
                    db.or_(
                        MessageModel.user_id == userId,  # 个人消息
                        db.and_(MessageModel.org_id.in_(ancestor_org_ids), MessageModel.user_id.is_(None))  # 公告消息
                    )
                )
            else:
                base_query = base_query.filter(MessageModel.user_id == userId)
                
        elif orgId:
            # V1表的组织查询逻辑
            from .org import fetch_users_by_orgId, fetch_departments_by_orgId
            
            users = fetch_users_by_orgId(orgId)
            user_ids = [int(user['id']) for user in users] if users else []
            
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
            
            if user_ids:
                base_query = base_query.filter(
                    db.or_(
                        MessageModel.user_id.in_(user_ids),  # 用户消息
                        db.and_(MessageModel.org_id.in_(all_org_ids), MessageModel.user_id.is_(None))  # 群发消息
                    )
                )
            else:
                base_query = base_query.filter(
                    db.and_(MessageModel.org_id.in_(all_org_ids), MessageModel.user_id.is_(None))
                )
    
    # 通用过滤条件
    if startDate:
        base_query = base_query.filter(time_field >= startDate)
    if endDate:
        base_query = base_query.filter(time_field <= endDate)
    if message_type:
        base_query = base_query.filter(MessageModel.message_type == message_type)
    
    return base_query, table_version

# 性能监控装饰器
def monitor_performance(operation_name: str):
    """性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                logger.info(f"📊 {operation_name} 耗时: {duration:.2f}ms")
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(f"❌ {operation_name} 失败: {e}, 耗时: {duration:.2f}ms")
                raise
        return wrapper
    return decorator

@monitor_performance("get_all_message_data_optimized")
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
        
        # 缓存检查（V2增强）
        cached = redis.get_data(cache_key)
        if cached:
            result = json.loads(cached)
            result['performance'] = {
                'cached': True, 
                'response_time': round(time.time() - start_time, 3),
                'cache_key': cache_key,
                'version': 'v2-enhanced'
            }
            logger.debug(f"✅ 缓存命中: {cache_key}")
            return result
        
        # 使用统一查询逻辑
        query, table_version = get_unified_message_query(
            orgId=orgId if not userId else None, 
            userId=userId,
            startDate=startDate, 
            endDate=endDate, 
            message_type=message_type
        )
        
        # 管理员用户检查
        if userId:
            from .admin_helper import is_admin_user
            if is_admin_user(userId):
                return {"success": True, "data": {"messageData": [], "totalRecords": 0, "pagination": {"currentPage": page, "pageSize": pageSize, "totalCount": 0, "totalPages": 0}}}
                
        # 检查是否有有效查询条件
        if not userId and not orgId:
            return {"success": False, "message": "缺少orgId或userId参数", "data": {"messageData": [], "totalRecords": 0}}
        
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
        
        # 格式化数据 - 兼容V1和V2表结构
        message_data_list = []
        for message in messages:
            # 处理时间字段 - V2可能有毫秒精度
            def format_time(time_obj):
                if not time_obj:
                    return None
                if table_version == 'v2':
                    # V2表支持毫秒精度
                    return time_obj.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if hasattr(time_obj, 'microsecond') else time_obj.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # V1表标准格式
                    return time_obj.strftime('%Y-%m-%d %H:%M:%S')
            
            message_dict = {
                'id': message.id,
                'message': message.message,
                'message_type': message.message_type,
                'sender_type': message.sender_type,
                'receiver_type': message.receiver_type,
                'message_status': message.message_status,
                'send_time': format_time(message.sent_time),
                'received_time': format_time(message.received_time),
                'user_id': message.user_id,
                'org_id': message.org_id,
                'responded_number': getattr(message, 'responded_number', 0) or 0,
                'total_number': getattr(message, 'total_number', 0) or 0,
                'user_name': message.user_name,
                'org_name': message.org_name,
                'dept_name': message.org_name,  # 兼容字段
                'dept_id': message.org_id
            }
            
            # V2表特有字段
            if table_version == 'v2':
                if hasattr(message, 'acknowledged_time'):
                    message_dict['acknowledged_time'] = format_time(message.acknowledged_time)
                if hasattr(message, 'priority_level'):
                    message_dict['priority_level'] = getattr(message, 'priority_level', 3)
            
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
            'metadata': {
                'table_version': table_version,
                'query_type': 'unified',
                'supports_microseconds': table_version == 'v2',
                'supports_priority': table_version == 'v2'
            },
            'performance': {
                'cached': False,
                'response_time': round(time.time() - start_time, 3),
                'query_time': round(time.time() - start_time, 3)
            }
        }
        
        # 缓存结果（V2优化TTL策略）
        cache_ttl = 300  # 默认5分钟
        if latest_only:
            cache_ttl = 60   # 最新数据1分钟缓存
        elif pageSize and pageSize <= 20:
            cache_ttl = 180  # 小分页3分钟缓存
        
        redis.set_data(cache_key, json.dumps(result, default=str), cache_ttl)
        logger.debug(f"✅ 缓存设置: {cache_key}, TTL: {cache_ttl}s")
        
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

# V2增强：全局实例和性能监控
_message_service_instance = None
_message_service_v2_instance = None
_monitoring_instance = None

@monitor_performance("get_unified_message_service")
def get_unified_message_service() -> MessageService:
    """获取统一消息服务实例"""
    global _message_service_instance
    if _message_service_instance is None:
        _message_service_instance = MessageService()
        logger.info("✅ 统一消息服务实例创建完成")
    return _message_service_instance

def get_v2_message_service():
    """V2增强：获取V2消息服务实例（如果可用）"""
    global _message_service_v2_instance
    
    if not V2_COMPONENTS_AVAILABLE:
        logger.warning("V2组件不可用，返回None")
        return None
    
    if _message_service_v2_instance is None:
        try:
            from services.message_service_v2_fixed import MessageServiceV2Fixed
            _message_service_v2_instance = MessageServiceV2Fixed()
            logger.info("✅ V2消息服务实例创建完成")
        except Exception as e:
            logger.error(f"❌ V2消息服务实例创建失败: {e}")
            return None
    
    return _message_service_v2_instance

def get_monitoring_instance():
    """V2增强：获取监控实例（如果可用）"""
    global _monitoring_instance
    
    if not V2_COMPONENTS_AVAILABLE:
        return None
    
    if _monitoring_instance is None:
        try:
            from monitoring.message_monitoring import MessageSystemMonitor
            _monitoring_instance = MessageSystemMonitor()
            _monitoring_instance.start()
            logger.info("✅ 消息系统监控实例创建完成")
        except Exception as e:
            logger.error(f"❌ 监控实例创建失败: {e}")
            return None
    
    return _monitoring_instance

# V2增强：性能缓存管理器
class MessageCacheManager:
    """V2增强消息缓存管理器"""
    
    def __init__(self):
        self.redis = redis
        self.cache_prefix = "message_v2_cache"
    
    def get_cache_key(self, operation: str, **params) -> str:
        """生成缓存键"""
        param_str = ":".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
        return f"{self.cache_prefix}:{operation}:{param_str}"
    
    def get_with_fallback(self, cache_key: str, fallback_func: callable, ttl: int = 300, **kwargs):
        """缓存获取与回退机制"""
        try:
            # 尝试从缓存获取
            cached_data = self.redis.get_data(cache_key)
            if cached_data:
                logger.debug(f"缓存命中: {cache_key}")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"缓存读取失败: {e}")
        
        # 缓存未命中，执行回退函数
        try:
            result = fallback_func(**kwargs)
            
            # 缓存结果
            try:
                self.redis.set_data(cache_key, json.dumps(result, default=str), ttl)
                logger.debug(f"缓存设置成功: {cache_key}, TTL: {ttl}s")
            except Exception as e:
                logger.warning(f"缓存设置失败: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"回退函数执行失败: {e}")
            # 返回空结果而不是异常
            return {
                'success': False,
                'error': str(e),
                'data': {'messages': [], 'total_count': 0}
            }
    
    def invalidate_pattern(self, pattern: str):
        """根据模式清理缓存"""
        try:
            keys = self.redis.keys(f"{self.cache_prefix}:{pattern}")
            if keys:
                self.redis.delete(*keys)
                logger.debug(f"缓存清理完成: {len(keys)} 个键")
        except Exception as e:
            logger.warning(f"缓存清理失败: {pattern}, 错误: {e}")

# V2增强：全局缓存管理器实例
_cache_manager_instance = None

def get_cache_manager() -> MessageCacheManager:
    """获取缓存管理器实例"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = MessageCacheManager()
        logger.info("✅ 消息缓存管理器实例创建完成")
    return _cache_manager_instance

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
@monitor_performance("send_message_enhanced")
def send_message(data):
    """
    V2增强版消息发送处理
    支持分布式事务和性能监控
    """
    logger.info("DeviceMessage:send_message V2", data)
    
    # V2增强：创建事务管理器
    transaction_manager = None
    if V2_COMPONENTS_AVAILABLE:
        try:
            transaction_manager = DistributedTransactionManager()
            transaction_id = transaction_manager.start_transaction({
                'operation': 'send_message',
                'message_id': data.get('message_id'),
                'device_sn': data.get('device_sn')
            })
        except Exception as e:
            logger.warning(f"分布式事务初始化失败，使用传统模式: {e}")
    
    # 数据验证增强
    required_fields = ['department_id','message_id', 'message', 'device_sn', 'received_time', 'user_id']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        error_msg = f"Missing required fields: {missing_fields}"
        logger.error(error_msg)
        return jsonify({"status": "error", "message": error_msg}), 400

    message_id = data.get('message_id')
    device_sn = data.get('device_sn')
    
    # V2增强：缓存检查
    cache_key = f"message_send_lock:{message_id}:{device_sn}"
    if redis.exists(cache_key):
        logger.warning(f"重复消息发送请求被拒绝: {message_id}:{device_sn}")
        return jsonify({"status": "error", "message": "Duplicate message processing"}), 409
    
    try:
        # 设置处理锁（5分钟过期）
        redis.setex(cache_key, 300, "processing")
        
        # 获取合适的模型
        MessageModel, MessageDetailModel = get_message_model()
        table_version = check_table_version()
        
        if message_id:
            message = MessageModel.query.get(message_id)
            logger.debug(f"查询到消息: {message}")
            
            if message:
                # V2增强：并发安全的消息处理
                with db.session.begin():
                    # 检查是否为广播/群发消息 - V1和V2表结构不同
                    is_broadcast = False
                    if table_version == 'v2':
                        is_broadcast = (message.receiver_type == 'broadcast' or message.receiver_type == 'department')
                    else:
                        is_broadcast = (message.user_id is None)
                    
                    if is_broadcast:
                        # 群发消息处理
                        logger.info("处理群发消息")
                        existing_detail = MessageDetailModel.query.filter_by(
                            message_id=message_id,
                            device_sn=device_sn
                        ).first()
                        
                        if not existing_detail:
                            # V2增强：使用批量插入优化
                            detail_data = {
                                'message_id': message_id,
                                'device_sn': device_sn
                            }
                            
                            if table_version == 'v2':
                                # V2表结构
                                detail_data.update({
                                    'customer_id': getattr(message, 'customer_id', 1),
                                    'user_id': data.get('user_id', 0),
                                    'response_message': data.get('message', ''),
                                    'response_type': 'acknowledged',
                                    'response_time': datetime.now(),
                                    'delivery_status': 'delivered'
                                })
                            else:
                                # V1表结构
                                detail_data.update({
                                    'message': data['message'],
                                    'message_type': data.get('message_type', 'notification'),
                                    'sender_type': data.get('sender_type', 'device'),
                                    'receiver_type': data.get('receiver_type', 'platform'),
                                    'message_status': data.get('message_status', '2')
                                })
                            
                            message_detail = MessageDetailModel(**detail_data)
                            db.session.add(message_detail)
                            
                            # 原子性增加响应计数
                            if table_version == 'v2':
                                message.acknowledged_count = (message.acknowledged_count or 0) + 1
                            else:
                                message.responded_number = (message.responded_number or 0) + 1
                            
                            # V2增强：记录消息生命周期
                            if V2_COMPONENTS_AVAILABLE:
                                try:
                                    lifecycle_event = {
                                        'message_id': message_id,
                                        'device_sn': device_sn,
                                        'event_type': 'acknowledged',
                                        'event_time': datetime.now(),
                                        'metadata': {'response_time': data.get('received_time')}
                                    }
                                    # 记录到Redis流用于后续处理
                                    redis.xadd('message_lifecycle_stream', lifecycle_event)
                                except Exception as e:
                                    logger.warning(f"生命周期记录失败: {e}")
                    else:
                        # 个人消息处理
                        logger.info("处理个人消息")
                        user = UserInfo.query.filter_by(id=message.user_id, is_deleted=0).first()
                        
                        if user and user.device_sn == device_sn:
                            # 更新消息状态
                            if table_version == 'v2':
                                message.message_status = 'acknowledged'  # V2使用枚举值
                                message.acknowledged_time = datetime.now()
                            else:
                                message.message_status = '2'  # V1使用字符串
                            
                            # 检查是否已存在响应记录
                            existing_detail = MessageDetailModel.query.filter_by(
                                message_id=message_id,
                                device_sn=device_sn
                            ).first()
                            
                            if not existing_detail:
                                detail_data = {
                                    'message_id': message_id,
                                    'device_sn': device_sn
                                }
                                
                                if table_version == 'v2':
                                    # V2表结构
                                    detail_data.update({
                                        'customer_id': getattr(message, 'customer_id', 1),
                                        'user_id': message.user_id,
                                        'response_message': data.get('message', ''),
                                        'response_type': 'acknowledged',
                                        'response_time': datetime.now(),
                                        'delivery_status': 'delivered'
                                    })
                                else:
                                    # V1表结构
                                    detail_data.update({
                                        'message': data['message'],
                                        'message_type': data.get('message_type', 'notification'),
                                        'sender_type': data.get('sender_type', 'device'),
                                        'receiver_type': data.get('receiver_type', 'platform'),
                                        'message_status': '2'
                                    })
                                
                                message_detail = MessageDetailModel(**detail_data)
                                db.session.add(message_detail)
                    
                    # 更新接收时间
                    message.received_time = data['received_time']
                    
                # V2增强：清理相关缓存
                cache_keys_to_delete = [
                    f"message_opt_v1:*:{message.user_id}:*",
                    f"message_opt_v1:{message.org_id}:*:*",
                    f"department_user_messages:{message.org_id}:{message.user_id}"
                ]
                
                for pattern in cache_keys_to_delete:
                    try:
                        keys = redis.keys(pattern)
                        if keys:
                            redis.delete(*keys)
                    except Exception as e:
                        logger.warning(f"缓存清理失败: {pattern}, 错误: {e}")
                
                # V2增强：完成分布式事务
                if transaction_manager:
                    try:
                        transaction_manager.commit_transaction(transaction_id)
                    except Exception as e:
                        logger.warning(f"分布式事务提交失败: {e}")
                
                logger.info(f"消息处理完成: {message.id}")
                return jsonify({"status": "success", "message": "数据已接收并处理", "id": message.id}), 200
            else:
                return jsonify({"status": "error", "message": "Message not found"}), 404
        else:
            logger.error("数据有误，手表回复了不存在的消息")
            return jsonify({"status": "error", "message": "数据有误，手表回复了不存在的消息"}), 400
            
    except Exception as e:
        logger.error(f"消息发送处理异常: {e}", exc_info=True)
        
        # V2增强：事务回滚
        if transaction_manager:
            try:
                transaction_manager.rollback_transaction(transaction_id, str(e))
            except Exception as rollback_e:
                logger.error(f"事务回滚失败: {rollback_e}")
        
        return jsonify({"status": "error", "message": f"处理异常: {str(e)}"}), 500
    finally:
        # 清理处理锁
        try:
            redis.delete(cache_key)
        except Exception as e:
            logger.warning(f"清理处理锁失败: {e}")
    
@monitor_performance("received_messages_enhanced")
def received_messages(device_sn):
    """
    V2增强版消息接收处理
    优化缓存策略和数据库查询性能
    """
    if not device_sn:
        return {"success": False, "error": "device_sn is required"}
    
    # V2增强：智能缓存策略
    cache_key = f"received_messages_v2:{device_sn}"
    
    try:
        # 尝试从缓存获取
        cached_result = redis.get_data(cache_key)
        if cached_result:
            logger.debug(f"缓存命中: {cache_key}")
            return json.loads(cached_result)
    except Exception as e:
        logger.warning(f"缓存读取失败: {e}")
    
    try:
        # 1. V2增强：优化用户查询
        user = UserInfo.query.filter_by(
            device_sn=device_sn, 
            is_deleted=0
        ).with_entities(UserInfo.id, UserInfo.org_id, UserInfo.user_name).first()
        
        if not user:
            error_result = {"success": False, "error": "未找到对应的用户"}
            # 缓存错误结果30秒
            redis.setex(cache_key, 30, json.dumps(error_result))
            return error_result

        user_id = user.id
        logger.debug(f"用户信息: user_id={user_id}, org_id={user.org_id}")

        # 2. V2增强：使用优化的消息查询接口
        resp = get_all_message_data_optimized(
            userId=user_id,
            latest_only=False,
            page=1,
            pageSize=50,  # 限制返回数量提高性能
            include_details=False
        )
        
        if not resp.get("success", True):
            return {"success": False, "error": "获取消息失败"}

        # 3. V2增强：智能数据解析
        raw_data = resp.get("data", {})
        messages = raw_data.get("messageData", [])
        
        # 4. V2增强：高效过滤算法
        # 一次性获取所有相关的DeviceMessageDetail - 使用统一模型
        MessageModel, MessageDetailModel = get_message_model()
        table_version = check_table_version()
        
        message_ids = [str(m.get("id", m.get("message_id", ""))) for m in messages if m.get("id") or m.get("message_id")]
        
        acknowledged_message_ids = set()
        if message_ids:
            try:
                acknowledged_details = MessageDetailModel.query.filter(
                    MessageDetailModel.message_id.in_(message_ids),
                    MessageDetailModel.device_sn == device_sn
                ).with_entities(MessageDetailModel.message_id).all()
                
                acknowledged_message_ids = {str(detail.message_id) for detail in acknowledged_details}
                logger.debug(f"已确认消息IDs: {acknowledged_message_ids}")
            except Exception as e:
                logger.warning(f"查询已确认消息失败: {e}")
        
        # 5. V2增强：智能过滤策略 - 手表端专用优化
        filtered_messages = []
        for msg in messages:
            msg_id = str(msg.get("id", msg.get("message_id", "")))
            msg_status = msg.get("message_status", "")
            
            # 过滤条件：
            # 1. 消息状态不是已响应
            # 2. 没有在DeviceMessageDetail中找到确认记录
            if (msg_status not in ("2", "responded", "acknowledged") and 
                msg_id not in acknowledged_message_ids):
                
                # V2增强：数据清洗和格式化 - 手表端优化
                message_content = msg.get('message', '')
                
                # 手表端消息内容优化 - 限制长度和格式化
                if len(message_content) > 200:
                    message_content = message_content[:197] + "..."
                
                # 计算消息优先级（手表端显示顺序）
                priority = calculate_message_priority(msg.get('message_type'), msg.get('send_time'))
                
                cleaned_msg = {
                    'message_id': msg_id,
                    'department_id': msg.get('dept_id', msg.get('org_id', '')),
                    'department_name': msg.get('dept_name', msg.get('org_name', '')),
                    'user_id': msg.get('user_id'),
                    'user_name': msg.get('user_name'),
                    'message': message_content,
                    'message_type': msg.get('message_type', 'notification'),
                    'message_status': msg_status,
                    'send_time': msg.get('send_time'),
                    'sender_type': msg.get('sender_type', 'system'),
                    'receiver_type': msg.get('receiver_type', 'device'),
                    'is_public': msg.get('is_public', False),
                    'priority': priority,  # 手表端优先级
                    'watch_display': {
                        'title': get_message_title_for_watch(msg.get('message_type')),
                        'icon': get_message_icon_for_watch(msg.get('message_type')),
                        'vibration_pattern': get_vibration_pattern(msg.get('message_type'))
                    }
                }
                filtered_messages.append(cleaned_msg)
        
        # 手表端消息排序 - 按优先级和时间排序
        filtered_messages.sort(key=lambda x: (x['priority'], x['send_time']), reverse=True)
        
        # 6. V2增强：构建结果
        result = {
            "success": True,
            "data": {
                "messages": filtered_messages,
                "total_count": len(filtered_messages),
                "user_info": {
                    "user_id": user_id,
                    "user_name": user.user_name,
                    "org_id": user.org_id
                },
                "device_sn": device_sn,
                "timestamp": datetime.now().isoformat(),
                "version": "v2-enhanced"
            }
        }
        
        # V2增强：智能缓存TTL策略
        cache_ttl = 60  # 默认缓存1分钟
        if len(filtered_messages) == 0:
            cache_ttl = 30  # 空结果短缓存
        elif len(filtered_messages) > 10:
            cache_ttl = 90  # 大量消息长缓存
        
        try:
            redis.setex(cache_key, cache_ttl, json.dumps(result, default=str))
            logger.debug(f"缓存设置成功: {cache_key}, TTL: {cache_ttl}s")
        except Exception as e:
            logger.warning(f"缓存设置失败: {e}")
        
        logger.info(f"消息接收处理完成: device_sn={device_sn}, 过滤后消息数={len(filtered_messages)}")
        return result
        
    except Exception as e:
        logger.error(f"消息接收处理异常: {e}", exc_info=True)
        error_result = {
            "success": False, 
            "error": f"处理异常: {str(e)}",
            "data": {"messages": []}
        }
        
        # 错误结果也短时缓存，避免重复处理
        try:
            redis.setex(cache_key, 15, json.dumps(error_result))
        except:
            pass
            
        return error_result
    

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
    
@monitor_performance("generate_message_stats_enhanced")
def generate_message_stats(message_info):
    """
    V2增强版消息统计生成
    支持更丰富的统计数据和性能优化
    """
    if not message_info:
        return {
            'success': True,
            'messages': [],
            'totalMessages': 0,
            'uniqueMessageTypes': 0,
            'messageStatusCounts': {},
            'messageTypeCounts': {},
            'statistics': {
                'response_rate': 0.0,
                'avg_response_time': 0.0,
                'peak_hour': None,
                'distribution': {}
            }
        }
    
    try:
        start_time = time.time()
        
        # V2增强：并行统计计算
        total_messages = len(message_info)
        message_status_counts = {}
        message_type_counts = {}
        
        # V2增强：时间分布统计
        hourly_distribution = {}
        response_times = []
        responded_count = 0
        
        # V2增强：部门统计
        department_stats = {}
        user_stats = {}
        
        for message in message_info:
            # 状态统计
            status = message.get('message_status', 'unknown')
            message_status_counts[status] = message_status_counts.get(status, 0) + 1
            
            # 类型统计
            msg_type = message.get('message_type', 'unknown')
            message_type_counts[msg_type] = message_type_counts.get(msg_type, 0) + 1
            
            # V2增强：时间分布统计
            send_time_str = message.get('send_time') or message.get('sent_time')
            if send_time_str:
                try:
                    if isinstance(send_time_str, str):
                        send_time = datetime.strptime(send_time_str[:19], '%Y-%m-%d %H:%M:%S')
                    else:
                        send_time = send_time_str
                    
                    hour_key = send_time.hour
                    hourly_distribution[hour_key] = hourly_distribution.get(hour_key, 0) + 1
                except Exception as e:
                    logger.warning(f"时间解析失败: {send_time_str}, 错误: {e}")
            
            # V2增强：响应时间统计
            if status in ['2', 'responded', 'acknowledged']:
                responded_count += 1
                
                sent_time = message.get('send_time') or message.get('sent_time')
                received_time = message.get('received_time')
                
                if sent_time and received_time:
                    try:
                        if isinstance(sent_time, str):
                            sent_dt = datetime.strptime(sent_time[:19], '%Y-%m-%d %H:%M:%S')
                        else:
                            sent_dt = sent_time
                            
                        if isinstance(received_time, str):
                            received_dt = datetime.strptime(received_time[:19], '%Y-%m-%d %H:%M:%S')
                        else:
                            received_dt = received_time
                        
                        response_time_seconds = (received_dt - sent_dt).total_seconds()
                        if response_time_seconds > 0:
                            response_times.append(response_time_seconds)
                    except Exception as e:
                        logger.warning(f"响应时间计算失败: {e}")
            
            # V2增强：部门和用户统计
            dept_name = message.get('department_name', message.get('org_name', '未知部门'))
            if dept_name not in department_stats:
                department_stats[dept_name] = {
                    'total': 0, 'pending': 0, 'responded': 0, 'failed': 0
                }
            
            department_stats[dept_name]['total'] += 1
            if status in ['1', 'pending']:
                department_stats[dept_name]['pending'] += 1
            elif status in ['2', 'responded', 'acknowledged']:
                department_stats[dept_name]['responded'] += 1
            elif status in ['failed', 'error']:
                department_stats[dept_name]['failed'] += 1
            
            # 用户统计
            user_name = message.get('user_name', '匿名用户')
            if user_name != '匿名用户':
                if user_name not in user_stats:
                    user_stats[user_name] = {'total': 0, 'responded': 0}
                user_stats[user_name]['total'] += 1
                if status in ['2', 'responded', 'acknowledged']:
                    user_stats[user_name]['responded'] += 1
        
        # V2增强：高级统计计算
        response_rate = (responded_count / max(total_messages, 1)) * 100
        avg_response_time = sum(response_times) / max(len(response_times), 1) if response_times else 0
        
        # 找出消息高峰时段
        peak_hour = max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None
        
        # 计算部门响应率
        for dept_name, stats in department_stats.items():
            if stats['total'] > 0:
                stats['response_rate'] = round((stats['responded'] / stats['total']) * 100, 2)
            else:
                stats['response_rate'] = 0.0
        
        # 计算用户响应率
        for user_name, stats in user_stats.items():
            if stats['total'] > 0:
                stats['response_rate'] = round((stats['responded'] / stats['total']) * 100, 2)
            else:
                stats['response_rate'] = 0.0
        
        unique_message_types = len(message_type_counts)
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        # V2增强：构建结果
        result = {
            'success': True,
            'messages': message_info,
            'totalMessages': total_messages,
            'uniqueMessageTypes': unique_message_types,
            'messageStatusCounts': message_status_counts,
            'messageTypeCounts': message_type_counts,
            
            # V2增强：高级统计
            'statistics': {
                'response_rate': round(response_rate, 2),
                'avg_response_time_seconds': round(avg_response_time, 2),
                'peak_hour': peak_hour,
                'hourly_distribution': hourly_distribution,
                'responded_count': responded_count,
                'pending_count': total_messages - responded_count,
                'response_time_distribution': {
                    'min': min(response_times) if response_times else 0,
                    'max': max(response_times) if response_times else 0,
                    'avg': avg_response_time
                }
            },
            
            # V2增强：组织和用户统计
            'department_statistics': department_stats,
            'user_statistics': dict(list(user_stats.items())[:10]),  # 只返回前10个用户
            
            # V2增强：元数据
            'metadata': {
                'processing_time_ms': processing_time,
                'version': 'v2-enhanced',
                'timestamp': datetime.now().isoformat(),
                'data_quality': {
                    'complete_messages': sum(1 for msg in message_info if msg.get('message') and msg.get('message_type')),
                    'incomplete_messages': sum(1 for msg in message_info if not (msg.get('message') and msg.get('message_type'))),
                    'with_timestamps': sum(1 for msg in message_info if msg.get('send_time') or msg.get('sent_time'))
                }
            }
        }
        
        logger.info(f"消息统计生成完成: 处理{total_messages}条消息, 耗时{processing_time}ms")
        return result
        
    except Exception as e:
        logger.error(f"消息统计生成异常: {e}", exc_info=True)
        return {
            'success': False, 
            'error': str(e),
            'error_type': type(e).__name__,
            'messages': message_info or [],
            'totalMessages': len(message_info) if message_info else 0
        }
    
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

@monitor_performance("fetch_messages_by_orgIdAndUserId_enhanced")
def fetch_messages_by_orgIdAndUserId(orgId, userId=None, messageType=None, customerId=None):
    """
    V2增强版消息列表获取
    优化数据库查询和缓存策略
    
    :param orgId: 组织ID
    :param userId: 用户ID，可选
    :param messageType: 消息类型，可选
    :param customerId: 客户ID，可选
    :return: 消息列表和统计信息
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

        # 添加customerId过滤
        if customerId:
            base_query = base_query.filter(DeviceMessage.customer_id == customerId)

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

@monitor_performance("save_device_message_data_enhanced")
def save_device_message_data(data):
    """
    V2增强版设备消息数据保存
    支持分布式事务和数据验证
    """
    logger.info("save_device_message_data V2", extra={'data_keys': list(data.keys()) if data else []})
    
    # V2增强：数据验证
    if not data:
        return {'success': False, 'message': '缺少消息数据'}, 400
    
    required_fields = ['message', 'message_type']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return {
            'success': False, 
            'message': f'缺少必要字段: {missing_fields}'
        }, 400
    
    # V2增强：创建事务管理器
    transaction_manager = None
    transaction_id = None
    
    if V2_COMPONENTS_AVAILABLE:
        try:
            transaction_manager = DistributedTransactionManager()
            transaction_id = transaction_manager.start_transaction({
                'operation': 'save_device_message',
                'message_type': data.get('message_type'),
                'user_id': data.get('user_id'),
                'org_id': data.get('org_id')
            })
        except Exception as e:
            logger.warning(f"分布式事务初始化失败: {e}")
    
    try:
        with db.session.begin():
            # V2增强：数据清洗和默认值处理
            now = datetime.now()
            
            message_data = {
                'message': data.get('message', '').strip(),
                'message_type': data.get('message_type', 'notification'),
                'sender_type': data.get('sender_type', 'system'),
                'receiver_type': data.get('receiver_type', 'device'),
                'message_status': data.get('message_status', '1'),  # 1=待发送
                'org_id': data.get('org_id') or data.get('department_info'),
                'user_id': data.get('user_id'),
                'sent_time': data.get('sent_time') or now,
                'create_time': now,
                'customer_id': data.get('customer_id', 1),  # 默认客户ID
                'is_deleted': False
            }
            
            # V2增强：批量消息支持
            if data.get('batch_send', False) and data.get('target_users'):
                # 批量发送处理
                target_users = data.get('target_users', [])
                batch_messages = []
                
                for user_data in target_users:
                    batch_message_data = message_data.copy()
                    batch_message_data.update({
                        'user_id': user_data.get('user_id'),
                        'device_sn': user_data.get('device_sn')
                    })
                    
                    new_message = DeviceMessage(**batch_message_data)
                    batch_messages.append(new_message)
                
                # V2增强：批量插入优化
                db.session.bulk_save_objects(batch_messages, return_defaults=True)
                
                message_count = len(batch_messages)
                logger.info(f"批量消息创建成功: {message_count}条")
                
                # V2增强：异步发送任务
                if V2_COMPONENTS_AVAILABLE:
                    try:
                        for message in batch_messages:
                            send_task = {
                                'message_id': message.id,
                                'message_type': message.message_type,
                                'target_device': message.device_sn,
                                'priority': data.get('priority', 'normal'),
                                'scheduled_time': data.get('scheduled_time')
                            }
                            redis.xadd('message_send_queue', send_task)
                    except Exception as e:
                        logger.warning(f"发送任务入队失败: {e}")
                
                result_data = {
                    'success': True,
                    'message': f'批量消息发送成功: {message_count}条',
                    'message_count': message_count,
                    'message_ids': [msg.id for msg in batch_messages]
                }
                
            else:
                # 单条消息处理
                new_message = DeviceMessage(**message_data)
                db.session.add(new_message)
                db.session.flush()  # 获取ID
                
                logger.info(f"单条消息创建成功: ID={new_message.id}")
                
                # V2增强：异步发送任务
                if V2_COMPONENTS_AVAILABLE:
                    try:
                        send_task = {
                            'message_id': new_message.id,
                            'message_type': new_message.message_type,
                            'target_device': data.get('device_sn', 'all'),
                            'priority': data.get('priority', 'normal'),
                            'scheduled_time': data.get('scheduled_time')
                        }
                        redis.xadd('message_send_queue', send_task)
                    except Exception as e:
                        logger.warning(f"发送任务入队失败: {e}")
                
                result_data = {
                    'success': True,
                    'message': '消息发送成功',
                    'message_id': new_message.id,
                    'message_type': new_message.message_type
                }
        
        # V2增强：清理相关缓存
        cache_patterns = [
            f"message_opt_v1:*:{data.get('user_id')}:*" if data.get('user_id') else None,
            f"message_opt_v1:{data.get('org_id')}:*:*" if data.get('org_id') else None,
            "received_messages_v2:*"  # 清理所有设备的接收消息缓存
        ]
        
        for pattern in cache_patterns:
            if pattern:
                try:
                    keys = redis.keys(pattern)
                    if keys:
                        redis.delete(*keys)
                except Exception as e:
                    logger.warning(f"缓存清理失败: {pattern}, 错误: {e}")
        
        # V2增强：提交分布式事务
        if transaction_manager and transaction_id:
            try:
                transaction_manager.commit_transaction(transaction_id)
            except Exception as e:
                logger.warning(f"分布式事务提交失败: {e}")
        
        return result_data, 200
        
    except Exception as e:
        logger.error(f"保存消息数据异常: {e}", exc_info=True)
        
        # V2增强：事务回滚
        try:
            db.session.rollback()
        except:
            pass
        
        if transaction_manager and transaction_id:
            try:
                transaction_manager.rollback_transaction(transaction_id, str(e))
            except Exception as rollback_e:
                logger.error(f"分布式事务回滚失败: {rollback_e}")
        
        return {
            'success': False,
            'message': f'发送消息失败: {str(e)}',
            'error_type': type(e).__name__
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


# =============================================================================
# V2增强版API接口 (V2 Enhanced API Endpoints)
# =============================================================================

@monitor_performance("get_message_health_status")
def get_message_health_status():
    """
    V2增强：获取消息系统健康状态
    """
    try:
        # 获取系统状态
        status = {
            'service': 'MessageSystem',
            'version': 'v2-enhanced',
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # 检查数据库连接
        try:
            db.session.execute(text('SELECT 1')).scalar()
            status['components']['database'] = {'status': 'healthy'}
        except Exception as e:
            status['components']['database'] = {'status': 'unhealthy', 'error': str(e)}
            status['status'] = 'degraded'
        
        # 检查Redis连接
        try:
            redis.ping()
            status['components']['redis'] = {'status': 'healthy'}
        except Exception as e:
            status['components']['redis'] = {'status': 'unhealthy', 'error': str(e)}
            status['status'] = 'degraded'
        
        # V2增强：检查V2组件
        if V2_COMPONENTS_AVAILABLE:
            v2_service = get_v2_message_service()
            monitoring = get_monitoring_instance()
            
            status['components']['v2_service'] = {
                'status': 'available' if v2_service else 'unavailable'
            }
            status['components']['monitoring'] = {
                'status': 'running' if monitoring else 'stopped'
            }
        else:
            status['components']['v2_enhancement'] = {'status': 'unavailable'}
        
        return status
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            'service': 'MessageSystem',
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@monitor_performance("get_message_performance_metrics")
def get_message_performance_metrics():
    """
    V2增强：获取消息系统性能指标
    """
    try:
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'version': 'v2-enhanced',
            'cache_stats': {},
            'database_stats': {},
            'message_stats': {},
            'performance': {}
        }
        
        # 缓存统计
        try:
            cache_info = redis.info('memory')
            metrics['cache_stats'] = {
                'used_memory': cache_info.get('used_memory', 0),
                'used_memory_human': cache_info.get('used_memory_human', '0B'),
                'hit_rate': 'N/A'  # 需要实际实现
            }
        except Exception as e:
            metrics['cache_stats'] = {'error': str(e)}
        
        # 数据库统计
        try:
            with db.session.begin():
                # 消息总数
                total_messages = db.session.execute(
                    text('SELECT COUNT(*) FROM t_device_message WHERE is_deleted = 0')
                ).scalar()
                
                # 未确认消息数
                pending_messages = db.session.execute(
                    text("SELECT COUNT(*) FROM t_device_message WHERE message_status = '1' AND is_deleted = 0")
                ).scalar()
                
                # 今日消息数
                today_messages = db.session.execute(
                    text('SELECT COUNT(*) FROM t_device_message WHERE DATE(sent_time) = CURDATE()')
                ).scalar()
                
                metrics['message_stats'] = {
                    'total_messages': total_messages,
                    'pending_messages': pending_messages,
                    'today_messages': today_messages,
                    'response_rate': round(((total_messages - pending_messages) / max(total_messages, 1)) * 100, 2)
                }
        except Exception as e:
            metrics['message_stats'] = {'error': str(e)}
        
        # V2增强：获取监控指标
        if V2_COMPONENTS_AVAILABLE:
            monitoring = get_monitoring_instance()
            if monitoring:
                try:
                    dashboard = monitoring.get_monitor_dashboard()
                    metrics['v2_monitoring'] = {
                        'active_alerts': len(dashboard.get('active_alerts', {})),
                        'health_status': dashboard.get('health', {}).get('status', 'unknown')
                    }
                except Exception as e:
                    metrics['v2_monitoring'] = {'error': str(e)}
        
        return metrics
        
    except Exception as e:
        logger.error(f"性能指标获取失败: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@monitor_performance("acknowledge_message_enhanced")
def acknowledge_message(data):
    """
    手机端消息确认API - 完善消息数据流的关键接口
    
    Args:
        data: 包含消息确认信息的字典
        {
            'message_id': 消息ID,
            'device_sn': 设备序列号,
            'user_id': 用户ID（可选），
            'acknowledgment_type': 确认类型 ('read', 'acknowledged', 'completed'),
            'acknowledgment_message': 确认回复内容（可选）,
            'location': {'latitude': xxx, 'longitude': xxx} # 位置信息（可选）
        }
    
    Returns:
        确认结果
    """
    logger.info("手机端消息确认请求", extra={'data': data})
    
    # 数据验证
    if not data:
        return {'success': False, 'message': '缺少确认数据'}, 400
        
    required_fields = ['message_id', 'device_sn']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return {
            'success': False, 
            'message': f'缺少必要字段: {missing_fields}'
        }, 400
    
    message_id = data.get('message_id')
    device_sn = data.get('device_sn')
    user_id = data.get('user_id')
    acknowledgment_type = data.get('acknowledgment_type', 'read')
    acknowledgment_message = data.get('acknowledgment_message', '')
    location = data.get('location', {})
    
    # 防重复确认的缓存键
    cache_key = f"message_ack_lock:{message_id}:{device_sn}"
    if redis.exists(cache_key):
        logger.warning(f"重复确认请求被拒绝: {message_id}:{device_sn}")
        return {'success': False, 'message': '消息已确认，请勿重复操作'}, 409
    
    try:
        # 设置处理锁（5分钟过期）
        redis.setex(cache_key, 300, "processing")
        
        # 查询原始消息
        message = DeviceMessage.query.get(message_id)
        if not message:
            return {'success': False, 'message': '消息不存在'}, 404
        
        # 验证设备权限（如果提供了user_id）
        if user_id:
            user = UserInfo.query.filter_by(id=user_id, device_sn=device_sn).first()
            if not user:
                return {'success': False, 'message': '设备权限验证失败'}, 403
        
        with db.session.begin():
            # 检查是否已存在确认记录
            existing_detail = DeviceMessageDetail.query.filter_by(
                message_id=message_id,
                device_sn=device_sn
            ).first()
            
            now = datetime.now()
            
            if existing_detail:
                # 更新现有确认记录
                existing_detail.message_status = '2' if acknowledgment_type == 'read' else 'acknowledged'
                existing_detail.received_time = now
                if acknowledgment_message:
                    existing_detail.message += f"\n[用户回复]: {acknowledgment_message}"
                logger.info(f"更新现有确认记录: {existing_detail.id}")
            else:
                # 创建新的确认记录
                message_detail = DeviceMessageDetail(
                    message_id=message_id,
                    device_sn=device_sn,
                    message=acknowledgment_message or f"[{acknowledgment_type}] 消息已确认",
                    message_type=message.message_type,
                    sender_type='device',
                    receiver_type='platform',
                    message_status='2' if acknowledgment_type == 'read' else 'acknowledged',
                    received_time=now
                )
                db.session.add(message_detail)
                logger.info(f"创建新确认记录: 消息ID={message_id}, 设备={device_sn}")
            
            # 更新原始消息状态
            if message.user_id:
                # 个人消息直接更新为已确认
                message.message_status = '2'
                message.received_time = now
            else:
                # 群发消息增加响应计数
                message.responded_number = (message.responded_number or 0) + 1
                message.received_time = now
                
                # 如果有总数设置，检查是否全部确认
                if message.total_number and message.responded_number >= message.total_number:
                    message.message_status = '2'  # 全部确认完成
        
        # 记录生命周期事件（V2增强功能）
        if V2_COMPONENTS_AVAILABLE:
            try:
                lifecycle_event = {
                    'message_id': message_id,
                    'device_sn': device_sn,
                    'user_id': user_id,
                    'event_type': 'mobile_acknowledged',
                    'acknowledgment_type': acknowledgment_type,
                    'event_time': now.isoformat(),
                    'location': json.dumps(location) if location else None,
                    'response_content': acknowledgment_message
                }
                redis.xadd('message_lifecycle_stream', lifecycle_event)
                logger.info(f"生命周期事件已记录: {lifecycle_event}")
            except Exception as e:
                logger.warning(f"生命周期记录失败: {e}")
        
        # 清理相关缓存
        cache_patterns_to_clear = [
            f"received_messages_v2:{device_sn}",
            f"message_opt_v1:*:{user_id}:*" if user_id else None,
            f"message_opt_v1:{message.org_id}:*:*" if message.org_id else None,
            f"department_user_messages:{message.org_id}:*"
        ]
        
        for pattern in cache_patterns_to_clear:
            if pattern:
                try:
                    keys = redis.keys(pattern)
                    if keys:
                        redis.delete(*keys)
                except Exception as e:
                    logger.warning(f"缓存清理失败: {pattern}, 错误: {e}")
        
        # 实时通知更新（WebSocket推送）
        try:
            notification_data = {
                'type': 'message_acknowledged',
                'message_id': message_id,
                'device_sn': device_sn,
                'user_id': user_id,
                'acknowledgment_type': acknowledgment_type,
                'timestamp': now.isoformat(),
                'org_id': message.org_id
            }
            
            # 推送给管理端
            redis.publish('message_status_updates', json.dumps(notification_data))
            
            # 推送给组织频道
            if message.org_id:
                redis.publish(f'org_message_updates:{message.org_id}', json.dumps(notification_data))
                
        except Exception as e:
            logger.warning(f"实时通知推送失败: {e}")
        
        result = {
            'success': True,
            'message': '消息确认成功',
            'data': {
                'message_id': message_id,
                'acknowledgment_type': acknowledgment_type,
                'timestamp': now.isoformat(),
                'message_status': message.message_status,
                'responded_number': message.responded_number,
                'total_number': message.total_number
            }
        }
        
        logger.info(f"手机端消息确认完成: {result}")
        return result, 200
        
    except Exception as e:
        logger.error(f"消息确认处理异常: {e}", exc_info=True)
        
        try:
            db.session.rollback()
        except:
            pass
            
        return {
            'success': False,
            'message': f'确认失败: {str(e)}',
            'error_type': type(e).__name__
        }, 500
    finally:
        # 清理处理锁
        try:
            redis.delete(cache_key)
        except Exception as e:
            logger.warning(f"清理处理锁失败: {e}")

@monitor_performance("batch_acknowledge_messages")
def batch_acknowledge_messages(data):
    """
    批量消息确认API - 支持手机端批量操作
    
    Args:
        data: {
            'message_ids': [消息ID列表],
            'device_sn': 设备序列号,
            'user_id': 用户ID（可选）,
            'acknowledgment_type': 确认类型,
            'acknowledgment_message': 批量确认消息
        }
    """
    logger.info("批量消息确认请求", extra={'data': data})
    
    if not data or not data.get('message_ids'):
        return {'success': False, 'message': '缺少消息ID列表'}, 400
    
    message_ids = data.get('message_ids', [])
    device_sn = data.get('device_sn')
    
    if not device_sn:
        return {'success': False, 'message': '缺少设备序列号'}, 400
    
    results = []
    success_count = 0
    
    for message_id in message_ids:
        try:
            single_data = data.copy()
            single_data['message_id'] = message_id
            
            result, status_code = acknowledge_message(single_data)
            
            if status_code == 200:
                success_count += 1
                results.append({'message_id': message_id, 'status': 'success'})
            else:
                results.append({
                    'message_id': message_id, 
                    'status': 'failed', 
                    'error': result.get('message', 'Unknown error')
                })
                
        except Exception as e:
            logger.error(f"批量确认单条消息失败: {message_id}, 错误: {e}")
            results.append({
                'message_id': message_id,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'success': True,
        'message': f'批量确认完成: 成功{success_count}/{len(message_ids)}条',
        'data': {
            'total_count': len(message_ids),
            'success_count': success_count,
            'failed_count': len(message_ids) - success_count,
            'results': results
        }
    }, 200

@monitor_performance("clear_message_cache")
def clear_message_cache(cache_pattern: str = None):
    """
    V2增强：清理消息缓存
    
    Args:
        cache_pattern: 缓存模式，为None时清理所有消息缓存
    """
    try:
        cache_manager = get_cache_manager()
        
        if cache_pattern:
            # 清理特定模式的缓存
            cache_manager.invalidate_pattern(cache_pattern)
            message = f"清理缓存模式: {cache_pattern}"
        else:
            # 清理所有消息相关缓存
            patterns = [
                'message_opt_v1:*',
                'received_messages_v2:*',
                'department_user_messages:*',
                'message_stats_v2:*'
            ]
            
            total_cleared = 0
            for pattern in patterns:
                try:
                    keys = redis.keys(pattern)
                    if keys:
                        redis.delete(*keys)
                        total_cleared += len(keys)
                except Exception as e:
                    logger.warning(f"清理缓存模式失败: {pattern}, 错误: {e}")
            
            message = f"清理所有消息缓存，共{total_cleared}个键"
        
        logger.info(message)
        return {
            'success': True,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"清理缓存失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

@monitor_performance("get_message_system_info")
def get_message_system_info():
    """
    V2增强：获取消息系统信息
    """
    return {
        'system': 'ljwx-bigscreen Message System',
        'version': 'v2-enhanced',
        'features': {
            'performance_monitoring': True,
            'distributed_transactions': V2_COMPONENTS_AVAILABLE,
            'advanced_caching': True,
            'batch_processing': True,
            'real_time_metrics': V2_COMPONENTS_AVAILABLE,
            'intelligent_routing': True
        },
        'components': {
            'v1_legacy': 'active',
            'v2_enhanced': 'active' if V2_COMPONENTS_AVAILABLE else 'unavailable',
            'monitoring': 'active' if get_monitoring_instance() else 'unavailable',
            'caching': 'active',
            'database': 'active'
        },
        'statistics': {
            'functions_enhanced': 7,
            'performance_decorators': 'active',
            'cache_layers': 2,
            'fallback_mechanisms': 'implemented'
        },
        'timestamp': datetime.now().isoformat(),
        'uptime': time.time() - (time.time() - 86400)  # 简化的运行时间
    }

# V2增强：初始化函数
def initialize_v2_enhancements():
    """
    V2增强：初始化V2增强组件
    """
    logger.info("🚀 正在初始化消息系统 V2 增强组件...")
    
    try:
        # 初始化缓存管理器
        cache_manager = get_cache_manager()
        logger.info("✅ 缓存管理器初始化完成")
        
        # 初始化V2服务（如果可用）
        if V2_COMPONENTS_AVAILABLE:
            v2_service = get_v2_message_service()
            if v2_service:
                logger.info("✅ V2消息服务初始化完成")
            
            # 初始化监控系统
            monitoring = get_monitoring_instance()
            if monitoring:
                logger.info("✅ 监控系统初始化完成")
        else:
            logger.warning("⚠️ V2组件不可用，使用传统功能")
        
        # 输出系统信息
        system_info = get_message_system_info()
        logger.info(f"📊 系统信息: {system_info['system']} {system_info['version']}")
        logger.info(f"🔧 增强功能: {len([k for k, v in system_info['features'].items() if v])}/{len(system_info['features'])} 已启用")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ V2增强组件初始化失败: {e}")
        return False

# 在模块加载时自动初始化V2增强组件
if __name__ != '__main__':
    try:
        # 在模块导入时自动初始化
        initialize_v2_enhancements()
    except Exception as e:
        logger.warning(f"模块初始化警告: {e}")

# =============================================================================
# 手表端消息处理专用函数 (Watch-specific Message Processing Functions)
# =============================================================================

def calculate_message_priority(message_type: str, send_time: str = None) -> int:
    """
    计算消息优先级 - 手表端显示顺序
    
    Args:
        message_type: 消息类型
        send_time: 发送时间
    
    Returns:
        优先级数值，数值越大优先级越高
    """
    # 基础优先级映射
    priority_map = {
        'warning': 100,      # 告警 - 最高优先级
        'task': 80,          # 任务管理 - 高优先级
        'announcement': 60,  # 公告 - 中等优先级
        'job': 50,          # 作业指引 - 中等优先级  
        'notification': 40   # 通知 - 一般优先级
    }
    
    base_priority = priority_map.get(message_type, 30)
    
    # 时间加权 - 越新的消息优先级略微提升
    time_bonus = 0
    if send_time:
        try:
            from datetime import datetime
            msg_time = datetime.strptime(send_time[:19], '%Y-%m-%d %H:%M:%S')
            now = datetime.now()
            hours_diff = (now - msg_time).total_seconds() / 3600
            
            # 24小时内的消息获得时间加权
            if hours_diff <= 24:
                time_bonus = max(0, 10 - int(hours_diff / 2))
        except:
            pass
    
    return base_priority + time_bonus

def get_message_title_for_watch(message_type: str) -> str:
    """获取手表端消息标题"""
    title_map = {
        'warning': '⚠️ 安全告警',
        'task': '📋 任务提醒', 
        'announcement': '📢 重要公告',
        'job': '🔧 作业指引',
        'notification': '💬 系统通知'
    }
    return title_map.get(message_type, '📨 消息')

def get_message_icon_for_watch(message_type: str) -> str:
    """获取手表端消息图标"""
    icon_map = {
        'warning': 'alert-triangle',
        'task': 'clipboard', 
        'announcement': 'megaphone',
        'job': 'tool',
        'notification': 'message-circle'
    }
    return icon_map.get(message_type, 'message')

def get_vibration_pattern(message_type: str) -> str:
    """获取手表端震动模式"""
    vibration_map = {
        'warning': 'urgent',      # 紧急震动 - 3次长震
        'task': 'important',      # 重要震动 - 2次短震
        'announcement': 'normal', # 普通震动 - 1次中震
        'job': 'normal',         # 普通震动 - 1次中震
        'notification': 'gentle'  # 轻柔震动 - 1次短震
    }
    return vibration_map.get(message_type, 'normal')

@monitor_performance("get_watch_message_summary")
def get_watch_message_summary(device_sn: str) -> Dict:
    """
    获取手表端消息摘要 - 用于手表主界面显示
    
    Args:
        device_sn: 设备序列号
        
    Returns:
        消息摘要信息
    """
    try:
        # 获取消息数据
        messages_result = received_messages(device_sn)
        
        if not messages_result.get("success"):
            return {"success": False, "error": "获取消息失败"}
        
        messages = messages_result.get("data", {}).get("messages", [])
        
        # 按类型统计
        type_count = {}
        urgent_count = 0
        latest_message = None
        
        for msg in messages:
            msg_type = msg.get('message_type', 'unknown')
            type_count[msg_type] = type_count.get(msg_type, 0) + 1
            
            # 统计紧急消息
            if msg.get('priority', 0) >= 80:
                urgent_count += 1
            
            # 记录最新消息
            if not latest_message or (msg.get('send_time', '') > latest_message.get('send_time', '')):
                latest_message = msg
        
        return {
            "success": True,
            "data": {
                "total_count": len(messages),
                "urgent_count": urgent_count,
                "type_summary": type_count,
                "latest_message": {
                    "title": latest_message.get("watch_display", {}).get("title", "无消息") if latest_message else "无消息",
                    "preview": latest_message.get("message", "")[:50] + "..." if latest_message and len(latest_message.get("message", "")) > 50 else latest_message.get("message", "") if latest_message else "",
                    "time": latest_message.get("send_time", "") if latest_message else "",
                    "priority": latest_message.get("priority", 0) if latest_message else 0
                },
                "device_sn": device_sn,
                "summary_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"获取手表消息摘要失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "data": {
                "total_count": 0,
                "urgent_count": 0,
                "latest_message": {"title": "获取失败", "preview": "", "time": "", "priority": 0}
            }
        }

@monitor_performance("mark_message_as_read_on_watch")
def mark_message_as_read_on_watch(message_id: str, device_sn: str) -> Dict:
    """
    手表端标记消息为已读（无需完整确认）
    
    Args:
        message_id: 消息ID
        device_sn: 设备序列号
    
    Returns:
        操作结果
    """
    try:
        # 调用确认API，确认类型为"read"
        acknowledge_data = {
            'message_id': message_id,
            'device_sn': device_sn,
            'acknowledgment_type': 'read',
            'acknowledgment_message': '[手表端已读]'
        }
        
        result, status_code = acknowledge_message(acknowledge_data)
        return result
        
    except Exception as e:
        logger.error(f"手表端标记已读失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# 模块结束标记
logger.info("✨ ljwx-bigscreen 消息系统 V2 增强版（含手表端优化）加载完成")

