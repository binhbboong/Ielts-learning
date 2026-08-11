import { Injectable, signal } from '@angular/core';
import { VocabularyRepository } from '../data/vocabulary.repository';
import {
  AddWordResult,
  DueQueueSummary,
  VocabularyHistory,
  VocabularyWordCreate,
  VocabularyRecommendationFeed,
} from '../models/vocabulary-word.model';
import {
  QuizState,
  ReviewOutcome,
  ReviewSessionState,
} from '../models/review-session.model';

export type VocabularyLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class VocabularyFacade {
  private reviewDay: string | undefined;
  private quizDay: string | undefined;
  private readonly dueSummarySignal = signal<DueQueueSummary | null>(null);
  private readonly reviewStateSignal = signal<ReviewSessionState | null>(null);
  private readonly dueLoadStateSignal = signal<VocabularyLoadState>('idle');
  private readonly reviewLoadStateSignal = signal<VocabularyLoadState>('idle');
  private readonly recommendationsSignal =
    signal<VocabularyRecommendationFeed | null>(null);
  private readonly recommendationsLoadStateSignal =
    signal<VocabularyLoadState>('idle');
  private readonly historySignal = signal<VocabularyHistory | null>(null);
  private readonly historyLoadStateSignal = signal<VocabularyLoadState>('idle');
  private readonly quizStateSignal = signal<QuizState | null>(null);
  private readonly quizLoadStateSignal = signal<VocabularyLoadState>('idle');

  readonly dueSummary = this.dueSummarySignal.asReadonly();
  readonly reviewState = this.reviewStateSignal.asReadonly();
  readonly dueLoadState = this.dueLoadStateSignal.asReadonly();
  readonly reviewLoadState = this.reviewLoadStateSignal.asReadonly();
  readonly recommendations = this.recommendationsSignal.asReadonly();
  readonly recommendationsLoadState =
    this.recommendationsLoadStateSignal.asReadonly();
  readonly history = this.historySignal.asReadonly();
  readonly historyLoadState = this.historyLoadStateSignal.asReadonly();
  readonly quizState = this.quizStateSignal.asReadonly();
  readonly quizLoadState = this.quizLoadStateSignal.asReadonly();

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

  async loadRecommendations(): Promise<void> {
    this.recommendationsLoadStateSignal.set('loading');
    try {
      this.recommendationsSignal.set(
        await this.repository.getRecommendations(),
      );
      this.recommendationsLoadStateSignal.set('ready');
    } catch (error) {
      this.recommendationsSignal.set(null);
      this.recommendationsLoadStateSignal.set('error');
      throw error;
    }
  }

  async addRecommendation(key: string): Promise<void> {
    await this.repository.addRecommendation(key);
    await Promise.all([this.loadRecommendations(), this.loadDueSummary()]);
  }

  async startOrResumeReview(day?: string): Promise<void> {
    this.reviewDay = day;
    this.reviewLoadStateSignal.set('loading');
    try {
      this.reviewStateSignal.set(
        await (day
          ? this.repository.startOrResumeReview(day)
          : this.repository.startOrResumeReview()),
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
      await (this.reviewDay
        ? this.repository.assessCurrentItem(outcome, this.reviewDay)
        : this.repository.assessCurrentItem(outcome)),
    );
  }

  addWord(value: VocabularyWordCreate): Promise<AddWordResult> {
    return this.repository.addWord(value);
  }

  async loadHistory(): Promise<void> {
    this.historyLoadStateSignal.set('loading');
    try {
      this.historySignal.set(await this.repository.getHistory());
      this.historyLoadStateSignal.set('ready');
    } catch (error) {
      this.historySignal.set(null);
      this.historyLoadStateSignal.set('error');
      throw error;
    }
  }

  async startQuiz(day?: string): Promise<void> {
    this.quizDay = day;
    this.quizLoadStateSignal.set('loading');
    try {
      this.quizStateSignal.set(
        await (day ? this.repository.startQuiz(day) : this.repository.startQuiz()),
      );
      this.quizLoadStateSignal.set('ready');
    } catch (error) {
      this.quizStateSignal.set(null);
      this.quizLoadStateSignal.set('error');
      throw error;
    }
  }

  async answerQuizItem(selectedOptionIndex: number): Promise<void> {
    this.quizStateSignal.set(
      await (this.quizDay
        ? this.repository.answerQuizItem(selectedOptionIndex, this.quizDay)
        : this.repository.answerQuizItem(selectedOptionIndex)),
    );
  }
}
