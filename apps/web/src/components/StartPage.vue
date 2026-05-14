<script setup lang="ts">
import { usePlannerStore } from '@/store/usePlannerStore';

const { state } = usePlannerStore();

function start() {
  state.step = 'chat';
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
      <button class="primary-btn large" @click="start">开始规划</button>
    </div>
    <div class="feature-panel">
      <div class="feature-item">
        <strong>问答收集需求</strong>
        <span>不用一次填大表单，按步骤确认旅行偏好。</span>
      </div>
      <div class="feature-item">
        <strong>推荐候选地点</strong>
        <span>可结合 AI 或 mock 数据，也支持粘贴攻略文本提取。</span>
      </div>
      <div class="feature-item">
        <strong>生成每日行程</strong>
        <span>按旅行强度控制密度，输出结构化日程。</span>
      </div>
      <div class="feature-item">
        <strong>地图展示</strong>
        <span>配置高德 Key 后显示真实地图；未配置时自动降级。</span>
      </div>
    </div>
  </section>
</template>
