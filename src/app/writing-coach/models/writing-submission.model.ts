export type WritingTaskType = 'task1' | 'task2';
export type WritingSubmissionStatus = 'complete' | 'failed';

export interface WritingCriterion {
  bandScore: number;
  feedback: string;
  strengths: string[];
  weaknesses: string[];
}

export interface WritingCorrection {
  original: string;
  corrected: string;
  explanation: string;
}

export interface WritingSubmissionCreate {
  taskType: WritingTaskType;
  questionText: string;
  responseText: string;
  day?: string;
}

export interface WritingSubmissionSummary {
  id: string;
  createdAt: string;
  taskType: WritingTaskType;
  status: WritingSubmissionStatus;
  overallBand: number | null;
  taskResponseScore: number | null;
  questionExcerpt: string;
}

export interface WritingSubmissionDetail extends WritingSubmissionCreate {
  id: string;
  createdAt: string;
  status: WritingSubmissionStatus;
  taskResponse: WritingCriterion | null;
  coherenceAndCohesion: WritingCriterion | null;
  lexicalResource: WritingCriterion | null;
  grammaticalRangeAndAccuracy: WritingCriterion | null;
  overallBand: number | null;
  corrections: WritingCorrection[] | null;
  errorMessage: string | null;
}
