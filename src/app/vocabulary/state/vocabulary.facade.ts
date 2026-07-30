import { Injectable, signal } from '@angular/core';
import { VocabularyRepository } from '../data/vocabulary.repository';
import {
  AddWordResult,
  DueQueueSummary,
  VocabularyWordCreate,
} from '../models/vocabulary-word.model';
import {
  ReviewOutcome,
  ReviewSessionState,
} from '../models/review-session.model';

export type VocabularyLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class VocabularyFacade {
  private readonly dueSummarySignal = signal<DueQueueSummary | null>(null);
  private readonly reviewStateSignal = signal<ReviewSessionState | null>(null);
  private readonly dueLoadStateSignal = signal<VocabularyLoadState>('idle');
  private readonly reviewLoadStateSignal = signal<VocabularyLoadState>('idle');

  readonly dueSummary = this.dueSummarySignal.asReadonly();
  readonly reviewState = this.reviewStateSignal.asReadonly();
  readonly dueLoadState = this.dueLoadStateSignal.asReadonly();
  readonly reviewLoadState = this.reviewLoadStateSignal.asReadonly();

  constructor(private readonly repository: VocabularyRepository) {}

  async loadDueSummary(): Promise<void> {
    this.dueLoadStateSignal.set('loading');
    try {
      this.dueSummarySignal.set(await this.repository.getDueSummary());
      this.dueLoadStateSignal.set('ready');
    } catch (error) {
      this.dueSummarySignal.set(null);
      this.dueLoadStateSignal.set('error');
      throw error;
    }
  }

  async startOrResumeReview(): Promise<void> {
    this.reviewLoadStateSignal.set('loading');
    try {
      this.reviewStateSignal.set(
        await this.repository.startOrResumeReview(),
      );
      this.reviewLoadStateSignal.set('ready');
    } catch (error) {
      this.reviewStateSignal.set(null);
      this.reviewLoadStateSignal.set('error');
      throw error;
    }
  }

  async assessCurrentItem(outcome: ReviewOutcome): Promise<void> {
    this.reviewStateSignal.set(
      await this.repository.assessCurrentItem(outcome),
    );
  }

  addWord(value: VocabularyWordCreate): Promise<AddWordResult> {
    return this.repository.addWord(value);
  }
}
