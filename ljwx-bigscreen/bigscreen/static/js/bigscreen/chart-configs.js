/**
 * 智能健康数据分析平台 - 图表配置
 */

// 健康评分雷达图配置
function getHealthScoreChartConfig(factors, overallScore = 0) {
  return {
    tooltip: {
      trigger: 'axis',
      formatter: function(params) {
        return params[0].name + '<br/>' +
               params[0].marker + params[0].seriesName + '：' + params[0].value;
      }
    },
    radar: {
      radius: '65%',
      center: ['50%', '55%'],
      indicator: [
        { name: `心率 ${getFactorScore(factors, 'heartRate', 'heart_rate')}分`, max: 100 },
        { name: `血氧 ${getFactorScore(factors, 'bloodOxygen', 'blood_oxygen')}分`, max: 100 },
        { name: `体温 ${getFactorScore(factors, 'temperature', 'temperature')}分`, max: 100 },
        { name: `步数 ${getFactorScore(factors, 'step', 'step')}分`, max: 100 },
        { name: `卡路里 ${getFactorScore(factors, 'calorie', 'calorie')}分`, max: 100 },
        { name: `收缩压 ${getFactorScore(factors, 'pressureHigh', 'pressure_high')}分`, max: 100 },
        { name: `舒张压 ${getFactorScore(factors, 'pressureLow', 'pressure_low')}分`, max: 100 },
        { name: `压力 ${getFactorScore(factors, 'stress', 'stress')}分`, max: 100 }
      ],
      name: {
        textStyle: {
          color: '#00e4ff',
          fontSize: 12,
          padding: [3, 5]
        },
        rich: {
          value: {
            color: '#00e4ff',
            fontSize: 12,
            fontWeight: 'normal'
          }
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(0,228,255,0.1)', 'rgba(0,228,255,0.2)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0,228,255,0.5)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0,228,255,0.3)'
        }
      }
    },
    series: [{
      name: '健康指标',
      type: 'radar',
      data: [{
        value: [
          getFactorScore(factors, 'heartRate', 'heart_rate'),
          getFactorScore(factors, 'bloodOxygen', 'blood_oxygen'),
          getFactorScore(factors, 'temperature', 'temperature'),
          getFactorScore(factors, 'step', 'step'),
          getFactorScore(factors, 'calorie', 'calorie'),
          getFactorScore(factors, 'pressureHigh', 'pressure_high'),
          getFactorScore(factors, 'pressureLow', 'pressure_low'),
          getFactorScore(factors, 'stress', 'stress')
        ],
        name: '当前状态',
        itemStyle: {
          color: '#00e4ff'
        },
        areaStyle: {
          color: 'rgba(0,228,255,0.4)'
        }
      }]
    }]
  };
}

// 设备状态分布饼图配置
function getDeviceStatusChartConfig(statusData) {
  return {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    series: [{
      name: '设备状态',
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['50%', '60%'],
      data: statusData || [
        { value: 0, name: '在线', itemStyle: { color: '#00ff9d' } },
        { value: 0, name: '离线', itemStyle: { color: '#ffbb00' } },
        { value: 0, name: '故障', itemStyle: { color: '#ff6666' } }
      ],
      label: {
        show: true,
        position: 'outside',
        color: '#fff',
        fontSize: 10
      },
      labelLine: {
        show: true,
        lineStyle: {
          color: '#00e4ff'
        }
      }
    }]
  };
} 