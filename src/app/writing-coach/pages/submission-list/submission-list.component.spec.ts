import { signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { WritingCoachFacade } from '../../state/writing-coach.facade';
import { WritingSubmissionListComponent } from './submission-list.component';

describe('WritingSubmissionListComponent', () => {
  it('renders task, date, score detail, and a distinct failed entry', async () => {
    const facade = {
      listState: signal('ready'),
      submissions: signal([
        {
          id: 'w1',
          createdAt: '2026-07-29T10:00:00Z',
          taskType: 'task2',
          status: 'complete',
          overallBand: 7,
          taskResponseScore: 7,
          questionExcerpt: 'Discuss both views.',
        },
        {
          id: 'w2',
          createdAt: '2026-07-28T10:00:00Z',
          taskType: 'task1',
          status: 'failed',
          overallBand: null,
          taskResponseScore: null,
          questionExcerpt: 'Describe the chart.',
        },
      ]),
      loadSubmissions: jasmine.createSpy('loadSubmissions').and.resolveTo(undefined),
    };
    await TestBed.configureTestingModule({
      imports: [WritingSubmissionListComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachFacade, useValue: facade },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmissionListComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    const text = fixture.nativeElement.textContent;
    expect(text).toContain('Overall band 7');
    expect(text).toContain('Evaluation failed');
    expect(text).toContain('Discuss both views.');
  });

  it('distinguishes empty history from a loading failure', async () => {
    const listState = signal('ready');
    const facade = {
      listState,
      submissions: signal([]),
      loadSubmissions: jasmine.createSpy('loadSubmissions').and.resolveTo(undefined),
    };
    await TestBed.configureTestingModule({
      imports: [WritingSubmissionListComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachFacade, useValue: facade },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmissionListComponent);
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="writing-list-empty"]'))
      .not.toBeNull();
    listState.set('error');
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="writing-list-error"]'))
      .not.toBeNull();
  });
});
