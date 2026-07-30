import { Injectable, signal } from '@angular/core';
import { WritingCoachRepository } from '../data/writing-coach.repository';
import {
  WritingSubmissionCreate,
  WritingSubmissionDetail,
  WritingSubmissionSummary,
} from '../models/writing-submission.model';

export type WritingLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class WritingCoachFacade {
  private readonly submissionStateSignal = signal<WritingLoadState>('idle');
  private readonly listStateSignal = signal<WritingLoadState>('idle');
  private readonly detailStateSignal = signal<WritingLoadState>('idle');
  private readonly draftSignal = signal<WritingSubmissionCreate | null>(null);
  private readonly currentSignal = signal<WritingSubmissionDetail | null>(null);
  private readonly submissionsSignal = signal<WritingSubmissionSummary[]>([]);

  readonly submissionState = this.submissionStateSignal.asReadonly();
  readonly listState = this.listStateSignal.asReadonly();
  readonly detailState = this.detailStateSignal.asReadonly();
  readonly draft = this.draftSignal.asReadonly();
  readonly current = this.currentSignal.asReadonly();
  readonly submissions = this.submissionsSignal.asReadonly();

  constructor(private readonly repository: WritingCoachRepository) {}

  async submit(value?: WritingSubmissionCreate): Promise<void> {
    if (value) this.draftSignal.set({ ...value });
    const draft = this.draftSignal();
    if (!draft) return;
    this.submissionStateSignal.set('loading');
    try {
      this.currentSignal.set(await this.repository.submit(draft));
      this.submissionStateSignal.set('ready');
    } catch (error) {
      this.submissionStateSignal.set('error');
      throw error;
    }
  }

  retry(): Promise<void> {
    return this.submit();
  }

  async loadSubmissions(): Promise<void> {
    this.listStateSignal.set('loading');
    try {
      this.submissionsSignal.set(await this.repository.list());
      this.listStateSignal.set('ready');
    } catch (error) {
      this.submissionsSignal.set([]);
      this.listStateSignal.set('error');
      throw error;
    }
  }

  async loadSubmission(id: string): Promise<void> {
    this.detailStateSignal.set('loading');
    try {
      this.currentSignal.set(await this.repository.get(id));
      this.detailStateSignal.set('ready');
    } catch (error) {
      this.currentSignal.set(null);
      this.detailStateSignal.set('error');
      throw error;
    }
  }
}
