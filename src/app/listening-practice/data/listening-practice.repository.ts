import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  ListeningAnswerResult,
  ListeningExercise,
  ListeningQuestion,
  ListeningSection,
  ListeningSubmissionResult,
} from '../models/listening-exercise.model';

function question(value: any): ListeningQuestion {
  return {
    id: value.id,
    questionText: value.question_text,
    questionType: value.question_type,
    options: value.options,
    groupInstructions: value.group_instructions,
    order: value.order,
  };
}

function section(value: any): ListeningSection {
  return {
    id: value.id,
    contextType: value.context_type,
    scriptText: value.script_text,
    order: value.order,
    questions: (value.questions ?? []).map(question),
  };
}

function exercise(value: any): ListeningExercise {
  return {
    day: value.day,
    status: value.status,
    focusReference: value.focus_reference,
    sections: (value.sections ?? []).map(section),
    phase: value.phase ?? null,
    targetMinutes: value.target_minutes ?? null,
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
    sections: (value.sections ?? []).map(section),
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

  audioUrl(day: string, order: number): string {
    return `/api/listening-practice/${day}/audio/${order}`;
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
