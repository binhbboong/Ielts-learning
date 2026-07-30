import { Routes } from '@angular/router';
import { RecordResponseComponent } from './pages/record-response/record-response.component';
import { SpeakingSubmissionDetailComponent } from './pages/submission-detail/submission-detail.component';
import { SpeakingSubmissionListComponent } from './pages/submission-list/submission-list.component';

export const speakingCoachRoutes: Routes = [
  { path: '', component: RecordResponseComponent },
  { path: 'history', component: SpeakingSubmissionListComponent },
  { path: 'submissions/:id', component: SpeakingSubmissionDetailComponent },
];
