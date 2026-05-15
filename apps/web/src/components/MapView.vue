<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import { addMarkers, createMap, hasAmapKey } from '@/services/amapService';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state } = usePlannerStore();
const mapReady = ref(false);
const mapMessage = ref('');
const selectedPlaces = computed(() => state.places.filter((place) => place.userStatus === 'want'));
const locatedPlaces = computed(() => selectedPlaces.value.filter((place) => place.lat && place.lng));
const pendingPlaces = computed(() => selectedPlaces.value.filter((place) => !place.lat || !place.lng));

async function initMap() {
  if (!hasAmapKey()) {
    mapMessage.value = '未配置高德地图 Key，当前显示降级地点清单。';
    return;
  }
  try {
    await nextTick();
    await createMap('amap-container');
    mapReady.value = true;
    addMarkers(selectedPlaces.value);
  } catch (error) {
    mapMessage.value = error instanceof Error ? error.message : '地图加载失败，已切换为清单视图。';
  }
}

onMounted(initMap);
watch(selectedPlaces, (places) => mapReady.value && addMarkers(places), { deep: true });
</script>

<template>
  <aside class="map-panel">
    <div class="section-head compact">
      <div>
        <p class="eyebrow">地图展示</p>
        <h2>已选地点</h2>
      </div>
    </div>
    <div v-if="mapMessage" class="map-fallback">
      <p>{{ mapMessage }}</p>
      <ul>
        <li v-for="place in selectedPlaces" :key="place.id">
          <strong>{{ place.name }}</strong>
          <span>{{ place.type }} · {{ place.reason }}</span>
        </li>
      </ul>
    </div>
    <div v-show="!mapMessage" id="amap-container" class="map-container"></div>
    <div class="pending-panel">
      <h3>待定位地点</h3>
      <p v-if="!pendingPlaces.length">所有已选地点都有经纬度，或暂无待定位项。</p>
      <ul v-else>
        <li v-for="place in pendingPlaces" :key="place.id">{{ place.name }} · {{ place.type }}</li>
      </ul>
      <p class="small-note">已定位：{{ locatedPlaces.length }} / {{ selectedPlaces.length }}</p>
    </div>
  </aside>
</template>
