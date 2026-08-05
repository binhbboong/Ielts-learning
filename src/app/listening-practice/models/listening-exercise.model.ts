export interface ListeningQuestion {
  id: string;
  questionText: string;
  questionType: string;
  options: string[] | null;
  groupInstructions: string | null;
  order: number;
}

export interface ListeningSection {
  id: string;
  contextType: string;
  scriptText: string | null;
  order: number;
  questions: ListeningQuestion[];
}

export interface ListeningExercise {
  day: string;
  status: string;
  focusReference: string | null;
  sections: ListeningSection[];
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
  sections: ListeningSection[];
  answers: ListeningAnswerResult[];
}
