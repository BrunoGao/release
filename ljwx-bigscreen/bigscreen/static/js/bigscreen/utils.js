/**
 * 智能健康数据分析平台 - 工具函数
 */

// 工具函数模块
console.log('📦 加载 utils.js');

// 更新元素内容的通用函数
function updateElement(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

// 注意：告警相关常量已在constants.js中定义，这里不重复声明

// 翻译函数
function translate(key) {
    const translations = {
        'heart_rate': '心率',
        'blood_oxygen': '血氧',
        'temperature': '体温',
        'steps': '步数',
        'calories': '卡路里',
        'systolic_pressure': '收缩压',
        'diastolic_pressure': '舒张压',
        'stress': '压力',
        'critical': '严重',
        'high': '高级',
        'medium': '中级',
        'low': '低级',
        'online': '在线',
        'offline': '离线',
        'error': '故障',
        'normal': '正常'
    };
    return translations[key] || key;
}

// 告警翻译函数（使用新的常量映射）
function translateAlertType(type) {
    return ALERT_TYPE_MAP[type] || type;
}

function translateAlertLevel(level) {
    return ALERT_LEVEL_MAP[level] || level;
}

function translateAlertStatus(status) {
    return ALERT_STATUS_MAP[status] || status;
}

function translateMessageType(type) {
    return MESSAGE_TYPE_MAP[type] || type;
}

function translateMessageStatus(status) {
    return MESSAGE_STATUS_MAP[status] || status;
}

// 告警颜色获取函数
function getAlertTypeColor(type) {
    return ALERT_TYPE_COLOR[type] || '#7ecfff';
}

function getAlertLevelColor(level) {
    return ALERT_SEVERITY_COLOR[level] || '#7ecfff';
}

function getAlertStatusColor(status) {
    return ALERT_STATUS_COLOR[status] || '#7ecfff';
}

function getMessageTypeColor(type) {
    return MESSAGE_TYPE_COLOR[type] || '#7ecfff';
}

// 获取告警级别对应的颜色
function getAlertColor(level) {
    const colors = {
        critical: '#ff4444',
        high: '#ff6666',
        medium: '#ffbb00',
        low: '#00ff9d'
    };
    return colors[level] || '#666666';
}

// 获取设备状态对应的颜色
function getDeviceStatusColor(status) {
    const colors = {
        online: '#00ff9d',
        offline: '#ffbb00',
        error: '#ff6666'
    };
    return colors[status] || '#666666';
}

// 格式化日期时间
function formatDateTime(dateTime) {
    if (!dateTime) return '-';
    const date = new Date(dateTime);
    return date.toLocaleString('zh-CN');
}

// 格式化日期
function formatDate(date) {
    if (!date) return '-';
    const d = new Date(date);
    return d.toLocaleDateString('zh-CN');
}

// 获取过去N天的日期字符串
function getPastDateStr(daysAgo) {
    const d = new Date();
    d.setDate(d.getDate() - daysAgo);
    return d.toISOString().slice(0,10);
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

// 格式化时间
function formatTime(time) {
    if (!time) return '-';
    const t = new Date(time);
    return t.toLocaleTimeString('zh-CN');
}

// 地图相关函数
// 显示地图信息弹窗
function showCustomMapInfo(feature) {
    const mapInfo = document.getElementById('customMapInfo');
    if (!mapInfo || !feature) return;
    
    const { properties, coordinates } = feature;
    const content = document.getElementById('mapInfoContent');
    const title = document.getElementById('mapInfoTitle');
    
    if (title) {
        title.textContent = properties.name || '设备信息';
    }
    
    if (content) {
        content.innerHTML = `
            <div class="info-item">
                <span class="info-label">用户名:</span>
                <span class="info-value">${properties.userName || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">设备类型:</span>
                <span class="info-value">${properties.deviceType || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">健康状态:</span>
                <span class="info-value" style="color: ${getHealthStatusColor(properties.healthStatus)}">${properties.healthStatus || '-'}</span>
            </div>
            <div class="info-item">
                <span class="info-label">最后更新:</span>
                <span class="info-value">${formatDateTime(properties.lastUpdate)}</span>
            </div>
            <div class="info-item">
                <span class="info-label">位置:</span>
                <span class="info-value">${coordinates ? `${coordinates[1].toFixed(6)}, ${coordinates[0].toFixed(6)}` : '-'}</span>
            </div>
        `;
    }
    
    mapInfo.style.display = 'block';
    
    // 根据特征位置调整弹窗位置
    if (coordinates && window.map) {
        const pixel = window.map.lngLatToContainer(coordinates);
        mapInfo.style.left = (pixel.x + 10) + 'px';
        mapInfo.style.top = (pixel.y - 80) + 'px';
    }
}

// 隐藏地图信息弹窗
function removeCustomMapInfo() {
    const mapInfo = document.getElementById('customMapInfo');
    if (mapInfo) {
        mapInfo.style.display = 'none';
    }
}

// 获取健康状态颜色
function getHealthStatusColor(status) {
    const colors = {
        '正常': '#00ff9d',
        '异常': '#ff6666',
        '预警': '#ffbb00',
        '严重': '#ff4444'
    };
    return colors[status] || '#666666';
}

// 筛选面板控制
function toggleFilterPanel() {
    const filterPanel = document.getElementById('filterPanel');
    if (filterPanel) {
        filterPanel.classList.toggle('active');
    }
}

// 初始化筛选面板事件
function initFilterPanelEvents() {
    const filterToggle = document.getElementById('filterToggle');
    if (filterToggle) {
        filterToggle.addEventListener('click', toggleFilterPanel);
    }
    
    // 搜索输入框事件
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const keyword = e.target.value;
            filterUsersByKeyword(keyword);
        });
    }
    
    // 部门选择事件
    const deptSelect = document.getElementById('deptSelect');
    if (deptSelect) {
        deptSelect.addEventListener('change', function(e) {
            const deptId = e.target.value;
            filterUsersByDept(deptId);
        });
    }
    
    // 用户选择事件
    const userSelect = document.getElementById('userSelect');
    if (userSelect) {
        userSelect.addEventListener('change', function(e) {
            const userId = e.target.value;
            focusOnUser(userId);
        });
    }
}

