import {
  ChangeDetectionStrategy,
  Component,
  EventEmitter,
  Input,
  Output,
  inject,
} from '@angular/core';
import { MistakeRepository } from '../../data/mistake.repository';
import { MistakeSkill, REASON_OPTIONS, ReasonCategory } from '../../models/mistake.model';

export interface MistakeQuickAddData {
  skill: MistakeSkill;
  source: string;
  ownAnswer: string;
  correctAnswer: string;
}

@Component({
  selector: 'app-mistake-quick-add',
  standalone: true,
  imports: [],
  templateUrl: './mistake-quick-add.component.html',
  styleUrl: './mistake-quick-add.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MistakeQuickAddComponent {
  private readonly repository = inject(MistakeRepository);

  @Input({ required: true }) data!: MistakeQuickAddData;
  @Output() readonly saved = new EventEmitter<void>();
  @Output() readonly cancelled = new EventEmitter<void>();

  readonly reasonOptions = REASON_OPTIONS;
  selectedReason: ReasonCategory | null = null;
  saving = false;

  selectReason(reason: ReasonCategory): void {
    this.selectedReason = reason;
  }

  async save(): Promise<void> {
    this.saving = true;
    try {
      await this.repository.create({
        skill: this.data.skill,
        source: this.data.source,
        ownAnswer: this.data.ownAnswer,
        correctAnswer: this.data.correctAnswer,
        reasonCategory: this.selectedReason ?? undefined,
      });
      this.saved.emit();
    } finally {
      this.saving = false;
    }
  }

  cancel(): void {
    this.cancelled.emit();
  }
}
