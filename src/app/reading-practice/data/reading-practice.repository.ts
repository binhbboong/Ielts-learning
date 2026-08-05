import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  ReadingAnswerResult,
  ReadingExercise,
  ReadingPassage,
  ReadingQuestion,
  ReadingSubmissionResult,
} from '../models/reading-exercise.model';

function question(value: any): ReadingQuestion {
  return {
    id: value.id,
    questionText: value.question_text,
    questionType: value.question_type,
    options: value.options,
    groupInstructions: value.group_instructions,
    order: value.order,
  };
}

function passage(value: any): ReadingPassage {
  return {
    id: value.id,
    title: value.title,
    passageText: value.passage_text,
    order: value.order,
    questions: (value.questions ?? []).map(question),
  };
}

function exercise(value: any): ReadingExercise {
  return {
    day: value.day,
    status: value.status,
    focusReference: value.focus_reference,
    passages: (value.passages ?? []).map(passage),
  };
}

function answerResult(value: any): ReadingAnswerResult {
  return {
    questionText: value.question_text,
    questionType: value.question_type,
    options: value.options,
    learnerAnswer: value.learner_answer,
    correctAnswer: value.correct_answer,
    correct: value.correct,
  };
}

function submissionResult(value: any): ReadingSubmissionResult {
  return {
    day: value.day,
    score: value.score,
    total: value.total,
    answers: (value.answers ?? []).map(answerResult),
  };
}

@Injectable({ providedIn: 'root' })
export class ReadingPracticeRepository {
  constructor(private readonly api: ApiClient) {}

  async get(day: string): Promise<ReadingExercise> {
    return exercise(
      await firstValueFrom(this.api.get<any>(`/api/reading-practice/${day}`)),
    );
  }

  async submit(day: string, answers: (number | string)[]): Promise<ReadingSubmissionResult> {
    return submissionResult(
      await firstValueFrom(
        this.api.post<any>(`/api/reading-practice/${day}/submit`, { answers }),
      ),
    );
  }

  async retry(day: string): Promise<ReadingExercise> {
    return exercise(
      await firstValueFrom(
        this.api.post<any>(`/api/reading-practice/${day}/retry`, {}),
      ),
    );
  }
}
