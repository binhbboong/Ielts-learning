export type ReviewOutcome = 'forgot' | 'remembered';

export interface ReviewItem {
  sessionId: string;
  itemId: string;
  wordId: string;
  word: string;
  meaning: string;
  example: string | null;
  position: number;
  total: number;
  isNew: boolean;
}

export interface ReviewCompleteSummary {
  sessionId: string;
  totalReviewed: number;
  forgot: number;
  remembered: number;
  newWordsIncluded: number;
  reviewDatesUpdated: boolean;
}

export type ReviewSessionState =
  | { status: 'item'; item: ReviewItem }
  | { status: 'nothing_due' }
  | { status: 'not_started' }
  | { status: 'complete'; summary?: ReviewCompleteSummary };

export interface QuizItem {
  quizId: string;
  itemId: string;
  word: string;
  options: string[];
  position: number;
  total: number;
}

export interface QuizCompleteSummary {
  quizId: string;
  correct: number;
  total: number;
  passed: boolean;
}

export type QuizState =
  | { status: 'item'; item: QuizItem }
  | { status: 'not_ready' }
  | { status: 'complete'; summary?: QuizCompleteSummary };
