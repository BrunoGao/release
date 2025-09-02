// 在全局作用域声明图表变量
      let globalCharts = null;
      let currentDept = '', currentUser = '';
      const ALERT_TYPE_MAP = {
        heart_rate: '心率',
        blood_pressure: '血压',
        stress: '压力',
        blood_oxygen: '血氧',
        temperature: '体温',
        one_key_alarm: '一键报警',
        fall_down: '跌倒',
        sleep: '睡眠'
      };
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
        // 注意：告警信息panel和设备信息panel不在此处初始化图表
        // 而是在refreshData时通过initAlertChart和initDeviceChart来初始化
        // 这样确保初始化时和数据更新时使用相同的图表配置，避免显示不一致
        try {
            let charts = {
                healthScore: null,
                stats: null,
                trend: null,
                alert: null,
                messageStats: null // 添加消息统计图表
            };

            // 检查并初始化健康评分图表
            const healthScoreContainer = document.getElementById('healthScoreChart');
            if (healthScoreContainer) {
                charts.healthScore = echarts.init(healthScoreContainer);
                
                // 从URL获取customerId参数
                const urlParams = new URLSearchParams(window.location.search);
                const customerId = urlParams.get('customerId') || '1';
                
                // 获取日期范围
                const today = new Date();
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 7);
                
                const startDate = formatDate(yesterday);
                const endDate = formatDate(today);
                
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
                            charts.healthScore.setOption(healthScoreOption);
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
                            charts.healthScore.setOption(healthScoreOption);
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
                        charts.healthScore.setOption(healthScoreOption);
                    });
            }

            // 检查并初始化数据统计图表
            // 检查并初始化数据统计图表
            const statsContainer = document.getElementById('statsChart');
            if (statsContainer) {
                // 创建默认的设备统计结构，与initDeviceChart相同风格但显示默认数据
                statsContainer.innerHTML = `
                    <div style="position: relative; height: 100%; padding: 8px;">
                        <!-- 设备状态总览 -->
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 6px 10px; background: rgba(0,228,255,0.1); border-radius: 6px; border-left: 4px solid #00e4ff;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div class="device-stat-item">
                                    <span style="color: #00ff9d; font-size: 18px; font-weight: bold;" id="onlineDevices">0</span>
                                    <span style="color: #fff; font-size: 12px; margin-left: 4px;">在线</span>
                                </div>
                                <div class="device-stat-item">
                                    <span style="color: #ffbb00; font-size: 16px; font-weight: bold;" id="offlineDevices">0</span>
                                    <span style="color: #fff; font-size: 12px; margin-left: 4px;">离线</span>
                                </div>
                                <div class="device-stat-item">
                                    <span style="color: #ff6666; font-size: 14px; font-weight: bold;" id="errorDevices">0</span>
                                    <span style="color: #fff; font-size: 12px; margin-left: 4px;">故障</span>
                                </div>
                            </div>
                            <div style="background: rgba(0,255,157,0.3); padding: 4px 8px; border-radius: 12px;" id="deviceStatusBadge">
                                <span style="color: #00ff9d; font-size: 11px; font-weight: bold;">✅ 正常</span>
                            </div>
                        </div>
                        
                        <!-- 图表区域 -->
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; height: calc(100% - 45px);">
                            <div id="deviceStatusChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">设备状态分布</div>
                            </div>
                            <div id="deviceTypeChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">设备类型分布</div>
                            </div>
                            <div id="deviceDeptChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">部门分布</div>
                            </div>
                            <div id="deviceTrendChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">使用趋势</div>
                            </div>
                        </div>
                    </div>
                `;

                // 延时初始化默认图表
                setTimeout(() => {
                    if (document.getElementById('deviceStatusChart')) {
                        // 设备状态分布图
                        const statusChart = echarts.init(document.getElementById('deviceStatusChart'));
                        statusChart.setOption({
                            tooltip: { trigger: 'item', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '55%'], data: [
                                { name: '暂无数据', value: 1, itemStyle: { color: '#666' } }
                            ], label: { show: false } }]
                        });

                        // 设备类型分布图
                        const typeChart = echarts.init(document.getElementById('deviceTypeChart'));
                        typeChart.setOption({
                            tooltip: { trigger: 'item', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '55%'], data: [
                                { name: '暂无数据', value: 1, itemStyle: { color: '#666' } }
                            ], label: { show: false } }]
                        });

                        // 部门分布图
                        const deptChart = echarts.init(document.getElementById('deviceDeptChart'));
                        deptChart.setOption({
                            tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            grid: { top: 25, left: 50, right: 15, bottom: 15 },
                            xAxis: { type: 'value', axisLabel: { color: '#7ecfff', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)' } }, axisLine: { show: false }, max: 1 },
                            yAxis: { type: 'category', data: ['暂无数据'], axisLabel: { color: '#fff', fontSize: 9 }, axisLine: { show: false }, axisTick: { show: false } },
                            series: [{ type: 'bar', data: [0], barWidth: '65%', itemStyle: { color: '#00e4ff88' } }]
                        });

                        // 使用趋势图
                        const trendChart = echarts.init(document.getElementById('deviceTrendChart'));
                        const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
                        trendChart.setOption({
                            tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            grid: { top: 25, left: 30, right: 15, bottom: 25 },
                            xAxis: { type: 'category', data: days, axisLabel: { color: '#7ecfff', fontSize: 8 }, axisLine: { show: false }, axisTick: { show: false } },
                            yAxis: { type: 'value', axisLabel: { color: '#7ecfff', fontSize: 8 }, splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)' } }, axisLine: { show: false } },
                            series: [{ type: 'line', data: [0, 0, 0, 0, 0, 0, 0], smooth: true, lineStyle: { color: '#00e4ff', width: 2 }, itemStyle: { color: '#00e4ff' }, symbol: 'circle', symbolSize: 4 }]
                        });
                    }
                }, 200);

                charts.stats = null; // 将在initDeviceChart中重新设置
            }

            // 检查并初始化预警信息图表
            const alertContainer = document.getElementById('alertList');
            if (alertContainer) {
                // 创建默认的告警信息结构，与initAlertChart相同风格但显示默认数据
                alertContainer.innerHTML = `
                    <div style="position: relative; height: 100%; padding: 8px;">
                        <!-- 告警状态总览 -->
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 6px 10px; background: rgba(0,228,255,0.1); border-radius: 6px; border-left: 4px solid #00e4ff;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div class="alert-stat-item">
                                    <span style="color: #ff4444; font-size: 18px; font-weight: bold;" id="criticalCount">0</span>
                                    <span style="color: #fff; font-size: 12px; margin-left: 4px;">严重</span>
                                </div>
                                <div class="alert-stat-item">
                                    <span style="color: #ffbb00; font-size: 16px; font-weight: bold;" id="mediumCount">0</span>
                                    <span style="color: #fff; font-size: 12px; margin-left: 4px;">中等</span>
                                </div>
                                <div class="alert-stat-item">
                                    <span style="color: #ff6666; font-size: 14px; font-weight: bold;" id="pendingCount">0</span>
                                    <span style="color: #fff; font-size: 12px; margin-left: 4px;">待处理</span>
                                </div>
                            </div>
                            <div style="background: rgba(0,255,157,0.3); padding: 4px 8px; border-radius: 12px;" id="alertBadge">
                                <span style="color: #00ff9d; font-size: 11px; font-weight: bold;">✅ 正常</span>
                            </div>
                        </div>
                        
                        <!-- 图表区域 -->
                        <div class="alert-charts-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 6px; height: calc(100% - 45px);">
                            <div id="alertTypeChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">告警类型分布</div>
                            </div>
                            <div id="alertLevelChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">严重程度分析</div>
                            </div>
                            <div id="alertStatusChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">处理状态</div>
                            </div>
                            <div id="alertTrendChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                                <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">24小时趋势</div>
                            </div>
                        </div>
                    </div>
                `;

                // 延时初始化默认图表
                setTimeout(() => {
                    if (document.getElementById('alertTypeChart')) {
                        // 告警类型分布图 
                        const typeChart = echarts.init(document.getElementById('alertTypeChart'));
                        typeChart.setOption({
                            tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            grid: { top: 25, left: 50, right: 15, bottom: 15 },
                            xAxis: { type: 'value', axisLabel: { color: '#7ecfff', fontSize: 9 }, splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)' } }, axisLine: { show: false }, max: 1 },
                            yAxis: { type: 'category', data: ['暂无数据'], axisLabel: { color: '#fff', fontSize: 9 }, axisLine: { show: false }, axisTick: { show: false } },
                            series: [{ type: 'bar', data: [0], barWidth: '65%', itemStyle: { color: '#00e4ff88' } }]
                        });

                        // 告警级别分布图
                        const levelChart = echarts.init(document.getElementById('alertLevelChart'));
                        levelChart.setOption({
                            tooltip: { trigger: 'item', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '55%'], data: [
                                { name: '暂无数据', value: 1, itemStyle: { color: '#666' } }
                            ], label: { show: false } }]
                        });

                        // 处理状态图
                        const statusChart = echarts.init(document.getElementById('alertStatusChart'));
                        statusChart.setOption({
                            tooltip: { trigger: 'item', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            series: [{ type: 'pie', radius: ['35%', '65%'], center: ['50%', '55%'], data: [
                                { name: '暂无数据', value: 1, itemStyle: { color: '#666' } }
                            ], label: { show: false } }]
                        });

                        // 24小时趋势图
                        const trendChart = echarts.init(document.getElementById('alertTrendChart'));
                        const hours = ['00', '04', '08', '12', '16', '20'];
                        trendChart.setOption({
                            tooltip: { trigger: 'axis', backgroundColor: 'rgba(0,21,41,0.95)', borderColor: '#00e4ff', textStyle: { color: '#fff', fontSize: 11 } },
                            grid: { top: 25, left: 30, right: 15, bottom: 25 },
                            xAxis: { type: 'category', data: hours, axisLabel: { color: '#7ecfff', fontSize: 8 }, axisLine: { show: false }, axisTick: { show: false } },
                            yAxis: { type: 'value', axisLabel: { color: '#7ecfff', fontSize: 8 }, splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)' } }, axisLine: { show: false } },
                            series: [{ type: 'line', data: [0, 0, 0, 0, 0, 0], smooth: true, lineStyle: { color: '#00e4ff', width: 2 }, itemStyle: { color: '#00e4ff' }, symbol: 'circle', symbolSize: 4 }]
                        });
                    }
                }, 200);

                charts.alert = null; // 将在initAlertChart中重新设置
            }

            // 添加窗口resize事件监听
            window.addEventListener('resize', () => {
                Object.values(charts).forEach(chart => {
                    if (chart) {
                        chart.resize();
                    }
                });
            });

            // 初始化消息统计图表
            const messageStatsContainer = document.getElementById('messageStatsChart');
            if (messageStatsContainer) {
                charts.messageStats = echarts.init(messageStatsContainer);
                
                // 消息类型颜色定义（与message_view.html保持一致）
                const messageTypeColors = {
                    'announcement': '#1890ff',  // 蓝色 - 公告
                    'notification': '#52c41a',  // 绿色 - 通知
                    'job': '#722ed1',          // 紫色 - 作业指导
                    'task': '#fa8c16',         // 橙色 - 任务管理
                    'warning': '#f5222d'       // 红色 - 告警
                };
                
                // 初始化消息统计图表
                const messageStatsOption = {
                    tooltip: {
                        trigger: 'item',
                        formatter: '{a} <br/>{b}: {c} ({d}%)'
                    },
                    legend: {
                        show: false
                    },
                    series: [{
                        name: '消息类型',
                        type: 'pie',
                        radius: ['30%', '70%'],
                        center: ['50%', '60%'],
                        avoidLabelOverlap: false,
                        label: {
                            show: false
                        },
                        emphasis: {
                            label: {
                                show: true,
                                fontSize: '10',
                                fontWeight: 'bold',
                                color: '#fff'
                            }
                        },
                        labelLine: {
                            show: false
                        },
                        data: [
                            {value: 0, name: '公告', itemStyle: {color: messageTypeColors.announcement}},
                            {value: 0, name: '工作指引', itemStyle: {color: messageTypeColors.job}},
                            {value: 0, name: '通知', itemStyle: {color: messageTypeColors.notification}},
                            {value: 0, name: '任务管理', itemStyle: {color: messageTypeColors.task}},
                            {value: 0, name: '告警', itemStyle: {color: messageTypeColors.warning}}
                        ]
                    }]
                };
                charts.messageStats.setOption(messageStatsOption);
            }

            // 返回图表实例对象，以便其他地方可能需要使用
            return charts;

        } catch (error) {
            console.error('Error initializing charts:', error);
        }
    }

    // 修改初始化调用
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            globalCharts = initCharts(); // 存储图表实例
            initializeMap('{{ customerId }}','-1'); // 初始化地图
            refreshData(); // 初始加载数据

            // 每分钟刷新一次数据
            setInterval(refreshData, 60000);
        }, 100);
    });

    // 修改消息列表初始化
    function initMessageList(data) {
        const messageList = document.getElementById('messageList');
        const messageCount = document.getElementById('messageCount');
        
        if (!messageList || !messageCount) return;
    
        // 消息类型颜色定义（参考message_view.html）
        const messageTypeColors = {
            'announcement': '#1890ff',  // 蓝色 - 公告
            'notification': '#52c41a',  // 绿色 - 通知
            'job': '#722ed1',          // 紫色 - 作业指导
            'task': '#fa8c16',         // 橙色 - 任务管理
            'warning': '#f5222d'       // 红色 - 告警
        };

        const typeMap = {
            'announcement': '公告',
            'job': '工作指引',
            'notification': '通知',
            'task': '任务管理',
            'warning': '告警'
        };
    
        // 从message_info中获取数据
        //console.log('initMessageList.data', data);
        const messages = data.message_info.messages || [];
        // 过滤出状态为pending的消息
        const pendingMessages = messages.filter(msg => msg.message_status === 'pending' || msg.message_status === '1');
        
        // 更新消息计数
        messageCount.textContent = pendingMessages.length;

        // 统计消息数据
        const today = new Date().toDateString();
        const todayMessages = messages.filter(msg => new Date(msg.received_time).toDateString() === today).length;
        const unreadMessages = messages.filter(msg => msg.message_status === 'pending' || msg.message_status === '1').length;
        const urgentMessages = messages.filter(msg => msg.priority === 'high' || msg.priority === 'urgent').length;

        // 更新统计显示
        document.getElementById('todayMessages').textContent = todayMessages;
        document.getElementById('unreadMessages').textContent = unreadMessages;
        document.getElementById('urgentMessages').textContent = urgentMessages;

        // 统计消息类型分布 - 使用正确的类型映射
        const messageTypes = {
            '公告': 0,
            '工作指引': 0,
            '通知': 0,
            '任务管理': 0,
            '告警': 0
        };

        messages.forEach(msg => {
            const type = msg.message_type || 'notification';
            const typeName = typeMap[type] || '通知';
            if (messageTypes.hasOwnProperty(typeName)) {
                messageTypes[typeName]++;
            }
        });

        // 更新消息统计图表
        if (globalCharts && globalCharts.messageStats) {
            const chartData = [
                {value: messageTypes['公告'], name: '公告', itemStyle: {color: messageTypeColors.announcement}},
                {value: messageTypes['工作指引'], name: '工作指引', itemStyle: {color: messageTypeColors.job}},
                {value: messageTypes['通知'], name: '通知', itemStyle: {color: messageTypeColors.notification}},
                {value: messageTypes['任务管理'], name: '任务管理', itemStyle: {color: messageTypeColors.task}},
                {value: messageTypes['告警'], name: '告警', itemStyle: {color: messageTypeColors.warning}}
            ];
            
            globalCharts.messageStats.setOption({
                series: [{
                    data: chartData
                }]
            });
        }
    
        // 清空现有消息
        messageList.innerHTML = '';
    
        // 创建消息容器
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container';
    
        // 添加所有消息
        pendingMessages.forEach(message => {
            const msgType = message.message_type || 'notification';
            const msgColor = messageTypeColors[msgType] || messageTypeColors.notification;
            const msgTypeName = typeMap[msgType] || '通知';
            
            const messageElement = document.createElement('div');
            messageElement.className = 'message-item';
            messageElement.innerHTML = `
                <div class="message-header">
                    <span style="color: ${msgColor}; font-weight: bold;">[${msgTypeName}] ${message.department_name || '未知部门'}-${message.user_name || '系统'}</span>
                    <span class="message-time">${message.received_time || new Date().toLocaleString()}</span>
                </div>
                <div class="message-content" style="border-left: 3px solid ${msgColor}; padding-left: 6px;">${message.message || '无消息内容'}</div>
            `;
            messageContainer.appendChild(messageElement);
        });
    
        // 如果没有消息，显示提示信息
        if (pendingMessages.length === 0) {
            messageList.innerHTML = '<div class="no-messages">暂无待处理消息</div>';
            return;
        }
    
        // 将消息容器添加到列表中
        messageList.appendChild(messageContainer);
    
        // 添加样式 - 移除重复样式防止冲突
        const existingStyle = document.getElementById('message-scroll-styles');
        if (existingStyle) {
            existingStyle.remove();
        }
        
        const style = document.createElement('style');
        style.id = 'message-scroll-styles';
        style.textContent = `
            #messageList {
                height: calc(100% - 5px);
                overflow: hidden;
                position: relative;
                background: linear-gradient(135deg, rgba(0, 42, 74, 0.8), rgba(0, 74, 114, 0.6));
                border-radius: 8px;
                border: 1px solid rgba(0, 228, 255, 0.25);
                box-shadow: inset 0 1px 3px rgba(0, 228, 255, 0.1);
            }
    
            .message-container {
                display: flex;
                flex-direction: column;
                width: 100%;
                padding: 8px;
            }
    
            .message-item {
                background: linear-gradient(135deg, rgba(0, 62, 94, 0.8), rgba(0, 94, 134, 0.6));
                border: 1px solid rgba(0, 228, 255, 0.2);
                border-radius: 6px;
                padding: 8px 12px;
                margin-bottom: 6px;
                position: relative;
                transition: all 0.3s ease;
                backdrop-filter: blur(10px);
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15), 0 0 15px rgba(0, 228, 255, 0.05);
            }
    
            .message-item::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 4px;
                border-radius: 2px 0 0 2px;
                transition: all 0.3s ease;
            }
    
            .message-item.type-announcement::before { background: linear-gradient(135deg, #4A90E2, #357ABD); }
            .message-item.type-notification::before { background: linear-gradient(135deg, #7ED321, #5BA317); }
            .message-item.type-job::before { background: linear-gradient(135deg, #9013FE, #6A1B9A); }
            .message-item.type-task::before { background: linear-gradient(135deg, #FF9500, #E6830F); }
            .message-item.type-warning::before { background: linear-gradient(135deg, #F5A623, #E8940F); }
    
            .message-item:hover {
                transform: translateX(2px);
                border-color: rgba(64, 169, 255, 0.4);
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3), 0 0 20px rgba(64, 169, 255, 0.1);
            }
    
            .message-item:last-child {
                margin-bottom: 0;
            }
    
            .message-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 4px;
            }
    
            .message-type-badge {
                display: inline-flex;
                align-items: center;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 10px;
                font-weight: 600;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                backdrop-filter: blur(5px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
    
            .message-type-badge.announcement {
                background: linear-gradient(135deg, rgba(74, 144, 226, 0.2), rgba(53, 122, 189, 0.3));
                color: #87CEEB;
                border-color: rgba(74, 144, 226, 0.3);
            }
    
            .message-type-badge.notification {
                background: linear-gradient(135deg, rgba(126, 211, 33, 0.2), rgba(91, 163, 23, 0.3));
                color: #98FB98;
                border-color: rgba(126, 211, 33, 0.3);
            }
    
            .message-type-badge.job {
                background: linear-gradient(135deg, rgba(144, 19, 254, 0.2), rgba(106, 27, 154, 0.3));
                color: #DDA0DD;
                border-color: rgba(144, 19, 254, 0.3);
            }
    
            .message-type-badge.task {
                background: linear-gradient(135deg, rgba(255, 149, 0, 0.2), rgba(230, 131, 15, 0.3));
                color: #FFB84D;
                border-color: rgba(255, 149, 0, 0.3);
            }
    
            .message-type-badge.warning {
                background: linear-gradient(135deg, rgba(245, 166, 35, 0.2), rgba(232, 148, 15, 0.3));
                color: #FFC04D;
                border-color: rgba(245, 166, 35, 0.3);
            }
    
            .message-sender {
                color: rgba(255, 255, 255, 0.9);
                font-size: 11px;
                font-weight: 500;
                margin-left: 8px;
            }
    
            .message-time {
                color: rgba(64, 169, 255, 0.8);
                font-size: 9px;
                font-weight: 400;
                font-family: 'Consolas', 'Monaco', monospace;
                background: rgba(64, 169, 255, 0.1);
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid rgba(64, 169, 255, 0.2);
            }
    
            .message-content {
                color: rgba(255, 255, 255, 0.95);
                font-size: 12px;
                line-height: 1.4;
                font-weight: 400;
                margin-top: 2px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
                max-height: 32px;
            }
    
            .no-messages {
                text-align: center;
                padding: 30px 20px;
                color: rgba(255, 255, 255, 0.4);
                font-size: 14px;
                background: linear-gradient(135deg, rgba(20, 45, 85, 0.3), rgba(30, 55, 95, 0.2));
                border-radius: 8px;
                border: 1px dashed rgba(64, 169, 255, 0.3);
                margin: 20px;
            }
    
            /* 滚动动画 */
            .message-container.scrolling {
                animation: verticalScroll linear infinite;
            }
    
            @keyframes verticalScroll {
                0% {
                    transform: translateY(0);
                }
                100% {
                    transform: translateY(-50%);
                }
            }
    
            /* 添加呼吸光效 */
            .message-item::after {
                content: '';
                position: absolute;
                top: -1px;
                left: -1px;
                right: -1px;
                bottom: -1px;
                background: linear-gradient(45deg, transparent, rgba(64, 169, 255, 0.1), transparent);
                border-radius: 6px;
                opacity: 0;
                animation: breathe 3s ease-in-out infinite;
                pointer-events: none;
                z-index: -1;
            }
    
            @keyframes breathe {
                0%, 100% { opacity: 0; }
                50% { opacity: 0.3; }
            }
        `;
        document.head.appendChild(style);
    
        // 实现滚动逻辑
        setTimeout(() => {
            const containerHeight = messageList.clientHeight;
            const contentHeight = messageContainer.scrollHeight;
            
            console.log('Container height:', containerHeight, 'Content height:', contentHeight);
            
            if (contentHeight > containerHeight && pendingMessages.length > 3) {
                // 复制内容实现无缝滚动
                messageContainer.innerHTML += messageContainer.innerHTML;
                
                // 计算滚动时间：每个消息显示3秒
                const scrollDuration = pendingMessages.length * 3;
                
                // 添加滚动类和设置动画时间
                messageContainer.classList.add('scrolling');
                messageContainer.style.animationDuration = `${scrollDuration}s`;
                
                console.log('启动滚动动画，持续时间:', scrollDuration + 's');
                
                // 鼠标悬停控制
                messageList.addEventListener('mouseenter', () => {
                    messageContainer.style.animationPlayState = 'paused';
                });
                
                messageList.addEventListener('mouseleave', () => {
                    messageContainer.style.animationPlayState = 'running';
                });
            } else {
                console.log('消息数量少，不启动滚动');
            }
            
            // 添加消息点击事件
            addMessageClickEvents();
        }, 500); // 延迟500ms确保DOM渲染完成
    }

    // 添加消息面板点击处理函数
    function openMessagePanel() {
        const urlParams = new URLSearchParams(window.location.search);
        const customerId = urlParams.get('customerId') || '1';
        createModalWindow('/message_view?customerId=' + customerId, '消息管理', '90%', '90%');
    }

    // 添加消息项点击事件
    function addMessageClickEvents() {
        const messageItems = document.querySelectorAll('.message-item');
        messageItems.forEach(item => {
            item.addEventListener('click', openMessagePanel);
            item.style.cursor = 'pointer';
        });
    }
    

      // Declare infoWindow globally
      // let infoWindow; // 移除
      let geoLevelF,geoLevelE,geo,map,loca,breathGreen,breathRed,breathYellow;//变量合并

      async function updateGeoJSONSources(deptId, userId) {
        try {
            console.log('Updating GeoJSON sources...', { deptId, userId });
    
            // 构建URL参数
            const params = new URLSearchParams({
                customerId: deptId || '1',
                userId: userId || '-1'
            }).toString();
    
     
            // 创建新的数据源
            const newGeoLevelF = new Loca.GeoJSONSource({
                data: criticalData
            });
    
            const newGeoLevelE = new Loca.GeoJSONSource({
                data: highData
            });
    
            const newGeo = new Loca.GeoJSONSource({
                data: healthData
            });
    
            // 更新图层数据源
            breathRed.setSource(newGeoLevelF);
            breathYellow.setSource(newGeoLevelE);
            breathGreen.setSource(newGeo);
    
            // 更新地图中心点
            if (healthData.features && healthData.features.length > 0) {
                const coordinates = healthData.features[0].geometry.coordinates;
                console.log('updateGeoJSONSources.coordinates',coordinates);
                map.setCenter(coordinates);
            }
    
            // 重新启动动画
            loca.animate.start();
    
            console.log('GeoJSON sources updated successfully');
    
        } catch (error) {
            console.error('Error updating GeoJSON sources:', error);
        }
    }


      function initializeMap(deptId, userId) {
        //console.log(AMap); // 如果打印 `undefined`，说明 AMap 没有正确加载
        //console.log(Loca); // 如果打印 `undefined`，说明 Loca 没有正确加载
        //console.log('initializeMap.deptId',deptId);
        //console.log('initializeMap.userId',userId);
        
        // 优化：初始化时不加载geo数据，减少3.8秒的性能损耗
        // 这些数据源将在updateMapData中根据实际数据动态创建
        console.log('地图初始化开始 - 仅创建地图实例和图层');

        // 获取默认坐标
        let current_coordinates = {
          'longitude': 114.01508952,
          'latitude': 22.58036796,
          'altitude': 0
        }
    
        // 初始化地图实例
          map = window.map = new AMap.Map('map-container', {
              zoom: 17,
              center: [current_coordinates['longitude'],current_coordinates['latitude']],
              pitch: 45,
              showLabel: false,
              mapStyle: 'amap://styles/blue',
              viewMode: '3D',
          });

        // 初始化Loca容器
          loca = new Loca.Container({
            map,
          });
        
        // 创建绿色健康点图层 - 不设置数据源
          breathGreen = new Loca.ScatterLayer({
            loca,
            zIndex: 113,
            opacity: 1,
            visible: true,
            zooms: [2, 22],
          });
  
        // 设置绿色点样式
        breathGreen.setStyle({
            unit: 'meter',
            color: 'rgb(39, 207, 14)',
            size: [10, 10],
            borderWidth: 0,
          texture: 'https://a.amap.com/Loca/static/loca-v2/demos/images/breath_green.png',
            duration: 500,
            animate: true,
        });
        
        // 添加到地图中
        loca.add(breathGreen);
      
        // 创建红色呼吸点图层 - 不设置数据源
        breathRed = new Loca.ScatterLayer({
            loca,
            zIndex: 113,
            opacity: 1,
            visible: true,
            zooms: [2, 22],
        });
        
        // 设置红色点样式
        breathRed.setStyle({
            unit: 'meter',
            size: [60, 60],
            borderWidth: 0,
            texture: 'https://a.amap.com/Loca/static/loca-v2/demos/images/breath_red.png',
            duration: 500,
            animate: true,
        });
        
        // 添加到地图中
        loca.add(breathRed);
        
        // 创建黄色告警点图层 - 不设置数据源
          breathYellow = new Loca.ScatterLayer({
              loca,
              zIndex: 112,
              opacity: 1,
              visible: true,
              zooms: [2, 22],
          });
        
        // 设置黄色点样式
          breathYellow.setStyle({
              unit: 'meter',
              size: [50, 50],
              borderWidth: 0,
              texture: 'https://a.amap.com/Loca/static/loca-v2/demos/images/breath_yellow.png',
              duration: 1000,
              animate: true,
          });
          loca.add(breathYellow);
      
        // 添加点击事件弹出信息框
        map.on('click',e=>{const p=e.pixel.toArray();let f=breathRed.queryFeature(p)||breathYellow.queryFeature(p)||breathGreen.queryFeature(p);if(f&&f.coordinates){showCustomMapInfo(f)}else{removeCustomMapInfo()}});
      
          // 启动渲染动画
          loca.animate.start();
      
        console.log('地图初始化完成 - 等待数据更新');
        
        // 优化说明：
        // 1. 移除了geoLevelF、geoLevelE、geo的HTTP请求初始化
        // 2. 减少了3.8秒的generateHealthJson请求时间  
        // 3. 地图点数据将通过updateMapData函数在refreshData时提供
        // 4. 显著提升页面加载性能
      }



  
  async function reverseGeocode(lng, lat) {
    try {
        const response = await fetch(`https://restapi.amap.com/v3/geocode/regeo?key=d45f28e481665db5b1145a5aa989e68a&location=${lng},${lat}`);
        const data = await response.json();
        
        if (data.status === '1') {
            const address = data.regeocode.formatted_address;
            console.log('Address:', address);
            return address;
        } else {
            console.error('Failed to reverse geocode:', data.info);
            return null;
        }
    } catch (error) {
        console.error('Error during reverse geocoding:', error);
        return null;
    }
  }


  function handleAlert(alertId) {
    fetch(`./dealAlert?alertId=${alertId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Alert processed:', data);
                showCustomAlert(data.message, () => {
                    location.reload();
                });
            } else {
                console.error('Failed to process alert:', data.message);
                showCustomAlert('处理失败，请重试', null);
            }
        })
        .catch(error => {
            console.error('Error processing alert:', error);
            showCustomAlert('处理过程中发生错误，请重试', null);
        });
}

// 添加自定义弹出框函数
function showCustomAlert(message, callback) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'custom-alert-overlay';
    document.body.appendChild(overlay);

    // 创建弹出框
    const alertBox = document.createElement('div');
    alertBox.className = 'custom-alert';
    alertBox.innerHTML = `
        <div class="custom-alert-content">${message}</div>
        <button class="custom-alert-button">确定</button>
    `;
    document.body.appendChild(alertBox);

    // 添加确定按钮点击事件
    const confirmButton = alertBox.querySelector('.custom-alert-button');
    confirmButton.onclick = () => {
        document.body.removeChild(overlay);
        document.body.removeChild(alertBox);
        if (callback) callback();
    };
}

  
  function mapAlertStatus(alertStatus) {
    switch (alertStatus) {
        case 'responded':
            return '已处理';
        case 'pending':
            return '未处理';
        case 'closed':
            return '已关闭';
        default:
            return '未知';
    }
}

// 添加在其他 JavaScript 代码之前
function toggleFilter() {
    const filterPanel = document.querySelector('.filter-panel');
    const filterContainer = document.querySelector('.filter-container');
    const toggleButton = document.querySelector('.filter-toggle i');

    console.log('toggleFilter', toggleButton);
    
    if (filterPanel.classList.contains('collapsed')) {
        // 展开面板
        filterPanel.classList.remove('collapsed');
        toggleButton.classList.remove('fa-search');
        toggleButton.classList.add('fa-times');
        filterContainer.style.display = 'flex';
    } else {
        // 收起面板
        filterPanel.classList.add('collapsed');
        toggleButton.classList.remove('fa-times');
        toggleButton.classList.add('fa-search');
        filterContainer.style.display = 'none';
    }
}

// 添加点击外部关闭筛选面板的功能
document.addEventListener('click', function(event) {
    const filterPanel = document.querySelector('.filter-panel');
    const filterToggle = document.querySelector('.filter-toggle');
    
    // 如果点击的不是筛选面板内的元素且面板是展开的
    if (!filterPanel.contains(event.target) && 
        !filterToggle.contains(event.target) && 
        !filterPanel.classList.contains('collapsed')) {
        toggleFilter();
    }
});

// 阻止筛选面板内的点击事件冒泡
document.querySelector('.filter-panel').addEventListener('click', function(event) {
    event.stopPropagation();
});

// 初始化人员管理面板
function initPersonnelManagementPanel(data) {
    // 更新总览数据
    document.getElementById('totalUsers').innerText = data.user_info.totalUsers;
    document.getElementById('totalBindDevices').innerText = data.user_info.totalDevices;

    // 初始化部门分布图表
    initDepartmentDistribution(data);
}

// 修改初始化部门分布图表函数 - 专业版
function initDepartmentDistribution(data) {
    console.log('initDepartmentDistribution 开始执行，数据:', data); // 调试信息
    
    const userInfo = data.user_info || {};
    
    // 更新统计卡片数据
    const totalUsers = userInfo.totalUsers || 0;
    const totalDevices = userInfo.totalDevices || 0;
    const departmentCount = userInfo.departmentCount || {};
    const activeDeptCount = Object.keys(departmentCount).length;
    
    // 模拟在线用户数据（实际应从后端获取）
    const onlineUsers = Math.floor(totalUsers * 0.75); // 假设75%在线
    const onlineRate = totalUsers > 0 ? ((onlineUsers / totalUsers) * 100).toFixed(1) : 0;
    const alertUsers = Math.floor(totalUsers * 0.1); // 假设10%有告警
    
    // 更新统计数据
    document.getElementById('totalUsers').textContent = totalUsers;
    document.getElementById('totalBindDevices').textContent = totalDevices;
    document.getElementById('onlineRate').textContent = onlineRate + '%';
    document.getElementById('activeDeptCount').textContent = activeDeptCount;
    document.getElementById('onlineUsers').textContent = onlineUsers;
    document.getElementById('boundDevices').textContent = totalDevices;
    document.getElementById('alertUsers').textContent = alertUsers;

    // 1. 部门分布图表 - 环形图
    const departmentChart = echarts.init(document.getElementById('departmentDistribution'));
    
    // 处理部门数据
    const departmentData = Object.entries(departmentCount)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value);

    // 如果没有数据，显示默认状态
    const hasDeptData = departmentData.length > 0 && departmentData.some(d => d.value > 0);
    const displayDeptData = hasDeptData ? departmentData : [
        { name: '暂无部门', value: 1 }
    ];

    const deptColors = ['#00e4ff', '#00a8ff', '#0080ff', '#48cae4', '#90e0ef', '#a8dadc', '#457b9d'];

    const departmentOption = {
        tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(0,21,41,0.95)',
            borderColor: '#00e4ff',
            borderWidth: 1,
            textStyle: { color: '#fff', fontSize: 11 },
            formatter: function(params) {
                if (!hasDeptData) return '暂无数据';
                return `${params.name}<br/>人数: ${params.value}人<br/>占比: ${params.percent}%`;
            }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '75%'],
            center: ['50%', '60%'],
            avoidLabelOverlap: true,
            itemStyle: {
                borderColor: 'rgba(0,21,41,0.8)',
                borderWidth: 2,
                shadowBlur: 8,
                shadowColor: 'rgba(0,228,255,0.3)'
            },
            label: {
                show: true,
                position: 'outside',
                color: '#fff',
                fontSize: 9,
                formatter: function(params) {
                    if (!hasDeptData) return '';
                    return params.value > 0 ? `${params.name}\n${params.value}人` : '';
                },
                lineHeight: 10
            },
            labelLine: {
                show: true,
                length: 6,
                length2: 4,
                lineStyle: { color: 'rgba(255,255,255,0.5)', width: 1 }
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 15,
                    shadowOffsetX: 0,
                    shadowColor: 'rgba(0,228,255,0.6)',
                    scale: 1.05
                }
            },
            data: displayDeptData.map((item, index) => ({
                ...item,
                itemStyle: { color: deptColors[index % deptColors.length] }
            }))
        }]
    };
    departmentChart.setOption(departmentOption);
    
    // 2. 用户状态图表 - 柱状图
    const statusChart = echarts.init(document.getElementById('userStatusChart'));

    // 模拟状态数据
    const statusData = {
        online: onlineUsers,
        offline: totalUsers - onlineUsers,
        bound: totalDevices,
        unbound: totalUsers - totalDevices,
        alert: alertUsers,
        normal: totalUsers - alertUsers
    };

    const statusOption = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(0,21,41,0.95)',
            borderColor: '#00e4ff',
            textStyle: { color: '#fff', fontSize: 11 },
            formatter: function(params) {
                if (!params || !params[0]) return '';
                const data = params[0];
                return `${data.name}: ${data.value}人`;
            }
        },
        grid: {
            top: 25,
            left: 25,
            right: 15,
            bottom: 20,
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ['在线', '离线', '绑定', '未绑定', '告警', '正常'],
            axisLabel: { 
                color: '#7ecfff', 
                fontSize: 9,
                interval: 0,
                rotate: 0
            },
            axisLine: { lineStyle: { color: 'rgba(126,207,255,0.3)' } },
            axisTick: { show: false }
        },
        yAxis: {
            type: 'value',
            axisLabel: { color: '#7ecfff', fontSize: 9 },
            splitLine: { lineStyle: { color: 'rgba(126,207,255,0.1)', type: 'dashed' } },
            axisLine: { show: false }
        },
        series: [{
            type: 'bar',
            data: [
                { value: statusData.online, itemStyle: { color: '#00ff9d' } },
                { value: statusData.offline, itemStyle: { color: '#666' } },
                { value: statusData.bound, itemStyle: { color: '#ffbb00' } },
                { value: statusData.unbound, itemStyle: { color: '#ff8800' } },
                { value: statusData.alert, itemStyle: { color: '#ff4444' } },
                { value: statusData.normal, itemStyle: { color: '#00e4ff' } }
            ],
            barWidth: '60%',
            label: {
                show: true,
                position: 'top',
                color: '#fff',
                fontSize: 9,
                formatter: '{c}'
            },
            emphasis: {
                itemStyle: {
                    shadowBlur: 10,
                    shadowColor: 'rgba(0,228,255,0.5)'
                }
            }
        }]
    };
    statusChart.setOption(statusOption);

    // 自适应大小
    const resizeCharts = () => {
        try {
            departmentChart && departmentChart.resize();
            statusChart && statusChart.resize();
        } catch (e) {
            console.warn('人员管理图表resize失败:', e);
        }
    };
    
    window.addEventListener('resize', resizeCharts);

    // 延迟执行确保图表正确渲染
    setTimeout(() => {
        resizeCharts();
        console.log('人员管理图表初始化完成');
    }, 200);

    // 图表点击交互
    departmentChart.on('click', function(params) {
        if (hasDeptData && params.data && params.data.value > 0) {
            showDepartmentDetails(params.data.name, params.data.value);
        }
    });

    statusChart.on('click', function(params) {
        const statusName = params.name;
        const statusValue = params.value;
        showStatusDetails(statusName, statusValue);
        });

    return { departmentChart, statusChart };
}

function getPastDateStr(daysAgo) {
    const d = new Date();
    d.setDate(d.getDate() - daysAgo);
    return d.toISOString().slice(0,10);
  }
  function loadHealthScoreChart(customerId) {
    console.log('loadHealthScoreChart 开始执行，customerId:', customerId);
    
    const endDate = getPastDateStr(0), startDate = getPastDateStr(6);
    
    if (globalCharts.healthScore) {
      // 获取日期范围
      const today = new Date();
      const yesterday = new Date(today);
      yesterday.setDate(yesterday.getDate() - 7);
      
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
                    // 更新健康评分图表
                    
                }

                // 更新人员管理面板
                initPersonnelManagementPanel(data);

                // 更新告警信息图表
                initAlertChart(data);

                // 更新设备管理图表
                initDeviceChart(data);

                // 更新消息列表
                initMessageList(data);

                // 为各个面板添加点击事件
                setupPanelClickEvents(customerId);
            }
        })
        .catch(error => console.error('Error fetching data:', error));
}

// 将面板点击事件设置抽取为单独的函数
function setupPanelClickEvents(customerId) {
    // 1. 告警信息面板
    const alertPanel = document.querySelector('.panel:has(#alertList)');
    if (alertPanel) {
        alertPanel.style.cursor = 'pointer';
        alertPanel.onclick = function() {
            createModalWindow(`/alert_view.html?customerId=${customerId}`);
        };
    }

    // 2. 设备管理面板
    const devicePanel = document.querySelector('.panel:has(#statsChart)');
    if (devicePanel) {
        devicePanel.style.cursor = 'pointer';
        devicePanel.onclick = function() {
            createModalWindow(`/device_view.html?customerId=${customerId}`);
        };
    }

    // 3. 消息信息面板
    const messagePanel = document.querySelector('.panel:has(#messageList)');
    if (messagePanel) {
        messagePanel.style.cursor = 'pointer';
        messagePanel.onclick = function() {
            createModalWindow(`/message_view.html?customerId=${customerId}`);
        };
    }

    // 4. 趋势分析面板
    const trendPanel = document.querySelector('.panel:has(#trendChart)');
    if (trendPanel) {
        trendPanel.style.cursor = 'pointer';
        trendPanel.onclick = function() {
            createModalWindow(`/health_main?customerId=${customerId}`);
        };
    }

    // 5. 人员管理面板
    const personnelPanel = document.querySelector('.panel:has(#departmentDistribution)');
    if (personnelPanel) {
        personnelPanel.style.cursor = 'pointer';
        personnelPanel.onclick = function() {
            createModalWindow(`/user_view.html?customerId=${customerId}`);
        };
    }

    // 6. 健康评分面板
    const scorePanel = document.querySelector('.panel:has(#healthScoreChart)');
    if (scorePanel) {
        scorePanel.style.cursor = 'pointer';
        scorePanel.onclick = function() {
            createModalWindow(`/user_health_data_analysis.html?customerId=${customerId}`);
        };
    }
}

// 修改初始化调用
document.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        globalCharts = initCharts(); // 存储图表实例
        refreshData(); // 初始加载数据
        // 每分钟刷新一次数据
        setInterval(refreshData, 60000);
    }, 100);
});

// 添加通用的创建模态窗口函数
function createModalWindow(url) {
    const modalContainer = document.createElement('div');
    modalContainer.className = 'modal-container';
    modalContainer.innerHTML = `
        <div class="modal-content">
            <button class="modal-close">✖</button>
            <div class="modal-header">
                <div class="filter-controls">
                    <div class="select-group">
                        <select id="modalDeptSelect" class="modal-select">
                            <option value="">选择部门</option>
                        </select>
                        <select id="modalUserSelect" class="modal-select">
                            <option value="">选择用户</option>
                        </select>
                    </div>
                    <div class="date-picker" style="display: none;">
                        <!-- 预留时间选择器位置 -->
                    </div>
                </div>
            </div>
            <iframe src="${url}" class="user-view-iframe"></iframe>
        </div>
    `;
    
    document.body.appendChild(modalContainer);
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .modal-header {
            position: absolute;
            top: 10px;
            right: 50px;
            z-index: 2;
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .filter-controls {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .select-group {
            display: flex;
            gap: 10px;
        }
        
        .modal-select {
            background: rgba(0, 21, 41, 0.8);
            border: 1px solid rgba(0, 228, 255, 0.3);
            border-radius: 4px;
            color: #fff;
            padding: 5px 10px;
            font-size: 14px;
            min-width: 120px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .modal-select:hover {
            border-color: rgba(0, 228, 255, 0.6);
        }
        
        .modal-select option {
            background: rgba(0, 21, 41, 0.9);
            color: #fff;
        }
        
        .user-view-iframe {
            margin-top: 10px;
        }
    `;
    document.head.appendChild(style);
    
    // 存储部门数据的映射关系
    const departmentMap = new Map();
    
    // 获取部门数据并填充选择框
    fetch(`/get_departments?orgId={{ customerId }}`)
        .then(response => response.json())
        .then(response => {
            if (response.success && response.data) {
                const deptSelect = document.getElementById('modalDeptSelect');
                
                // 递归添加部门选项并保存映射关系
                function addDepartmentOptions(departments, level = 0) {
                    departments.forEach(dept => {
                        const option = document.createElement('option');
                        option.value = dept.id;
                        const indent = '　'.repeat(level);
                        option.textContent = indent + dept.name;
                        deptSelect.appendChild(option);
                        
                        // 保存部门ID和名称的映射
                        departmentMap.set(dept.id.toString(), dept.name); // 确保key为字符串类型
                        
                        if (dept.children && dept.children.length > 0) {
                            addDepartmentOptions(dept.children, level + 1);
                        }
                    });
                }
                
                addDepartmentOptions(response.data);
            }
        })
        .catch(error => console.error('Error fetching departments:', error));
    
    // 部门选择变化时更新用户列表
    const deptSelect = document.getElementById('modalDeptSelect');
    const userSelect = document.getElementById('modalUserSelect');
    
    deptSelect.addEventListener('change', function() {
        const selectedDeptId = this.value;
        const selectedDeptName = selectedDeptId ? departmentMap.get(selectedDeptId.toString()) : ''; // 确保ID为字符串类型进行查找
        userSelect.innerHTML = '<option value="">选择用户</option>';
        
        if (selectedDeptId) {
            fetch(`/fetch_users?orgId=${selectedDeptId}`)
                .then(response => response.json())
                .then(data => {
                    if (data) {
                        data.forEach(user => {
                            const option = document.createElement('option');
                            option.value = user.id;
                            option.textContent = user.user_name;
                            // 将用户名存储在data属性中
                            option.dataset.userName = user.user_name;
                            userSelect.appendChild(option);
                        });
                        // 添加"全部用户"选项
                        const allOption = document.createElement('option');
                        allOption.value = 'all';
                        allOption.textContent = '全部用户';
                        userSelect.appendChild(allOption);
                    }
                })
                .catch(error => console.error('Error fetching users:', error));
        }
        
        // 更新 iframe URL，包含部门信息
        updateIframeUrl(selectedDeptId, selectedDeptName);
    });
    
    // 用户选择变化时触发事件
    userSelect.addEventListener('change', function() {
        const selectedDeptId = deptSelect.value;
        const selectedDeptName = selectedDeptId ? departmentMap.get(selectedDeptId.toString()) : ''; // 确保ID为字符串类型进行查找
        const selectedUserId = this.value;
        const selectedOption = this.options[this.selectedIndex];
        const selectedUserName = selectedOption.dataset.userName || '';
        
        // 更新 iframe URL，包含部门和用户信息
        updateIframeUrl(selectedDeptId, selectedDeptName, selectedUserId, selectedUserName);
    });
    
    // 更新 iframe URL 的辅助函数
    function updateIframeUrl(deptId, deptName, userId, userName) {
        const iframe = modalContainer.querySelector('iframe');
        let newUrl = new URL(iframe.src);
        
        // 保持原有的 customerId 参数
        const customerId = newUrl.searchParams.get('customerId');
        
        // 重置 URL 参数
        newUrl.search = '';
        
        // 重新添加所有必要的参数
        if (customerId) {
            newUrl.searchParams.set('customerId', customerId);
        }
        if (deptId) {
            newUrl.searchParams.set('deptId', deptId);
            newUrl.searchParams.set('deptName', encodeURIComponent(deptName || ''));
        }
        if (userId && userId !== 'all') {
            newUrl.searchParams.set('userId', userId);
            newUrl.searchParams.set('userName', encodeURIComponent(userName || ''));
        }
        
        // 更新 iframe 的 src
        iframe.src = newUrl.toString();
        
        // 如果页面有刷新数据的函数，尝试调用它
        try {
            iframe.contentWindow.fetchData && iframe.contentWindow.fetchData();
        } catch (e) {
            console.log('No fetchData function found in iframe or cross-origin restrictions apply');
        }
    }
    
    // 添加关闭事件
    const closeBtn = modalContainer.querySelector('.modal-close');
    closeBtn.onclick = () => {
        modalContainer.remove();
        style.remove();
    };
    
    // 点击遮罩层关闭
    modalContainer.onclick = (e) => {
        if (e.target === modalContainer) {
            modalContainer.remove();
            style.remove();
        }
    };
}

// 添加面板样式
const panelStyle = document.createElement('style');
panelStyle.textContent = `
    .panel {
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .panel:hover {
        border-color: rgba(0, 228, 255, 0.4);
        box-shadow: 0 0 15px rgba(0, 228, 255, 0.2);
    }

    .modal-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 9999;
        animation: fadeIn 0.3s ease;
    }

    .modal-content {
        position: relative;
        width: 90%;
        height: 90%;
        background: rgba(0, 21, 41, 0.95);
        border: 1px solid rgba(0, 228, 255, 0.3);
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 228, 255, 0.2);
        animation: slideIn 0.3s ease;
    }

    .modal-close {
        position: absolute;
        top: 10px;
        right: 10px;
        background: transparent;
        border: none;
        color: #00e4ff;
        font-size: 18px;
        cursor: pointer;
        z-index: 1;
        padding: 5px 10px;
        transition: all 0.3s ease;
    }

    .modal-close:hover {
        transform: scale(1.1);
        color: #ff4444;
    }

    .user-view-iframe {
        width: 100%;
        height: 100%;
        border: none;
        border-radius: 4px;
        background: rgba(1, 19, 38, 0.8);
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }

    @keyframes slideIn {
        from {
            transform: translateY(-20px);
            opacity: 0;
        }
        to {
            transform: translateY(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(panelStyle);

// 初始化告警信息图表 - 专业版
function initAlertChart(data) {
    console.log('initAlertChart 开始执行，数据:', data); // 调试信息
    
    const alertContainer = document.getElementById('alertList');
    if (!alertContainer) {
        console.warn('告警容器 #alertList 未找到');
        return;
    }

    // 清空容器并创建专业布局
    alertContainer.innerHTML = `
        <div style="position: relative; height: 100%; padding: 8px;">
            <!-- 告警状态总览 -->
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 6px 10px; background: rgba(0,228,255,0.1); border-radius: 6px; border-left: 4px solid #00e4ff;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div class="alert-stat-item">
                        <span style="color: #ff4444; font-size: 18px; font-weight: bold;" id="criticalCount">0</span>
                        <span style="color: #fff; font-size: 12px; margin-left: 4px;">严重</span>
                    </div>
                    <div class="alert-stat-item">
                        <span style="color: #ffbb00; font-size: 16px; font-weight: bold;" id="mediumCount">0</span>
                        <span style="color: #fff; font-size: 12px; margin-left: 4px;">中等</span>
                    </div>
                    <div class="alert-stat-item">
                        <span style="color: #ff6666; font-size: 14px; font-weight: bold;" id="pendingCount">0</span>
                        <span style="color: #fff; font-size: 12px; margin-left: 4px;">待处理</span>
                    </div>
                </div>
                <div style="background: rgba(255,68,68,0.2); padding: 4px 8px; border-radius: 12px; animation: pulse 2s infinite;" id="alertBadge">
                    <span style="color: #ff4444; font-size: 11px; font-weight: bold;">🚨 实时监控</span>
                </div>
            </div>
            
            <!-- 图表区域 -->
            <div class="alert-charts-grid">
                <div id="alertTypeChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                    <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">告警类型分布</div>
                </div>
                <div id="alertLevelChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                    <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">严重程度分析</div>
                </div>
                <div id="alertStatusChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                    <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">处理状态</div>
                </div>
                <div id="alertTrendChart" style="background: rgba(0,21,41,0.4); border: 1px solid rgba(0,228,255,0.3); border-radius: 6px; position: relative;">
                    <div style="position: absolute; top: 5px; left: 8px; color: #00e4ff; font-size: 12px; font-weight: bold; z-index: 10;">24小时趋势</div>
                </div>
            </div>
        </div>
    `;

    const alertInfo = data.alert_info || {};
    const alerts = alertInfo.alerts || [];
    
    console.log('告警信息:', alertInfo); // 调试信息
    console.log('告警列表:', alerts); // 调试信息
    
    // 更新统计数据
    const criticalCount = alertInfo.alertLevelCount?.critical || 0;
    const mediumCount = alertInfo.alertLevelCount?.medium || 0;
    const pendingCount = alertInfo.alertStatusCount?.pending || 0;
    
    document.getElementById('criticalCount').textContent = criticalCount;
    document.getElementById('mediumCount').textContent = mediumCount;
    document.getElementById('pendingCount').textContent = pendingCount;
    
    // 更新告警徽章
    const badge = document.getElementById('alertBadge');
    if (criticalCount > 0) {
        badge.innerHTML = '<span style="color: #ff4444; font-size: 11px; font-weight: bold;">🔴 严重告警</span>';
        badge.style.background = 'rgba(255,68,68,0.3)';
    } else if (pendingCount > 0) {
        badge.innerHTML = '<span style="color: #ffbb00; font-size: 11px; font-weight: bold;">⚠️ 待处理</span>';
        badge.style.background = 'rgba(255,187,0,0.3)';
    } else {
        badge.innerHTML = '<span style="color: #00ff9d; font-size: 11px; font-weight: bold;">✅ 正常</span>';
        badge.style.background = 'rgba(0,255,157,0.3)';
    }

    // 1. 告警类型分布图 - 水平条形图（优化版）
    const typeChart = echarts.init(document.getElementById('alertTypeChart'));
    const alertTypes = Object.keys(alertInfo.alertTypeCount || {});
    const alertValues = Object.values(alertInfo.alertTypeCount || {});

    // 如果没有数据，显示默认数据
    const hasTypeData = alertTypes.length > 0 && alertValues.some(v => v > 0);
    let displayTypes = hasTypeData ? alertTypes : ['heart_rate', 'blood_pressure', 'temperature'];
    let displayValues = hasTypeData ? alertValues : [0, 0, 0];

    // 限制显示数量，防止图表变形，由于高度增加可以显示更多类型
    const MAX_DISPLAY_TYPES = 8; // 从6增加到8种类型，充分利用增加的高度空间
    if (displayTypes.length > MAX_DISPLAY_TYPES) {
        // 按数值排序，取前8个
        const sortedData = displayTypes.map((type, index) => ({
            type: type,
            value: displayValues[index]
        })).sort((a, b) => b.value - a.value);
        
        displayTypes = sortedData.slice(0, MAX_DISPLAY_TYPES).map(item => item.type);
        displayValues = sortedData.slice(0, MAX_DISPLAY_TYPES).map(item => item.value);
        
        // 如果有更多类型，将剩余的合并为"其他"
        if (sortedData.length > MAX_DISPLAY_TYPES) {
            const otherValue = sortedData.slice(MAX_DISPLAY_TYPES).reduce((sum, item) => sum + item.value, 0);
            displayTypes.push('others');
            displayValues.push(otherValue);
        }
    }

    const typeColors = {
        'temperature': '#ffd700',
        'stress': '#ff8800', 
        'heart_rate': '#00e4ff',
        'blood_pressure': '#ffbb00',
        'blood_oxygen': '#ff6666',
        'others': '#888888'
    };

    const typeOption = {
        tooltip: {
            trigger: 'axis',
            backgroundColor: 'rgba(0,21,41,0.95)',
            borderColor: '#00e4ff',
            borderWidth: 1,
            textStyle: { color: '#fff', fontSize: 11 },
            formatter: function(params) {
                if (!params || !params[0]) return '';
                const data = params[0];
                const total = displayValues.reduce((a, b) => a + b, 0);
                const percent = total > 0 ? (data.value / total * 100).toFixed(1) : 0;
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
            data: ['心率', '血压', '压力指数', '距离', '卡路里', '步数', '预测值'],
            textStyle: { color: '#fff' },
            top: 30
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
            xAxis: {
                type: 'category',
            boundaryGap: false,
            data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '预测'],
            axisLabel: { color: '#fff' },
            axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
            },
            yAxis: {
                type: 'value',
            axisLabel: { color: '#fff' },
            splitLine: {
                lineStyle: {
                    color: 'rgba(255,255,255,0.1)',
                    type: 'dashed'
                }
            }
        },
        series: [
            {
                name: '心率',
                type: 'line',
                smooth: true,
                data: [75, 72, 78, 85, 80, 75, 77],
                itemStyle: { color: '#ff4444' }
            },
            {
                name: '血压',
                type: 'line',
                smooth: true,
                data: [120, 118, 122, 125, 121, 119, 120],
                itemStyle: { color: '#00e4ff' }
            },
            {
                name: '压力指数',
                type: 'line',
                smooth: true,
                data: [45, 48, 52, 55, 50, 47, 49],
                itemStyle: { color: '#ffbb00' }
            },
            {
                name: '距离',
                type: 'line',
                smooth: true,
                data: [2.1, 2.3, 2.8, 3.2, 3.5, 3.8, 4.0],
                itemStyle: { color: '#00ff9d' }
            },
            {
                name: '卡路里',
                type: 'line',
                smooth: true,
                data: [150, 180, 220, 280, 320, 350, 380],
                itemStyle: { color: '#ff7777' }
            },
            {
                name: '步数',
                type: 'line',
                smooth: true,
                data: [2000, 2500, 3000, 3800, 4200, 4500, 4800],
                itemStyle: { color: '#7777ff' }
            }
        ]
    };

    // 为每个系列添加预测区域
    trendOption.series.forEach(series => {
        const lastIndex = series.data.length - 1;
        series.markArea = {
                itemStyle: {
                color: 'rgba(0, 228, 255, 0.1)'
            },
            data: [[{
                xAxis: trendOption.xAxis.data[lastIndex - 1]
            }, {
                xAxis: trendOption.xAxis.data[lastIndex]
            }]]
        };
    });

    trendChart.setOption(trendOption);
    return trendChart;
}

// 人员管理面板交互函数
function showPersonnelDetails() {
    showCustomAlert('人员详情功能：显示完整的人员管理统计信息');
}

function filterByDepartment() {
    showCustomAlert('部门筛选功能：按部门查看人员分布详情');
}

function filterByOnlineStatus() {
    showCustomAlert('在线状态筛选功能：显示在线/离线人员列表');
}

function filterByDeviceStatus() {
    showCustomAlert('设备状态筛选功能：显示已绑定/未绑定设备人员');
}

function filterByAlertStatus() {
    showCustomAlert('告警状态筛选功能：显示有告警的人员列表');
}

// 显示部门详情
function showDepartmentDetails(deptName, userCount) {
    const modal = document.createElement('div');
    modal.className = 'modal-container';
    modal.innerHTML = `
        <div class="modal-content" style="width: 60%; height: 70%;">
            <button class="modal-close">✕</button>
            <h3 style="color: #00e4ff; margin-bottom: 20px; text-align: center; font-size: 18px;">📊 ${deptName} 部门详情</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; padding: 20px;">
                <div style="background: rgba(0,228,255,0.1); padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="color: #00e4ff; font-size: 24px; font-weight: bold;">${userCount}</div>
                    <div style="color: #fff; margin-top: 5px;">总人数</div>
                </div>
                <div style="background: rgba(0,255,157,0.1); padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="color: #00ff9d; font-size: 24px; font-weight: bold;">${Math.floor(userCount * 0.8)}</div>
                    <div style="color: #fff; margin-top: 5px;">在线人数</div>
                </div>
                <div style="background: rgba(255,187,0,0.1); padding: 20px; border-radius: 8px; text-align: center;">
                    <div style="color: #ffbb00; font-size: 24px; font-weight: bold;">${Math.floor(userCount * 0.9)}</div>
                    <div style="color: #fff; margin-top: 5px;">设备绑定</div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 20px; color: #7ecfff;">
                点击可查看该部门的详细人员列表和设备状态
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 关闭事件
    modal.querySelector('.modal-close').onclick = () => modal.remove();
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
}

