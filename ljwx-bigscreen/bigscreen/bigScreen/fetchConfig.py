from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
import mysql.connector
from .models import HealthDataConfig, CustomerConfig, Interface, db
from .device import fetch_customer_id_by_deviceSn, fetch_user_info_by_deviceSn

app = Flask(__name__)
CORS(app)

# Database configuration
import os
config = {
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', '123456'),
    'host': os.getenv('MYSQL_HOST', 'mysql' if os.getenv('IS_DOCKER', 'false').lower() == 'true' else '127.0.0.1'),
    'database': os.getenv('MYSQL_DATABASE', 'lj-06'),
    'raise_on_warnings': True
}

def copy_health_data_config(old_customer_id, new_customer_id):
    # Fetch all configurations with customer_id 8
    health_data_config = HealthDataConfig.query.filter_by(customer_id=old_customer_id).all()

    for health_data in health_data_config:
        print("health_data", health_data)
        new_health_data = HealthDataConfig(
            customer_id=new_customer_id,
            data_type=health_data.data_type,
            frequency_interval=health_data.frequency_interval,
            is_realtime=health_data.is_realtime,
            is_enabled=health_data.is_enabled,
            is_default=health_data.is_default,
            warning_high=health_data.warning_high,
            warning_low=health_data.warning_low,
            warning_cnt=health_data.warning_cnt
        )
        print("new_health_data", new_health_data)
        db.session.add(new_health_data)  # Add the new entry to the session
    
    db.session.commit()  # Commit the changes to the database
    
    interface_config = Interface.query.filter_by(customer_id=old_customer_id).all()
    for interface in interface_config:
        new_interface = Interface(
            customer_id=new_customer_id,
            name=interface.name,
            url=interface.url,
            call_interval=interface.call_interval,
            method=interface.method,
            description=interface.description,
            is_enabled=interface.is_enabled,
            api_id=interface.api_id,
            api_auth=interface.api_auth,
            create_user=interface.create_user,
            create_user_id=interface.create_user_id,
            create_time=interface.create_time,
            update_user=interface.update_user,
            update_user_id=interface.update_user_id,
            update_time=interface.update_time
            # Copy other fields from interface as needed
        )
        print("new_interface", new_interface)
        db.session.add(new_interface)  # Add the new entry to the session
    db.session.commit()  # Commit the changes to the database
    
    customer_config = CustomerConfig.query.filter_by(id=old_customer_id).first()
    # Check if the new_customer_id already exists
    existing_customer = CustomerConfig.query.filter_by(id=new_customer_id).first()
    if existing_customer:
        return jsonify({"success": False, "error": "Customer ID already exists"}), 400

    new_customer_config = CustomerConfig(
        id=new_customer_id,
        customer_name=customer_config.customer_name,
        upload_method=customer_config.upload_method,
        is_support_license=customer_config.is_support_license,
        license_key=customer_config.license_key,
        os_version=customer_config.os_version,
        create_user=customer_config.create_user,
        create_user_id=customer_config.create_user_id,
        create_time=customer_config.create_time,
        update_user=customer_config.update_user,
        update_user_id=customer_config.update_user_id,
        update_time=customer_config.update_time
        # Copy other fields from customer_config as needed
    )
    print("new_customer_config", new_customer_config)
    db.session.add(new_customer_config)  # Add the new entry to the session
    db.session.commit()  # Commit the changes to the database   
    
    return jsonify({"success": True, "message": "Configuration copied successfully"})


