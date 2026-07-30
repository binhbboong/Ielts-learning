import { Routes } from '@angular/router';
import { WritingSubmitComponent } from './pages/submit/submit.component';
import { WritingSubmissionDetailComponent } from './pages/submission-detail/submission-detail.component';
import { WritingSubmissionListComponent } from './pages/submission-list/submission-list.component';

export const writingCoachRoutes: Routes = [
  { path: '', component: WritingSubmitComponent },
  { path: 'history', component: WritingSubmissionListComponent },
  { path: 'submissions/:id', component: WritingSubmissionDetailComponent },
];
