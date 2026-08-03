import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { VocabularyFacade } from '../../state/vocabulary.facade';

@Component({
  selector: 'app-vocabulary-quiz',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './vocabulary-quiz.component.html',
  styleUrl: './vocabulary-quiz.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class VocabularyQuizComponent {
  readonly facade = inject(VocabularyFacade);
  readonly answering = signal(false);

  ngOnInit(): void {
    void this.facade.startQuiz().catch(() => undefined);
  }

  async answer(index: number): Promise<void> {
    if (this.answering()) return;
    this.answering.set(true);
    try {
      await this.facade.answerQuizItem(index);
    } finally {
      this.answering.set(false);
    }
  }
}
