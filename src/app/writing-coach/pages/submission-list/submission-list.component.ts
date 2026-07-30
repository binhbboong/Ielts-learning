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
}
