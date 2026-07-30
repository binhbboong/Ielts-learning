import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  MistakeCategoryDetail,
  MistakeCreate,
  MistakeEntry,
  MistakeGroupedCategory,
  ReasonCategory,
} from '../models/mistake.model';
import { DateRange } from '../models/review-period.model';

interface ApiMistake {
  id: string;
  skill: MistakeEntry['skill'];
  question_type: string | null;
  source: string;
  own_answer: string | null;
  correct_answer: string | null;
  explanation: string | null;
  reason_category: ReasonCategory;
  logged_at: string;
  is_incomplete: boolean;
}

function mapEntry(value: ApiMistake): MistakeEntry {
  return {
    id: value.id,
    skill: value.skill,
    questionType: value.question_type,
    source: value.source,
    ownAnswer: value.own_answer,
    correctAnswer: value.correct_answer,
    explanation: value.explanation,
    reasonCategory: value.reason_category,
    loggedAt: value.logged_at,
    isIncomplete: value.is_incomplete,
  };
}

function query(range: DateRange): string {
  return `start=${encodeURIComponent(range.start.toISOString())}&end=${encodeURIComponent(
    range.end.toISOString(),
  )}`;
}

@Injectable({ providedIn: 'root' })
export class MistakeRepository {
  constructor(private readonly api: ApiClient) {}

  async create(value: MistakeCreate): Promise<MistakeEntry> {
    const body: Record<string, unknown> = {
      skill: value.skill,
      source: value.source,
    };
    const mappings: Array<[keyof MistakeCreate, string]> = [
      ['questionType', 'question_type'],
      ['ownAnswer', 'own_answer'],
      ['correctAnswer', 'correct_answer'],
      ['explanation', 'explanation'],
      ['reasonCategory', 'reason_category'],
    ];
    for (const [key, apiKey] of mappings) {
      if (value[key] !== undefined) body[apiKey] = value[key];
    }
    return mapEntry(
      await firstValueFrom(this.api.post<ApiMistake>('/api/mistakes', body)),
    );
  }

  async listChronological(range: DateRange): Promise<MistakeEntry[]> {
    const rows = await firstValueFrom(
      this.api.get<ApiMistake[]>(`/api/mistakes?${query(range)}`),
    );
    return rows.map(mapEntry);
  }

  async listGrouped(range: DateRange): Promise<MistakeGroupedCategory[]> {
    const rows = await firstValueFrom(
      this.api.get<Array<{ reason_category: ReasonCategory; count: number }>>(
        `/api/mistakes/grouped?${query(range)}`,
      ),
    );
    return rows.map((row) => ({
      reasonCategory: row.reason_category,
      count: row.count,
    }));
  }

  async getCategoryDetail(
    reason: ReasonCategory,
    range: DateRange,
  ): Promise<MistakeCategoryDetail[]> {
    const rows = await firstValueFrom(
      this.api.get<
        Array<{
          own_answer: string | null;
          correct_answer: string | null;
          explanation: string | null;
        }>
      >(`/api/mistakes/grouped/${reason}?${query(range)}`),
    );
    return rows.map((row) => ({
      ownAnswer: row.own_answer,
      correctAnswer: row.correct_answer,
      explanation: row.explanation,
    }));
  }
}
