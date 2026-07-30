import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  HistorySort,
  PracticeResult,
  PracticeResultCreate,
  PracticeSkill,
  TaxonomyResponse,
  TrendPeriod,
  TrendResult,
  TrendSkill,
} from '../models/practice-result.model';

function mapResult(value: any): PracticeResult {
  return {
    id: value.id,
    skill: value.skill,
    source: value.source,
    score: value.score,
    total: value.total,
    timeTakenSeconds: value.time_taken_seconds,
    missedQuestionTypes: value.missed_question_types ?? [],
    note: value.note ?? undefined,
    loggedAt: value.logged_at,
  };
}

function mapTrend(value: any): TrendResult {
  return {
    sessionCount: value.session_count,
    averageScorePercentage: value.average_score_percentage,
    direction: value.direction,
    threshold: value.threshold,
    breakdown: value.breakdown,
  };
}

@Injectable({ providedIn: 'root' })
export class PracticeResultRepository {
  constructor(private readonly api: ApiClient) {}

  async create(value: PracticeResultCreate): Promise<PracticeResult> {
    const body: Record<string, unknown> = {
      skill: value.skill,
      source: value.source,
      score: value.score,
      total: value.total,
      time_taken_seconds: value.timeTakenSeconds,
      missed_question_types: value.missedQuestionTypes ?? [],
    };
    if (value.note?.trim()) body['note'] = value.note.trim();
    return mapResult(await firstValueFrom(
      this.api.post<any>('/api/practice-results', body),
    ));
  }

  async getTaxonomy(): Promise<TaxonomyResponse> {
    return firstValueFrom(
      this.api.get<TaxonomyResponse>('/api/practice-results/taxonomy'),
    );
  }

  async getTrend(
    skill: TrendSkill = 'Both',
    period: TrendPeriod = '8_weeks',
  ): Promise<TrendResult> {
    const query = new URLSearchParams({ skill, period });
    return mapTrend(await firstValueFrom(
      this.api.get<any>(`/api/practice-results/trend?${query.toString()}`),
    ));
  }

  async getHistory(
    skill?: PracticeSkill,
    sort: HistorySort = 'newest',
  ): Promise<PracticeResult[]> {
    const query = new URLSearchParams();
    if (skill) query.set('skill', skill);
    query.set('sort', sort);
    const values = await firstValueFrom(
      this.api.get<any[]>(`/api/practice-results?${query.toString()}`),
    );
    return values.map(mapResult);
  }
}
