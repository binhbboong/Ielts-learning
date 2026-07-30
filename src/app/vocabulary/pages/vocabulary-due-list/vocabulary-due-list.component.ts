import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { AddVocabularyWordPanelComponent } from '../../components/add-vocabulary-word-panel/add-vocabulary-word-panel.component';
import { VocabularyFacade } from '../../state/vocabulary.facade';

@Component({
  selector: 'app-vocabulary-due-list',
  standalone: true,
  imports: [AddVocabularyWordPanelComponent],
  templateUrl: './vocabulary-due-list.component.html',
  styleUrl: './vocabulary-due-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VocabularyDueListComponent {
  readonly facade = inject(VocabularyFacade);
  readonly addPanelOpen = signal(false);
  readonly wordAddedMessage = signal('');

  ngOnInit(): void {
    void this.facade.loadDueSummary().catch(() => undefined);
  }

  entries(value: Record<string, number>): Array<[string, number]> {
    return Object.entries(value);
  }

  wordSaved(): void {
    this.addPanelOpen.set(false);
    this.wordAddedMessage.set('Word added to your review schedule.');
  }
}
