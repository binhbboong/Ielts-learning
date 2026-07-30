import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { SpeakingCoachFacade } from '../../state/speaking-coach.facade';
import { SpeakingSubmissionDetailComponent } from './submission-detail.component';

describe('SpeakingSubmissionDetailComponent', () => {
  it('renders transcript, three criteria, and Pronunciation not assessed', async () => {
    const criterion = {
      bandScore: 7,
      feedback: 'Specific transcript feedback.',
      strengths: ['Clear idea'],
      weaknesses: ['Add linking phrases'],
    };
    const facade = {
      state: signal('ready'),
      current: signal({
        id: 's1',
        questionId: 'q1',
        question: 'Tell me about your home.',
        part: 'PART_1',
        audioDurationSeconds: 30,
        transcript: 'I live in a quiet town.',
        status: 'COMPLETED',
        fluencyAndCoherence: criterion,
        lexicalResource: criterion,
        grammaticalRangeAndAccuracy: criterion,
        pronunciation: 'Not assessed',
        errorMessage: null,
        createdAt: '2026-07-29T10:00:00Z',
      }),
      loadSubmission: jasmine.createSpy('loadSubmission').and.resolveTo(undefined),
      retryTranscription: jasmine.createSpy('retryTranscription'),
      retryEvaluation: jasmine.createSpy('retryEvaluation'),
    };
    await TestBed.configureTestingModule({
      imports: [SpeakingSubmissionDetailComponent],
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: {
          snapshot: { paramMap: { get: () => 's1' } },
        } },
        { provide: SpeakingCoachFacade, useValue: facade },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(SpeakingSubmissionDetailComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('I live in a quiet town.');
    expect(text).toContain('Fluency and Coherence');
    expect(text).toContain('Lexical Resource');
    expect(text).toContain('Grammar');
    expect(text).toContain('Not assessed');
  });

  it('shows distinct retry actions for each failure step', async () => {
    const status = signal('TRANSCRIPTION_FAILED');
    const current = signal<any>({
      id: 's1', question: 'Prompt', part: 'PART_1', transcript: null,
      status: status(), fluencyAndCoherence: null, lexicalResource: null,
      grammaticalRangeAndAccuracy: null,
    });
    const facade = {
      state: signal('ready'),
      current,
      loadSubmission: jasmine.createSpy('loadSubmission').and.resolveTo(undefined),
      retryTranscription: jasmine.createSpy('retryTranscription').and.resolveTo(undefined),
      retryEvaluation: jasmine.createSpy('retryEvaluation').and.resolveTo(undefined),
    };
    await TestBed.configureTestingModule({
      imports: [SpeakingSubmissionDetailComponent],
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: {
          snapshot: { paramMap: { get: () => 's1' } },
        } },
        { provide: SpeakingCoachFacade, useValue: facade },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(SpeakingSubmissionDetailComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Retry transcription');
    current.set({ ...current(), status: 'EVALUATION_FAILED', transcript: 'Captured.' });
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Retry evaluation');
  });
});
