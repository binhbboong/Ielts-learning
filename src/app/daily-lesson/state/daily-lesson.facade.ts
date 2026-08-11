import { Injectable, signal } from '@angular/core';
import { DailyLessonRepository } from '../data/daily-lesson.repository';
import { DailyOverview } from '../models/daily-focus.model';

export type DailyLessonLoadState = 'idle' | 'loading' | 'ready' | 'error';

@Injectable({ providedIn: 'root' })
export class DailyLessonFacade {
  private readonly stateSignal = signal<DailyLessonLoadState>('idle');
  private readonly overviewSignal = signal<DailyOverview | null>(null);

  readonly state = this.stateSignal.asReadonly();
  readonly overview = this.overviewSignal.asReadonly();

  constructor(private readonly repository: DailyLessonRepository) {}

  async load(day?: string): Promise<void> {
    this.stateSignal.set('loading');
    try {
      this.overviewSignal.set(await this.repository.getOverview(day));
      this.stateSignal.set('ready');
    } catch {
      this.stateSignal.set('error');
    }
  }

  async retry(skill: string, day: string): Promise<void> {
    const updated = await this.repository.retry(skill, day);
    const current = this.overviewSignal();
    if (!current) return;
    this.overviewSignal.set({
      ...current,
      skills: current.skills.map((entry) =>
        entry.skill === updated.skill && entry.day === updated.day ? updated : entry,
      ),
    });
  }
}
