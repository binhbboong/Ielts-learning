import { Location } from '@angular/common';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { WritingTaskType } from '../../models/writing-submission.model';
import { WritingCoachFacade } from '../../state/writing-coach.facade';

@Component({
  selector: 'app-writing-submit',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './submit.component.html',
  styleUrl: './submit.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WritingSubmitComponent {
  private readonly location = inject(Location);
  readonly facade = inject(WritingCoachFacade);
  taskType: WritingTaskType = 'task2';
  questionText = '';
  responseText = '';

  get canSubmit(): boolean {
    return Boolean(this.questionText.trim() && this.responseText.trim());
  }

  async submit(): Promise<void> {
    if (!this.canSubmit) return;
    try {
      await this.facade.submit({
        taskType: this.taskType,
        questionText: this.questionText.trim(),
        responseText: this.responseText.trim(),
      });
    } catch {
      // Facade owns the visible retry state and retained draft.
    }
  }

  async retry(): Promise<void> {
    try {
      await this.facade.retry();
    } catch {
      // Preserve the same retry state.
    }
  }

  cancel(): void {
    this.location.back();
  }
}
