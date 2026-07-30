import { Injectable, signal } from '@angular/core';
import { PracticeResultRepository } from '../data/practice-result.repository';
import {
  PracticeResult,
  PracticeResultCreate,
} from '../models/practice-result.model';

export type PracticeLogSubmissionState =
  | 'filled'
  | 'saving'
  | 'error'
  | 'confirmed';

@Injectable({ providedIn: 'root' })
export class PracticeLogFacade {
  private readonly stateSignal = signal<PracticeLogSubmissionState>('filled');
  private readonly draftSignal = signal<PracticeResultCreate | null>(null);
  private readonly savedResultSignal = signal<PracticeResult | null>(null);

  readonly submissionState = this.stateSignal.asReadonly();
  readonly draft = this.draftSignal.asReadonly();
  readonly savedResult = this.savedResultSignal.asReadonly();

  constructor(private readonly repository: PracticeResultRepository) {}

  fill(value: PracticeResultCreate): void {
    this.draftSignal.set({ ...value });
    if (this.stateSignal() !== 'saving') this.stateSignal.set('filled');
  }

  async submit(value?: PracticeResultCreate): Promise<void> {
    if (value) this.fill(value);
    const draft = this.draftSignal();
    if (!draft) return;
    this.stateSignal.set('saving');
    try {
      this.savedResultSignal.set(await this.repository.create(draft));
      this.stateSignal.set('confirmed');
    } catch (error) {
      this.stateSignal.set('error');
      throw error;
    }
  }

  retry(): Promise<void> {
    return this.submit();
  }

  reset(): void {
    this.draftSignal.set(null);
    this.savedResultSignal.set(null);
    this.stateSignal.set('filled');
  }
}
