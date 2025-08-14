const ALERT_TYPE_MAP = {
        heart_rate: '心率',
      const ALERT_SEVERITY_MAP = {
        critical: '严重',
        high: '高',
        medium: '中',
        low: '低'
      };
      const ALERT_STATUS_MAP = {
        pending: '待处理',
        responded: '已响应',
        resolved: '已解决'
      };
      function translateAlertType(type) {
        return ALERT_TYPE_MAP[type] || type;
      }
      function translateAlertSeverity(severity) {
        return ALERT_SEVERITY_MAP[severity] || severity;
      }
      function translateAlertStatus(status) {
        return ALERT_STATUS_MAP[status] || status;
      }
      const ALERT_TYPE_COLOR = {
        heart_rate: '#ff6b6b',
        blood_pressure: '#ffb347',
        stress: '#f7b731',
        blood_oxygen: '#00e4ff',
        temperature: '#ffd700',
        one_key_alarm: '#ffe066',
        fall_down: '#00cfff',
        sleep: '#7ecfff'
      };
      const ALERT_SEVERITY_COLOR = {    
        critical: '#ff6b6b',
        high: '#ffb347',
        medium: '#f7b731',
        low: '#00e4ff'
      };
      const ALERT_STATUS_COLOR = {
        pending: '#ff6b6b',
        responded: '#ffb347',
        resolved: '#00e4ff'
      };
      function getAlertTypeColor(type) {
        return ALERT_TYPE_COLOR[type] || '#7ecfff';
      }
      function getAlertSeverityColor(severity) {
        return ALERT_SEVERITY_COLOR[severity] || '#7ecfff';
      }
      function getAlertStatusColor(status) {
        return ALERT_STATUS_COLOR[status] || '#7ecfff';
      }

      // 添加日期格式化函数
      function formatDate(date) {
          const year = date.getFullYear();
          const month = String(date.getMonth() + 1).padStart(2, '0');
          const day = String(date.getDate()).padStart(2, '0');
          return `${year}-${month}-${day}`;
      }

      // 修改initCharts函数
      function initCharts() {
                const startDate = formatDate(yesterday);
                const endDate = formatDate(today);
                
      const startDate = formatDate(yesterday);
      const endDate = formatDate(today);
      
      fetch(`/health_data/score?orgId=${customerId}&startDate=${startDate}&endDate=${endDate}`)
          .then(response => response.json())
          .then(result => {
              if (result.success && result.data && result.data.healthScores) {
                  const factors = result.data.healthScores.factors;
                  console.log('factors',factors);
                  
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
                              { name: `心率 ${factors.heartRate?.score || 0}分`, max: 100 },
                              { name: `血氧 ${factors.bloodOxygen?.score || 0}分`, max: 100 },
                              { name: `体温 ${factors.temperature?.score || 0}分`, max: 100 },
                              { name: `步数 ${factors.step?.score || 0}分`, max: 100 },
                              { name: `卡路里 ${factors.calorie?.score || 0}分`, max: 100 },
                              { name: `收缩压 ${factors.pressureHigh?.score || 0}分`, max: 100 },
                              { name: `舒张压 ${factors.pressureLow?.score || 0}分`, max: 100 },
                              { name: `压力 ${factors.stress?.score || 0}分`, max: 100 }
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
                                  factors.heartRate?.score || 0,
                                  factors.bloodOxygen?.score || 0,
                                  factors.temperature?.score || 0,
                                  factors.step?.score || 0,
                                  factors.calorie?.score || 0,
                                  factors.pressureHigh?.score || 0,
                                  factors.pressureLow?.score || 0,
                                  factors.stress?.score || 0
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
                  globalCharts.healthScore.setOption(healthScoreOption);
              } else {
                  // 如果没有数据，显示0分
                  const totalScoreElement = document.querySelector('.total-score');
                  if (totalScoreElement) {
                      totalScoreElement.textContent = '总分：0';
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
                              { name: '心率 0分', max: 100 },
                              { name: '血氧 0分', max: 100 },
                              { name: '体温 0分', max: 100 },
                              { name: '步数 0分', max: 100 },
                              { name: '卡路里 0分', max: 100 },
                              { name: '收缩压 0分', max: 100 },
                              { name: '舒张压 0分', max: 100 },
                              { name: '压力 0分', max: 100 }
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
                              value: [0, 0, 0, 0, 0, 0, 0, 0],
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
                  globalCharts.healthScore.setOption(healthScoreOption);
              }
          })
          .catch(error => {
              console.error('Error fetching health data:', error);
              // 发生错误时也显示0分
              const totalScoreElement = document.querySelector('.total-score');
              if (totalScoreElement) {
                  totalScoreElement.textContent = '总分：0';
              }
              // 设置默认的0分图表
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
                          { name: '心率 0分', max: 100 },
                          { name: '血氧 0分', max: 100 },
                          { name: '体温 0分', max: 100 },
                          { name: '步数 0分', max: 100 },
                          { name: '卡路里 0分', max: 100 },
                          { name: '收缩压 0分', max: 100 },
                          { name: '舒张压 0分', max: 100 },
                          { name: '压力 0分', max: 100 }
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
                          value: [0, 0, 0, 0, 0, 0, 0, 0],
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
              globalCharts.healthScore.setOption(healthScoreOption);
          });
  }
  }
  
  function loadBaselineTrendChart(orgId) {
    console.log('loadBaselineTrendChart 开始执行，orgId:', orgId);
    
    const endDate = getPastDateStr(0), startDate = getPastDateStr(6);
    
    fetch(`/health_data/chart/baseline?orgId=${orgId}&startDate=${startDate}&endDate=${endDate}`)
      .then(r=>r.json())
      .then(result=>{
        console.log('健康数据接口返回:', result);
        
        // 检查是否有数据，如果没有数据则生成baseline
        if (!result || !result.dates || result.dates.length === 0) {
          console.warn('baseline数据缺失，开始生成baseline');
          return generateBaselineAndRetry(orgId, startDate, endDate);
        }
        
        renderHealthChart(result);
      })
      .catch(error => {
        console.error('健康数据加载失败:', error);
        // 尝试生成baseline后重试
        generateBaselineAndRetry(orgId, startDate, endDate);
      });
  }

  // 生成baseline并重试获取数据
  function generateBaselineAndRetry(orgId, startDate, endDate) {
    console.log('正在生成baseline数据...');
    
    fetch('/api/baseline/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_date: endDate })
    })
    .then(r => r.json())
    .then(generateResult => {
      console.log('baseline生成结果:', generateResult);
      
      if (generateResult.success) {
        // 生成成功后重新获取数据
        return fetch(`/health_data/chart/baseline?orgId=${orgId}&startDate=${startDate}&endDate=${endDate}`);
      } else {
        throw new Error('baseline生成失败: ' + generateResult.error);
      }
    })
    .then(r => r.json())
    .then(result => {
      console.log('重新获取的健康数据:', result);
      renderHealthChart(result);
    })
    .catch(error => {
      console.error('生成baseline或重新获取数据失败:', error);
      showDefaultHealthData();
    });
  }

  // 渲染健康图表
  function renderHealthChart(result) {
    const {dates, metrics, health_summary} = result;
    
    // 更新健康统计数据
    if (health_summary) {
      document.getElementById('healthScore').textContent = health_summary.overall_score || 0;
      document.getElementById('normalCount').textContent = health_summary.normal_indicators || 0;
      document.getElementById('riskCount').textContent = health_summary.risk_indicators || 0;
    }
    
    // 健康趋势图
    const trendChart = echarts.init(document.getElementById('trendChart'));
    
    // 核心健康指标
    const mainMetrics = ['心率', '血氧', '体温', '压力', '睡眠'];
    const metricColors = {
      '心率': '#ff6b6b',
      '血氧': '#00ff9d', 
      '体温': '#ffbb00',
      '压力': '#ff9500',
      '睡眠': '#7ecfff'
    };
    const series = [];
    
    if (metrics && metrics.length > 0) {
      mainMetrics.forEach(metricName => {
        const metric = metrics.find(m => m.name === metricName);
        if (metric && metric.values) {
          series.push({
            name: metric.name,
            type: 'line',
            data: metric.values,
            smooth: true,
            symbol: 'circle',
            symbolSize: 4,
            lineStyle: { 
              width: 2, 
              color: metricColors[metric.name] || '#00e4ff'
            },
            itemStyle: { 
              color: metricColors[metric.name] || '#00e4ff'
            }
          });
        }
      });
    }
    
    const trendOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10,24,48,0.98)',
        borderColor: '#00e4ff',
        borderWidth: 1,
        textStyle: { color: '#fff', fontSize: 10 },
        formatter: function(params) {
          let result = params[0].axisValue + '<br/>';
          params.forEach(param => {
            const unit = getMetricUnit(param.seriesName);
            result += `${param.seriesName}: ${param.value}${unit}<br/>`;
          });
          return result;
        }
      },
      legend: {
        show: true,
        top: 5,
        textStyle: { color: '#fff', fontSize: 10 }
      },
      grid: { 
        top: 35, 
        left: 30, 
        right: 20, 
        bottom: 25, 
        containLabel: true 
      },
      xAxis: {
        type: 'category',
        data: dates,
        axisLabel: { 
          color: '#7ecfff', 
          fontSize: 9
        },
        axisLine: { lineStyle: { color: 'rgba(0,228,255,0.2)' } }
      },
      yAxis: {
        type: 'value',
        axisLabel: { 
          color: '#7ecfff', 
          fontSize: 10
        },
        splitLine: { 
          lineStyle: { 
            color: 'rgba(0,228,255,0.1)', 
            type: 'dashed' 
          } 
        }
      },
      series
    };
    
    trendChart.setOption(trendOption);
    
    // 图表点击事件
    trendChart.on('click', function(params) {
      console.log('点击了健康趋势图:', params);
    });
    
    // 自适应大小
    window.addEventListener('resize', () => {
      trendChart.resize();
    });
  }

  // 获取指标单位
  function getMetricUnit(metricName) {
    const units = {
      '心率': 'bpm',
      '血氧': '%',
      '体温': '°C',
      '压力': '',
      '睡眠': 'h'
    };
    return units[metricName] || '';
  }

