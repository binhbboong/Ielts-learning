import { Routes } from '@angular/router';
import { LogPracticeResultComponent } from './pages/log-practice-result/log-practice-result.component';
import { PracticeLogHistoryComponent } from './pages/practice-log-history/practice-log-history.component';
import { ProgressTrendComponent } from './pages/progress-trend/progress-trend.component';

export const progressRoutes: Routes = [
  { path: '', component: ProgressTrendComponent },
  { path: 'log', component: LogPracticeResultComponent },
  { path: 'history', component: PracticeLogHistoryComponent },
];
