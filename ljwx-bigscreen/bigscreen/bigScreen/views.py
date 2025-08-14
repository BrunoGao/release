from flask import Blueprint, jsonify, render_template, request #添加缺失导入#
from .models import OrgInfo, UserInfo, UserOrg, db #修复db导入路径#

# 创建蓝图
bp = Blueprint('views', __name__)

@bp.route('/test')
def test_page():
    return render_template('test.html')

@bp.route('/get_organizations')
def get_organizations():
    try:
        orgs = db.session.query(OrgInfo).filter(
            OrgInfo.is_deleted.is_(False),
            OrgInfo.status == '1'
        ).all()
        
        org_list = [{
            'id': str(org.id),
            'name': org.name,
            'parent_id': str(org.parent_id) if org.parent_id else None
        } for org in orgs]
        
        return jsonify({
            'success': True,
            'data': org_list
        })
    except Exception as e:
        print("Error:", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        })

@bp.route('/get_users_by_orgId')
def get_users_by_orgId():
    try:
        from .admin_helper import admin_helper  # 导入admin判断工具
        
        org_id = request.args.get('orgId')
        if not org_id:
            return jsonify({
                'success': False,
                'error': 'Missing orgId parameter'
            })

        users = db.session.query(
            UserInfo
        ).join(
            UserOrg,
            UserInfo.id == UserOrg.user_id
        ).filter(
            UserOrg.org_id == org_id,
            UserInfo.is_deleted.is_(False),
            UserInfo.status == '1'
        ).all()
        
        user_list = [{
            'id': str(user.id),
            'user_name': user.user_name,
            'device_sn': user.device_sn
        } for user in users]
        
        # 过滤掉管理员用户
        filtered_user_list = admin_helper.filter_non_admin_users(user_list, 'id')
        
        return jsonify({
            'success': True,
            'data': filtered_user_list
        })
    except Exception as e:
        print("Error:", str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }) 