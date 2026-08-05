export interface ListeningQuestion {
  id: string;
  questionText: string;
  questionType: string;
  options: string[] | null;
  order: number;
}

export interface ListeningExercise {
  day: string;
  status: string;
  focusReference: string | null;
  scriptText: string | null;
  questions: ListeningQuestion[];
}

export interface ListeningAnswerResult {
  questionText: string;
  questionType: string;
  options: string[] | null;
  learnerAnswer: number | string;
  correctAnswer: number | string | null;
  correct: boolean;
}

export interface ListeningSubmissionResult {
  day: string;
  score: number;
  total: number;
  scriptText: string;
  answers: ListeningAnswerResult[];
}
