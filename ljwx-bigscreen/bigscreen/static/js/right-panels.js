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
                charts.healthScore = echarts.init(healthScoreContainer);
                
                // 从URL获取customerId参数
                const urlParams = new URLSearchParams(window.location.search);
                const customerId = urlParams.get('customerId') || '1';
                
                // 获取日期范围
                const today = new Date();
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 7);
                
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
                            
                            // 兼容驼峰和下划线命名的辅助函数
                            function getFactorScore(factors, camelCase, snakeCase) {
                                return factors[camelCase]?.score || factors[snakeCase]?.score || 0;
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
                    // 更新健康评分图表
                    
                }

                // 更新人员管理面板
                initPersonnelManagementPanel(data);

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