"""
健康数据服务
提供健康数据管理的业务逻辑
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import logging

from app.base.mysql import MySQLClient
from app.base.redis import RedisClient
from .analyzer import HealthAnalyzer
from .scorer import HealthScorer

logger = logging.getLogger(__name__)


class HealthDataService:
    """健康数据服务"""
    
    def __init__(self, mysql_client: MySQLClient, redis_client: RedisClient):
        self.mysql = mysql_client
        self.redis = redis_client
        self.analyzer = HealthAnalyzer(mysql_client, redis_client)
        self.scorer = HealthScorer(mysql_client, redis_client)
        self.cache_prefix = "health:"
        self.cache_ttl = 300  # 5分钟
    
    # 健康数据采集
    async def upload_health_data(self, health_data: Dict[str, Any]) -> str:
        """上传健康数据"""
        try:
            # 数据验证和标准化
            validated_data = await self._validate_health_data(health_data)
            
            # 设置默认值
            validated_data.setdefault('collect_time', datetime.now())
            validated_data['created_time'] = datetime.now()
            
            # 确定表名（支持分表）
            table_name = self._get_health_table_name(validated_data['collect_time'])
            
            # 插入数据
            query = f"""
                INSERT INTO {table_name} (
                    user_id, device_id, customer_id, org_id,
                    heart_rate, blood_oxygen, temperature, 
                    pressure_high, pressure_low, stress,
                    step, calorie, distance, sleep_duration,
                    collect_time, created_time, source_type
                ) VALUES (
                    :user_id, :device_id, :customer_id, :org_id,
                    :heart_rate, :blood_oxygen, :temperature,
                    :pressure_high, :pressure_low, :stress,
                    :step, :calorie, :distance, :sleep_duration,
                    :collect_time, :created_time, :source_type
                )
            """
            
            data_id = await self.mysql.execute_insert(query, validated_data)
            
            # 异步处理：触发实时分析和告警检测
            await self._trigger_realtime_analysis(validated_data)
            
            logger.info(f"健康数据上传成功: user={validated_data['user_id']}, id={data_id}")
            return str(data_id)
            
        except Exception as e:
            logger.error(f"健康数据上传失败: {e}")
            raise
    
    async def batch_upload_health_data(self, health_data_list: List[Dict[str, Any]]) -> int:
        """批量上传健康数据"""
        try:
            validated_list = []
            
            # 验证所有数据
            for data in health_data_list:
                validated_data = await self._validate_health_data(data)
                validated_data.setdefault('collect_time', datetime.now())
                validated_data['created_time'] = datetime.now()
                validated_list.append(validated_data)
            
            if not validated_list:
                return 0
            
            # 按表名分组
            table_groups = {}
            for data in validated_list:
                table_name = self._get_health_table_name(data['collect_time'])
                if table_name not in table_groups:
                    table_groups[table_name] = []
                table_groups[table_name].append(data)
            
            total_inserted = 0
            
            # 分表批量插入
            for table_name, data_list in table_groups.items():
                inserted_count = await self.mysql.batch_insert(table_name, data_list)
                total_inserted += inserted_count
            
            logger.info(f"批量健康数据上传成功: {total_inserted} 条记录")
            return total_inserted
            
        except Exception as e:
            logger.error(f"批量健康数据上传失败: {e}")
            raise
    
    # 健康数据查询
    async def get_user_health_data(
        self,
        user_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metrics: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取用户健康数据"""
        try:
            # 默认查询最近24小时
            if not end_time:
                end_time = datetime.now()
            if not start_time:
                start_time = end_time - timedelta(days=1)
            
            # 确定需要查询的表
            table_names = self._get_health_table_names(start_time, end_time)
            
            # 构建查询字段
            if metrics:
                valid_metrics = [m for m in metrics if m in self._get_valid_metrics()]
                select_fields = ['id', 'user_id', 'collect_time'] + valid_metrics
            else:
                select_fields = ['*']
            
            select_clause = ', '.join(select_fields)
            
            all_data = []
            
            # 查询所有相关表
            for table_name in table_names:
                query = f"""
                    SELECT {select_clause}
                    FROM {table_name}
                    WHERE user_id = :user_id
                    AND collect_time BETWEEN :start_time AND :end_time
                    ORDER BY collect_time DESC
                """
                
                params = {
                    'user_id': user_id,
                    'start_time': start_time,
                    'end_time': end_time
                }
                
                table_data = await self.mysql.execute_query(query, params)
                all_data.extend(table_data)
            
            # 按时间排序并限制数量
            all_data.sort(key=lambda x: x['collect_time'], reverse=True)
            
            return all_data[:limit]
            
        except Exception as e:
            logger.error(f"获取用户健康数据失败 {user_id}: {e}")
            raise
    
    async def get_latest_health_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户最新健康数据"""
        cache_key = f"{self.cache_prefix}latest:{user_id}"
        
        # 尝试从缓存获取
        cached_data = await self.redis.get_json(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # 查询最近的表
            current_table = self._get_health_table_name(datetime.now())
            
            query = f"""
                SELECT *
                FROM {current_table}
                WHERE user_id = :user_id
                ORDER BY collect_time DESC
                LIMIT 1
            """
            
            latest_data = await self.mysql.execute_first(query, {'user_id': user_id})
            
            if not latest_data:
                # 如果当前表没有数据，尝试查询上个月的表
                last_month = datetime.now() - timedelta(days=30)
                last_table = self._get_health_table_name(last_month)
                
                if last_table != current_table:
                    query = f"""
                        SELECT *
                        FROM {last_table}
                        WHERE user_id = :user_id
                        ORDER BY collect_time DESC
                        LIMIT 1
                    """
                    
                    latest_data = await self.mysql.execute_first(query, {'user_id': user_id})
            
            if latest_data:
                # 缓存结果（较短的TTL）
                await self.redis.set_json(cache_key, latest_data, 60)  # 1分钟
            
            return latest_data
            
        except Exception as e:
            logger.error(f"获取最新健康数据失败 {user_id}: {e}")
            raise
    
    async def get_health_data_statistics(
        self,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        time_range: str = '24h'
    ) -> Dict[str, Any]:
        """获取健康数据统计"""
        cache_key = f"{self.cache_prefix}stats:{user_id or org_id or customer_id or 'all'}:{time_range}"
        
        # 尝试从缓存获取
        cached_stats = await self.redis.get_json(cache_key)
        if cached_stats:
            return cached_stats
        
        try:
            # 计算时间范围
            end_time = datetime.now()
            if time_range == '1h':
                start_time = end_time - timedelta(hours=1)
            elif time_range == '24h':
                start_time = end_time - timedelta(days=1)
            elif time_range == '7d':
                start_time = end_time - timedelta(days=7)
            elif time_range == '30d':
                start_time = end_time - timedelta(days=30)
            else:
                start_time = end_time - timedelta(days=1)
            
            # 确定查询表
            table_names = self._get_health_table_names(start_time, end_time)
            
            conditions = ["collect_time BETWEEN :start_time AND :end_time"]
            params = {
                'start_time': start_time,
                'end_time': end_time
            }
            
            if user_id:
                conditions.append("user_id = :user_id")
                params['user_id'] = user_id
            elif org_id:
                conditions.append("org_id = :org_id")
                params['org_id'] = org_id
            elif customer_id:
                conditions.append("customer_id = :customer_id")
                params['customer_id'] = customer_id
            
            where_clause = " AND ".join(conditions)
            
            all_stats = {}
            
            # 查询所有表的统计数据
            for table_name in table_names:
                query = f"""
                    SELECT 
                        COUNT(*) as record_count,
                        COUNT(DISTINCT user_id) as user_count,
                        AVG(heart_rate) as avg_heart_rate,
                        AVG(blood_oxygen) as avg_blood_oxygen,
                        AVG(temperature) as avg_temperature,
                        AVG(pressure_high) as avg_pressure_high,
                        AVG(pressure_low) as avg_pressure_low,
                        SUM(step) as total_steps,
                        SUM(calorie) as total_calories,
                        SUM(distance) as total_distance
                    FROM {table_name}
                    WHERE {where_clause}
                """
                
                table_stats = await self.mysql.execute_first(query, params)
                
                # 合并统计数据
                for key, value in table_stats.items():
                    if value is not None:
                        if key in all_stats:
                            if key.startswith('avg_'):
                                # 平均值需要重新计算
                                continue
                            else:
                                all_stats[key] += value
                        else:
                            all_stats[key] = value
            
            # 重新计算平均值
            if all_stats.get('record_count', 0) > 0:
                # 这里需要更精确的平均值计算，简化处理
                pass
            
            stats = {
                'basic': all_stats,
                'time_range': time_range,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'generated_at': datetime.now().isoformat()
            }
            
            # 缓存结果
            await self.redis.set_json(cache_key, stats, 120)  # 2分钟
            
            return stats
            
        except Exception as e:
            logger.error(f"获取健康数据统计失败: {e}")
            raise
    
    # 健康分析
    async def analyze_user_health(
        self, 
        user_id: str,
        analysis_type: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """分析用户健康状况"""
        try:
            return await self.analyzer.analyze_user_health(user_id, analysis_type)
        except Exception as e:
            logger.error(f"用户健康分析失败 {user_id}: {e}")
            raise
    
    async def generate_health_score(self, user_id: str) -> Dict[str, Any]:
        """生成健康评分"""
        try:
            return await self.scorer.calculate_health_score(user_id)
        except Exception as e:
            logger.error(f"健康评分生成失败 {user_id}: {e}")
            raise
    
    async def get_health_trends(
        self,
        user_id: str,
        metrics: List[str],
        time_range: str = '7d'
    ) -> Dict[str, Any]:
        """获取健康趋势"""
        try:
            return await self.analyzer.get_health_trends(user_id, metrics, time_range)
        except Exception as e:
            logger.error(f"获取健康趋势失败 {user_id}: {e}")
            raise
    
    # 私有方法
    async def _validate_health_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证健康数据"""
        required_fields = ['user_id']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必填字段: {field}")
        
        # 数据类型验证和范围检查
        numeric_fields = {
            'heart_rate': (30, 200),
            'blood_oxygen': (70, 100),
            'temperature': (35.0, 42.0),
            'pressure_high': (80, 200),
            'pressure_low': (40, 120),
            'stress': (0, 100),
            'step': (0, 100000),
            'calorie': (0, 10000),
            'distance': (0, 100000)
        }
        
        validated_data = data.copy()
        
        for field, (min_val, max_val) in numeric_fields.items():
            if field in validated_data and validated_data[field] is not None:
                try:
                    value = float(validated_data[field])
                    if not (min_val <= value <= max_val):
                        logger.warning(f"健康数据超出正常范围: {field}={value}")
                    validated_data[field] = value
                except (ValueError, TypeError):
                    logger.warning(f"健康数据类型错误: {field}={validated_data[field]}")
                    validated_data[field] = None
        
        return validated_data
    
    def _get_health_table_name(self, date: datetime) -> str:
        """获取健康数据表名（按月分表）"""
        return f"user_health_data_{date.strftime('%Y_%m')}"
    
    def _get_health_table_names(self, start_time: datetime, end_time: datetime) -> List[str]:
        """获取时间范围内的所有健康数据表名"""
        table_names = []
        current_date = start_time.replace(day=1)  # 月初
        
        while current_date <= end_time:
            table_names.append(self._get_health_table_name(current_date))
            # 下一个月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return list(set(table_names))  # 去重
    
    def _get_valid_metrics(self) -> List[str]:
        """获取有效的健康指标列表"""
        return [
            'heart_rate', 'blood_oxygen', 'temperature',
            'pressure_high', 'pressure_low', 'stress',
            'step', 'calorie', 'distance', 'sleep_duration'
        ]
    
    async def _trigger_realtime_analysis(self, health_data: Dict[str, Any]):
        """触发实时分析和告警检测"""
        try:
            # 异步任务：健康数据分析
            # 这里可以集成 Celery 或其他任务队列
            
            # 简化版本：直接调用
            # await self.analyzer.analyze_realtime_data(health_data)
            
            # 告警检测
            from app.business.alert import AlertService
            # alert_service = AlertService(self.mysql, self.redis)
            # await alert_service.check_health_data_alerts(health_data)
            
            pass
            
        except Exception as e:
            logger.error(f"实时分析触发失败: {e}")
    
    # 缓存管理
    async def clear_health_cache(self, user_id: Optional[str] = None):
        """清除健康数据缓存"""
        try:
            if user_id:
                pattern = f"{self.cache_prefix}*:{user_id}"
            else:
                pattern = f"{self.cache_prefix}*"
            
            keys = await self.redis.scan_keys(pattern)
            if keys:
                await self.redis.delete(*keys)
            
        except Exception as e:
            logger.error(f"清除健康数据缓存失败: {e}")