import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import {
  TrendPeriod,
  TrendSkill,
} from '../../models/practice-result.model';
import { ProgressTrendFacade } from '../../state/progress-trend.facade';

@Component({
  selector: 'app-progress-trend',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './progress-trend.component.html',
  styleUrl: './progress-trend.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ProgressTrendComponent implements OnInit {
  readonly facade = inject(ProgressTrendFacade);

  async ngOnInit(): Promise<void> {
    await this.loadSafely();
  }

  async setSkill(skill: TrendSkill): Promise<void> {
    try {
      await this.facade.setSkill(skill);
    } catch {
      // Visible error state is owned by the facade.
    }
  }

  async setPeriod(period: TrendPeriod): Promise<void> {
    try {
      await this.facade.setPeriod(period);
    } catch {
      // Visible error state is owned by the facade.
    }
  }

  async refresh(): Promise<void> {
    await this.loadSafely();
  }

  humanize(key: string): string {
    return key
      .split('_')
      .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }

  directionLabel(direction: string | null): string {
    if (direction === 'up') return 'Improving';
    if (direction === 'down') return 'Needs attention';
    return 'Steady';
  }

  private async loadSafely(): Promise<void> {
    try {
      await this.facade.refresh();
    } catch {
      // Visible error state is owned by the facade.
    }
  }
}
