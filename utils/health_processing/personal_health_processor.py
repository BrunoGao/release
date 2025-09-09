#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
个人健康数据处理器
生成个人健康基线、评分、预测、建议和画像

@Author: bruno.gao <gaojunivas@gmail.com>
@ProjectName: ljwx-boot
@CreateTime: 2025-01-26
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
from auth_manager import AuthManager, create_auth_manager
from database_helper import DatabaseHelper

@dataclass
class HealthProcessingResult:
    """健康数据处理结果"""
    user_id: int
    baseline_success: bool = False
    score_success: bool = False
    prediction_success: bool = False
    recommendation_success: bool = False
    profile_success: bool = False
    baseline_data: Optional[Dict] = None
    score_data: Optional[Dict] = None
    prediction_data: Optional[Dict] = None
    recommendation_data: Optional[Dict] = None
    profile_data: Optional[Dict] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class PersonalHealthProcessor:
    """个人健康数据处理器"""
    
    def __init__(self, base_url: str = "http://localhost:8080", token: str = None, auth_manager: AuthManager = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.auth_manager = auth_manager
        
        # 如果有认证管理器，使用它的session，否则创建新的
        if auth_manager:
            self.session = auth_manager.get_authenticated_session()
            if not self.session:
                raise Exception("认证失败，无法获取有效session")
        else:
            self.session = requests.Session()
            # 设置请求头
            if token:
                self.session.headers.update({
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                })
        
        # 确保Content-Type头存在
        self.session.headers.update({'Content-Type': 'application/json'})
        
        # 初始化数据库辅助工具
        self.db_helper = DatabaseHelper()
        
        # 配置日志
        self.setup_logging()
        
        # API 端点配置
        self.endpoints = {
            'baseline': '/health/baseline',
            'score': '/health/score', 
            'prediction': '/health/prediction',
            'recommendation': '/health/recommendation',
            'profile': '/health/profile',
            'users': '/system/user/list'
        }
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'personal_health_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_authenticated(self) -> bool:
        """确保认证有效"""
        if self.auth_manager:
            if self.auth_manager.ensure_authenticated():
                self.session = self.auth_manager.get_authenticated_session()
                return True
            else:
                self.logger.error("❌ 认证失效且无法重新认证")
                return False
        return True  # 如果没有认证管理器，假设不需要认证
        
    def get_active_users(self, days: int = 30) -> List[Dict]:
        """获取活跃用户列表"""
        try:
            # 使用数据库直接查询活跃用户
            users = self.db_helper.get_active_users(days)
            
            # 转换格式以保持兼容性
            formatted_users = []
            for user in users:
                formatted_users.append({
                    'id': user['user_id'],
                    'username': user['user_name'],
                    'user_name': user['user_name'],
                    'phone': user.get('phone', ''),
                    'customer_id': user.get('customer_id', 1),
                    'org_id': user.get('org_id', 1),
                    'health_data_count': user['health_data_count']
                })
            
            self.logger.info(f"📊 找到 {len(formatted_users)} 个活跃用户")
            return formatted_users
            
        except Exception as e:
            self.logger.error(f"获取活跃用户失败: {str(e)}")
            return []
    
    def generate_personal_baseline(self, user_id: int, days: int = 30) -> Dict:
        """生成个人健康基线"""
        try:
            data = {
                'userId': user_id,
                'days': days,
                'baselineType': 'personal'
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['baseline']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 用户{user_id}基线生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 用户{user_id}基线生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 用户{user_id}基线生成异常: {str(e)}")
            raise
    
    def generate_health_score(self, user_id: int, days: int = 30) -> Dict:
        """生成健康评分"""
        try:
            data = {
                'userId': user_id,
                'days': days,
                'includeWeights': True
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['score']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 用户{user_id}评分生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 用户{user_id}评分生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 用户{user_id}评分生成异常: {str(e)}")
            raise
    
    def generate_health_prediction(self, user_id: int, prediction_days: int = 30) -> Dict:
        """生成健康预测"""
        try:
            data = {
                'userId': user_id,
                'predictionDays': prediction_days,
                'includeTrends': True,
                'includeRiskAssessment': True
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['prediction']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 用户{user_id}预测生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 用户{user_id}预测生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 用户{user_id}预测生成异常: {str(e)}")
            raise
    
    def generate_health_recommendation(self, user_id: int) -> Dict:
        """生成健康建议"""
        try:
            data = {
                'userId': user_id,
                'includePersonalized': True,
                'includeBehavioral': True
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['recommendation']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 用户{user_id}建议生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 用户{user_id}建议生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 用户{user_id}建议生成异常: {str(e)}")
            raise
    
    def generate_health_profile(self, user_id: int, days: int = 90) -> Dict:
        """生成健康画像"""
        try:
            data = {
                'userId': user_id,
                'days': days,
                'includeRiskProfile': True,
                'includeBehaviorProfile': True,
                'includeHealthTrends': True
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['profile']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 用户{user_id}画像生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 用户{user_id}画像生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 用户{user_id}画像生成异常: {str(e)}")
            raise
    
    def process_single_user(self, user: Dict, config: Dict) -> HealthProcessingResult:
        """处理单个用户的健康数据"""
        user_id = user['id']
        result = HealthProcessingResult(user_id=user_id)
        
        self.logger.info(f"🔄 开始处理用户{user_id}: {user.get('username', 'Unknown')}")
        
        # 1. 生成健康基线
        if config.get('generate_baseline', True):
            try:
                result.baseline_data = self.generate_personal_baseline(
                    user_id, config.get('baseline_days', 30))
                result.baseline_success = True
            except Exception as e:
                result.errors.append(f"基线生成失败: {str(e)}")
        
        # 2. 生成健康评分
        if config.get('generate_score', True):
            try:
                result.score_data = self.generate_health_score(
                    user_id, config.get('score_days', 30))
                result.score_success = True
            except Exception as e:
                result.errors.append(f"评分生成失败: {str(e)}")
        
        # 3. 生成健康预测
        if config.get('generate_prediction', True):
            try:
                result.prediction_data = self.generate_health_prediction(
                    user_id, config.get('prediction_days', 30))
                result.prediction_success = True
            except Exception as e:
                result.errors.append(f"预测生成失败: {str(e)}")
        
        # 4. 生成健康建议
        if config.get('generate_recommendation', True):
            try:
                result.recommendation_data = self.generate_health_recommendation(user_id)
                result.recommendation_success = True
            except Exception as e:
                result.errors.append(f"建议生成失败: {str(e)}")
        
        # 5. 生成健康画像
        if config.get('generate_profile', True):
            try:
                result.profile_data = self.generate_health_profile(
                    user_id, config.get('profile_days', 90))
                result.profile_success = True
            except Exception as e:
                result.errors.append(f"画像生成失败: {str(e)}")
        
        success_count = sum([
            result.baseline_success, result.score_success, 
            result.prediction_success, result.recommendation_success, result.profile_success
        ])
        
        if result.errors:
            self.logger.warning(f"⚠️ 用户{user_id}处理完成，成功{success_count}项，失败{len(result.errors)}项")
            for error in result.errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info(f"✅ 用户{user_id}处理完成，成功{success_count}项")
        
        return result
    
    def process_all_users(self, config: Dict = None) -> List[HealthProcessingResult]:
        """批量处理所有用户的健康数据"""
        if config is None:
            config = {
                'generate_baseline': True,
                'generate_score': True, 
                'generate_prediction': True,
                'generate_recommendation': True,
                'generate_profile': True,
                'baseline_days': 30,
                'score_days': 30,
                'prediction_days': 30,
                'profile_days': 90,
                'max_workers': 5,
                'user_days': 30
            }
        
        self.logger.info("🚀 开始批量处理个人健康数据")
        start_time = time.time()
        
        # 获取活跃用户
        users = self.get_active_users(config.get('user_days', 30))
        if not users:
            self.logger.warning("⚠️ 没有找到活跃用户")
            return []
        
        results = []
        max_workers = config.get('max_workers', 5)
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_user = {
                executor.submit(self.process_single_user, user, config): user 
                for user in users
            }
            
            # 收集结果
            for future in as_completed(future_to_user):
                user = future_to_user[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ 用户{user['id']}处理异常: {str(e)}")
                    error_result = HealthProcessingResult(
                        user_id=user['id'],
                        errors=[f"处理异常: {str(e)}"]
                    )
                    results.append(error_result)
        
        # 统计结果
        total_users = len(results)
        success_stats = {
            'baseline': sum(1 for r in results if r.baseline_success),
            'score': sum(1 for r in results if r.score_success),
            'prediction': sum(1 for r in results if r.prediction_success),
            'recommendation': sum(1 for r in results if r.recommendation_success),
            'profile': sum(1 for r in results if r.profile_success)
        }
        
        error_count = sum(1 for r in results if r.errors)
        elapsed_time = time.time() - start_time
        
        self.logger.info("🎉 个人健康数据批量处理完成!")
        self.logger.info(f"📊 处理统计:")
        self.logger.info(f"  - 总用户数: {total_users}")
        self.logger.info(f"  - 基线生成成功: {success_stats['baseline']}")
        self.logger.info(f"  - 评分生成成功: {success_stats['score']}")
        self.logger.info(f"  - 预测生成成功: {success_stats['prediction']}")
        self.logger.info(f"  - 建议生成成功: {success_stats['recommendation']}")
        self.logger.info(f"  - 画像生成成功: {success_stats['profile']}")
        self.logger.info(f"  - 有错误的用户: {error_count}")
        self.logger.info(f"  - 总耗时: {elapsed_time:.2f}秒")
        
        return results
    
    def save_results(self, results: List[HealthProcessingResult], output_file: str = None):
        """保存处理结果到文件"""
        if output_file is None:
            output_file = f'personal_health_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # 将结果转换为可序列化的格式
        serializable_results = []
        for result in results:
            serializable_results.append({
                'user_id': result.user_id,
                'baseline_success': result.baseline_success,
                'score_success': result.score_success,
                'prediction_success': result.prediction_success,
                'recommendation_success': result.recommendation_success,
                'profile_success': result.profile_success,
                'baseline_data': result.baseline_data,
                'score_data': result.score_data,
                'prediction_data': result.prediction_data,
                'recommendation_data': result.recommendation_data,
                'profile_data': result.profile_data,
                'errors': result.errors
            })
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2, default=str)
            
            self.logger.info(f"📁 处理结果已保存到: {output_file}")
            return output_file
        except Exception as e:
            self.logger.error(f"❌ 保存结果失败: {str(e)}")
            return None

def main():
    """主函数"""
    # 配置参数
    config = {
        'base_url': 'http://localhost:8080',
        'token': None,  # 如果需要认证，在这里设置token
        'generate_baseline': True,
        'generate_score': True,
        'generate_prediction': True,
        'generate_recommendation': True,
        'generate_profile': True,
        'baseline_days': 30,
        'score_days': 30,
        'prediction_days': 30,
        'profile_days': 90,
        'user_days': 30,  # 获取最近30天活跃的用户
        'max_workers': 5  # 并发线程数
    }
    
    # 创建处理器
    processor = PersonalHealthProcessor(
        base_url=config['base_url'],
        token=config['token']
    )
    
    # 执行批量处理
    results = processor.process_all_users(config)
    
    # 保存结果
    if results:
        output_file = processor.save_results(results)
        print(f"\n🎉 个人健康数据处理完成!")
        print(f"📁 结果文件: {output_file}")
    else:
        print("\n⚠️ 没有处理任何用户数据")

if __name__ == "__main__":
    main()