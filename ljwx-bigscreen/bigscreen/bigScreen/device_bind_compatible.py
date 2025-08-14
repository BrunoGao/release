from flask import Blueprint, request, jsonify, render_template, current_app, url_for
from .models import db, DeviceInfo, DeviceUser, DeviceBindRequest, UserInfo
import io, base64, hmac, hashlib, time, uuid
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, desc

device_bind_bp = Blueprint('device_bind', __name__, url_prefix='/api/device')

def generate_simple_qr_url(device_sn, timestamp, signature):
    """生成简单的文本二维码URL，如果qrcode库不可用则返回URL链接"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=8, border=4)
        url = f"{request.host_url}api/device/bind/apply?sn={device_sn}&ts={timestamp}&sign={signature}"
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        
        return {
            'qrcode': f"data:image/png;base64,{img_b64}",
            'url': url,
            'type': 'image'
        }
    except ImportError:
        # qrcode库不可用时返回文本链接
        url = f"{request.host_url}api/device/bind/apply?sn={device_sn}&ts={timestamp}&sign={signature}"
        return {
            'qrcode': None,
            'url': url,
            'type': 'url',
            'message': '二维码库未安装，请直接访问链接或安装qrcode[pil]库'
        }

@device_bind_bp.route('/<sn>/qrcode', methods=['GET'])
def get_device_qrcode(sn):
    try:
        device = DeviceInfo.query.filter_by(serial_number=sn, is_deleted=False).first()
        if not device: 
            return jsonify({'code': 404, 'msg': '设备不存在'}), 404
        
        ts = int(time.time())
        secret = current_app.config.get('SECRET_KEY', 'ljwx-secret')
        sign = hmac.new(f"{secret}".encode(), f"{sn}:{ts}".encode(), hashlib.sha256).hexdigest()[:16]
        
        qr_data = generate_simple_qr_url(sn, ts, sign)
        
        return jsonify({'code': 200, 'data': qr_data})
    except Exception as e:
        return jsonify({'code': 500, 'msg': f'生成失败: {str(e)}'}), 500

@device_bind_bp.route('/bind/apply', methods=['GET', 'POST'])
def bind_apply():
    if request.method == 'GET':
        sn = request.args.get('sn')
        ts = request.args.get('ts')
        sign = request.args.get('sign')
        
        if not all([sn, ts, sign]): 
            return "参数错误", 400
        if int(time.time()) - int(ts) > 3600: 
            return "二维码已过期", 400
        
        secret = current_app.config.get('SECRET_KEY', 'ljwx-secret')
        valid_sign = hmac.new(f"{secret}".encode(), f"{sn}:{ts}".encode(), hashlib.sha256).hexdigest()[:16]
        if sign != valid_sign: 
            return "签名无效", 400
        
        device = DeviceInfo.query.filter_by(serial_number=sn, is_deleted=False).first()
        return render_template('device_bind_apply.html', device=device, sn=sn, ts=ts, sign=sign)
    
    data = request.get_json()
    sn, user_id, org_id = data.get('sn'), data.get('user_id'), data.get('org_id')
    
    try:
        device = DeviceInfo.query.filter_by(serial_number=sn, is_deleted=False).first()
        if not device: 
            return jsonify({'code': 404, 'msg': '设备不存在'})
        if device.user_id: 
            return jsonify({'code': 400, 'msg': '设备已绑定'})
        
        existing = DeviceBindRequest.query.filter_by(device_sn=sn, status='PENDING', is_deleted=False).first()
        if existing: 
            return jsonify({'code': 400, 'msg': '已有待审批申请'})
        
        req = DeviceBindRequest(device_sn=sn, user_id=user_id, org_id=org_id)
        db.session.add(req)
        db.session.commit()
        
        return jsonify({'code': 200, 'msg': '申请提交成功', 'data': {'id': req.id}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'提交失败: {str(e)}'})

@device_bind_bp.route('/bind/approve', methods=['POST'])
def approve_bind():
    data = request.get_json()
    req_ids, action, approver_id, comment = data.get('ids', []), data.get('action'), data.get('approver_id'), data.get('comment', '')
    
    if action not in ['APPROVED', 'REJECTED']: 
        return jsonify({'code': 400, 'msg': '操作无效'})
    
    try:
        reqs = DeviceBindRequest.query.filter(DeviceBindRequest.id.in_(req_ids), DeviceBindRequest.status=='PENDING').all()
        success_count = 0
        
        for req in reqs:
            if action == 'APPROVED':
                device = DeviceInfo.query.filter_by(serial_number=req.device_sn, is_deleted=False).first()
                if device and not device.user_id:
                    device.user_id, device.org_id = req.user_id, req.org_id
                    DeviceUser(device_sn=req.device_sn, user_id=req.user_id, user_name=f"用户{req.user_id}", status='BIND').save()
            
            req.status, req.approve_time, req.approver_id, req.comment = action, datetime.utcnow(), approver_id, comment
            success_count += 1
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': f'处理完成: {success_count}个申请'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'处理失败: {str(e)}'})

@device_bind_bp.route('/bind/manual', methods=['POST'])
def manual_bind():
    data = request.get_json()
    device_sn, user_id, org_id, operator_id = data.get('device_sn'), data.get('user_id'), data.get('org_id'), data.get('operator_id')
    
    try:
        device = DeviceInfo.query.filter_by(serial_number=device_sn, is_deleted=False).first()
        if not device: 
            return jsonify({'code': 404, 'msg': '设备不存在'})
        if device.user_id: 
            return jsonify({'code': 400, 'msg': '设备已绑定'})
        
        device.user_id, device.org_id = user_id, org_id
        DeviceUser(device_sn=device_sn, user_id=user_id, user_name=f"用户{user_id}", status='BIND', create_user_id=operator_id).save()
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '绑定成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'绑定失败: {str(e)}'})

@device_bind_bp.route('/unbind', methods=['POST'])
def unbind_device():
    data = request.get_json()
    device_sn, operator_id, reason = data.get('device_sn'), data.get('operator_id'), data.get('reason', '')
    
    try:
        device = DeviceInfo.query.filter_by(serial_number=device_sn, is_deleted=False).first()
        if not device: 
            return jsonify({'code': 404, 'msg': '设备不存在'})
        if not device.user_id: 
            return jsonify({'code': 400, 'msg': '设备未绑定'})
        
        old_user_id = device.user_id
        device.user_id, device.org_id = None, None
        DeviceUser(device_sn=device_sn, user_id=old_user_id, user_name=f"用户{old_user_id}", status='UNBIND', create_user_id=operator_id).save()
        
        db.session.commit()
        return jsonify({'code': 200, 'msg': '解绑成功'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'msg': f'解绑失败: {str(e)}'})

@device_bind_bp.route('/bind/requests', methods=['GET'])
def get_bind_requests():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    status = request.args.get('status')
    
    query = DeviceBindRequest.query.filter_by(is_deleted=False)
    if status: query = query.filter_by(status=status)
    
    pagination = query.order_by(desc(DeviceBindRequest.apply_time)).paginate(page=page, per_page=size, error_out=False)
    
    items = []
    for req in pagination.items:
        item = req.to_dict()
        device = DeviceInfo.query.filter_by(serial_number=req.device_sn).first()
        user = UserInfo.query.filter_by(id=req.user_id).first() if hasattr(UserInfo, 'query') else None
        
        item.update({
            'device_name': device.device_name if device else '未知设备',
            'user_name': user.user_name if user else f'用户{req.user_id}',
            'org_name': f'组织{req.org_id}'
        })
        items.append(item)
    
    return jsonify({'code': 200, 'data': {'items': items, 'total': pagination.total, 'pages': pagination.pages}})

@device_bind_bp.route('/bind/logs', methods=['GET'])
def get_bind_logs():
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    device_sn = request.args.get('device_sn')
    user_id = request.args.get('user_id')
    
    query = DeviceUser.query.filter_by(is_deleted=False)
    if device_sn: query = query.filter_by(device_sn=device_sn)
    if user_id: query = query.filter_by(user_id=int(user_id))
    
    pagination = query.order_by(desc(DeviceUser.operate_time)).paginate(page=page, per_page=size, error_out=False)
    
    items = [{'id': log.id, 'device_sn': log.device_sn, 'user_id': log.user_id, 'user_name': log.user_name, 
             'status': log.status, 'operate_time': log.operate_time.strftime('%Y-%m-%d %H:%M:%S')} for log in pagination.items]
    
    return jsonify({'code': 200, 'data': {'items': items, 'total': pagination.total}})

# 安装指南API
@device_bind_bp.route('/install-guide', methods=['GET'])
def install_guide():
    return jsonify({
        'code': 200,
        'msg': '依赖安装指南',
        'data': {
            'qrcode_install': {
                'command': 'pip install qrcode[pil]',
                'description': '安装二维码生成库以启用图片二维码功能',
                'alternative': '不安装时系统将提供文本链接作为替代方案'
            }
        }
    }) 