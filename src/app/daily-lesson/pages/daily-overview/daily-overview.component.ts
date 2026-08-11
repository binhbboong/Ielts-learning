import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { ReviewOutcome } from '../../../vocabulary/models/review-session.model';
import { VocabularyFacade } from '../../../vocabulary/state/vocabulary.facade';
import { LessonCalendarDay, Skill, SkillOverviewEntry } from '../../models/daily-focus.model';
import { DailyLessonFacade } from '../../state/daily-lesson.facade';

function todayIso(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
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
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  readonly today = todayIso();
  // Speaking is no longer part of the daily rotation/checkpoint (it remains a
  // standalone feature reachable from the secondary-links nav) — see
  // docs/adr/2026-08-05-remove-speaking-from-daily-checkpoint.md.
  readonly skillOrder: readonly Skill[] = ['reading', 'listening', 'writing'];
  readonly vocabularyRevealed = signal(false);
  readonly vocabularyAssessing = signal(false);
  readonly addingRecommendation = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    const routeDay = this.route.snapshot.queryParamMap.get('day');
    const lessonDay = routeDay && routeDay !== this.today ? routeDay : undefined;
    await Promise.all([
      this.facade.load(lessonDay),
      this.vocabulary.startOrResumeReview(lessonDay).catch(() => undefined),
      this.vocabulary.loadRecommendations().catch(() => undefined),
    ]);
  }

  isCarriedOver(entry: Pick<SkillOverviewEntry, 'day'>): boolean {
    return entry.day !== this.today;
  }

  doneActionLabel(entry: Pick<SkillOverviewEntry, 'skill'>): string {
    return entry.skill === 'writing' ? 'Try again' : 'Review';
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

  skillQueryParams(entry: Pick<SkillOverviewEntry, 'skill' | 'day'>): Record<string, string> | null {
    return entry.skill === 'writing' ? { day: entry.day } : null;
  }

  skillEntry(entries: SkillOverviewEntry[], skill: Skill): SkillOverviewEntry | undefined {
    return entries.find((entry) => entry.skill === skill);
  }

  async retry(skill: string, day: string): Promise<void> {
    await this.facade.retry(skill, day);
  }

  async selectDay(item: LessonCalendarDay): Promise<void> {
    if (item.status === 'inactive' || item.status === 'upcoming' || item.selected) return;
    const day = item.day === this.today ? undefined : item.day;
    this.vocabularyRevealed.set(false);
    await Promise.all([
      this.facade.load(day),
      this.vocabulary.startOrResumeReview(day).catch(() => undefined),
    ]);
    await this.router.navigate([], { queryParams: { day: day ?? null } });
  }

  async backToToday(): Promise<void> {
    this.vocabularyRevealed.set(false);
    await Promise.all([
      this.facade.load(),
      this.vocabulary.startOrResumeReview().catch(() => undefined),
    ]);
    await this.router.navigate([], { queryParams: { day: null } });
  }

  calendarDayLabel(day: string): string {
    return new Intl.DateTimeFormat('en', { weekday: 'short', day: 'numeric', month: 'short' })
      .format(new Date(`${day}T00:00:00`));
  }

  calendarTitle(item: LessonCalendarDay): string {
    const labels: Record<LessonCalendarDay['status'], string> = {
      inactive: 'Before your study plan',
      upcoming: 'Not available yet',
      today: item.passedCount === item.requiredCount ? 'Today · complete' : 'Today’s lesson',
      complete: 'Completed · open to review',
      missed: `Needs make-up · ${item.passedCount}/${item.requiredCount} skills complete`,
    };
    return `${this.calendarDayLabel(item.day)} · ${labels[item.status]}`;
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
