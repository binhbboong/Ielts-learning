import { ChangeDetectionStrategy, Component, input } from '@angular/core';
import { MistakeCategoryDetail } from '../../models/mistake.model';

@Component({
  selector: 'app-review-category-detail',
  standalone: true,
  templateUrl: './review-category-detail.component.html',
  styleUrl: './review-category-detail.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReviewCategoryDetailComponent {
  readonly items = input.required<MistakeCategoryDetail[]>();
}
