# your_package/models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, Enum, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Integer, Numeric, Float, DateTime, Boolean, JSON, SmallInteger, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

Base = declarative_base()

def datetime_to_str(dt):
    """Convert a datetime object to a string."""
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else None
# ... existing code ...

class Interface(db.Model):
    __tablename__ = 't_interface'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(200), nullable=False)
    call_interval = db.Column(db.Integer, nullable=False)
    method = db.Column(db.Enum('upload', 'fetch'), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=True)
    customer_id = db.Column(db.BigInteger, nullable=True)
    api_id = db.Column(db.String(50), nullable=True)
    api_auth = db.Column(db.String(200), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.TIMESTAMP, default=func.current_timestamp(), nullable=True)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)


class UserAlert(db.Model):
    __tablename__ = 't_user_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    userName = db.Column(db.String(64), nullable=False)
    phoneNumber = db.Column(db.String(20), nullable=False)
    alertType = db.Column(db.String(64), nullable=False)
    latitude = db.Column(db.Float, nullable=False, default=0.0)
    longitude = db.Column(db.Float, nullable=False, default=0.0)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    deviceSn = db.Column(db.String(255), nullable=False)
    severityLevel = db.Column(db.String(255), nullable=False)
    alertStatus = db.Column(db.String(255), nullable=False)
    
    def __init__(self, userName, phoneNumber, alertType, latitude, longitude, timestamp, deviceSn, severityLevel, alertStatus):
        self.userName = userName
        self.phoneNumber = phoneNumber
        self.alertType = alertType
        self.latitude = latitude
        self.longitude = longitude
        self.timestamp = timestamp
        self.deviceSn = deviceSn
        self.severityLevel = severityLevel
        self.alertStatus = alertStatus

class DeviceMessage(db.Model):
    __tablename__ = 't_device_message'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_sn = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)   
    org_id = db.Column(db.String(50), nullable=True)  # 修改: department_info -> org_id
    user_id = db.Column(db.String(50), nullable=True)
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，继承自设备所属租户')
    message_type = db.Column(db.String(50), nullable=False)
    sender_type = db.Column(db.String(50), nullable=False)
    receiver_type = db.Column(db.String(50), nullable=False)
    message_status = db.Column(db.String(50), default='pending', nullable=False)
    responded_number = db.Column(db.Integer, default=0, nullable=False)
    sent_time = db.Column(db.DateTime, default=datetime.utcnow)
    received_time = db.Column(db.DateTime, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)

class DeviceMessageDetail(db.Model):
    __tablename__ = 't_device_message_detail'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    message_id = db.Column(db.BigInteger, nullable=False)
    device_sn = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), nullable=False)
    sender_type = db.Column(db.String(50), nullable=False)
    receiver_type = db.Column(db.String(50), nullable=False)
    message_status = db.Column(db.String(50), default='pending', nullable=False)
    sent_time = db.Column(db.DateTime, default=datetime.utcnow)
    received_time = db.Column(db.DateTime, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False)
    
class HealthDataConfig(db.Model):
    __tablename__ = 't_health_data_config'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.BigInteger, nullable=False)
    data_type = db.Column(db.String(50), nullable=False)
    frequency_interval = db.Column(db.Integer, nullable=True)
    is_realtime = db.Column(db.Boolean, default=True, nullable=True)
    is_enabled = db.Column(db.Boolean, default=True, nullable=True)
    is_default = db.Column(db.Boolean, default=False, nullable=True)
    warning_high = db.Column(db.Numeric(5, 1), nullable=True)
    warning_low = db.Column(db.Numeric(5, 1), nullable=True)
    warning_cnt = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Numeric(5, 4), nullable=True)

class DeviceInfoHistory(db.Model):
    __tablename__ = 't_device_info_history'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    serial_number = db.Column(db.String(255), nullable=False, comment='设备唯一编号')
    timestamp = db.Column(db.DateTime, nullable=False, comment='采集时间')
    
    # 可变字段
    system_software_version = db.Column(db.String(255), nullable=True, comment='系统版本')
    battery_level = db.Column(db.Integer, nullable=True, comment='电量')
    wearable_status = db.Column(db.Enum('WORN', 'NOT_WORN'), nullable=True, comment='佩戴状态')
    charging_status = db.Column(db.Enum('NOT_CHARGING', 'CHARGING'), nullable=True, comment='充电状态')
    voltage = db.Column(db.Integer, nullable=True, comment='电压')
    ip_address = db.Column(db.String(255), nullable=True, comment='IP地址')
    network_access_mode = db.Column(db.String(10), nullable=True, comment='网络访问模式')
    status = db.Column(db.Enum('INACTIVE', 'ACTIVE'), nullable=True, comment='状态')
    
    # 数据管理字段
    is_deleted = db.Column(db.Boolean, default=False, nullable=True, comment='是否删除(0:否,1:是)')
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP'), nullable=True)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.DateTime, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=True)
    
    __table_args__ = (
        db.Index('idx_sn_time', 'serial_number', 'timestamp'),
    )

class DeviceInfo(db.Model):
    __tablename__ = 't_device_info'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    serial_number = db.Column(db.String(255), nullable=False, unique=True)
    system_software_version = db.Column(db.String(255), nullable=False)
    wifi_address = db.Column(db.String(255), nullable=True)
    bluetooth_address = db.Column(db.String(255), nullable=True)
    ip_address = db.Column(db.String(255), nullable=True)
    network_access_mode = db.Column(db.String(10), nullable=True)
    device_name = db.Column(db.String(255), nullable=True)
    imei = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    battery_level = db.Column(db.String(10), default='0', nullable=True)
    voltage = db.Column(db.String(10), default='0', nullable=True)
    model = db.Column(db.String(50), nullable=True)
    status = db.Column(db.Enum('INACTIVE', 'ACTIVE'), nullable=True)
    wearable_status = db.Column(db.Enum('WORN', 'NOT_WORN'), nullable=True)
    charging_status = db.Column(db.Enum('NOT_CHARGING', 'CHARGING'), nullable=True)
    user_id = db.Column(db.BigInteger, nullable=True, comment='绑定用户ID')
    org_id = db.Column(db.BigInteger, nullable=True, comment='绑定组织ID')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，继承自当前绑定用户，0表示全局设备')
    is_deleted = db.Column(db.Boolean, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.DateTime, nullable=True)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.DateTime, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        return {
            "id": self.id,
            "serial_number": self.serial_number,
            "system_software_version": self.system_software_version,
            "wifi_address": self.wifi_address,
            "bluetooth_address": self.bluetooth_address,
            "ip_address": self.ip_address,
            "network_access_mode": self.network_access_mode,
            "device_name": self.device_name,
            "imei": self.imei,
            "battery_level": self.battery_level,
            "voltage": self.voltage,
            "model": self.model,
            "status": self.status,
            "wearable_status": self.wearable_status,
            "charging_status": self.charging_status,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S") if self.create_time else None,
            "update_time": self.update_time.strftime("%Y-%m-%d %H:%M:%S") if self.update_time else None,
            "is_deleted": self.is_deleted
        }

