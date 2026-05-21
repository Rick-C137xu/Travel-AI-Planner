<script setup lang="ts">
import { computed, ref } from 'vue';
import PreferenceSummary from '@/components/PreferenceSummary.vue';
import { questions } from '@/data/questions';
import { buildUserPreferencesFromTravelForm, saveUserPreferences } from '@/services/userPreferences';
import { usePlannerStore } from '@/store/usePlannerStore';
import type { BudgetLevel, Pace } from '@/types';

const { state } = usePlannerStore();
const currentQuestion = computed(() => questions[state.questionIndex] ?? questions[0]);
const localValue = ref('');
const localMulti = ref<string[]>([]);
const preferenceSaveMessage = ref('');

function syncLocal() {
  const question = currentQuestion.value;
  const value = state.preference[question.key];
  if (Array.isArray(value)) {
    localMulti.value = [...value];
    localValue.value = '';
  } else {
    localValue.value = String(value || '');
    localMulti.value = [];
  }
}

syncLocal();

function toggleOption(value: string) {
  localMulti.value = localMulti.value.includes(value)
    ? localMulti.value.filter((item) => item !== value)
    : [...localMulti.value, value];
}

function commitCurrentAnswer() {
  const question = currentQuestion.value;
  const key = question.key;
  if (question.kind === 'multi') {
    if (key === 'interests') state.preference.interests = [...localMulti.value];
    if (key === 'dislikes') state.preference.dislikes = [...localMulti.value];
    if (key === 'transportPreference') state.preference.transportPreference = [...localMulti.value];
  } else if (question.kind === 'number') {
    const numericValue = Math.max(1, Number(localValue.value || 1));
    if (key === 'days') state.preference.days = numericValue;
    if (key === 'peopleCount') state.preference.peopleCount = numericValue;
  } else if (key === 'pace') {
    state.preference.pace = localValue.value as Pace;
  } else if (key === 'budgetLevel') {
    state.preference.budgetLevel = localValue.value as BudgetLevel;
  } else if (key === 'destination') {
    state.preference.destination = localValue.value.trim();
  } else if (key === 'startDate') {
    state.preference.startDate = localValue.value;
  } else if (key === 'endDate') {
    state.preference.endDate = localValue.value;
  } else if (key === 'hotelArea') {
    state.preference.hotelArea = localValue.value.trim();
  }

  if (key === 'startDate' && state.preference.startDate && state.preference.days) {
    const date = new Date(state.preference.startDate);
    date.setDate(date.getDate() + state.preference.days - 1);
    state.preference.endDate = date.toISOString().slice(0, 10);
  }
}

function saveAnswer() {
  commitCurrentAnswer();
  preferenceSaveMessage.value = '';
  if (state.questionIndex < questions.length - 1) {
    state.questionIndex += 1;
    syncLocal();
  } else {
    state.step = 'places';
  }
}

function goBack() {
  if (state.questionIndex > 0) {
    state.questionIndex -= 1;
    syncLocal();
  } else {
    state.step = 'start';
  }
}

function isReady() {
  const question = currentQuestion.value;
  if (question.kind === 'multi') return true;
  return Boolean(localValue.value);
}

function setSingle(value: string | number) {
  localValue.value = String(value);
}

function canSaveAsDefault() {
  return state.questionIndex >= 4;
}

function saveAsDefaultPreference() {
  commitCurrentAnswer();
  const saved = saveUserPreferences(buildUserPreferencesFromTravelForm(state.preference));
  preferenceSaveMessage.value = saved
    ? '已保存为默认旅行偏好。下次新建计划时可一键使用。'
    : '当前浏览器暂时无法写入 localStorage，本次偏好未保存。';
}
</script>

<template>
  <section class="two-column">
    <div class="chat-panel">
      <p class="eyebrow">第 {{ state.questionIndex + 1 }} / {{ questions.length }} 步</p>
      <div class="chat-bubble system">
        <h2>{{ currentQuestion.title }}</h2>
        <p v-if="currentQuestion.helper">{{ currentQuestion.helper }}</p>
      </div>

      <div class="answer-box">
        <input
          v-if="currentQuestion.kind === 'text'"
          v-model="localValue"
          class="text-input"
          type="text"
          placeholder="输入你的答案"
          @keyup.enter="isReady() && saveAnswer()"
        />
        <input v-else-if="currentQuestion.kind === 'date'" v-model="localValue" class="text-input" type="date" />
        <input
          v-else-if="currentQuestion.kind === 'number'"
          v-model="localValue"
          class="text-input"
          type="number"
          min="1"
        />
        <div v-else-if="currentQuestion.kind === 'single'" class="option-grid">
          <button
            v-for="option in currentQuestion.options"
            :key="option.value"
            :class="['option-btn', { active: localValue === String(option.value) }]"
            @click="setSingle(option.value)"
          >
            <strong>{{ option.label }}</strong>
            <span v-if="option.description">{{ option.description }}</span>
          </button>
        </div>
        <div v-else class="option-grid">
          <button
            v-for="option in currentQuestion.options"
            :key="option.value"
            :class="['option-btn', { active: localMulti.includes(String(option.value)) }]"
            @click="toggleOption(String(option.value))"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div class="flow-actions">
        <button class="ghost-btn" @click="goBack">返回上一步</button>
        <button v-if="canSaveAsDefault()" class="ghost-btn" @click="saveAsDefaultPreference">
          保存为我的默认偏好
        </button>
        <button class="primary-btn" :disabled="!isReady()" @click="saveAnswer">
          {{ state.questionIndex === questions.length - 1 ? '查看候选地点' : '下一步' }}
        </button>
      </div>
      <p v-if="preferenceSaveMessage" class="small-note preference-save-note">{{ preferenceSaveMessage }}</p>
    </div>
    <PreferenceSummary :preference="state.preference" />
  </section>
</template>
