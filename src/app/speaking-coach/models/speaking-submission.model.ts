import { SpeakingPart } from './speaking-question.model';

export type SpeakingStatus =
  | 'PROCESSING'
  | 'TRANSCRIPTION_FAILED'
  | 'EVALUATION_FAILED'
  | 'COMPLETED';

export interface SpeakingCriterion {
  bandScore: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
}

export interface SpeakingSubmission {
  id: string;
  questionId: string;
  question: string;
  part: SpeakingPart;
  audioDurationSeconds: number;
  transcript: string | null;
  status: SpeakingStatus;
  fluencyAndCoherence: SpeakingCriterion | null;
  lexicalResource: SpeakingCriterion | null;
  grammaticalRangeAndAccuracy: SpeakingCriterion | null;
  pronunciation: 'Not assessed';
  errorMessage: string | null;
  createdAt: string;
}
