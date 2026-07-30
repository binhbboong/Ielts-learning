import { ActivatedRoute } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ReadingPracticeRepository } from '../../data/reading-practice.repository';
import { ReadingExerciseComponent } from './reading-exercise.component';

const exercise = {
  day: '2026-07-30', status: 'ready' as const,
  focusReference: "the word 'nevertheless'", passageText: 'A passage about nevertheless.',
  questions: [
    { id: 'q1', questionText: 'What is discussed?', options: ['A', 'B', 'C', 'D'], order: 1 },
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

  it('submits selected answers and shows the result', async () => {
    const { component, repository } = await setUp({
      submit: jasmine.createSpy().and.resolveTo(undefined) as any,
    });
    repository.submit.and.resolveTo({
      day: '2026-07-30', score: 1, total: 1,
      answers: [{
        questionText: 'What is discussed?', options: ['A', 'B', 'C', 'D'],
        learnerAnswerIndex: 1, correctOptionIndex: 1, correct: true,
      }],
    });
    await component.ngOnInit();
    component.selectAnswer(0, 1);

    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1]);
    expect(component.facade.result()?.score).toBe(1);
  });

  it('retries generation when the exercise failed', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo({ ...exercise, status: 'failed', passageText: null });
    repository.retry.and.resolveTo(exercise);
    await component.ngOnInit();

    await component.retry();

    expect(repository.retry).toHaveBeenCalledWith('2026-07-30');
  });

  it('builds pre-filled quick-add data from a wrong answer with no re-entry needed', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    const data = component.quickAddData({
      questionText: 'What is discussed?', options: ['A', 'B', 'C', 'D'],
      learnerAnswerIndex: 0, correctOptionIndex: 2, correct: false,
    });

    expect(data.skill).toBe('reading');
    expect(data.ownAnswer).toBe('A');
    expect(data.correctAnswer).toBe('C');
    expect(data.source).toContain('What is discussed?');
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