// 显示状态详情
function showStatusDetails(statusName, statusValue) {
    const statusMap = {
        '在线': '当前在线的用户列表',
        '离线': '当前离线的用户列表',
        '绑定': '已绑定设备的用户',
        '未绑定': '未绑定设备的用户',
        '告警': '当前有告警的用户',
        '正常': '状态正常的用户'
    };
    
    const modal = document.createElement('div');
    modal.className = 'modal-container';
    modal.innerHTML = `
        <div class="modal-content" style="width: 70%; height: 80%;">
            <button class="modal-close">✕</button>
            <h3 style="color: #00e4ff; margin-bottom: 20px; text-align: center; font-size: 18px;">📋 ${statusName}用户详情</h3>
            <div style="background: rgba(0,228,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center;">
                <div style="color: #00e4ff; font-size: 28px; font-weight: bold;">${statusValue}</div>
                <div style="color: #fff; margin-top: 5px;">${statusMap[statusName] || '用户统计'}</div>
            </div>
            <div style="color: #7ecfff; text-align: center; padding: 40px;">
                <div style="font-size: 48px; margin-bottom: 15px;">👥</div>
                <div style="font-size: 16px;">详细用户列表功能开发中...</div>
                <div style="font-size: 12px; margin-top: 10px; color: rgba(255,255,255,0.5);">将显示具体的用户信息、设备状态和健康数据</div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 关闭事件
    modal.querySelector('.modal-close').onclick = () => modal.remove();
    modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
    };
}

  

  $(document).ready(function() {
    // 获取部门数据
    $.ajax({
        url: `/get_departments?orgId={{ customerId }}`,
        method: 'GET',
        success: function(response) {
            console.log('response', response);
            if (response.success && response.data) {
                updateDepartmentSelect(response.data);
            } else {
                console.error('Invalid response format:', response);
            }
        },
        error: function(error) {
            console.error('Failed to fetch departments:', error);
        }
    });

    // 部门选择变化时更新用户列表
    $('#deptSelect').change(function() {
        const selectedDeptId = $(this).val();
        currentDept=selectedDeptId
        console.log('currentDept',currentDept);
        updateUsers(selectedDeptId);
    });

    // 用户选择变化时刷新地图
    $('#userSelect').change(function() {
        currentUser=$(this).val()
       //console.log('currentUser',currentUser);
        // 调用 initializeMap 刷新数据
        //initializeMap(selectedDeptId, selectedUserId);
        updateMapData(lastTotalInfo);
    });



    // 更新部门选择框
    function updateDepartmentSelect(departments) {
        const deptSelect = document.getElementById('deptSelect');
        if (!deptSelect) return;

        // 清空现有选项
        deptSelect.innerHTML = '<option value="">选择部门</option>';

        // 递归添加部门选项
        function addDepartmentOptions(departments, level = 0) {
            departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept.id;
                const indent = '　'.repeat(level);
                option.textContent = indent + dept.name;
                deptSelect.appendChild(option);

                if (dept.children && dept.children.length > 0) {
                    addDepartmentOptions(dept.children, level + 1);
                }
            });
        }

        addDepartmentOptions(departments);
        deptSelect.style.fontFamily = 'monospace';
    }

    // 更新用户选择框
    async function updateUsers(deptId) {
        try {
            const userSelect = document.getElementById('userSelect');
            if (!userSelect) return;

            // 清空现有选项
            userSelect.innerHTML = '<option value="">选择用户</option>';

            if (!deptId) return;

            const response = await fetch(`/fetch_users?orgId=${deptId}`);
            const data = await response.json();
            console.log('updateUsers.data', data);

            if (data) {
                data.forEach(user => {
                    const option = document.createElement('option');
                    option.value = user.id;
                    let displayText = user.user_name;
                    // 如果有职位信息，添加到显示文本中
                    if (user.position) {
                        displayText += ` (${user.position})`;
                    }
                    option.textContent = displayText;
                    userSelect.appendChild(option);
                });
                const option = document.createElement('option');
                option.value = 'all';
                option.textContent = '全部用户';
                userSelect.appendChild(option);
            }
        } catch (error) {
            console.error('获取用户列表失败:', error);
        }
    }

    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        .filter-select {
            font-family: monospace;
            white-space: pre;
            width: 100%;
            padding: 8px;
            margin-bottom: 10px;
            background: rgba(0, 0, 0, 0.3);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 4px;
        }
        
        .filter-select option {
            font-family: monospace;
            white-space: pre;
            background: #1a1a1a;
            color: #fff;
        }

        .filter-panel {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            background: rgba(0, 21, 41, 0.9);
            backdrop-filter: blur(8px);
            padding: 15px;
            border-radius: 8px;
            width: 280px;
            border: 1px solid rgba(0, 228, 255, 0.2);
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
        }

        .filter-container {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .filter-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 228, 255, 0.2);
        }

        .filter-header span {
            color: #00e4ff;
            font-size: 14px;
        }

        .filter-toggle {
            background: transparent;
            border: none;
            color: #00e4ff;
            cursor: pointer;
            padding: 5px;
            transition: all 0.3s ease;
        }

        .filter-toggle:hover {
            transform: scale(1.1);
        }
    `;
    document.head.appendChild(style);
  });


