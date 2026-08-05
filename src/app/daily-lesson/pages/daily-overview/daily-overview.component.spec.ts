import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { VocabularyRepository } from '../../../vocabulary/data/vocabulary.repository';
import { DailyLessonRepository } from '../../data/daily-lesson.repository';
import { DailyOverviewComponent } from './daily-overview.component';

const emptyOverview = {
  examType: 'ielts_academic',
  week: 1,
  phase: 'foundation',
  targetBand: 4.5,
  totalMinutes: 60,
  reviewMinutes: 10,
  effectiveDay: new Date().toISOString().slice(0, 10),
  checkpoint: {
    day: new Date().toISOString().slice(0, 10),
    skills: { reading: false, listening: false, writing: false, speaking: false },
    vocabularyQuiz: false,
    passedCount: 0,
    requiredCount: 5,
    allPassed: false,
  },
  skills: [],
};

async function setUp(
  repositoryOverrides: Partial<jasmine.SpyObj<DailyLessonRepository>> = {},
) {
  const repository = jasmine.createSpyObj<DailyLessonRepository>(
    'DailyLessonRepository', ['getOverview', 'retry'],
  );
  const vocabularyRepository = jasmine.createSpyObj<VocabularyRepository>(
    'VocabularyRepository',
    [
      'startOrResumeReview',
      'getRecommendations',
      'assessCurrentItem',
      'addRecommendation',
      'getDueSummary',
    ],
  );
  repository.getOverview.and.resolveTo(emptyOverview);
  vocabularyRepository.startOrResumeReview.and.resolveTo({ status: 'nothing_due' });
  vocabularyRepository.getRecommendations.and.resolveTo({
    currentBand: 4.5,
    cefrLevel: 'B1',
    phase: 'foundation',
    week: 1,
    recommendations: [],
  });
  Object.assign(repository, repositoryOverrides);

  await TestBed.configureTestingModule({
    imports: [DailyOverviewComponent],
    providers: [
      provideRouter([]),
      { provide: DailyLessonRepository, useValue: repository },
      { provide: VocabularyRepository, useValue: vocabularyRepository },
    ],
  }).compileComponents();
  const fixture = TestBed.createComponent(DailyOverviewComponent);
  return {
    fixture,
    component: fixture.componentInstance,
    repository,
    vocabularyRepository,
  };
}

// Matches the component's own todayIso() so these tests stay correct on any real calendar day.
const today = new Date().toISOString().slice(0, 10);

describe('DailyOverviewComponent', () => {
  it('loads the overview on init', async () => {
    const { fixture, repository, vocabularyRepository } = await setUp();
    await fixture.componentInstance.ngOnInit();
    expect(repository.getOverview).toHaveBeenCalled();
    expect(vocabularyRepository.startOrResumeReview).toHaveBeenCalled();
    expect(vocabularyRepository.getRecommendations).toHaveBeenCalled();
  });

  it('exposes the four skill cards for today', async () => {
    const { component } = await setUp({
      getOverview: jasmine.createSpy().and.resolveTo({
        skills: [
          { day: today, skill: 'reading', status: 'ready', focusReference: "the word 'nevertheless'" },
          { day: today, skill: 'listening', status: 'generating', focusReference: null },
          { day: today, skill: 'writing', status: 'done', focusReference: null },
          { day: today, skill: 'speaking', status: 'failed', focusReference: null },
        ],
      }) as any,
    });
    await component.ngOnInit();

    expect(component.facade.overview()?.skills.length).toBe(4);
  });

  it('distinguishes a carried-over day from today', async () => {
    const { component } = await setUp({
      getOverview: jasmine.createSpy().and.resolveTo({
        skills: [
          { day: today, skill: 'reading', status: 'ready', focusReference: null },
          { day: '2026-07-29', skill: 'writing', status: 'ready', focusReference: null },
        ],
      }) as any,
    });
    await component.ngOnInit();

    expect(component.isCarriedOver({ day: '2026-07-29' } as any)).toBeTrue();
    expect(component.isCarriedOver({ day: today } as any)).toBeFalse();
  });

  it('routes reading and listening to the entry day, not just the skill root', async () => {
    const { component } = await setUp();

    expect(component.skillRoute({ skill: 'reading', day: '2026-07-29' } as any)).toEqual([
      '/reading', '2026-07-29',
    ]);
    expect(component.skillRoute({ skill: 'listening', day: '2026-07-29' } as any)).toEqual([
      '/listening', '2026-07-29',
    ]);
  });

  it('routes writing and speaking to the skill root without a day segment', async () => {
    const { component } = await setUp();

    expect(component.skillRoute({ skill: 'writing', day: '2026-07-29' } as any)).toEqual([
      '/writing',
    ]);
    expect(component.skillRoute({ skill: 'speaking', day: '2026-07-29' } as any)).toEqual([
      '/speaking',
    ]);
  });

  it('offers a standalone link to Speaking practice outside the daily skill grid', async () => {
    const { fixture, component } = await setUp();
    await component.ngOnInit();
    fixture.detectChanges();

    const link = fixture.nativeElement.querySelector(
      '[data-testid="speaking-practice-link"]',
    );
    expect(link).not.toBeNull();
    expect(component.skillOrder).not.toContain('speaking');
  });

  it('labels a done Writing entry as retryable, other done skills as review-only', async () => {
    const { component } = await setUp();

    expect(component.doneActionLabel({ skill: 'writing' } as any)).toBe('Try again');
    expect(component.doneActionLabel({ skill: 'reading' } as any)).toBe('Review');
    expect(component.doneActionLabel({ skill: 'listening' } as any)).toBe('Review');
  });

  it('retries a failed skill', async () => {
    const { component, repository } = await setUp({
      getOverview: jasmine.createSpy().and.resolveTo({
        skills: [
          { day: today, skill: 'speaking', status: 'failed', focusReference: null },
        ],
      }) as any,
      retry: jasmine.createSpy().and.resolveTo(
        { day: today, skill: 'speaking', status: 'ready', focusReference: null },
      ) as any,
    });
    await component.ngOnInit();

    await component.retry('speaking', today);

    expect(repository.retry).toHaveBeenCalledWith('speaking', today);
  });

  it('reveals and assesses a vocabulary word inside the daily lesson', async () => {
    const { component, vocabularyRepository } = await setUp();
    vocabularyRepository.startOrResumeReview.and.resolveTo({
      status: 'item',
      item: {
        sessionId: 'session-1',
        itemId: 'item-1',
        wordId: 'word-1',
        word: 'mitigate',
        meaning: 'make something less severe',
        example: 'Green spaces can mitigate air pollution.',
        position: 0,
        total: 1,
        isNew: true,
      },
    });
    vocabularyRepository.assessCurrentItem.and.resolveTo({
      status: 'complete',
      summary: {
        sessionId: 'session-1',
        totalReviewed: 1,
        forgot: 0,
        remembered: 1,
        newWordsIncluded: 0,
        reviewDatesUpdated: true,
      },
    });

    await component.ngOnInit();
    expect((component.vocabulary.reviewState() as any).item.isNew).toBeTrue();
    component.revealVocabulary();
    await component.assessVocabulary('remembered');

    expect(vocabularyRepository.assessCurrentItem).toHaveBeenCalledWith('remembered');
    expect(component.vocabularyRevealed()).toBeFalse();
  });
});
