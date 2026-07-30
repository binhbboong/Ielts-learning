import { Location } from '@angular/common';
import {
  ChangeDetectionStrategy,
  Component,
  OnInit,
  inject,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { PracticeResultRepository } from '../../data/practice-result.repository';
import {
  PracticeResultCreate,
  PracticeSkill,
  QuestionTypeOption,
  TaxonomyResponse,
} from '../../models/practice-result.model';
import { PracticeLogFacade } from '../../state/practice-log.facade';

@Component({
  selector: 'app-log-practice-result',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './log-practice-result.component.html',
  styleUrl: './log-practice-result.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class LogPracticeResultComponent implements OnInit {
  private readonly repository = inject(PracticeResultRepository);
  private readonly location = inject(Location);
  readonly facade = inject(PracticeLogFacade);

  skill: PracticeSkill = 'Reading';
  source = '';
  score: number | null = null;
  total = 40;
  timeTakenMinutes: number | null = null;
  note = '';
  readonly missedQuestionTypes = new Set<string>();
  taxonomy: TaxonomyResponse = { Reading: [], Listening: [] };
  taxonomyFailed = false;

  get questionTypes(): QuestionTypeOption[] {
    return this.taxonomy[this.skill];
  }

  get canSave(): boolean {
    return Boolean(
      this.source.trim()
      && this.score !== null
      && this.score >= 0
      && this.total > 0
      && this.score <= this.total
      && this.timeTakenMinutes
      && this.timeTakenMinutes > 0,
    );
  }

  async ngOnInit(): Promise<void> {
    try {
      this.taxonomy = await this.repository.getTaxonomy();
    } catch {
      this.taxonomyFailed = true;
    }
  }

  changeSkill(skill: PracticeSkill): void {
    this.skill = skill;
    this.missedQuestionTypes.clear();
  }

  toggleMissedType(key: string, checked: boolean): void {
    if (checked) this.missedQuestionTypes.add(key);
    else this.missedQuestionTypes.delete(key);
  }

  private payload(): PracticeResultCreate {
    return {
      skill: this.skill,
      source: this.source.trim(),
      score: this.score ?? 0,
      total: this.total,
      timeTakenSeconds: Math.round((this.timeTakenMinutes ?? 0) * 60),
      missedQuestionTypes: [...this.missedQuestionTypes],
      note: this.note.trim() || undefined,
    };
  }

  async save(): Promise<void> {
    if (!this.canSave) return;
    try {
      await this.facade.submit(this.payload());
    } catch {
      // The facade exposes the visible error state and retains the draft.
    }
  }

  async retry(): Promise<void> {
    try {
      await this.facade.retry();
    } catch {
      // Keep the same recoverable error state.
    }
  }

  logAnother(): void {
    this.facade.reset();
    this.skill = 'Reading';
    this.source = '';
    this.score = null;
    this.total = 40;
    this.timeTakenMinutes = null;
    this.note = '';
    this.missedQuestionTypes.clear();
  }

  cancel(): void {
    this.location.back();
  }

  returnBack(): void {
    this.location.back();
  }
}
