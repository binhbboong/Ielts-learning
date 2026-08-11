import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { WritingCriterion } from '../../models/writing-submission.model';
import { WritingCoachFacade } from '../../state/writing-coach.facade';

@Component({
  selector: 'app-writing-submission-detail',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './submission-detail.component.html',
  styleUrl: './submission-detail.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WritingSubmissionDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly facade = inject(WritingCoachFacade);

  async ngOnInit(): Promise<void> {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    try {
      await this.facade.loadSubmission(id);
    } catch {
      // Facade owns the visible error state.
    }
  }

  criteria(value: {
    exerciseType?: string | null;
    taskResponse: WritingCriterion | null;
    coherenceAndCohesion: WritingCriterion | null;
    lexicalResource: WritingCriterion | null;
    grammaticalRangeAndAccuracy: WritingCriterion | null;
  }): { label: string; value: WritingCriterion | null }[] {
    if (this.isDevelopmental(value.exerciseType)) {
      return [
        { label: 'Follow the instruction', value: value.taskResponse },
        { label: 'Connect your sentences', value: value.coherenceAndCohesion },
        { label: 'Choose useful words', value: value.lexicalResource },
        { label: 'Build accurate sentences', value: value.grammaticalRangeAndAccuracy },
      ];
    }
    return [
      { label: 'Task Response / Achievement', value: value.taskResponse },
      { label: 'Coherence and Cohesion', value: value.coherenceAndCohesion },
      { label: 'Lexical Resource', value: value.lexicalResource },
      { label: 'Grammatical Range and Accuracy', value: value.grammaticalRangeAndAccuracy },
    ];
  }

  isDevelopmental(exerciseType: string | null | undefined): boolean {
    return Boolean(exerciseType && [
      'sentence_building',
      'sentence_expansion',
      'guided_paragraph',
      'structured_response',
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
