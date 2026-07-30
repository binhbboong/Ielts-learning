import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { DatePipe, TitleCasePipe } from '@angular/common';
import { MistakeEntry, reasonLabel } from '../../models/mistake.model';

@Component({
  selector: 'app-review-list',
  standalone: true,
  imports: [DatePipe, TitleCasePipe],
  templateUrl: './review-list.component.html',
  styleUrl: './review-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewListComponent {
  readonly entries = input.required<MistakeEntry[]>();
  readonly sortedEntries = computed(() =>
    [...this.entries()].sort((a, b) => b.loggedAt.localeCompare(a.loggedAt)),
  );
  readonly reasonLabel = reasonLabel;
}
