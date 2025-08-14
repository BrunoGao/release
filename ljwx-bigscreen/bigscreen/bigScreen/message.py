import json
from flask import request, jsonify
from .models import DeviceMessage, DeviceMessageDetail, db, DeviceInfo, UserInfo, UserOrg, OrgInfo
from .redis_helper import RedisHelper
from datetime import datetime, timedelta
from .org import fetch_departments_by_orgId


redis = RedisHelper()
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
            DeviceMessage.department_info,
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
            # 获取用户所在的组织ID
            user_org = UserOrg.query.filter_by(user_id=userId).first()
            print(f"DEBUG: user_org 查询结果: {user_org}")
            if not user_org:
                ##print(f"DEBUG: 用户 {userId} 没有找到组织关联，尝试查找用户信息")
                # 尝试直接查找用户信息
                user_info = UserInfo.query.filter_by(id=userId).first()
                #print(f"DEBUG: user_info 查询结果: {user_info}")
                if not user_info:
                    raise Exception(f"User {userId} not found")
                # 尝试使用orgId作为组织ID
                org_id = int(orgId) if orgId else None
                if not org_id:
                    raise Exception("User organization not found and no orgId provided")
                #print(f"DEBUG: 使用提供的orgId {org_id} 作为用户组织")
            else:
                org_id = user_org.org_id
                #print(f"DEBUG: 从user_org获取到org_id: {org_id}")
            
            # 1. 获取用户个人消息
            personal_messages = base_query.filter(DeviceMessage.user_id == userId).all()
            #print(f"DEBUG: 用户个人消息数量: {len(personal_messages)}")
            
            # 2. 获取用户所在组织及其所有上级组织的ID
            org_info = OrgInfo.query.filter_by(id=org_id).first()
            #print(f"DEBUG: org_info 查询结果: {org_info}")
            if not org_info:
                #print(f"DEBUG: 组织 {org_id} 不存在，尝试查询所有消息")
                # 如果组织不存在，直接查询所有相关消息
                announcement_messages = base_query.filter(
                    DeviceMessage.user_id == None
                ).all()
            else:
                ancestor_org_ids = [int(id) for id in org_info.ancestors.split(',') if id != '0'] if org_info.ancestors else []
                ancestor_org_ids.append(org_id)
                #print(f"DEBUG: ancestor_org_ids: {ancestor_org_ids}")
                
                # 3. 获取这些组织的公告消息
                announcement_messages = base_query.filter(
                    DeviceMessage.department_info.in_(ancestor_org_ids),
                    DeviceMessage.user_id == None
                ).all()
            
            #print(f"DEBUG: 公告消息数量: {len(announcement_messages)}")

        else:
            # 如果只提供了orgId
            if not orgId:
                raise Exception("Either userId or orgId must be provided")

            # 1. 获取组织及其所有上级组织的ID
            org_info = OrgInfo.query.filter_by(id=orgId).first()
            if not org_info:
                raise Exception("Organization not found")
            
            ancestor_org_ids = [int(id) for id in org_info.ancestors.split(',') if id != '0'] if org_info.ancestors else []
            #print("ancestor_org_ids:", ancestor_org_ids)
            ancestor_org_ids.append(int(orgId))

            # 2. 获取下属组织ID（包括所有子部门）
            departments_response = fetch_departments_by_orgId(orgId)
            #print("departments_response:", departments_response)
            
            subordinate_org_ids = []
            if departments_response['success'] and departments_response['data']:
                # 递归提取所有部门ID
                subordinate_org_ids = extract_department_ids(departments_response['data'])
            
            #print("subordinate_org_ids:", subordinate_org_ids)
            all_org_ids = list(set(ancestor_org_ids + subordinate_org_ids))
            #print("all_org_ids:", all_org_ids)

            # 3. 获取所有相关消息
            # 3.1 获取所有公告消息（包括上级组织的公告）
            announcement_messages = base_query.filter(
                DeviceMessage.department_info.in_([str(id) for id in all_org_ids]),
                DeviceMessage.user_id == None
            ).all()

            # 3.2 获取下属组织所有用户的个人消息
            personal_messages = base_query.filter(
                DeviceMessage.department_info.in_([str(id) for id in subordinate_org_ids]),
                DeviceMessage.user_id != None
            ).all()

        # 处理消息并添加到结果列表
        def process_messages(messages, is_public=False):
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
                    dept_id = str(msg.department_info)
                    dept_name = OrgInfo.query.filter_by(id=dept_id).first()
                    message_dict = {
                        'department_name': dept_name.name if dept_name else 'Unknown Department',
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

