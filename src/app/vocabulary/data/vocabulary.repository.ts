import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  AddWordResult,
  DueQueueSummary,
  VocabularyWord,
  VocabularyWordCreate,
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
