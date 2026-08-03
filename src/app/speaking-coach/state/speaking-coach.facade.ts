import { Injectable, signal } from '@angular/core';
import { SpeakingCoachRepository } from '../data/speaking-coach.repository';
import { SpeakingQuestion } from '../models/speaking-question.model';
import { SpeakingSubmission } from '../models/speaking-submission.model';

export type SpeakingLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class SpeakingCoachFacade {
  private readonly stateSignal = signal<SpeakingLoadState>('idle');
  private readonly questionsSignal = signal<SpeakingQuestion[]>([]);
  private readonly currentSignal = signal<SpeakingSubmission | null>(null);
  private readonly submissionsSignal = signal<SpeakingSubmission[]>([]);

  readonly state = this.stateSignal.asReadonly();
  readonly questions = this.questionsSignal.asReadonly();
  readonly current = this.currentSignal.asReadonly();
  readonly submissions = this.submissionsSignal.asReadonly();

  constructor(private readonly repository: SpeakingCoachRepository) {}

  async loadQuestions(): Promise<void> {
    this.questionsSignal.set(await this.repository.questions());
  }

  async submit(
    options: { questionId?: string; promptText?: string; day?: string },
    audio: Blob,
    durationSeconds: number,
  ): Promise<void> {
    this.stateSignal.set('loading');
    try {
      const created = await this.repository.create({ ...options, audio, durationSeconds });
      this.currentSignal.set(created);
      await this.advanceProcessing(created);
      this.stateSignal.set('ready');
    } catch (error) {
      this.stateSignal.set('error');
      throw error;
    }
  }

  async loadSubmissions(): Promise<void> {
    this.stateSignal.set('loading');
    try {
      this.submissionsSignal.set(await this.repository.list());
      this.stateSignal.set('ready');
    } catch (error) {
      this.submissionsSignal.set([]);
      this.stateSignal.set('error');
      throw error;
    }
  }

  async loadSubmission(id: string): Promise<void> {
    this.stateSignal.set('loading');
    try {
      const value = await this.repository.get(id);
      this.currentSignal.set(value);
      if (value.status === 'PROCESSING') await this.advanceProcessing(value);
      this.stateSignal.set('ready');
    } catch (error) {
      this.currentSignal.set(null);
      this.stateSignal.set('error');
      throw error;
    }
  }

  async retryTranscription(): Promise<void> {
    const current = this.currentSignal();
    if (!current) return;
    this.stateSignal.set('loading');
    const transcribed = await this.repository.transcribe(current.id);
    this.currentSignal.set(transcribed);
    if (transcribed.status === 'PROCESSING' && transcribed.transcript) {
      this.currentSignal.set(await this.repository.evaluate(current.id));
    }
    this.stateSignal.set('ready');
  }

  async retryEvaluation(): Promise<void> {
    const current = this.currentSignal();
    if (!current) return;
    this.stateSignal.set('loading');
    this.currentSignal.set(await this.repository.evaluate(current.id));
    this.stateSignal.set('ready');
  }

  private async advanceProcessing(value: SpeakingSubmission): Promise<void> {
    let next = value;
    if (!next.transcript) {
      next = await this.repository.transcribe(next.id);
      this.currentSignal.set(next);
    }
    if (next.status === 'PROCESSING' && next.transcript) {
      next = await this.repository.evaluate(next.id);
      this.currentSignal.set(next);
    }
  }
}