// 全局变量
let infoPanelVisible = false;
let lastTotalInfo = null;

// 切换信息面板显示状态
function toggleInfoPanel() {
  const panel = document.getElementById('infoPanel');
  infoPanelVisible = !infoPanelVisible;
  panel.style.display = infoPanelVisible ? 'block' : 'none';
}

// 添加键盘快捷键切换信息面板
document.addEventListener('keydown', (e) => {
  if (e.key === 'i' && e.ctrlKey) {
    toggleInfoPanel();
  }
});

function openInfoPanelWithAlertId(alertId) {
  infoPanelVisible = true;
  document.getElementById('infoPanel').style.display = 'block';
  updateInfoPanel(lastTotalInfo, alertId);
}
function showCustomMapInfo(f){
  removeCustomMapInfo();
  const d=f.properties,toStr=x=>x===undefined||x===null?'':String(x);
  const get=(...k)=>k.map(x=>d[x]).find(x=>x!==undefined&&x!==null&&x!=='')||'-';
  // 判断是否为告警点：有alert_id/alertId且有alert_type/alertType，且type不是health
  const isAlert=!!(get('alert_id','alertId')&&get('alert_type','alertType')&&d.type!=='health');
  console.log('showCustomMapInfo.d',d);
  console.log('showCustomMapInfo.isAlert',isAlert);
  const level=get('severity_level','severityLevel');
  const levelColor=level==='critical'?'#ff4d4f':level==='high'?'#ffbb00':'#ffe066';
  const avatarUrl=d.avatar||'/static/images/avatar-tech.svg';
  const div=document.createElement('div');
  div.className='custom-map-info';
  div.style.cssText='position:absolute;z-index:9999;min-width:360px;max-width:420px;background:rgba(10,24,48,0.98);border:1.5px solid #00e4ff;border-radius:16px;box-shadow:0 0 24px #00e4ff44;padding:22px 28px 18px 28px;color:#fff;top:120px;left:50%;transform:translateX(-50%);font-size:15px;font-family:Roboto,Arial,sans-serif;backdrop-filter:blur(6px);';
  // 获取位置信息
      const longitude = get('longitude');
      const latitude = get('latitude');
      if(longitude && latitude){
        reverseGeocode(longitude, latitude)
          .then(address => {
            const locationInfo = document.getElementById('locationInfo');
            if(locationInfo){
              locationInfo.textContent = address || '未知位置';
            }
          })
          .catch(error => {
            console.error('获取位置信息失败:', error);
            const locationInfo = document.getElementById('locationInfo');
            if(locationInfo){
              locationInfo.textContent = '获取位置信息失败';
            }
          });
      }
  if(isAlert){
    
    // 告警点内容
    div.innerHTML=`
      <div style="display:flex;align-items:center;gap:18px;margin-bottom:12px;">
        <img src="${avatarUrl}" style="width:56px;height:56px;border-radius:50%;border:2px solid #00e4ff;box-shadow:0 0 8px #00e4ff44;object-fit:cover;background:#001529;">
        <div>
          <div style="font-size:18px;font-weight:700;letter-spacing:1px;">${get('dept_name','deptName')}</div>
          <div style="font-size:16px;color:#00e4ff;font-weight:500;margin-top:2px;">${get('user_name','userName')}</div>
        </div>
      </div>
    
      <div style="display:flex;gap:18px;flex-wrap:wrap;margin-bottom:8px;">
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
        <span style="color:#7ecfff;margin-left:18px;">血压：</span>${get('pressureHigh','pressure_high')}/${get('pressureLow','pressure_low')} mmHg
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">血氧：</span>${get('bloodOxygen','blood_oxygen')}
        <span style="color:#7ecfff;margin-left:18px;">体温：</span>${get('temperature','temp')} ℃
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">步数：</span>${get('step','steps')} 步
        <span style="color:#7ecfff;margin-left:18px;">卡路里：</span>${get('calorie','calories')} kcal
        <span style="color:#7ecfff;margin-left:18px;">距离：</span>${get('distance','distance')} 米
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">压力：</span>${get('stress','pressure')}
        <span style="color:#7ecfff;margin-left:18px;">睡眠：</span>${get('sleepData','scientificSleepData')}
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">位置信息：</span><span id="locationInfo">正在获取...</span>
      </div>
      <div style="margin-bottom:8px;">
        <span style="color:#7ecfff;">采集时间：</span>${get('timestamp')}
      </div>
      <div style="display:flex;gap:18px;align-items:center;">
        <span style="flex:1"></span>
        <span style="color:#00e4ff;cursor:pointer;font-size:22px;font-weight:700;" onclick="removeCustomMapInfo()">×</span>
      </div>
    `;
    document.body.appendChild(div);
    
    // 获取位置信息
    const longitude = get('longitude');
    const latitude = get('latitude');
    if(longitude && latitude){
      reverseGeocode(longitude, latitude)
        .then(address => {
          const locationInfo = document.getElementById('locationInfo');
          if(locationInfo){
            locationInfo.textContent = address || '未知位置';
          }
        })
        .catch(error => {
          console.error('获取位置信息失败:', error);
          const locationInfo = document.getElementById('locationInfo');
          if(locationInfo){
            locationInfo.textContent = '获取位置信息失败';
          }
        });
    }
  }
}
function showHealthProfile(healthId){
  fetch(`/fetchHealthDataById?id=${healthId}`).then(r=>r.json()).then(j=>{
    if(!j.success||!j.data)return showCustomAlert('无健康数据');
    const d=j.data,g=(...k)=>k.map(x=>d[x]).find(x=>x!==undefined&&x!==null&&x!=='')||'-';
    let sleepStr=g('sleepData','scientificSleepData'),sleep='-';
    try{
      if(typeof sleepStr==='string'&&sleepStr.startsWith('{')){
        const o=JSON.parse(sleepStr),arr=o.data||[];
        if(arr.length){
          const s=arr[0],fmt=m=>m?`${Math.floor(m/60)}h${m%60}m`:'-';
          sleep=`总:${fmt(s.total)} 深:${fmt(s.deep)} 浅:${fmt(s.light)} 醒:${fmt(s.awake)}`;
        }
      }
    }catch(e){sleep='-';}
    const html=`
      <div style="font-size:20px;font-weight:700;color:#00e4ff;margin-bottom:12px;text-align:center;">健康数据</div>
      <div style="display:grid;grid-template-columns:100px 1fr;row-gap:8px;column-gap:10px;">
        <span>心率</span><span style="text-align:right;font-weight:600;color:#7ecfff;">${g('heartRate','heart_rate')||'-'} <span style="color:#888;font-weight:400;">bpm</span></span>
        <span>血压</span><span style="text-align:right;">${(g('pressureHigh','pressure_high')||'-')+'/'+(g('pressureLow','pressure_low')||'-')} <span style="color:#888;font-weight:400;">mmHg</span></span>
        <span>血氧</span><span style="text-align:right;">${g('bloodOxygen','blood_oxygen')||'-'} <span style="color:#888;font-weight:400;">%</span></span>
        <span>体温</span><span style="text-align:right;">${g('temperature','temp')||'-'} <span style="color:#888;font-weight:400;">℃</span></span>
        <span>步数</span><span style="text-align:right;">${g('step','steps')||'-'} <span style="color:#888;font-weight:400;">步</span></span>
        <span>距离</span><span style="text-align:right;">${g('distance','distance')||'-'} <span style="color:#888;font-weight:400;">米</span></span>
        <span>卡路里</span><span style="text-align:right;">${g('calorie','calories')||'-'} <span style="color:#888;font-weight:400;">kcal</span></span>
        <span>压力</span><span style="text-align:right;">${g('stress','pressure')||'-'} <span style="color:#888;font-weight:400;">分</span></span>
        <span>睡眠</span><span style="text-align:right;">${sleep}</span>
        <span>采集时间</span><span style="text-align:right;">${g('timestamp')||'-'}</span>
      </div>
    `;
    const m=document.createElement('div');
    m.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(0,21,41,0.7);z-index:10000;display:flex;align-items:center;justify-content:center;';
    m.innerHTML=`<div style="background:rgba(10,24,48,0.98);border-radius:14px;box-shadow:0 0 24px #00e4ff44;padding:32px 38px;min-width:320px;max-width:420px;color:#fff;position:relative;">
      <span style="position:absolute;right:18px;top:12px;cursor:pointer;font-size:22px;color:#00e4ff;" onclick="this.parentNode.parentNode.remove()">×</span>
      ${html}
    </div>`;
    document.body.appendChild(m);
  }).catch(()=>showCustomAlert('获取健康数据失败'));
}