// 按关键词筛选用户
function filterUsersByKeyword(keyword) {
    console.log('按关键词筛选用户:', keyword);
    // TODO: 实现筛选逻辑
}

// 按部门筛选用户
function filterUsersByDept(deptId) {
    console.log('按部门筛选用户:', deptId);
    // TODO: 实现筛选逻辑
}

// 聚焦到特定用户
function focusOnUser(userId) {
    console.log('聚焦到用户:', userId);
    // TODO: 实现聚焦逻辑
}

// 模态框控制函数
function showPersonnelDetails() {
    const modal = document.getElementById('personnelModal');
    const modalBody = document.getElementById('personnelModalBody');
    
    if (modal && modalBody) {
        // 加载人员详情数据
        modalBody.innerHTML = '<div class="loading">加载中...</div>';
        modal.style.display = 'flex';
        
        // 获取详细数据
        const customerId = window.CUSTOMER_ID || '1';
        fetch(`/api/personnel_details/${customerId}`)
            .then(response => response.json())
            .then(data => {
                modalBody.innerHTML = generatePersonnelDetailsHTML(data);
            })
            .catch(error => {
                console.error('加载人员详情失败:', error);
                modalBody.innerHTML = '<div class="error">加载失败，请重试</div>';
            });
    }
}

function closePersonnelModal() {
    const modal = document.getElementById('personnelModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 生成人员详情HTML
function generatePersonnelDetailsHTML(data) {
    if (!data || !data.personnel) {
        return '<div class="no-data">暂无数据</div>';
    }
    
    return `
        <div class="personnel-details">
            <div class="details-header">
                <h4>人员列表 (共 ${data.total || 0} 人)</h4>
            </div>
            <div class="details-table">
                <table>
                    <thead>
                        <tr>
                            <th>姓名</th>
                            <th>部门</th>
                            <th>设备状态</th>
                            <th>在线状态</th>
                            <th>最后活跃时间</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${data.personnel.map(person => `
                            <tr>
                                <td>${person.name || '-'}</td>
                                <td>${person.department || '-'}</td>
                                <td>
                                    <span class="status-badge ${person.deviceStatus}" style="color: ${getDeviceStatusColor(person.deviceStatus)}">
                                        ${translate(person.deviceStatus)}
                                    </span>
                                </td>
                                <td>
                                    <span class="status-badge ${person.onlineStatus}" style="color: ${person.onlineStatus === 'online' ? '#00ff9d' : '#ffbb00'}">
                                        ${translate(person.onlineStatus)}
                                    </span>
                                </td>
                                <td>${formatDateTime(person.lastActiveTime)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// 快速统计卡片点击事件
function filterByDepartment() {
    console.log('按部门筛选');
    // TODO: 实现部门筛选
}

function filterByOnlineStatus() {
    console.log('按在线状态筛选');
    // TODO: 实现在线状态筛选
}

function filterByDeviceStatus() {
    console.log('按设备状态筛选');
    // TODO: 实现设备状态筛选
}

function filterByAlertStatus() {
    console.log('按告警状态筛选');
    // TODO: 实现告警状态筛选
}

// 兼容性和浏览器检测
function checkBrowserCompatibility() {
    const isIE = /MSIE|Trident/.test(navigator.userAgent);
    if (isIE) {
        console.warn('⚠️ 检测到IE浏览器，部分功能可能不兼容');
        return false;
    }
    
    // 检查必要的API支持
    const requiredAPIs = [
        'fetch',
        'Promise',
        'Map',
        'Set'
    ];
    
    const missingAPIs = requiredAPIs.filter(api => !(api in window));
    if (missingAPIs.length > 0) {
        console.warn('⚠️ 缺少必要的API支持:', missingAPIs);
        return false;
    }
    
    return true;
}

// 错误处理和重试机制
function retryWithBackoff(fn, maxRetries = 3, delay = 1000) {
    return new Promise((resolve, reject) => {
        let retries = 0;
        
        function attempt() {
            fn()
                .then(resolve)
                .catch(error => {
                    retries++;
                    if (retries < maxRetries) {
                        console.log(`重试 ${retries}/${maxRetries} 次，${delay}ms 后重试...`);
                        setTimeout(attempt, delay * retries);
                    } else {
                        reject(error);
                    }
                });
        }
        
        attempt();
    });
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 检查浏览器兼容性
    if (!checkBrowserCompatibility()) {
        console.error('❌ 浏览器兼容性检查失败');
    }
    
    // 初始化筛选面板事件
    initFilterPanelEvents();
    
    // 初始化模态框关闭事件
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closePersonnelModal();
        }
    });
    
    console.log('🎯 事件监听器初始化完成');
});

