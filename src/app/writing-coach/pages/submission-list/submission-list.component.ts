import { DatePipe } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { WritingCoachFacade } from '../../state/writing-coach.facade';

@Component({
  selector: 'app-writing-submission-list',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './submission-list.component.html',
  styleUrl: './submission-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WritingSubmissionListComponent implements OnInit {
  readonly facade = inject(WritingCoachFacade);

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async load(): Promise<void> {
    try {
      await this.facade.loadSubmissions();
    } catch {
      // Facade owns the visible error state.
    }
  }

  isDevelopmental(exerciseType: string | null | undefined): boolean {
    return Boolean(exerciseType && [
      'sentence_building', 'sentence_expansion', 'guided_paragraph', 'structured_response',
    ].includes(exerciseType));
  }

  exerciseLabel(exerciseType: string | null | undefined, taskType: string): string {
    const labels: Record<string, string> = {
      sentence_building: 'Sentence foundations',
      sentence_expansion: 'Connect and expand',
      guided_paragraph: 'Guided paragraph',
      structured_response: 'Structured response',
      ielts_task1: 'IELTS Task 1',
      ielts_task2: 'IELTS Task 2',
      exam_simulation: 'Timed exam practice',
    };
    return exerciseType ? labels[exerciseType] ?? exerciseType : (taskType === 'task1' ? 'Task 1' : 'Task 2');
  }
}
