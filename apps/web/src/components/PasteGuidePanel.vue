<script setup lang="ts">
import { computed, ref } from 'vue';
import { extractPlaces } from '@/services/api';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state } = usePlannerStore();
const loading = ref(false);
const guideTooShort = computed(() => state.guideText.trim().length > 0 && state.guideText.trim().length < 20);

async function extract() {
  if (!state.guideText.trim()) return;
  loading.value = true;
  state.warning = guideTooShort.value
    ? '粘贴文本较短，V2.1 会先做演示提取；建议粘贴包含地点名、推荐理由或避坑提醒的段落。'
    : '';
  try {
    const response = await extractPlaces(state.preference, state.guideText);
    const existingIds = new Set(state.places.map((place) => place.id));
    state.places = [...state.places, ...response.data.filter((place) => !existingIds.has(place.id))];
    state.warning = response.warning || state.warning;
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
      <p>
        当前是 V2.1 演示提取，适合粘贴含有地点名、推荐理由、避坑提醒的文字。暂不做 OCR，也不会自动抓取任何平台；真实 AI 解析计划放到 V4。
      </p>
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
