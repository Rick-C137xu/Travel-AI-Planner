<script setup lang="ts">
import { computed, ref } from 'vue';
import PasteGuidePanel from '@/components/PasteGuidePanel.vue';
import PlaceCard from '@/components/PlaceCard.vue';
import PreferenceSummary from '@/components/PreferenceSummary.vue';
import { generateItinerary, isFrontendMockMode, recommendPlaces } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';
import type { PlaceStatus } from '@/types';

const { state, updateRuntimeStatus } = usePlannerStore();
const loadingPlaces = ref(false);
const loadingItinerary = ref(false);
const selectedPlaces = computed(() => state.places.filter((place) => place.userStatus === 'want'));
const sourceNote = computed(() => {
  if (isFrontendMockMode) {
    return '当前为 V2.1 / 前端 Mock 演示数据，未请求后端。地点推荐来自前端内置 Mock 数据，用于展示规划流程。';
  }
  if (!state.backendConnected) {
    if (state.dataSourceLabel === '前端 Mock') {
      return '当前为 V4.1 后端模式，但后端请求失败，已降级为前端 Mock 数据。';
    }
    return '当前为 V4.1 后端模式，正在请求后端推荐接口。';
  }
  const label = state.dataSourceLabel;
  if (label === '高德地图 + AI') {
    return '当前为 V4.1 高德地图 + AI 模式：候选地点由高德地图返回真实 POI，并由 AI 补充推荐文案。';
  }
  if (label === '高德地图 + 后端模板') {
    return '当前为 V4.1 高德地图 + 后端模板：AI 请求失败，已降级为后端模板，地点仍来自高德 POI。';
  }
  if (label === '高德地图') {
    return '当前为 V4 高德模式：候选地点来自高德 POI 搜索；后端未配置 AI_API_KEY，文案为后端模板生成。';
  }
  if (label === 'AI 生成') {
    return '当前为 V4.1 AI 生成模式：地点由 AI 生成，未经过高德地图校验，请人工核对营业信息。';
  }
  return '当前为 V3 后端 Mock 模式：后端已连接成功，但未配置 AI_API_KEY 与 AMAP_KEY，返回后端 Mock 数据。';
});
const aiFallbackNotice = computed(() =>
  state.backendConnected && state.dataSourceLabel === '高德地图 + 后端模板'
    ? 'AI 请求失败，已降级为后端模板；地点仍来自高德 POI，不影响地点准确性。'
    : ''
);

async function loadPlaces() {
  loadingPlaces.value = true;
  state.warning = '';
  try {
    const response = await recommendPlaces(state.preference, state.guideText);
    updateRuntimeStatus(response);
    state.places = response.data;
    state.warning = response.warning || '';
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '候选地点生成失败';
  } finally {
    loadingPlaces.value = false;
  }
}

function updateStatus(id: string, status: PlaceStatus) {
  state.places = state.places.map((place) => (place.id === id ? { ...place, userStatus: status } : place));
}

async function buildItinerary() {
  loadingItinerary.value = true;
  state.warning = '';
  try {
    const response = await generateItinerary(state.preference, selectedPlaces.value);
    updateRuntimeStatus(response);
    state.itinerary = response.data;
    state.warning = response.warning || '';
    state.step = 'itinerary';
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '行程生成失败';
  } finally {
    loadingItinerary.value = false;
  }
}

if (!state.places.length) {
  void loadPlaces();
}
</script>

<template>
  <section class="two-column wide">
    <div class="places-main">
      <div class="section-head">
        <div>
          <p class="eyebrow">候选地点推荐</p>
          <h2>先挑地点，再排行程</h2>
        </div>
        <div class="head-actions">
          <button class="ghost-btn" :disabled="loadingPlaces" @click="loadPlaces">
            {{ loadingPlaces ? '生成中...' : '重新推荐地点' }}
          </button>
          <button class="primary-btn" :disabled="loadingItinerary || selectedPlaces.length === 0" @click="buildItinerary">
            {{ loadingItinerary ? '生成中...' : `生成行程（${selectedPlaces.length}）` }}
          </button>
        </div>
      </div>

      <div class="source-note">
        {{ sourceNote }} 你也可以粘贴攻略文本，系统会尝试提取其中的地点信息；不会自动抓取任何平台内容。
      </div>

      <p v-if="aiFallbackNotice" class="warning-banner">{{ aiFallbackNotice }}</p>
      <p v-if="state.warning && state.warning !== aiFallbackNotice" class="warning-banner">{{ state.warning }}</p>
      <PasteGuidePanel />
      <div v-if="loadingPlaces" class="empty-state">正在生成候选地点...</div>
      <div v-else class="place-grid compact-place-grid">
        <PlaceCard v-for="place in state.places" :key="place.id" :place="place" @status="updateStatus" />
      </div>
    </div>
    <PreferenceSummary :preference="state.preference" />
  </section>
</template>
