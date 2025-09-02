from flask import Blueprint, request, jsonify
from models.interface import Interface
from models.health_data_config import HealthDataConfig
from models.customer_config import CustomerConfig
from utils.response import success, error

config_bp = Blueprint('config', __name__)

# 获取接口配置
@config_bp.route('/get_interface_config', methods=['GET'])
def get_interface_config():
    try:
        configs = Interface.query.all()
        data = {config.key: config.value for config in configs}
        return success(data)
    except Exception as e:
        return error(str(e))

# 保存接口配置
@config_bp.route('/save_interface_config', methods=['POST'])
def save_interface_config():
    try:
        data = request.get_json()
        for key, value in data.items():
            config = Interface.query.filter_by(key=key).first()
            if config:
                config.value = value
            else:
                config = Interface(key=key, value=value)
                config.save()
        return success('接口配置保存成功')
    except Exception as e:
        return error(str(e))

# 获取健康数据配置
@config_bp.route('/get_health_config', methods=['GET'])
def get_health_config():
    try:
        configs = HealthDataConfig.query.all()
        data = {config.key: config.value for config in configs}
        return success(data)
    except Exception as e:
        return error(str(e))

# 保存健康数据配置
@config_bp.route('/save_health_config', methods=['POST'])
def save_health_config():
    try:
        data = request.get_json()
        for key, value in data.items():
            config = HealthDataConfig.query.filter_by(key=key).first()
            if config:
                config.value = value
            else:
                config = HealthDataConfig(key=key, value=value)
                config.save()
        return success('健康数据配置保存成功')
    except Exception as e:
        return error(str(e))

# 获取客户配置
@config_bp.route('/get_customer_config', methods=['GET'])
def get_customer_config():
    try:
        configs = CustomerConfig.query.all()
        data = {config.key: config.value for config in configs}
        return success(data)
    except Exception as e:
        return error(str(e))

# 保存客户配置
@config_bp.route('/save_customer_config', methods=['POST'])
def save_customer_config():
    try:
        data = request.get_json()
        for key, value in data.items():
            config = CustomerConfig.query.filter_by(key=key).first()
            if config:
                config.value = value
            else:
                config = CustomerConfig(key=key, value=value)
                config.save()
        return success('客户配置保存成功')
    except Exception as e:
        return error(str(e))

# 获取最优配置
@config_bp.route('/get_optimal_config', methods=['GET'])
def get_optimal_config():
    try:
        # 获取所有配置
        interface_configs = Interface.query.all()
        health_configs = HealthDataConfig.query.all()
        customer_configs = CustomerConfig.query.all()
        
        # 转换为字典格式
        data = {
            'interface': {config.key: config.value for config in interface_configs},
            'health': {config.key: config.value for config in health_configs},
            'customer': {config.key: config.value for config in customer_configs}
        }
        
        return success(data)
    except Exception as e:
        return error(str(e)) 