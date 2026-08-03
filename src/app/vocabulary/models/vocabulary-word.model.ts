export const INTERVAL_DAYS = [1, 3, 7, 14, 30] as const;

export interface VocabularyWordCreate {
  word: string;
  meaning: string;
  example?: string;
  topic?: string;
}

export interface VocabularyWord {
  id: string;
  word: string;
  meaning: string;
  example: string | null;
  topic: string | null;
  targetBand: number | null;
  cefrLevel: string | null;
  source: string;
  intervalIndex: number;
  nextDueDate: string;
  createdAt: string;
  lastReviewedAt: string | null;
}

export interface AddWordResult {
  saved: true;
  word: VocabularyWord;
}

export interface DueQueueSummary {
  totalDue: number;
  byInterval: Record<string, number>;
  byTopic: Record<string, number>;
  dailyTarget: number;
  backfillCount: number;
  shortfall: boolean;
}

export interface VocabularyRecommendation {
  key: string;
  word: string;
  meaning: string;
  example: string;
  topic: string;
  targetBand: number;
  cefrLevel: string;
}

export interface VocabularyRecommendationFeed {
  currentBand: number;
  cefrLevel: string;
  phase: string;
  week: number;
  recommendations: VocabularyRecommendation[];
}

export interface VocabularyHistoryWord {
  word: string;
  meaning: string;
}

export interface VocabularyHistoryReview {
  word: string;
  outcome: string;
  assessedAt: string;
}

export interface VocabularyHistoryDay {
  day: string;
  wordsAdded: VocabularyHistoryWord[];
  wordsReviewed: VocabularyHistoryReview[];
}

export interface VocabularyHistory {
  days: VocabularyHistoryDay[];
}
