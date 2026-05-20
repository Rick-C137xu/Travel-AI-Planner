<script setup lang="ts">
import { computed, ref } from 'vue';
import { extractPlaces, isFrontendMockMode } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state, updateRuntimeStatus } = usePlannerStore();
const loading = ref(false);
const guideTooShort = computed(() => state.guideText.trim().length > 0 && state.guideText.trim().length < 20);
const panelDescription = computed(() => {
  if (isFrontendMockMode) {
    return '当前为 V4.3 / 前端 Mock 演示提取，适合粘贴含有地点名、推荐理由、避坑提醒的文字。暂不做 OCR，也不会自动抓取任何平台。';
  }
  if (!state.backendConnected) {
    if ((state.placeSourceLabel || state.dataSourceLabel) === '前端 Mock') {
      return '当前为 V4.3 后端模式，但后端请求失败，已降级为前端 Mock 提取。';
    }
    return '当前为 V4.3 后端模式，会请求后端文本提取接口。暂不做 OCR，也不会自动抓取任何平台。';
  }
  const label = state.placeSourceLabel || state.dataSourceLabel;
  if (label === '高德地图 + AI') {
    return '当前为 V4.3 高德地图 + AI 提取：AI 从粘贴文本中识别地点，再通过高德 POI 搜索补充地址与经纬度。';
  }
  if (label === '高德地图 + 后端模板') {
    return '当前为 V4.3 高德地图 + 后端模板提取：AI 请求失败，已降级为后端规则提取，再用高德搜索补全地址。';
  }
  if (state.aiEnabled && !state.amapEnabled) {
    return '当前为 V4.3 AI 提取：AI 从粘贴文本中识别地点；未配置 AMAP_KEY，地址需人工核对。';
  }
  if (state.amapEnabled) {
    return '当前为 V4.3 后端规则 + 高德 提取：后端按规则切分文本，再用高德搜索补全地址。';
  }
  return '当前为 V4.3 后端 Mock 提取：后端未配置 AI_API_KEY 与 AMAP_KEY，按演示规则返回提取结果。';
});

async function extract() {
  if (!state.guideText.trim()) return;
  loading.value = true;
  state.warning = guideTooShort.value
    ? '粘贴文本较短，当前会先做演示提取；建议粘贴包含地点名、推荐理由或避坑提醒的段落。'
    : '';
  try {
    const response = await extractPlaces(state.preference, state.guideText);
    updateRuntimeStatus(response, 'places');
    const existingIds = new Set(state.places.map((place) => place.id));
    state.places = [...state.places, ...response.data.filter((place) => !existingIds.has(place.id))];
    state.warning = response.warning || state.warning;
    state.placeWarning = response.warning || state.placeWarning;
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '攻略文本提取失败';
    state.placeWarning = state.warning;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="paste-panel">
    <div>
      <h3>粘贴攻略文本</h3>
      <p>{{ panelDescription }}</p>
    </div>
    <textarea
      v-model="state.guideText"
      placeholder="示例：1. 天门山：索道很震撼，雨雾天视野一般；2. 溪布街：晚上吃饭散步方便。"
    ></textarea>
    <p v-if="guideTooShort" class="small-note">文本有点短，提取结果可能偏演示。多粘贴几行会更好。</p>
    <button class="ghost-btn" :disabled="loading || !state.guideText.trim()" @click="extract">
      {{ loading ? '提取中...' : '从文本提取地点' }}
    </button>
  </section>
</template>