class UserInfo(db.Model):
    __tablename__ = 'sys_user'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_card_number = db.Column(db.String(40), nullable=False, comment='用户卡号')
    working_years = db.Column(db.Integer, nullable=True, comment='工作年限')
    avatar = db.Column(db.String(200), nullable=True, comment='头像')
    user_name = db.Column(db.String(40), nullable=False, comment='用户名称')
    password = db.Column(db.String(100), nullable=False, comment='密码')
    nick_name = db.Column(db.String(20), nullable=True, comment='昵称')
    real_name = db.Column(db.String(20), nullable=False, comment='真实姓名')
    avatar = db.Column(db.String(200), nullable=True, comment='头像')
    email = db.Column(db.String(45), nullable=False, comment='邮箱')
    phone = db.Column(db.String(45), nullable=True, comment='手机')
    gender = db.Column(db.String(2), default='0', comment='性别 0保密 1男 2女')
    create_user = db.Column(db.String(40), nullable=False, comment='创建用户')
    create_user_id = db.Column(db.BigInteger, nullable=False, comment='创建用户ID')
    create_time = db.Column(db.DateTime, nullable=False, comment='创建时间')
    update_user = db.Column(db.String(40), nullable=True, comment='修改用户')
    update_user_id = db.Column(db.BigInteger, nullable=True, comment='修改用户ID')
    update_time = db.Column(db.DateTime, nullable=True, comment='修改时间')
    salt = db.Column(db.String(6), nullable=True, comment='MD5的盐值')
    last_login_time = db.Column(db.DateTime, nullable=True, comment='最后登录时间')
    update_password_time = db.Column(db.DateTime, nullable=True, comment='修改密码时间')
    status = db.Column(db.String(2), default='1', comment='是否启用(0:禁用,1:启用)')
    is_deleted = db.Column(db.Boolean, default=False, comment='是否删除(0:否,1:是)')
    device_sn = db.Column(db.String(50), nullable=True)
    customer_id = db.Column(db.BigInteger, nullable=True)
    

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': str(self.id),
            'user_card_number': self.user_card_number,
            'avatar': self.avatar,
            'working_years': self.working_years,
            'positions': [pos.name for pos in self.positions],
            'user_name': self.user_name,
            'phone': self.phone,
            'device_sn': self.device_sn,
            'status': self.status,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

    @staticmethod
    def generate_password():
        """生成随机密码和盐值 #密码生成 - 与ljwx-boot保持一致"""
        import random
        import string
        import hashlib
        
        # 生成12位字母密码（与ljwx-boot一致）
        random_pwd = ''.join(random.choices(string.ascii_letters, k=12))
        
        # 生成6位字母盐值（与ljwx-boot一致）
        salt = ''.join(random.choices(string.ascii_letters, k=6))
        
        # 使用SHA256双重加密（与ljwx-boot一致）
        sha256_hex_pwd = hashlib.sha256(random_pwd.encode()).hexdigest()
        password_hash = hashlib.sha256((sha256_hex_pwd + salt).encode()).hexdigest()
        
        return {
            'random_pwd': random_pwd,  # 明文密码，用于返回给用户
            'password': password_hash,  # 加密后的密码，存储到数据库
            'salt': salt  # 盐值，存储到数据库
        }

    def verify_password(self, password):
        """验证密码 #密码验证 - 与ljwx-boot保持一致"""
        import hashlib
        
        if not self.salt or not self.password:
            return False
        
        # 使用相同的双重SHA256加密方式验证密码
        sha256_hex_pwd = hashlib.sha256(password.encode()).hexdigest()
        password_hash = hashlib.sha256((sha256_hex_pwd + self.salt).encode()).hexdigest()
        return password_hash == self.password

class Position(db.Model):
    __tablename__ = 'sys_position'
    __table_args__ = {'comment': '岗位管理'}

    id = Column(BigInteger, primary_key=True, comment='主键')
    name = Column(String(200), nullable=False, comment='岗位名称')
    code = Column(String(100), comment='岗位编码')
    abbr = Column(String(50), comment='岗位名称简写')
    description = Column(String(500), comment='岗位描述')
    sort = Column(Integer, default=999, comment='排序值')
    status = Column(String(2), default='1', comment='是否启用(0:禁用,1:启用)')
    org_id = Column(BigInteger, comment='组织ID')
    risk_level = Column(String(20), default='normal', comment='岗位风险等级')
    weight = Column(db.Numeric(5, 2), default=0.15, comment='岗位健康权重')
    customer_id = Column(BigInteger, nullable=False, default=0, comment='租户ID')
    is_deleted = Column(SmallInteger, default=0, comment='是否删除(0:否,1:是)')
    create_user = Column(String(64), nullable=False, comment='创建用户')
    create_user_id = Column(BigInteger, nullable=False, comment='创建用户ID')
    create_time = Column(DateTime, nullable=False, comment='创建时间')
    update_user = Column(String(64), comment='修改用户')
    update_user_id = Column(BigInteger, comment='修改用户ID')
    update_time = Column(DateTime, comment='修改时间')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'abbr': self.abbr,
            'description': self.description,
            'sort': self.sort,
            'status': self.status,
            'org_id': self.org_id,
            'risk_level': self.risk_level,
            'weight': float(self.weight) if self.weight else 0.15,
            'customer_id': self.customer_id,
            'is_deleted': self.is_deleted,
            'create_user': self.create_user,
            'create_user_id': self.create_user_id,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_user': self.update_user,
            'update_user_id': self.update_user_id,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

