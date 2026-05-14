<script setup lang="ts">
import { ref } from 'vue';
import { extractPlaces } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state } = usePlannerStore();
const loading = ref(false);

async function extract() {
  if (!state.guideText.trim()) return;
  loading.value = true;
  state.warning = '';
  try {
    const response = await extractPlaces(state.preference, state.guideText);
    const existingIds = new Set(state.places.map((place) => place.id));
    state.places = [...state.places, ...response.data.filter((place) => !existingIds.has(place.id))];
    state.warning = response.warning || '';
  } catch (error) {
    state.warning = error instanceof Error ? error.message : '攻略文本提取失败';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <section class="paste-panel">
    <div>
      <h3>粘贴攻略文本</h3>
      <p>可以手动粘贴小红书、公众号、朋友攻略等内容，系统会尝试提取地点。不会自动爬取任何平台。</p>
    </div>
    <textarea v-model="state.guideText" placeholder="把攻略文本粘贴到这里"></textarea>
    <button class="ghost-btn" :disabled="loading || !state.guideText.trim()" @click="extract">
      {{ loading ? '提取中...' : '从文本提取地点' }}
    </button>
  </section>
</template>
