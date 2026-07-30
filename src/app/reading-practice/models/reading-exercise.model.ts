export type ReadingExerciseStatus = 'ready' | 'failed';

export interface ReadingQuestion {
  id: string;
  questionText: string;
  options: string[];
  order: number;
}

export interface ReadingExercise {
  day: string;
  status: ReadingExerciseStatus;
  focusReference: string | null;
  passageText: string | null;
  questions: ReadingQuestion[];
}

export interface ReadingAnswerResult {
  questionText: string;
  options: string[];
  learnerAnswerIndex: number;
  correctOptionIndex: number;
  correct: boolean;
}

export interface ReadingSubmissionResult {
  day: string;
  score: number;
  total: number;
  answers: ReadingAnswerResult[];
}
