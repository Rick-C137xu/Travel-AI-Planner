<script setup lang="ts">
import { computed, ref } from 'vue';
import { isFrontendMockMode } from '@/services/api';
import {
  clearUserPreferences,
  getUserPreferences,
  mergePreferencesIntoTravelForm,
  summarizeUserPreferences
} from '@/services/userPreferences';
import { usePlannerStore } from '@/store/usePlannerStore';

const { state } = usePlannerStore();
const savedProfile = ref(getUserPreferences());
const showPreferenceManager = ref(false);
const recommendationText = computed(() =>
  isFrontendMockMode
    ? '当前为 V4.4 / 前端 Mock 模式，使用更贴近城市的内置 Mock 数据，也支持粘贴攻略文本做演示提取。'
    : '当前为 V4.4 后端模式，会请求后端推荐与行程接口；未配置 AI_API_KEY 时返回后端 Mock 数据。'
);
const savedPreferenceSummary = computed(() =>
  savedProfile.value ? summarizeUserPreferences(savedProfile.value) : []
);

function start() {
  state.step = 'chat';
}

function useSavedPreferences() {
  if (savedProfile.value) {
    state.preference = mergePreferencesIntoTravelForm(state.preference, savedProfile.value);
  }
  state.questionIndex = 0;
  state.step = 'chat';
}

function startFresh() {
  state.questionIndex = 0;
  state.step = 'chat';
}

function clearSavedPreferences() {
  clearUserPreferences();
  savedProfile.value = null;
  showPreferenceManager.value = false;
}
</script>

<template>
  <section class="start-page">
    <div class="hero-copy">
      <p class="eyebrow">从需求到路线，一步步来</p>
      <h2>把旅行想法整理成可执行的每日行程</h2>
      <p>
        通过问答收集目的地、天数、偏好和雷区，先推荐候选地点，让你选择想去或避开，再生成每日行程并在地图区域展示地点。
      </p>
      <div v-if="savedProfile" class="preference-prompt">
        <strong>检测到你已保存默认旅行偏好，是否使用？</strong>
        <span>数据仅保存在当前浏览器，不会上传到服务器；换设备或清理缓存后不会同步。</span>
        <div class="preference-actions">
          <button class="primary-btn" @click="useSavedPreferences">使用默认偏好</button>
          <button class="ghost-btn" @click="startFresh">重新填写</button>
          <button class="ghost-btn" @click="showPreferenceManager = !showPreferenceManager">管理偏好</button>
        </div>
      </div>
      <button v-else class="primary-btn large" @click="start">开始规划</button>

      <div v-if="showPreferenceManager && savedProfile" class="preference-manager">
        <strong>当前默认偏好</strong>
        <div class="tag-row">
          <span v-for="item in savedPreferenceSummary" :key="item" class="mini-tag">{{ item }}</span>
        </div>
        <small>清除后会恢复为无默认偏好状态，不影响已经生成的当前计划。</small>
        <button class="ghost-btn" @click="clearSavedPreferences">清除默认偏好</button>
      </div>
    </div>
    <div class="feature-panel">
      <div class="feature-item">
        <strong>本地偏好保存</strong>
        <span>V4.4 支持保存常用节奏、兴趣、预算、住宿和交通偏好；仅保存在当前浏览器。</span>
      </div>
      <div class="feature-item">
        <strong>问答收集需求</strong>
        <span>不用一次填大表单，按步骤确认旅行偏好。</span>
      </div>
      <div class="feature-item">
        <strong>推荐候选地点</strong>
        <span>{{ recommendationText }}</span>
      </div>
      <div class="feature-item">
        <strong>生成每日行程</strong>
        <span>按旅行强度控制密度，输出结构化日程。</span>
      </div>
      <div class="feature-item">
        <strong>地图展示</strong>
        <span>未配置高德 Key 时自动降级为地点清单，不影响主流程。</span>
      </div>
    </div>
  </section>
</template>
