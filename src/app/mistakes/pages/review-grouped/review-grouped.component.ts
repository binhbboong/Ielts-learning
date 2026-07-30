import { ChangeDetectionStrategy, Component, computed, input, output } from '@angular/core';
import {
  MistakeGroupedCategory,
  ReasonCategory,
  reasonLabel,
} from '../../models/mistake.model';

@Component({
  selector: 'app-review-grouped',
  standalone: true,
  templateUrl: './review-grouped.component.html',
  styleUrl: './review-grouped.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewGroupedComponent {
  readonly groups = input.required<MistakeGroupedCategory[]>();
  readonly selected = output<ReasonCategory>();
  readonly rankedGroups = computed(() =>
    [...this.groups()].sort((a, b) => b.count - a.count),
  );
  readonly reasonLabel = reasonLabel;
}
