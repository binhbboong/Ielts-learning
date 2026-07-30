import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { WritingCoachFacade } from '../../state/writing-coach.facade';
import { WritingSubmissionDetailComponent } from './submission-detail.component';

describe('WritingSubmissionDetailComponent', () => {
  it('renders all four criteria and sentence corrections unchanged', async () => {
    const criterion = {
      bandScore: 7,
      feedback: 'Specific feedback.',
      strengths: ['Clear idea'],
      weaknesses: ['Develop evidence'],
    };
    const facade = {
      detailState: signal('ready'),
      current: signal({
        id: 'w1',
        createdAt: '2026-07-29T10:00:00Z',
        taskType: 'task2',
        questionText: 'Discuss both views.',
        responseText: 'People is affected.',
        status: 'complete',
        taskResponse: criterion,
        coherenceAndCohesion: criterion,
        lexicalResource: criterion,
        grammaticalRangeAndAccuracy: criterion,
        overallBand: 7,
        corrections: [{
          original: 'People is affected.',
          corrected: 'People are affected.',
          explanation: 'Plural agreement.',
        }],
        errorMessage: null,
      }),
      loadSubmission: jasmine.createSpy('loadSubmission').and.resolveTo(undefined),
    };
    await TestBed.configureTestingModule({
      imports: [WritingSubmissionDetailComponent],
      providers: [
        provideRouter([]),
        { provide: ActivatedRoute, useValue: {
          snapshot: { paramMap: { get: () => 'w1' } },
        } },
        { provide: WritingCoachFacade, useValue: facade },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmissionDetailComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Task Response / Achievement');
    expect(text).toContain('Coherence and Cohesion');
    expect(text).toContain('Lexical Resource');
    expect(text).toContain('Grammatical Range and Accuracy');
    expect(text).toContain('People are affected.');
  });
});
