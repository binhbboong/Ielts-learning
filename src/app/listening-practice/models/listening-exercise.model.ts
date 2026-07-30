export interface ListeningQuestion {
  id: string;
  questionText: string;
  options: string[];
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
  options: string[];
  learnerAnswerIndex: number;
  correctOptionIndex: number;
  correct: boolean;
}

export interface ListeningSubmissionResult {
  day: string;
  score: number;
  total: number;
  scriptText: string;
  answers: ListeningAnswerResult[];
}
