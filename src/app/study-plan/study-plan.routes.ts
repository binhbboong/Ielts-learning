import { inject } from '@angular/core';
import { ResolveFn, Routes } from '@angular/router';
import { DailyChecklistComponent } from './pages/daily-checklist/daily-checklist.component';
import { TaskDetailComponent } from './pages/task-detail/task-detail.component';
import { DayHistoryComponent } from './pages/day-history/day-history.component';
import { StudyPlanFacade } from './state/study-plan.facade';
import { Task } from './models/task.model';

export const taskResolver: ResolveFn<Task | undefined> = (route) => {
  const facade = inject(StudyPlanFacade);
  const taskId = Number(route.paramMap.get('taskId'));
  return facade.getTaskById(taskId);
};

export const studyPlanRoutes: Routes = [
  { path: '', component: DailyChecklistComponent },
  { path: 'task/:taskId', component: TaskDetailComponent, resolve: { task: taskResolver } },
  { path: 'history', component: DayHistoryComponent },
];