class UserPosition(db.Model):
    __tablename__ = 'sys_user_position'
    __table_args__ = {'comment': '用户岗位管理'}

    id = Column(BigInteger, primary_key=True, comment='主键')
    user_id = Column(BigInteger, ForeignKey('sys_user.id'), comment='用户ID')
    position_id = Column(BigInteger, ForeignKey('sys_position.id'), comment='岗位ID')
    is_deleted = Column(SmallInteger, default=0, comment='是否删除(0:否,1:是)')
    create_user = Column(String(64), nullable=False, comment='创建用户')
    create_user_id = Column(BigInteger, nullable=False, comment='创建用户ID')
    create_time = Column(DateTime, nullable=False, comment='创建时间')
    update_user = Column(String(64), comment='修改用户')
    update_user_id = Column(BigInteger, comment='修改用户ID')
    update_time = Column(DateTime, comment='修改时间')


Base = declarative_base()

class UserHealthData(db.Model):
    __tablename__ = 't_user_health_data'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    upload_method = Column(String(20), nullable=True)
    heart_rate = Column(Integer, nullable=True)
    pressure_high = Column(Integer, nullable=True)
    pressure_low = Column(Integer, nullable=True)
    blood_oxygen = Column(Integer, nullable=True)
    temperature = Column(Numeric(5, 2), nullable=True)
    stress = Column(Integer, nullable=True)
    step = Column(Integer, nullable=True)
    timestamp = Column(DateTime, nullable=True)
    latitude = Column(Numeric(10, 6), nullable=True)
    longitude = Column(Numeric(10, 6), nullable=True)
    altitude = Column(Float, nullable=True)
    device_sn = Column(String(255), nullable=False)
    distance = Column(Float, nullable=True)
    calorie = Column(Float, nullable=True)
    sleep = Column(Float, nullable=True, comment='睡眠时长(小时)，由sleepData计算得出')
    user_id = Column(BigInteger, nullable=True)
    org_id = Column(BigInteger, nullable=True)
    customer_id = Column(BigInteger, nullable=False, default=0, comment='租户ID，0表示全局数据，其他值表示特定租户')
    is_deleted = Column(Boolean, default=False, nullable=False)
    create_user = Column(String(255), nullable=True)
    create_user_id = Column(BigInteger, nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_user = Column(String(255), nullable=True)
    update_user_id = Column(BigInteger, nullable=True)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    #添加唯一约束防止重复插入
    __table_args__ = (
        db.UniqueConstraint('device_sn', 'timestamp', name='uk_device_timestamp'),
        db.Index('idx_device_timestamp', 'device_sn', 'timestamp'),#性能优化索引
        db.Index('idx_timestamp', 'timestamp'),#时间查询索引
    )

class CustomerConfig(db.Model):
    __tablename__ = 't_customer_config'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    customer_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    upload_method = Column(Enum('wifi', 'bluetooth', 'common_event'), default='wifi', nullable=True)
    license_key = Column(Integer, nullable=False)
    is_support_license = Column(Boolean, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=True)
    create_user = Column(String(255), nullable=True)
    create_user_id = Column(BigInteger, nullable=True)
    create_time = Column(TIMESTAMP, default=func.current_timestamp(), nullable=True)
    update_user = Column(String(255), nullable=True)
    update_user_id = Column(BigInteger, nullable=True)
    update_time = Column(TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)
    os_version = Column(String(200), nullable=True)
    enable_resume = Column(Boolean, default=False, nullable=True)
    upload_retry_count = Column(Integer, default=3, nullable=True)
    cache_max_count = Column(Integer, default=100, nullable=True)
    upload_retry_interval = Column(Integer, default=5, nullable=True)
class AlertInfo(db.Model):
    __tablename__ = 't_alert_info'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    rule_id = db.Column(db.BigInteger, db.ForeignKey('t_alert_rules.id'), nullable=False)
    alert_type = db.Column(db.String(100), nullable=False)
    device_sn = db.Column(db.String(20), nullable=False)
    alert_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    responded_time = db.Column(db.DateTime, nullable=True)
    alert_desc = db.Column(db.String(2000), nullable=True)
    severity_level = db.Column(db.String(50), default='medium', nullable=False)
    alert_status = db.Column(db.String(50), default='pending', nullable=True)
    assigned_user = db.Column(db.String(255), nullable=True)
    assigned_user_id = db.Column(db.BigInteger, nullable=True)
    org_id = db.Column(db.BigInteger, nullable=True, comment='组织ID')
    user_id = db.Column(db.BigInteger, nullable=True, comment='用户ID')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，0表示全局告警，其他值表示特定租户告警')
    is_deleted = db.Column(db.Boolean, default=False, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    latitude = db.Column(db.Numeric(12, 8), default=114.01508952, nullable=True)
    longitude = db.Column(db.Numeric(12, 8), default=22.54036796, nullable=True)
    altitude = db.Column(db.Numeric(10, 2), default=0.00, nullable=True)
    health_id = db.Column(db.BigInteger, nullable=True)

class AlertLog(db.Model):
    __tablename__ = 't_alert_action_log'
    
    log_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    id = db.Column(db.Integer, nullable=True)
    alert_id = db.Column(db.BigInteger, db.ForeignKey('t_alert_info.id'), nullable=False)
    action = db.Column(db.String(255), nullable=False)
    action_timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    action_user = db.Column(db.String(255), nullable=True)
    action_user_id = db.Column(db.BigInteger, nullable=True)
    details = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    handled_via = db.Column(db.String(50), nullable=True, comment='处理途径（如微信、消息等）')
    result = db.Column(db.String(50), nullable=True, comment='处理结果（如成功、失败等）')

class HealthBaseline(db.Model):
    __tablename__ = 't_health_baseline'
    baseline_id = Column(BigInteger, primary_key=True, autoincrement=True, comment='基线记录主键')
    device_sn = Column(String(50), nullable=False, comment='设备序列号')
    user_id = Column(BigInteger, nullable=True, comment='用户ID')
    customer_id = Column(BigInteger, nullable=False, default=0, comment='租户ID，继承自用户所属租户')
    feature_name = Column(String(50), nullable=False, comment='体征名称，如 heart_rate/blood_oxygen')
    baseline_date = Column(db.Date, nullable=False, comment='基线日期')
    mean_value = Column(Float, comment='该期平均值')
    std_value = Column(Float, comment='该期标准差')
    min_value = Column(Float, comment='该期最小值')
    max_value = Column(Float, comment='该期最大值')
    sample_count = Column(Integer, default=0, comment='样本数量')
    is_current = Column(Boolean, nullable=False, comment='是否当前有效基线(1=是,0=否)')
    
    # 扩展字段 - 支持多层次基线
    baseline_type = Column(String(20), default='personal', comment='基线类型：personal|population|position')
    age_group = Column(String(20), comment='年龄组')
    gender = Column(String(10), comment='性别')
    position_risk_level = Column(String(20), comment='职位风险等级')
    seasonal_factor = Column(db.Numeric(5, 4), default=1.0000, comment='季节调整因子')
    confidence_level = Column(db.Numeric(5, 4), default=0.9500, comment='置信水平')
    
    create_user = Column(String(255), comment='创建人')
    create_user_id = Column(BigInteger, comment='创建人ID')
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment='记录创建时间')
    update_user = Column(String(255), comment='最后修改人')
    update_user_id = Column(BigInteger, comment='最后修改人ID')
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment='记录更新时间')
    baseline_time = Column(DateTime, nullable=False, comment='基线生成时戳')
    
    __table_args__ = (
        db.Index('idx_baseline_device_date', 'device_sn', 'baseline_date'),
        db.Index('idx_baseline_user_date', 'user_id', 'baseline_date'),
        db.Index('idx_baseline_type_date', 'baseline_type', 'baseline_date', 'is_current'),
        db.Index('idx_baseline_user_feature', 'user_id', 'feature_name', 'baseline_date'),
    )

    
    def to_dict(self):
        return {
            'baseline_id': self.baseline_id,
            'device_sn': self.device_sn,
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'feature_name': self.feature_name,
            'baseline_date': self.baseline_date.strftime('%Y-%m-%d') if self.baseline_date else None,
            'mean_value': float(self.mean_value) if self.mean_value is not None else None,
            'std_value': float(self.std_value) if self.std_value is not None else None,
            'min_value': float(self.min_value) if self.min_value is not None else None,
            'max_value': float(self.max_value) if self.max_value is not None else None,
            'sample_count': self.sample_count,
            'is_current': bool(self.is_current),
            'baseline_type': self.baseline_type,
            'age_group': self.age_group,
            'gender': self.gender,
            'position_risk_level': self.position_risk_level,
            'seasonal_factor': float(self.seasonal_factor) if self.seasonal_factor else 1.0,
            'confidence_level': float(self.confidence_level) if self.confidence_level else 0.95,
            'create_user': self.create_user,
            'create_user_id': self.create_user_id,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_user': self.update_user,
            'update_user_id': self.update_user_id,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'baseline_time': self.baseline_time.strftime('%Y-%m-%d %H:%M:%S') if self.baseline_time else None
        }