// 显示默认健康数据 - 增强版
function showDefaultHealthData() {
    // 更新统计数据
    document.getElementById('healthScore').textContent = '85';
    document.getElementById('normalCount').textContent = '6';
    document.getElementById('riskCount').textContent = '2';
    
    // 显示默认趋势图 - 7天数据，5个指标
    const trendChart = echarts.init(document.getElementById('trendChart'));
    
    // 生成最近7天的日期
    const defaultDates = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        defaultDates.push((date.getMonth() + 1).toString().padStart(2, '0') + '-' + date.getDate().toString().padStart(2, '0'));
    }
    
    const defaultOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10,24,48,0.98)',
        borderColor: '#00e4ff',
        borderWidth: 1,
        textStyle: { color: '#fff', fontSize: 10 },
        formatter: function(params) {
          let result = params[0].name + '<br/>';
          params.forEach(param => {
            result += param.marker + param.seriesName + ': ' + param.value;
            if (param.seriesName === '体温') result += '°C';
            else if (param.seriesName === '血氧') result += '%';
            else if (param.seriesName === '心率') result += 'bpm';
            else if (param.seriesName === '睡眠') result += 'h';
            result += '<br/>';
          });
          return result;
        }
      },
      legend: {
        show: true,
        top: 5,
        textStyle: { color: '#fff', fontSize: 10 },
        itemWidth: 12,
        itemHeight: 8
      },
      grid: { 
        top: 35, 
        left: 35, 
        right: 20, 
        bottom: 25, 
        containLabel: true 
      },
      xAxis: {
        type: 'category',
        data: defaultDates,
        axisLabel: { color: '#7ecfff', fontSize: 9 },
        axisLine: { lineStyle: { color: 'rgba(0,228,255,0.2)' } }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#7ecfff', fontSize: 10 },
        splitLine: { 
          lineStyle: { 
            color: 'rgba(0,228,255,0.1)', 
            type: 'dashed' 
          } 
        }
      },
      series: [
        {
          name: '心率',
          type: 'line',
          data: [72, 75, 78, 74, 76, 73, 77],
          smooth: true,
          lineStyle: { color: '#ff6b6b', width: 2 },
          itemStyle: { color: '#ff6b6b' },
          symbolSize: 4
        },
        {
          name: '血氧',
          type: 'line',
          data: [98, 97, 99, 98, 97, 98, 99],
          smooth: true,
          lineStyle: { color: '#00ff9d', width: 2 },
          itemStyle: { color: '#00ff9d' },
          symbolSize: 4
        },
        {
          name: '体温',
          type: 'line',
          data: [36.5, 36.7, 36.4, 36.6, 36.8, 36.5, 36.6],
          smooth: true,
          lineStyle: { color: '#ffbb00', width: 2 },
          itemStyle: { color: '#ffbb00' },
          symbolSize: 4
        },
        {
          name: '压力',
          type: 'line',
          data: [45, 52, 38, 48, 55, 42, 47],
          smooth: true,
          lineStyle: { color: '#ff9500', width: 2 },
          itemStyle: { color: '#ff9500' },
          symbolSize: 4
        },
        {
          name: '睡眠',
          type: 'line',
          data: [7.5, 8.2, 6.8, 7.8, 8.0, 7.2, 7.6],
          smooth: true,
          lineStyle: { color: '#7ecfff', width: 2 },
          itemStyle: { color: '#7ecfff' },
          symbolSize: 4
        }
      ]
    };
    
    trendChart.setOption(defaultOption);
    
    // 自适应大小
    window.addEventListener('resize', () => {
      trendChart.resize();
    });
}


