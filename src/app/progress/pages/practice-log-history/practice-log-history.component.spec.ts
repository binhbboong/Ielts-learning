import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { PracticeResultRepository } from '../../data/practice-result.repository';
import { PracticeLogHistoryComponent } from './practice-log-history.component';

describe('PracticeLogHistoryComponent', () => {
  it('renders full entries and refetches for filter and sort', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['getHistory'],
    );
    repository.getHistory.and.resolveTo([{
      id: 'r1',
      skill: 'Reading',
      source: 'Cambridge 18',
      score: 32,
      total: 40,
      timeTakenSeconds: 3600,
      missedQuestionTypes: ['matching_headings'],
      note: 'Review headings',
      loggedAt: '2026-07-29T10:00:00Z',
    }]);
    await TestBed.configureTestingModule({
      imports: [PracticeLogHistoryComponent],
      providers: [
        provideRouter([]),
        { provide: PracticeResultRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(PracticeLogHistoryComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="history-entry"]')
      .textContent).toContain('Cambridge 18');

    await fixture.componentInstance.setSkill('Reading');
    await fixture.componentInstance.setSort('oldest');
    expect(repository.getHistory.calls.allArgs()).toEqual([
      [undefined, 'newest'],
      ['Reading', 'newest'],
      ['Reading', 'oldest'],
    ]);
  });

  it('distinguishes empty from load failure', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['getHistory'],
    );
    repository.getHistory.and.resolveTo([]);
    await TestBed.configureTestingModule({
      imports: [PracticeLogHistoryComponent],
      providers: [
        provideRouter([]),
        { provide: PracticeResultRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(PracticeLogHistoryComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="history-empty"]'))
      .not.toBeNull();

    repository.getHistory.and.rejectWith(new Error('offline'));
    await fixture.componentInstance.refresh();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="history-error"]'))
      .not.toBeNull();
  });
});
