from flask import jsonify, request
from .models import AlertInfo, AlertLog, DeviceInfo, db, AlertRules, UserInfo, UserOrg, OrgInfo, UserHealthData
import requests, json
import random
from .user import get_user_name
from .redis_helper import RedisHelper
import time
import threading
from sqlalchemy import and_, case, text
from datetime import datetime
from decimal import Decimal
from .device import get_device_user_org_info
from .time_config import get_now #统一时间配置
import os
from dotenv import load_dotenv
import sys

# 导入组织架构优化查询服务
from .org_optimized import get_org_service, find_principals_optimized, find_escalation_chain_optimized

# 添加项目根目录到Python路径以导入微信配置模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from wechat_config import get_wechat_config

# 加载环境变量
load_dotenv()

redis = RedisHelper()

# 获取微信配置实例
wechat_config = get_wechat_config()

# 保留原有的变量名以兼容现有代码
app_id = wechat_config.app_id
app_secret = wechat_config.app_secret
WECHAT_API_URL = wechat_config.api_url
WECHAT_ACCESS_TOKEN = ""  # 通过配置管理模块动态获取
WECHAT_TEMPLATE_ID = wechat_config.template_id
WECHAT_USER_OPENID = wechat_config.user_openid
WECHAT_ALERT_ENABLED = wechat_config.enabled

def get_access_token(app_id, app_secret):
    # 使用微信配置管理模块获取AccessToken
    return wechat_config.get_access_token()
    
def refresh_access_token():
    """定期刷新AccessToken - 增强配置检查和错误抑制"""
    global WECHAT_ACCESS_TOKEN
    last_error_time = 0 # 上次错误时间
    error_interval = 3600 # 错误抑制间隔1小时
    
    while True:
        current_time = time.time()
        
        # 检查配置是否启用
        if not wechat_config.is_enabled():
            time.sleep(3600)
            continue
            
        # 使用静默模式获取token，减少日志输出
        token = wechat_config.get_access_token(silent=True)
        if token:
            WECHAT_ACCESS_TOKEN = token
            last_error_time = 0 # 重置错误时间
        else:
            # 仅在间隔时间后才输出获取失败信息
            if current_time - last_error_time > error_interval:
                configured, msg = wechat_config.is_configured()
                if not configured:
                    print(f"微信配置检查: {msg}")
                else:
                    print("微信AccessToken获取失败，将在1小时后重试")
                last_error_time = current_time
                
        time.sleep(3600) # 每小时检查一次
    
threading.Thread(target=refresh_access_token, daemon=True).start()    

def send_wechat_alert(alert_type, user_openid, user_name, severity_level):
    """发送微信告警消息 - 使用配置管理模块统一处理"""
    # 直接使用配置管理模块的发送方法
    result = wechat_config.send_alert(alert_type, user_name, severity_level, user_openid)
    
    # 兼容原有的返回格式
    if result.get('success'):
        return result.get('data', result)
    else:
        return {"errcode": 1, "errmsg": result.get('message', '发送失败')}

def upload_alerts():
    data = request.get_json()
    userName = data.get('userName')
    phoneNumber = data.get('phoneNumber')
    alertType = data.get('alertType')
    timestamp = data.get('timestamp')
    latitude = data.get('latitude', random.uniform(-90, 90))
    longitude = data.get('longitude', random.uniform(-180, 180))
    device_sn = data.get('deviceSn') or data.get('device_sn')
    
    # 获取设备的用户和组织信息
    device_user_org = get_device_user_org_info(device_sn)

    new_alert = AlertInfo(
        alert_type=alertType,
        device_sn=device_sn,
        alert_timestamp=get_now(), #使用统一时间配置
        alert_desc=f"用户{userName}发生{alertType}告警",
        severity_level='medium',
        alert_status='pending',
        latitude=latitude,
        longitude=longitude,
        org_id=device_user_org.get('org_id') if device_user_org.get('success') else None,
        user_id=device_user_org.get('user_id') if device_user_org.get('success') else None
    )
    db.session.add(new_alert)
    db.session.commit()

    return jsonify({'message': 'Alert uploaded successfully'}), 201

def fetch_alerts_by_orgIdAndUserId(orgId=None, userId=None, severityLevel=None):
    """获取告警信息 - 使用AlertInfo表中的org_id和user_id字段"""
    try:
        print(f"查询参数: orgId={orgId}, userId={userId}, severityLevel={severityLevel}")
        
        # 构建基础查询
        query = db.session.query(
            AlertInfo.id,
            AlertInfo.alert_type,
            AlertInfo.severity_level,
            AlertInfo.alert_desc,
            AlertInfo.alert_status,
            AlertInfo.alert_timestamp,
            AlertInfo.responded_time,
            AlertInfo.device_sn,
            AlertInfo.health_id,
            AlertInfo.user_id,
            AlertInfo.org_id,
            AlertInfo.latitude,
            AlertInfo.longitude,
            AlertInfo.altitude,
            UserInfo.user_name,
            OrgInfo.name.label('org_name')
        ).outerjoin(
            UserInfo, AlertInfo.user_id == UserInfo.id
        ).outerjoin(
            OrgInfo, AlertInfo.org_id == OrgInfo.id
        )
        
        # 添加过滤条件
        if userId:
            query = query.filter(AlertInfo.user_id == userId)
        elif orgId:
            query = query.filter(AlertInfo.org_id == orgId)
        
        # 添加严重级别过滤
        if severityLevel:
            if severityLevel == 'high':
                query = query.filter(AlertInfo.severity_level.in_(['high', 'medium']))
            else:
                query = query.filter(AlertInfo.severity_level == severityLevel)
        
        # 排序：严重级别优先，状态次之，时间倒序
        severity_order = case(
            (AlertInfo.severity_level == 'critical', 1),
            (AlertInfo.severity_level == 'high', 2),
            (AlertInfo.severity_level == 'medium', 3),
            else_=4
        )
        status_order = case(
            (AlertInfo.alert_status == 'pending', 1),
            (AlertInfo.alert_status == 'responded', 2),
            else_=3
        )
        
        alerts = query.order_by(severity_order, status_order, AlertInfo.alert_timestamp.desc()).all()
        
        # 处理结果数据
        result_list = []
        alert_type_count = {}
        alert_level_count = {}
        alert_status_count = {}
        device_alert_count = {}
        
        for alert in alerts:
            alert_dict = {
                'alert_id': str(alert.id),
                'device_sn': alert.device_sn,
                'user_id': str(alert.user_id) if alert.user_id else None,
                'user_name': alert.user_name or '未知用户',
                'org_id': str(alert.org_id) if alert.org_id else None,
                'org_name': alert.org_name or '未知组织',
                'health_id': str(alert.health_id) if alert.health_id else None,
                'alert_type': alert.alert_type,
                'severity_level': alert.severity_level,
                'alert_desc': alert.alert_desc,
                'alert_status': alert.alert_status,
                'alert_timestamp': alert.alert_timestamp.strftime("%Y-%m-%d %H:%M:%S") if alert.alert_timestamp else None,
                'responded_time': alert.responded_time.strftime("%Y-%m-%d %H:%M:%S") if alert.responded_time else None,
                'latitude': str(alert.latitude) if alert.latitude else '22.54036796',
                'longitude': str(alert.longitude) if alert.longitude else '114.01508952',
                'altitude': str(alert.altitude) if alert.altitude else '0'
            }
            result_list.append(alert_dict)
            
            # 统计计数
            alert_type_count[alert.alert_type] = alert_type_count.get(alert.alert_type, 0) + 1
            alert_level_count[alert.severity_level] = alert_level_count.get(alert.severity_level, 0) + 1
            alert_status_count[alert.alert_status] = alert_status_count.get(alert.alert_status, 0) + 1
            device_alert_count[alert.device_sn] = device_alert_count.get(alert.device_sn, 0) + 1
        
        # 获取组织名称
        org_name = None
        if orgId:
            org = db.session.query(OrgInfo).filter(OrgInfo.id == orgId).first()
            org_name = org.name if org else None
        
        response_data = {
            'success': True,
            'data': {
                'alerts': result_list,
                'totalAlerts': len(result_list),
                'alertTypeCount': alert_type_count,
                'alertLevelCount': alert_level_count,
                'alertStatusCount': alert_status_count,
                'deviceAlertCount': device_alert_count,
                'totalDevices': len(device_alert_count),
                'orgId': str(orgId) if orgId else None,
                'org_name': org_name,
                'userId': str(userId) if userId else None
            }
        }
        
        print(f"查询结果: 共{len(result_list)}条告警")
        return response_data
        
    except Exception as e:
        print(f"查询告警失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'data': None
        }

