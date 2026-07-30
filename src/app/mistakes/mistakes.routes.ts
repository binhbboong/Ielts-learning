import { Routes } from '@angular/router';
import { LoggingFormComponent } from './pages/logging-form/logging-form.component';
import { ReviewShellComponent } from './pages/review-shell/review-shell.component';

export const routes: Routes = [
  { path: '', component: ReviewShellComponent },
  { path: 'log', component: LoggingFormComponent },
];
