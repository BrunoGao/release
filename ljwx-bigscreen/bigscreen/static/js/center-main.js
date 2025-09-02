let currentDept = '', currentUser = '';
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
            // 更新地图中心点
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
    //console.log('filterData.data',currentDept,currentUser);

  const dept=toStr(currentDept),user=toStr(currentUser);
  const alerts=(data.alert_info?.alerts||[]).filter(a=>
    (!dept||[a.dept_id,a.deptId].some(v=>toStr(v)===dept))&&
    (!user||[a.user_id,a.userId].some(v=>toStr(v)===user))&&
    (['pending','1'].includes(toStr(a.alert_status||a.status)))
  );
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