// 地理逆编码函数 - 经纬度转地址 #修复错误处理
async function reverseGeocode(lng, lat) {
    try {
        return new Promise((resolve, reject) => {
            if (!window.AMap) {
                console.warn('高德地图API未加载');
                resolve('位置信息获取中...');
                return;
            }
            
            if (!lng || !lat || isNaN(lng) || isNaN(lat)) {
                console.warn('无效的经纬度坐标:', lng, lat);
                resolve('坐标无效');
                return;
            }
            
            AMap.plugin('AMap.Geocoder', function() {
                try {
                    const geocoder = new AMap.Geocoder({
                        city: '全国', // 改回全国避免平台限制
                        radius: 1000,
                        extensions: 'base'
                    });
                    
                    const lnglat = new AMap.LngLat(parseFloat(lng), parseFloat(lat));
                    
                    // 添加超时处理
                    const timeout = setTimeout(() => {
                        resolve('位置查询超时');
                    }, 5000);
                    
                    geocoder.getAddress(lnglat, function(status, result) {
                        clearTimeout(timeout);
                        if (status === 'complete' && result && result.regeocode && result.regeocode.formattedAddress) {
                            resolve(result.regeocode.formattedAddress);
                        } else {
                            console.warn('逆地理编码状态:', status, '结果:', result);
                            // 对于USERKEY_PLAT_NOMATCH错误，直接返回默认位置
                            if (status === 'error' && result === 'USERKEY_PLAT_NOMATCH') {
                                resolve('深圳市南山区');
                            } else {
                                resolve('位置解析失败');
                            }
                        }
                    });
                } catch (innerError) {
                    console.error('Geocoder创建错误:', innerError);
                    resolve('位置服务异常');
                }
            });
        });
    } catch (error) {
        console.error('逆地理编码错误:', error);
        return '未知位置';
    }
}

