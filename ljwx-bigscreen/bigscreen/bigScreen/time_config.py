from datetime import datetime
import pytz

class TimeConfig: #时间配置统一管理
    def __init__(self,tz='Asia/Shanghai'):self.tz=pytz.timezone(tz) #设置时区
    def now(self):return datetime.now(self.tz).replace(tzinfo=None) #获取当前时间
    def utc_now(self):return datetime.utcnow() #获取UTC时间

time_config=TimeConfig() #全局时间配置实例
get_now=lambda:time_config.now() #当前时间快捷方法 