def fetch_alerts_by_orgIdAndUserId1(orgId=None, userId=None, severityLevel=None):
    """
    获取告警信息
    :param orgId: 组织ID，可选
    :param userId: 用户ID，可选
    :param severityLevel: 告警级别，可选
    """
    try:
        from .admin_helper import is_admin_user  # 导入admin判断函数
        
        print("fetch_alerts_by_orgIdAndUserId.userId:", userId)
        print("fetch_alerts_by_orgIdAndUserId.orgId:", orgId)
        print("fetch_alerts_by_orgIdAndUserId.severityLevel:", severityLevel)
        # 如果提供了userId，优先使用userId查询
        result_list = []
        device_sns = set()
        if userId:
            # 检查是否为管理员用户
            if is_admin_user(userId):
                org = db.session.query(OrgInfo).filter(OrgInfo.id == orgId).first() if orgId else None
                return {
                    'success': True,
                    'data': {
                        'alerts': [],
                        'totalAlerts': 0,
                        'alertTypeCount': {},
                        'alertLevelCount': {},
                        'alertStatusCount': {},
                        'deviceAlertCount': {},
                        'totalDevices': 0,
                        'orgId': str(orgId),
                        'org_name': org.name if org else None
                    }
                }
          
            # 直接查询用户信息
            user = UserInfo.query.filter_by(id=userId).first()
            if user.device_sn:
                device_sns.add(user.device_sn)
            print('device_sns:',device_sns)
            # 修复部门查询
            dept = db.session.query(
                OrgInfo
            ).join(
                UserOrg,
                UserOrg.org_id == OrgInfo.id
            ).filter(
                UserOrg.user_id == userId
            ).first()
            
            if dept:
                # 获取所有部门信息
                departments = {
                    str(dept.id): dept.name
                }
            else:
                departments = {}
        
        elif orgId:
   
            # 直接查询部门信息，而不是调用fetch_departments_by_orgId
            departments = db.session.query(OrgInfo)\
                .filter(OrgInfo.parent_id == orgId)\
                .all()
            
            department_ids = [dept.id for dept in departments]
            
            # 获取所有部门信息
            departments = {
                str(dept.id): dept.name for dept in OrgInfo.query.filter(
                    OrgInfo.id.in_(department_ids),
                    OrgInfo.is_deleted.is_(False),
                    OrgInfo.status == '1'
                ).all()
            }
        
            # 获取组织下所有用户
            from .org import fetch_users_by_orgId
            users = fetch_users_by_orgId(orgId)
            
            # 获取所有设备的告警
            
            for user in users:
                if user.get('device_sn'):
                    device_sns.add(user['device_sn'])

        if not device_sns:
            org = db.session.query(OrgInfo).filter(OrgInfo.id == orgId).first()
            return {
                'success': True,
                'data': {
                    'alerts': [],
                    'totalAlerts': 0,
                    'alertTypeCount': {},
                    'alertLevelCount': {},
                    'alertStatusCount': {},
                    'deviceAlertCount': {},
                    'totalDevices': 0,
                    'orgId': str(orgId),
                    'org_name': org.name if org else None
                }
            }

        # 定义排序顺序
        severity_order = case(
            (AlertInfo.severity_level == 'critical', 1),
            (AlertInfo.severity_level == 'high', 2),
            (AlertInfo.severity_level == 'medium', 3),
            else_=4
        )

        status_order = case(
            (AlertInfo.alert_status == 'pending', 1),
            (AlertInfo.alert_status == 'responded', 2),
            else_=3
        )

        # 获取设备信息
        device_query = db.session.query(DeviceInfo.serial_number).filter(   
            DeviceInfo.serial_number.in_(device_sns)  # 确保设备号在用户列表中
        )
        print('device_sns:',device_sns)
        # 获取告警信息
        alerts = db.session.query(
            AlertInfo.id,
            AlertInfo.alert_type,
            AlertInfo.severity_level,
            AlertInfo.alert_desc,
            AlertInfo.alert_status,
            AlertInfo.alert_timestamp,
            AlertInfo.responded_time,
            AlertInfo.device_sn,
            AlertInfo.health_id,
            UserInfo.id.label('user_id'),
            UserInfo.user_name,
            OrgInfo.id.label('dept_id'),
            OrgInfo.name.label('dept_name'),
            OrgInfo.ancestors,
            UserHealthData.latitude.label('latitude'),
            UserHealthData.longitude.label('longitude'),
            UserHealthData.altitude.label('altitude')
        ).outerjoin(
            UserInfo,
            AlertInfo.device_sn == UserInfo.device_sn
        ).outerjoin(
            UserOrg,
            UserInfo.id == UserOrg.user_id
        ).outerjoin(
            OrgInfo,
            UserOrg.org_id == OrgInfo.id
        ).outerjoin(
            UserHealthData,
            AlertInfo.health_id == UserHealthData.id
        ).filter(
            AlertInfo.device_sn.in_(device_query)  # 使用子查询
        )
        #print('alerts before filter:',alerts)
       
        
        # 修改 severityLevel 过滤逻辑
        if severityLevel:
            if severityLevel == 'high':
                # 如果是high，显示high和medium级别的告警
                alerts = alerts.filter(
                    AlertInfo.severity_level.in_(['high', 'medium'])
                )
            else:
                # 其他情况只显示指定级别的告警
                alerts = alerts.filter(
                    AlertInfo.severity_level == severityLevel
                )

        alerts = alerts.order_by(
            severity_order,
            status_order,
            AlertInfo.alert_timestamp.desc()
        ).distinct().all()
        
        #print('alerts:',alerts)
      
        # 处理告警数据
     
        department_stats = {}  # 部门统计

        for alert in alerts:
            # 获取部门层级信息
            dept_hierarchy = []
            if alert.ancestors:
                ancestor_ids = alert.ancestors.split(',')
                dept_hierarchy = [departments.get(aid, 'Unknown') for aid in ancestor_ids]
            if alert.dept_name:
                dept_hierarchy.append(alert.dept_name)

            current_dept_id = str(alert.dept_id) if alert.dept_id else 'unknown'
            current_dept_name = alert.dept_name if alert.dept_name else 'Unknown Department'

            # v1.0.32 - 构建告警字典，为空坐标提供默认值
            # 为没有坐标的告警提供默认坐标(深圳坐标)
            default_lat = '22.54036796'
            default_lng = '114.01508952'
            
            alert_dict = {
                'alert_id': str(alert.id),
                'device_sn': alert.device_sn,
                'alert_type': alert.alert_type,
                'severity_level': alert.severity_level,
                'alert_desc': alert.alert_desc,
                'alert_status': alert.alert_status,
                'alert_timestamp': alert.alert_timestamp.strftime("%Y-%m-%d %H:%M:%S") if alert.alert_timestamp else None,
                'responded_time': alert.responded_time.strftime("%Y-%m-%d %H:%M:%S") if alert.responded_time else None,
                'user_id': str(alert.user_id) if alert.user_id else None,
                'user_name': alert.user_name,
                'dept_id': str(alert.dept_id) if alert.dept_id else None,
                'dept_name': current_dept_name,
                'dept_hierarchy': dept_hierarchy,
                'latitude': str(alert.latitude) if alert.latitude else default_lat,
                'longitude': str(alert.longitude) if alert.longitude else default_lng,
                'altitude': str(alert.altitude) if alert.altitude else '0'
            }
            
            result_list.append(alert_dict)

            # 统计信息
            if current_dept_id not in department_stats:
                department_stats[current_dept_id] = {
                    'name': current_dept_name,
                    'total_alerts': 0,
                    'severity_stats': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'status_stats': {'pending': 0, 'responded': 0, 'closed': 0},
                    'device_count': set()
                }

            dept_stat = department_stats[current_dept_id]
            dept_stat['total_alerts'] += 1
            dept_stat['severity_stats'][alert.severity_level] = dept_stat['severity_stats'].get(alert.severity_level, 0) + 1
            dept_stat['status_stats'][alert.alert_status] = dept_stat['status_stats'].get(alert.alert_status, 0) + 1
            dept_stat['device_count'].add(alert.device_sn)

        # 转换设备计数
        for dept_id, stats in department_stats.items():
            stats['device_count'] = len(stats['device_count'])

        # 计算统计信息
        alert_type_count = {}
        alert_level_count = {}
        alert_status_count = {}
        device_alert_count = set()

        for alert in result_list:
            # 按类型计数
            alert_type = alert['alert_type']
            alert_type_count[alert_type] = alert_type_count.get(alert_type, 0) + 1

            # 按级别计数
            severity_level = alert['severity_level']
            alert_level_count[severity_level] = alert_level_count.get(severity_level, 0) + 1

            # 按状态计数
            alert_status = alert['alert_status']
            alert_status_count[alert_status] = alert_status_count.get(alert_status, 0) + 1

            # 设备计数（去重）
            device_alert_count.add(alert['device_sn'])

        # 获取orgId对应的部门名称
        org_name = "Unknown Organization"
        if orgId:
            org = db.session.query(OrgInfo).filter(OrgInfo.id == orgId).first()
            org_name = org.name if org else "Unknown Organization"

        return {
            'success': True,
            'data': {
                'alerts': result_list,
                'totalAlerts': len(result_list),
                'alertTypeCount': alert_type_count,
                'alertLevelCount': alert_level_count,
                'alertStatusCount': alert_status_count,
                'deviceAlertCount': dict(enumerate(device_alert_count)),
                'totalDevices': len(device_alert_count),
                'orgId': str(orgId) if orgId else None,
                'org_name': org_name,
                'departmentStats': department_stats
            }
        }

    except Exception as e:
        print(f"告警查询错误: {e}")
        return {
            'success': False,
            'error': f'告警查询失败: {str(e)}',
            'data': {
                'alerts': [],
                'totalAlerts': 0,
                'alertTypeCount': {},
                'alertLevelCount': {},
                'alertStatusCount': {},
                'deviceAlertCount': {},
                'totalDevices': 0,
                'orgId': str(orgId) if orgId else None,
                'org_name': None,
                'departmentStats': {}
            }
        }