function removeCustomMapInfo(){const old=document.querySelector('.custom-map-info');if(old)old.remove();}

function filterData(data){
    //console.log('filterData.data',currentDept,currentUser);

    //console.log('filterData.data.healthData',data.healthData);
  const toStr=x=>x===undefined||x===null?'':String(x);
  const dept=toStr(currentDept),user=toStr(currentUser);
  const alerts=(data.alert_info?.alerts||[]).filter(a=>
    (!dept||[a.dept_id,a.deptId].some(v=>toStr(v)===dept))&&
    (!user||[a.user_id,a.userId].some(v=>toStr(v)===user))&&
    (['pending','1'].includes(toStr(a.alert_status||a.status)))
  );
  const healths=(data.health_data?.healthData||[]).filter(h=>
    (!dept||[h.dept_id,h.deptId].some(v=>toStr(v)===dept))&&
    (!user||[h.user_id,h.userId].some(v=>toStr(v)===user))
  );
  //console.log('filterData.alerts',alerts);
  //console.log('filterData.healths',healths);
  return {alerts,healths};
}

window.updateMapData = function(data){
    //console.log('updateMapData.data',data);
  if(!data||!map||!loca)return;
  const {alerts,healths}=filterData(data);
  const f=[];
  // 处理告警数据
  alerts.forEach(a=>{
    if((a.longitude||a.longitude===0)&&(a.latitude||a.latitude===0)){
      f.push({
        type:'Feature',
        geometry:{type:'Point',coordinates:[+a.longitude,+a.latitude]},
        properties:{
          ...a,
          alert_id: a.alert_id,
          alert_type: a.alert_type,
          alert_status: a.alert_status,
          severity_level: a.severity_level,
          dept_name: a.dept_name,
          user_name: a.user_name,
          health_id: a.health_id,
          device_sn: a.device_sn,
          alert_timestamp: a.alert_timestamp,
          type: 'alert'
        }
      });
    }
  });
  // 处理健康数据
  healths.forEach(h=>{
    if((h.longitude||h.longitude===0)&&(h.latitude||h.latitude===0)){
      f.push({
        type:'Feature',
        geometry:{type:'Point',coordinates:[+h.longitude,+h.latitude]},
        properties:{
          ...h,
          dept_name: h.deptName,
          user_name: h.userName,
          heart_rate: h.heartRate,
          blood_oxygen: h.bloodOxygen,
          temperature: h.temperature,
          pressure_high: h.pressureHigh,
          pressure_low: h.pressureLow,
          step: h.step,
          stress: h.stress,
          device_sn: h.deviceSn,
          timestamp: h.timestamp,
          avatar: h.avatar,
          sleepData: h.sleepData,
          timestamp: h.timestamp,
          type: 'health'
        }
      });
    }
  });
  
  const geoJSON={type:'FeatureCollection',features:f};
  const criticalAlerts={type:'FeatureCollection',features:geoJSON.features.filter(f=>f.properties.severity_level==='critical')};
  const highAlerts={type:'FeatureCollection',features:geoJSON.features.filter(f=>f.properties.severity_level==='high'||f.properties.severity_level==='medium')};
  const healthData={type:'FeatureCollection',features:geoJSON.features.filter(f=>f.properties.type==='health')};
  
  if(breathRed)breathRed.setSource(new Loca.GeoJSONSource({data:criticalAlerts})); // 变量检查
  if(breathYellow)breathYellow.setSource(new Loca.GeoJSONSource({data:highAlerts})); // 变量检查
  if(breathGreen)breathGreen.setSource(new Loca.GeoJSONSource({data:healthData})); // 变量检查
  
  // 设置地图中心
  let center=null;
  const getCoord=f=>f&&f.geometry&&f.geometry.coordinates;
  const findFirst=(arr,cond)=>{for(let i=0;i<arr.length;i++)if(cond(arr[i]))return arr[i];return null;};
  const cAlert=findFirst(geoJSON.features,f=>f.properties.type==='alert'&&['critical','high','medium'].includes(f.properties.severity_level));
  const cHealth=findFirst(geoJSON.features,f=>f.properties.type==='health');
  if(cAlert)center=getCoord(cAlert);
  else if(cHealth)center=getCoord(cHealth);
  if(center&&center.length>=2)map.setCenter([center[0],center[1]]);
  else if(navigator.geolocation){
    navigator.geolocation.getCurrentPosition(pos=>{
      map.setCenter([pos.coords.longitude,pos.coords.latitude]);
    });
  }
}

