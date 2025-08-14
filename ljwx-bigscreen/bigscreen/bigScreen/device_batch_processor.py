import threading
import queue
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any
from .redis_helper import RedisHelper
from .time_config import get_now #统一时间配置
import logging
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
import pymysql

# 高并发设备信息批量处理器 v2.0 - 参考optimized_health_data.py
class DeviceBatchProcessor:
    def __init__(self, batch_size=50, max_wait_time=2.0, max_workers=4, app=None):
        self.batch_size = batch_size  # 批量大小
        self.max_wait_time = max_wait_time  # 最大等待时间(秒)
        self.max_workers = max_workers  # 最大工作线程数
        self.device_queue = queue.Queue(maxsize=10000)  # 设备数据队列
        self.redis = RedisHelper()
        self.running = False
        self.workers = []
        self.stats = {'processed': 0, 'failed': 0, 'queued': 0}
        self.logger = logging.getLogger(__name__)
        self.app = app  # Flask应用实例
        self.processed_keys = set()  # 已处理记录键值集合
        
    def start(self):
        """启动批量处理器"""
        self.running = True
        self.start_time = time.time()  # 记录启动时间
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f'DeviceWorker-{i}')
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        self.logger.info(f"🚀 设备批量处理器启动，工作线程数: {self.max_workers}")
        
    def stop(self):
        """停止批量处理器"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)
        self.logger.info("⛔ 设备批量处理器已停止")
        
    def submit(self, device_data) -> bool:
        """提交设备数据到处理队列 - 支持单个设备或设备列表"""
        
        def submit_single_device(single_device_data: Dict[str, Any]) -> bool:
            """提交单个设备数据"""
            try:
                # 添加提交时间戳和请求ID
                single_device_data['_submit_time'] = time.time()
                device_sn = single_device_data.get('SerialNumber') or single_device_data.get('serial_number', 'unknown')
                single_device_data['_request_id'] = f"{device_sn}_{int(time.time()*1000)}"
                
                # 重复数据检测
                timestamp = single_device_data.get('timestamp', get_now().strftime('%Y-%m-%d %H:%M:%S')) #使用统一时间配置
                key = f"{device_sn}:{timestamp}"
                
                if key in self.processed_keys:
                    self.logger.info(f"跳过重复设备数据: {key}")
                    return True
                
                # 非阻塞提交，如果队列满则拒绝
                self.device_queue.put_nowait(single_device_data)
                self.processed_keys.add(key)
                self.stats['queued'] += 1
                
                self.logger.info(f"📥 设备数据已提交: {device_sn}, 队列大小: {self.device_queue.qsize()}")
                return True
            except queue.Full:
                self.logger.warning(f"⚠️ 设备数据队列已满, 拒绝新请求: {single_device_data.get('SerialNumber', 'unknown')}")
                return False
            except Exception as e:
                self.logger.error(f"❌ 提交单个设备数据失败: {e}, 设备: {single_device_data.get('SerialNumber', 'unknown')}")
                return False
        
        # 处理列表或单个设备
        if isinstance(device_data, list):
            self.logger.info(f"📥 批量提交设备数据，设备数量: {len(device_data)}")
            success_count = 0
            for single_device in device_data:
                if submit_single_device(single_device):
                    success_count += 1
            
            # 如果所有设备都成功提交，返回True
            result = success_count == len(device_data)
            self.logger.info(f"📊 批量提交完成: 成功 {success_count}/{len(device_data)}")
            return result
        else:
            # 处理单个设备
            return submit_single_device(device_data)
            
    def _worker(self):
        """工作线程主循环"""
        batch = []
        last_process_time = time.time()
        
        while self.running:
            try:
                # 尝试获取数据，超时后检查批量处理条件
                try:
                    item = self.device_queue.get(timeout=0.5)
                    batch.append(item)
                    self.device_queue.task_done()
                except queue.Empty:
                    pass
                
                current_time = time.time()
                # 批量处理条件：达到批量大小或超过最大等待时间
                if (len(batch) >= self.batch_size or 
                    (batch and current_time - last_process_time >= self.max_wait_time)):
                    
                    if batch:
                        self._process_batch(batch)
                        batch = []
                        last_process_time = current_time
                        
            except Exception as e:
                self.logger.error(f"💥 工作线程异常: {e}")
                time.sleep(1)
                
    def _process_batch(self, batch: List[Dict[str, Any]]):
        """批量处理设备数据"""
        if not batch:
            return
            
        start_time = time.time()
        self.logger.info(f"🔄 开始批量处理设备数据: 数量={len(batch)}, 工作线程={threading.current_thread().name}")
        
        # 使用pymysql直接连接数据库，避免SQLAlchemy问题
        conn = None
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE,
                autocommit=False
            )
            
            success_count = 0
            failed_count = 0
            
            for item in batch:
                try:
                    if self._process_single_device(conn, item):
                        success_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    self.logger.error(f"❌ 处理单个设备失败: {e}, 设备: {item.get('SerialNumber', 'unknown')}")
                    failed_count += 1
            
            # 提交事务
            conn.commit()
            
            # 更新统计信息
            self.stats['processed'] += success_count
            self.stats['failed'] += failed_count
            self.stats['queued'] -= len(batch)
            
            process_time = time.time() - start_time
            self.logger.info(f"📊 批量处理完成: 成功{success_count}, 失败{failed_count}, 耗时{process_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"💥 批量处理异常: {e}")
            if conn:
                conn.rollback()
            self.stats['failed'] += len(batch)
        finally:
            if conn:
                conn.close()
                
    def _process_single_device(self, conn, raw_data: Dict[str, Any]) -> bool:
        """处理单个设备数据"""
        try:
            # 标准化设备数据
            normalized_data = self._normalize_device_data(raw_data)
            if not normalized_data:
                return False
                
            with conn.cursor() as cursor:
                # 1. 更新或插入设备信息表 (不更新org_id和user_id)
                upsert_sql = """
                    INSERT INTO t_device_info 
                    (serial_number, system_software_version, wifi_address, bluetooth_address, 
                     ip_address, network_access_mode, device_name, imei, battery_level, 
                     charging_status, wearable_status, status, voltage, timestamp, 
                     update_time, is_deleted, create_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                        system_software_version = VALUES(system_software_version),
                        wifi_address = VALUES(wifi_address),
                        bluetooth_address = VALUES(bluetooth_address),
                        ip_address = VALUES(ip_address),
                        network_access_mode = VALUES(network_access_mode),
                        device_name = VALUES(device_name),
                        imei = VALUES(imei),
                        battery_level = VALUES(battery_level),
                        charging_status = VALUES(charging_status),
                        wearable_status = VALUES(wearable_status),
                        status = VALUES(status),
                        voltage = VALUES(voltage),
                        timestamp = VALUES(timestamp),
                        update_time = VALUES(update_time)
                """
                
                cursor.execute(upsert_sql, (
                    normalized_data['serial_number'],
                    normalized_data['system_software_version'],
                    normalized_data['wifi_address'],
                    normalized_data['bluetooth_address'],
                    normalized_data['ip_address'],
                    normalized_data['network_access_mode'],
                    normalized_data['device_name'],
                    normalized_data['imei'],
                    normalized_data['battery_level'],
                    normalized_data['charging_status'],
                    normalized_data['wearable_status'],
                    normalized_data['status'],
                    normalized_data['voltage'],
                    normalized_data['timestamp'],
                    normalized_data['update_time'],
                    normalized_data['is_deleted']
                ))
                
                # 2. 插入历史记录表 (不包含org_id和user_id)
                history_sql = """
                    INSERT INTO t_device_info_history 
                    (serial_number, system_software_version, ip_address, network_access_mode, 
                     battery_level, charging_status, wearable_status, status, voltage, 
                     timestamp, update_time, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(history_sql, (
                    normalized_data['serial_number'],
                    normalized_data['system_software_version'],
                    normalized_data['ip_address'],
                    normalized_data['network_access_mode'],
                    normalized_data['battery_level'],
                    normalized_data['charging_status'],
                    normalized_data['wearable_status'],
                    normalized_data['status'],
                    normalized_data['voltage'],
                    normalized_data['timestamp'],
                    normalized_data['update_time'],
                    normalized_data['is_deleted']
                ))
                
                self.logger.info(f"✅ 设备历史记录插入成功: {normalized_data['serial_number']}")
                
                # 3. 更新Redis缓存
                self._update_redis_cache(normalized_data)
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ 处理单个设备数据失败: {e}, 设备: {raw_data.get('SerialNumber', 'unknown')}")
            return False
    
    def _get_device_org_user(self, cursor, device_sn): #根据设备序列号查询org_id和user_id
        try:
            sql="SELECT u.id,o.org_id FROM t_user u JOIN t_user_org o ON u.id=o.user_id WHERE u.device_sn=%s AND u.is_deleted=0 AND o.is_deleted=0 LIMIT 1" #查询用户和组织关联
            cursor.execute(sql,(device_sn,))
            result=cursor.fetchone()
            return (result[1],result[0]) if result else (None,None) #返回org_id,user_id
        except Exception as e:
            self.logger.error(f"❌ 查询设备组织用户失败: {e}, 设备: {device_sn}")
            return (None,None)
            
    def _normalize_device_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化设备数据"""
        try:
            data = raw_data.get("data", raw_data)
            
            # 提取关键字段
            serial_number = data.get("SerialNumber") or data.get("serial_number")
            if not serial_number:
                self.logger.warning(f"❌ 设备数据缺少序列号: {raw_data}")
                return None
                
            timestamp = data.get("timestamp") or get_now().strftime("%Y-%m-%d %H:%M:%S") #使用统一时间配置
            if str(timestamp).isdigit() and len(str(timestamp)) == 13:
                timestamp = datetime.fromtimestamp(int(timestamp)/1000).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                
            update_time = get_now().strftime("%Y-%m-%d %H:%M:%S") #使用统一时间配置
            
            # 标准化数据 - 只使用存在的字段
            normalized = {
                'serial_number': serial_number,
                'system_software_version': data.get("System Software Version") or data.get("system_version"),
                'wifi_address': data.get("Wifi Address") or data.get("wifi_address"),
                'bluetooth_address': data.get("Bluetooth Address") or data.get("bluetooth_address"),
                'ip_address': self._extract_ip(data.get("IP Address") or data.get("ip_address")),
                'network_access_mode': data.get("Network Access Mode") or data.get("network_mode"),
                'device_name': data.get("Device Name") or data.get("device_name"),
                'imei': data.get("IMEI") or data.get("imei"),
                'voltage': data.get("voltage") or 0,
                'battery_level': self._normalize_battery(data.get("batteryLevel") or data.get("battery_level")),
                'charging_status': self._normalize_charging_status(data.get("chargingStatus") or data.get("charging_status")),
                'wearable_status': self._normalize_wear_status(data.get("wearState") or data.get("wear_state")),
                'status': data.get("status"),
                'timestamp': timestamp,
                'update_time': update_time,
                'is_deleted': 0
            }
            
            return normalized
            
        except Exception as e:
            self.logger.error(f"❌ 设备数据标准化失败: {e}")
            return None
            
    def _extract_ip(self, ip_str):
        """提取有效的IPv4地址"""
        if not ip_str:
            return None
        ipv4_match = re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', str(ip_str))
        return ipv4_match.group(0) if ipv4_match else None
        
    def _normalize_battery(self, battery_level):
        """标准化电池电量"""
        if battery_level is None:
            return None
        try:
            value = str(battery_level).strip().replace('%', '')
            return int(value)
        except (ValueError, TypeError):
            return None
            
    def _normalize_charging_status(self, charging_status):
        """标准化充电状态"""
        if charging_status in ["CHARGING", "ENABLE", "1", 1, True]:
            return "CHARGING"
        elif charging_status in ["NOT_CHARGING", "NONE", "0", 0, False]:
            return "NOT_CHARGING"
        else:
            return "UNKNOWN"
            
    def _normalize_wear_status(self, wearable_status):
        """标准化佩戴状态"""
        return "WORN" if wearable_status and int(wearable_status) == 1 else "NOT_WORN"
        
    def _update_redis_cache(self, normalized_data):
        """更新Redis缓存"""
        try:
            serial_number = normalized_data['serial_number']
            
            # 过滤None值
            device_dict = {k: v for k, v in normalized_data.items() if v is not None}
            
            # 写入Redis
            self.redis.hset_data(f"device_info:{serial_number}", device_dict)
            self.redis.publish(f"device_info_channel:{serial_number}", serial_number)
            
            self.logger.debug(f"✅ Redis缓存更新成功: {serial_number}")
            
        except Exception as e:
            self.logger.error(f"❌ Redis缓存更新失败: {e}, 设备: {normalized_data.get('serial_number', 'unknown')}")
            
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        current_stats = self.stats.copy()
        current_stats['queue_size'] = self.device_queue.qsize()
        current_stats['workers'] = len(self.workers)
        current_stats['running'] = self.running
        current_stats['processed_keys_count'] = len(self.processed_keys)
        
        # 计算处理速率
        if hasattr(self, 'start_time') and self.running:
            uptime = time.time() - self.start_time
            current_stats['uptime_seconds'] = int(uptime)
            current_stats['processing_rate'] = round(self.stats['processed'] / max(uptime, 1), 2)
        
        return current_stats
        
    def clear_processed_keys(self):
        """智能清理过期的处理键值"""
        if len(self.processed_keys) > 10000:
            # 只保留最近1小时的记录
            current_time = time.time()
            new_keys = set()
            
            for key in self.processed_keys:
                try:
                    # 从键值中提取时间戳
                    parts = key.split(':')
                    if len(parts) >= 2:
                        timestamp_str = parts[1]
                        key_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').timestamp()
                        # 保留1小时内的记录
                        if current_time - key_timestamp < 3600:
                            new_keys.add(key)
                except:
                    continue
                    
            self.processed_keys = new_keys
            self.logger.info(f'智能清理processed_keys缓存，保留{len(new_keys)}条记录')

# 全局批处理器实例
_batch_processor = None
_processor_lock = threading.Lock()

def get_batch_processor(app=None) -> DeviceBatchProcessor:
    """获取批量处理器单例"""
    global _batch_processor
    
    with _processor_lock:
        if _batch_processor is None or not _batch_processor.running:
            if app:
                _batch_processor = DeviceBatchProcessor(app=app)
            else:
                _batch_processor = DeviceBatchProcessor()
            _batch_processor.start()
            
            # 启动定时清理任务
            def cleanup_worker():
                while _batch_processor.running:
                    time.sleep(1800)  # 每30分钟清理一次
                    _batch_processor.clear_processed_keys()
            
            cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
            cleanup_thread.start()
            
        return _batch_processor

def shutdown_batch_processor():
    """关闭批量处理器"""
    global _batch_processor
    
    with _processor_lock:
        if _batch_processor and _batch_processor.running:
            _batch_processor.stop()
            _batch_processor = None 