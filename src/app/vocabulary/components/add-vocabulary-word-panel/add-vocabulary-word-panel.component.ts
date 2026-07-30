import { Component, inject, output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { VocabularyFacade } from '../../state/vocabulary.facade';

@Component({
  selector: 'app-add-vocabulary-word-panel',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './add-vocabulary-word-panel.component.html',
  styleUrl: './add-vocabulary-word-panel.component.css',
})
export class AddVocabularyWordPanelComponent {
  private readonly facade = inject(VocabularyFacade);
  readonly closed = output<void>();
  readonly saved = output<void>();

  word = '';
  meaning = '';
  example = '';
  topic = '';
  saving = false;
  savedMessage = '';
  errorMessage = '';

  get saveDisabled(): boolean {
    return this.saving || !this.word.trim() || !this.meaning.trim();
  }

  async save(): Promise<void> {
    if (this.saveDisabled) return;
    this.saving = true;
    this.errorMessage = '';
    this.savedMessage = '';
    try {
      await this.facade.addWord({
        word: this.word.trim(),
        meaning: this.meaning.trim(),
        example: this.example.trim() || undefined,
        topic: this.topic.trim() || undefined,
      });
      this.savedMessage = 'Added to your review schedule.';
      this.saved.emit();
    } catch {
      this.errorMessage = 'Could not save the word. Please try again.';
    } finally {
      this.saving = false;
    }
  }
}
