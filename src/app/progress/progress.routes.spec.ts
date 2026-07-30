import { progressRoutes } from './progress.routes';
import { LogPracticeResultComponent } from './pages/log-practice-result/log-practice-result.component';
import { PracticeLogHistoryComponent } from './pages/practice-log-history/practice-log-history.component';
import { ProgressTrendComponent } from './pages/progress-trend/progress-trend.component';

describe('progressRoutes', () => {
  it('declares trend, log, and history screens', () => {
    expect(progressRoutes).toEqual([
      { path: '', component: ProgressTrendComponent },
      { path: 'log', component: LogPracticeResultComponent },
      { path: 'history', component: PracticeLogHistoryComponent },
    ]);
  });
});
