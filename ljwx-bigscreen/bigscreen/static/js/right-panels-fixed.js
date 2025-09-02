// 健康评分雷达图兼容性修复
function initHealthScoreChart() {
    const alertTypeMap = {
        blood_pressure: '血压',
        stress: '压力',
        blood_oxygen: '血氧',
        temperature: '体温',
        one_key_alarm: '一键报警',
        fall_down: '跌倒',
        sleep: '睡眠'
    };

    // 检查并初始化健康评分图表
    const healthScoreContainer = document.getElementById('healthScoreChart');
    if (healthScoreContainer) {
        const charts = { healthScore: echarts.init(healthScoreContainer) };
        
        // 从URL获取customerId参数
        const urlParams = new URLSearchParams(window.location.search);
        const customerId = urlParams.get('customerId') || '1';
        
        // 获取日期范围
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 7);
        
        function formatDate(date) {
            return date.toISOString().split('T')[0];
        }
        
        const startDate = formatDate(yesterday);
        const endDate = formatDate(today);
        
        // 兼容驼峰和下划线命名的辅助函数
        function getFactorScore(factors, camelCase, snakeCase) {
            return factors[camelCase]?.score || factors[snakeCase]?.score || 0;
        }
        
        // 调用接口获取健康评分数据
        fetch(`/health_data/score?orgId=${customerId}&startDate=${startDate}&endDate=${endDate}`)
            .then(response => response.json())
            .then(result => {
                if (result.success && result.data && result.data.healthScores) {
                    const factors = result.data.healthScores.factors;
                    
                    // 更新总分显示
                    const totalScoreElement = document.querySelector('.total-score');
                    if (totalScoreElement) {
                        totalScoreElement.textContent = `总分：${result.data.summary.overallScore}`;
                    }
                    
                    const healthScoreOption = {
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
                    charts.healthScore.setOption(healthScoreOption);
                } else {
                    // 显示默认0分图表
                    const healthScoreOption = {
                        radar: {
                            radius: '65%',
                            center: ['50%', '55%'],
                            indicator: [
                                { name: '心率 0分', max: 100 },
                                { name: '血氧 0分', max: 100 },
                                { name: '体温 0分', max: 100 },
                                { name: '步数 0分', max: 100 },
                                { name: '卡路里 0分', max: 100 },
                                { name: '收缩压 0分', max: 100 },
                                { name: '舒张压 0分', max: 100 },
                                { name: '压力 0分', max: 100 }
                            ]
                        },
                        series: [{
                            name: '健康指标',
                            type: 'radar',
                            data: [{
                                value: [0, 0, 0, 0, 0, 0, 0, 0],
                                name: '当前状态'
                            }]
                        }]
                    };
                    charts.healthScore.setOption(healthScoreOption);
                }
            })
            .catch(error => {
                console.error('Error fetching health data:', error);
            });
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initHealthScoreChart); 