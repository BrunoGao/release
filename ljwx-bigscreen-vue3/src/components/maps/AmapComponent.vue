<template>
  <div class="amap-container">
    <div 
      :id="containerId" 
      class="amap-canvas"
      :style="{ width: '100%', height: '100%' }"
    ></div>
    
    <!-- 地图控制面板 -->
    <div class="map-controls" v-if="showControls">
      <div class="control-group">
        <button 
          class="control-btn"
          :class="{ active: view3D }"
          @click="toggle3D"
          title="3D视图"
        >
          <span class="icon">🏢</span>
        </button>
        
        <button 
          class="control-btn"
          @click="resetView"
          title="重置视角"
        >
          <span class="icon">🎯</span>
        </button>
        
        <button 
          class="control-btn"
          :class="{ active: showLabels }"
          @click="toggleLabels"
          title="显示/隐藏标签"
        >
          <span class="icon">🏷️</span>
        </button>
      </div>
      
      <div class="control-group">
        <select v-model="currentMapStyle" @change="changeMapStyle" class="style-selector">
          <option value="amap://styles/blue">蓝色主题</option>
          <option value="amap://styles/dark">深色主题</option>
          <option value="amap://styles/light">浅色主题</option>
          <option value="amap://styles/fresh">清新主题</option>
        </select>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div v-if="loading" class="map-loading">
      <div class="loading-spinner"></div>
      <span>正在加载地图...</span>
    </div>
    
    <!-- 错误提示 -->
    <div v-if="error" class="map-error">
      <span class="error-icon">⚠️</span>
      <span>{{ error }}</span>
      <button @click="retryLoad" class="retry-btn">重试</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

// Props
interface Props {
  containerId?: string
  center?: [number, number]
  zoom?: number
  pitch?: number
  rotation?: number
  mapStyle?: string
  showControls?: boolean
  showLabels?: boolean
  view3D?: boolean
  geoData?: Array<{
    id: string
    position: [number, number]
    level: 'critical' | 'high' | 'medium' | 'low' | 'healthy'
    title: string
    content?: string
    data?: any
  }>
}

const props = withDefaults(defineProps<Props>(), {
  containerId: 'amap-container',
  center: () => [116.397428, 39.90923], // 北京
  zoom: 17,
  pitch: 45,
  rotation: 0,
  mapStyle: 'amap://styles/blue',
  showControls: true,
  showLabels: false,
  view3D: true,
  geoData: () => []
})

// Emits
const emit = defineEmits<{
  mapReady: [map: any]
  markerClick: [data: any]
  mapClick: [position: [number, number]]
  error: [error: string]
}>()

// State
const loading = ref(true)
const error = ref('')
const currentMapStyle = ref(props.mapStyle)
const view3D = ref(props.view3D)
const showLabels = ref(props.showLabels)

// 地图实例
let map: any = null
let loca: any = null
let markerLayers: any[] = []