class OrgHealthBaseline(db.Model):
    """组织级健康基线模型"""
    __tablename__ = 't_org_health_baseline'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键')
    org_id = Column(BigInteger, nullable=False, comment='组织ID')
    feature_name = Column(String(50), nullable=False, comment='体征名称')
    baseline_date = Column(db.Date, nullable=False, comment='基线日期')
    mean_value = Column(Float, comment='组织平均值')
    std_value = Column(Float, comment='组织标准差')
    min_value = Column(Float, comment='组织最小值')
    max_value = Column(Float, comment='组织最大值')
    user_count = Column(Integer, default=0, comment='参与用户数')
    sample_count = Column(Integer, default=0, comment='总样本数')
    create_time = Column(DateTime, nullable=False, server_default=func.now())
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        db.Index('idx_org_baseline_date', 'org_id', 'baseline_date'),
        db.Index('idx_org_baseline_feature', 'org_id', 'feature_name', 'baseline_date'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'org_id': self.org_id,
            'feature_name': self.feature_name,
            'baseline_date': self.baseline_date.strftime('%Y-%m-%d') if self.baseline_date else None,
            'mean_value': float(self.mean_value) if self.mean_value else None,
            'std_value': float(self.std_value) if self.std_value else None,
            'min_value': float(self.min_value) if self.min_value else None,
            'max_value': float(self.max_value) if self.max_value else None,
            'user_count': self.user_count,
            'sample_count': self.sample_count,
            'create_time': datetime_to_str(self.create_time),
            'update_time': datetime_to_str(self.update_time)
        }

class HealthAnomaly(db.Model):
    __tablename__ = 't_health_anomaly'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_sn = db.Column(db.String(50), nullable=False)  # 工人编号
    timestamp = db.Column(db.DateTime, nullable=False)  # 数据上传时间
    feature_name = db.Column(db.String(50), nullable=False)  # 异常特征
    value = db.Column(db.Numeric(10, 2), nullable=True)  # 异常值
    anomaly_type = db.Column(db.String(50), nullable=True)  # 异常类型 (高于范围/低于范围/其他)
    created_at = db.Column(db.TIMESTAMP, default=func.current_timestamp(), nullable=False)
    
class AlertRules(db.Model):
    __tablename__ = 't_alert_rules'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    rule_type = db.Column(db.String(50), nullable=False)
    physical_sign = db.Column(db.String(50), nullable=True)
    threshold_min = db.Column(db.Numeric(10, 2), nullable=True)
    threshold_max = db.Column(db.Numeric(10, 2), nullable=True)
    deviation_percentage = db.Column(db.Numeric(5, 2), nullable=True)
    trend_duration = db.Column(db.Integer, nullable=True)
    parameters = db.Column(db.JSON, nullable=True)
    trigger_condition = db.Column(db.Text, nullable=True)
    alert_message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='message', nullable=True)
    severity_level = db.Column(db.String(50), default='medium', nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=True)
    create_user = db.Column(db.String(255), nullable=True)
    create_user_id = db.Column(db.BigInteger, nullable=True)
    create_time = db.Column(db.TIMESTAMP, default=func.current_timestamp(), nullable=True)
    update_user = db.Column(db.String(255), nullable=True)
    update_user_id = db.Column(db.BigInteger, nullable=True)
    update_time = db.Column(db.TIMESTAMP, default=func.current_timestamp(), onupdate=func.current_timestamp(), nullable=True)
    
    __table_args__ = (
        db.UniqueConstraint('rule_type', 'physical_sign', name='uk_rule_type_physical_sign'),
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "rule_type": self.rule_type,
            "physical_sign": self.physical_sign,
            "threshold_min": self.threshold_min,
            "threshold_max": self.threshold_max,
            "deviation_percentage": self.deviation_percentage,
            "trend_duration": self.trend_duration,
            "alert_message": self.alert_message,
            "notification_type": self.notification_type,
            "severity_level": self.severity_level
        }

