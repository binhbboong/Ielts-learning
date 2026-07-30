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
}