// 高德地图API加载
const loadAmapAPI = () => {
  return new Promise((resolve, reject) => {
    if (window.AMap && window.Loca) {
      resolve({ AMap: window.AMap, Loca: window.Loca })
      return
    }

    // 检查是否已经开始加载
    if (window.amapLoading) {
      // 等待加载完成
      const checkInterval = setInterval(() => {
        if (window.AMap && window.Loca) {
          clearInterval(checkInterval)
          resolve({ AMap: window.AMap, Loca: window.Loca })
        }
      }, 100)
      return
    }

    window.amapLoading = true

    // 动态加载高德地图API
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=YOUR_AMAP_KEY&plugin=AMap.Scale,AMap.ToolBar,AMap.ControlBar&callback=initAmapCallback`
    
    window.initAmapCallback = () => {
      // 加载Loca
      const locaScript = document.createElement('script')
      locaScript.src = 'https://webapi.amap.com/loca?v=2.0.0'
      locaScript.onload = () => {
        window.amapLoading = false
        resolve({ AMap: window.AMap, Loca: window.Loca })
      }
      locaScript.onerror = () => {
        window.amapLoading = false
        reject(new Error('Loca加载失败'))
      }
      document.head.appendChild(locaScript)
    }
    
    script.onerror = () => {
      window.amapLoading = false
      reject(new Error('高德地图API加载失败'))
    }
    
    document.head.appendChild(script)
  })
}

// 初始化地图
const initMap = async () => {
  try {
    loading.value = true
    error.value = ''

    const { AMap, Loca } = await loadAmapAPI()

    await nextTick()

    // 创建地图实例
    map = new AMap.Map(props.containerId, {
      center: props.center,
      zoom: props.zoom,
      pitch: view3D.value ? props.pitch : 0,
      rotation: props.rotation,
      mapStyle: currentMapStyle.value,
      showLabel: showLabels.value,
      viewMode: view3D.value ? '3D' : '2D',
      features: ['bg', 'road', 'building', 'point'],
      resizeEnable: true,
      rotateEnable: true,
      pitchEnable: true,
      zoomEnable: true,
      dragEnable: true
    })

    // 添加控件
    map.addControl(new AMap.Scale({
      position: {
        top: '20px',
        right: '20px'
      }
    }))

    map.addControl(new AMap.ControlBar({
      position: {
        top: '60px',
        right: '20px'
      },
      showZoomBar: true,
      showControlButton: true
    }))

    // 创建Loca实例
    loca = new Loca.Container({
      map
    })

    // 地图加载完成事件
    map.on('complete', () => {
      loading.value = false
      emit('mapReady', map)
      
      // 初始化标点图层
      if (props.geoData.length > 0) {
        createMarkerLayers()
      }
    })

    // 地图点击事件
    map.on('click', (e: any) => {
      emit('mapClick', [e.lnglat.lng, e.lnglat.lat])
    })

  } catch (err) {
    loading.value = false
    error.value = err instanceof Error ? err.message : '地图初始化失败'
    emit('error', error.value)
  }
}

// 创建标点图层
const createMarkerLayers = () => {
  if (!loca || !props.geoData.length) return

  // 清除现有图层
  clearLayers()

  // 按级别分组数据
  const groupedData = props.geoData.reduce((acc, item) => {
    if (!acc[item.level]) acc[item.level] = []
    acc[item.level].push({
      coordinate: item.position,
      id: item.id,
      title: item.title,
      content: item.content || '',
      level: item.level,
      data: item.data || {}
    })
    return acc
  }, {} as Record<string, any[]>)

  // 图层配置
  const layerConfigs = {
    critical: { color: '#ff4444', size: 60, zIndex: 113 },
    high: { color: '#ff6600', size: 50, zIndex: 112 },
    medium: { color: '#ffbb00', size: 40, zIndex: 111 },
    low: { color: '#00ff9d', size: 30, zIndex: 110 },
    healthy: { color: '#00e4ff', size: 20, zIndex: 109 }
  }

  // 创建各级别图层
  Object.entries(groupedData).forEach(([level, data]) => {
    const config = layerConfigs[level as keyof typeof layerConfigs]
    if (!config || !data.length) return

    // 创建散点图层
    const scatterLayer = new Loca.ScatterLayer({
      loca,
      zIndex: config.zIndex,
      opacity: 0.8,
      visible: true,
      zooms: [3, 22]
    })

    // 设置数据源
    scatterLayer.setSource({
      type: 'FeatureCollection',
      features: data.map(item => ({
        type: 'Feature',
        properties: item,
        geometry: {
          type: 'Point',
          coordinates: item.coordinate
        }
      }))
    })

    // 设置样式
    scatterLayer.setStyle({
      radius: config.size / 2,
      color: config.color,
      borderWidth: 2,
      borderColor: '#ffffff',
      opacity: 0.8,
      // 动画效果
      animation: {
        enable: true,
        type: 'breathing',
        duration: 2000,
        repeat: -1
      }
    })

    // 点击事件
    scatterLayer.on('click', (e: any) => {
      const feature = e.feature
      if (feature && feature.properties) {
        emit('markerClick', feature.properties)
        showMarkerInfo(feature.properties)
      }
    })

    // 添加到容器
    loca.add(scatterLayer)
    markerLayers.push(scatterLayer)
  })

  loca.render()
}

// 显示标点信息
const showMarkerInfo = (data: any) => {
  if (!map) return

  // 创建信息窗体
  const infoWindow = new AMap.InfoWindow({
    content: `
      <div class="marker-info">
        <div class="marker-title">${data.title}</div>
        <div class="marker-level ${data.level}">${getLevelText(data.level)}</div>
        ${data.content ? `<div class="marker-content">${data.content}</div>` : ''}
        <div class="marker-actions">
          <button onclick="viewDetails('${data.id}')">查看详情</button>
        </div>
      </div>
    `,
    offset: [0, -30],
    closeWhenClickMap: true
  })

  infoWindow.open(map, data.coordinate)
}

// 获取级别文本
const getLevelText = (level: string) => {
  const levelMap = {
    critical: '严重',
    high: '重要', 
    medium: '一般',
    low: '轻微',
    healthy: '健康'
  }
  return levelMap[level as keyof typeof levelMap] || level
}

// 清除图层
const clearLayers = () => {
  if (loca && markerLayers.length) {
    markerLayers.forEach(layer => {
      loca.remove(layer)
    })
    markerLayers = []
    loca.render()
  }
}

// 控制方法
const toggle3D = () => {
  if (!map) return
  
  view3D.value = !view3D.value
  
  map.setViewMode(view3D.value ? '3D' : '2D')
  map.setPitch(view3D.value ? props.pitch : 0)
}

const resetView = () => {
  if (!map) return
  
  map.setCenter(props.center)
  map.setZoom(props.zoom)
  map.setPitch(view3D.value ? props.pitch : 0)
  map.setRotation(props.rotation)
}

const toggleLabels = () => {
  if (!map) return
  
  showLabels.value = !showLabels.value
  map.setMapStyle(currentMapStyle.value, showLabels.value)
}

const changeMapStyle = () => {
  if (!map) return
  
  map.setMapStyle(currentMapStyle.value, showLabels.value)
}

const retryLoad = () => {
  error.value = ''
  initMap()
}

// 监听数据变化
watch(() => props.geoData, (newData) => {
  if (map && loca && newData) {
    createMarkerLayers()
  }
}, { deep: true })

// 暴露方法
defineExpose({
  getMap: () => map,
  getLoca: () => loca,
  clearLayers,
  createMarkerLayers,
  toggle3D,
  resetView
})

// 全局方法（供信息窗体使用）
window.viewDetails = (id: string) => {
  const item = props.geoData.find(d => d.id === id)
  if (item) {
    emit('markerClick', item)
  }
}

// 生命周期
onMounted(() => {
  initMap()
})

onUnmounted(() => {
  clearLayers()
  if (map) {
    map.destroy()
    map = null
  }
  if (loca) {
    loca.destroy()
    loca = null
  }
})
</script>

<style lang="scss" scoped>
.amap-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
  border-radius: 4px;
}

.amap-canvas {
  width: 100%;
  height: 100%;
}

// ========== 地图控制面板 ==========
.map-controls {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-group {
  display: flex;
  gap: 4px;
  background: rgba(0, 21, 41, 0.9);
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 4px;
  padding: 4px;
  backdrop-filter: blur(10px);
}

.control-btn {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 3px;
  background: rgba(0, 21, 41, 0.8);
  color: #00e4ff;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    border-color: #00e4ff;
    background: rgba(0, 228, 255, 0.1);
    box-shadow: 0 0 10px rgba(0, 228, 255, 0.3);
  }
  
  &.active {
    background: #00e4ff;
    color: #001529;
    border-color: #00e4ff;
  }
  
  .icon {
    font-size: 14px;
  }
}

.style-selector {
  padding: 6px 8px;
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 3px;
  background: rgba(0, 21, 41, 0.9);
  color: #00e4ff;
  font-size: 12px;
  min-width: 100px;
  
  &:focus {
    outline: none;
    border-color: #00e4ff;
  }
  
  option {
    background: #001529;
    color: #00e4ff;
  }
}

// ========== 加载和错误状态 ==========
.map-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  background: rgba(0, 21, 41, 0.9);
  border: 1px solid rgba(0, 228, 255, 0.3);
  border-radius: 6px;
  color: #00e4ff;
  font-size: 14px;
  z-index: 1001;
  
  .loading-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid rgba(0, 228, 255, 0.3);
    border-top: 2px solid #00e4ff;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

.map-error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 15px 20px;
  background: rgba(41, 0, 0, 0.9);
  border: 1px solid rgba(255, 68, 68, 0.5);
  border-radius: 6px;
  color: #ff4444;
  font-size: 14px;
  z-index: 1001;
  
  .error-icon {
    font-size: 18px;
  }
  
  .retry-btn {
    padding: 4px 8px;
    border: 1px solid #ff4444;
    border-radius: 3px;
    background: transparent;
    color: #ff4444;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s ease;
    
    &:hover {
      background: rgba(255, 68, 68, 0.1);
    }
  }
}

// ========== 动画 ==========
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

<style>
/* 全局样式 - 信息窗体 */
.marker-info {
  min-width: 200px;
  padding: 12px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.marker-title {
  font-size: 16px;
  font-weight: 600;
  color: #001529;
  margin-bottom: 8px;
}

.marker-level {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 8px;
}

.marker-level.critical {
  background: #ff4444;
  color: white;
}

.marker-level.high {
  background: #ff6600;
  color: white;
}

.marker-level.medium {
  background: #ffbb00;
  color: white;
}

.marker-level.low {
  background: #00ff9d;
  color: #001529;
}

.marker-level.healthy {
  background: #00e4ff;
  color: #001529;
}

.marker-content {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
  line-height: 1.4;
}

.marker-actions button {
  padding: 6px 12px;
  border: 1px solid #00e4ff;
  border-radius: 4px;
  background: #00e4ff;
  color: white;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.marker-actions button:hover {
  background: #0099cc;
  border-color: #0099cc;
}

/* 高德地图控件样式调整 */
.amap-icon {
  background-image: none !important;
}

.amap-control-bar {
  background: rgba(0, 21, 41, 0.9) !important;
  border: 1px solid rgba(0, 228, 255, 0.3) !important;
}

.amap-scale-num {
  color: #00e4ff !important;
  background: rgba(0, 21, 41, 0.9) !important;
}
</style>