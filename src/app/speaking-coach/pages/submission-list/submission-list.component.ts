import { DatePipe } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { SpeakingStatus } from '../../models/speaking-submission.model';
import { SpeakingCoachFacade } from '../../state/speaking-coach.facade';

@Component({
  selector: 'app-speaking-submission-list',
  standalone: true,
  imports: [DatePipe, RouterLink],
  templateUrl: './submission-list.component.html',
  styleUrl: './submission-list.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SpeakingSubmissionListComponent implements OnInit {
  readonly facade = inject(SpeakingCoachFacade);

  async ngOnInit(): Promise<void> {
    try {
      await this.facade.loadSubmissions();
    } catch {
      // Facade owns visible error state.
    }
  }

  statusLabel(status: SpeakingStatus): string {
    return {
      PROCESSING: 'Processing',
      TRANSCRIPTION_FAILED: 'Transcription failed',
      EVALUATION_FAILED: 'Evaluation failed',
      COMPLETED: 'Completed',
    }[status];
  }
}
