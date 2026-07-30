import { Injectable, signal } from '@angular/core';
import { ListeningPracticeRepository } from '../data/listening-practice.repository';
import {
  ListeningExercise,
  ListeningSubmissionResult,
} from '../models/listening-exercise.model';

export type ListeningLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class ListeningPracticeFacade {
  private readonly exerciseStateSignal = signal<ListeningLoadState>('idle');
  private readonly submitStateSignal = signal<ListeningLoadState>('idle');
  private readonly exerciseSignal = signal<ListeningExercise | null>(null);
  private readonly resultSignal = signal<ListeningSubmissionResult | null>(null);
  private daySignal = signal<string | null>(null);

  readonly exerciseState = this.exerciseStateSignal.asReadonly();
  readonly submitState = this.submitStateSignal.asReadonly();
  readonly exercise = this.exerciseSignal.asReadonly();
  readonly result = this.resultSignal.asReadonly();

  constructor(private readonly repository: ListeningPracticeRepository) {}

  audioUrl(day: string): string {
    return this.repository.audioUrl(day);
  }

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

  async submit(answers: number[]): Promise<void> {
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

  async retryScript(): Promise<void> {
    const day = this.daySignal();
    if (!day) return;
    this.exerciseStateSignal.set('loading');
    try {
      this.exerciseSignal.set(await this.repository.retryScript(day));
      this.exerciseStateSignal.set('ready');
    } catch {
      this.exerciseStateSignal.set('error');
    }
  }

  async retryAudio(): Promise<void> {
    const day = this.daySignal();
    if (!day) return;
    this.exerciseStateSignal.set('loading');
    try {
      this.exerciseSignal.set(await this.repository.retryAudio(day));
      this.exerciseStateSignal.set('ready');
    } catch {
      this.exerciseStateSignal.set('error');
    }
  }
}
