import { Injectable, signal } from '@angular/core';
import { StudyPlanRepository } from '../data/study-plan.repository';
import { Task, TaskStatus } from '../models/task.model';

export type MoveToNextDayResult =
  | { success: true }
  | { success: false; unresolvedTaskIds: number[] };

@Injectable({ providedIn: 'root' })
export class StudyPlanFacade {
  private readonly currentDayNumberSignal = signal(1);
  private readonly tasksSignal = signal<Task[]>([]);

  readonly currentDayNumber = this.currentDayNumberSignal.asReadonly();
  readonly tasks = this.tasksSignal.asReadonly();

  constructor(private readonly repository: StudyPlanRepository) {}

  async loadCurrentDay(): Promise<void> {
    const planState = await this.repository.getPlanState();
    this.currentDayNumberSignal.set(planState.currentDayNumber);
    await this.refreshCurrentDayTasks();
  }

  private async refreshCurrentDayTasks(): Promise<void> {
    const tasks = await this.repository.getTasksForDay(this.currentDayNumberSignal());
    this.tasksSignal.set(tasks);
  }

  async setStatus(taskId: number, status: TaskStatus): Promise<void> {
    await this.repository.updateTaskStatus(taskId, status);
    await this.refreshCurrentDayTasks();
  }

  async updateNote(taskId: number, note: string): Promise<void> {
    await this.repository.updateTaskNote(taskId, note);
    await this.refreshCurrentDayTasks();
  }

  async updateTaskDetails(
    taskId: number,
    details: { description: string; estimatedMinutes: number },
  ): Promise<void> {
    await this.repository.updateTaskDetails(taskId, details);
    await this.refreshCurrentDayTasks();
  }

  async moveToNextDay(): Promise<MoveToNextDayResult> {
    const result = await this.repository.moveToNextDay();
    if (!result.success) {
      return { success: false, unresolvedTaskIds: result.unresolvedTaskIds };
    }
    this.currentDayNumberSignal.set(result.currentDayNumber);
    await this.refreshCurrentDayTasks();
    return { success: true };
  }

  getHistoryForDay(dayNumber: number): Promise<Task[]> {
    return this.repository.getTasksForDay(dayNumber);
  }

  getTaskById(id: number): Promise<Task | undefined> {
    return this.repository.getTask(id);
  }
}
