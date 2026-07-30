import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { StudyPlanRepository } from './study-plan.repository';

const API_TASK = {
  id: 7,
  day_number: 2,
  skill: 'reading',
  title: 'Read',
  description: 'Original',
  estimated_minutes: 20,
  status: 'not_started',
  note: null,
  updated_at: '2026-07-29T00:00:00Z',
};

describe('StudyPlanRepository', () => {
  let api: jasmine.SpyObj<ApiClient>;
  let repository: StudyPlanRepository;

  beforeEach(() => {
    api = jasmine.createSpyObj<ApiClient>('ApiClient', ['get', 'patch', 'post']);
    repository = new StudyPlanRepository(api);
  });

  it('maps plan state and task reads from snake_case', async () => {
    api.get.and.callFake(((url: string) => {
      if (url.endsWith('/state')) {
        return of({ current_day_number: 2, total_days: 180 });
      }
      if (url.includes('/days/')) {
        return of([API_TASK]);
      }
      return of(API_TASK);
    }) as never);

    expect(await repository.getPlanState()).toEqual({ currentDayNumber: 2, totalDays: 180 });
    expect(await repository.getTasksForDay(2)).toEqual([
      jasmine.objectContaining({
        id: 7,
        dayNumber: 2,
        skill: 'Reading',
        status: 'NotStarted',
        note: '',
      }),
    ]);
    expect((await repository.getTask(7))?.estimatedMinutes).toBe(20);
    expect(api.get).toHaveBeenCalledWith('/api/study-plan/days/2/tasks');
    expect(api.get).toHaveBeenCalledWith('/api/study-plan/tasks/7');
  });

  it('maps targeted mutations and their payloads', async () => {
    api.patch.and.returnValue(of({ ...API_TASK, status: 'completed' }));

    expect((await repository.updateTaskStatus(7, 'Completed')).status).toBe('Completed');
    await repository.updateTaskNote(7, 'Remember');
    await repository.updateTaskDetails(7, {
      description: 'Edited',
      estimatedMinutes: 35,
    });

    expect(api.patch).toHaveBeenCalledWith('/api/study-plan/tasks/7/status', {
      status: 'completed',
    });
    expect(api.patch).toHaveBeenCalledWith('/api/study-plan/tasks/7/note', {
      note: 'Remember',
    });
    expect(api.patch).toHaveBeenCalledWith('/api/study-plan/tasks/7', {
      description: 'Edited',
      estimated_minutes: 35,
    });
  });

  it('maps move-to-next-day success and blocked responses', async () => {
    api.post.and.returnValues(
      of({ blocked: false, unresolved_task_ids: [], current_day_number: 3 }),
      throwError(
        () =>
          new HttpErrorResponse({
            status: 409,
            error: { detail: { unresolved_task_ids: [7] } },
          }),
      ),
    );

    expect(await repository.moveToNextDay()).toEqual({
      success: true,
      currentDayNumber: 3,
    });
    expect(await repository.moveToNextDay()).toEqual({
      success: false,
      unresolvedTaskIds: [7],
    });
    expect(api.post).toHaveBeenCalledWith('/api/study-plan/move-to-next-day', {});
  });
});
