import { Component, Input, OnChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StudyPlanFacade } from '../../state/study-plan.facade';
import { Task, TaskStatus } from '../../models/task.model';

@Component({
  selector: 'app-task-detail',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './task-detail.component.html',
})
export class TaskDetailComponent implements OnChanges {
  @Input() task!: Task;

  protected noteDraft = '';
  protected descriptionDraft = '';
  protected estimatedMinutesDraft = 0;

  constructor(protected readonly facade: StudyPlanFacade) {}

  ngOnChanges(): void {
    this.noteDraft = this.task?.note ?? '';
    this.descriptionDraft = this.task?.description ?? '';
    this.estimatedMinutesDraft = this.task?.estimatedMinutes ?? 0;
  }

  protected onNoteInput(event: Event): void {
    this.noteDraft = (event.target as HTMLTextAreaElement).value;
  }

  protected saveNote(): void {
    void this.facade.updateNote(this.task.id, this.noteDraft);
  }

  protected cancelNote(): void {
    this.noteDraft = this.task.note;
  }

  protected onDescriptionInput(event: Event): void {
    this.descriptionDraft = (event.target as HTMLTextAreaElement).value;
  }

  protected onEstimatedMinutesInput(event: Event): void {
    this.estimatedMinutesDraft = Number((event.target as HTMLInputElement).value);
  }

  protected saveDetails(): void {
    void this.facade.updateTaskDetails(this.task.id, {
      description: this.descriptionDraft,
      estimatedMinutes: this.estimatedMinutesDraft,
    });
  }

  protected cancelDetails(): void {
    this.descriptionDraft = this.task.description;
    this.estimatedMinutesDraft = this.task.estimatedMinutes;
  }

  protected setStatus(status: TaskStatus): void {
    void this.facade.setStatus(this.task.id, status);
  }
}
