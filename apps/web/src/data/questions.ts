import type { TravelPreference } from '@/types';

export type QuestionKey = keyof TravelPreference;
export type QuestionKind = 'text' | 'number' | 'single' | 'multi' | 'date';

export interface Question {
  key: QuestionKey;
  title: string;
  helper?: string;
  kind: QuestionKind;
  options?: Array<{ label: string; value: string | number; description?: string }>;
}

export const questions: Question[] = [
  { key: 'destination', title: '这次想去哪里？', helper: '例如：张家界、重庆、上海、成都、杭州', kind: 'text' },
  { key: 'startDate', title: '什么时候出发？', kind: 'date' },
  { key: 'days', title: '准备玩几天？', kind: 'number' },
  { key: 'peopleCount', title: '同行一共几个人？', kind: 'number' },
  {
    key: 'pace',
    title: '你喜欢什么旅行强度？',
    kind: 'single',
    options: [
      { label: '轻松', value: 'relaxed' },
      { label: '正常', value: 'normal' },
      { label: '特种兵', value: 'intense' }
    ]
  },
  {
    key: 'interests',
    title: '这趟更想体验什么？',
    helper: '可以多选',
    kind: 'multi',
    options: ['美食', '自然风景', '拍照', '博物馆', '夜市', '购物', 'Citywalk', '亲子', '情侣'].map((item) => ({
      label: item,
      value: item
    }))
  },
  {
    key: 'dislikes',
    title: '有哪些明确不喜欢的内容？',
    helper: '可以多选，也可以跳过',
    kind: 'multi',
    options: ['早起', '排队', '爬山', '太贵', '太赶路', '网红店'].map((item) => ({ label: item, value: item }))
  },
  {
    key: 'budgetLevel',
    title: '预算大概是什么水平？',
    helper: '当前先用档位快速判断，后续会加入人均/每日预算等量化输入。',
    kind: 'single',
    options: [
      { label: '低', value: 'low', description: '公共交通、平价餐饮、免费或低门票景点优先' },
      { label: '中', value: 'medium', description: '兼顾体验和性价比，适当安排付费景点与特色餐饮' },
      { label: '高', value: 'high', description: '优先体验质量，可接受更高交通、餐饮和门票成本' }
    ]
  },
  {
    key: 'hotelArea',
    title: '住宿区域定了吗？',
    helper: '例如：春熙路附近；还没订；不确定',
    kind: 'text'
  },
  {
    key: 'transportPreference',
    title: '当地交通更偏好什么？',
    helper: '可以多选',
    kind: 'multi',
    options: ['地铁公交', '打车', '步行', '自驾'].map((item) => ({ label: item, value: item }))
  }
];
