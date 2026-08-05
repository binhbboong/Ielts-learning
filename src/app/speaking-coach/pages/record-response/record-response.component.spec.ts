import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { DailyLessonRepository } from '../../../daily-lesson/data/daily-lesson.repository';
import { SpeakingCoachFacade } from '../../state/speaking-coach.facade';
import { SpeakingCoachRepository } from '../../data/speaking-coach.repository';
import { RecordResponseComponent } from './record-response.component';

function dailyLessonRepositoryStub(generatedPromptText: string | null = null) {
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
    skills: generatedPromptText
      ? [{
          day: '2026-07-30', skill: 'speaking', status: 'ready', focusReference: null,
          targetBand: 4.5, estimatedMinutes: 20, priority: 'primary', phase: 'foundation',
          rationale: 'Scheduled', generatedPromptText, taskType: null,
        }]
      : [],
  });
  return repository;
}

describe('RecordResponseComponent', () => {
  it('requires a question and recording before submit', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository', ['questions'],
    );
    repository.questions.and.resolveTo([]);
    await TestBed.configureTestingModule({
      imports: [RecordResponseComponent],
      providers: [
        provideRouter([]),
        { provide: SpeakingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepositoryStub() },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(RecordResponseComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance.canSubmit).toBeFalse();
    fixture.componentInstance.audio = new Blob(['audio']);
    fixture.componentInstance.elapsedSeconds = 10;
    expect(fixture.componentInstance.canSubmit).toBeFalse();
    fixture.componentInstance.selectedQuestionId = 'q1';
    expect(fixture.componentInstance.canSubmit).toBeTrue();
  });

  it('stops and warns at the 120-second cap', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository', ['questions'],
    );
    repository.questions.and.resolveTo([]);
    await TestBed.configureTestingModule({
      imports: [RecordResponseComponent],
      providers: [
        provideRouter([]),
        { provide: SpeakingCoachRepository, useValue: repository },
        { provide: DailyLessonRepository, useValue: dailyLessonRepositoryStub() },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(RecordResponseComponent);
    const component = fixture.componentInstance;
    const stop = spyOn(component, 'stopRecording');
    component.elapsedSeconds = 119;
    component.advanceRecordingClock();
    expect(stop).toHaveBeenCalled();
    expect(component.recordingError).toContain('120-second limit');
  });

  it('defaults to the daily-generated prompt when one exists and submits by prompt text + day', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository', ['questions'],
    );
    repository.questions.and.resolveTo([]);
    const facade = jasmine.createSpyObj<SpeakingCoachFacade>(
      'SpeakingCoachFacade', ['loadQuestions', 'submit'],
      { questions: () => [] } as any,
    );
    facade.loadQuestions.and.resolveTo(undefined);
    facade.submit.and.resolveTo(undefined);
    await TestBed.configureTestingModule({
      imports: [RecordResponseComponent],
      providers: [
        provideRouter([]),
        { provide: SpeakingCoachRepository, useValue: repository },
        { provide: SpeakingCoachFacade, useValue: facade },
        {
          provide: DailyLessonRepository,
          useValue: dailyLessonRepositoryStub('Tell me about your hometown.'),
        },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(RecordResponseComponent);
    const component = fixture.componentInstance;

    await component.ngOnInit();

    expect(component.promptSource).toBe('daily');
    expect(component.dailyPromptText).toBe('Tell me about your hometown.');
    component.audio = new Blob(['audio']);
    component.elapsedSeconds = 10;
    expect(component.canSubmit).toBeTrue();

    await component.submit();

    expect(facade.submit).toHaveBeenCalledWith(
      { promptText: 'Tell me about your hometown.', day: '2026-07-30' },
      component.audio,
      10,
    );
  });
});