def fetch_alerts(deviceSn, customerId):
    print("fetch_alerts:deviceSn:", deviceSn)
    from .user import get_user_info
    user_info = get_user_info(deviceSn)
    print("fetch_alerts:user_info:", user_info)
    if user_info:
        user_dict = json.loads(user_info)
        userId = user_dict.get('user_id')
        return fetch_alerts_by_orgIdAndUserId(orgId=None, userId=userId, severityLevel=None)
    else:
        return jsonify({"error": "User not found"}), 404

    try:
        severity_order = case(
            (AlertInfo.severity_level == 'critical', 1),
            (AlertInfo.severity_level == 'high', 2),
            (AlertInfo.severity_level == 'medium', 3),
            else_=4
        )

        status_order = case(
            (AlertInfo.alert_status == 'pending', 1),
            (AlertInfo.alert_status == 'responded', 2),
            else_=3
        )

        if deviceSn is None:
            subquery = db.session.query(DeviceInfo.serial_number).filter(DeviceInfo.customer_id == 1).subquery()
            alerts = AlertInfo.query.filter(AlertInfo.device_sn.in_(subquery)).order_by(
                status_order,
                severity_order,
                AlertInfo.update_time.desc()
            ).all()
        else:
            alerts = AlertInfo.query.filter_by(device_sn=deviceSn).order_by(
                status_order,
                severity_order,
                AlertInfo.update_time.desc()
            ).all()
        
        # Helper function to convert Decimal to float
        def convert_decimal(obj):
            if isinstance(obj, Decimal):
                return float(obj)  # or str(obj) if you prefer
            return obj

        alerts_data = [{
            'id': alert.id,
            'deviceSn': alert.device_sn,
            'alertType': alert.alert_type,
            'latitude': convert_decimal(alert.latitude),
            'longitude': convert_decimal(alert.longitude),
            'timestamp': alert.alert_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'severityLevel': alert.severity_level,
            'alertStatus': alert.alert_status,
            'userName': get_user_name(alert.device_sn) if alert.device_sn else "Unknown"
        } for alert in alerts]
        
        # Calculate total number of alerts
        total_alerts = len(alerts)

        # Calculate total number of unique alert types
        unique_alert_types = len(set(alert.alert_type for alert in alerts))

        # Calculate counts for each alertStatus
        alert_status_counts = {}
        for alert in alerts:
            status = alert.alert_status
            if status in alert_status_counts:
                alert_status_counts[status] += 1
            else:
                alert_status_counts[status] = 1

        # Calculate counts for each alertType
        alert_type_counts = {}
        for alert in alerts:
            alert_type = alert.alert_type
            if alert_type in alert_type_counts:
                alert_type_counts[alert_type] = alert_type_counts.get(alert_type, 0) + 1
            else:
                alert_type_counts[alert_type] = 1

        # Calculate counts for each severityLevel
        severity_level_counts = {}
        for alert in alerts:
            severity_level = alert.severity_level
            if severity_level in severity_level_counts:
                severity_level_counts[severity_level] += 1
            else:
                severity_level_counts[severity_level] = 1

        response_data = {
            'success': True,
            'alerts': alerts_data,
            'totalAlerts': total_alerts,
            'uniqueAlertTypes': unique_alert_types,
            'alertStatusCounts': alert_status_counts,
            'alertTypeCounts': alert_type_counts,
            'severityLevelCounts': severity_level_counts
        }
        
        # Serialize the alerts_data list to a JSON string
        alerts_data_json = json.dumps(alerts_data, default=convert_decimal)
        #print("alerts_data_json:", alerts_data_json)
        if len(alerts_data_json) > 0:  # Check if alerts_data_json is not empty
            mapping = {str(alert['id']): json.dumps(alert) for alert in alerts_data}
            if mapping:  # Ensure mapping is not empty
                if deviceSn is None:
                    redis.hset(f"alert_info:all", mapping=mapping)
                    redis.publish("alert_info_channel", alerts_data_json)
                else:
                    redis.hset(f"alert_info:{deviceSn}", mapping=mapping)
                    redis.publish(f"alert_info_channel:{deviceSn}", alerts_data_json)

        return jsonify(response_data)
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
def generate_alert_stats(alert_info):
    #print("generate_alert_stats:alert_info:", alert_info)

    try:
        # Calculate total number of alerts
        total_alerts = len(alert_info)

        # Initialize dictionaries for counts
        alert_status_counts = {}
        alert_type_counts = {}
        severity_level_counts = {}

        # Calculate counts for each category
        for alert in alert_info:
            # Count alert statuses
            alert_status_counts[alert['alertStatus']] = alert_status_counts.get(alert['alertStatus'], 0) + 1

            # Count alert types
            alert_type_counts[alert['alertType']] = alert_type_counts.get(alert['alertType'], 0) + 1

            # Count severity levels
            severity_level_counts[alert['severityLevel']] = severity_level_counts.get(alert['severityLevel'], 0) + 1

        # Calculate total number of unique alert types
        unique_alert_types = len(alert_type_counts)
        print("unique_alert_types:", unique_alert_types)
        print("alert_status_counts:", alert_status_counts)
        print("alert_type_counts:", alert_type_counts)
        print("severity_level_counts:", severity_level_counts)

        # Return a raw dictionary, not a Flask Response
        return {
            'alerts': alert_info,
            'totalAlerts': total_alerts,
            'uniqueAlertTypes': unique_alert_types,
            'alertStatusCounts': alert_status_counts,
            'alertTypeCounts': alert_type_counts,
            'severityLevelCounts': severity_level_counts
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {'success': False, 'error': str(e)}  # Return raw error data

def fetch_alertType_stats():
    userName = request.args.get('userName')
    try:
        from sqlalchemy import func
        from datetime import datetime

        # Base query for alert type counts
        query = db.session.query(AlertInfo.alertType, func.count(AlertInfo.alertType).label('count'))

        if userName:
            query = query.filter(AlertInfo.userName == userName)

        alert_type_counts = query.group_by(AlertInfo.alertType).all()

        # Convert query results to dictionary list
        alert_type_data = [{'name': alert_type, 'value': count} for alert_type, count in alert_type_counts]

        # Calculate total number of alerts
        total_alerts_query = db.session.query(func.count(AlertInfo.id))
        if userName:
            total_alerts_query = total_alerts_query.filter(AlertInfo.userName == userName)
        total_alerts = total_alerts_query.scalar()

        # Calculate number of alerts added this month
        start_of_month = datetime(datetime.now().year, datetime.now().month, 1)
        monthly_alerts_query = db.session.query(func.count(AlertInfo.id)).filter(AlertInfo.timestamp >= start_of_month)
        if userName:
            monthly_alerts_query = monthly_alerts_query.filter(AlertInfo.userName == userName)
        monthly_alerts = monthly_alerts_query.scalar()

        return jsonify({
            'success': True,
            'alertTypeStats': alert_type_data,
            'totalAlerts': total_alerts,
            'monthlyAlerts': monthly_alerts
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
def get_severity_level_mapping(severity):
    """
    将英文告警级别映射为数字级别
    medium -> 三级
    high -> 二级
    critical -> 一级
    """
    severity_mapping = {
        'medium': '三级',
        'high': '二级',
        'critical': '一级'
    }
    return severity_mapping.get(severity.lower(), '未知级别')

def deal_alert(alertId):
    """告警处理函数 - 根据notification_type执行不同处理逻辑"""
    print("deal_alert:alertId:", alertId)
    
    try:
        # 获取告警信息
        alert = AlertInfo.query.filter_by(id=alertId).first()
        if not alert:
            return jsonify({'success': False, 'message': '告警记录不存在'}), 404
            
        print(f"📋 告警信息: device_sn={alert.device_sn}, rule_id={alert.rule_id}, alert_type={alert.alert_type}")
        
        # 检查rule_id是否存在
        if not alert.rule_id:
            print("⚠️ 告警记录缺少rule_id，使用默认处理方式")
            # 使用默认规则处理
            rule_data = {
                'id': None,
                'rule_type': alert.alert_type,
                'notification_type': 'message',  # 默认消息通知
                'severity_level': alert.severity_level or 'medium',
                'alert_message': alert.alert_desc or f'{alert.alert_type}告警'
            }
        else:
            # 使用ORM查询获取告警规则信息
            rule=AlertRules.query.filter_by(id=alert.rule_id,is_deleted=False).first()
            
            if not rule:
                print(f"⚠️ 告警规则ID {alert.rule_id} 不存在，使用默认处理方式")
                # 使用默认规则处理
                rule_data = {
                    'id': alert.rule_id,
                    'rule_type': alert.alert_type,
                    'notification_type': 'message',  # 默认为message
                    'severity_level': alert.severity_level or 'medium',
                    'alert_message': alert.alert_desc or f'{alert.alert_type}告警'
                }
            else:
                # 解析规则数据
                rule_data = {
                    'id': rule.id,
                    'rule_type': rule.rule_type, 
                    'notification_type': rule.notification_type or 'message',  # 默认为message
                    'severity_level': rule.severity_level or 'medium',
                    'alert_message': rule.alert_message
                }
                
        print(f"📋 规则信息: ID={rule_data['id']}, notification_type={rule_data['notification_type']}")
            
        # 获取设备用户信息
        print(f"📋 设备用户信息: device_sn={alert.device_sn}")
        user = UserInfo.query.filter_by(device_sn=alert.device_sn).first()
        print(f"📋 设备用户信息: user={user}")
        if not user:
            return jsonify({'success': False, 'message': '设备用户不存在'}), 404
            
        userName = user.user_name
        userId = user.id
        mapped_severity = get_severity_level_mapping(alert.severity_level)
        
        # 根据notification_type处理告警
        wechat_result = None
        message_result = None
        websocket_result = None
        notification_type = rule_data['notification_type']
        
        # 🚨 Critical级别告警增强处理
        if alert.severity_level == 'critical':
            print(f"🚨 Critical级别告警 - 执行增强处理")
            
            # 1. WebSocket推送到大屏
            try:
                from .bigScreen import socketio
                
                # 构建告警推送数据
                alert_data = {
                    'alert_id': alert.id,
                    'device_sn': alert.device_sn,
                    'alert_type': alert.alert_type,
                    'alert_desc': alert.alert_desc,
                    'severity_level': 'critical',
                    'alert_timestamp': alert.alert_timestamp.strftime('%Y-%m-%d %H:%M:%S') if alert.alert_timestamp else None,
                    'user_name': userName,
                    'user_id': userId,
                    'latitude': str(alert.latitude) if alert.latitude else None,
                    'longitude': str(alert.longitude) if alert.longitude else None
                }
                
                # 通过WebSocket推送到大屏页面
                socketio.emit('critical_alert', alert_data, namespace='/')
                print(f"🚨 Critical告警已推送到大屏: alert_id={alert.id}")
                websocket_result = True
                
            except Exception as ws_error:
                print(f"⚠️ WebSocket推送失败: {ws_error}")
                websocket_result = False
        
        if notification_type in ['wechat', 'both']:
            # 微信推送
            from .wechat import send_message
            wechat_result = send_message(alert.alert_type, userName, mapped_severity)
            print("微信推送结果:", wechat_result)
            
        if notification_type in ['message', 'both']:
            # 插入消息记录 - 增强版层级通知
            message_result = _insert_device_messages_enhanced(alert.device_sn, alert.alert_type, mapped_severity, userName, alert.severity_level)
            print("消息插入结果:", message_result)
        
        # 记录处理日志
        _create_alert_log_enhanced(alertId, userName, userId, notification_type, wechat_result, message_result, websocket_result)
        
        # 更新告警状态
        if ((notification_type == 'wechat' and wechat_result and wechat_result.get('errcode') == 0) or
            (notification_type == 'message' and message_result) or
            (notification_type == 'both' and message_result and 
             (not wechat_result or wechat_result.get('errcode') == 0))):
            
            alert.alert_status = 'responded'
            alert.responded_time = get_now() #使用统一时间配置
            db.session.commit()
            return jsonify({'success': True, 'message': f'告警已通过{notification_type}处理'})
        else:
            db.session.commit()
            return jsonify({'success': False, 'message': '告警处理失败'}), 500
            
    except Exception as e:
        db.session.rollback()
        print(f"告警处理异常: {e}")
        return jsonify({'success': False, 'message': f'告警处理异常: {str(e)}'}), 500

def _insert_device_messages_enhanced(device_sn, alert_type, severity_level, user_name, alert_severity_level):
    """插入设备消息记录 - 增强版层级通知"""
    try:
        from .models import DeviceMessage, UserOrg, DeviceInfo, OrgInfo
        
        # 根据device_sn查询org_id和user_id
        device = DeviceInfo.query.filter_by(serial_number=device_sn).first()
        if not device or not device.org_id or not device.user_id:
            print(f"设备{device_sn}未绑定组织或用户")
            return False
            
        org_id = device.org_id
        user_id = device.user_id
        
        # 构建消息内容
        message_content = f"设备{device_sn}发生{alert_type}告警，严重级别：{severity_level}，请及时处理。"
        
        # 创建消息记录
        message_records = []
        
        # 1. 给设备用户的消息
        user_message = DeviceMessage(
            device_sn=device_sn,
            message=message_content,
            department_info=str(org_id),
            user_id=str(user_id),
            message_type='warning',
            sender_type='system', 
            receiver_type='user',
            message_status='1',
            create_time=get_now()
        )
        message_records.append(user_message)
        
        # 2. 给部门主管的消息 - 使用优化查询
        try:
            # 获取租户ID (customer_id)
            customer_id = getattr(device, 'customer_id', 0)
            org_service = get_org_service()
            principals_data = org_service.find_org_managers(org_id, customer_id, "manager")
            
            for principal_data in principals_data:
                principal_user_id = principal_data['user_id']
                if principal_user_id != user_id:  # 避免重复给同一人发消息
                    principal_message = DeviceMessage(
                        device_sn=device_sn,
                        message=message_content + f"（设备用户：{user_name}）",
                        department_info=str(org_id),
                        user_id=str(principal_user_id),
                        message_type='warning',
                        sender_type='system',
                        receiver_type='manager',
                        message_status='1',
                        create_time=get_now()
                    )
                    message_records.append(principal_message)
        except Exception as e:
            print(f"使用优化查询失败，回退到原始查询: {str(e)}")
            # 回退到原始查询方式
            principals = UserOrg.query.filter_by(org_id=org_id, principal='1', is_deleted=False).all()
            for principal in principals:
                if principal.user_id != user_id:  # 避免重复给同一人发消息
                    principal_message = DeviceMessage(
                        device_sn=device_sn,
                        message=message_content + f"（设备用户：{user_name}）",
                        department_info=str(org_id),
                        user_id=str(principal.user_id),
                        message_type='warning',
                        sender_type='system',
                        receiver_type='manager',
                        message_status='1',
                        create_time=get_now()
                    )
                    message_records.append(principal_message)
        
        # 3. 如果是message方式且没有部门管理员，给租户级别管理员发消息
        try:
            # 检查是否有部门管理员
            if not principals_data:
                # 查找当前部门的父级组织(租户级别)
                current_org = OrgInfo.query.filter_by(id=org_id).first()
                if current_org and current_org.parent_id:
                    # 使用优化查询获取父级组织管理员
                    parent_principals_data = org_service.find_org_managers(
                        current_org.parent_id, customer_id, "manager")
                    
                    for parent_principal_data in parent_principals_data:
                        tenant_message = DeviceMessage(
                            device_sn=device_sn,
                            message=message_content + f"（设备用户：{user_name}，部门：{current_org.name}）",
                            department_info=str(current_org.parent_id),
                            user_id=str(parent_principal_data['user_id']),
                            message_type='warning',
                            sender_type='system',
                            receiver_type='tenant_admin',
                            message_status='1',
                            create_time=get_now()
                        )
                        message_records.append(tenant_message)
        except Exception as e:
            print(f"租户级别管理员查询失败: {str(e)}")
        
        # 批量插入消息记录
        for record in message_records:
            db.session.add(record)
        db.session.flush()
        
        print(f"✅ 成功插入{len(message_records)}条消息记录（层级通知）")
        return True
        
    except Exception as e:
        print(f"❌ 插入消息记录失败: {e}")
        return False

def _insert_device_messages(device_sn, alert_type, severity_level, user_name):
    """插入设备消息记录"""
    try:
        from .models import DeviceMessage, UserOrg, DeviceInfo
        
        # 根据device_sn查询org_id和user_id
        device = DeviceInfo.query.filter_by(serial_number=device_sn).first()
        if not device or not device.org_id or not device.user_id:
            print(f"设备{device_sn}未绑定组织或用户")
            return False
            
        org_id = device.org_id
        user_id = device.user_id
        
        # 查询该组织的主管(principal=1) - 使用优化查询
        try:
            # 获取租户ID (customer_id)
            customer_id = getattr(device, 'customer_id', 0)
            org_service = get_org_service()
            principals_data = org_service.find_org_managers(org_id, customer_id, "manager")
            principal_user_ids = [p['user_id'] for p in principals_data]
        except Exception as e:
            print(f"使用优化查询失败，回退到原始查询: {str(e)}")
            # 回退到原始查询方式
            principals = UserOrg.query.filter_by(org_id=org_id, principal='1', is_deleted=False).all()
            principal_user_ids = [p.user_id for p in principals]
        
        # 构建消息内容
        message_content = f"设备{device_sn}发生{alert_type}告警，严重级别：{severity_level}，请及时处理。"
        
        # 创建消息记录
        message_records = []
        
        # 如果用户本人是主管，只插入一条记录
        if user_id in principal_user_ids:
            message = DeviceMessage(
                device_sn=device_sn,
                message=message_content,
                department_info=str(org_id),
                user_id=str(user_id),
                message_type='warning',
                sender_type='system',
                receiver_type='manager_and_user',
                message_status='1',
                create_time=get_now() #使用统一时间配置
            )
            message_records.append(message)
        else:
            # 用户和主管不同，插入两条记录
            # 1. 给用户的消息
            user_message = DeviceMessage(
                device_sn=device_sn,
                message=message_content,
                department_info=str(org_id),
                user_id=str(user_id),
                message_type='warning',
                sender_type='system', 
                receiver_type='user',
                message_status='1',
                create_time=get_now() #使用统一时间配置
            )
            message_records.append(user_message)
            
            # 2. 给主管的消息
            for principal_id in principal_user_ids:
                principal_message = DeviceMessage(
                    device_sn=device_sn,
                    message=message_content + f"（设备用户：{user_name}）",
                    department_info=str(org_id),
                    user_id=str(principal_id),
                    message_type='warning',
                    sender_type='system',
                    receiver_type='manager',
                    message_status='1',
                    create_time=get_now() #使用统一时间配置
                )
                message_records.append(principal_message)
        
        # 批量插入消息记录
        for record in message_records:
            db.session.add(record)
        db.session.flush()  # 提交到数据库但不结束事务
        
        print(f"成功插入{len(message_records)}条消息记录")
        return True
        
    except Exception as e:
        print(f"插入消息记录失败: {e}")
        return False

def _create_alert_log_enhanced(alert_id, user_name, user_id, notification_type, wechat_result, message_result, websocket_result):
    """创建告警处理日志 - 增强版"""
    try:
        from .models import AlertLog
        
        # 确定处理方式和结果
        handled_via_list = []
        results = []
        
        if notification_type in ['wechat', 'both']:
            handled_via_list.append('WeChat')
            results.append('success' if wechat_result and wechat_result.get('errcode') == 0 else 'failed')
            
        if notification_type in ['message', 'both']:
            handled_via_list.append('Message')
            results.append('success' if message_result else 'failed')
            
        if websocket_result is not None:
            handled_via_list.append('WebSocket')
            results.append('success' if websocket_result else 'failed')
        
        handled_via = '+'.join(handled_via_list)
        result = 'success' if 'success' in results else 'failed'
        
        details = f"告警通过{handled_via}处理"
        if notification_type == 'both':
            details += f"，微信：{'成功' if wechat_result and wechat_result.get('errcode') == 0 else '失败'}，消息：{'成功' if message_result else '失败'}"
        if websocket_result is not None:
            details += f"，WebSocket推送：{'成功' if websocket_result else '失败'}"
        
        alert_log = AlertLog(
            alert_id=alert_id,
            action='deal_alert_enhanced',
            action_user=user_name,
            action_user_id=user_id,
            details=details,
            handled_via=handled_via,
            result=result,
            action_timestamp=get_now()
        )
        db.session.add(alert_log)
        
    except Exception as e:
        print(f"创建告警日志失败: {e}")

def _create_alert_log(alert_id, user_name, user_id, notification_type, wechat_result, message_result):
    """创建告警处理日志"""
    try:
        from .models import AlertLog
        
        # 确定处理方式和结果
        handled_via_list = []
        results = []
        
        if notification_type in ['wechat', 'both']:
            handled_via_list.append('WeChat')
            results.append('success' if wechat_result and wechat_result.get('errcode') == 0 else 'failed')
            
        if notification_type in ['message', 'both']:
            handled_via_list.append('Message')
            results.append('success' if message_result else 'failed')
        
        handled_via = '+'.join(handled_via_list)
        result = 'success' if 'success' in results else 'failed'
        
        details = f"告警通过{handled_via}处理"
        if notification_type == 'both':
            details += f"，微信：{'成功' if wechat_result and wechat_result.get('errcode') == 0 else '失败'}，消息：{'成功' if message_result else '失败'}"
        
        alert_log = AlertLog(
            alert_id=alert_id,
            action='deal_alert',
            action_user=user_name,
            action_user_id=user_id,
            details=details,
            handled_via=handled_via,
            result=result,
            action_timestamp=get_now() #使用统一时间配置
        )
        db.session.add(alert_log)
        
    except Exception as e:
        print(f"创建告警日志失败: {e}")

def generate_alert_chart_by_type(customerId):

    if not customerId:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400
    subquery = db.session.query(DeviceInfo.serial_number).filter(DeviceInfo.customer_id == customerId).subquery()
    # Query using SQLAlchemy ORM
    alert_counts = db.session.query(
        db.func.count(AlertInfo.id).label('alertCount'),
        AlertInfo.alert_type
    ).filter(AlertInfo.device_sn.in_(subquery)).group_by(AlertInfo.alert_type).order_by(AlertInfo.alert_type).all()

    # Convert the result to a list of dictionaries
    alert_counts = [{'alertCount': count, 'alertType': alert_type} for count, alert_type in alert_counts]

    # Return the JSON response
    return jsonify({'success': True, 'data': alert_counts})


def gather_deal_alert(customerId):  # Get the severityLevel from query parameters
    # 子查询：获取所有匹配的设备序列号
    subquery = db.session.query(DeviceInfo.serial_number).filter(DeviceInfo.customer_id == customerId)
    filter_query = and_(AlertInfo.alert_status == 'responded')

    query = (
        AlertInfo.query
        .filter(filter_query)
        .filter(AlertInfo.device_sn.in_(subquery))  # 使用直接的子查询
    )

    alerts = query.all()
    
    # Calculate the number of alerts
    alert_count = len(alerts)
    
    # Return the count of alerts
    return jsonify({'success': True, 'alertCount': alert_count})
    

def generate_alert_json(orgId, userId, severityLevel):
    # 获取告警数据
    alerts_response = fetch_alerts_by_orgIdAndUserId(orgId, userId, severityLevel)
    #print("generate_alert_json.alerts_response:", alerts_response)
    
    # 检查响应是否成功
    if not alerts_response.get('success'):
        return jsonify({
            "type": "FeatureCollection",
            "features": []
        })

    # 从响应中获取告警列表
  
    alerts = alerts_response['data']['alerts']
    #print("generate_alert_json.alerts:", alerts)
    
    # 格式化为 GeoJSON
    features = []
    for alert in alerts:
        print("generate_alert_json.alert:", alert['alert_status'])
        # v1.0.32 - 修复告警点过滤逻辑：检查坐标和状态
        longitude = alert.get('longitude')
        latitude = alert.get('latitude') 
        status = alert.get('alert_status')
        print(f"🔍 检查告警点: ID={alert.get('alert_id')}, 经度={longitude}, 纬度={latitude}, 状态={status}")
        
        # 改进条件判断：确保坐标有效且状态为pending
        if (longitude and longitude != 'None' and longitude != '0' and 
            latitude and latitude != 'None' and latitude != '0' and 
            status == 'pending'):
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        float(alert['longitude']) if alert['longitude'] is not None else 0.0,
                        float(alert['latitude']) if alert['latitude'] is not None else 0.0
                    ]
                },
                "properties": {
                    "id": alert['alert_id'],
                    "deviceSn": alert['device_sn'],
                    "alertType": alert['alert_type'],
                    "alertDesc": alert['alert_desc'],
                    "status": alert['alert_status'],
                    "severityLevel": alert['severity_level'],
                    "userName": alert['user_name'],
                    "timestamp": alert['alert_timestamp']
                }
            }
            features.append(feature)

    # 构造最终的 GeoJSON
    alert_json = {
        "type": "FeatureCollection",
        "features": features
    }

    # 返回 JSON 响应
    return jsonify(alert_json)