class UserOrg(db.Model):
    __tablename__ = 'sys_user_org'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键')
    user_id = db.Column(db.BigInteger, nullable=True, comment='用户ID')
    org_id = db.Column(db.BigInteger, nullable=True, comment='组织/部门/子部门ID')
    principal = db.Column(db.String(2), default='0', nullable=True, comment='组织/部门/子部门负责人(0:否,1:是)')
    create_user = db.Column(db.String(64), nullable=False, comment='创建用户')
    create_user_id = Column(BigInteger, nullable=False, comment='创建用户ID')
    create_time = Column(DateTime, nullable=False, comment='创建时间')
    update_user = Column(db.String(64), nullable=True, comment='修改用户')
    update_user_id = Column(db.BigInteger, nullable=True, comment='修改用户ID')
    update_time = Column(db.DateTime, nullable=True, comment='修改时间')
    is_deleted = Column(db.Boolean, default=False, nullable=True, comment='是否删除(0:否,1:是)')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，继承自组织或用户')

    __table_args__ = {'comment': '用户组织/部门/子部门管理'}

class OrgInfo(db.Model):
    __tablename__ = 'sys_org_units'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键')
    parent_id = db.Column(db.BigInteger, nullable=True, comment='父组织/部门/子部门ID')
    name = db.Column(db.String(200), nullable=False, comment='组织/部门/子部门名称')
    code = db.Column(db.String(100), nullable=True, comment='组织/部门/子部门编码')
    abbr = db.Column(db.String(50), nullable=True, comment='组织/部门/子部门名称简写')
    level = db.Column(db.Integer, default=0, nullable=False, comment='组织/部门/子部门层级')
    ancestors = db.Column(db.String(500), nullable=False, comment='祖先节点 - 已废弃，请使用闭包表查询')
    description = db.Column(db.String(500), nullable=True, comment='组织/部门/子部门描述')
    sort = db.Column(db.Integer, default=999, nullable=True, comment='排序值')
    create_user = db.Column(db.String(64), nullable=False, comment='创建用户')
    create_user_id = Column(BigInteger, nullable=False, comment='创建用户ID')
    create_time = Column(DateTime, nullable=False, comment='创建时间')
    update_user = Column(db.String(64), nullable=True, comment='修改用户')
    update_user_id = Column(db.BigInteger, nullable=True, comment='修改用户ID')
    update_time = Column(db.DateTime, nullable=True, comment='修改时间')
    status = Column(db.String(2), default='1', nullable=True, comment='是否启用(0:禁用,1:启用)')
    is_deleted = Column(db.Boolean, default=False, nullable=True, comment='是否删除(0:否,1:是)')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，0表示全局组织，顶级组织ID表示租户')

class OrgClosure(db.Model):
    """组织架构闭包表 - 用于高效层级查询"""
    __tablename__ = 'sys_org_closure'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键')
    ancestor_id = db.Column(db.BigInteger, nullable=False, comment='祖先组织ID')
    descendant_id = db.Column(db.BigInteger, nullable=False, comment='后代组织ID')
    depth = db.Column(db.Integer, default=0, nullable=False, comment='层级深度，0表示自己')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True, comment='更新时间')
    
    # 索引提示
    __table_args__ = (
        db.Index('uk_closure_ancestor_descendant', 'ancestor_id', 'descendant_id', 'customer_id', unique=True),
        db.Index('idx_closure_ancestor', 'ancestor_id', 'customer_id'),
        db.Index('idx_closure_descendant', 'descendant_id', 'customer_id'),
        db.Index('idx_closure_depth', 'depth'),
        db.Index('idx_closure_customer', 'customer_id'),
        {'comment': '组织架构闭包表 - 用于高效层级查询'}
    )

class OrgManagerCache(db.Model):
    """组织管理员缓存表 - 用于快速查找部门管理员"""
    __tablename__ = 'sys_org_manager_cache'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键')
    org_id = db.Column(db.BigInteger, nullable=False, comment='组织ID')
    user_id = db.Column(db.BigInteger, nullable=False, comment='用户ID')
    user_name = db.Column(db.String(50), nullable=False, comment='用户姓名')
    role_type = db.Column(db.String(20), nullable=False, comment='角色类型：manager-部门经理，director-部门主管，admin-管理员')
    org_level = db.Column(db.Integer, default=0, nullable=False, comment='组织层级')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID')
    is_active = db.Column(db.Boolean, default=True, nullable=True, comment='是否激活')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True, comment='更新时间')
    
    # 索引提示
    __table_args__ = (
        db.Index('uk_manager_org_user_role', 'org_id', 'user_id', 'role_type', 'customer_id', unique=True),
        db.Index('idx_manager_org', 'org_id', 'customer_id'),
        db.Index('idx_manager_user', 'user_id', 'customer_id'),
        db.Index('idx_manager_role', 'role_type', 'customer_id'),
        {'comment': '组织管理员缓存表 - 用于快速查找部门管理员'}
    )

    __table_args__ = {'comment': '组织/部门/子部门管理'}

class HealthSummaryDaily(db.Model):
    __tablename__ = 't_health_summary_daily'
    summary_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='汇总记录主键')
    device_sn = db.Column(db.String(50), nullable=False, comment='设备序列号')
    summary_date = db.Column(db.Date, nullable=False, comment='汇总日期')
    health_score = db.Column(db.DECIMAL(5,2), nullable=False, comment='综合健康得分（0–100）')
    create_time = db.Column(db.DateTime, nullable=False, default=func.now(), comment='创建时间')
    update_time = db.Column(db.DateTime, nullable=False, default=func.now(), onupdate=func.now(), comment='更新时间')
    heart_rate_score = db.Column(db.DECIMAL(5,2), comment='心率得分')
    blood_oxygen_score = db.Column(db.DECIMAL(5,2), comment='血氧得分')
    temperature_score = db.Column(db.DECIMAL(5,2), comment='体温得分')
    blood_pressure_score = db.Column(db.DECIMAL(5,2), comment='血压得分')
    stress_score = db.Column(db.DECIMAL(5,2), comment='压力得分')
    sleep_data_score = db.Column(db.DECIMAL(5,2), comment='睡眠得分')
    step_score = db.Column(db.DECIMAL(5,2), comment='步数得分')
    distance_score = db.Column(db.DECIMAL(5,2), comment='距离得分')
    calorie_score = db.Column(db.DECIMAL(5,2), comment='卡路里得分')
    __table_args__ = (
        db.UniqueConstraint('device_sn', 'summary_date', name='uk_device_date'),
        db.Index('idx_device_sn', 'device_sn'),
        db.Index('idx_summary_date', 'summary_date')
    )

    def to_dict(self):
        return {
            'summary_id': self.summary_id,
            'device_sn': self.device_sn,
            'summary_date': self.summary_date.strftime('%Y-%m-%d') if self.summary_date else None,
            'health_score': float(self.health_score) if self.health_score else None,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'heart_rate_score': float(self.heart_rate_score) if self.heart_rate_score else None,
            'blood_oxygen_score': float(self.blood_oxygen_score) if self.blood_oxygen_score else None,
            'temperature_score': float(self.temperature_score) if self.temperature_score else None,
            'blood_pressure_score': float(self.blood_pressure_score) if self.blood_pressure_score else None,
            'stress_score': float(self.stress_score) if self.stress_score else None,
            'sleep_data_score': float(self.sleep_data_score) if self.sleep_data_score else None,
            'step_score': float(self.step_score) if self.step_score else None,
            'distance_score': float(self.distance_score) if self.distance_score else None,
            'calorie_score': float(self.calorie_score) if self.calorie_score else None
        }

