import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { VocabularyFacade } from '../../state/vocabulary.facade';

@Component({
  selector: 'app-vocabulary-history',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './vocabulary-history.component.html',
  styleUrl: './vocabulary-history.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VocabularyHistoryComponent implements OnInit {
  readonly facade = inject(VocabularyFacade);

  async ngOnInit(): Promise<void> {
    await this.facade.loadHistory();
  }
}
