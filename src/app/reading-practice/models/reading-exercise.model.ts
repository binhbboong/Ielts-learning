export type ReadingExerciseStatus = 'ready' | 'failed';

export interface ReadingQuestion {
  id: string;
  questionText: string;
  questionType: string;
  options: string[] | null;
  groupInstructions: string | null;
  order: number;
}

export interface ReadingPassage {
  id: string;
  title: string | null;
  passageText: string;
  order: number;
  questions: ReadingQuestion[];
}

export interface ReadingExercise {
  day: string;
  status: ReadingExerciseStatus;
  focusReference: string | null;
  passages: ReadingPassage[];
  phase: string | null;
  targetMinutes: number | null;
}

export interface ReadingAnswerResult {
  questionText: string;
  questionType: string;
  options: string[] | null;
  learnerAnswer: number | string;
  correctAnswer: number | string | null;
  correct: boolean;
}

export interface ReadingSubmissionResult {
  day: string;
  score: number;
  total: number;
  answers: ReadingAnswerResult[];
}
