/**
 * 地图增强补丁脚本 - 执行后立即应用所有功能
 * 使用方法：
 * 1. 复制此脚本内容
 * 2. 在大屏页面打开浏览器控制台(F12)
 * 3. 粘贴并执行此脚本
 * 
 * 功能：
 * 1. 绿色圆点上方显示员工名字(部门-姓名)
 * 2. 美化健康信息框样式
 * 3. 添加个人大屏链接按钮
 */

(function() {
    console.log('🚀 开始应用地图增强功能...');
    
    // 备份原始函数
    if (!window.originalShowCustomMapInfo) {
        window.originalShowCustomMapInfo = window.showCustomMapInfo;
    }
    if (!window.originalUpdateMapData) {
        window.originalUpdateMapData = window.updateMapData;
    }
    
    // 增强版信息框显示函数
    window.showCustomMapInfo = function(f) {
        removeCustomMapInfo();
        const d = f.properties;
        const get = (...k) => k.map(x => d[x]).find(x => x !== undefined && x !== null && x !== '') || '-';
        const isAlert = !!(get('alert_id','alertId') && get('alert_type','alertType') && d.type !== 'health');
        const avatarUrl = d.avatar || '/static/images/avatar-tech.svg';
        const div = document.createElement('div');
        div.className = 'custom-map-info';
        div.style.cssText = 'position:absolute;z-index:9999;min-width:420px;max-width:480px;background:rgba(10,24,48,0.98);border:2px solid #00e4ff;border-radius:18px;box-shadow:0 0 32px rgba(0,228,255,0.5);padding:28px 34px 24px 34px;color:#fff;top:120px;left:50%;transform:translateX(-50%);font-size:15px;font-family:"Microsoft YaHei",Roboto,Arial,sans-serif;backdrop-filter:blur(8px);animation:fadeInScale 0.3s ease;';
        
        // 添加CSS动画
        if (!document.getElementById('mapInfoStyles')) {
            const style = document.createElement('style');
            style.id = 'mapInfoStyles';
            style.innerHTML = `
                @keyframes fadeInScale {
                    from { opacity: 0; transform: translate(-50%, -10px) scale(0.95); }
                    to { opacity: 1; transform: translate(-50%, 0) scale(1); }
                }
                .custom-map-info:hover { box-shadow: 0 0 40px rgba(0,228,255,0.6); }
            `;
            document.head.appendChild(style);
        }
        
        if (!isAlert) { // 健康点美化版本
            const deviceSn = get('device_sn','deviceSn');
            div.innerHTML = `
                <div style="display:flex;align-items:center;gap:24px;margin-bottom:22px;">
                    <img src="${avatarUrl}" style="width:72px;height:72px;border-radius:50%;border:3px solid #00e4ff;box-shadow:0 0 20px rgba(0,228,255,0.7);object-fit:cover;background:#001529;">
                    <div style="flex:1;">
                        <div style="font-size:22px;font-weight:700;letter-spacing:1px;color:#00e4ff;margin-bottom:8px;">${get('dept_name','deptName')}</div>
                        <div style="font-size:19px;color:#ffffff;font-weight:600;">${get('user_name','userName')}</div>
                        <div style="font-size:13px;color:#7ecfff;margin-top:8px;">设备编号: ${deviceSn}</div>
                    </div>
                </div>
                
                <div style="background:rgba(0,228,255,0.08);border:1px solid rgba(0,228,255,0.25);border-radius:14px;padding:20px;margin-bottom:20px;">
                    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:14px;">
                        <div><span style="color:#7ecfff;font-size:14px;">💓 心率：</span><span style="color:#fff;font-weight:600;font-size:17px;">${get('heartRate','heart_rate')} <span style="color:#bbb;font-size:12px;">bpm</span></span></div>
                        <div><span style="color:#7ecfff;font-size:14px;">🫁 血氧：</span><span style="color:#fff;font-weight:600;font-size:17px;">${get('bloodOxygen','blood_oxygen')} <span style="color:#bbb;font-size:12px;">%</span></span></div>
                        <div><span style="color:#7ecfff;font-size:14px;">🩸 血压：</span><span style="color:#fff;font-weight:600;font-size:17px;">${get('pressureHigh','pressure_high')}/${get('pressureLow','pressure_low')} <span style="color:#bbb;font-size:12px;">mmHg</span></span></div>
                        <div><span style="color:#7ecfff;font-size:14px;">🌡️ 体温：</span><span style="color:#fff;font-weight:600;font-size:17px;">${get('temperature','temp')} <span style="color:#bbb;font-size:12px;">℃</span></span></div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;">
                        <div><span style="color:#7ecfff;font-size:13px;">👣 步数：</span><span style="color:#fff;font-weight:500;">${get('step','steps')}</span></div>
                        <div><span style="color:#7ecfff;font-size:13px;">📏 距离：</span><span style="color:#fff;font-weight:500;">${get('distance','distance')}m</span></div>
                        <div><span style="color:#7ecfff;font-size:13px;">🔥 卡路里：</span><span style="color:#fff;font-weight:500;">${get('calorie','calories')}</span></div>
                    </div>
                </div>
                
                <div style="margin-bottom:18px;">
                    <div style="color:#7ecfff;font-size:14px;margin-bottom:10px;">📍 位置信息：</div>
                    <div id="locationInfo" style="color:#fff;font-size:14px;padding:14px;background:rgba(255,255,255,0.06);border-radius:10px;border:1px solid rgba(255,255,255,0.1);">正在获取...</div>
                </div>
                
                <div style="margin-bottom:20px;">
                    <span style="color:#7ecfff;font-size:14px;">⏰ 采集时间：</span><span style="color:#fff;">${get('timestamp')}</span>
                </div>
                
                <div style="display:flex;gap:18px;align-items:center;">
                    <a href="personal?deviceSn=${deviceSn}" target="_blank" 
                       style="padding:14px 32px;background:linear-gradient(135deg,#00e4ff,#0099cc);color:#001529;text-decoration:none;border-radius:14px;font-weight:700;font-size:16px;box-shadow:0 6px 18px rgba(0,228,255,0.4);transition:all 0.3s ease;display:inline-flex;align-items:center;gap:12px;" 
                       onmouseover="this.style.transform='translateY(-3px)';this.style.boxShadow='0 10px 25px rgba(0,228,255,0.6)'" 
                       onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 6px 18px rgba(0,228,255,0.4)'">
                        📊 查看个人大屏
                    </a>
                    <span style="flex:1"></span>
                    <span style="color:#00e4ff;cursor:pointer;font-size:30px;font-weight:700;padding:10px;border-radius:8px;transition:background 0.2s;" onclick="removeCustomMapInfo()" onmouseover="this.style.background='rgba(0,228,255,0.1)'" onmouseout="this.style.background='transparent'" title="关闭">×</span>
                </div>
            `;
        } else { // 告警点保持原有样式但略有美化
            const level = get('severity_level','severityLevel');
            const levelColor = level === 'critical' ? '#ff4d4f' : level === 'high' ? '#ffbb00' : '#ffe066';
            div.innerHTML = `
                <div style="display:flex;align-items:center;gap:20px;margin-bottom:14px;">
                    <img src="${avatarUrl}" style="width:60px;height:60px;border-radius:50%;border:3px solid #ff4d4f;box-shadow:0 0 12px rgba(255,77,79,0.5);object-fit:cover;background:#001529;">
                    <div>
                        <div style="font-size:19px;font-weight:700;letter-spacing:1px;">${get('dept_name','deptName')}</div>
                        <div style="font-size:17px;color:#ff4d4f;font-weight:600;margin-top:3px;">${get('user_name','userName')}</div>
                    </div>
                </div>
                <div style="display:flex;gap:20px;flex-wrap:wrap;margin-bottom:10px;">
                    <div><span style="color:#7ecfff;">🚨 告警类别：</span><span style="color:${levelColor};font-weight:700;">${get('alert_type','alertType','-')}</span></div>
                    <div><span style="color:#7ecfff;">⚡ 级别：</span><span style="color:${levelColor};font-weight:700;">${level||'-'}</span></div>
                    <div><span style="color:#7ecfff;">📊 状态：</span><span style="color:#ff9c00;font-weight:700;">${get('alert_status','status','-')}</span></div>
                </div>
                <div style="margin-bottom:10px;">
                    <span style="color:#7ecfff;">📍 位置信息：</span><span id="locationInfo">正在获取...</span>
                </div>
                <div style="margin-bottom:10px;">
                    <span style="color:#7ecfff;">⏰ 告警时间：</span>${get('alert_timestamp','timestamp','-')}
                </div>
                <div style="display:flex;gap:20px;align-items:center;">
                    <button onclick="handleAlert('${get('alert_id','alertId')}')" style="padding:10px 26px;background:${levelColor};color:#001529;border:none;border-radius:8px;cursor:pointer;font-weight:700;font-size:15px;box-shadow:0 4px 12px ${levelColor}44;transition:all 0.2s;" onmouseover="this.style.transform='translateY(-1px)'" onmouseout="this.style.transform='translateY(0)'">🔧 一键处理</button>
                    <span style="flex:1"></span>
                    <span style="color:#ff4d4f;cursor:pointer;font-size:26px;font-weight:700;" onclick="removeCustomMapInfo()">×</span>
                </div>
            `;
        }
        
        document.body.appendChild(div);
        
        // 获取位置信息
        const longitude = get('longitude');
        const latitude = get('latitude');
        if (longitude && latitude) {
            reverseGeocode(longitude, latitude)
                .then(address => {
                    const locationInfo = document.getElementById('locationInfo');
                    if (locationInfo) locationInfo.textContent = address || '未知位置';
                })
                .catch(error => {
                    const locationInfo = document.getElementById('locationInfo');
                    if (locationInfo) locationInfo.textContent = '获取位置信息失败';
                });
        }
    };
    
    // 增强版地图数据更新函数 - 添加员工标签
    window.updateMapData = function(data) {
        if (!data || !map || !loca) return;
        const {alerts, healths} = filterData(data);
        const f = [];
        
        // 处理告警数据
        alerts.forEach(a => {
            if ((a.longitude || a.longitude === 0) && (a.latitude || a.latitude === 0)) {
                f.push({
                    type: 'Feature',
                    geometry: {type: 'Point', coordinates: [+a.longitude, +a.latitude]},
                    properties: {...a, type: 'alert'}
                });
            }
        });
        
        // 处理健康数据，添加用户标签字段
        healths.forEach(h => {
            if ((h.longitude || h.longitude === 0) && (h.latitude || h.latitude === 0)) {
                f.push({
                    type: 'Feature',
                    geometry: {type: 'Point', coordinates: [+h.longitude, +h.latitude]},
                    properties: {
                        ...h,
                        user_label: `${h.deptName||'未知部门'}-${h.userName||'未知用户'}`, // 员工标签
                        type: 'health'
                    }
                });
            }
        });
        
        const geoJSON = {type: 'FeatureCollection', features: f};
        const criticalAlerts = {type: 'FeatureCollection', features: geoJSON.features.filter(f => f.properties.severity_level === 'critical')};
        const highAlerts = {type: 'FeatureCollection', features: geoJSON.features.filter(f => f.properties.severity_level === 'high' || f.properties.severity_level === 'medium')};
        const healthData = {type: 'FeatureCollection', features: geoJSON.features.filter(f => f.properties.type === 'health')};
        
        // 更新图层数据源
        if (breathRed) breathRed.setSource(new Loca.GeoJSONSource({data: criticalAlerts}));
        if (breathYellow) breathYellow.setSource(new Loca.GeoJSONSource({data: highAlerts}));
        if (breathGreen) breathGreen.setSource(new Loca.GeoJSONSource({data: healthData}));
        
        // 创建或更新文字标签图层
        if (!window.breathGreenText && healthData.features.length > 0 && loca) {
            window.breathGreenText = new Loca.TextLayer({
                loca,
                zIndex: 114, // 高于圆点层
                opacity: 1,
                visible: true,
                zooms: [13, 22], // 只在较大缩放级别显示
            });
            
            window.breathGreenText.setSource(new Loca.GeoJSONSource({data: healthData}));
            window.breathGreenText.setStyle({
                text: {
                    field: 'user_label', // 使用标签字段
                    style: {
                        fontSize: 11,
                        fontFamily: '"Microsoft YaHei", Arial, sans-serif',
                        fontWeight: 'bold',
                        fillColor: '#ffffff',
                        strokeColor: '#1f4e79',
                        strokeWidth: 2,
                    }
                },
                offset: [0, -24], // 显示在圆点上方
                selectStyle: {
                    text: {
                        style: {
                            fillColor: '#00e4ff',
                            fontSize: 12,
                        }
                    }
                }
            });
            
            loca.add(window.breathGreenText);
            console.log('✅ 文字标签图层已创建');
        } else if (window.breathGreenText) {
            window.breathGreenText.setSource(new Loca.GeoJSONSource({data: healthData}));
        }
        
        // 设置地图中心（优先显示有数据的位置）
        if (f.length > 0) {
            const center = f.find(item => item.geometry && item.geometry.coordinates);
            if (center && map) {
                const [lng, lat] = center.geometry.coordinates;
                map.setCenter([lng, lat]);
            }
        }
    };
    
    console.log('✅ 地图增强功能应用完成！');
    console.log('📋 功能清单：');
    console.log('  1. ✅ 绿色圆点上方显示员工名字（部门-姓名）');
    console.log('  2. ✅ 健康信息框美化升级');
    console.log('  3. ✅ 添加个人大屏链接按钮');
    console.log('💡 提示：放大地图到13级以上可看到员工标签');
})(); 