// 修改数据刷新函数
function refreshData() {
    // 从 URL 获取 customerId 参数
    const urlParams = new URLSearchParams(window.location.search);
    console.log('urlParams', urlParams.get('customerId'));
    const customerId = urlParams.get('customerId') || '1';
    loadBaselineTrendChart(customerId);
    loadHealthScoreChart(customerId);
    loadStatisticsData();
    //loadMessages(); // 加载消息数据

    fetch(`/get_total_info?customer_id=${customerId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;
                console.log('Refreshing data:', data);

                lastTotalInfo = data;
                updateMapData(lastTotalInfo);

                // 刷新所有图表
                if (globalCharts) {
                const typeName = data.name === 'others' ? '其他类型' : translateAlertType(data.name);
                return `${typeName}<br/>告警: ${data.value}次 (${percent}%)`;
            }
        },
        grid: { 
            top: 25, 
            left: 50, 
            right: 15, 
            bottom: 15,
            containLabel: true
        },
        xAxis: {
            type: 'value',
            axisLabel: { color: '#7ecfff', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)' } },
            axisLine: { show: false },
            max: Math.max(...displayValues, 1)
        },
        yAxis: {
            type: 'category',
            data: displayTypes.map(t => t === 'others' ? '其他' : translateAlertType(t)),
            axisLabel: { 
                color: '#fff', 
                fontSize: 9,
                interval: 0, // 强制显示所有标签
                formatter: function(value) {
                    return value.length > 5 ? value.substring(0, 5) + '...' : value; /* 从4增加到5，允许显示更多字符 */
                }
            },
            axisLine: { show: false },
            axisTick: { show: false }
        },
        series: [{
            type: 'bar',
            data: displayTypes.map((type, index) => ({
                value: displayValues[index],
                itemStyle: { 
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        { offset: 0, color: typeColors[type] || '#00e4ff' },
                        { offset: 1, color: (typeColors[type] || '#00e4ff') + '88' }
                    ])
                }
            })),
            barWidth: displayTypes.length > 6 ? '40%' : displayTypes.length > 4 ? '50%' : '65%', // 动态调整条形宽度，适应更多类型
            label: { 
                show: true, 
                position: 'right', 
                color: '#fff', 
                fontSize: 9,
                formatter: '{c}'
            }
        }]
    };
    typeChart.setOption(typeOption);

    // 2. 告警级别分布图 - 环形图
    const levelChart = echarts.init(document.getElementById('alertLevelChart'));
    const levelEntries = Object.entries(alertInfo.alertLevelCount || {});
    const hasLevelData = levelEntries.length > 0 && levelEntries.some(([_, count]) => count > 0);
    
    const levelData = hasLevelData ? 
        levelEntries.map(([level, count]) => ({
            name: level === 'critical' ? '严重' : level === 'medium' ? '中等' : '轻微',
            value: count,
            itemStyle: { 
                color: level === 'critical' ? '#ff4444' : level === 'medium' ? '#ffbb00' : '#00e4ff'
            }
        })) :
        [
            { name: '严重', value: 0, itemStyle: { color: '#ff4444' } },
            { name: '中等', value: 0, itemStyle: { color: '#ffbb00' } },
            { name: '正常', value: 1, itemStyle: { color: '#00e4ff' } }
        ];

    const levelOption = {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(0,21,41,0.95)',
            borderColor: '#00e4ff',
            textStyle: { color: '#fff', fontSize: 11 },
            formatter: function(params) {
                return `${params.name}<br/>数量: ${params.value}次<br/>占比: ${params.percent}%`;
            }
        },
        series: [{
            type: 'pie',
            radius: ['35%', '65%'],
            center: ['50%', '55%'],
            data: levelData,
            label: {
                show: true,
                position: 'outside',
                color: '#fff',
                fontSize: 10,
                formatter: function(params) {
                    return hasLevelData ? `${params.name}\n${params.value}次` : `${params.name}`;
                },
                lineHeight: 12
            },
            labelLine: {
                show: true,
                length: 8,
                length2: 5,
                lineStyle: { color: 'rgba(255,255,255,0.5)' }
            },
            emphasis: {
                itemStyle: { 
                    shadowBlur: 15, 
                    shadowOffsetX: 0, 
                    shadowColor: 'rgba(0, 0, 0, 0.8)',
                    scale: 1.05
                }
            }
        }]
    };
    levelChart.setOption(levelOption);

    // 3. 告警状态分布图 - 仪表盘样式
    const statusChart = echarts.init(document.getElementById('alertStatusChart'));
    const totalAlerts = (alertInfo.alertStatusCount?.pending || 0) + (alertInfo.alertStatusCount?.responded || 0);
    const pendingPercent = totalAlerts > 0 ? ((alertInfo.alertStatusCount?.pending || 0) / totalAlerts * 100).toFixed(1) : 0;

    const statusOption = {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(0,21,41,0.95)',
            borderColor: '#00e4ff',
            textStyle: { color: '#fff', fontSize: 11 }
        },
        series: [{
            type: 'gauge',
            radius: '75%',
            center: ['50%', '55%'],
            startAngle: 180,
            endAngle: 0,
            min: 0,
            max: 100,
            splitNumber: 4,
            axisLine: {
                lineStyle: {
                    width: 8,
                    color: [
                        [0.3, '#00e4ff'],
                        [0.7, '#ffbb00'],
                        [1, '#ff4444']
                    ]
                }
            },
            pointer: {
                icon: 'circle',
                length: '60%',
                width: 4,
                offsetCenter: [0, '5%'],
                itemStyle: { color: '#fff' }
            },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: {
                show: true,
                distance: -25,
                color: '#7ecfff',
                fontSize: 9,
                formatter: function(value) {
                    if (value === 0) return '正常';
                    if (value === 50) return '中等';
                    if (value === 100) return '严重';
                    return '';
                }
            },
            detail: {
                valueAnimation: true,
                formatter: function(value) {
                    return `{value|${value}%}\n{name|待处理率}`;
                },
                rich: {
                    value: {
                        fontSize: 16,
                        fontWeight: 'bold',
                        color: pendingPercent > 70 ? '#ff4444' : pendingPercent > 30 ? '#ffbb00' : '#00e4ff'
                    },
                    name: {
                        fontSize: 10,
                        color: '#7ecfff',
                        padding: [5, 0, 0, 0]
                    }
                },
                offsetCenter: [0, '20%']
            },
            data: [{ value: pendingPercent }]
        }]
    };
    statusChart.setOption(statusOption);

    // 4. 24小时告警趋势图 - 修复数据处理
    const trendChart = echarts.init(document.getElementById('alertTrendChart'));
    
    // 处理时间数据，按小时统计
    const hourlyData = {};
    const now = new Date();
    
    // 初始化24小时数据
    for (let i = 0; i < 24; i++) {
        hourlyData[i] = 0;
    }
    
    // 统计告警数据
    if (alerts && alerts.length > 0) {
        alerts.forEach(alert => {
            try {
                let alertTime;
                if (alert.alert_timestamp) {
                    // 尝试解析时间戳
                    alertTime = new Date(alert.alert_timestamp);
                    if (isNaN(alertTime.getTime())) {
                        // 如果解析失败，尝试其他格式
                        alertTime = new Date(alert.alert_timestamp.replace(/-/g, '/'));
                    }
                } else if (alert.timestamp) {
                    alertTime = new Date(alert.timestamp);
                } else {
                    alertTime = now; // 默认当前时间
                }
                
                if (!isNaN(alertTime.getTime())) {
                    const hour = alertTime.getHours();
                    hourlyData[hour] = (hourlyData[hour] || 0) + 1;
                }
            } catch (e) {
                console.warn('解析告警时间失败:', alert, e);
            }
        });
    }
    
    const hours = Array.from({length: 24}, (_, i) => i);
    const hourlyValues = hours.map(h => hourlyData[h] || 0);
    const maxValue = Math.max(...hourlyValues, 1);

    const trendOption = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(0,21,41,0.95)',
            borderColor: '#00e4ff',
            textStyle: { color: '#fff', fontSize: 11 },
                formatter: function(params) {
                if (!params || !params[0]) return '';
                const data = params[0];
                return `${data.name}:00<br/>告警数量: ${data.value}次`;
            }
        },
        grid: { top: 25, left: 25, right: 15, bottom: 20 },
        xAxis: {
            type: 'category',
            data: hours.map(h => h.toString().padStart(2, '0')),
            axisLabel: { 
                color: '#7ecfff', 
                fontSize: 9,
                interval: 3
            },
            axisLine: { lineStyle: { color: 'rgba(126,207,255,0.3)' } },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            max: Math.max(maxValue + 1, 3),
            axisLabel: { color: '#7ecfff', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)', type: 'dashed' } },
            axisLine: { show: false }
        },
        series: [{
            type: 'line',
            data: hourlyValues,
            smooth: true,
            lineStyle: { 
                color: '#00e4ff', 
                width: 2,
                shadowColor: 'rgba(0,228,255,0.3)',
                shadowBlur: 5
            },
            itemStyle: { 
                color: '#00e4ff',
                borderColor: '#fff',
                borderWidth: 1
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                    { offset: 0, color: 'rgba(0,228,255,0.4)' },
                    { offset: 1, color: 'rgba(0,228,255,0.05)' }
                ])
            },
            symbol: 'circle',
            symbolSize: function(value) {
                return value > 0 ? 4 : 2;
            },
            emphasis: {
                itemStyle: {
                    color: '#fff', 
                    borderColor: '#00e4ff', 
                    borderWidth: 2,
                    shadowColor: 'rgba(0,228,255,0.6)',
                    shadowBlur: 8
                },
                scale: 1.2
            }
        }]
    };
    trendChart.setOption(trendOption);

    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.8; }
        }
        
        .alert-stat-item {
            display: flex;
            align-items: baseline;
            transition: all 0.3s ease;
        }
        
        .alert-stat-item:hover {
            transform: translateY(-2px);
        }
        
        #alertBadge {
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        #alertBadge:hover {
            transform: scale(1.1);
            box-shadow: 0 0 10px rgba(0,228,255,0.5);
        }
    `;
    document.head.appendChild(style);

    // 自适应大小 - 延迟执行确保DOM已渲染
    setTimeout(() => {
        const resizeCharts = () => {
            try {
                typeChart && typeChart.resize();
                levelChart && levelChart.resize();
                statusChart && statusChart.resize();
                trendChart && trendChart.resize();
            } catch (e) {
                console.warn('图表resize失败:', e);
            }
        };
        
        resizeCharts(); // 立即执行一次
        window.addEventListener('resize', resizeCharts);
    }, 100);

    // 添加点击事件显示详细告警列表
    badge.onclick = () => showAlertDetails(alerts);
    
    // 图表点击交互
    typeChart.on('click', function(params) {
        if (hasTypeData && params.dataIndex < alertTypes.length) {
            const alertType = alertTypes[params.dataIndex];
            const filteredAlerts = alerts.filter(alert => alert.alert_type === alertType);
            showAlertDetails(filteredAlerts, `${translateAlertType(alertType)}告警详情`);
        }
    });

    // 确保图表正确渲染 - 延迟执行
    setTimeout(() => {
        try {
            typeChart.resize();
            levelChart.resize();
            statusChart.resize();
            trendChart.resize();
            console.log('告警图表初始化完成');
        } catch (e) {
            console.warn('告警图表初始化失败:', e);
        }
    }, 200);

    return { typeChart, levelChart, statusChart, trendChart };
}

// 显示详细告警列表
function showAlertDetails(alerts, title = '📋 详细告警列表') {
    const modal = document.createElement('div');
    modal.className = 'modal-container';
    modal.innerHTML = `
        <div class="modal-content" style="width: 85%; height: 85%;">
            <button class="modal-close">✕</button>
            <h3 style="color: #00e4ff; margin-bottom: 20px; text-align: center; font-size: 18px;">${title}</h3>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding: 10px; background: rgba(0,228,255,0.1); border-radius: 6px;">
                <div style="color: #fff; font-size: 14px;">
                    共 <span style="color: #00e4ff; font-weight: bold;">${alerts.length}</span> 条告警记录
                </div>
                <div style="display: flex; gap: 10px;">
                    <button onclick="exportAlerts()" style="background: rgba(0,228,255,0.2); border: 1px solid #00e4ff; color: #00e4ff; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">📊 导出</button>
                    <button onclick="refreshAlerts()" style="background: rgba(0,228,255,0.2); border: 1px solid #00e4ff; color: #00e4ff; padding: 5px 12px; border-radius: 4px; cursor: pointer; font-size: 12px;">🔄 刷新</button>
                </div>
            </div>
            <div style="height: calc(100% - 100px); overflow-y: auto; border: 1px solid rgba(0,228,255,0.2); border-radius: 6px;">
                <table style="width: 100%; border-collapse: collapse; color: #fff; font-size: 13px;">
                    <thead style="position: sticky; top: 0; z-index: 10;">
                        <tr style="background: rgba(0,228,255,0.3); border-bottom: 2px solid #00e4ff;">
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">时间</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">类型</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">级别</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">状态</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">用户</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">部门</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold; border-right: 1px solid rgba(0,228,255,0.2);">设备</th>
                            <th style="padding: 12px 8px; text-align: left; font-weight: bold;">描述</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${alerts.map((alert, index) => `
                            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1); transition: all 0.2s ease; ${alert.severity_level === 'critical' ? 'background: rgba(255,68,68,0.15);' : index % 2 === 0 ? 'background: rgba(0,21,41,0.3);' : 'background: rgba(0,21,41,0.1);'}" 
                                onmouseover="this.style.background='rgba(0,228,255,0.1)'" 
                                onmouseout="this.style.background='${alert.severity_level === 'critical' ? 'rgba(255,68,68,0.15)' : index % 2 === 0 ? 'rgba(0,21,41,0.3)' : 'rgba(0,21,41,0.1)'}'">
                                <td style="padding: 10px 8px; font-size: 11px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <div style="color: #7ecfff;">${alert.alert_timestamp.split(' ')[0]}</div>
                                    <div style="color: #fff; font-size: 10px;">${alert.alert_timestamp.split(' ')[1]}</div>
                                </td>
                                <td style="padding: 10px 8px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <span style="background: ${getAlertTypeColor(alert.alert_type)}; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; color: #000;">
                                        ${translateAlertType(alert.alert_type)}
                                    </span>
                                </td>
                                <td style="padding: 10px 8px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <span style="background: ${alert.severity_level === 'critical' ? '#ff4444' : '#ffbb00'}; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; color: #000;">
                                        ${alert.severity_level === 'critical' ? '🔴 严重' : '🟡 中等'}
                                    </span>
                                </td>
                                <td style="padding: 10px 8px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <span style="background: ${alert.alert_status === 'pending' ? '#ff4444' : '#00e4ff'}; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: bold; color: ${alert.alert_status === 'pending' ? '#fff' : '#000'};">
                                        ${alert.alert_status === 'pending' ? '⏳ 待处理' : '✅ 已处理'}
                                    </span>
                                </td>
                                <td style="padding: 10px 8px; font-size: 12px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <div style="color: #00e4ff; font-weight: bold;">${alert.user_name}</div>
                                    <div style="color: #7ecfff; font-size: 10px;">ID: ${alert.user_id}</div>
                                </td>
                                <td style="padding: 10px 8px; font-size: 12px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <div style="color: #fff;">${alert.dept_name}</div>
                                    <div style="color: #7ecfff; font-size: 10px;">部门ID: ${alert.dept_id}</div>
                                </td>
                                <td style="padding: 10px 8px; font-size: 11px; border-right: 1px solid rgba(255,255,255,0.05);">
                                    <div style="color: #ffbb00; font-family: monospace;">${alert.device_sn}</div>
                                    ${alert.health_id ? `<div style="color: #7ecfff; font-size: 10px;">健康ID: ${alert.health_id}</div>` : ''}
                                </td>
                                <td style="padding: 10px 8px; font-size: 11px; max-width: 200px; word-wrap: break-word; line-height: 1.4;">
                                    <div style="color: #fff;">${alert.alert_desc || '无详细描述'}</div>
                                    ${alert.alert_status === 'pending' ? `
                                        <button onclick="handleAlert('${alert.alert_id}')" 
                                                style="margin-top: 5px; background: #ff4444; color: #fff; border: none; padding: 3px 8px; border-radius: 4px; cursor: pointer; font-size: 10px; transition: all 0.2s ease;"
                                                onmouseover="this.style.background='#ff6666'" 
                                                onmouseout="this.style.background='#ff4444'">
                                            🚨 立即处理
                                        </button>
                                    ` : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                ${alerts.length === 0 ? `
                    <div style="text-align: center; padding: 40px; color: #7ecfff;">
                        <div style="font-size: 48px; margin-bottom: 10px;">📭</div>
                        <div style="font-size: 16px;">暂无告警记录</div>
                        <div style="font-size: 12px; margin-top: 5px; color: rgba(255,255,255,0.5);">系统运行正常</div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 关闭事件
    modal.querySelector('.modal-close').onclick = () => modal.remove();
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
    
    // 添加键盘事件
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            modal.remove();
            document.removeEventListener('keydown', escHandler);
        }
    });
}

// 导出告警数据
function exportAlerts() {
    // 这里可以实现导出功能
    showCustomAlert('导出功能开发中...', null);
}

// 刷新告警数据
function refreshAlerts() {
    refreshData();
    showCustomAlert('告警数据已刷新', null);
}

// 获取告警类型颜色
function getAlertTypeColor(type) {
    const colors = {
        'temperature': '#ff4444',
        'stress': '#ff8800',
        'heart_rate': '#00e4ff', 
        'blood_pressure': '#ffbb00',
        'blood_oxygen': '#ff6666'
    };
    return colors[type] || '#00e4ff';
}

// 修改设备管理图表初始化函数
function initDeviceChart(data) {
    const statsContainer = document.getElementById('statsChart');
    if (!statsContainer) return;

    const statsChart = echarts.init(statsContainer);
    
    const deviceInfo = data.device_info || {};
    const totalDevices = deviceInfo.totalDevices || 0;
    document.getElementById('totalWatchDevices').textContent = totalDevices;
    


    // 添加点击事件监听器
    statsContainer.onclick = () => {
        const legendData = {
            '部门分布': deviceInfo.departmentDeviceCount || {},
            '充电状态': deviceInfo.deviceChargingCount || {},
            '设备状态': deviceInfo.deviceStatusCount || {},
            '系统版本': deviceInfo.deviceSystemVersionCount || {},
            '佩戴状态': deviceInfo.deviceWearableCount || {}
        };
        showFullLegend(legendData);
    };

    // 处理数据为堆叠格式
    const categories = ['部门分布', '充电状态', '设备状态', '系统版本', '佩戴状态'];
    
    // 处理部门设备数据
    const departmentData = Object.entries(deviceInfo.departmentDeviceCount || {}).map(([name, value]) => ({
        name,
        value
    }));

    // 处理充电状态数据
    const chargingData = Object.entries(deviceInfo.deviceChargingCount || {}).map(([status, value]) => ({
        name: status === 'NOT_CHARGING' ? '未充电' : '充电中',
        value
    }));

    // 处理设备状态数据
    const statusData = Object.entries(deviceInfo.deviceStatusCount || {}).map(([status, value]) => ({
        name: status === 'ACTIVE' ? '活跃' : '非活跃',
        value
    }));

    // 处理系统版本数据
    const versionData = Object.entries(deviceInfo.deviceSystemVersionCount || {}).map(([version, value]) => ({
        name: version,
        value
    }));

    // 处理佩戴状态数据
    const wearableData = Object.entries(deviceInfo.deviceWearableCount || {}).map(([status, value]) => ({
        name: status === 'WORN' ? '已佩戴' : '未佩戴',
        value
    }));

    // 创建系列数据
    const series = [];
    
    // 部门分布系列
    departmentData.forEach((item, index) => {
        series.push({
            name: item.name,
            type: 'bar',
            stack: '部门分布',
            emphasis: {
                focus: 'series'
            },
            data: [item.value, 0, 0, 0, 0]
        });
    });

    // 充电状态系列
    chargingData.forEach((item, index) => {
        series.push({
            name: item.name,
            type: 'bar',
            stack: '充电状态',
            emphasis: {
                focus: 'series'
            },
            data: [0, item.value, 0, 0, 0]
        });
    });

    // 设备状态系列
    statusData.forEach((item, index) => {
        series.push({
            name: item.name,
            type: 'bar',
            stack: '设备状态',
            emphasis: {
                focus: 'series'
            },
            data: [0, 0, item.value, 0, 0]
        });
    });

    // 系统版本系列
    versionData.forEach((item, index) => {
        series.push({
            name: item.name,
            type: 'bar',
            stack: '系统版本',
            emphasis: {
                focus: 'series'
            },
            data: [0, 0, 0, item.value, 0]
        });
    });

    // 佩戴状态系列
    wearableData.forEach((item, index) => {
        series.push({
            name: item.name,
            type: 'bar',
            stack: '佩戴状态',
            emphasis: {
                focus: 'series'
            },
            data: [0, 0, 0, 0, item.value]
        });
    });

    const statsOption = {
        title: {
            text: '设备状态统计',
            textStyle: {
                color: '#fff',
                fontSize: 14
            },
            left: 'center',
            top: 10
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: function(params) {
                const stackName = params[0].axisValue;
                let result = `${stackName}<br/>`;
                params.forEach(param => {
                    if (param.value > 0) {
                        result += `${param.seriesName}: ${param.value}<br/>`;
                    }
                });
                return result;
            }
        },
        legend: {
            textStyle: {
                color: '#fff'
            },
            top: 35,
            type: 'scroll',
            orient: 'horizontal'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            top: '25%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: categories,
            axisLabel: {
                color: '#fff',
                interval: 0,
                rotate: 30
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                color: '#fff'
            },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.1)'
                }
            }
        },
        series: series
    };
    
    statsChart.setOption(statsOption);
    return statsChart;
}

// 修改趋势分析图表，增加预测数据
function updateTrendChart(data) {
    const trendContainer = document.getElementById('trendChart');
    if (!trendContainer) return;

    const trendChart = echarts.init(trendContainer);
    
    const trendOption = {
        title: {
            text: '健康指标趋势及预测',
            textStyle: {
                color: '#fff',
                fontSize: 16
            }
        },
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(0,21,41,0.9)',
            borderColor: 'rgba(0,228,255,0.2)',
            textStyle: { color: '#fff' }
        },
        legend: {
        <div><span style="color:#7ecfff;">告警类别：</span><span style="color:${getAlertTypeColor(get('alert_type','alertType','-'))};font-weight:700;">${translateAlertType(get('alert_type','alertType','-'))}</span></div>
        <div><span style="color:#7ecfff;">级别：</span><span style="color:${getAlertSeverityColor(level||'-')};font-weight:700;">${translateAlertSeverity(level||'-')}</span></div>
        <div><span style="color:#7ecfff;">状态：</span><span style="color:${getAlertStatusColor(get('alert_status','status','-'))};font-weight:700;">${translateAlertStatus(get('alert_status','status','-'))}</span></div>
      </div>
      <div style="margin-bottom:12px;">
        <span style="color:#7ecfff;">健康信息：</span>
        <a href="javascript:void(0)" onclick="showHealthProfile('${get('health_id','healthId')}')" style="color:#00e4ff;text-decoration:underline;font-family:monospace;font-size:15px;">${get('health_id','healthId')}</a>
      </div>
    <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">位置信息：</span><span id="locationInfo">正在获取...</span>
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">告警时间：</span>${get('alert_timestamp','timestamp','-')}
      </div>

      <div style="display:flex;gap:18px;align-items:center;">
        <button onclick="handleAlert('${get('alert_id','alertId')}')" style="padding:7px 22px;background:${levelColor};color:#001529;border:none;border-radius:6px;cursor:pointer;font-weight:700;box-shadow:0 2px 8px ${levelColor}44;transition:.2s;">一键处理</button>
        <span style="flex:1"></span>
        <span style="color:#00e4ff;cursor:pointer;font-size:22px;font-weight:700;" onclick="removeCustomMapInfo()">×</span>
      </div>
    `;
    document.body.appendChild(div);
    

  } else {
    // 健康点内容
    div.innerHTML=`
      <div style="display:flex;align-items:center;gap:18px;margin-bottom:12px;">
        <img src="${avatarUrl}" style="width:56px;height:56px;border-radius:50%;border:2px solid #00e4ff;box-shadow:0 0 8px #00e4ff44;object-fit:cover;background:#001529;">
        <div>
          <div style="font-size:18px;font-weight:700;letter-spacing:1px;">${get('dept_name','deptName')}</div>
          <div style="font-size:16px;color:#00e4ff;font-weight:500;margin-top:2px;">${get('user_name','userName')}</div>
        </div>
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">心率：</span>${get('heartRate','heart_rate')}