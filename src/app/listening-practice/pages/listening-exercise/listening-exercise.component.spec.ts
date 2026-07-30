import { ActivatedRoute } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ListeningPracticeRepository } from '../../data/listening-practice.repository';
import { ListeningExerciseComponent } from './listening-exercise.component';

const exercise = {
  day: '2026-07-30', status: 'ready',
  focusReference: "the word 'nevertheless'", scriptText: null,
  questions: [
    { id: 'q1', questionText: 'What is discussed?', options: ['A', 'B', 'C', 'D'], order: 1 },
  ],
};

async function setUp(
  repositoryOverrides: Partial<jasmine.SpyObj<ListeningPracticeRepository>> = {},
  day: string | null = '2026-07-30',
) {
  const repository = jasmine.createSpyObj<ListeningPracticeRepository>(
    'ListeningPracticeRepository',
    ['get', 'submit', 'retryScript', 'retryAudio', 'audioUrl'],
  );
  repository.get.and.resolveTo(exercise);
  repository.audioUrl.and.callFake((day: string) => `/api/listening-practice/${day}/audio`);
  Object.assign(repository, repositoryOverrides);

  await TestBed.configureTestingModule({
    imports: [ListeningExerciseComponent],
    providers: [
      provideRouter([]),
      { provide: ListeningPracticeRepository, useValue: repository },
      {
        provide: ActivatedRoute,
        useValue: { snapshot: { paramMap: { get: () => day } } },
      },
    ],
  }).compileComponents();
  const fixture = TestBed.createComponent(ListeningExerciseComponent);
  return { fixture, component: fixture.componentInstance, repository };
}

describe('ListeningExerciseComponent', () => {
  it('loads the exercise for the route day and builds the audio URL', async () => {
    const { component, repository } = await setUp();
    await component.ngOnInit();
    expect(repository.get).toHaveBeenCalledWith('2026-07-30');
    expect(component.audioUrl).toBe('/api/listening-practice/2026-07-30/audio');
  });

  it('does not allow submit until every question is answered', async () => {
    const { component } = await setUp();
    await component.ngOnInit();
    expect(component.canSubmit).toBeFalse();
    component.selectAnswer(0, 1);
    expect(component.canSubmit).toBeTrue();
  });

  it('submits selected answers', async () => {
    const { component, repository } = await setUp();
    repository.submit.and.resolveTo({
      day: '2026-07-30', score: 1, total: 1, scriptText: 'A script.',
      answers: [{
        questionText: 'What is discussed?', options: ['A', 'B', 'C', 'D'],
        learnerAnswerIndex: 1, correctOptionIndex: 1, correct: true,
      }],
    });
    await component.ngOnInit();
    component.selectAnswer(0, 1);

    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1]);
    expect(component.facade.result()?.scriptText).toBe('A script.');
  });

  it('retries the script when script generation failed', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo({ ...exercise, status: 'script_failed' });
    repository.retryScript.and.resolveTo(exercise);
    await component.ngOnInit();

    await component.retryScript();

    expect(repository.retryScript).toHaveBeenCalledWith('2026-07-30');
  });

  it('retries only the audio when audio generation failed', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo({ ...exercise, status: 'audio_failed' });
    repository.retryAudio.and.resolveTo(exercise);
    await component.ngOnInit();

    await component.retryAudio();

    expect(repository.retryAudio).toHaveBeenCalledWith('2026-07-30');
    expect(repository.retryScript).not.toHaveBeenCalled();
  });

  it('builds pre-filled quick-add data from a wrong answer with skill listening', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    const data = component.quickAddData({
      questionText: 'What is discussed?', options: ['A', 'B', 'C', 'D'],
      learnerAnswerIndex: 0, correctOptionIndex: 2, correct: false,
    });

    expect(data.skill).toBe('listening');
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