// 健康数据统计计算函数
function calculateHealthStats(metrics) {
  const stats = {
    healthScore: 0,
    normalCount: 0,
    riskCount: 0,
    avgHeartRate: 0,
    avgBloodOxygen: 0,
    avgTemperature: 0,
    avgSteps: 0
  };
  
  if (!metrics || metrics.length === 0) return stats;
  
  let totalScore = 0, validMetrics = 0;
  
  metrics.forEach(metric => {
    const values = metric.values.filter(v => v !== null && v !== undefined);
    if (values.length === 0) return;
    
    const avg = values.reduce((a, b) => a + b, 0) / values.length;
    
    switch(metric.name) {
      case '心率':
        stats.avgHeartRate = Math.round(avg);
        const heartScore = avg >= 60 && avg <= 100 ? 85 : (avg < 60 ? 70 : 60); // 正常范围评分
        totalScore += heartScore;
        if (heartScore >= 80) stats.normalCount++; else stats.riskCount++;
        validMetrics++;
        break;
      case '血氧':
        stats.avgBloodOxygen = Math.round(avg);
        const oxygenScore = avg >= 95 ? 90 : (avg >= 90 ? 75 : 50);
        totalScore += oxygenScore;
        if (oxygenScore >= 80) stats.normalCount++; else stats.riskCount++;
        validMetrics++;
        break;
      case '体温':
        stats.avgTemperature = avg.toFixed(1);
        const tempScore = avg >= 36.1 && avg <= 37.2 ? 88 : 65;
        totalScore += tempScore;
        if (tempScore >= 80) stats.normalCount++; else stats.riskCount++;
        validMetrics++;
        break;
      case '步数':
        stats.avgSteps = Math.round(avg);
        const stepScore = avg >= 8000 ? 85 : (avg >= 5000 ? 70 : 55);
        totalScore += stepScore;
        if (stepScore >= 80) stats.normalCount++; else stats.riskCount++;
        validMetrics++;
        break;
    }
  });
  
  stats.healthScore = validMetrics > 0 ? Math.round(totalScore / validMetrics) : 0;
  return stats;
}

