import { Location } from '@angular/common';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DailyLessonRepository } from '../../../daily-lesson/data/daily-lesson.repository';
import { WritingCoachRepository } from '../../data/writing-coach.repository';
import { WritingSubmitComponent } from './submit.component';

function dailyLessonRepositoryStub() {
  const repository = jasmine.createSpyObj<DailyLessonRepository>(
    'DailyLessonRepository', ['getOverview', 'retry'],
  );
  repository.getOverview.and.resolveTo({
    examType: 'ielts_academic', week: 1, phase: 'foundation', targetBand: 4.5,
    totalMinutes: 60, reviewMinutes: 10, effectiveDay: '2026-07-30',
    checkpoint: {
      day: '2026-07-30',
      skills: { reading: false, listening: false, writing: false, speaking: false },
      vocabularyQuiz: false, passedCount: 0, requiredCount: 5, allPassed: false,
    },
    skills: [],
  });
  return repository;
}

describe('WritingSubmitComponent', () => {
  it('blocks blank input, preserves failed text, and retries', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    repository.submit.and.rejectWith(new Error('offline'));
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepositoryStub() },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    const component = fixture.componentInstance;
    expect(component.canSubmit).toBeFalse();
    component.questionText = 'Discuss both views.';
    component.responseText = 'My complete response.';
    await component.submit();
    fixture.detectChanges();
    expect(component.responseText).toBe('My complete response.');
    expect(fixture.nativeElement.querySelector('[data-testid="writing-error"]'))
      .not.toBeNull();
    expect(repository.submit).toHaveBeenCalledTimes(1);
  });

  it('abandons without submitting', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    const location = jasmine.createSpyObj<Location>('Location', ['back']);
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: Location, useValue: location },
        { provide: DailyLessonRepository, useValue: dailyLessonRepositoryStub() },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    fixture.componentInstance.cancel();
    expect(repository.submit).not.toHaveBeenCalled();
    expect(location.back).toHaveBeenCalled();
  });

  it('pre-fills the question from the daily-generated writing prompt and submits with its day', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    const dailyLessonRepository = dailyLessonRepositoryStub();
    dailyLessonRepository.getOverview.and.resolveTo({
      examType: 'ielts_academic', week: 1, phase: 'foundation', targetBand: 4.5,
      totalMinutes: 60, reviewMinutes: 10, effectiveDay: '2026-07-30',
      checkpoint: {
        day: '2026-07-30',
        skills: { reading: false, listening: false, writing: false, speaking: false },
        vocabularyQuiz: false, passedCount: 0, requiredCount: 5, allPassed: false,
      },
      skills: [
        {
          day: '2026-07-30', skill: 'writing', status: 'ready', focusReference: null,
          targetBand: 4.5, estimatedMinutes: 20, priority: 'primary', phase: 'foundation',
          rationale: 'Scheduled', generatedPromptText: 'Describe your daily routine.',
          taskType: null,
        },
      ],
    });
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    const component = fixture.componentInstance;

    await component.ngOnInit();

    expect(component.questionText).toBe('Describe your daily routine.');
    expect(component.promptDay).toBe('2026-07-30');
    expect(component.promptTargetBand).toBe(4.5);
    expect(component.promptPhase).toBe('foundation');

    component.responseText = 'My response.';
    await component.submit();

    expect(repository.submit).toHaveBeenCalledWith(jasmine.objectContaining({
      questionText: 'Describe your daily routine.',
      day: '2026-07-30',
    }));
  });

  it('pre-fills task type from the daily-generated prompt (Task 1, not the default Task 2)', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    const dailyLessonRepository = dailyLessonRepositoryStub();
    dailyLessonRepository.getOverview.and.resolveTo({
      examType: 'ielts_academic', week: 5, phase: 'consolidation', targetBand: 6.0,
      totalMinutes: 60, reviewMinutes: 10, effectiveDay: '2026-07-31',
      checkpoint: {
        day: '2026-07-31',
        skills: { reading: false, listening: false, writing: false, speaking: false },
        vocabularyQuiz: false, passedCount: 0, requiredCount: 4, allPassed: false,
      },
      skills: [
        {
          day: '2026-07-31', skill: 'writing', status: 'ready', focusReference: null,
          targetBand: 6.0, estimatedMinutes: 38, priority: 'primary', phase: 'consolidation',
          rationale: 'Scheduled', generatedPromptText: 'Describe the chart below.',
          taskType: 'task1',
        },
      ],
    });
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    const component = fixture.componentInstance;

    await component.ngOnInit();

    expect(component.taskType).toBe('task1');
  });

  it('shows the latest same-day attempt instead of a blank form, until asked to write again', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit', 'list'],
    );
    repository.list.and.resolveTo([
      {
        id: 'w1', createdAt: '2026-07-30T09:00:00Z', taskType: 'task2', status: 'complete',
        overallBand: 6, taskResponseScore: 6, questionExcerpt: 'Describe your daily routine.',
      },
    ]);
    const dailyLessonRepository = dailyLessonRepositoryStub();
    dailyLessonRepository.getOverview.and.resolveTo({
      examType: 'ielts_academic', week: 1, phase: 'foundation', targetBand: 4.5,
      totalMinutes: 60, reviewMinutes: 10, effectiveDay: '2026-07-30',
      checkpoint: {
        day: '2026-07-30',
        skills: { reading: false, listening: false, writing: false, speaking: false },
        vocabularyQuiz: false, passedCount: 0, requiredCount: 5, allPassed: false,
      },
      skills: [
        {
          day: '2026-07-30', skill: 'writing', status: 'done', focusReference: null,
          targetBand: 4.5, estimatedMinutes: 20, priority: 'primary', phase: 'foundation',
          rationale: 'Scheduled', generatedPromptText: 'Describe your daily routine.',
          taskType: null,
        },
      ],
    });
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    const component = fixture.componentInstance;

    await component.ngOnInit();
    fixture.detectChanges();

    expect(repository.list).toHaveBeenCalledWith('2026-07-30');
    expect(component.facade.latestForDay()?.overallBand).toBe(6);
    expect(
      fixture.nativeElement.querySelector('[data-testid="writing-latest-attempt"]'),
    ).not.toBeNull();

    component.writeAgain();
    fixture.detectChanges();

    expect(component.writingAgain()).toBeTrue();
    expect(fixture.nativeElement.querySelector('textarea[name="responseText"]')).not.toBeNull();
  });

  it('shows foundation targets, hides IELTS task choice, and requires the minimum', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    const dailyLessonRepository = dailyLessonRepositoryStub();
    dailyLessonRepository.getOverview.and.resolveTo({
      examType: 'ielts_academic', week: 1, phase: 'foundation', targetBand: 4.5,
      totalMinutes: 60, reviewMinutes: 10, effectiveDay: '2026-07-30',
      checkpoint: {
        day: '2026-07-30',
        skills: { reading: false, listening: false, writing: false, speaking: false },
        vocabularyQuiz: false, passedCount: 0, requiredCount: 4, allPassed: false,
      },
      skills: [{
        day: '2026-07-30', skill: 'writing', status: 'ready', focusReference: null,
        targetBand: 4.5, estimatedMinutes: 20, priority: 'primary', phase: 'foundation',
        rationale: 'Scheduled', generatedPromptText: 'Write about your favourite activity.',
        taskType: null, writingLevel: 1, exerciseType: 'sentence_building',
        exerciseLabel: 'Sentence foundations',
        objective: 'Write a few clear sentences.', minSentences: 1, maxSentences: 3,
        minWords: 8, maxWords: 40, sentenceFrames: ['I like ... because ...'],
        showIeltsBand: false,
      }],
    });
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    const component = fixture.componentInstance;

    await component.ngOnInit();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('[data-testid="writing-level-card"]')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('select[name="taskType"]')).toBeNull();
    component.responseText = 'I like reading.';
    expect(component.canSubmit).toBeFalse();
    component.responseText = 'I like reading because it helps me relax every evening.';
    expect(component.sentenceCount).toBe(1);
    expect(component.wordCount).toBe(10);
    expect(component.canSubmit).toBeTrue();
  });
});
