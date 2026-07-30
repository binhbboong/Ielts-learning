import { Injectable, signal } from '@angular/core';
import { PracticeResultRepository } from '../data/practice-result.repository';
import {
  TrendPeriod,
  TrendResult,
  TrendSkill,
} from '../models/practice-result.model';

export type TrendLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class ProgressTrendFacade {
  private readonly skillSignal = signal<TrendSkill>('Both');
  private readonly periodSignal = signal<TrendPeriod>('8_weeks');
  private readonly resultSignal = signal<TrendResult | null>(null);
  private readonly loadStateSignal = signal<TrendLoadState>('idle');

  readonly skill = this.skillSignal.asReadonly();
  readonly period = this.periodSignal.asReadonly();
  readonly result = this.resultSignal.asReadonly();
  readonly loadState = this.loadStateSignal.asReadonly();

  constructor(private readonly repository: PracticeResultRepository) {}

  async load(): Promise<void> {
    this.loadStateSignal.set('loading');
    try {
      this.resultSignal.set(
        await this.repository.getTrend(this.skillSignal(), this.periodSignal()),
      );
      this.loadStateSignal.set('ready');
    } catch (error) {
      this.resultSignal.set(null);
      this.loadStateSignal.set('error');
      throw error;
    }
  }

  setSkill(skill: TrendSkill): Promise<void> {
    this.skillSignal.set(skill);
    return this.load();
  }

  setPeriod(period: TrendPeriod): Promise<void> {
    this.periodSignal.set(period);
    return this.load();
  }

  refresh(): Promise<void> {
    return this.load();
  }
}
