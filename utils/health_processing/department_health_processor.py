#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
部门健康数据处理器
生成部门健康基线、评分、预测、建议和画像

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

@dataclass
class DepartmentHealthResult:
    """部门健康数据处理结果"""
    org_id: int
    org_name: str
    baseline_success: bool = False
    score_success: bool = False
    prediction_success: bool = False
    recommendation_success: bool = False
    profile_success: bool = False
    user_count: int = 0
    baseline_data: Optional[Dict] = None
    score_data: Optional[Dict] = None
    prediction_data: Optional[Dict] = None
    recommendation_data: Optional[Dict] = None
    profile_data: Optional[Dict] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class DepartmentHealthProcessor:
    """部门健康数据处理器"""
    
    def __init__(self, base_url: str = "http://localhost:8080", token: str = None):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session = requests.Session()
        
        # 设置请求头
        if token:
            self.session.headers.update({
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            })
        
        # 配置日志
        self.setup_logging()
        
        # API 端点配置
        self.endpoints = {
            'org_baseline': '/health/baseline/organization',
            'org_score': '/health/score/organization', 
            'org_prediction': '/health/prediction/organization',
            'org_recommendation': '/health/recommendation/organization',
            'org_profile': '/health/profile/organization',
            'organizations': '/system/org/list',
            'org_users': '/system/user/org'
        }
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'department_health_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_active_organizations(self, days: int = 30) -> List[Dict]:
        """获取活跃组织列表"""
        try:
            # 获取过去N天有健康数据的组织
            params = {
                'pageSize': 1000,
                'current': 1,
                'days': days,
                'hasHealthData': True,
                'includeUserCount': True
            }
            
            response = self.session.get(f"{self.base_url}{self.endpoints['organizations']}", params=params)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200 and result.get('data'):
                orgs = result['data'].get('records', [])
                # 过滤掉用户数少于2的组织
                active_orgs = [org for org in orgs if org.get('userCount', 0) >= 2]
                self.logger.info(f"📊 找到 {len(active_orgs)} 个活跃组织")
                return active_orgs
            else:
                self.logger.error(f"获取组织列表失败: {result.get('msg', 'Unknown error')}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取活跃组织失败: {str(e)}")
            return []
    
    def get_organization_users(self, org_id: int) -> List[Dict]:
        """获取组织用户列表"""
        try:
            params = {
                'orgId': org_id,
                'pageSize': 1000,
                'current': 1
            }
            
            response = self.session.get(f"{self.base_url}{self.endpoints['org_users']}", params=params)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200 and result.get('data'):
                users = result['data'].get('records', [])
                return users
            else:
                self.logger.warning(f"获取组织{org_id}用户列表失败: {result.get('msg', 'Unknown error')}")
                return []
                
        except Exception as e:
            self.logger.error(f"获取组织{org_id}用户失败: {str(e)}")
            return []
    
    def generate_organization_baseline(self, org_id: int, days: int = 90) -> Dict:
        """生成组织健康基线"""
        try:
            data = {
                'orgId': org_id,
                'days': days,
                'baselineType': 'organization',
                'includeSubOrgs': True
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['org_baseline']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 组织{org_id}基线生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 组织{org_id}基线生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 组织{org_id}基线生成异常: {str(e)}")
            raise
    
    def generate_organization_score(self, org_id: int, days: int = 30) -> Dict:
        """生成组织健康评分"""
        try:
            data = {
                'orgId': org_id,
                'days': days,
                'includeWeights': True,
                'includeUserScores': True
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['org_score']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 组织{org_id}评分生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 组织{org_id}评分生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 组织{org_id}评分生成异常: {str(e)}")
            raise
    
    def generate_organization_prediction(self, org_id: int, prediction_days: int = 30) -> Dict:
        """生成组织健康预测"""
        try:
            data = {
                'orgId': org_id,
                'predictionDays': prediction_days,
                'includeTrends': True,
                'includeRiskAssessment': True,
                'includeUserPredictions': False  # 组织级预测不包含个人详情
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['org_prediction']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 组织{org_id}预测生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 组织{org_id}预测生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 组织{org_id}预测生成异常: {str(e)}")
            raise
    
    def generate_organization_recommendation(self, org_id: int) -> Dict:
        """生成组织健康建议"""
        try:
            data = {
                'orgId': org_id,
                'includeManagement': True,    # 包含管理建议
                'includePolicy': True,        # 包含政策建议
                'includeTraining': True       # 包含培训建议
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['org_recommendation']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 组织{org_id}建议生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 组织{org_id}建议生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 组织{org_id}建议生成异常: {str(e)}")
            raise
    
    def generate_organization_profile(self, org_id: int, days: int = 180) -> Dict:
        """生成组织健康画像"""
        try:
            data = {
                'orgId': org_id,
                'days': days,
                'includeRiskProfile': True,      # 包含风险画像
                'includeHealthTrends': True,     # 包含健康趋势
                'includeComplianceProfile': True, # 包含合规画像
                'includeBenchmark': True         # 包含基准对比
            }
            
            response = self.session.post(f"{self.base_url}{self.endpoints['org_profile']}/generate", json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 200:
                self.logger.debug(f"✅ 组织{org_id}画像生成成功")
                return result.get('data', {})
            else:
                error_msg = result.get('msg', 'Unknown error')
                self.logger.error(f"❌ 组织{org_id}画像生成失败: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ 组织{org_id}画像生成异常: {str(e)}")
            raise
    
    def process_single_organization(self, org: Dict, config: Dict) -> DepartmentHealthResult:
        """处理单个组织的健康数据"""
        org_id = org['id']
        org_name = org.get('name', f'Organization-{org_id}')
        result = DepartmentHealthResult(org_id=org_id, org_name=org_name)
        
        self.logger.info(f"🔄 开始处理组织{org_id}: {org_name}")
        
        # 获取组织用户数量
        users = self.get_organization_users(org_id)
        result.user_count = len(users)
        
        if result.user_count < 2:
            result.errors.append("组织用户数量不足，跳过处理")
            self.logger.warning(f"⚠️ 组织{org_id}用户数量不足({result.user_count})，跳过处理")
            return result
        
        # 1. 生成组织健康基线
        if config.get('generate_baseline', True):
            try:
                result.baseline_data = self.generate_organization_baseline(
                    org_id, config.get('baseline_days', 90))
                result.baseline_success = True
            except Exception as e:
                result.errors.append(f"基线生成失败: {str(e)}")
        
        # 2. 生成组织健康评分
        if config.get('generate_score', True):
            try:
                result.score_data = self.generate_organization_score(
                    org_id, config.get('score_days', 30))
                result.score_success = True
            except Exception as e:
                result.errors.append(f"评分生成失败: {str(e)}")
        
        # 3. 生成组织健康预测
        if config.get('generate_prediction', True):
            try:
                result.prediction_data = self.generate_organization_prediction(
                    org_id, config.get('prediction_days', 30))
                result.prediction_success = True
            except Exception as e:
                result.errors.append(f"预测生成失败: {str(e)}")
        
        # 4. 生成组织健康建议
        if config.get('generate_recommendation', True):
            try:
                result.recommendation_data = self.generate_organization_recommendation(org_id)
                result.recommendation_success = True
            except Exception as e:
                result.errors.append(f"建议生成失败: {str(e)}")
        
        # 5. 生成组织健康画像
        if config.get('generate_profile', True):
            try:
                result.profile_data = self.generate_organization_profile(
                    org_id, config.get('profile_days', 180))
                result.profile_success = True
            except Exception as e:
                result.errors.append(f"画像生成失败: {str(e)}")
        
        success_count = sum([
            result.baseline_success, result.score_success, 
            result.prediction_success, result.recommendation_success, result.profile_success
        ])
        
        if result.errors:
            self.logger.warning(f"⚠️ 组织{org_id}({org_name})处理完成，成功{success_count}项，失败{len(result.errors)}项")
            for error in result.errors:
                self.logger.warning(f"  - {error}")
        else:
            self.logger.info(f"✅ 组织{org_id}({org_name})处理完成，成功{success_count}项，用户数{result.user_count}")
        
        return result
    
    def process_all_organizations(self, config: Dict = None) -> List[DepartmentHealthResult]:
        """批量处理所有组织的健康数据"""
        if config is None:
            config = {
                'generate_baseline': True,
                'generate_score': True, 
                'generate_prediction': True,
                'generate_recommendation': True,
                'generate_profile': True,
                'baseline_days': 90,      # 组织基线需要更长时间
                'score_days': 30,
                'prediction_days': 30,
                'profile_days': 180,      # 组织画像需要更长时间
                'max_workers': 3,         # 组织处理并发数相对较少
                'org_days': 30
            }
        
        self.logger.info("🚀 开始批量处理部门健康数据")
        start_time = time.time()
        
        # 获取活跃组织
        organizations = self.get_active_organizations(config.get('org_days', 30))
        if not organizations:
            self.logger.warning("⚠️ 没有找到活跃组织")
            return []
        
        results = []
        max_workers = config.get('max_workers', 3)
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_org = {
                executor.submit(self.process_single_organization, org, config): org 
                for org in organizations
            }
            
            # 收集结果
            for future in as_completed(future_to_org):
                org = future_to_org[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"❌ 组织{org['id']}处理异常: {str(e)}")
                    error_result = DepartmentHealthResult(
                        org_id=org['id'],
                        org_name=org.get('name', f'Organization-{org["id"]}'),
                        errors=[f"处理异常: {str(e)}"]
                    )
                    results.append(error_result)
        
        # 统计结果
        total_orgs = len(results)
        total_users = sum(r.user_count for r in results)
        success_stats = {
            'baseline': sum(1 for r in results if r.baseline_success),
            'score': sum(1 for r in results if r.score_success),
            'prediction': sum(1 for r in results if r.prediction_success),
            'recommendation': sum(1 for r in results if r.recommendation_success),
            'profile': sum(1 for r in results if r.profile_success)
        }
        
        error_count = sum(1 for r in results if r.errors)
        elapsed_time = time.time() - start_time
        
        self.logger.info("🎉 部门健康数据批量处理完成!")
        self.logger.info(f"📊 处理统计:")
        self.logger.info(f"  - 总组织数: {total_orgs}")
        self.logger.info(f"  - 总用户数: {total_users}")
        self.logger.info(f"  - 基线生成成功: {success_stats['baseline']}")
        self.logger.info(f"  - 评分生成成功: {success_stats['score']}")
        self.logger.info(f"  - 预测生成成功: {success_stats['prediction']}")
        self.logger.info(f"  - 建议生成成功: {success_stats['recommendation']}")
        self.logger.info(f"  - 画像生成成功: {success_stats['profile']}")
        self.logger.info(f"  - 有错误的组织: {error_count}")
        self.logger.info(f"  - 总耗时: {elapsed_time:.2f}秒")
        
        return results
    
    def save_results(self, results: List[DepartmentHealthResult], output_file: str = None):
        """保存处理结果到文件"""
        if output_file is None:
            output_file = f'department_health_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # 将结果转换为可序列化的格式
        serializable_results = []
        for result in results:
            serializable_results.append({
                'org_id': result.org_id,
                'org_name': result.org_name,
                'user_count': result.user_count,
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
        'baseline_days': 90,      # 组织基线需要更长的时间窗口
        'score_days': 30,
        'prediction_days': 30,
        'profile_days': 180,      # 组织画像需要更长的时间窗口
        'org_days': 30,           # 获取最近30天活跃的组织
        'max_workers': 3          # 并发线程数(组织处理相对较重)
    }
    
    # 创建处理器
    processor = DepartmentHealthProcessor(
        base_url=config['base_url'],
        token=config['token']
    )
    
    # 执行批量处理
    results = processor.process_all_organizations(config)
    
    # 保存结果
    if results:
        output_file = processor.save_results(results)
        print(f"\n🎉 部门健康数据处理完成!")
        print(f"📁 结果文件: {output_file}")
    else:
        print("\n⚠️ 没有处理任何组织数据")

if __name__ == "__main__":
    main()