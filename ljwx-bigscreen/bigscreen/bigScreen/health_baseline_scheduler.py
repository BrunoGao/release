#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康基线和评分生成定时任务系统
基于健康数据定期生成个人和组织健康基线，计算健康评分
"""

import threading
import time
import schedule
import logging
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Tuple
import numpy as np
from sqlalchemy import func, and_, or_
from flask import current_app

from .models import db, HealthBaseline, OrgHealthBaseline, UserInfo, UserOrg, OrgInfo
from .user_health_data import get_all_health_data_optimized
from .health_daping_analyzer import generate_health_score

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthBaselineScheduler:
    """健康基线生成调度器"""
    
    def __init__(self, app=None):
        self.app = app
        self.running = False
        self.scheduler_thread = None
        
        # 健康指标配置
        self.health_features = {
            'heart_rate': {'min_samples': 10, 'valid_range': (40, 200)},
            'blood_oxygen': {'min_samples': 5, 'valid_range': (80, 100)},
            'temperature': {'min_samples': 5, 'valid_range': (35.0, 42.0)},
            'step': {'min_samples': 3, 'valid_range': (0, 50000)},
            'calorie': {'min_samples': 3, 'valid_range': (0, 5000)},
            'pressure_high': {'min_samples': 5, 'valid_range': (80, 200)},
            'pressure_low': {'min_samples': 5, 'valid_range': (40, 130)},
            'stress': {'min_samples': 3, 'valid_range': (0, 100)},
            'sleep_hours': {'min_samples': 1, 'valid_range': (0, 24)}
        }
    
    def start(self):
        """启动定时任务调度器"""
        if self.running:
            logger.warning("健康基线调度器已经在运行")
            return
        
        self.running = True
        logger.info("🏥 启动健康基线生成调度器")
        
        # 配置定时任务
        # 每日凌晨2点生成个人基线
        schedule.every().day.at("02:00").do(self._generate_daily_personal_baselines)
        
        # 每日凌晨3点生成组织基线
        schedule.every().day.at("03:00").do(self._generate_daily_org_baselines)
        
        # 每日凌晨4点生成健康评分
        schedule.every().day.at("04:00").do(self._generate_daily_health_scores)
        
        # 每周日凌晨1点生成周基线
        schedule.every().sunday.at("01:00").do(self._generate_weekly_baselines)
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ 健康基线调度器启动完成")
    
    def stop(self):
        """停止定时任务调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("⛔ 健康基线调度器已停止")
    
    def _run_scheduler(self):
        """调度器主循环"""
        logger.info("📅 健康基线调度器开始运行")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"❌ 调度器运行异常: {e}")
                time.sleep(300)  # 出错后等待5分钟再继续
    
    def _generate_daily_personal_baselines(self):
        """生成日常个人健康基线"""
        try:
            with self.app.app_context():
                logger.info("🔄 开始生成日常个人健康基线")
                
                # 获取昨天的数据
                yesterday = date.today() - timedelta(days=1)
                start_date = yesterday.strftime('%Y-%m-%d')
                end_date = start_date
                
                # 获取所有活跃用户
                users = self._get_active_users()
                logger.info(f"📊 找到 {len(users)} 个活跃用户")
                
                success_count = 0
                for user in users:
                    try:
                        if self._generate_user_baseline(user, start_date, end_date):
                            success_count += 1
                    except Exception as e:
                        logger.error(f"❌ 生成用户 {user['user_id']} 基线失败: {e}")
                
                logger.info(f"✅ 日常个人基线生成完成: 成功 {success_count}/{len(users)}")
                
        except Exception as e:
            logger.error(f"❌ 生成日常个人基线失败: {e}")
    
    def _generate_daily_org_baselines(self):
        """生成日常组织健康基线"""
        try:
            with self.app.app_context():
                logger.info("🔄 开始生成日常组织健康基线")
                
                yesterday = date.today() - timedelta(days=1)
                
                # 获取所有组织
                orgs = self._get_active_orgs()
                logger.info(f"🏢 找到 {len(orgs)} 个活跃组织")
                
                success_count = 0
                for org in orgs:
                    try:
                        if self._generate_org_baseline(org['org_id'], yesterday):
                            success_count += 1
                    except Exception as e:
                        logger.error(f"❌ 生成组织 {org['org_id']} 基线失败: {e}")
                
                logger.info(f"✅ 日常组织基线生成完成: 成功 {success_count}/{len(orgs)}")
                
        except Exception as e:
            logger.error(f"❌ 生成日常组织基线失败: {e}")
    
    def _generate_daily_health_scores(self):
        """生成日常健康评分"""
        try:
            with self.app.app_context():
                logger.info("🔄 开始生成日常健康评分")
                
                # 获取昨天的数据
                yesterday = date.today() - timedelta(days=1)
                start_date = yesterday.strftime('%Y-%m-%d')
                end_date = start_date
                
                # 获取所有有基线的用户
                users_with_baseline = self._get_users_with_baseline()
                logger.info(f"📊 找到 {len(users_with_baseline)} 个有基线的用户")
                
                success_count = 0
                for user in users_with_baseline:
                    try:
                        if self._generate_user_health_score(user, start_date, end_date):
                            success_count += 1
                    except Exception as e:
                        logger.error(f"❌ 生成用户 {user['user_id']} 健康评分失败: {e}")
                
                logger.info(f"✅ 日常健康评分生成完成: 成功 {success_count}/{len(users_with_baseline)}")
                
        except Exception as e:
            logger.error(f"❌ 生成日常健康评分失败: {e}")
    
    def _generate_weekly_baselines(self):
        """生成周基线"""
        try:
            with self.app.app_context():
                logger.info("🔄 开始生成周健康基线")
                
                # 获取上周数据
                today = date.today()
                last_sunday = today - timedelta(days=today.weekday() + 1)
                week_start = last_sunday - timedelta(days=6)
                week_end = last_sunday
                
                start_date = week_start.strftime('%Y-%m-%d')
                end_date = week_end.strftime('%Y-%m-%d')
                
                # 生成周个人基线
                users = self._get_active_users()
                user_success = 0
                for user in users:
                    try:
                        if self._generate_user_baseline(user, start_date, end_date, baseline_type='weekly'):
                            user_success += 1
                    except Exception as e:
                        logger.error(f"❌ 生成用户 {user['user_id']} 周基线失败: {e}")
                
                # 生成周组织基线
                orgs = self._get_active_orgs()
                org_success = 0
                for org in orgs:
                    try:
                        if self._generate_org_baseline(org['org_id'], week_end, baseline_type='weekly'):
                            org_success += 1
                    except Exception as e:
                        logger.error(f"❌ 生成组织 {org['org_id']} 周基线失败: {e}")
                
                logger.info(f"✅ 周基线生成完成: 用户 {user_success}/{len(users)}, 组织 {org_success}/{len(orgs)}")
                
        except Exception as e:
            logger.error(f"❌ 生成周基线失败: {e}")
    
    def _get_active_users(self) -> List[Dict]:
        """获取活跃用户列表"""
        try:
            users = db.session.query(
                UserInfo.id.label('user_id'),
                UserInfo.user_name,
                UserInfo.device_sn,
                UserOrg.org_id
            ).join(
                UserOrg, UserInfo.id == UserOrg.user_id
            ).filter(
                UserInfo.is_deleted == False,
                UserInfo.device_sn.isnot(None),
                UserInfo.device_sn != '',
                UserInfo.device_sn != '-'
            ).all()
            
            return [{'user_id': u.user_id, 'user_name': u.user_name, 
                    'device_sn': u.device_sn, 'org_id': u.org_id} for u in users]
        except Exception as e:
            logger.error(f"❌ 获取活跃用户失败: {e}")
            return []
    
    def _get_active_orgs(self) -> List[Dict]:
        """获取活跃组织列表"""
        try:
            orgs = db.session.query(
                OrgInfo.id.label('org_id'),
                OrgInfo.name.label('org_name')
            ).filter(
                OrgInfo.is_deleted == False,
                OrgInfo.status == '1'
            ).all()
            
            return [{'org_id': o.org_id, 'org_name': o.org_name} for o in orgs]
        except Exception as e:
            logger.error(f"❌ 获取活跃组织失败: {e}")
            return []
    
    def _get_users_with_baseline(self) -> List[Dict]:
        """获取有基线数据的用户"""
        try:
            users = db.session.query(
                HealthBaseline.user_id,
                UserInfo.user_name,
                UserInfo.device_sn
            ).join(
                UserInfo, HealthBaseline.user_id == UserInfo.id
            ).filter(
                HealthBaseline.is_current == True,
                UserInfo.is_deleted == False
            ).distinct().all()
            
            return [{'user_id': u.user_id, 'user_name': u.user_name, 
                    'device_sn': u.device_sn} for u in users]
        except Exception as e:
            logger.error(f"❌ 获取有基线用户失败: {e}")
            return []
    
    def _generate_user_baseline(self, user: Dict, start_date: str, end_date: str, baseline_type: str = 'daily') -> bool:
        """为单个用户生成健康基线"""
        try:
            # 获取用户健康数据
            health_data = get_all_health_data_optimized(
                userId=user['user_id'],
                startDate=start_date,
                endDate=end_date,
                pageSize=10000
            )
            
            if not health_data.get('success') or not health_data.get('data', {}).get('healthData'):
                return False
            
            raw_data = health_data['data']['healthData']
            logger.info(f"📊 用户 {user['user_id']} 获取到 {len(raw_data)} 条健康数据")
            
            # 按特征分组数据
            feature_data = self._group_health_data_by_feature(raw_data)
            
            # 生成基线日期
            baseline_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
            success_count = 0
            for feature_name, values in feature_data.items():
                if feature_name not in self.health_features:
                    continue
                
                # 计算基线统计信息
                baseline_stats = self._calculate_baseline_stats(feature_name, values)
                if not baseline_stats:
                    continue
                
                # 保存基线数据
                if self._save_user_baseline(user, feature_name, baseline_date, baseline_stats, baseline_type):
                    success_count += 1
            
            logger.info(f"✅ 用户 {user['user_id']} 基线生成成功: {success_count} 个特征")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 生成用户 {user['user_id']} 基线失败: {e}")
            return False
    
    def _group_health_data_by_feature(self, raw_data: List[Dict]) -> Dict[str, List[float]]:
        """将健康数据按特征分组"""
        feature_data = {}
        
        for record in raw_data:
            # 处理各种健康指标
            if record.get('heart_rate') is not None:
                self._add_to_feature(feature_data, 'heart_rate', record['heart_rate'])
            
            if record.get('blood_oxygen') is not None:
                self._add_to_feature(feature_data, 'blood_oxygen', record['blood_oxygen'])
            
            if record.get('temperature') is not None:
                self._add_to_feature(feature_data, 'temperature', record['temperature'])
            
            if record.get('step') is not None:
                self._add_to_feature(feature_data, 'step', record['step'])
            
            if record.get('calorie') is not None:
                self._add_to_feature(feature_data, 'calorie', record['calorie'])
            
            if record.get('pressure_high') is not None:
                self._add_to_feature(feature_data, 'pressure_high', record['pressure_high'])
            
            if record.get('pressure_low') is not None:
                self._add_to_feature(feature_data, 'pressure_low', record['pressure_low'])
            
            if record.get('stress') is not None:
                self._add_to_feature(feature_data, 'stress', record['stress'])
            
            # 处理睡眠数据
            if record.get('sleep_hours') is not None:
                self._add_to_feature(feature_data, 'sleep_hours', record['sleep_hours'])
        
        return feature_data
    
    def _add_to_feature(self, feature_data: Dict, feature_name: str, value):
        """添加值到特征数据中"""
        try:
            float_value = float(value)
            # 检查值是否在有效范围内
            if feature_name in self.health_features:
                min_val, max_val = self.health_features[feature_name]['valid_range']
                if min_val <= float_value <= max_val:
                    if feature_name not in feature_data:
                        feature_data[feature_name] = []
                    feature_data[feature_name].append(float_value)
        except (ValueError, TypeError):
            pass
    
    def _calculate_baseline_stats(self, feature_name: str, values: List[float]) -> Optional[Dict]:
        """计算基线统计信息"""
        if not values:
            return None
        
        feature_config = self.health_features.get(feature_name)
        if not feature_config or len(values) < feature_config['min_samples']:
            return None
        
        try:
            values_array = np.array(values)
            
            # 去除异常值（使用IQR方法）
            q1, q3 = np.percentile(values_array, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            filtered_values = values_array[(values_array >= lower_bound) & (values_array <= upper_bound)]
            
            if len(filtered_values) < feature_config['min_samples']:
                filtered_values = values_array  # 如果过滤后数据太少，使用原始数据
            
            return {
                'mean_value': float(np.mean(filtered_values)),
                'std_value': float(np.std(filtered_values)),
                'min_value': float(np.min(filtered_values)),
                'max_value': float(np.max(filtered_values)),
                'sample_count': len(filtered_values)
            }
        except Exception as e:
            logger.error(f"❌ 计算 {feature_name} 基线统计失败: {e}")
            return None
    
    def _save_user_baseline(self, user: Dict, feature_name: str, baseline_date: date, 
                           stats: Dict, baseline_type: str = 'daily') -> bool:
        """保存用户基线数据"""
        try:
            # 先设置旧基线为非当前
            db.session.query(HealthBaseline).filter(
                HealthBaseline.user_id == user['user_id'],
                HealthBaseline.feature_name == feature_name,
                HealthBaseline.is_current == True
            ).update({'is_current': False})
            
            # 创建新基线
            baseline = HealthBaseline(
                device_sn=user['device_sn'],
                user_id=user['user_id'],
                feature_name=feature_name,
                baseline_date=baseline_date,
                mean_value=stats['mean_value'],
                std_value=stats['std_value'],
                min_value=stats['min_value'],
                max_value=stats['max_value'],
                sample_count=stats['sample_count'],
                is_current=True,
                create_user='system',
                create_user_id=0,
                baseline_time=datetime.now()
            )
            
            db.session.add(baseline)
            db.session.commit()
            
            logger.debug(f"✅ 保存用户 {user['user_id']} {feature_name} 基线成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存用户 {user['user_id']} {feature_name} 基线失败: {e}")
            db.session.rollback()
            return False
    
    def _generate_org_baseline(self, org_id: int, baseline_date: date, baseline_type: str = 'daily') -> bool:
        """为组织生成健康基线"""
        try:
            logger.info(f"🏢 开始生成组织 {org_id} 的健康基线")
            
            # 获取组织下所有有效基线的用户
            user_baselines = db.session.query(
                HealthBaseline.feature_name,
                HealthBaseline.mean_value,
                HealthBaseline.std_value,
                HealthBaseline.min_value,
                HealthBaseline.max_value,
                HealthBaseline.sample_count,
                HealthBaseline.user_id
            ).join(
                UserOrg, HealthBaseline.user_id == UserOrg.user_id
            ).filter(
                UserOrg.org_id == org_id,
                HealthBaseline.is_current == True,
                HealthBaseline.baseline_date == baseline_date
            ).all()
            
            if not user_baselines:
                logger.warning(f"⚠️ 组织 {org_id} 没有有效的个人基线数据")
                return False
            
            # 按特征分组
            feature_groups = {}
            for baseline in user_baselines:
                feature = baseline.feature_name
                if feature not in feature_groups:
                    feature_groups[feature] = []
                feature_groups[feature].append(baseline)
            
            success_count = 0
            for feature_name, baselines in feature_groups.items():
                # 计算组织级统计信息
                org_stats = self._calculate_org_baseline_stats(baselines)
                if org_stats and self._save_org_baseline(org_id, feature_name, baseline_date, org_stats):
                    success_count += 1
            
            logger.info(f"✅ 组织 {org_id} 基线生成成功: {success_count} 个特征")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ 生成组织 {org_id} 基线失败: {e}")
            return False
    
    def _calculate_org_baseline_stats(self, baselines: List) -> Optional[Dict]:
        """计算组织级基线统计信息"""
        try:
            if len(baselines) < 2:  # 至少需要2个用户的数据
                return None
            
            mean_values = [b.mean_value for b in baselines if b.mean_value is not None]
            min_values = [b.min_value for b in baselines if b.min_value is not None]
            max_values = [b.max_value for b in baselines if b.max_value is not None]
            
            if not mean_values:
                return None
            
            return {
                'mean_value': float(np.mean(mean_values)),
                'std_value': float(np.std(mean_values)),
                'min_value': float(np.min(min_values)) if min_values else None,
                'max_value': float(np.max(max_values)) if max_values else None,
                'user_count': len(baselines),
                'sample_count': sum(b.sample_count for b in baselines if b.sample_count)
            }
        except Exception as e:
            logger.error(f"❌ 计算组织基线统计失败: {e}")
            return None
    
    def _save_org_baseline(self, org_id: int, feature_name: str, baseline_date: date, stats: Dict) -> bool:
        """保存组织基线数据"""
        try:
            # 删除或更新已存在的记录
            existing = db.session.query(OrgHealthBaseline).filter(
                OrgHealthBaseline.org_id == org_id,
                OrgHealthBaseline.feature_name == feature_name,
                OrgHealthBaseline.baseline_date == baseline_date
            ).first()
            
            if existing:
                # 更新现有记录
                existing.mean_value = stats['mean_value']
                existing.std_value = stats['std_value']
                existing.min_value = stats.get('min_value')
                existing.max_value = stats.get('max_value')
                existing.user_count = stats['user_count']
                existing.sample_count = stats['sample_count']
                existing.update_time = datetime.now()
            else:
                # 创建新记录
                baseline = OrgHealthBaseline(
                    org_id=org_id,
                    feature_name=feature_name,
                    baseline_date=baseline_date,
                    mean_value=stats['mean_value'],
                    std_value=stats['std_value'],
                    min_value=stats.get('min_value'),
                    max_value=stats.get('max_value'),
                    user_count=stats['user_count'],
                    sample_count=stats['sample_count']
                )
                db.session.add(baseline)
            
            db.session.commit()
            logger.debug(f"✅ 保存组织 {org_id} {feature_name} 基线成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存组织 {org_id} {feature_name} 基线失败: {e}")
            db.session.rollback()
            return False
    
    def _generate_user_health_score(self, user: Dict, start_date: str, end_date: str) -> bool:
        """为用户生成健康评分"""
        try:
            # 获取用户当天健康数据
            health_data = get_all_health_data_optimized(
                userId=user['user_id'],
                startDate=start_date,
                endDate=end_date,
                pageSize=1000
            )
            
            if not health_data.get('success') or not health_data.get('data', {}).get('healthData'):
                return False
            
            # 获取用户健康基线
            baselines = db.session.query(HealthBaseline).filter(
                HealthBaseline.user_id == user['user_id'],
                HealthBaseline.is_current == True
            ).all()
            
            if not baselines:
                logger.warning(f"⚠️ 用户 {user['user_id']} 没有健康基线数据")
                return False
            
            # 调用健康评分生成函数
            score_result = generate_health_score(
                orgId=None,
                userId=user['user_id'],
                startDate=start_date,
                endDate=end_date
            )
            
            if score_result.get('success'):
                logger.debug(f"✅ 用户 {user['user_id']} 健康评分生成成功")
                return True
            else:
                logger.warning(f"⚠️ 用户 {user['user_id']} 健康评分生成失败: {score_result.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 生成用户 {user['user_id']} 健康评分失败: {e}")
            return False
    
    def manual_generate_baseline(self, user_id: Optional[int] = None, org_id: Optional[int] = None, 
                                start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
        """手动生成基线（用于调试和补充数据）"""
        try:
            with self.app.app_context():
                if not start_date or not end_date:
                    yesterday = date.today() - timedelta(days=1)
                    start_date = end_date = yesterday.strftime('%Y-%m-%d')
                
                results = {'personal': 0, 'org': 0, 'errors': []}
                
                # 生成个人基线
                if user_id:
                    user_info = db.session.query(UserInfo, UserOrg.org_id).join(
                        UserOrg, UserInfo.id == UserOrg.user_id
                    ).filter(UserInfo.id == user_id).first()
                    
                    if user_info:
                        user_dict = {
                            'user_id': user_info[0].id,
                            'user_name': user_info[0].user_name,
                            'device_sn': user_info[0].device_sn,
                            'org_id': user_info[1]
                        }
                        if self._generate_user_baseline(user_dict, start_date, end_date):
                            results['personal'] = 1
                else:
                    users = self._get_active_users()
                    for user in users:
                        try:
                            if self._generate_user_baseline(user, start_date, end_date):
                                results['personal'] += 1
                        except Exception as e:
                            results['errors'].append(f"用户 {user['user_id']}: {str(e)}")
                
                # 生成组织基线
                if org_id:
                    baseline_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    if self._generate_org_baseline(org_id, baseline_date):
                        results['org'] = 1
                else:
                    orgs = self._get_active_orgs()
                    baseline_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    for org in orgs:
                        try:
                            if self._generate_org_baseline(org['org_id'], baseline_date):
                                results['org'] += 1
                        except Exception as e:
                            results['errors'].append(f"组织 {org['org_id']}: {str(e)}")
                
                return {
                    'success': True,
                    'data': results,
                    'message': f"基线生成完成: 个人 {results['personal']}, 组织 {results['org']}"
                }
                
        except Exception as e:
            return {'success': False, 'message': f'手动生成基线失败: {str(e)}'}

# 全局调度器实例
_health_baseline_scheduler = None

def get_health_baseline_scheduler(app=None):
    """获取健康基线调度器单例"""
    global _health_baseline_scheduler
    if _health_baseline_scheduler is None:
        _health_baseline_scheduler = HealthBaselineScheduler(app)
    return _health_baseline_scheduler

def init_health_baseline_scheduler(app):
    """初始化健康基线调度器"""
    scheduler = get_health_baseline_scheduler(app)
    scheduler.start()
    logger.info("✅ 健康基线调度器初始化完成")
    return scheduler