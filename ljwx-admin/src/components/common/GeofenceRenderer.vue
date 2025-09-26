<script setup lang="tsx">
import { ref, watch, onUnmounted } from 'vue';
import type { Api } from '@/typings';

interface Props {
  /** 地图实例 */
  map: AMap.Map | null;
  /** 围栏数据 */
  geofenceData: Api.Geofence.Geofence[];
  /** 是否可编辑 */
  editable?: boolean;
  /** 活跃围栏颜色 */
  activeColor?: string;
  /** 非活跃围栏颜色 */
  inactiveColor?: string;
  /** 编辑中的围栏颜色 */
  editingColor?: string;
  /** 透明度 */
  fillOpacity?: number;
}

interface Emits {
  (e: 'geofenceClick', geofence: Api.Geofence.Geofence): void;
  (e: 'geofenceEdit', geofence: Api.Geofence.Geofence, area: any): void;
}

const props = withDefaults(defineProps<Props>(), {
  editable: false,
  activeColor: '#1b38d3',
  inactiveColor: '#999999',
  editingColor: '#ff4444',
  fillOpacity: 0.2
});

const emit = defineEmits<Emits>();

const polygons = ref<Map<number, AMap.Polygon>>(new Map());
const polyEditor = ref<AMap.PolygonEditor | null>(null);
const currentEditingId = ref<number | null>(null);

// 清除所有围栏
function clearGeofences() {
  if (props.map && polygons.value.size > 0) {
    const allPolygons = Array.from(polygons.value.values());
    props.map.remove(allPolygons);
    polygons.value.clear();
  }
  stopEditing();
}

// 渲染围栏
function renderGeofences() {
  if (!props.map || !props.geofenceData) {
    return;
  }
  
  clearGeofences();
  
  props.geofenceData.forEach(geofence => {
    if (geofence.area && geofence.id !== undefined) {
      try {
        const area = JSON.parse(geofence.area);
        if (area.type === 'Polygon' && area.coordinates && area.coordinates[0]) {
          const color = geofence.isActive ? props.activeColor : props.inactiveColor;
          
          const polygon = new AMap.Polygon({
            path: area.coordinates[0],
            strokeColor: color,
            strokeOpacity: 1,
            strokeWeight: 2,
            fillColor: color,
            fillOpacity: props.fillOpacity,
            zIndex: 50,
            extData: geofence // 存储围栏数据
          });
          
          // 添加点击事件
          polygon.on('click', (e: any) => {
            e.stopPropagation();
            emit('geofenceClick', geofence);
          });
          
          props.map.add(polygon);
          polygons.value.set(geofence.id, polygon);
        }
      } catch (error) {
        console.error('解析围栏区域失败:', error);
      }
    }
  });
}

// 高亮围栏
function highlightGeofence(geofenceId: number, highlight: boolean = true) {
  const polygon = polygons.value.get(geofenceId);
  if (polygon) {
    const geofence = polygon.getExtData() as Api.Geofence.Geofence;
    const color = highlight 
      ? props.editingColor 
      : (geofence.isActive ? props.activeColor : props.inactiveColor);
    
    polygon.setOptions({
      strokeColor: color,
      fillColor: color,
      strokeWeight: highlight ? 3 : 2,
      zIndex: highlight ? 100 : 50
    });
  }
}

// 定位到围栏
function focusOnGeofence(geofenceId: number) {
  const polygon = polygons.value.get(geofenceId);
  if (polygon && props.map) {
    const bounds = polygon.getBounds();
    if (bounds) {
      props.map.setBounds(bounds);
    }
  }
}

// 开始编辑围栏
function startEditing(geofenceId: number) {
  if (!props.editable || !props.map) return false;
  
  stopEditing();
  
  const polygon = polygons.value.get(geofenceId);
  if (!polygon) return false;
  
  if (!polyEditor.value) {
    polyEditor.value = new AMap.PolygonEditor(props.map);
  }
  
  currentEditingId.value = geofenceId;
  highlightGeofence(geofenceId, true);
  
  polyEditor.value.setTarget(polygon);
  polyEditor.value.open();
  
  // 监听编辑结束事件
  polyEditor.value.on('end', () => {
    const geofence = polygon.getExtData() as Api.Geofence.Geofence;
    const path = polygon.getPath();
    const coordinates = path.map((point: any) => [point.lng, point.lat]);
    
    const geoJson = {
      type: 'Polygon',
      coordinates: [coordinates]
    };
    
    emit('geofenceEdit', geofence, geoJson);
    stopEditing();
  });
  
  return true;
}

// 停止编辑
function stopEditing() {
  if (polyEditor.value) {
    polyEditor.value.close();
  }
  
  if (currentEditingId.value !== null) {
    highlightGeofence(currentEditingId.value, false);
    currentEditingId.value = null;
  }
}

// 创建新围栏的临时多边形
function createTempPolygon(center?: [number, number]) {
  if (!props.map || !props.editable) return null;
  
  const defaultCenter = center || props.map.getCenter();
  const centerLng = typeof defaultCenter === 'object' && 'lng' in defaultCenter ? defaultCenter.lng : defaultCenter[0];
  const centerLat = typeof defaultCenter === 'object' && 'lat' in defaultCenter ? defaultCenter.lat : defaultCenter[1];
  
  // 创建一个默认的矩形围栏
  const offset = 0.005; // 大约500米
  const tempPolygon = new AMap.Polygon({
    path: [
      [centerLng - offset, centerLat + offset],
      [centerLng + offset, centerLat + offset],
      [centerLng + offset, centerLat - offset],
      [centerLng - offset, centerLat - offset]
    ],
    strokeColor: props.editingColor,
    strokeOpacity: 1,
    strokeWeight: 3,
    fillColor: props.editingColor,
    fillOpacity: props.fillOpacity,
    zIndex: 100
  });
  
  props.map.add(tempPolygon);
  
  if (!polyEditor.value) {
    polyEditor.value = new AMap.PolygonEditor(props.map);
  }
  
  polyEditor.value.setTarget(tempPolygon);
  polyEditor.value.open();
  
  return tempPolygon;
}

// 获取编辑结果
function getEditResult(tempPolygon: AMap.Polygon) {
  const path = tempPolygon.getPath();
  const coordinates = path.map((point: any) => [point.lng, point.lat]);
  
  const geoJson = {
    type: 'Polygon',
    coordinates: [coordinates]
  };
  
  return geoJson;
}

// 移除临时多边形
function removeTempPolygon(tempPolygon: AMap.Polygon) {
  if (props.map) {
    props.map.remove(tempPolygon);
  }
  stopEditing();
}

// 监听围栏数据变化
watch(() => props.geofenceData, () => {
  renderGeofences();
}, { deep: true });

// 监听地图实例变化
watch(() => props.map, (newMap) => {
  if (newMap) {
    renderGeofences();
  }
});

// 暴露方法
defineExpose({
  clearGeofences,
  renderGeofences,
  highlightGeofence,
  focusOnGeofence,
  startEditing,
  stopEditing,
  createTempPolygon,
  getEditResult,
  removeTempPolygon
});

onUnmounted(() => {
  stopEditing();
  clearGeofences();
});
</script>

<template>
  <div></div>
</template>