import sys
import os
import pytest
from datetime import datetime, timedelta
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from health_ai_analyzer import DeepseekHealthAnalyzer, analyze_health_trends

def generate_test_data():
    """生成测试数据"""
    base_time = datetime.now()
    test_data = []
    
    for i in range(24):  # 生成24小时的数据
        timestamp = (base_time - timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        data_point = {
            "timestamp": timestamp,
            "heartRate": "75",
            "bloodOxygen": "98",
            "temperature": "36.5",
            "pressureHigh": "120",
            "pressureLow": "80",
            "stress": "45",
            "step": "8000",
            "calorie": "400"
        }
        test_data.append(data_point)
    
    return test_data

def test_deepseek_analyzer():
    """测试 DeepseekHealthAnalyzer"""
    try:
        # 准备测试数据
        test_data = generate_test_data()
        
        # 创建分析器实例
        analyzer = DeepseekHealthAnalyzer(test_data)
        
        # 测试时间序列分析
        print("\n开始测试时间序列分析...")
        time_series = analyzer.analyze_time_series()
        assert time_series is not None, "时间序列分析返回为空"
        print("时间序列分析结果:", json.dumps(time_series, ensure_ascii=False, indent=2))
        
        # 测试健康评分计算
        print("\n开始测试健康评分计算...")
        scores = analyzer.calculate_health_scores()
        assert scores is not None, "健康评分计算返回为空"
        print("健康评分计算结果:", json.dumps(scores, ensure_ascii=False, indent=2))
        
        # 测试完整分析流程
        print("\n开始测试完整分析流程...")
        result = analyze_health_trends(test_data)
        assert result['success'] is True, "完整分析流程失败"
        print("完整分析流程结果:", json.dumps(result, ensure_ascii=False, indent=2))
        
        print("\n所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        return False

def test_fallback_mechanism():
    """测试后备机制"""
    try:
        # 准备测试数据
        test_data = generate_test_data()
        analyzer = DeepseekHealthAnalyzer(test_data)
        
        # 测试后备时间序列分析
        print("\n开始测试后备时间序列分析...")
        time_series = analyzer._fallback_time_series_analysis()
        assert time_series is not None, "后备时间序列分析返回为空"
        print("后备时间序列分析结果:", json.dumps(time_series, ensure_ascii=False, indent=2))
        
        # 测试后备健康评分计算
        print("\n开始测试后备健康评分计算...")
        scores = analyzer._fallback_health_scores()
        assert scores is not None, "后备健康评分计算返回为空"
        print("后备健康评分计算结果:", json.dumps(scores, ensure_ascii=False, indent=2))
        
        print("\n后备机制测试通过！")
        return True
        
    except Exception as e:
        print(f"\n后备机制测试过程中出现错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("开始执行测试...")
    test_deepseek_analyzer()
    test_fallback_mechanism()