// 更新健康统计UI
function updateHealthStats(stats) {
  try {
    document.getElementById('healthScore').textContent = stats.healthScore;
    document.getElementById('normalCount').textContent = stats.normalCount;
    document.getElementById('riskCount').textContent = stats.riskCount;
    document.getElementById('avgHeartRate').textContent = stats.avgHeartRate;
    document.getElementById('avgBloodOxygen').textContent = stats.avgBloodOxygen + '%';
    document.getElementById('avgTemperature').textContent = stats.avgTemperature + '°C';
    document.getElementById('avgSteps').textContent = stats.avgSteps;
  } catch (e) {
    console.warn('更新健康统计UI失败:', e);
  }
}

// 计算雷达图数据
function calculateRadarData(metrics) {
  const indicators = [];
  const values = [];
  
  const metricMap = {
    '心率': { max: 100, unit: 'bpm' },
    '血氧': { max: 100, unit: '%' },
    '体温': { max: 100, unit: '°C' },
    '步数': { max: 100, unit: '步' },
    '压力': { max: 100, unit: '级' },
    '睡眠': { max: 100, unit: '小时' },
    '卡路里': { max: 100, unit: 'kcal' },
    '血压': { max: 100, unit: 'mmHg' }
  };
  
  metrics.forEach(metric => {
    const config = metricMap[metric.name];
    if (!config) return;
    
    const validValues = metric.values.filter(v => v !== null && v !== undefined);
    if (validValues.length === 0) return;
    
    const avg = validValues.reduce((a, b) => a + b, 0) / validValues.length;
    
    // 根据指标类型计算健康评分
    let score = 0;
    switch(metric.name) {
      case '心率':
        score = avg >= 60 && avg <= 100 ? 85 : (avg < 60 ? 70 : 60);
        break;
      case '血氧':
        score = avg >= 95 ? 90 : (avg >= 90 ? 75 : 50);
        break;
      case '体温':
        score = avg >= 36.1 && avg <= 37.2 ? 88 : 65;
        break;
      case '步数':
        score = avg >= 8000 ? 85 : (avg >= 5000 ? 70 : 55);
        break;
      case '压力':
        score = avg <= 3 ? 85 : (avg <= 5 ? 70 : 50);
        break;
      case '睡眠':
        score = avg >= 7 ? 85 : (avg >= 6 ? 70 : 55);
        break;
      default:
        score = Math.min(90, Math.max(50, 100 - (avg * 0.5))); // 默认计算
    }
    
    indicators.push({
      name: metric.name,
      max: 100,
      min: 0
    });
    
    values.push(Math.round(score));
  });
  
  return { indicators, values };
}