class UserHealthDataDaily(db.Model):#每日更新健康数据表
    __tablename__ = 't_user_health_data_daily'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_sn = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.BigInteger, nullable=True)
    org_id = db.Column(db.BigInteger, nullable=True)
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，继承自用户所属租户')
    date = db.Column(db.Date, nullable=False)
    sleep_data = db.Column(db.JSON, nullable=True, comment='睡眠数据(每日更新)')
    exercise_daily_data = db.Column(db.JSON, nullable=True, comment='每日运动数据')
    workout_data = db.Column(db.JSON, nullable=True, comment='锻炼数据')
    scientific_sleep_data = db.Column(db.JSON, nullable=True, comment='科学睡眠数据')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('device_sn', 'date', name='uk_device_date'),
        db.Index('idx_user_date', 'user_id', 'date'),
        db.Index('idx_org_date', 'org_id', 'date')
    )

class UserHealthDataWeekly(db.Model):#每周更新健康数据表
    __tablename__ = 't_user_health_data_weekly'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_sn = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.BigInteger, nullable=True)
    org_id = db.Column(db.BigInteger, nullable=True)
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，继承自用户所属租户')
    week_start = db.Column(db.Date, nullable=False, comment='周开始日期(周一)')
    exercise_week_data = db.Column(db.JSON, nullable=True, comment='每周运动数据')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('device_sn', 'week_start', name='uk_device_week'),
        db.Index('idx_user_week', 'user_id', 'week_start'),
        db.Index('idx_org_week', 'org_id', 'week_start')
    )

class WeChatAlarmConfig(db.Model):
    """微信告警配置表(租户维度)"""
    __tablename__ = 't_wechat_alarm_config'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    tenant_id = db.Column(db.BigInteger, nullable=False, comment='租户ID')
    type = db.Column(db.String(20), nullable=False, comment='微信类型: enterprise/official')
    corp_id = db.Column(db.String(100), nullable=True, comment='企业微信企业ID')
    agent_id = db.Column(db.String(50), nullable=True, comment='企业微信应用ID')
    secret = db.Column(db.String(100), nullable=True, comment='企业微信应用Secret')
    appid = db.Column(db.String(100), nullable=True, comment='微信公众号AppID')
    appsecret = db.Column(db.String(100), nullable=True, comment='微信公众号AppSecret')
    template_id = db.Column(db.String(100), nullable=True, comment='微信模板ID')
    enabled = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.Index('idx_tenant_type', 'tenant_id', 'type'),
    )

class SystemEventRule(db.Model):
    """系统事件规则表"""
    __tablename__ = 't_system_event_rule'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(100), nullable=False, comment='事件类型(完整)')
    rule_type = db.Column(db.String(50), nullable=False, comment='规则类型(简化)')
    severity_level = db.Column(db.String(20), default='medium', nullable=False, comment='告警级别:critical/high/medium/low')
    alert_message = db.Column(db.String(500), nullable=False, comment='告警消息模板')
    is_emergency = db.Column(db.Boolean, default=False, nullable=False, comment='是否紧急事件(微信推送)')
    notification_type = db.Column(db.String(20), default='message', nullable=False, comment='通知类型:wechat/message/both')
    retry_count = db.Column(db.Integer, default=3, nullable=False, comment='重试次数')
    is_active = db.Column(db.Boolean, default=True, nullable=False, comment='是否启用')
    tenant_id = db.Column(db.BigInteger, default=1, nullable=False, comment='租户ID')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('rule_type', 'tenant_id', name='uk_rule_tenant'),
        db.Index('idx_event_type', 'event_type'),
        db.Index('idx_is_emergency', 'is_emergency'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_type': self.event_type,
            'rule_type': self.rule_type,
            'severity_level': self.severity_level,
            'alert_message': self.alert_message,
            'is_emergency': self.is_emergency,
            'notification_type': self.notification_type,
            'retry_count': self.retry_count,
            'is_active': self.is_active,
            'tenant_id': self.tenant_id,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

class EventAlarmQueue(db.Model):
    """事件告警队列表"""
    __tablename__ = 't_event_alarm_queue'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    event_type = db.Column(db.String(100), nullable=False, comment='事件类型')
    device_sn = db.Column(db.String(50), nullable=False, comment='设备序列号')
    event_value = db.Column(db.String(500), nullable=True, comment='事件值')
    event_data = db.Column(db.JSON, nullable=True, comment='完整事件数据')
    processing_status = db.Column(db.String(20), default='pending', nullable=False, comment='处理状态:pending/processing/completed/failed')
    retry_count = db.Column(db.Integer, default=0, nullable=False, comment='重试次数')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    process_time = db.Column(db.DateTime, nullable=True, comment='处理时间')
    complete_time = db.Column(db.DateTime, nullable=True, comment='完成时间')
    
    __table_args__ = (
        db.Index('idx_status_time', 'processing_status', 'create_time'),
        db.Index('idx_device_time', 'device_sn', 'create_time'),
    )

class DeviceBindRequest(db.Model):
    """设备绑定申请表"""
    __tablename__ = 't_device_bind_request'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    device_sn = db.Column(db.String(100), nullable=False, comment='设备序列号')
    user_id = db.Column(db.BigInteger, nullable=False, comment='申请用户ID')
    org_id = db.Column(db.BigInteger, nullable=False, comment='申请组织ID')
    status = db.Column(db.Enum('PENDING', 'APPROVED', 'REJECTED'), default='PENDING', nullable=False, comment='申请状态')
    apply_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='申请时间')
    approve_time = db.Column(db.DateTime, nullable=True, comment='审批时间')
    approver_id = db.Column(db.BigInteger, nullable=True, comment='审批人ID')
    comment = db.Column(db.String(255), nullable=True, comment='审批备注')
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, comment='是否删除')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False, comment='更新时间')
    
    __table_args__ = (
        db.Index('idx_device_sn', 'device_sn'),
        db.Index('idx_user_status', 'user_id', 'status'),
        {'comment': '设备绑定申请表'}
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_sn': self.device_sn,
            'user_id': self.user_id,
            'org_id': self.org_id,
            'status': self.status,
            'apply_time': self.apply_time.strftime('%Y-%m-%d %H:%M:%S') if self.apply_time else None,
            'approve_time': self.approve_time.strftime('%Y-%m-%d %H:%M:%S') if self.approve_time else None,
            'approver_id': self.approver_id,
            'comment': self.comment
        }

