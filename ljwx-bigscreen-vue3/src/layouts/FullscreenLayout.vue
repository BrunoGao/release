<template>
  <div class="fullscreen-layout">
    <router-view />
  </div>
</template>

<script setup lang="ts">

</script>

<style lang="scss" scoped>
.fullscreen-layout {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
  background: var(--bg-primary);
}
</style>