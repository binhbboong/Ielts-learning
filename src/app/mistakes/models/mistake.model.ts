export const REASON_OPTIONS = [
  { key: 'missing_vocab', label: "Didn't know the vocabulary" },
  { key: 'missed_paraphrase', label: 'Missed a paraphrase' },
  { key: 'misread_question', label: 'Misread the question' },
  { key: 'missing_information', label: 'Missing information' },
  { key: 'outside_knowledge', label: 'Used outside knowledge' },
  { key: 'ran_out_of_time', label: 'Ran out of time' },
  { key: 'carelessness', label: 'Carelessness' },
  { key: 'wrong_grammar', label: 'Wrong grammar' },
  { key: 'not_sure_other', label: 'Not sure yet / other' },
] as const;

export type ReasonCategory = (typeof REASON_OPTIONS)[number]['key'];
export type MistakeSkill = 'reading' | 'listening' | 'writing' | 'speaking';

export interface MistakeCreate {
  skill: MistakeSkill;
  source: string;
  questionType?: string;
  ownAnswer?: string;
  correctAnswer?: string;
  explanation?: string;
  reasonCategory?: ReasonCategory;
}

export interface MistakeEntry {
  id: string;
  skill: MistakeSkill;
  questionType: string | null;
  source: string;
  ownAnswer: string | null;
  correctAnswer: string | null;
  explanation: string | null;
  reasonCategory: ReasonCategory;
  loggedAt: string;
  isIncomplete: boolean;
}

export interface MistakeGroupedCategory {
  reasonCategory: ReasonCategory;
  count: number;
}

export interface MistakeCategoryDetail {
  ownAnswer: string | null;
  correctAnswer: string | null;
  explanation: string | null;
}

export function reasonLabel(reason: ReasonCategory): string {
  return REASON_OPTIONS.find((option) => option.key === reason)?.label ?? reason;
}