class DeviceUser(db.Model):
    """设备用户关联表"""
    __tablename__ = 't_device_user'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True, comment='主键ID')
    device_sn = db.Column(db.String(200), nullable=False, comment='设备ID')
    user_id = db.Column(db.BigInteger, nullable=False, comment='用户ID')
    customer_id = db.Column(db.BigInteger, nullable=False, default=0, comment='租户ID，继承自用户的租户信息')
    user_name = db.Column(db.String(50), nullable=True)
    operate_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True, comment='绑定时间')
    status = db.Column(db.Enum('BIND','UNBIND'), default='BIND', nullable=True, comment='绑定状态')
    is_deleted = db.Column(db.Boolean, default=False, nullable=True, comment='是否删除')
    create_user = db.Column(db.String(255), nullable=True, comment='创建用户')
    create_user_id = db.Column(db.BigInteger, nullable=True, comment='创建用户ID')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True, comment='创建时间')
    update_user = db.Column(db.String(255), nullable=True, comment='最后修改用户')
    update_user_id = db.Column(db.BigInteger, nullable=True, comment='最后修改用户ID')
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True, comment='最后修改时间')
    
    __table_args__ = (
        db.Index('fk_user_id', 'user_id'),
        {'comment': '设备与用户关联表'}
    )
    
    def save(self):
        """保存设备用户关联记录"""
        try:
            db.session.add(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"保存设备用户关联记录失败: {e}")
            return False

class SystemEventProcessLog(db.Model):
    """系统事件告警处理日志表"""
    __tablename__ = 't_system_event_process_log'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    event_id = db.Column(db.BigInteger, nullable=True, comment='事件队列ID')
    alert_id = db.Column(db.BigInteger, nullable=True, comment='告警ID')
    device_sn = db.Column(db.String(50), nullable=False, comment='设备序列号')
    event_type = db.Column(db.String(100), nullable=False, comment='事件类型')
    rule_id = db.Column(db.BigInteger, nullable=True, comment='规则ID')
    process_status = db.Column(db.String(20), nullable=False, comment='处理状态:processing/completed/failed')
    notification_type = db.Column(db.String(20), nullable=True, comment='通知类型:wechat/message/both')
    message_count = db.Column(db.Integer, default=0, comment='消息推送数量')
    wechat_status = db.Column(db.String(20), nullable=True, comment='微信推送状态:success/failed/skipped')
    process_duration = db.Column(db.Integer, nullable=True, comment='处理耗时(毫秒)')
    error_message = db.Column(db.Text, nullable=True, comment='错误信息')
    process_details = db.Column(db.JSON, nullable=True, comment='处理详情')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    complete_time = db.Column(db.DateTime, nullable=True, comment='完成时间')
    
    __table_args__ = (
        db.Index('idx_device_event_time', 'device_sn', 'event_type', 'create_time'),
        db.Index('idx_process_status_time', 'process_status', 'create_time'),
        {'comment': '系统事件告警处理日志表'}
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'event_id': self.event_id,
            'alert_id': self.alert_id,
            'device_sn': self.device_sn,
            'event_type': self.event_type,
            'rule_id': self.rule_id,
            'process_status': self.process_status,
            'notification_type': self.notification_type,
            'message_count': self.message_count,
            'wechat_status': self.wechat_status,
            'process_duration': self.process_duration,
            'error_message': self.error_message,
            'process_details': self.process_details,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'complete_time': self.complete_time.strftime('%Y-%m-%d %H:%M:%S') if self.complete_time else None
        }

class HealthScore(db.Model):
    """健康评分表"""
    __tablename__ = 't_health_score'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    device_sn = db.Column(db.String(50), nullable=False, comment='设备序列号')
    user_id = db.Column(db.BigInteger, nullable=True, default=0, comment='用户ID')
    org_id = db.Column(db.String(20), nullable=True, default='1', comment='组织ID')
    feature_name = db.Column(db.String(20), nullable=False, comment='体征名称')
    avg_value = db.Column(db.Numeric(10, 2), nullable=True, default=0.00, comment='平均值')
    z_score = db.Column(db.Numeric(10, 4), nullable=True, default=0.0000, comment='Z-score')
    score_value = db.Column(db.Numeric(5, 2), nullable=True, default=0.00, comment='评分值')
    penalty_value = db.Column(db.Numeric(5, 2), nullable=True, default=0.00, comment='惩罚值')
    baseline_time = db.Column(db.Date, nullable=True, comment='基线时间')
    score_date = db.Column(db.Date, nullable=False, comment='评分日期')
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    
    __table_args__ = (
        db.Index('idx_device_sn_score_date', 'device_sn', 'score_date'),
        db.Index('idx_user_id_score_date', 'user_id', 'score_date'),
        {'comment': '健康评分表'}
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_sn': self.device_sn,
            'user_id': self.user_id,
            'org_id': self.org_id,
            'feature_name': self.feature_name,
            'avg_value': float(self.avg_value) if self.avg_value else 0.0,
            'z_score': float(self.z_score) if self.z_score else 0.0,
            'score_value': float(self.score_value) if self.score_value else 0.0,
            'penalty_value': float(self.penalty_value) if self.penalty_value else 0.0,
            'baseline_time': self.baseline_time.isoformat() if self.baseline_time else None,
            'score_date': self.score_date.isoformat() if self.score_date else None,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }

