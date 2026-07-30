import { ChangeDetectionStrategy, Component, input, output } from '@angular/core';
import { MistakeSkill } from '../../models/mistake.model';

export interface MistakeStudyContext {
  skill: MistakeSkill;
  source: string;
}

@Component({
  selector: 'app-log-entry-action',
  standalone: true,
  templateUrl: './log-entry-action.component.html',
  styleUrl: './log-entry-action.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogEntryActionComponent {
  readonly context = input.required<MistakeStudyContext>();
  readonly opened = output<MistakeStudyContext>();

  open(): void {
    this.opened.emit({ ...this.context() });
  }
}
