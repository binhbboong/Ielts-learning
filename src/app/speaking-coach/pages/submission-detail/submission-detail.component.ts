import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { SpeakingCriterion } from '../../models/speaking-submission.model';
import { SpeakingCoachFacade } from '../../state/speaking-coach.facade';

@Component({
  selector: 'app-speaking-submission-detail',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './submission-detail.component.html',
  styleUrl: './submission-detail.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SpeakingSubmissionDetailComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly facade = inject(SpeakingCoachFacade);

  async ngOnInit(): Promise<void> {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) return;
    try {
      await this.facade.loadSubmission(id);
    } catch {
      // Facade owns visible error state.
    }
  }

  criteria(value: any): { label: string; value: SpeakingCriterion | null }[] {
    return [
      { label: 'Fluency and Coherence', value: value.fluencyAndCoherence },
      { label: 'Lexical Resource', value: value.lexicalResource },
      { label: 'Grammar', value: value.grammaticalRangeAndAccuracy },
    ];
  }

  retryTranscription(): Promise<void> {
    return this.facade.retryTranscription();
  }

  retryEvaluation(): Promise<void> {
    return this.facade.retryEvaluation();
  }
}