class UserHealthProfile(db.Model):
    """用户健康画像主表"""
    __tablename__ = 't_user_health_profile'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, nullable=False, comment='用户ID')
    customer_id = db.Column(db.BigInteger, nullable=False, comment='租户ID')
    profile_date = db.Column(db.Date, nullable=False, comment='画像日期')
    
    # 综合评分
    overall_health_score = db.Column(db.Numeric(5, 2), default=0.00, comment='综合健康评分')
    health_level = db.Column(db.String(20), default='fair', comment='健康等级')
    
    # 各维度评分
    physiological_score = db.Column(db.Numeric(5, 2), default=0.00, comment='生理指标评分')
    behavioral_score = db.Column(db.Numeric(5, 2), default=0.00, comment='行为指标评分')
    risk_factor_score = db.Column(db.Numeric(5, 2), default=0.00, comment='风险因子评分')
    
    # 健康指标分析
    cardiovascular_score = db.Column(db.Numeric(5, 2), default=0.00, comment='心血管健康评分')
    respiratory_score = db.Column(db.Numeric(5, 2), default=0.00, comment='呼吸系统评分')
    metabolic_score = db.Column(db.Numeric(5, 2), default=0.00, comment='代谢功能评分')
    psychological_score = db.Column(db.Numeric(5, 2), default=0.00, comment='心理健康评分')
    
    # 行为模式分析
    activity_consistency_score = db.Column(db.Numeric(5, 2), default=0.00, comment='活动一致性评分')
    sleep_quality_score = db.Column(db.Numeric(5, 2), default=0.00, comment='睡眠质量评分')
    health_engagement_score = db.Column(db.Numeric(5, 2), default=0.00, comment='健康参与度评分')
    
    # 风险评估
    current_risk_level = db.Column(db.String(20), default='medium', comment='当前风险等级')
    predicted_risk_score = db.Column(db.Numeric(5, 2), default=0.00, comment='预测风险评分')
    
    # JSON扩展字段
    detailed_analysis = db.Column(db.JSON, comment='详细分析数据')
    trend_analysis = db.Column(db.JSON, comment='趋势分析数据')
    recommendations = db.Column(db.JSON, comment='个性化建议')
    
    # 审计字段
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    version = db.Column(db.Integer, default=1)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'profile_date', 'is_deleted', name='idx_user_profile_date'),
        db.Index('idx_customer_date', 'customer_id', 'profile_date'),
        db.Index('idx_health_level', 'health_level', 'profile_date'),
        db.Index('idx_risk_level', 'current_risk_level', 'profile_date'),
        {'comment': '用户健康画像主表'}
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'profile_date': self.profile_date.strftime('%Y-%m-%d') if self.profile_date else None,
            'overall_health_score': float(self.overall_health_score) if self.overall_health_score else 0.0,
            'health_level': self.health_level,
            'physiological_score': float(self.physiological_score) if self.physiological_score else 0.0,
            'behavioral_score': float(self.behavioral_score) if self.behavioral_score else 0.0,
            'risk_factor_score': float(self.risk_factor_score) if self.risk_factor_score else 0.0,
            'cardiovascular_score': float(self.cardiovascular_score) if self.cardiovascular_score else 0.0,
            'respiratory_score': float(self.respiratory_score) if self.respiratory_score else 0.0,
            'metabolic_score': float(self.metabolic_score) if self.metabolic_score else 0.0,
            'psychological_score': float(self.psychological_score) if self.psychological_score else 0.0,
            'activity_consistency_score': float(self.activity_consistency_score) if self.activity_consistency_score else 0.0,
            'sleep_quality_score': float(self.sleep_quality_score) if self.sleep_quality_score else 0.0,
            'health_engagement_score': float(self.health_engagement_score) if self.health_engagement_score else 0.0,
            'current_risk_level': self.current_risk_level,
            'predicted_risk_score': float(self.predicted_risk_score) if self.predicted_risk_score else 0.0,
            'detailed_analysis': self.detailed_analysis,
            'trend_analysis': self.trend_analysis,
            'recommendations': self.recommendations,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'is_deleted': self.is_deleted,
            'version': self.version
        }

class HealthRecommendationTrack(db.Model):
    """健康建议执行跟踪表"""
    __tablename__ = 't_health_recommendation_track'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, nullable=False, comment='用户ID')
    customer_id = db.Column(db.BigInteger, nullable=False, comment='租户ID')
    recommendation_id = db.Column(db.String(64), nullable=False, comment='建议ID')
    recommendation_type = db.Column(db.String(50), nullable=False, comment='建议类型')
    
    # 建议内容
    title = db.Column(db.String(200), nullable=False, comment='建议标题')
    description = db.Column(db.Text, comment='建议描述')
    recommended_actions = db.Column(db.JSON, comment='推荐行动')
    
    # 执行状态
    status = db.Column(db.String(20), default='pending', comment='执行状态')
    start_date = db.Column(db.Date, comment='开始日期')
    target_completion_date = db.Column(db.Date, comment='目标完成日期')
    actual_completion_date = db.Column(db.Date, comment='实际完成日期')
    
    # 效果评估
    effectiveness_score = db.Column(db.Numeric(5, 2), comment='效果评分')
    user_feedback = db.Column(db.Text, comment='用户反馈')
    health_improvement_metrics = db.Column(db.JSON, comment='健康改善指标')
    
    # 审计字段
    create_time = db.Column(db.DateTime, default=datetime.utcnow)
    update_time = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    
    __table_args__ = (
        db.Index('idx_user_status', 'user_id', 'status', 'is_deleted'),
        db.Index('idx_customer_type', 'customer_id', 'recommendation_type'),
        db.Index('idx_completion_date', 'target_completion_date', 'status'),
        {'comment': '健康建议执行跟踪表'}
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'customer_id': self.customer_id,
            'recommendation_id': self.recommendation_id,
            'recommendation_type': self.recommendation_type,
            'title': self.title,
            'description': self.description,
            'recommended_actions': self.recommended_actions,
            'status': self.status,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'target_completion_date': self.target_completion_date.strftime('%Y-%m-%d') if self.target_completion_date else None,
            'actual_completion_date': self.actual_completion_date.strftime('%Y-%m-%d') if self.actual_completion_date else None,
            'effectiveness_score': float(self.effectiveness_score) if self.effectiveness_score else None,
            'user_feedback': self.user_feedback,
            'health_improvement_metrics': self.health_improvement_metrics,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'is_deleted': self.is_deleted
        }

