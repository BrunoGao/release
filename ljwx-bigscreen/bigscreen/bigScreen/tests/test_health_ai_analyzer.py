import pytest
import numpy as np
from datetime import datetime, timedelta
from ..health_ai_analyzer import DeepseekHealthAnalyzer, HealthDapingAnalyzer, analyze_health_trends

def generate_test_data(days=5, interval_hours=6):
    data = []
    base_time = datetime.now() - timedelta(days=days)
    
    for day in range(days):
        for hour in range(0, 24, interval_hours):
            timestamp = base_time + timedelta(days=day, hours=hour)
            data.append({
                "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "heartRate": "75",
                "bloodOxygen": "98",
                "temperature": "36.5",
                "pressureHigh": "120",
                "pressureLow": "80",
                "stress": "50",
                "step": "8000",
                "calorie": "300",
                "sleep": "8"
            })
    return data

def test_deepseek_analyzer_initialization():
    test_data = generate_test_data()
    analyzer = DeepseekHealthAnalyzer(test_data)
    assert analyzer.health_data_list == sorted(
        test_data,
        key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    )

def test_daping_analyzer_initialization():
    test_data = generate_test_data()
    analyzer = HealthDapingAnalyzer(test_data)
    assert analyzer.health_data_list == sorted(
        test_data,
        key=lambda x: datetime.strptime(x.get('timestamp', '1970-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    )

def test_analyze_time_series():
    test_data = generate_test_data()
    analyzer = HealthDapingAnalyzer(test_data)
    time_series = analyzer.analyze_time_series()
    
    assert time_series is not None
    assert 'timestamps' in time_series
    assert 'metrics' in time_series
    assert 'anomalies' in time_series
    assert 'trends' in time_series
    
    # Check if all metrics are present
    expected_metrics = ['heartRate', 'bloodOxygen', 'temperature', 'pressureHigh', 
                       'pressureLow', 'stress', 'step', 'calorie']
    for metric in expected_metrics:
        assert metric in time_series['metrics']
        assert len(time_series['metrics'][metric]) == len(test_data)

def test_calculate_health_scores():
    test_data = generate_test_data()
    analyzer = HealthDapingAnalyzer(test_data)
    scores = analyzer.calculate_health_scores()
    
    assert scores is not None
    assert 'overall' in scores
    assert 'factors' in scores
    assert 'details' in scores
    
    # Check overall score range
    assert 0 <= scores['overall'] <= 100
    
    # Check individual metrics
    for metric in analyzer.metrics:
        assert metric in scores['factors']
        factor = scores['factors'][metric]
        assert 0 <= factor['score'] <= 100
        assert factor['weight'] > 0
        assert factor['status'] in ['excellent', 'good', 'normal', 'warning', 'danger']

def test_analyze_health_trends():
    test_data = generate_test_data()
    result = analyze_health_trends(test_data)
    
    assert result['success'] is True
    assert 'data' in result
    
    data = result['data']
    assert 'summary' in data
    assert 'healthScores' in data
    assert 'timeSeriesData' in data
    
    summary = data['summary']
    assert summary['totalRecords'] == len(test_data)
    assert 'timeRange' in summary
    assert 'overallScore' in summary
    assert 'status' in summary

def test_empty_data_handling():
    with pytest.raises(ValueError):
        HealthDapingAnalyzer([])
    
    result = analyze_health_trends([])
    assert result['success'] is False
    assert 'error' in result

def test_invalid_data_handling():
    invalid_data = [{'timestamp': 'invalid', 'heartRate': 'abc'}]
    analyzer = HealthDapingAnalyzer([{
        'timestamp': '2024-03-20 10:00:00',
        'heartRate': '75'
    }])
    
    # Test safe float conversion
    assert analyzer._safe_float('abc') == 0.0
    assert analyzer._safe_float(None) == 0.0
    assert analyzer._safe_float('') == 0.0
    
    # Test trend calculation with invalid data
    trend = analyzer._calculate_trend([0.0])
    assert trend['direction'] == '未知'
    assert trend['significance'] == 'low'

def test_trend_analysis():
    # Test increasing trend
    increasing_data = generate_test_data()
    for i, data in enumerate(increasing_data):
        data['heartRate'] = str(75 + i)
    
    analyzer = HealthDapingAnalyzer(increasing_data)
    time_series = analyzer.analyze_time_series()
    assert time_series['trends']['heartRate']['direction'] == '上升'
    
    # Test decreasing trend
    decreasing_data = generate_test_data()
    for i, data in enumerate(decreasing_data):
        data['heartRate'] = str(75 - i)
    
    analyzer = HealthDapingAnalyzer(decreasing_data)
    time_series = analyzer.analyze_time_series()
    assert time_series['trends']['heartRate']['direction'] == '下降'
    
    # Test stable trend
    stable_data = generate_test_data()
    analyzer = HealthDapingAnalyzer(stable_data)
    time_series = analyzer.analyze_time_series()
    assert time_series['trends']['heartRate']['direction'] == '稳定'