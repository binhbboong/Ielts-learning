import { Component, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StudyPlanFacade, MoveToNextDayResult } from '../../state/study-plan.facade';

@Component({
  selector: 'app-daily-checklist',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './daily-checklist.component.html',
})
export class DailyChecklistComponent {
  constructor(protected readonly facade: StudyPlanFacade) {
    void this.facade.loadCurrentDay();
  }

  protected readonly tasks = computed(() => this.facade.tasks());
  protected readonly currentDayNumber = computed(() => this.facade.currentDayNumber());
  protected readonly resolvedCount = computed(
    () => this.tasks().filter((task) => task.status !== 'NotStarted').length,
  );

  protected setStatus(taskId: number, status: 'Completed' | 'Skipped' | 'NotStarted'): void {
    void this.facade.setStatus(taskId, status);
  }

  protected readonly blockedResult = signal<{ unresolvedTaskIds: number[] } | null>(null);

  protected async moveToNextDay(): Promise<void> {
    const result: MoveToNextDayResult = await this.facade.moveToNextDay();
    this.blockedResult.set(result.success ? null : { unresolvedTaskIds: result.unresolvedTaskIds });
  }
}
