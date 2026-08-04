import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ReviewOutcome } from '../../../vocabulary/models/review-session.model';
import { VocabularyFacade } from '../../../vocabulary/state/vocabulary.facade';
import { Skill, SkillOverviewEntry } from '../../models/daily-focus.model';
import { DailyLessonFacade } from '../../state/daily-lesson.facade';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

@Component({
  selector: 'app-daily-overview',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './daily-overview.component.html',
  styleUrl: './daily-overview.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DailyOverviewComponent implements OnInit {
  readonly facade = inject(DailyLessonFacade);
  readonly vocabulary = inject(VocabularyFacade);
  readonly today = todayIso();
  readonly skillOrder: readonly Skill[] = ['reading', 'listening', 'writing', 'speaking'];
  readonly vocabularyRevealed = signal(false);
  readonly vocabularyAssessing = signal(false);
  readonly addingRecommendation = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    await Promise.all([
      this.facade.load(),
      this.vocabulary.startOrResumeReview().catch(() => undefined),
      this.vocabulary.loadRecommendations().catch(() => undefined),
    ]);
  }

  isCarriedOver(entry: Pick<SkillOverviewEntry, 'day'>): boolean {
    return entry.day !== this.today;
  }

  skillRoute(entry: Pick<SkillOverviewEntry, 'skill' | 'day'>): string[] {
    const routes: Record<string, string> = {
      reading: '/reading',
      listening: '/listening',
      writing: '/writing',
      speaking: '/speaking',
    };
    const base = routes[entry.skill] ?? '/';
    if (entry.skill === 'reading' || entry.skill === 'listening') {
      return [base, entry.day];
    }
    return [base];
  }

  async retry(skill: string, day: string): Promise<void> {
    await this.facade.retry(skill, day);
  }

  revealVocabulary(): void {
    this.vocabularyRevealed.set(true);
  }

  async assessVocabulary(outcome: ReviewOutcome): Promise<void> {
    if (this.vocabularyAssessing()) return;
    this.vocabularyAssessing.set(true);
    try {
      await this.vocabulary.assessCurrentItem(outcome);
      this.vocabularyRevealed.set(false);
    } finally {
      this.vocabularyAssessing.set(false);
    }
  }

  async addVocabularyRecommendation(key: string): Promise<void> {
    if (this.addingRecommendation()) return;
    this.addingRecommendation.set(key);
    try {
      await this.vocabulary.addRecommendation(key);
    } finally {
      this.addingRecommendation.set(null);
    }
  }
}