// 显示默认健康数据
function showDefaultHealthData() {
    // 更新统计数据
    document.getElementById('healthScore').textContent = '85';
    document.getElementById('normalCount').textContent = '6';
    document.getElementById('riskCount').textContent = '2';
    
    // 显示默认趋势图
    const trendChart = echarts.init(document.getElementById('trendChart'));
    
    const defaultDates = ['05-20', '05-21', '05-22', '05-23', '05-24', '05-25', '05-26'];
    const defaultOption = {
      backgroundColor: 'transparent',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10,24,48,0.98)',
        borderColor: '#00e4ff',
        textStyle: { color: '#fff', fontSize: 10 }
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
          lineStyle: { color: '#ff4444' },
          itemStyle: { color: '#ff4444' }
        },
        {
          name: '血氧',
                    type: 'line',
          data: [98, 97, 99, 98, 97, 98, 99],
          smooth: true,
          lineStyle: { color: '#00ff9d' },
          itemStyle: { color: '#00ff9d' }
        },
        {
          name: '体温',
          type: 'line',
          data: [36.5, 36.7, 36.4, 36.6, 36.8, 36.5, 36.6],
          smooth: true,
          lineStyle: { color: '#ffbb00' },
          itemStyle: { color: '#ffbb00' }
        }
      ]
    };
    
    trendChart.setOption(defaultOption);
}

// 交互功能函数
function showHealthDetails() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('健康详情功能开发中...\n\n当前显示的是7天健康数据汇总');
    return;
  }
  
  const { health_summary, risk_alerts } = data;
  let message = `健康数据详情报告\n\n`;
  message += `📊 综合评分: ${health_summary.overall_score}分\n`;
  message += `✅ 正常指标: ${health_summary.normal_indicators}项\n`;
  message += `⚠️ 风险指标: ${health_summary.risk_indicators}项\n`;
  message += `👥 活跃用户: ${health_summary.active_users}/${health_summary.total_users}人\n\n`;
  
  if (risk_alerts && risk_alerts.length > 0) {
    message += `🚨 风险预警:\n`;
    risk_alerts.slice(0, 3).forEach(alert => {
      message += `• ${alert.message}\n`;
    });
  } else {
    message += `✨ 暂无风险预警，整体健康状况良好`;
  }
  
  alert(message);
}

function filterByHeartRate() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('心率筛选功能：显示心率异常的时间段和用户');
    return;
  }
  
  const heartRateMetric = data.metrics.find(m => m.name === '心率');
  if (heartRateMetric) {
    const abnormalDays = heartRateMetric.daily_stats ? 
      heartRateMetric.daily_stats.filter(d => d.status === 'risk').length : 0;
    alert(`心率分析结果\n\n平均心率: ${heartRateMetric.avg_value}bpm\n异常天数: ${abnormalDays}天\n正常范围: ${heartRateMetric.normal_range[0]}-${heartRateMetric.normal_range[1]}bpm`);
  } else {
    alert('暂无心率数据');
  }
}

function filterByBloodOxygen() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('血氧筛选功能：显示血氧偏低的时间段和用户');
    return;
  }
  
  const oxygenMetric = data.metrics.find(m => m.name === '血氧');
  if (oxygenMetric) {
    const abnormalDays = oxygenMetric.daily_stats ? 
      oxygenMetric.daily_stats.filter(d => d.status === 'risk').length : 0;
    alert(`血氧分析结果\n\n平均血氧: ${oxygenMetric.avg_value}%\n异常天数: ${abnormalDays}天\n正常范围: ${oxygenMetric.normal_range[0]}-${oxygenMetric.normal_range[1]}%`);
  } else {
    alert('暂无血氧数据');
  }
}

function filterByTemperature() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('体温筛选功能：显示体温异常的时间段和用户');
    return;
  }
  
  const tempMetric = data.metrics.find(m => m.name === '体温');
  if (tempMetric) {
    const abnormalDays = tempMetric.daily_stats ? 
      tempMetric.daily_stats.filter(d => d.status === 'risk').length : 0;
    alert(`体温分析结果\n\n平均体温: ${tempMetric.avg_value}°C\n异常天数: ${abnormalDays}天\n正常范围: ${tempMetric.normal_range[0]}-${tempMetric.normal_range[1]}°C`);
  } else {
    alert('暂无体温数据');
  }
}

function filterBySteps() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('步数筛选功能：显示运动量不足的用户');
    return;
  }
  
  const stepsMetric = data.metrics.find(m => m.name === '步数');
  if (stepsMetric) {
    const lowActivityDays = stepsMetric.daily_stats ? 
      stepsMetric.daily_stats.filter(d => d.value && d.value < 5000).length : 0;
    alert(`步数分析结果\n\n平均步数: ${stepsMetric.avg_value}步\n运动不足天数: ${lowActivityDays}天\n建议目标: ${stepsMetric.normal_range[0]}步以上`);
  } else {
    alert('暂无步数数据');
  }
}

function showMetricDetails(metricName, value, date) {
  const data = window.healthAnalysisData;
  if (!data) {
    alert(`指标详情\n\n指标: ${metricName}\n数值: ${value}\n日期: ${date}\n\n点击可查看该指标的详细分析和建议`);
    return;
  }
  
  const metric = data.metrics.find(m => m.name === metricName);
  if (metric) {
    const dayData = metric.daily_stats ? metric.daily_stats.find(d => d.date === date) : null;
    let message = `${metricName}详细信息\n\n`;
    message += `📅 日期: ${date}\n`;
    message += `📊 数值: ${value}${metric.unit}\n`;
    message += `📈 7天平均: ${metric.avg_value}${metric.unit}\n`;
    message += `📏 正常范围: ${metric.normal_range[0]}-${metric.normal_range[1]}${metric.unit}\n`;
    
    if (dayData) {
      message += `⭐ 健康评分: ${dayData.score}分\n`;
      message += `🔍 状态: ${dayData.status === 'normal' ? '正常' : '需关注'}\n`;
    }
    
    message += `\n💡 建议: 保持规律监测，如有异常请及时就医`;
    alert(message);
  }
}

function showHealthRadarDetails(radarData) {
  const data = window.healthAnalysisData;
  const avgScore = radarData.values.reduce((a,b)=>a+b,0) / radarData.values.length;
  
  let message = `健康雷达详情\n\n`;
  message += `🎯 综合评分: ${avgScore.toFixed(1)}分\n\n`;
  message += `📋 各项指标评分:\n`;
  radarData.indicators.forEach((ind,i) => {
    const score = radarData.values[i];
    const status = score >= 80 ? '✅' : score >= 60 ? '⚠️' : '❌';
    message += `${status} ${ind.name}: ${score}分\n`;
  });
  
  if (data && data.risk_alerts && data.risk_alerts.length > 0) {
    message += `\n🚨 需要关注:\n`;
    data.risk_alerts.slice(0, 2).forEach(alert => {
      message += `• ${alert.metric}: ${alert.current_value}\n`;
    });
  }
  
  alert(message);
}

// 获取指标平均值的辅助函数
function getMetricAvg(metrics, metricName) {
  const metric = metrics.find(m => m.name === metricName);
  if (!metric || !metric.values) return 0;
  
  const validValues = metric.values.filter(v => v !== null && v !== undefined);
  return validValues.length > 0 ? Math.round(validValues.reduce((a,b) => a+b, 0) / validValues.length) : 0;
}

