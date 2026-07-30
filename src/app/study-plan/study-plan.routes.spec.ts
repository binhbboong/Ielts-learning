import { TestBed } from '@angular/core/testing';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { signal } from '@angular/core';
import { routes } from '../app.routes';
import { StudyPlanFacade } from './state/study-plan.facade';
import { DailyChecklistComponent } from './pages/daily-checklist/daily-checklist.component';
import { TaskDetailComponent } from './pages/task-detail/task-detail.component';
import { DayHistoryComponent } from './pages/day-history/day-history.component';
import { Task } from './models/task.model';
import { AuthState } from '../core/auth/state/auth.state';

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 1,
    dayNumber: 1,
    skill: 'Grammar',
    title: 'Grammar practice',
    description: 'desc',
    estimatedMinutes: 20,
    status: 'NotStarted',
    note: '',
    updatedAt: '',
    ...overrides,
  };
}

describe('Study Plan routing', () => {
  beforeEach(() => {
    const facadeStub = {
      tasks: signal<Task[]>([]),
      currentDayNumber: signal(4),
      loadCurrentDay: jasmine.createSpy('loadCurrentDay').and.resolveTo(undefined),
      getHistoryForDay: jasmine.createSpy('getHistoryForDay').and.resolveTo([]),
      getTaskById: jasmine.createSpy('getTaskById').and.resolveTo(makeTask({ id: 1 })),
    };

    TestBed.configureTestingModule({
      providers: [
        provideRouter(routes, withComponentInputBinding()),
        { provide: StudyPlanFacade, useValue: facadeStub },
        {
          provide: AuthState,
          useValue: {
            authenticated: signal(true),
            initialized: signal(true),
          },
        },
      ],
    });
  });

  it('resolves the default route (/) to DailyChecklistComponent', async () => {
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl('/', DailyChecklistComponent as any);
    expect(component).toBeInstanceOf(DailyChecklistComponent);
  });

  it('resolves a task-detail route to TaskDetailComponent', async () => {
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl('/task/day-1-0', TaskDetailComponent as any);
    expect(component).toBeInstanceOf(TaskDetailComponent);
  });

  it('resolves the history route to DayHistoryComponent', async () => {
    const harness = await RouterTestingHarness.create();
    const component = await harness.navigateByUrl('/history', DayHistoryComponent as any);
    expect(component).toBeInstanceOf(DayHistoryComponent);
  });
});
