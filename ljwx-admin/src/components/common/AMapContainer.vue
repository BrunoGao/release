<script setup lang="tsx">
import { onMounted, onUnmounted, ref, watch, nextTick } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';
import { useMessage } from 'naive-ui';

interface Props {
  /** 地图高度 */
  height?: string;
  /** 地图中心点 */
  center?: [number, number];
  /** 缩放级别 */
  zoom?: number;
  /** 地图ID，用于多个地图实例 */
  mapId?: string;
  /** 是否显示缩放控件 */
  showZoomControl?: boolean;
  /** 是否显示地图类型控件 */
  showMapTypeControl?: boolean;
  /** 需要加载的插件 */
  plugins?: string[];
}

interface Emits {
  (e: 'mapReady', map: AMap.Map): void;
  (e: 'click', event: any): void;
}

const props = withDefaults(defineProps<Props>(), {
  height: '400px',
  center: () => [116.397428, 39.90923],
  zoom: 12,
  mapId: 'amap-container',
  showZoomControl: true,
  showMapTypeControl: false,
  plugins: () => ['AMap.Polygon', 'AMap.PolygonEditor', 'AMap.Polyline', 'AMap.Marker', 'AMap.Circle', 'AMap.Rectangle']
});

const emit = defineEmits<Emits>();
const message = useMessage();

const map = ref<AMap.Map | null>(null);
const mapContainer = ref<HTMLElement>();
const loading = ref(false);

// 初始化地图
async function initMap() {
  if (map.value || !mapContainer.value) return;
  
  loading.value = true;
  try {
    await AMapLoader.load({
      key: '7de0c6b90cb13571ce931ca75a66c6e7', // 应该从环境变量获取
      version: '2.0',
      plugins: props.plugins
    });

    map.value = new AMap.Map(mapContainer.value, {
      zoom: props.zoom,
      center: props.center,
      showBuildingBlock: true,
      showLabel: true,
      mapStyle: 'amap://styles/normal'
    });

    // 添加控件
    if (props.showZoomControl) {
      map.value.addControl(new AMap.Scale());
      map.value.addControl(new AMap.ToolBar({
        position: {
          top: '110px',
          right: '40px'
        }
      }));
    }

    if (props.showMapTypeControl) {
      map.value.addControl(new AMap.MapType());
    }

    // 绑定事件
    map.value.on('click', (e: any) => {
      emit('click', e);
    });

    emit('mapReady', map.value);
    message.success('地图加载完成');
  } catch (error) {
    console.error('地图初始化失败:', error);
    message.error('地图加载失败');
  } finally {
    loading.value = false;
  }
}

// 销毁地图
function destroyMap() {
  if (map.value) {
    map.value.destroy();
    map.value = null;
  }
}

// 设置地图中心点
function setCenter(center: [number, number]) {
  if (map.value) {
    map.value.setCenter(center);
  }
}

// 设置缩放级别
function setZoom(zoom: number) {
  if (map.value) {
    map.value.setZoom(zoom);
  }
}

// 适应视野
function setFitView(overlays?: any[], immediately?: boolean, margins?: number[]) {
  if (map.value) {
    map.value.setFitView(overlays, immediately, margins);
  }
}

// 获取地图实例
function getMapInstance() {
  return map.value;
}

// 监听center变化
watch(() => props.center, (newCenter) => {
  if (map.value && newCenter) {
    map.value.setCenter(newCenter);
  }
}, { deep: true });

// 监听zoom变化
watch(() => props.zoom, (newZoom) => {
  if (map.value && newZoom) {
    map.value.setZoom(newZoom);
  }
});

// 暴露方法给父组件
defineExpose({
  getMapInstance,
  setCenter,
  setZoom,
  setFitView,
  initMap,
  destroyMap
});

onMounted(() => {
  nextTick(() => {
    initMap();
  });
});

onUnmounted(() => {
  destroyMap();
});
</script>

<template>
  <div class="amap-container-wrapper">
    <div
      ref="mapContainer"
      :id="mapId"
      class="amap-container"
      :style="{ height }"
    />
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        正在加载地图...
      </div>
    </div>
  </div>
</template>

<style scoped>
.amap-container-wrapper {
  position: relative;
  width: 100%;
}

.amap-container {
  width: 100%;
  border: 1px solid #e0e0e6;
  border-radius: 6px;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  padding: 20px;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-size: 14px;
  color: #666;
}
</style>