<script setup lang="ts">
import { onMounted, ref } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';

const map = ref<AMap.Map | null>(null);
const polygon = ref<AMap.Polygon | null>(null);
const polyEditor = ref<AMap.PolygonEditor | null>(null);
const PolygonoArr = ref<Array<[number, number]>>([]);
const isCreateBtn = ref(true);

function initMap() {
  AMapLoader.load({
    key: '7de0c6b90cb13571ce931ca75a66c6e7', // Replace with your own AMap API key
    version: '2.0',
    plugins: ['AMap.Polygon', 'AMap.PolygonEditor']
  }).then(AMap => {
    map.value = new AMap.Map('map-container', {
      zoom: 12,
      center: [116.397428, 39.90923] // Default center point (Tiananmen, Beijing)
    });

    polyEditor.value = new AMap.PolygonEditor(map.value);
  });
}

function createPolygon() {
  if (polygon.value) {
    map.value?.remove(polygon.value);
  }

  polygon.value = new AMap.Polygon({
    path: [
      [116.397428, 39.90923],
      [116.407428, 39.90923],
      [116.407428, 39.91923]
    ],
    strokeColor: '#1b38d3',
    strokeOpacity: 1,
    strokeWeight: 3,
    fillColor: '#1b38d3',
    fillOpacity: 0.5,
    zIndex: 50
  });

  map.value?.add(polygon.value);
  polyEditor.value?.setTarget(polygon.value);

  isCreateBtn.value = false;
}

function polyEditorStart() {
  if (polygon.value) {
    polyEditor.value?.setTarget(polygon.value);
    polyEditor.value?.open();
  } else {
    alert('请先创建围栏！');
  }
}

function polyEditorEnd() {
  polyEditor.value?.close();
  alert('编辑结束');
}

function handleKeep() {
  if (polygon.value) {
    const path = polygon.value.getPath();
    PolygonoArr.value = path.map((point: any) => [point.lng, point.lat]);
    console.log(PolygonoArr.value);
    alert('围栏已保存！');
  } else {
    alert('当前没有围栏可保存');
  }
}

function handleRemove() {
  if (polygon.value) {
    map.value?.remove(polygon.value);
    polygon.value = null;
    PolygonoArr.value = [];
    isCreateBtn.value = true;
    alert('围栏已删除');
  } else {
    alert('当前没有围栏可删除');
  }
}

onMounted(() => {
  initMap();
});
</script>

<template>
  <div>
    <!-- 操作按钮 -->
    <button v-if="isCreateBtn" class="btn custom-btn" @click="createPolygon">新建围栏</button>
    <button class="btn custom-btn" @click="polyEditorStart">开始编辑</button>
    <button class="btn custom-btn" @click="polyEditorEnd">结束编辑</button>
    <button class="btn custom-btn" @click="handleKeep">保存</button>
    <button class="btn custom-btn" @click="handleRemove">删除围栏</button>
    <button class="btn custom-btn" @click="loadPolygon">加载围栏</button>
    <!-- 地图容器 -->
    <div id="map-container" class="map-container"></div>
  </div>
</template>

<style scoped>
.map-container {
  height: 500px;
  width: 100%;
  border: 1px solid #ccc;
}
.btn {
  margin-right: 10px;
  margin-bottom: 5px;
}
.custom-btn {
  background-color: #729fe2; /* Green background */
  border: none; /* Remove borders */
  color: white; /* White text */
  padding: 10px 20px; /* Some padding */
  text-align: center; /* Centered text */
  text-decoration: none; /* Remove underline */
  display: inline-block; /* Get the element to behave like a button */
  font-size: 12px; /* Increase font size */
  margin: 4px 2px; /* Some margin */
  cursor: pointer; /* Pointer/hand icon */
  border-radius: 8px; /* Rounded corners */
  transition: background-color 0.3s; /* Smooth transition */
}

.custom-btn:hover {
  background-color: #bed89d; /* Darker green on hover */
}
</style>
