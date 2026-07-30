import { Injectable, signal } from '@angular/core';
import { MistakeRepository } from '../data/mistake.repository';
import {
  MistakeCategoryDetail,
  MistakeCreate,
  MistakeEntry,
  MistakeGroupedCategory,
  ReasonCategory,
} from '../models/mistake.model';
import { ReviewPeriod } from '../models/review-period.model';
import { resolveReviewPeriod } from './mistake-period.resolver';

export type MistakeViewMode = 'list' | 'grouped';

@Injectable({ providedIn: 'root' })
export class MistakeFacade {
  private readonly periodSignal = signal<ReviewPeriod>('this_week');
  private readonly viewModeSignal = signal<MistakeViewMode>('list');
  private readonly entriesSignal = signal<MistakeEntry[]>([]);
  private readonly groupedSignal = signal<MistakeGroupedCategory[]>([]);
  private readonly categoryDetailSignal = signal<MistakeCategoryDetail[]>([]);

  readonly selectedPeriod = this.periodSignal.asReadonly();
  readonly viewMode = this.viewModeSignal.asReadonly();
  readonly entries = this.entriesSignal.asReadonly();
  readonly grouped = this.groupedSignal.asReadonly();
  readonly categoryDetail = this.categoryDetailSignal.asReadonly();

  constructor(private readonly repository: MistakeRepository) {}

  async create(value: MistakeCreate): Promise<MistakeEntry> {
    return this.repository.create(value);
  }

  async load(): Promise<void> {
    const range = resolveReviewPeriod(this.periodSignal());
    if (this.viewModeSignal() === 'list') {
      this.entriesSignal.set(await this.repository.listChronological(range));
    } else {
      this.groupedSignal.set(await this.repository.listGrouped(range));
    }
  }

  async selectPeriod(period: ReviewPeriod): Promise<void> {
    this.periodSignal.set(period);
    await this.load();
  }

  async setViewMode(mode: MistakeViewMode): Promise<void> {
    this.viewModeSignal.set(mode);
    await this.load();
  }

  async loadCategory(reason: ReasonCategory): Promise<void> {
    this.categoryDetailSignal.set(
      await this.repository.getCategoryDetail(
        reason,
        resolveReviewPeriod(this.periodSignal()),
      ),
    );
  }
}