def generate_alert_chart():
    customerId = request.args.get('customerId')
    timeDimension = request.args.get('timeDimension')  # New parameter for time dimension

    if not customerId:
        return jsonify({'success': False, 'error': 'Missing customerId parameter'}), 400

    # Subquery to get all serial numbers for the given customer_id
    subquery = db.session.query(DeviceInfo.serial_number).filter(DeviceInfo.customer_id == customerId).subquery()

    # Base query using SQLAlchemy ORM
    query = db.session.query(
        db.func.count(AlertInfo.id).label('alertCount'),
        AlertInfo.severity_level
    ).filter(
        AlertInfo.device_sn.in_(subquery)  # Add the filter for device_sn
    )

    # Modify query based on time dimension
    if timeDimension == 'day':
        query = query.add_columns(db.func.hour(AlertInfo.alert_timestamp).label('timeUnit'))
    elif timeDimension == 'week':
        query = query.add_columns(db.func.dayofweek(AlertInfo.alert_timestamp).label('timeUnit'))
    elif timeDimension == 'month':
        query = query.add_columns(db.func.day(AlertInfo.alert_timestamp).label('timeUnit'))
    else:
        return jsonify({'success': False, 'error': 'Invalid timeDimension parameter'}), 400

    query = query.group_by('timeUnit', AlertInfo.severity_level).order_by('timeUnit')

    alert_counts = query.all()

    # Convert the result to a list of dictionaries
    alert_counts = [{'alertCount': count, 'severityLevel': severity_level, 'timeUnit': time_unit} for count, severity_level, time_unit in alert_counts]

    # Return the JSON response
    return jsonify({'success': True, 'data': alert_counts})


