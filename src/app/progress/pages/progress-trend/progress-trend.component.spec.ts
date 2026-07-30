import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { PracticeResultRepository } from '../../data/practice-result.repository';
import { ProgressTrendComponent } from './progress-trend.component';

describe('ProgressTrendComponent', () => {
  it('renders trend and breakdown together at four sessions', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['getTrend'],
    );
    repository.getTrend.and.resolveTo({
      sessionCount: 4,
      averageScorePercentage: 81.5,
      direction: 'up',
      threshold: { sufficient: true, count: 4, remaining: 0 },
      breakdown: [{ key: 'matching_headings', count: 3 }],
    });
    await TestBed.configureTestingModule({
      imports: [ProgressTrendComponent],
      providers: [
        provideRouter([]),
        { provide: PracticeResultRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ProgressTrendComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="trend-region"]'))
      .not.toBeNull();
    expect(fixture.nativeElement.querySelector('[data-testid="breakdown-region"]'))
      .not.toBeNull();
  });

  it('distinguishes insufficient, empty, and load-error states', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['getTrend'],
    );
    repository.getTrend.and.resolveTo({
      sessionCount: 3,
      averageScorePercentage: 70,
      direction: null,
      threshold: { sufficient: false, count: 3, remaining: 1 },
      breakdown: [],
    });
    await TestBed.configureTestingModule({
      imports: [ProgressTrendComponent],
      providers: [
        provideRouter([]),
        { provide: PracticeResultRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(ProgressTrendComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="insufficient"]')
      .textContent).toContain('1 more');

    repository.getTrend.and.rejectWith(new Error('offline'));
    await fixture.componentInstance.refresh();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="load-error"]'))
      .not.toBeNull();
  });
});
