import { ActivatedRoute } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ListeningPracticeRepository } from '../../data/listening-practice.repository';
import { ListeningExerciseComponent } from './listening-exercise.component';

const exercise = {
  day: '2026-07-30', status: 'ready',
  focusReference: "the word 'nevertheless'",
  phase: 'foundation', targetMinutes: 20,
  sections: [
    {
      id: 's1', contextType: 'monologue', scriptText: null, order: 1,
      questions: [
        {
          id: 'q1', questionText: 'What is discussed?', questionType: 'multiple_choice',
          options: ['A', 'B', 'C', 'D'], groupInstructions: null, order: 1,
        },
      ],
    },
  ],
};

const twoSectionExercise = {
  ...exercise,
  sections: [
    exercise.sections[0],
    {
      id: 's2', contextType: 'social_conversation', scriptText: null, order: 2,
      questions: [
        {
          id: 'q2', questionText: 'Complete the note: the team missed the ___ deadline.',
          questionType: 'note_completion', options: null,
          groupInstructions: null, order: 1,
        },
      ],
    },
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
  repository.audioUrl.and.callFake(
    (day: string, order: number) => `/api/listening-practice/${day}/audio/${order}`,
  );
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
  it('loads the exercise for the route day and builds the audio URL per section', async () => {
    const { component, repository } = await setUp();
    await component.ngOnInit();
    expect(repository.get).toHaveBeenCalledWith('2026-07-30');
    expect(component.audioUrl(1)).toBe('/api/listening-practice/2026-07-30/audio/1');
  });

  it('does not allow submit until every question is answered', async () => {
    const { component } = await setUp();
    await component.ngOnInit();
    expect(component.canSubmit).toBeFalse();
    component.selectAnswer(0, 1);
    expect(component.canSubmit).toBeTrue();
  });

  it('flattens questions across sections in section/question order', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo(twoSectionExercise);
    await component.ngOnInit();

    expect(component.flatQuestions.map((q) => q.id)).toEqual(['q1', 'q2']);
    expect(component.sectionViews.length).toBe(2);
    expect(component.sectionViews[1].questions[0].flatIndex).toBe(1);
  });

  it('submits selected answers', async () => {
    const { component, repository } = await setUp();
    repository.submit.and.resolveTo({
      day: '2026-07-30', score: 1, total: 1,
      sections: [{ id: 's1', contextType: 'monologue', scriptText: 'A script.', order: 1, questions: [] }],
      answers: [{
        questionText: 'What is discussed?', questionType: 'multiple_choice',
        options: ['A', 'B', 'C', 'D'], learnerAnswer: 1, correctAnswer: 1, correct: true,
      }],
    });
    await component.ngOnInit();
    component.selectAnswer(0, 1);

    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1]);
    expect(component.facade.result()?.sections[0].scriptText).toBe('A script.');
  });

  it('does not allow submit until a text-based question has a non-blank answer', async () => {
    const { component, repository } = await setUp({}, '2026-07-30');
    repository.get.and.resolveTo(twoSectionExercise);
    await component.ngOnInit();
    component.selectAnswer(0, 1);
    expect(component.canSubmit).toBeFalse();

    component.setTextAnswer(1, '   ');
    expect(component.canSubmit).toBeFalse();

    component.setTextAnswer(1, 'funding');
    expect(component.canSubmit).toBeTrue();
  });

  it('submits a mix of option indexes and free text answers', async () => {
    const { component, repository } = await setUp();
    repository.get.and.resolveTo(twoSectionExercise);
    repository.submit.and.resolveTo({
      day: '2026-07-30', score: 2, total: 2, sections: [], answers: [],
    });
    await component.ngOnInit();
    component.selectAnswer(0, 1);
    component.setTextAnswer(1, 'funding');

    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith('2026-07-30', [1, 'funding']);
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

  it('builds pre-filled quick-add data from a wrong option-based answer with skill listening', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    const data = component.quickAddData({
      questionText: 'What is discussed?', questionType: 'multiple_choice',
      options: ['A', 'B', 'C', 'D'], learnerAnswer: 0, correctAnswer: 2, correct: false,
    });

    expect(data.skill).toBe('listening');
    expect(data.ownAnswer).toBe('A');
    expect(data.correctAnswer).toBe('C');
    expect(data.source).toContain('What is discussed?');
  });

  it('builds pre-filled quick-add data from a wrong text-based answer', async () => {
    const { component } = await setUp();
    await component.ngOnInit();

    const data = component.quickAddData({
      questionText: 'Complete the note.', questionType: 'note_completion', options: null,
      learnerAnswer: 'staffing', correctAnswer: 'funding', correct: false,
    });

    expect(data.ownAnswer).toBe('staffing');
    expect(data.correctAnswer).toBe('funding');
  });

  it('shows no countdown timer at beginner tier', async () => {
    const { fixture, component } = await setUp();

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.showTimer).toBeFalse();
    expect(fixture.nativeElement.querySelector('app-countdown-timer')).toBeNull();
  });

  it('shows a countdown timer at standard/advanced tier', async () => {
    const { fixture, component, repository } = await setUp();
    repository.get.and.resolveTo({ ...exercise, phase: 'development', targetMinutes: 38 });

    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(component.showTimer).toBeTrue();
    expect(fixture.nativeElement.querySelector('app-countdown-timer')).not.toBeNull();
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