// 从后端metrics数据计算雷达图数据
function calculateRadarDataFromMetrics(metrics) {
  const indicators = [];
  const values = [];
  
  // 选择主要健康指标
  const mainMetrics = ['心率', '血氧', '体温', '步数', '压力', '收缩压'];
  
  metrics.forEach(metric => {
    if (mainMetrics.includes(metric.name) && metric.avg_value > 0) {
      // 根据指标类型计算健康评分
      let score = 0;
      const avg = metric.avg_value;
      const [min, max] = metric.normal_range;
      
      if (avg >= min && avg <= max) {
        score = 85 + (15 * (1 - Math.abs(avg - (min + max)/2) / ((max - min)/2)));
      } else {
        if (avg < min) {
          score = Math.max(50, 85 - (min - avg) / min * 35);
        } else {
          score = Math.max(50, 85 - (avg - max) / max * 35);
        }
      }
      
      indicators.push({
        name: metric.name,
        max: 100,
        min: 0
      });
      
      values.push(Math.round(Math.min(100, Math.max(0, score))));
    }
  });
  
  // 如果指标不足，添加默认指标
  if (indicators.length < 4) {
    const defaultIndicators = [
      { name: '心率', max: 100, min: 0 },
      { name: '血氧', max: 100, min: 0 },
      { name: '体温', max: 100, min: 0 },
      { name: '步数', max: 100, min: 0 }
    ];
    const defaultValues = [75, 85, 80, 65];
    
    for (let i = indicators.length; i < 4; i++) {
      indicators.push(defaultIndicators[i]);
      values.push(defaultValues[i]);
    }
  }
  
  return { indicators, values };
}

// 更新交互功能函数
function showHealthDetails() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('健康详情功能开发中...\n\n当前显示的是7天健康数据汇总');
    return;
  }
  
  const { health_summary, risk_alerts } = data;
  let message = `健康数据详情报告\n\n`;
  message += `📊 综合评分: ${health_summary.overall_score}分\n`;
  message += `✅ 正常指标: ${health_summary.normal_indicators}项\n`;
  message += `⚠️ 风险指标: ${health_summary.risk_indicators}项\n`;
  message += `👥 活跃用户: ${health_summary.active_users}/${health_summary.total_users}人\n\n`;
  
  if (risk_alerts && risk_alerts.length > 0) {
    message += `🚨 风险预警:\n`;
    risk_alerts.slice(0, 3).forEach(alert => {
      message += `• ${alert.message}\n`;
    });
  } else {
    message += `✨ 暂无风险预警，整体健康状况良好`;
  }
  
  alert(message);
}

function filterByHeartRate() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('心率筛选功能：显示心率异常的时间段和用户');
    return;
  }
  
  const heartRateMetric = data.metrics.find(m => m.name === '心率');
  if (heartRateMetric) {
    const abnormalDays = heartRateMetric.daily_stats ? 
      heartRateMetric.daily_stats.filter(d => d.status === 'risk').length : 0;
    alert(`心率分析结果\n\n平均心率: ${heartRateMetric.avg_value}bpm\n异常天数: ${abnormalDays}天\n正常范围: ${heartRateMetric.normal_range[0]}-${heartRateMetric.normal_range[1]}bpm`);
  } else {
    alert('暂无心率数据');
  }
}

function filterByBloodOxygen() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('血氧筛选功能：显示血氧偏低的时间段和用户');
    return;
  }
  
  const oxygenMetric = data.metrics.find(m => m.name === '血氧');
  if (oxygenMetric) {
    const abnormalDays = oxygenMetric.daily_stats ? 
      oxygenMetric.daily_stats.filter(d => d.status === 'risk').length : 0;
    alert(`血氧分析结果\n\n平均血氧: ${oxygenMetric.avg_value}%\n异常天数: ${abnormalDays}天\n正常范围: ${oxygenMetric.normal_range[0]}-${oxygenMetric.normal_range[1]}%`);
  } else {
    alert('暂无血氧数据');
  }
}

function filterByTemperature() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('体温筛选功能：显示体温异常的时间段和用户');
    return;
  }
  
  const tempMetric = data.metrics.find(m => m.name === '体温');
  if (tempMetric) {
    const abnormalDays = tempMetric.daily_stats ? 
      tempMetric.daily_stats.filter(d => d.status === 'risk').length : 0;
    alert(`体温分析结果\n\n平均体温: ${tempMetric.avg_value}°C\n异常天数: ${abnormalDays}天\n正常范围: ${tempMetric.normal_range[0]}-${tempMetric.normal_range[1]}°C`);
  } else {
    alert('暂无体温数据');
  }
}

function filterBySteps() {
  const data = window.healthAnalysisData;
  if (!data) {
    alert('步数筛选功能：显示运动量不足的用户');
    return;
  }
  
  const stepsMetric = data.metrics.find(m => m.name === '步数');
  if (stepsMetric) {
    const lowActivityDays = stepsMetric.daily_stats ? 
      stepsMetric.daily_stats.filter(d => d.value && d.value < 5000).length : 0;
    alert(`步数分析结果\n\n平均步数: ${stepsMetric.avg_value}步\n运动不足天数: ${lowActivityDays}天\n建议目标: ${stepsMetric.normal_range[0]}步以上`);
  } else {
    alert('暂无步数数据');
  }
}

function showMetricDetails(metricName, value, date) {
  const data = window.healthAnalysisData;
  if (!data) {
    alert(`指标详情\n\n指标: ${metricName}\n数值: ${value}\n日期: ${date}\n\n点击可查看该指标的详细分析和建议`);
    return;
  }
  
  const metric = data.metrics.find(m => m.name === metricName);
  if (metric) {
    const dayData = metric.daily_stats ? metric.daily_stats.find(d => d.date === date) : null;
    let message = `${metricName}详细信息\n\n`;
    message += `📅 日期: ${date}\n`;
    message += `📊 数值: ${value}${metric.unit}\n`;
    message += `📈 7天平均: ${metric.avg_value}${metric.unit}\n`;
    message += `📏 正常范围: ${metric.normal_range[0]}-${metric.normal_range[1]}${metric.unit}\n`;
    
    if (dayData) {
      message += `⭐ 健康评分: ${dayData.score}分\n`;
      message += `🔍 状态: ${dayData.status === 'normal' ? '正常' : '需关注'}\n`;
    }
    
    message += `\n💡 建议: 保持规律监测，如有异常请及时就医`;
    alert(message);
  }
}

function showHealthRadarDetails(radarData) {
  const data = window.healthAnalysisData;
  const avgScore = radarData.values.reduce((a,b)=>a+b,0) / radarData.values.length;
  
  let message = `健康雷达详情\n\n`;
  message += `🎯 综合评分: ${avgScore.toFixed(1)}分\n\n`;
  message += `📋 各项指标评分:\n`;
  radarData.indicators.forEach((ind,i) => {
    const score = radarData.values[i];
    const status = score >= 80 ? '✅' : score >= 60 ? '⚠️' : '❌';
    message += `${status} ${ind.name}: ${score}分\n`;
  });
  
  if (data && data.risk_alerts && data.risk_alerts.length > 0) {
    message += `\n🚨 需要关注:\n`;
    data.risk_alerts.slice(0, 2).forEach(alert => {
      message += `• ${alert.metric}: ${alert.current_value}\n`;
    });
  }
  
  alert(message);
}



function openMessagePanel() {
  // 获取customerId参数
  const urlParams = new URLSearchParams(window.location.search);
  const customerId = urlParams.get('customerId') || '1';
  
  // 打开消息详情页面
  createModalWindow(`/message_view.html?customerId=${customerId}`);
}

// 获取统计数据
function loadStatisticsData() {
  const urlParams = new URLSearchParams(window.location.search);
  const customerId = urlParams.get('customerId') || '1';
  //const today = new Date().toISOString().split('T')[0];
    // 获取北京时间日期(UTC+8) - 修复时区问题




    const today = new Date().toLocaleDateString('zh-CN', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).replace(/\//g, '-');
    console.log("today", today);
  
  // 设置当前日期
  document.getElementById('statsDate').textContent = today;
  
  // 获取统计概览数据
  fetch(`/api/statistics/overview?orgId=${customerId}&date=${today}`)
    .then(response => response.json())
    .then(result => {
      if (result.success) {
        const data = result.data;
        console.log("statistics", data);
        
        // 更新数据显示
        document.getElementById('healthDataCount').textContent = formatNumber(data.healthData);
        document.getElementById('pendingAlerts').textContent = formatNumber(data.pendingAlerts);
        document.getElementById('activeDevices').textContent = data.activeDevices;
        document.getElementById('unreadMessages').textContent = formatNumber(data.unreadMessages);
        
        // 更新系统状态
        updateSystemStatus(data.summary);
        
        // 计算并显示趋势（模拟数据，实际应该从历史数据计算）
        updateTrends(data);
        
        // 添加数据更新动画
        animateStatCards();
      }
    })
    .catch(error => {
      console.error('获取统计数据失败:', error);
      // 显示错误状态
      showErrorState();
    });
}

// 格式化数字显示
function formatNumber(num) {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toString();
}

// 更新系统状态
function updateSystemStatus(summary) {
  const indicator = document.getElementById('statusIndicator');
  const statusText = document.getElementById('statusText');
  const healthScore = document.getElementById('systemHealthScore');
  
  // 移除所有状态类
  indicator.className = 'status-indicator';
  
  // 根据系统状态设置样式和文本
  switch (summary.systemStatus) {
    case 'normal':
      indicator.classList.add('normal');
      statusText.textContent = '系统正常';
      break;
    case 'warning':
      indicator.classList.add('warning');
      statusText.textContent = '系统警告';
      break;
    case 'critical':
      indicator.classList.add('critical');
      statusText.textContent = '系统异常';
      break;
  }
  
  // 更新健康评分
  healthScore.textContent = summary.healthScore;
  
  // 根据评分设置颜色
  if (summary.healthScore >= 80) {
    healthScore.style.color = '#00ff9d';
  } else if (summary.healthScore >= 60) {
    healthScore.style.color = '#ffbb00';
  } else {
    healthScore.style.color = '#ff6b6b';
  }
}

// 更新趋势显示
// 更新趋势显示
function updateTrends(data) {
  // 使用接口返回的真实变化数据
  if (data.changes) {
  const trends = {
      health: data.changes.healthDataChange || '0%',
      alert: data.changes.alertsChange || '0%', 
      device: data.changes.activeDevicesChange || '0%',
      message: data.changes.messagesChange || '0%'
  };
  
  // 更新趋势显示
  updateTrendElement('healthTrend', trends.health);
  updateTrendElement('alertTrend', trends.alert);
  updateTrendElement('deviceTrend', trends.device);
  updateTrendElement('messageTrend', trends.message);
    
    console.log('趋势数据已更新:', trends);
    console.log('昨天对比数据:', data.yesterday);
  } else {
    // 兜底：如果没有changes数据，显示无数据状态
    updateTrendElement('healthTrend', '0%');
    updateTrendElement('alertTrend', '0%');
    updateTrendElement('deviceTrend', '0%');
    updateTrendElement('messageTrend', '0%');
    
    console.warn('接口未返回changes数据，使用默认值');
  }
}

// 更新单个趋势元素
function updateTrendElement(elementId, trend) {
  const element = document.getElementById(elementId);
  element.textContent = trend;
  element.className = 'stat-trend';
  
  if (trend.startsWith('-')) {
    element.classList.add('negative');
  }
}

// 统计卡片动画
function animateStatCards() {
  const cards = document.querySelectorAll('.stat-card');
  cards.forEach((card, index) => {
    setTimeout(() => {
      card.style.transform = 'scale(1.05)';
      setTimeout(() => {
        card.style.transform = 'scale(1)';
      }, 200);
    }, index * 100);
  });
}

// 显示错误状态
function showErrorState() {
  const statusText = document.getElementById('statusText');
  const indicator = document.getElementById('statusIndicator');
  
  statusText.textContent = '数据获取失败';
  indicator.className = 'status-indicator critical';
  
  // 显示默认值
  document.getElementById('healthDataCount').textContent = '--';
  document.getElementById('pendingAlerts').textContent = '--';
  document.getElementById('activeDevices').textContent = '--';
  document.getElementById('unreadMessages').textContent = '--';
}


// 初始化统计概览图表
function initOverviewChart() {
  const overviewContainer = document.getElementById('overviewChart');
  if (overviewContainer) {
    const overviewChart = echarts.init(overviewContainer);
    
    const overviewOption = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        show: false
      },
      series: [{
        name: '数据概览',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['50%', '50%'],
        data: [
          {value: 0, name: '健康数据', itemStyle: {color: '#00e4ff'}},
          {value: 0, name: '告警数据', itemStyle: {color: '#ff6b6b'}},
          {value: 0, name: '设备数据', itemStyle: {color: '#00ff9d'}},
          {value: 0, name: '消息数据', itemStyle: {color: '#ffbb00'}}
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          show: false
        },
        labelLine: {
          show: false
        }
      }]
    };
    
    overviewChart.setOption(overviewOption);
    
    // 保存图表实例以便后续更新
    window.overviewChart = overviewChart;
  }
}