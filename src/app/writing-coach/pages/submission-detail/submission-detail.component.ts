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
    taskResponse: WritingCriterion | null;
    coherenceAndCohesion: WritingCriterion | null;
    lexicalResource: WritingCriterion | null;
    grammaticalRangeAndAccuracy: WritingCriterion | null;
  }): { label: string; value: WritingCriterion | null }[] {
    return [
      { label: 'Task Response / Achievement', value: value.taskResponse },
      { label: 'Coherence and Cohesion', value: value.coherenceAndCohesion },
      { label: 'Lexical Resource', value: value.lexicalResource },
      { label: 'Grammatical Range and Accuracy', value: value.grammaticalRangeAndAccuracy },
    ];
  }
}
