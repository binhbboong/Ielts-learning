import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  WritingCriterion,
  WritingSubmissionCreate,
  WritingSubmissionDetail,
  WritingSubmissionSummary,
} from '../models/writing-submission.model';

function criterion(value: any): WritingCriterion | null {
  if (!value) return null;
  return {
    bandScore: value.band_score,
    feedback: value.feedback,
    strengths: value.strengths ?? [],
    weaknesses: value.weaknesses ?? [],
  };
}

function detail(value: any): WritingSubmissionDetail {
  return {
    id: value.id,
    createdAt: value.created_at,
    taskType: value.task_type,
    questionText: value.question_text,
    responseText: value.response_text,
    status: value.status,
    taskResponse: criterion(value.task_response),
    coherenceAndCohesion: criterion(value.coherence_and_cohesion),
    lexicalResource: criterion(value.lexical_resource),
    grammaticalRangeAndAccuracy: criterion(value.grammatical_range_and_accuracy),
    overallBand: value.overall_band,
    corrections: value.corrections ?? null,
    errorMessage: value.error_message,
  };
}

@Injectable({ providedIn: 'root' })
export class WritingCoachRepository {
  constructor(private readonly api: ApiClient) {}

  async submit(value: WritingSubmissionCreate): Promise<WritingSubmissionDetail> {
    const body: Record<string, unknown> = {
      task_type: value.taskType,
      question_text: value.questionText,
      response_text: value.responseText,
    };
    if (value.day) body['day'] = value.day;
    return detail(await firstValueFrom(this.api.post<any>(
      '/api/writing-coach/submissions',
      body,
    )));
  }

  async list(): Promise<WritingSubmissionSummary[]> {
    const values = await firstValueFrom(
      this.api.get<any[]>('/api/writing-coach/submissions'),
    );
    return values.map((value) => ({
      id: value.id,
      createdAt: value.created_at,
      taskType: value.task_type,
      status: value.status,
      overallBand: value.overall_band,
      taskResponseScore: value.task_response_score,
      questionExcerpt: value.question_excerpt,
    }));
  }

  async get(id: string): Promise<WritingSubmissionDetail> {
    return detail(await firstValueFrom(
      this.api.get<any>(`/api/writing-coach/submissions/${encodeURIComponent(id)}`),
    ));
  }
}
