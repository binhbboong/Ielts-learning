import { Location, NgTemplateOutlet } from '@angular/common';
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { DailyLessonFacade } from '../../../daily-lesson/state/daily-lesson.facade';
import { SkillOverviewEntry } from '../../../daily-lesson/models/daily-focus.model';
import { WritingTaskType } from '../../models/writing-submission.model';
import { WritingCoachFacade } from '../../state/writing-coach.facade';

@Component({
  selector: 'app-writing-submit',
  standalone: true,
  imports: [FormsModule, RouterLink, NgTemplateOutlet],
  templateUrl: './submit.component.html',
  styleUrl: './submit.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class WritingSubmitComponent implements OnInit {
  private readonly location = inject(Location);
  readonly facade = inject(WritingCoachFacade);
  private readonly dailyLessonFacade = inject(DailyLessonFacade);
  taskType: WritingTaskType = 'task2';
  questionText = '';
  responseText = '';
  promptDay: string | null = null;
  promptTargetBand: number | null = null;
  promptPhase: string | null = null;
  practiceEntry: SkillOverviewEntry | null = null;
  readonly writingAgain = signal(false);

  async ngOnInit(): Promise<void> {
    if (this.dailyLessonFacade.state() === 'idle') {
      await this.dailyLessonFacade.load().catch(() => undefined);
    }
    const overview = this.dailyLessonFacade.overview();
    const entry = overview?.skills.find(
      (s) => s.skill === 'writing' && s.generatedPromptText,
    );
    if (entry?.generatedPromptText) {
      this.practiceEntry = entry;
      this.questionText = entry.generatedPromptText;
      this.promptDay = entry.day;
      this.promptTargetBand = entry.targetBand;
      this.promptPhase = entry.phase;
      // Task 1/Task 2 alternate from the standard tier onward — pre-fill the
      // task type the generated prompt actually is, rather than leaving the
      // default 'task2' selected for a Task 1 (data-description) prompt.
      if (entry.taskType === 'task1' || entry.taskType === 'task2') {
        this.taskType = entry.taskType;
      }
    }
    if (this.promptDay) {
      await this.facade.loadLatestForDay(this.promptDay).catch(() => undefined);
    }
  }

  writeAgain(): void {
    this.writingAgain.set(true);
  }

  get canSubmit(): boolean {
    return Boolean(
      this.questionText.trim() &&
      this.responseText.trim() &&
      this.meetsMinimumTarget,
    );
  }

  get wordCount(): number {
    const text = this.responseText.trim();
    return text ? text.split(/\s+/).length : 0;
  }

  get sentenceCount(): number {
    const text = this.responseText.trim();
    if (!text) return 0;
    const completed = text.match(/[^.!?]+[.!?]+(?=\s|$)/g)?.length ?? 0;
    const remainder = text.replace(/[^.!?]+[.!?]+(?=\s|$)/g, '').trim();
    return completed + (remainder ? 1 : 0);
  }

  get meetsMinimumTarget(): boolean {
    if (!this.practiceEntry) return true;
    const minSentences = this.practiceEntry.minSentences ?? 1;
    const minWords = this.practiceEntry.minWords ?? 1;
    return this.sentenceCount >= minSentences && this.wordCount >= minWords;
  }

  get showIeltsTaskSelector(): boolean {
    return this.practiceEntry?.showIeltsBand ?? true;
  }

  isDevelopmental(exerciseType: string | null | undefined): boolean {
    return Boolean(exerciseType && [
      'sentence_building',
      'sentence_expansion',
      'guided_paragraph',
      'structured_response',
    ].includes(exerciseType));
  }

  async submit(): Promise<void> {
    if (!this.canSubmit) return;
    try {
      await this.facade.submit({
        taskType: this.taskType,
        questionText: this.questionText.trim(),
        responseText: this.responseText.trim(),
        day: this.promptDay ?? undefined,
      });
    } catch {
      // Facade owns the visible retry state and retained draft.
    }
  }

  async retry(): Promise<void> {
    try {
      await this.facade.retry();
    } catch {
      // Preserve the same retry state.
    }
  }

  cancel(): void {
    this.location.back();
  }
}
