import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  AddWordResult,
  DueQueueSummary,
  VocabularyHistory,
  VocabularyWord,
  VocabularyWordCreate,
  VocabularyRecommendationFeed,
} from '../models/vocabulary-word.model';
import {
  ReviewItem,
  ReviewOutcome,
  ReviewSessionState,
} from '../models/review-session.model';

function mapWord(value: any): VocabularyWord {
  return {
    id: value.id,
    word: value.word,
    meaning: value.meaning,
    example: value.example,
    topic: value.topic,
    targetBand: value.target_band ?? null,
    cefrLevel: value.cefr_level ?? null,
    source: value.source ?? 'manual',
    intervalIndex: value.interval_index,
    nextDueDate: value.next_due_date,
    createdAt: value.created_at,
    lastReviewedAt: value.last_reviewed_at,
  };
}

function mapItem(value: any): ReviewItem {
  return {
    sessionId: value.session_id,
    itemId: value.item_id,
    wordId: value.word_id,
    word: value.word,
    meaning: value.meaning,
    example: value.example,
    position: value.position,
    total: value.total,
    isNew: value.is_new,
  };
}

function mapReviewState(value: any): ReviewSessionState {
  if (value.status === 'item') {
    return { status: 'item', item: mapItem(value.item) };
  }
  if (value.status === 'complete') {
    const summary = value.summary;
    return {
      status: 'complete',
      summary: summary
        ? {
            sessionId: summary.session_id,
            totalReviewed: summary.total_reviewed,
            forgot: summary.forgot,
            remembered: summary.remembered,
            newWordsIncluded: summary.new_words_included,
            reviewDatesUpdated: summary.review_dates_updated,
          }
        : undefined,
    };
  }
  return { status: value.status };
}

@Injectable({ providedIn: 'root' })
export class VocabularyRepository {
  constructor(private readonly api: ApiClient) {}

  async addWord(value: VocabularyWordCreate): Promise<AddWordResult> {
    const body: Record<string, string> = {
      word: value.word,
      meaning: value.meaning,
    };
    if (value.example) body['example'] = value.example;
    if (value.topic) body['topic'] = value.topic;
    const result = await firstValueFrom(
      this.api.post<any>('/api/vocabulary/words', body),
    );
    return { saved: true, word: mapWord(result.word) };
  }

  async getDueSummary(): Promise<DueQueueSummary> {
    const result = await firstValueFrom(
      this.api.get<any>('/api/vocabulary/due'),
    );
    return {
      totalDue: result.total_due,
      byInterval: result.by_interval,
      byTopic: result.by_topic,
      dailyTarget: result.daily_target,
      backfillCount: result.backfill_count,
      shortfall: result.shortfall,
    };
  }

  async getRecommendations(): Promise<VocabularyRecommendationFeed> {
    const result = await firstValueFrom(
      this.api.get<any>('/api/vocabulary/recommendations'),
    );
    return {
      currentBand: result.current_band,
      cefrLevel: result.cefr_level,
      phase: result.phase,
      week: result.week,
      recommendations: result.recommendations.map((item: any) => ({
        key: item.key,
        word: item.word,
        meaning: item.meaning,
        example: item.example,
        topic: item.topic,
        targetBand: item.target_band,
        cefrLevel: item.cefr_level,
      })),
    };
  }

  async addRecommendation(key: string): Promise<AddWordResult> {
    const result = await firstValueFrom(
      this.api.post<any>(
        `/api/vocabulary/recommendations/${encodeURIComponent(key)}/add`,
        {},
      ),
    );
    return { saved: true, word: mapWord(result.word) };
  }

  async getHistory(): Promise<VocabularyHistory> {
    const result = await firstValueFrom(
      this.api.get<any>('/api/vocabulary/history'),
    );
    return {
      days: (result.days ?? []).map((day: any) => ({
        day: day.day,
        wordsAdded: (day.words_added ?? []).map((w: any) => ({
          word: w.word,
          meaning: w.meaning,
        })),
        wordsReviewed: (day.words_reviewed ?? []).map((r: any) => ({
          word: r.word,
          outcome: r.outcome,
          assessedAt: r.assessed_at,
        })),
      })),
    };
  }

  async startOrResumeReview(): Promise<ReviewSessionState> {
    return mapReviewState(
      await firstValueFrom(
        this.api.post<any>('/api/vocabulary/review/start', {}),
      ),
    );
  }

  async getCurrentItem(): Promise<ReviewSessionState> {
    return mapReviewState(
      await firstValueFrom(
        this.api.get<any>('/api/vocabulary/review/current'),
      ),
    );
  }

  async assessCurrentItem(
    outcome: ReviewOutcome,
  ): Promise<ReviewSessionState> {
    return mapReviewState(
      await firstValueFrom(
        this.api.post<any>('/api/vocabulary/review/current/assess', {
          outcome,
        }),
      ),
    );
  }
}
