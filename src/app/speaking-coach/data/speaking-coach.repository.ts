import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { SpeakingQuestion } from '../models/speaking-question.model';
import {
  SpeakingCriterion,
  SpeakingSubmission,
} from '../models/speaking-submission.model';

function criterion(value: any): SpeakingCriterion | null {
  return value ? {
    bandScore: value.band_score,
    feedback: value.feedback,
    strengths: value.strengths ?? [],
    weaknesses: value.weaknesses ?? [],
  } : null;
}

function submission(value: any): SpeakingSubmission {
  return {
    id: value.id,
    questionId: value.question_id,
    question: value.question,
    part: value.part,
    audioDurationSeconds: value.audio_duration_seconds,
    transcript: value.transcript,
    status: value.status,
    fluencyAndCoherence: criterion(value.fluency_and_cohesion),
    lexicalResource: criterion(value.lexical_resource),
    grammaticalRangeAndAccuracy: criterion(value.grammatical_range_and_accuracy),
    pronunciation: 'Not assessed',
    errorMessage: value.error_message,
    createdAt: value.created_at,
  };
}

@Injectable({ providedIn: 'root' })
export class SpeakingCoachRepository {
  constructor(private readonly api: ApiClient) {}

  async questions(): Promise<SpeakingQuestion[]> {
    return firstValueFrom(this.api.get<SpeakingQuestion[]>(
      '/api/speaking-coach/questions',
    ));
  }

  async create(
    questionId: string,
    audio: Blob,
    durationSeconds: number,
  ): Promise<SpeakingSubmission> {
    const body = new FormData();
    body.append('question_id', questionId);
    body.append('duration_seconds', String(durationSeconds));
    body.append('audio', audio, 'response.webm');
    return submission(await firstValueFrom(
      this.api.post<any>('/api/speaking-coach/submissions', body),
    ));
  }

  async transcribe(id: string): Promise<SpeakingSubmission> {
    return submission(await firstValueFrom(this.api.post<any>(
      `/api/speaking-coach/submissions/${encodeURIComponent(id)}/transcribe`,
      {},
    )));
  }

  async evaluate(id: string): Promise<SpeakingSubmission> {
    return submission(await firstValueFrom(this.api.post<any>(
      `/api/speaking-coach/submissions/${encodeURIComponent(id)}/evaluate`,
      {},
    )));
  }

  async list(): Promise<SpeakingSubmission[]> {
    return (await firstValueFrom(
      this.api.get<any[]>('/api/speaking-coach/submissions'),
    )).map(submission);
  }

  async get(id: string): Promise<SpeakingSubmission> {
    return submission(await firstValueFrom(this.api.get<any>(
      `/api/speaking-coach/submissions/${encodeURIComponent(id)}`,
    )));
  }
}
