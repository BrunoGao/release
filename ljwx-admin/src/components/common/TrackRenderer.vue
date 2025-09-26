<script setup lang="tsx">
import { ref, watch, onUnmounted } from 'vue';
import type { Api } from '@/typings';

interface Props {
  /** 地图实例 */
  map: AMap.Map | null;
  /** 轨迹数据 */
  trackData: Api.Track.TrackPoint[];
  /** 是否显示起点终点标记 */
  showMarkers?: boolean;
  /** 轨迹线颜色 */
  strokeColor?: string;
  /** 轨迹线宽度 */
  strokeWeight?: number;
  /** 轨迹线透明度 */
  strokeOpacity?: number;
  /** 是否显示方向箭头 */
  showDirection?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showMarkers: true,
  strokeColor: '#1b38d3',
  strokeWeight: 5,
  strokeOpacity: 0.8,
  showDirection: true
});

const trackPolyline = ref<AMap.Polyline | null>(null);
const markers = ref<AMap.Marker[]>([]);

// 清除轨迹显示
function clearTrack() {
  if (trackPolyline.value && props.map) {
    props.map.remove(trackPolyline.value);
    trackPolyline.value = null;
  }
  
  if (markers.value.length > 0 && props.map) {
    props.map.remove(markers.value);
    markers.value = [];
  }
}

// 渲染轨迹
function renderTrack() {
  if (!props.map || !props.trackData || props.trackData.length === 0) {
    return;
  }
  
  clearTrack();
  
  const path = props.trackData.map(point => [point.longitude, point.latitude]);
  
  if (path.length === 1) {
    // 单点显示
    const marker = new AMap.Marker({
      position: path[0],
      title: '位置点',
      content: `<div style="
        width: 12px; 
        height: 12px; 
        background: ${props.strokeColor}; 
        border: 2px solid white; 
        border-radius: 50%;
        box-shadow: 0 0 4px rgba(0,0,0,0.3);
      "></div>`
    });
    
    props.map.add(marker);
    markers.value.push(marker);
    props.map.setCenter(path[0]);
  } else if (path.length > 1) {
    // 轨迹线显示
    trackPolyline.value = new AMap.Polyline({
      path: path,
      strokeColor: props.strokeColor,
      strokeWeight: props.strokeWeight,
      strokeOpacity: props.strokeOpacity,
      showDir: props.showDirection,
      lineJoin: 'round',
      lineCap: 'round'
    });
    
    props.map.add(trackPolyline.value);
    
    // 添加起点终点标记
    if (props.showMarkers) {
      const startMarker = new AMap.Marker({
        position: path[0],
        title: `起点 - ${new Date(props.trackData[0].timestamp).toLocaleString()}`,
        content: `<div style="
          width: 12px; 
          height: 12px; 
          background: #00ff00; 
          border: 2px solid white; 
          border-radius: 50%;
          box-shadow: 0 0 4px rgba(0,0,0,0.3);
        "></div>`
      });
      
      const endMarker = new AMap.Marker({
        position: path[path.length - 1],
        title: `终点 - ${new Date(props.trackData[props.trackData.length - 1].timestamp).toLocaleString()}`,
        content: `<div style="
          width: 12px; 
          height: 12px; 
          background: #ff0000; 
          border: 2px solid white; 
          border-radius: 50%;
          box-shadow: 0 0 4px rgba(0,0,0,0.3);
        "></div>`
      });
      
      props.map.add([startMarker, endMarker]);
      markers.value.push(startMarker, endMarker);
    }
    
    // 自适应视野
    props.map.setFitView([trackPolyline.value], false, [50, 50, 50, 50]);
  }
}

// 轨迹回放功能
const playbackTimer = ref<NodeJS.Timeout | null>(null);
const playbackIndex = ref(0);
const playbackMarker = ref<AMap.Marker | null>(null);

function startPlayback(speed: number = 1000) {
  if (!props.trackData || props.trackData.length < 2) {
    return false;
  }
  
  stopPlayback();
  clearTrack();
  
  playbackIndex.value = 0;
  const playedPath: [number, number][] = [];
  
  playbackTimer.value = setInterval(() => {
    if (playbackIndex.value >= props.trackData.length) {
      stopPlayback();
      return;
    }
    
    const currentPoint = props.trackData[playbackIndex.value];
    const position: [number, number] = [currentPoint.longitude, currentPoint.latitude];
    playedPath.push(position);
    
    // 更新当前位置标记
    if (playbackMarker.value) {
      props.map?.remove(playbackMarker.value);
    }
    
    playbackMarker.value = new AMap.Marker({
      position: position,
      title: `时间: ${new Date(currentPoint.timestamp).toLocaleString()}`,
      content: `<div style="
        width: 16px; 
        height: 16px; 
        background: #0066ff; 
        border: 3px solid white; 
        border-radius: 50%;
        box-shadow: 0 0 6px rgba(0,102,255,0.5);
        animation: pulse 1.5s infinite;
      "></div>
      <style>
        @keyframes pulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.2); }
          100% { transform: scale(1); }
        }
      </style>`
    });
    
    props.map?.add(playbackMarker.value);
    
    // 更新已播放的轨迹
    if (trackPolyline.value) {
      props.map?.remove(trackPolyline.value);
    }
    
    if (playedPath.length > 1) {
      trackPolyline.value = new AMap.Polyline({
        path: playedPath,
        strokeColor: props.strokeColor,
        strokeWeight: props.strokeWeight,
        strokeOpacity: props.strokeOpacity,
        lineJoin: 'round',
        lineCap: 'round'
      });
      props.map?.add(trackPolyline.value);
    }
    
    props.map?.setCenter(position);
    playbackIndex.value++;
  }, speed);
  
  return true;
}

function stopPlayback() {
  if (playbackTimer.value) {
    clearInterval(playbackTimer.value);
    playbackTimer.value = null;
  }
  
  if (playbackMarker.value && props.map) {
    props.map.remove(playbackMarker.value);
    playbackMarker.value = null;
  }
  
  // 恢复完整轨迹显示
  renderTrack();
}

function isPlaying() {
  return playbackTimer.value !== null;
}

// 监听轨迹数据变化
watch(() => props.trackData, () => {
  renderTrack();
}, { deep: true });

// 监听地图实例变化
watch(() => props.map, (newMap) => {
  if (newMap) {
    renderTrack();
  }
});

// 暴露方法
defineExpose({
  clearTrack,
  renderTrack,
  startPlayback,
  stopPlayback,
  isPlaying
});

onUnmounted(() => {
  stopPlayback();
  clearTrack();
});
</script>

<template>
  <div></div>
</template>