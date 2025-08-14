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
                data: healthData
            });
    
            // 更新图层数据源
            breathRed.setSource(newGeoLevelF);
            breathYellow.setSource(newGeoLevelE);
            breathGreen.setSource(newGeo);
    
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
    //console.log('filterData.data.healthData',data.healthData);
  const toStr=x=>x===undefined||x===null?'':String(x);
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