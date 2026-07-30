import {
  ChangeDetectionStrategy,
  Component,
  Input,
  inject,
  output,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  MistakeCreate,
  MistakeSkill,
  REASON_OPTIONS,
  ReasonCategory,
} from '../../models/mistake.model';
import { MistakeFacade } from '../../state/mistake.facade';

@Component({
  selector: 'app-logging-form',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './logging-form.component.html',
  styleUrl: './logging-form.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LoggingFormComponent {
  private readonly facade = inject(MistakeFacade);

  readonly saved = output<void>();
  readonly cancelled = output<void>();
  readonly reasons = REASON_OPTIONS;

  skill: MistakeSkill = 'reading';
  source = '';
  questionType = '';
  ownAnswer = '';
  correctAnswer = '';
  explanation = '';
  reasonCategory: ReasonCategory = 'not_sure_other';
  correctAnswerUnknown = false;
  validationMessage = '';

  @Input()
  set initialSkill(value: MistakeSkill) {
    this.skill = value;
  }

  @Input()
  set initialSource(value: string) {
    this.source = value;
  }

  private optional(value: string): string | undefined {
    const trimmed = value.trim();
    return trimmed || undefined;
  }

  private payload(): MistakeCreate | null {
    if (!this.skill || !this.source.trim()) {
      this.validationMessage = 'Skill and source are required.';
      return null;
    }
    this.validationMessage = '';
    return {
      skill: this.skill,
      source: this.source.trim(),
      questionType: this.optional(this.questionType),
      ownAnswer: this.optional(this.ownAnswer),
      correctAnswer: this.correctAnswerUnknown
        ? undefined
        : this.optional(this.correctAnswer),
      explanation: this.optional(this.explanation),
      reasonCategory: this.reasonCategory,
    };
  }

  async save(): Promise<void> {
    const payload = this.payload();
    if (!payload) return;
    await this.facade.create(payload);
    this.saved.emit();
  }

  async close(): Promise<void> {
    await this.save();
  }

  cancel(): void {
    this.cancelled.emit();
  }
}
