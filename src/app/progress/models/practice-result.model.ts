export type PracticeSkill = 'Reading' | 'Listening';
export type TrendSkill = PracticeSkill | 'Both';
export type TrendPeriod = '4_weeks' | '8_weeks' | '12_weeks';
export type HistorySort = 'newest' | 'oldest';
export type TrendDirection = 'up' | 'steady' | 'down';

export interface QuestionTypeOption {
  key: string;
  label: string;
}

export interface TaxonomyResponse {
  Reading: QuestionTypeOption[];
  Listening: QuestionTypeOption[];
}

export interface PracticeResultCreate {
  skill: PracticeSkill;
  source: string;
  score: number;
  total: number;
  timeTakenSeconds: number;
  missedQuestionTypes?: string[];
  note?: string;
}

export interface PracticeResult extends PracticeResultCreate {
  id: string;
  loggedAt: string;
}

export interface TrendThreshold {
  sufficient: boolean;
  count: number;
  remaining: number;
}

export interface BreakdownEntry {
  key: string;
  count: number;
}

export interface TrendResult {
  sessionCount: number;
  averageScorePercentage: number | null;
  direction: TrendDirection | null;
  threshold: TrendThreshold;
  breakdown: BreakdownEntry[];
}