def fetch_health_data_config(customer_id=None,deviceSn=None):
    if customer_id is None:
        customer_id = request.args.get('customerId')  # Get customerId from request parameters
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')  # Get deviceSn from request parameters
    
    # 获取设备的完整客户信息
    device_info = fetch_user_info_by_deviceSn(deviceSn)
    customerId = device_info.get('customer_id', '0')
    orgId = device_info.get('org_id')
    userId = device_info.get('user_id')
    
    print("fetchHealthDataConfig - customerId:", customerId, "orgId:", orgId, "userId:", userId)
    if not customerId or customerId == '0':
        return jsonify({"success": False, "error": "customerId parameter is required"}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
            h.data_type,
            h.frequency_interval,
            h.is_enabled,
            h.is_realtime,
            h.warning_high,
            h.warning_low,
            h.warning_cnt,
            c.customer_name,
            c.upload_method,
            c.is_support_license,
            c.license_key,
            c.enable_resume,
            c.upload_retry_count,
            c.cache_max_count,
            c.upload_retry_interval,
            i.name               AS interface_name,
            i.url                AS interface_url,
            i.call_interval      AS interface_call_interval,
            i.is_enabled         AS interface_is_enabled,
            i.api_id             AS interface_api_id,
            i.api_auth           AS interface_api_auth
            FROM t_health_data_config h
            JOIN t_customer_config   c ON h.customer_id = c.id
            JOIN t_interface         i ON h.customer_id = i.customer_id
            WHERE h.customer_id = %s
        """
        cursor.execute(query, (customerId,))
        result = cursor.fetchall()

        # Format the result into the desired JSON structure
        config_data = {
            "customer_name": result[0]['customer_name'] if result else None,
            "customer_id": customerId,
            "org_id": orgId,
            "user_id": userId,
            "upload_method": result[0]['upload_method'] if result else 'wifi',  # Default to 'wifi' if None
            "enable_resume": result[0]['enable_resume'] if result else False,
            "upload_retry_count": result[0]['upload_retry_count'] if result else 3,
            "cache_max_count": result[0]['cache_max_count'] if result else 100,
            "upload_retry_interval": result[0]['upload_retry_interval'] if result else 5,
            "health_data": {
                row['data_type']: f"{row['frequency_interval']}:{row['is_enabled']}:{row['is_realtime']}:" +
                                  f"{row['warning_high'] if row['warning_high'] is not None else -1}:" +
                                  f"{row['warning_low'] if row['warning_low'] is not None else -1}:" +
                                  f"{row['warning_cnt'] if row['warning_cnt'] is not None else -1}"
                for row in result
            },
            "is_support_license": result[0]['is_support_license'] if result else False,
            "license_key": result[0]['license_key'] if result else None,
            "interface_data": {
                row['interface_name']: f"{row['interface_url']};{row['interface_call_interval']};{row['interface_is_enabled']};" +
                                       f"{row['interface_api_id']};{row['interface_api_auth']}"
                for row in result
            }
        }

        return jsonify(config_data)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()
def fetch_health_data_config_bak(customer_id=None,deviceSn=None):
    if customer_id is None:
        customer_id = request.args.get('customerId')  # Get customerId from request parameters
    if deviceSn is None:
        deviceSn = request.args.get('deviceSn')  # Get deviceSn from request parameters
    
    # 获取设备的完整客户信息
    device_info = fetch_user_info_by_deviceSn(deviceSn)
    customerId = device_info.get('customer_id', '0')
    orgId = device_info.get('org_id')
    userId = device_info.get('user_id')
    
    print("fetchHealthDataConfig_bak - customerId:", customerId, "orgId:", orgId, "userId:", userId)
    if not customerId or customerId == '0':
        return jsonify({"success": False, "error": "customerId parameter is required"}), 400

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT h.data_type, h.frequency_interval, h.is_enabled, h.is_realtime, h.warning_high, h.warning_low, h.warning_cnt,
                   c.customer_name, c.upload_method, c.is_support_license,
                   c.license_key, i.name as interface_name, i.url as interface_url, i.call_interval as interface_call_interval,
                   i.is_enabled as interface_is_enabled, i.api_id as interface_api_id, i.api_auth as interface_api_auth
            FROM t_health_data_config h
            JOIN t_customer_config c ON h.customer_id = c.id
            JOIN t_interface i ON h.customer_id = i.customer_id
            WHERE h.customer_id = %s
        """
        cursor.execute(query, (customerId,))
        result = cursor.fetchall()

        # Format the result into the desired JSON structure
        config_data = {
            "customer_name": result[0]['customer_name'] if result else None,
            "customer_id": customerId,
            "org_id": orgId,
            "user_id": userId,
            "upload_method": result[0]['upload_method'] if result else 'wifi',  # Default to 'wifi' if None
            "health_data": {
                row['data_type']: f"{row['frequency_interval']}:{row['is_enabled']}:{row['is_realtime']}:" +
                                  f"{row['warning_high'] if row['warning_high'] is not None else -1}:" +
                                  f"{row['warning_low'] if row['warning_low'] is not None else -1}:" +
                                  f"{row['warning_cnt'] if row['warning_cnt'] is not None else -1}"
                for row in result
            },
            "is_support_license": result[0]['is_support_license'] if result else False,
            "license_key": result[0]['license_key'] if result else None,
            "interface_data": {
                row['interface_name']: f"{row['interface_url']};{row['interface_call_interval']};{row['interface_is_enabled']};" +
                                       f"{row['interface_api_id']};{row['interface_api_auth']}"
                for row in result
            }
        }

        return jsonify(config_data)
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return jsonify({"success": False, "error": str(err)}), 500
    finally:
        cursor.close()
        connection.close()
def main():
    app.run(host='0.0.0.0', port=6063, debug=True)

if __name__ == "__main__":
    main()

config_bp = Blueprint('config', __name__)

@config_bp.route('/get_interface_config', methods=['GET'])
def get_interface_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        interfaces = Interface.query.filter_by(customer_id=customer_id).all()
        config = {interface.name: interface.url for interface in interfaces}
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@config_bp.route('/save_interface_config', methods=['POST'])
def save_interface_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        data = request.get_json()
        for name, url in data.items():
            interface = Interface.query.filter_by(customer_id=customer_id, name=name).first()
            if interface:
                interface.url = url
            else:
                interface = Interface(customer_id=customer_id, name=name, url=url)
                db.session.add(interface)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@config_bp.route('/get_health_config', methods=['GET'])
def get_health_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        configs = HealthDataConfig.query.filter_by(customer_id=customer_id).all()
        config = {}
        for cfg in configs:
            config[cfg.data_type] = {
                'frequency_interval': cfg.frequency_interval,
                'is_enabled': cfg.is_enabled,
                'is_realtime': cfg.is_realtime,
                'warning_cnt': cfg.warning_cnt,
                'warning_high': cfg.warning_high,
                'warning_low': cfg.warning_low,
                'weight': cfg.weight
            }
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@config_bp.route('/save_health_config', methods=['POST'])
def save_health_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        data = request.get_json()
        for data_type, config in data.items():
            health_config = HealthDataConfig.query.filter_by(customer_id=customer_id, data_type=data_type).first()
            if health_config:
                health_config.frequency_interval = config.get('frequency_interval')
                health_config.is_enabled = config.get('is_enabled')
                health_config.is_realtime = config.get('is_realtime')
                health_config.warning_cnt = config.get('warning_cnt')
                health_config.warning_high = config.get('warning_high')
                health_config.warning_low = config.get('warning_low')
            else:
                health_config = HealthDataConfig(
                    customer_id=customer_id,
                    data_type=data_type,
                    frequency_interval=config.get('frequency_interval'),
                    is_enabled=config.get('is_enabled'),
                    is_realtime=config.get('is_realtime'),
                    warning_cnt=config.get('warning_cnt'),
                    warning_high=config.get('warning_high'),
                    warning_low=config.get('warning_low')
                )
                db.session.add(health_config)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@config_bp.route('/get_customer_config', methods=['GET'])
def get_customer_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        customer = CustomerConfig.query.filter_by(id=customer_id).first()
        if not customer:
            return jsonify({'success': False, 'error': '客户不存在'})
            
        config = {
            customer_id: {
                'customer_name': customer.customer_name,
                'is_support_license': customer.is_support_license,
                'license_key': customer.license_key,
                'os_version': customer.os_version,
                'upload_method': customer.upload_method
            }
        }
        return jsonify({'success': True, 'data': config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@config_bp.route('/save_customer_config', methods=['POST'])
def save_customer_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        data = request.get_json()
        customer = CustomerConfig.query.filter_by(id=customer_id).first()
        if not customer:
            return jsonify({'success': False, 'error': '客户不存在'})
            
        customer.customer_name = data.get('customer_name')
        customer.is_support_license = data.get('is_support_license')
        customer.license_key = data.get('license_key')
        customer.os_version = data.get('os_version')
        customer.upload_method = data.get('upload_method')
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@config_bp.route('/get_optimal_config', methods=['GET'])
def get_optimal_config():
    try:
        customer_id = request.args.get('customerId')
        if not customer_id:
            return jsonify({'success': False, 'error': '缺少 customerId 参数'})
            
        # 获取所有配置
        interfaces = Interface.query.filter_by(customer_id=customer_id).all()
        health_configs = HealthDataConfig.query.filter_by(customer_id=customer_id).all()
        customer = CustomerConfig.query.filter_by(id=customer_id).first()
        
        if not customer:
            return jsonify({'success': False, 'error': '客户不存在'})
            
        # 构建最优配置
        optimal_config = {
            'interface': {interface.name: interface.url for interface in interfaces},
            'health': {
                config.data_type: {
                    'frequency_interval': config.frequency_interval,
                    'is_enabled': config.is_enabled,
                    'is_realtime': config.is_realtime,
                    'warning_cnt': config.warning_cnt,
                    'warning_high': config.warning_high,
                    'warning_low': config.warning_low
                } for config in health_configs
            },
            'customer': {
                customer_id: {
                    'customer_name': customer.customer_name,
                    'is_support_license': customer.is_support_license,
                    'license_key': customer.license_key,
                    'os_version': customer.os_version,
                    'upload_method': customer.upload_method
                }
            }
        }
        
        return jsonify({'success': True, 'data': optimal_config})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
