#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
健康查询基础模块
提供统一的查询参数解析、验证和日志记录功能
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class HealthQueryBase:
    """健康查询基础类"""

    def __init__(self):
        self.logger = logger

    def parse_query_params(self, **kwargs) -> Dict[str, Any]:
        """
        解析和标准化查询参数

        Args:
            user_id: 用户ID
            org_id: 组织ID
            customer_id: 租户ID
            startDate/start_date: 开始日期
            endDate/end_date: 结束日期
            days: 查询天数（默认7天）

        Returns:
            Dict: 标准化的查询参数
        """
        # 提取ID参数
        user_id = kwargs.get('user_id') or kwargs.get('userId')
        org_id = kwargs.get('org_id') or kwargs.get('orgId')
        customer_id = kwargs.get('customer_id') or kwargs.get('customerId')

        # 提取日期参数
        start_date = kwargs.get('start_date') or kwargs.get('startDate')
        end_date = kwargs.get('end_date') or kwargs.get('endDate')
        days = kwargs.get('days', 7)

        # 如果没有指定日期，使用days参数计算
        if not start_date or not end_date:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=int(days))
        else:
            # 转换字符串日期为datetime对象
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # 其他参数
        include_factors = kwargs.get('includeFactors', kwargs.get('include_factors', False))
        include_trends = kwargs.get('includeTrends', kwargs.get('include_trends', False))

        # 确定查询层级和标识符
        query_level = None
        identifier = None

        if user_id:
            query_level = 'user'
            identifier = user_id
        elif org_id:
            query_level = 'org'
            identifier = org_id
        elif customer_id:
            query_level = 'customer'
            identifier = customer_id

        return {
            'user_id': user_id,
            'org_id': org_id,
            'customer_id': customer_id,
            'query_level': query_level,
            'identifier': identifier,
            'start_date': start_date,
            'end_date': end_date,
            'days': days,
            'include_factors': include_factors,
            'include_trends': include_trends
        }

    def validate_query_params(self, query_params: Dict) -> Tuple[bool, Optional[str]]:
        """
        验证查询参数

        Args:
            query_params: 查询参数字典

        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 错误消息)
        """
        # 至少需要一个ID参数
        user_id = query_params.get('user_id')
        org_id = query_params.get('org_id')
        customer_id = query_params.get('customer_id')

        if not any([user_id, org_id, customer_id]):
            return False, '缺少必需参数: user_id, org_id 或 customer_id 至少需要一个'

        # 验证日期参数
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                return False, '开始日期不能晚于结束日期'

            # 检查日期范围（不超过90天）
            date_diff = (end_date - start_date).days
            if date_diff > 90:
                return False, '日期范围不能超过90天'

        return True, None

    def log_query_info(self, query_type: str, query_params: Dict, result_summary: Optional[Dict] = None):
        """
        记录查询信息

        Args:
            query_type: 查询类型（如 'score', 'baseline', 'recommendation'）
            query_params: 查询参数
            result_summary: 结果摘要（可选）
        """
        log_msg = f"[{query_type}] 查询参数: "

        # 构建日志消息
        if query_params.get('user_id'):
            log_msg += f"user_id={query_params['user_id']}, "
        if query_params.get('org_id'):
            log_msg += f"org_id={query_params['org_id']}, "
        if query_params.get('customer_id'):
            log_msg += f"customer_id={query_params['customer_id']}, "

        if query_params.get('start_date'):
            log_msg += f"start_date={query_params['start_date'].strftime('%Y-%m-%d')}, "
        if query_params.get('end_date'):
            log_msg += f"end_date={query_params['end_date'].strftime('%Y-%m-%d')}"

        # 添加结果摘要
        if result_summary:
            log_msg += f" | 结果: {result_summary}"

        self.logger.info(log_msg)

    def build_cache_key(self, query_type: str, query_params: Dict) -> str:
        """
        构建缓存键

        Args:
            query_type: 查询类型
            query_params: 查询参数

        Returns:
            str: 缓存键
        """
        key_parts = [f"health:{query_type}"]

        if query_params.get('user_id'):
            key_parts.append(f"user:{query_params['user_id']}")
        elif query_params.get('org_id'):
            key_parts.append(f"org:{query_params['org_id']}")
        elif query_params.get('customer_id'):
            key_parts.append(f"customer:{query_params['customer_id']}")

        if query_params.get('start_date'):
            key_parts.append(query_params['start_date'].strftime('%Y%m%d'))
        if query_params.get('end_date'):
            key_parts.append(query_params['end_date'].strftime('%Y%m%d'))

        return ":".join(key_parts)

    def build_database_conditions(self, query_params: Dict) -> Tuple[list, Dict]:
        """
        构建数据库查询条件

        Args:
            query_params: 查询参数

        Returns:
            Tuple[list, Dict]: (条件列表, 参数字典)
        """
        conditions = []
        params = {}

        # 根据查询层级构建条件
        query_level = query_params.get('query_level')
        identifier = query_params.get('identifier')

        if query_level and identifier:
            if query_level == 'user':
                conditions.append('user_id = :identifier')
            elif query_level == 'org':
                conditions.append('org_id = :identifier')
            elif query_level == 'customer':
                conditions.append('customer_id = :identifier')

            params['identifier'] = identifier

        # 日期条件
        start_date = query_params.get('start_date')
        end_date = query_params.get('end_date')

        if start_date and end_date:
            if start_date == end_date:
                conditions.append('score_date = :score_date')
                params['score_date'] = start_date
            else:
                conditions.append('score_date BETWEEN :start_date AND :end_date')
                params['start_date'] = start_date
                params['end_date'] = end_date

        return conditions, params


# 全局单例实例
health_query_base = HealthQueryBase()