// 处理告警函数 #从原版bigscreen_main.html复制
function handleAlert(alertId) {
    if (!alertId) {
        console.warn('告警ID为空');
        return;
    }
    
    console.log('🚨 处理告警:', alertId);
    
    // 使用原版API路径
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

// 自定义弹出框函数 #从原版复制
function showCustomAlert(message, callback) {
    const overlay = document.createElement('div');
    overlay.className = 'custom-alert-overlay';
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);z-index:10000;';
    document.body.appendChild(overlay);

    const alertBox = document.createElement('div');
    alertBox.className = 'custom-alert';
    alertBox.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:rgba(0,21,41,0.95);border:1px solid #00e4ff;border-radius:8px;padding:30px;color:#fff;text-align:center;z-index:10001;min-width:300px;';
    alertBox.innerHTML = `
        <div class="custom-alert-content" style="margin-bottom:20px;font-size:16px;">${message}</div>
        <button class="custom-alert-button" style="background:#00e4ff;color:#000;border:none;padding:8px 20px;border-radius:4px;cursor:pointer;">确定</button>
    `;
    document.body.appendChild(alertBox);

    const confirmButton = alertBox.querySelector('.custom-alert-button');
    confirmButton.onclick = () => {
        document.body.removeChild(overlay);
        document.body.removeChild(alertBox);
        if (callback) callback();
    };
}

// 显示处理中提示
function showProcessingAlert() {
    // 移除现有提示
    const existing = document.querySelector('.processing-alert');
    if (existing) existing.remove();
    
    const modal = document.createElement('div');
    modal.className = 'processing-alert';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 20000;
        animation: fadeIn 0.3s ease;
    `;
    
    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, rgba(10,24,48,0.98) 0%, rgba(15,35,65,0.98) 100%);
            border-radius: 16px;
            border: 2px solid rgba(0,228,255,0.4);
            padding: 30px 40px;
            text-align: center;
            color: #fff;
            min-width: 300px;
            box-shadow: 0 25px 80px rgba(0,228,255,0.3);
        ">
            <div style="
                width: 50px;
                height: 50px;
                border: 3px solid rgba(0,228,255,0.3);
                border-top: 3px solid #00e4ff;
                border-radius: 50%;
                margin: 0 auto 20px;
                animation: spin 1s linear infinite;
            "></div>
            <div style="font-size: 18px; color: #00e4ff; margin-bottom: 10px;">处理告警中...</div>
            <div style="font-size: 14px; color: #7ecfff;">正在通过message处理</div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 3000);
}

// 显示告警处理成功模态框
function showAlertSuccessModal() {
    // 移除处理中提示
    const processing = document.querySelector('.processing-alert');
    if (processing) processing.remove();
    
    // 移除现有成功提示
    const existing = document.querySelector('.alert-success-modal');
    if (existing) existing.remove();
    
    const modal = document.createElement('div');
    modal.className = 'alert-success-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 20000;
        animation: fadeIn 0.3s ease;
    `;
    
    modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, rgba(10,24,48,0.98) 0%, rgba(15,35,65,0.98) 100%);
            border-radius: 20px;
            border: 2px solid rgba(0,228,255,0.4);
            padding: 40px 50px;
            text-align: center;
            color: #fff;
            min-width: 380px;
            box-shadow: 0 25px 80px rgba(0,228,255,0.3);
            position: relative;
            overflow: hidden;
        ">
            <!-- 背景装饰 -->
            <div style="
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(0,228,255,0.1) 0%, transparent 70%);
                animation: rotate 6s linear infinite;
            "></div>
            
            <!-- 内容 -->
            <div style="position: relative; z-index: 2;">
                <div style="
                    font-size: 48px;
                    margin-bottom: 20px;
                    animation: bounce 0.6s ease-in-out;
                ">✅</div>
                
                <div style="
                    font-size: 24px;
                    font-weight: 700;
                    color: #00e4ff;
                    margin-bottom: 15px;
                    text-shadow: 0 0 10px rgba(0,228,255,0.5);
                ">告警已通过message处理</div>
                
                <div style="
                    font-size: 16px;
                    color: #7ecfff;
                    margin-bottom: 30px;
                    line-height: 1.5;
                ">系统已成功处理该告警信息<br/>相关人员将收到处理通知</div>
                
                <button onclick="closeAlertSuccessModal()" style="
                    background: linear-gradient(135deg, rgba(0,228,255,0.2) 0%, rgba(0,180,255,0.3) 100%);
                    border: 1px solid rgba(0,228,255,0.5);
                    border-radius: 25px;
                    color: #00e4ff;
                    padding: 12px 30px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-shadow: 0 0 8px rgba(0,228,255,0.3);
                " onmouseover="this.style.background='linear-gradient(135deg, rgba(0,228,255,0.3) 0%, rgba(0,180,255,0.4) 100%)'; this.style.transform='scale(1.05)';"
                   onmouseout="this.style.background='linear-gradient(135deg, rgba(0,228,255,0.2) 0%, rgba(0,180,255,0.3) 100%)'; this.style.transform='scale(1)';">
                    确定
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 点击外部关闭
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeAlertSuccessModal();
        }
    });
}

