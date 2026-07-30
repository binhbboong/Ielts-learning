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
}

export interface ReviewCompleteSummary {
  sessionId: string;
  totalReviewed: number;
  forgot: number;
  remembered: number;
  reviewDatesUpdated: boolean;
}

export type ReviewSessionState =
  | { status: 'item'; item: ReviewItem }
  | { status: 'nothing_due' }
  | { status: 'not_started' }
  | { status: 'complete'; summary?: ReviewCompleteSummary };
