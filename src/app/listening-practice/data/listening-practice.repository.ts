import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  ListeningAnswerResult,
  ListeningExercise,
  ListeningQuestion,
  ListeningSubmissionResult,
} from '../models/listening-exercise.model';

function question(value: any): ListeningQuestion {
  return {
    id: value.id,
    questionText: value.question_text,
    questionType: value.question_type,
    options: value.options,
    order: value.order,
  };
}

function exercise(value: any): ListeningExercise {
  return {
    day: value.day,
    status: value.status,
    focusReference: value.focus_reference,
    scriptText: value.script_text,
    questions: (value.questions ?? []).map(question),
  };
}

function answerResult(value: any): ListeningAnswerResult {
  return {
    questionText: value.question_text,
    questionType: value.question_type,
    options: value.options,
    learnerAnswer: value.learner_answer,
    correctAnswer: value.correct_answer,
    correct: value.correct,
  };
}

function submissionResult(value: any): ListeningSubmissionResult {
  return {
    day: value.day,
    score: value.score,
    total: value.total,
    scriptText: value.script_text,
    answers: (value.answers ?? []).map(answerResult),
  };
}

@Injectable({ providedIn: 'root' })
export class ListeningPracticeRepository {
  constructor(private readonly api: ApiClient) {}

  async get(day: string): Promise<ListeningExercise> {
    return exercise(
      await firstValueFrom(this.api.get<any>(`/api/listening-practice/${day}`)),
    );
  }

  audioUrl(day: string): string {
    return `/api/listening-practice/${day}/audio`;
  }

  async submit(
    day: string,
    answers: (number | string)[],
  ): Promise<ListeningSubmissionResult> {
    return submissionResult(
      await firstValueFrom(
        this.api.post<any>(`/api/listening-practice/${day}/submit`, { answers }),
      ),
    );
  }

  async retryScript(day: string): Promise<ListeningExercise> {
    return exercise(
      await firstValueFrom(
        this.api.post<any>(`/api/listening-practice/${day}/retry-script`, {}),
      ),
    );
  }

  async retryAudio(day: string): Promise<ListeningExercise> {
    return exercise(
      await firstValueFrom(
        this.api.post<any>(`/api/listening-practice/${day}/retry-audio`, {}),
      ),
    );
  }
}
