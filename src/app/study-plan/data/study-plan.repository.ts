import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import { PlanState } from '../models/plan-state.model';
import { Skill, Task, TaskStatus } from '../models/task.model';

interface ApiTask {
  id: number;
  day_number: number;
  skill: string;
  title: string;
  description: string;
  estimated_minutes: number;
  status: string;
  note: string | null;
  updated_at: string;
}

interface ApiPlanState {
  current_day_number: number;
  total_days: number;
}

interface ApiMoveResult {
  blocked: boolean;
  unresolved_task_ids: number[];
  current_day_number: number;
}

export type RepositoryMoveResult =
  | { success: true; currentDayNumber: number }
  | { success: false; unresolvedTaskIds: number[] };

const SKILLS: Record<string, Skill> = {
  grammar: 'Grammar',
  vocabulary: 'Vocabulary',
  listening: 'Listening',
  reading: 'Reading',
  speaking: 'Speaking',
  writing: 'Writing',
  review: 'Review',
};

const STATUSES_FROM_API: Record<string, TaskStatus> = {
  not_started: 'NotStarted',
  completed: 'Completed',
  skipped: 'Skipped',
};

const STATUSES_TO_API: Record<TaskStatus, string> = {
  NotStarted: 'not_started',
  Completed: 'completed',
  Skipped: 'skipped',
};

function mapTask(task: ApiTask): Task {
  return {
    id: task.id,
    dayNumber: task.day_number,
    skill: SKILLS[task.skill],
    title: task.title,
    description: task.description,
    estimatedMinutes: task.estimated_minutes,
    status: STATUSES_FROM_API[task.status],
    note: task.note ?? '',
    updatedAt: task.updated_at,
  };
}

@Injectable({ providedIn: 'root' })
export class StudyPlanRepository {
  constructor(private readonly api: ApiClient) {}

  async getPlanState(): Promise<PlanState> {
    const state = await firstValueFrom(
      this.api.get<ApiPlanState>('/api/study-plan/state'),
    );
    return {
      currentDayNumber: state.current_day_number,
      totalDays: state.total_days,
    };
  }

  async getTasksForDay(dayNumber: number): Promise<Task[]> {
    const tasks = await firstValueFrom(
      this.api.get<ApiTask[]>(`/api/study-plan/days/${dayNumber}/tasks`),
    );
    return tasks.map(mapTask);
  }

  async getTask(id: number): Promise<Task | undefined> {
    const task = await firstValueFrom(
      this.api.get<ApiTask>(`/api/study-plan/tasks/${id}`),
    );
    return mapTask(task);
  }

  async updateTaskStatus(id: number, status: TaskStatus): Promise<Task> {
    const task = await firstValueFrom(
      this.api.patch<ApiTask>(`/api/study-plan/tasks/${id}/status`, {
        status: STATUSES_TO_API[status],
      }),
    );
    return mapTask(task);
  }

  async updateTaskNote(id: number, note: string): Promise<Task> {
    const task = await firstValueFrom(
      this.api.patch<ApiTask>(`/api/study-plan/tasks/${id}/note`, { note }),
    );
    return mapTask(task);
  }

  async updateTaskDetails(
    id: number,
    details: { description: string; estimatedMinutes: number },
  ): Promise<Task> {
    const task = await firstValueFrom(
      this.api.patch<ApiTask>(`/api/study-plan/tasks/${id}`, {
        description: details.description,
        estimated_minutes: details.estimatedMinutes,
      }),
    );
    return mapTask(task);
  }

  async moveToNextDay(): Promise<RepositoryMoveResult> {
    let result: ApiMoveResult;
    try {
      result = await firstValueFrom(
        this.api.post<ApiMoveResult>('/api/study-plan/move-to-next-day', {}),
      );
    } catch (error) {
      if (error instanceof HttpErrorResponse && error.status === 409) {
        return {
          success: false,
          unresolvedTaskIds: error.error.detail.unresolved_task_ids,
        };
      }
      throw error;
    }
    return result.blocked
      ? {
          success: false,
          unresolvedTaskIds: result.unresolved_task_ids,
        }
      : { success: true, currentDayNumber: result.current_day_number };
  }
}
