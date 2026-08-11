import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { AddVocabularyWordPanelComponent } from '../../components/add-vocabulary-word-panel/add-vocabulary-word-panel.component';
import { ReviewOutcome } from '../../models/review-session.model';
import { VocabularyFacade } from '../../state/vocabulary.facade';

@Component({
  selector: 'app-vocabulary-review-session',
  standalone: true,
  imports: [AddVocabularyWordPanelComponent, RouterLink],
  templateUrl: './vocabulary-review-session.component.html',
  styleUrl: './vocabulary-review-session.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VocabularyReviewSessionComponent {
  readonly facade = inject(VocabularyFacade);
  private readonly route = inject(ActivatedRoute);
  readonly day = this.route.snapshot.queryParamMap.get('day');
  readonly revealed = signal(false);
  readonly addPanelOpen = signal(false);
  readonly assessing = signal(false);
  readonly wordAddedMessage = signal('');

  ngOnInit(): void {
    void this.facade.startOrResumeReview(this.day ?? undefined).catch(() => undefined);
  }

  reveal(): void {
    this.revealed.set(true);
  }

  async assess(outcome: ReviewOutcome): Promise<void> {
    if (this.assessing()) return;
    this.assessing.set(true);
    try {
      await this.facade.assessCurrentItem(outcome);
      this.revealed.set(false);
    } finally {
      this.assessing.set(false);
    }
  }

  wordSaved(): void {
    this.addPanelOpen.set(false);
    this.wordAddedMessage.set('Word added to your review schedule.');
  }
}
