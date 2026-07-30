import { Component, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StudyPlanFacade } from '../../state/study-plan.facade';
import { Task } from '../../models/task.model';

/** Read-only: selecting and viewing a past day's tasks has no mutation controls (FR-10). */
@Component({
  selector: 'app-day-history',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './day-history.component.html',
})
export class DayHistoryComponent {
  constructor(private readonly facade: StudyPlanFacade) {}

  protected readonly availableDays = computed(() =>
    Array.from({ length: Math.max(this.facade.currentDayNumber() - 1, 0) }, (_, i) => i + 1),
  );

  protected readonly selectedDay = signal<number | null>(null);
  protected readonly historyTasks = signal<Task[]>([]);

  protected async selectDay(day: number): Promise<void> {
    this.selectedDay.set(day);
    const tasks = await this.facade.getHistoryForDay(day);
    this.historyTasks.set(tasks);
  }
}
