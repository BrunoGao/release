// 地图渲染修复补丁
// 用于修复 breathRed, breathYellow, breathGreen 不显示的问题

// 覆盖原有的 updateMapData 函数，添加强制渲染
(function() {
    // 保存原始函数
    const originalUpdateMapData = window.updateMapData;
    
    // 重写函数
    window.updateMapData = function(data) {
        console.log('🔧 使用修复版本的 updateMapData');
        
        // 调用原始函数
        if (originalUpdateMapData) {
            originalUpdateMapData(data);
        }
        
        // 添加额外的渲染逻辑
        setTimeout(() => {
            try {
                console.log('🎨 执行地图渲染修复');
                
                // 检查图层是否存在
                if (window.breathRed) {
                    console.log('✅ breathRed 图层存在');
                    // 强制设置可见性
                    window.breathRed.setVisible(true);
                }
                
                if (window.breathYellow) {
                    console.log('✅ breathYellow 图层存在');
                    window.breathYellow.setVisible(true);
                }
                
                if (window.breathGreen) {
                    console.log('✅ breathGreen 图层存在');
                    window.breathGreen.setVisible(true);
                }
                
                // 强制重新渲染
                if (window.loca) {
                    if (window.loca.render) {
                        window.loca.render();
                        console.log('🎨 Loca 容器渲染完成');
                    }
                    
                    if (window.loca.animate && window.loca.animate.start) {
                        window.loca.animate.start();
                        console.log('🎬 Loca 动画重启完成');
                    }
                }
                
                // 单独渲染每个图层
                ['breathRed', 'breathYellow', 'breathGreen'].forEach(layerName => {
                    const layer = window[layerName];
                    if (layer) {
                        if (layer.render) layer.render();
                        if (layer.show) layer.show();
                        console.log(`🔧 ${layerName} 图层渲染完成`);
                    }
                });
                
            } catch (error) {
                console.error('❌ 地图渲染修复失败:', error);
            }
        }, 100); // 延迟100ms确保数据设置完成
    };
})();

console.log('🚀 地图渲染修复补丁已加载'); 