def test_wechat_alert():
    # 测试数据
    test_heart_rate = 140
    test_user_openid = WECHAT_USER_OPENID
    test_user_name = "测试用户"
    
    # Debug prints to check values
    print(f"Testing alert for user: {test_user_name}, heart rate: {test_heart_rate}")

    # 调用 send_wechat_alert 函数
    response = send_wechat_alert("心率异常", WECHAT_USER_OPENID, "测试用户", "二级")

    # 返回响应结果
    return jsonify(response)
def upload_common_event():
    try:
        data=request.json
        print(f"📡 [upload_common_event] 接口被调用")
        print(f"📡 [upload_common_event] 接收原始数据:{data}")
        
        #提取事件类型
        event_type=data.get('eventType','').split('.')[-1] #从com.tdtech.ohos.action.WEAR_STATUS_CHANGED提取WEAR_STATUS_CHANGED
        device_sn=data.get('deviceSn','')
        from .time_config import TimeConfig
        time_cfg = TimeConfig()
        alert_timestamp=data.get('timestamp', time_cfg.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        device_user_org=get_device_user_org_info(device_sn)
        if not device_user_org.get('success'):
            return jsonify({"status":"error","message":f"未找到{device_sn}的组织或用户"}),400
        
        
        #查询告警规则
        rule=AlertRules.query.filter_by(rule_type=event_type,is_deleted=False).first()
        if not rule:return jsonify({"status":"error","message":f"未找到{event_type}的告警规则"}),400
        
        #创建告警记录
        alert=AlertInfo(
            rule_id=rule.id,alert_type=event_type,device_sn=device_sn,
            alert_desc=f"{rule.alert_message}(事件值:{data.get('eventValue','')})",
            severity_level=rule.severity_level,latitude=data.get('latitude',22.54036796),
            longitude=data.get('longitude',114.01508952),altitude=data.get('altitude',0),
            org_id=device_user_org.get('org_id') if device_user_org.get('success') else None,
            user_id=device_user_org.get('user_id') if device_user_org.get('success') else None,
            alert_timestamp=alert_timestamp
        )
        db.session.add(alert)
        db.session.flush() #获取alert.id
        
        #处理健康数据
        health_id=None
        if data.get('healthData'):
            print(f"🏥 发现healthData字段: {data['healthData']}")
            
            # 检查healthData的结构
            health_data = data['healthData']
            if isinstance(health_data, dict):
                print(f"🏥 healthData是字典类型，键: {list(health_data.keys())}")
                
                # 尝试从不同的可能路径提取数据
                actual_health_data = None
                if 'data' in health_data:
                    actual_health_data = health_data['data']
                    print(f"🏥 从healthData.data提取: {actual_health_data}")
                else:
                    actual_health_data = health_data
                    print(f"🏥 直接使用healthData: {actual_health_data}")
                
                # 处理健康数据
                if actual_health_data:
                    from .user_health_data import process_single_health_data
                    print(f"🏥 准备处理健康数据: {actual_health_data}")
                    health_id = process_single_health_data(actual_health_data)
                    print(f"🏥 健康数据处理结果，health_id: {health_id}")
                    if health_id:
                        alert.health_id = health_id
                else:
                    print("🏥 ❌ 无法提取有效的健康数据")
            else:
                print(f"🏥 ❌ healthData不是字典类型: {type(health_data)}, 值: {health_data}")
        else:
            print("🏥 ❌ 数据中没有healthData字段")
        
        db.session.commit()
        
        # 🚨 Critical级别告警WebSocket实时推送到大屏
        if rule.severity_level == 'critical':
            try:
                from .bigScreen import socketio
                
                # 构建告警推送数据
                alert_data = {
                    'alert_id': alert.id,
                    'event_type': event_type,
                    'device_sn': device_sn,
                    'alert_desc': alert.alert_desc,
                    'severity_level': 'critical',
                    'alert_timestamp': alert_timestamp,
                    'user_name': device_user_org.get('user_name', '未知用户'),
                    'org_name': device_user_org.get('org_name', '未知组织'),
                    'latitude': alert.latitude,
                    'longitude': alert.longitude,
                    'health_id': health_id
                }
                
                # 通过WebSocket推送到大屏页面
                socketio.emit('critical_alert', alert_data, namespace='/')
                print(f"🚨 Critical告警已推送到大屏: {alert_data}")
                
            except Exception as ws_error:
                print(f"⚠️ WebSocket推送失败: {ws_error}")
        
        return jsonify({
            "status":"success","message":"事件处理成功","alert_id":alert.id,
            "event_type":event_type,"device_sn":device_sn,"health_id":health_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"事件处理失败:{e}")
        return jsonify({"status":"error","message":f"事件处理失败:{str(e)}"}),500

def acknowledge_alert():
    """告警确认接口"""
    try:
        data = request.json
        alert_id = data.get('alert_id')
        
        if not alert_id:
            return jsonify({"status": "error", "message": "缺少alert_id参数"}), 400
        
        # 更新告警状态为已确认
        alert = AlertInfo.query.filter_by(id=alert_id).first()
        if not alert:
            return jsonify({"status": "error", "message": "告警不存在"}), 404
        
        # 更新确认状态和时间
        alert.status = 'acknowledged'
        alert.acknowledged_at = get_now()
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "告警确认成功",
            "alert_id": alert_id
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"告警确认失败: {e}")
        return jsonify({
            "status": "error", 
            "message": f"告警确认失败: {str(e)}"
        }), 500




# 修改 alert.py 中的 upload_common_event
def upload_common_event1():
    """企业级通用事件上传接口 - 使用统一告警处理器"""
    try:
        data = request.json 
        logger.info(f"事件接收:{data}")
        
        # 🔥改造：使用统一告警处理器
        from .unified_alert_processor import get_unified_processor
        processor = get_unified_processor()
        
        # 提交到统一处理器
        alert_id = processor.submit_event_alert(data)
        
        return jsonify({
            "status": "success",
            "message": "事件已提交到统一处理器",
            "alert_id": alert_id,
            "event_type": data.get('eventType', ''),
            "device_sn": data.get('deviceSn', ''),
            "processing": "队列处理中"
        })
            
    except Exception as e:
        logger.error(f"事件接收失败: {e}")
        return jsonify({
            "status": "error", 
            "message": f"事件接收失败: {str(e)}"
        }), 500

def upload_common_event2():
    """企业级通用事件上传接口 - 使用队列处理架构"""
    try:
        data = request.json 
        print("🚀企业级事件接收:", data)
        
        # 使用新的系统事件处理器
        from .system_event_alert import process_common_event
        result = process_common_event(data)
        
        # 立即返回给客户端，后台队列异步处理
        if result['status'] == 'success':
            return jsonify({
                "status": "success",
                "message": result['message'],
                "event_type": data.get('eventType', ''),
                "device_sn": data.get('deviceSn', ''),
                "processing": "队列处理中"
            })
        else:
            return jsonify({
                "status": "error",
                "message": result['message']
            }), 500
            
    except Exception as e:
        print(f"❌企业级事件接收失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error", 
            "message": f"事件接收失败: {str(e)}"
        }), 500


