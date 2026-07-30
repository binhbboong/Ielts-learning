import { StudyPlanRepository } from '../data/study-plan.repository';
import { Task } from '../models/task.model';
import { StudyPlanFacade } from './study-plan.facade';

function task(id: number, status: Task['status'] = 'NotStarted'): Task {
  return {
    id,
    dayNumber: 3,
    skill: 'Reading',
    title: 'Read',
    description: 'Practice',
    estimatedMinutes: 20,
    status,
    note: '',
    updatedAt: '',
  };
}

describe('StudyPlanFacade', () => {
  let repository: jasmine.SpyObj<StudyPlanRepository>;
  let facade: StudyPlanFacade;

  beforeEach(() => {
    repository = jasmine.createSpyObj<StudyPlanRepository>('StudyPlanRepository', [
      'getPlanState',
      'getTasksForDay',
      'getTask',
      'updateTaskStatus',
      'updateTaskNote',
      'updateTaskDetails',
      'moveToNextDay',
    ]);
    repository.getPlanState.and.resolveTo({ currentDayNumber: 3, totalDays: 180 });
    repository.getTasksForDay.and.resolveTo([task(1)]);
    repository.getTask.and.resolveTo(task(1));
    repository.updateTaskStatus.and.resolveTo(task(1, 'Completed'));
    repository.updateTaskNote.and.resolveTo(task(1));
    repository.updateTaskDetails.and.resolveTo(task(1));
    facade = new StudyPlanFacade(repository);
  });

  it('loads current-day state and tasks', async () => {
    await facade.loadCurrentDay();
    expect(facade.currentDayNumber()).toBe(3);
    expect(facade.tasks()).toEqual([task(1)]);
    expect(repository.getTasksForDay).toHaveBeenCalledWith(3);
  });

  it('passes targeted mutations through and refreshes without changing day', async () => {
    await facade.loadCurrentDay();
    await facade.setStatus(1, 'Completed');
    await facade.updateNote(1, 'Remember');
    await facade.updateTaskDetails(1, {
      description: 'Edited',
      estimatedMinutes: 30,
    });

    expect(repository.updateTaskStatus).toHaveBeenCalledWith(1, 'Completed');
    expect(repository.updateTaskNote).toHaveBeenCalledWith(1, 'Remember');
    expect(repository.updateTaskDetails).toHaveBeenCalledWith(1, {
      description: 'Edited',
      estimatedMinutes: 30,
    });
    expect(facade.currentDayNumber()).toBe(3);
  });

  it('returns blocked move results without changing day', async () => {
    await facade.loadCurrentDay();
    repository.moveToNextDay.and.resolveTo({
      success: false,
      unresolvedTaskIds: [1],
    });

    expect(await facade.moveToNextDay()).toEqual({
      success: false,
      unresolvedTaskIds: [1],
    });
    expect(facade.currentDayNumber()).toBe(3);
  });

  it('applies successful movement and refreshes the new day', async () => {
    await facade.loadCurrentDay();
    repository.moveToNextDay.and.resolveTo({
      success: true,
      currentDayNumber: 4,
    });

    expect(await facade.moveToNextDay()).toEqual({ success: true });
    expect(facade.currentDayNumber()).toBe(4);
    expect(repository.getTasksForDay).toHaveBeenCalledWith(4);
  });

  it('supports history and task detail reads', async () => {
    await facade.getHistoryForDay(1);
    await facade.getTaskById(1);
    expect(repository.getTasksForDay).toHaveBeenCalledWith(1);
    expect(repository.getTask).toHaveBeenCalledWith(1);
  });
});
