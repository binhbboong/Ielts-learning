import { Injectable, signal } from '@angular/core';
import { ReadingPracticeRepository } from '../data/reading-practice.repository';
import {
  ReadingExercise,
  ReadingSubmissionResult,
} from '../models/reading-exercise.model';

export type ReadingLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class ReadingPracticeFacade {
  private readonly exerciseStateSignal = signal<ReadingLoadState>('idle');
  private readonly submitStateSignal = signal<ReadingLoadState>('idle');
  private readonly exerciseSignal = signal<ReadingExercise | null>(null);
  private readonly resultSignal = signal<ReadingSubmissionResult | null>(null);
  private daySignal = signal<string | null>(null);

  readonly exerciseState = this.exerciseStateSignal.asReadonly();
  readonly submitState = this.submitStateSignal.asReadonly();
  readonly exercise = this.exerciseSignal.asReadonly();
  readonly result = this.resultSignal.asReadonly();

  constructor(private readonly repository: ReadingPracticeRepository) {}

  async load(day: string): Promise<void> {
    this.daySignal.set(day);
    this.resultSignal.set(null);
    this.exerciseStateSignal.set('loading');
    try {
      this.exerciseSignal.set(await this.repository.get(day));
      this.exerciseStateSignal.set('ready');
    } catch {
      this.exerciseStateSignal.set('error');
    }
  }

  async submit(answers: (number | string)[]): Promise<void> {
    const day = this.daySignal();
    if (!day) return;
    this.submitStateSignal.set('loading');
    try {
      this.resultSignal.set(await this.repository.submit(day, answers));
      this.submitStateSignal.set('ready');
    } catch {
      this.submitStateSignal.set('error');
    }
  }

  async retry(): Promise<void> {
    const day = this.daySignal();
    if (!day) return;
    this.exerciseStateSignal.set('loading');
    try {
      this.exerciseSignal.set(await this.repository.retry(day));
      this.exerciseStateSignal.set('ready');
    } catch {
      this.exerciseStateSignal.set('error');
    }
  }
}
