import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
  signal,
} from '@angular/core';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { PracticeResultRepository } from '../../data/practice-result.repository';
import {
  HistorySort,
  PracticeResult,
  PracticeSkill,
} from '../../models/practice-result.model';

type HistoryLoadState = 'loading' | 'ready' | 'error';

@Component({
  selector: 'app-practice-log-history',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './practice-log-history.component.html',
  styleUrl: './practice-log-history.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PracticeLogHistoryComponent implements OnInit {
  private readonly repository = inject(PracticeResultRepository);
  readonly results = signal<PracticeResult[]>([]);
  readonly loadState = signal<HistoryLoadState>('loading');
  skill: PracticeSkill | undefined;
  sort: HistorySort = 'newest';

  async ngOnInit(): Promise<void> {
    await this.loadSafely();
  }

  async setSkill(skill: PracticeSkill | ''): Promise<void> {
    this.skill = skill || undefined;
    await this.loadSafely();
  }

  async setSort(sort: HistorySort): Promise<void> {
    this.sort = sort;
    await this.loadSafely();
  }

  async refresh(): Promise<void> {
    await this.loadSafely();
  }

  minutes(seconds: number): number {
    return Math.round(seconds / 60);
  }

  humanize(key: string): string {
    return key
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  private async loadSafely(): Promise<void> {
    this.loadState.set('loading');
    try {
      this.results.set(await this.repository.getHistory(this.skill, this.sort));
      this.loadState.set('ready');
    } catch {
      this.results.set([]);
      this.loadState.set('error');
    }
  }
}
