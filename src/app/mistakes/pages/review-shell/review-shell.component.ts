import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ReasonCategory, reasonLabel } from '../../models/mistake.model';
import {
  REVIEW_PERIOD_OPTIONS,
  ReviewPeriod,
} from '../../models/review-period.model';
import { MistakeFacade, MistakeViewMode } from '../../state/mistake.facade';
import { ReviewCategoryDetailComponent } from '../review-category-detail/review-category-detail.component';
import { ReviewGroupedComponent } from '../review-grouped/review-grouped.component';
import { ReviewListComponent } from '../review-list/review-list.component';

@Component({
  selector: 'app-review-shell',
  standalone: true,
  imports: [
    FormsModule,
    ReviewListComponent,
    ReviewGroupedComponent,
    ReviewCategoryDetailComponent,
  ],
  templateUrl: './review-shell.component.html',
  styleUrl: './review-shell.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewShellComponent {
  readonly facade = inject(MistakeFacade);
  readonly periods = REVIEW_PERIOD_OPTIONS;
  readonly selectedReason = signal<ReasonCategory | null>(null);
  readonly reasonLabel = reasonLabel;

  ngOnInit(): void {
    void this.facade.load();
  }

  changePeriod(period: ReviewPeriod): void {
    this.selectedReason.set(null);
    void this.facade.selectPeriod(period);
  }

  changeView(mode: MistakeViewMode): void {
    this.selectedReason.set(null);
    void this.facade.setViewMode(mode);
  }

  showCategory(reason: ReasonCategory): void {
    this.selectedReason.set(reason);
    void this.facade.loadCategory(reason);
  }
}
