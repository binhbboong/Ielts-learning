import { ActivatedRoute } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ReadingPracticeRepository } from '../../data/reading-practice.repository';
import { ReadingExerciseComponent } from './reading-exercise.component';

const exercise = {
  day: '2026-07-30', status: 'ready' as const,
  focusReference: "the word 'nevertheless'",
  phase: 'foundation', targetMinutes: 20,
  passages: [
    {
      id: 'p1', title: null, passageText: 'A passage about nevertheless.', order: 1,
      questions: [
        {
          id: 'q1', questionText: 'What is discussed?', questionType: 'multiple_choice',
          options: ['A', 'B', 'C', 'D'], groupInstructions: null, order: 1,
        },
      ],
    },
  ],
};

const twoPassageExercise = {
  ...exercise,
  passages: [
    exercise.passages[0],
    {
      id: 'p2', title: 'Passage 2', passageText: 'Second passage.', order: 2,
      questions: [
        {
          id: 'q2', questionText: 'Complete the summary: the delay was caused by ___.',
          questionType: 'summary_completion', options: null,
          groupInstructions: 'Complete the summary below.', order: 1,
        },
      ],
    },
  ],
};

async function setUp(
  repositoryOverrides: Partial<jasmine.SpyObj<ReadingPracticeRepository>> = {},
  day: string | null = '2026-07-30',
) {
  const repository = jasmine.createSpyObj<ReadingPracticeRepository>(
    'ReadingPracticeRepository', ['get', 'submit', 'retry'],
  );
  repository.get.and.resolveTo(exercise);
  Object.assign(repository, repositoryOverrides);

  await TestBed.configureTestingModule({
    imports: [ReadingExerciseComponent],
    providers: [
      provideRouter([]),
      { provide: ReadingPracticeRepository, useValue: repository },
      {
        provide: ActivatedRoute,
        useValue: { snapshot: { paramMap: { get: () => day } } },
      },
    ],
  }).compileComponents();
  const fixture = TestBed.createComponent(ReadingExerciseComponent);
  return { fixture, component: fixture.componentInstance, repository };
}

describe('ReadingExerciseComponent', () => {
  it('loads the exercise for the route day on init', async () => {
    const { fixture, repository } = await setUp();
    await fixture.componentInstance.ngOnInit();
    expect(repository.get).toHaveBeenCalledWith('2026-07-30');
  });

  it('defaults to today when no day route param is present', async () => {
    const { fixture, repository } = await setUp({}, null);
    await fixture.componentInstance.ngOnInit();
    const isoDatePattern = /^\d{4}-\d{2}-\d{2}$/;
    expect(repository.get).toHaveBeenCalledWith(jasmine.stringMatching(isoDatePattern));
  });

  it('does not allow submit until every question is answered', async () => {
    const { component } = await setUp();
    await component.ngOnInit();
    expect(component.canSubmit).toBeFalse();
    component.selectAnswer(0, 1);
    expect(component.canSubmit).toBeTrue();
  });

  it('flattens questions across passages in passage/question order', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo(twoPassageExercise);
    await component.ngOnInit();

    expect(component.flatQuestions.map((q) => q.id)).toEqual(['q1', 'q2']);
    expect(component.passageSections.length).toBe(2);
    expect(component.passageSections[1].questions[0].flatIndex).toBe(1);
  });

  it('does not allow submit until a text-based question has a non-blank answer', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo(twoPassageExercise);
    await component.ngOnInit();
    component.selectAnswer(0, 1);
    expect(component.canSubmit).toBeFalse();

    component.setTextAnswer(1, '   ');
    expect(component.canSubmit).toBeFalse();

    component.setTextAnswer(1, 'funding');
    expect(component.canSubmit).toBeTrue();
  });

  it('submits selected answers and shows the result', async () => {
    const { component, repository } = await setUp({
      submit: jasmine.createSpy().and.resolveTo(undefined) as any,
    });
    repository.submit.and.resolveTo({
      day: '2026-07-30', score: 1, total: 1,
      answers: [{
        questionText: 'What is discussed?', questionType: 'multiple_choice',
        options: ['A', 'B', 'C', 'D'], learnerAnswer: 1, correctAnswer: 1, correct: true,
      }],
    });
    await component.ngOnInit();
    component.selectAnswer(0, 1);

    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1]);
    expect(component.facade.result()?.score).toBe(1);
  });

  it('submits a mix of option indexes and free text answers', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo(twoPassageExercise);
    repository.submit.and.resolveTo({ day: '2026-07-30', score: 2, total: 2, answers: [] });
    await component.ngOnInit();
    component.selectAnswer(0, 1);
    component.setTextAnswer(1, 'funding');

    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1, 'funding']);
  });

  it('retries generation when the exercise failed', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo({ ...exercise, status: 'failed', passages: [] });
    repository.retry.and.resolveTo(exercise);
    await component.ngOnInit();

    await component.retry();

    expect(repository.retry).toHaveBeenCalledWith('2026-07-30');
  });

  it('builds pre-filled quick-add data from a wrong option-based answer with no re-entry needed', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    const data = component.quickAddData({
      questionText: 'What is discussed?', questionType: 'multiple_choice',
      options: ['A', 'B', 'C', 'D'], learnerAnswer: 0, correctAnswer: 2, correct: false,
    });

    expect(data.skill).toBe('reading');
    expect(data.ownAnswer).toBe('A');
    expect(data.correctAnswer).toBe('C');
    expect(data.source).toContain('What is discussed?');
  });

  it('builds pre-filled quick-add data from a wrong text-based answer', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    const data = component.quickAddData({
      questionText: 'Complete the summary.', questionType: 'summary_completion',
      options: null, learnerAnswer: 'staffing', correctAnswer: 'funding', correct: false,
    });

    expect(data.ownAnswer).toBe('staffing');
    expect(data.correctAnswer).toBe('funding');
  });

  it('shows no countdown timer at beginner tier', async () => {
    const { fixture, component } = await setUp();

    // Let Angular's own lifecycle drive ngOnInit exactly once (calling it
    // manually too, as other tests in this file do for direct property
    // assertions, would trigger a second unawaited load on detectChanges and
    // leave exerciseState back at 'loading' when the DOM is inspected).
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.showTimer).toBeFalse();
    expect(
      fixture.nativeElement.querySelector('app-countdown-timer'),
    ).toBeNull();
  });

  it('shows a countdown timer at standard/advanced tier', async () => {
    const { fixture, component, repository } = await setUp();
    repository.get.and.resolveTo({ ...exercise, phase: 'consolidation', targetMinutes: 38 });

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.showTimer).toBeTrue();
    expect(
      fixture.nativeElement.querySelector('app-countdown-timer'),
    ).not.toBeNull();
  });

  it('toggles the quick-add panel open and closed per question', async () => {
    const { component } = await setUp();
    await component.ngOnInit();
    expect(component.openQuickAddIndex).toBeNull();

    component.openQuickAdd(0);
    expect(component.openQuickAddIndex).toBe(0);

    component.closeQuickAdd();
    expect(component.openQuickAddIndex).toBeNull();
  });
});