def fetch_alert_rules():
    # Attempt to read alert rules from Redis
    alert_rules_data = redis.get('alert_rules')
    
    if alert_rules_data:
        # If data is found in Redis, parse it and return
        alert_rules = json.loads(alert_rules_data)
    else:
        # If not found in Redis, query the database
        alert_rules = AlertRules.query.all()
        # Store the fetched rules in Redis for future use
        alert_rules_data = {rule.id: rule.to_dict() for rule in alert_rules}  # Assuming AlertRules has a to_dict method
        redis.set('alert_rules', json.dumps(alert_rules_data))
    
    return jsonify({'success': True, 'alert_rules': alert_rules})

def generate_alerts(data, health_data_id):
    try:
        print(f"🔍 generate_alerts started with data keys: {list(data.keys()) if data else 'None'}")
        
        # 从数据库获取告警规则并转换为字典格式
        alert_rules = AlertRules.query.all()
        alert_rules_dict = {}
        
        # 将 SQLAlchemy 对象转换为字典
        for rule in alert_rules:
            rule_dict = {
                'id': rule.id,
                'rule_type': rule.rule_type,
                'physical_sign': rule.physical_sign,
                'threshold_min': rule.threshold_min,
                'threshold_max': rule.threshold_max,
                'trend_duration': rule.trend_duration,
                'severity_level': rule.severity_level,
                'alert_message': rule.alert_message
            }
            alert_rules_dict[rule.id] = rule_dict

        # 初始化异常计数器
        abnormal_counts = {}

        # 遍历每个告警规则
        for rule_id, rule in alert_rules_dict.items():
            if not rule.get('is_enabled', True):
                continue

            physical_sign = rule.get('physical_sign')
            
            # 检查physical_sign是否为空
            if not physical_sign:
                print(f"Skipping rule {rule_id}: missing physical_sign")
                continue
            
            # 修复threshold值的空值处理
            try:
                threshold_min_value = rule.get('threshold_min')
                if threshold_min_value is None or threshold_min_value == '':
                    threshold_min = 0
                else:
                    threshold_min = float(threshold_min_value)
            except (TypeError, ValueError):
                print(f"Invalid threshold_min for rule {rule_id}: {rule.get('threshold_min')}")
                threshold_min = 0
                
            try:
                threshold_max_value = rule.get('threshold_max')
                if threshold_max_value is None or threshold_max_value == '':
                    threshold_max = float('inf')
                else:
                    threshold_max = float(threshold_max_value)
            except (TypeError, ValueError):
                print(f"Invalid threshold_max for rule {rule_id}: {rule.get('threshold_max')}")
                threshold_max = float('inf')
            
            try:
                trend_duration_value = rule.get('trend_duration')
                if trend_duration_value is None or trend_duration_value == '':
                    trend_duration = 1
                else:
                    trend_duration = int(trend_duration_value)
            except (TypeError, ValueError):
                print(f"Invalid trend_duration for rule {rule_id}: {rule.get('trend_duration')}")
                trend_duration = 1

            # Special handling for blood pressure
            if physical_sign == 'bloodPressure':
                systolic = data.get('pressureHigh')
                diastolic = data.get('pressureLow')
                try:
                    # 修复空值处理：检查None值和空字符串
                    if systolic is None or systolic == '' or str(systolic).strip() == '':
                        systolic = None
                    else:
                        systolic = float(systolic)
                        
                    if diastolic is None or diastolic == '' or str(diastolic).strip() == '':
                        diastolic = None
                    else:
                        diastolic = float(diastolic)
                except (TypeError, ValueError) as e:
                    print(f"Invalid blood pressure values for rule {rule_id}: systolic={systolic}, diastolic={diastolic}, error={e}")
                    abnormal_counts[physical_sign] = 0  # Reset count if conversion fails
                    continue
                
                # Check if either systolic or diastolic is outside the thresholds
                if (systolic is not None and (systolic < threshold_min or systolic > threshold_max)) or \
                   (diastolic is not None and (diastolic < threshold_min or diastolic > threshold_max)):
                    
                    # Update abnormal count for this physical sign
                    abnormal_counts[physical_sign] = abnormal_counts.get(physical_sign, 0) + 1
                else:
                    abnormal_counts[physical_sign] = 0  # Reset count if within range

            else:
                # General case for other physical signs
                value = data.get(physical_sign)
                
                try:
                    # 修复空字符串和None值的处理
                    if value is None or value == '' or str(value).strip() == '':
                        value = None
                    else:
                        value = float(value)
                except (TypeError, ValueError) as e:
                    print(f"Invalid value for rule {rule_id}, physical_sign={physical_sign}: value={value}, error={e}")
                    abnormal_counts[physical_sign] = 0  # Reset count if conversion fails
                    continue

                if value is not None and (value < threshold_min or value > threshold_max):
                    # Update abnormal count for this physical sign
                    abnormal_counts[physical_sign] = abnormal_counts.get(physical_sign, 0) + 1
                else:
                    abnormal_counts[physical_sign] = 0  # Reset count if within range

            # If abnormal count exceeds the trend_duration, generate alert
            if abnormal_counts.get(physical_sign, 0) >= trend_duration:
                print("generate_alerts:abnormal_counts:", abnormal_counts)
                
                # 获取设备的用户和组织信息
                device_user_org = get_device_user_org_info(data.get('deviceSn', 'Unknown'))
                
                # Create an alert
                alert_info_instance = AlertInfo(
                    rule_id=rule_id,
                    alert_type=rule['rule_type'],
                    device_sn=data.get('deviceSn', 'Unknown'),
                    alert_timestamp=get_now(), #使用统一时间配置
                    alert_desc=rule['alert_message'],
                    severity_level=rule['severity_level'],
                    alert_status='pending',
                    health_id=health_data_id,
                    org_id=device_user_org.get('org_id') if device_user_org.get('success') else None,
                    user_id=device_user_org.get('user_id') if device_user_org.get('success') else None
                )
                print("generate_alerts:alert_info_instance:", alert_info_instance)
                db.session.add(alert_info_instance)

        db.session.commit()
        print(f"✅ generate_alerts completed successfully")
        return jsonify({'success': True})

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ Error in generate_alerts: {e}")
        print(f"📋 Full error details: {error_details}")
        print(f"📊 Data passed to function: {data}")
        print(f"🆔 Health data ID: {health_data_id}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