// 关闭告警成功模态框
function closeAlertSuccessModal() {
    const modal = document.querySelector('.alert-success-modal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            modal.remove();
            // 关闭原始告警框
            if (window.removeCustomMapInfo) {
                removeCustomMapInfo();
            }
        }, 300);
    }
}

// 显示健康详情函数 - 创建健康信息框
function showHealthProfile(healthId) {
    if (!healthId) {
        console.warn('健康数据ID为空');
        return;
    }
    
    console.log('📊 显示健康详情:', healthId);
    
    // 移除现有的健康信息框
    const existingHealthModal = document.querySelector('.health-modal-overlay');
    if(existingHealthModal) {
        existingHealthModal.remove();
    }
    
    // 创建健康信息框
    const healthModal = document.createElement('div');
    healthModal.className = 'health-modal-overlay';
    healthModal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        animation: fadeIn 0.3s ease;
    `;
    
    // 模拟健康数据（实际应该从API获取）
    const healthData = {
        healthScore: 50,
        heartRate: 79,
        bloodPressureHigh: 120,
        bloodPressureLow: 82,
        bloodOxygen: 98,
        temperature: 36.5, // 正常体温
        steps: '8,356',
        distance: '6.2',
        calories: '425',
        pressure: '35' // 压力指数
    };
    
    healthModal.innerHTML = `
        <div style="
            position: relative;
            width: 400px;
            max-height: 90vh;
            overflow-y: auto;
            background: linear-gradient(135deg, rgba(10,24,48,0.98) 0%, rgba(15,35,65,0.98) 50%, rgba(10,24,48,0.98) 100%);
            border-radius: 20px;
            border: 2px solid rgba(0,228,255,0.4);
            box-shadow: 0 25px 80px rgba(0,228,255,0.3), 0 0 40px rgba(0,228,255,0.2);
            color: #fff;
            padding: 24px;
            animation: slideIn 0.4s ease-out;
        ">
            <!-- 关闭按钮 -->
            <button onclick="closeHealthModal()" style="
                position: absolute;
                top: 15px;
                right: 15px;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                background: rgba(0,228,255,0.1);
                border: 1px solid rgba(0,228,255,0.3);
                color: #00e4ff;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                font-weight: 700;
                transition: all 0.3s ease;
            " onmouseover="this.style.background='rgba(0,228,255,0.2)'" 
               onmouseout="this.style.background='rgba(0,228,255,0.1)'">✕</button>
            
            <!-- 头部标题 -->
            <div style="
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 24px;
                padding-bottom: 16px;
                border-bottom: 1px solid rgba(0,228,255,0.2);
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="
                        width: 48px;
                        height: 48px;
                        border-radius: 12px;
                        background: linear-gradient(135deg, rgba(255,107,107,0.3) 0%, rgba(0,228,255,0.4) 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 24px;
                    ">❤️</div>
                    <div>
                        <div style="
                            font-size: 18px;
                            font-weight: 700;
                            color: #00e4ff;
                            margin-bottom: 4px;
                        ">智能健康监测</div>
                        <div style="
                            font-size: 12px;
                            color: #7ecfff;
                            text-transform: uppercase;
                            letter-spacing: 1px;
                        ">HEALTH PROFILE ANALYSIS</div>
                    </div>
                </div>
                
                <!-- 健康评分圆环 -->
                <div style="position: relative; width: 60px; height: 60px;">
                    <svg width="60" height="60" style="transform: rotate(-90deg);">
                        <circle cx="30" cy="30" r="25" stroke="rgba(255,107,107,0.2)" stroke-width="4" fill="none"/>
                        <circle cx="30" cy="30" r="25" stroke="#ff6b6b" stroke-width="4" fill="none"
                            stroke-dasharray="157" stroke-dashoffset="${157 * (1 - healthData.healthScore/100)}"
                            style="transition: stroke-dashoffset 1s ease;"/>
                    </svg>
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        font-size: 14px;
                        font-weight: 700;
                        color: #ff6b6b;
                    ">${healthData.healthScore}</div>
                </div>
            </div>
            
            <!-- 心率监测 -->
            <div style="
                background: rgba(0,21,41,0.6);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                border: 1px solid rgba(255,107,107,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        border-radius: 8px;
                        background: linear-gradient(135deg, rgba(0,228,255,0.3) 0%, rgba(0,180,255,0.5) 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    ">+</div>
                    <div>
                        <div style="color: #7ecfff; font-size: 12px; margin-bottom: 2px;">心率监测</div>
                        <div style="color: #00ff88; font-size: 18px; font-weight: 700;">
                            ${healthData.heartRate} <span style="font-size: 12px; color: #888;">bpm</span>
                        </div>
                    </div>
                </div>
                <div style="
                    width: 100%;
                    height: 4px;
                    background: rgba(255,107,107,0.2);
                    border-radius: 2px;
                    overflow: hidden;
                ">
                    <div style="
                        width: ${(healthData.heartRate/120)*100}%;
                        height: 100%;
                        background: linear-gradient(90deg, #ff6b6b, #ff8a80);
                        transition: width 1s ease;
                    "></div>
                </div>
            </div>
            
            <!-- 血压监测 -->
            <div style="
                background: rgba(0,21,41,0.6);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                border: 1px solid rgba(0,180,255,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        border-radius: 8px;
                        background: linear-gradient(135deg, rgba(0,180,255,0.3) 0%, rgba(0,228,255,0.5) 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    ">⊕</div>
                    <div style="flex: 1;">
                        <div style="color: #7ecfff; font-size: 12px; margin-bottom: 2px;">血压监测</div>
                        <div style="color: #fff; font-size: 18px; font-weight: 700;">
                            ${healthData.bloodPressureHigh}/${healthData.bloodPressureLow} <span style="font-size: 12px; color: #888;">mmHg</span>
                        </div>
                    </div>
                </div>
                <div style="
                    display: inline-block;
                    padding: 4px 8px;
                    background: rgba(255,187,0,0.2);
                    border: 1px solid rgba(255,187,0,0.4);
                    border-radius: 4px;
                    color: #ffbb00;
                    font-size: 10px;
                    font-weight: 600;
                ">需要关注</div>
            </div>
            
            <!-- 血氧饱和度 -->
            <div style="
                background: rgba(0,21,41,0.6);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                border: 1px solid rgba(0,255,136,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        border-radius: 8px;
                        background: linear-gradient(135deg, rgba(0,255,136,0.3) 0%, rgba(0,204,102,0.5) 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    ">◇</div>
                    <div>
                        <div style="color: #7ecfff; font-size: 12px; margin-bottom: 2px;">血氧饱和度</div>
                        <div style="color: #00ff88; font-size: 18px; font-weight: 700;">
                            ${healthData.bloodOxygen} <span style="font-size: 12px; color: #888;">%</span>
                        </div>
                    </div>
                </div>
                <div style="
                    width: 100%;
                    height: 4px;
                    background: rgba(0,255,136,0.2);
                    border-radius: 2px;
                    overflow: hidden;
                ">
                    <div style="
                        width: ${healthData.bloodOxygen}%;
                        height: 100%;
                        background: linear-gradient(90deg, #00ff88, #00cc66);
                        transition: width 1s ease;
                    "></div>
                </div>
            </div>
            
            <!-- 体温监测 -->
            <div style="
                background: rgba(0,21,41,0.6);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                border: 1px solid ${healthData.temperature > 37.3 ? 'rgba(255,68,68,0.3)' : 'rgba(0,255,136,0.3)'};
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        border-radius: 8px;
                        background: linear-gradient(135deg, ${healthData.temperature > 37.3 ? 'rgba(255,68,68,0.3)' : 'rgba(0,255,136,0.3)'} 0%, ${healthData.temperature > 37.3 ? 'rgba(220,38,38,0.5)' : 'rgba(0,204,102,0.5)'} 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    ">${healthData.temperature > 37.3 ? '🌡️' : '🌡️'}</div>
                    <div style="flex: 1;">
                        <div style="color: #7ecfff; font-size: 12px; margin-bottom: 2px;">体温监测</div>
                        <div style="color: ${healthData.temperature > 37.3 ? '#ff6b6b' : '#00ff88'}; font-size: 18px; font-weight: 700;">
                            ${healthData.temperature} <span style="font-size: 12px; color: #888;">°C</span>
                        </div>
                    </div>
                </div>
                <div style="
                    display: inline-block;
                    padding: 4px 8px;
                    background: ${healthData.temperature > 37.3 ? 'rgba(255,68,68,0.2)' : 'rgba(0,255,136,0.2)'};
                    border: 1px solid ${healthData.temperature > 37.3 ? 'rgba(255,68,68,0.4)' : 'rgba(0,255,136,0.4)'};
                    border-radius: 4px;
                    color: ${healthData.temperature > 37.3 ? '#ff4444' : '#00ff88'};
                    font-size: 10px;
                    font-weight: 600;
                ">${healthData.temperature > 37.3 ? '异常体温' : '体温正常'}</div>
            </div>
            
            <!-- 运动数据 -->
            <div style="
                background: rgba(0,21,41,0.6);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                border: 1px solid rgba(138,43,226,0.3);
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        border-radius: 8px;
                        background: linear-gradient(135deg, rgba(138,43,226,0.3) 0%, rgba(75,0,130,0.5) 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    ">⚘</div>
                    <div>
                        <div style="color: #7ecfff; font-size: 12px; margin-bottom: 2px;">运动数据</div>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; text-align: center;">
                    <div>
                        <div style="color: #9d4edd; font-size: 16px; font-weight: 700;">${healthData.steps}</div>
                        <div style="color: #7ecfff; font-size: 10px;">步数</div>
                    </div>
                    <div>
                        <div style="color: #9d4edd; font-size: 16px; font-weight: 700;">${healthData.distance}</div>
                        <div style="color: #7ecfff; font-size: 10px;">米</div>
                    </div>
                    <div>
                        <div style="color: #9d4edd; font-size: 16px; font-weight: 700;">${healthData.calories}</div>
                        <div style="color: #7ecfff; font-size: 10px;">卡路里</div>
                    </div>
                </div>
                <div style="
                    text-align: center;
                    margin-top: 12px;
                    color: #00ff88;
                    font-size: 14px;
                    font-weight: 600;
                ">0%</div>
            </div>
            
            <!-- 压力指数 -->
            <div style="
                background: rgba(0,21,41,0.6);
                border-radius: 12px;
                padding: 16px;
                border: 1px solid ${parseInt(healthData.pressure) > 70 ? 'rgba(255,68,68,0.3)' : parseInt(healthData.pressure) > 40 ? 'rgba(255,187,0,0.3)' : 'rgba(0,255,136,0.3)'};
            ">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                    <div style="
                        width: 32px;
                        height: 32px;
                        border-radius: 8px;
                        background: linear-gradient(135deg, ${parseInt(healthData.pressure) > 70 ? 'rgba(255,68,68,0.3)' : parseInt(healthData.pressure) > 40 ? 'rgba(255,187,0,0.3)' : 'rgba(0,255,136,0.3)'} 0%, ${parseInt(healthData.pressure) > 70 ? 'rgba(220,38,38,0.5)' : parseInt(healthData.pressure) > 40 ? 'rgba(255,193,7,0.5)' : 'rgba(0,204,102,0.5)'} 100%);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 16px;
                    ">💆</div>
                    <div style="flex: 1;">
                        <div style="color: #7ecfff; font-size: 12px; margin-bottom: 2px;">压力指数</div>
                        <div style="color: ${parseInt(healthData.pressure) > 70 ? '#ff6b6b' : parseInt(healthData.pressure) > 40 ? '#ffbb00' : '#00ff88'}; font-size: 18px; font-weight: 700;">
                            ${healthData.pressure} <span style="font-size: 12px; color: #888;">分</span>
                        </div>
                    </div>
                </div>
                <div style="
                    display: inline-block;
                    padding: 4px 8px;
                    background: ${parseInt(healthData.pressure) > 70 ? 'rgba(255,68,68,0.2)' : parseInt(healthData.pressure) > 40 ? 'rgba(255,187,0,0.2)' : 'rgba(0,255,136,0.2)'};
                    border: 1px solid ${parseInt(healthData.pressure) > 70 ? 'rgba(255,68,68,0.4)' : parseInt(healthData.pressure) > 40 ? 'rgba(255,187,0,0.4)' : 'rgba(0,255,136,0.4)'};
                    border-radius: 4px;
                    color: ${parseInt(healthData.pressure) > 70 ? '#ff4444' : parseInt(healthData.pressure) > 40 ? '#ffbb00' : '#00ff88'};
                    font-size: 10px;
                    font-weight: 600;
                ">${parseInt(healthData.pressure) > 70 ? '压力偏高' : parseInt(healthData.pressure) > 40 ? '压力适中' : '压力正常'}</div>
            </div>
        </div>
    `;
    
    // 添加到页面
    document.body.appendChild(healthModal);
    
    // 点击外部关闭
    healthModal.addEventListener('click', function(e) {
        if (e.target === healthModal) {
            closeHealthModal();
        }
    });
    
    console.log('✅ 健康信息框显示完成');
}

// 关闭健康信息框（独立函数，不影响告警框）
function closeHealthModal() {
    const healthModal = document.querySelector('.health-modal-overlay');
    if (healthModal) {
        healthModal.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => {
            healthModal.remove();
            console.log('✅ 健康信息框已关闭');
        }, 300);
    }
}

// 导出函数到全局作用域
window.updateElement = updateElement;
window.translate = translate;
window.getAlertColor = getAlertColor;
window.getDeviceStatusColor = getDeviceStatusColor;
window.formatDateTime = formatDateTime;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.showCustomMapInfo = showCustomMapInfo;
window.removeCustomMapInfo = removeCustomMapInfo;
window.handleAlert = handleAlert;
window.showCustomAlert = showCustomAlert;
window.reverseGeocode = reverseGeocode;
window.showPersonnelDetails = showPersonnelDetails;
window.closePersonnelModal = closePersonnelModal;
window.filterByDepartment = filterByDepartment;
window.filterByOnlineStatus = filterByOnlineStatus;
window.filterByDeviceStatus = filterByDeviceStatus;
window.filterByAlertStatus = filterByAlertStatus;
window.retryWithBackoff = retryWithBackoff;
window.debounce = debounce;
window.throttle = throttle;
window.reverseGeocode = reverseGeocode;
window.handleAlert = handleAlert;
window.showHealthProfile = showHealthProfile;
window.closeHealthModal = closeHealthModal;
window.showProcessingAlert = showProcessingAlert;
window.showAlertSuccessModal = showAlertSuccessModal;
window.closeAlertSuccessModal = closeAlertSuccessModal;

console.log('✅ utils.js 加载完成'); 