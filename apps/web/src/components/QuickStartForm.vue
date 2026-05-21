<script setup lang="ts">
import { computed, ref } from 'vue';
import PreferenceSummary from '@/components/PreferenceSummary.vue';
import { summarizeUserPreferences } from '@/services/userPreferences';
import { usePlannerStore } from '@/store/usePlannerStore';
import type { UserPreferenceProfile } from '@/types';

const props = defineProps<{
  savedProfile: UserPreferenceProfile;
}>();

const { state } = usePlannerStore();

const destination = ref('');
const startDate = ref('');
const days = ref(3);
const peopleCount = ref(2);
const hotelArea = ref('');
const additionalNotes = ref('');

const preferenceSummary = computed(() => summarizeUserPreferences(props.savedProfile));

const minDate = computed(() => {
  const today = new Date();
  return today.toISOString().slice(0, 10);
});

const endDate = computed(() => {
  if (!startDate.value || !days.value) return '';
  const date = new Date(startDate.value);
  date.setDate(date.getDate() + days.value - 1);
  return date.toISOString().slice(0, 10);
});

function isFormValid() {
  return destination.value.trim().length > 0 && startDate.value && days.value > 0 && peopleCount.value > 0;
}

function goBack() {
  state.step = 'start';
}

function submitQuickStart() {
  if (!isFormValid()) return;

  state.preference.destination = destination.value.trim();
  state.preference.startDate = startDate.value;
  state.preference.days = days.value;
  state.preference.peopleCount = peopleCount.value;
  state.preference.hotelArea = hotelArea.value.trim();

  const date = new Date(startDate.value);
  date.setDate(date.getDate() + days.value - 1);
  state.preference.endDate = date.toISOString().slice(0, 10);

  if (additionalNotes.value.trim()) {
    state.guideText = additionalNotes.value.trim();
  }

  state.step = 'places';
}
</script>

<template>
  <section class="quick-start-form">
    <div class="form-header">
      <h2>补充本次旅行信息</h2>
      <p class="form-hint">
        你的行程节奏、预算、交通、兴趣和避雷偏好已自动套用。本次只需要填写目的地、日期、人数和住宿位置。
      </p>
    </div>

    <div class="preference-summary-section">
      <strong>已应用的默认偏好</strong>
      <div class="tag-row">
        <span v-for="item in preferenceSummary" :key="item" class="mini-tag">{{ item }}</span>
      </div>
    </div>

    <div class="form-body">
      <div class="form-field">
        <label for="destination">目的地 <span class="required">*</span></label>
        <input
          id="destination"
          v-model="destination"
          type="text"
          placeholder="例如：昆明"
          class="text-input"
        />
      </div>

      <div class="form-row">
        <div class="form-field">
          <label for="startDate">出发日期 <span class="required">*</span></label>
          <input
            id="startDate"
            v-model="startDate"
            type="date"
            :min="minDate"
            class="text-input"
          />
        </div>

        <div class="form-field">
          <label for="days">旅行天数 <span class="required">*</span></label>
          <input
            id="days"
            v-model.number="days"
            type="number"
            min="1"
            max="30"
            class="text-input"
          />
        </div>
      </div>

      <div v-if="endDate" class="form-hint-inline">
        返程日期：{{ endDate }}
      </div>

      <div class="form-field">
        <label for="peopleCount">出行人数 <span class="required">*</span></label>
        <input
          id="peopleCount"
          v-model.number="peopleCount"
          type="number"
          min="1"
          max="20"
          class="text-input"
        />
      </div>

      <div class="form-field">
        <label for="hotelArea">住宿位置</label>
        <input
          id="hotelArea"
          v-model="hotelArea"
          type="text"
          placeholder="例如：市中心、景区附近、地铁站附近（可选）"
          class="text-input"
        />
        <small class="field-hint">如果不确定，可以留空或填写"还没确定"</small>
      </div>

      <div class="form-field">
        <label for="additionalNotes">本次补充需求</label>
        <textarea
          id="additionalNotes"
          v-model="additionalNotes"
          placeholder="例如：这次想去翠湖公园和滇池，不想去太远的景点（可选）"
          class="text-input"
          rows="3"
        />
        <small class="field-hint">如果本次旅行有特别想去或不想去的地方，可以在这里说明</small>
      </div>
    </div>

    <div class="form-actions">
      <button class="ghost-btn" @click="goBack">返回</button>
      <button class="primary-btn" :disabled="!isFormValid()" @click="submitQuickStart">
        生成推荐地点
      </button>
    </div>

    <div class="form-footer">
      <small>如果想重新填写完整问答，可以返回首页选择"重新填写"。</small>
    </div>
  </section>
</template>

<style scoped>
.quick-start-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

.form-header {
  margin-bottom: 2rem;
}

.form-header h2 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
}

.form-hint {
  color: #666;
  font-size: 0.9rem;
  line-height: 1.5;
}

.preference-summary-section {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 2rem;
}

.preference-summary-section strong {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.mini-tag {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: white;
  border: 1px solid #ddd;
  border-radius: 12px;
  font-size: 0.85rem;
}

.form-body {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-field label {
  font-weight: 500;
  font-size: 0.95rem;
}

.required {
  color: #e74c3c;
}

.text-input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
}

.text-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-hint-inline {
  color: #666;
  font-size: 0.9rem;
  margin-top: -1rem;
  padding-left: 0.25rem;
}

.field-hint {
  color: #888;
  font-size: 0.85rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #eee;
}

.form-actions button {
  flex: 1;
}

.form-footer {
  margin-top: 1.5rem;
  text-align: center;
}

.form-footer small {
  color: #888;
  font-size: 0.85rem;
}

@media (max-width: 600px) {
  .quick-start-form {
    padding: 1rem 0.75rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }
}
</style>
