import { Location } from '@angular/common';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { PracticeResultRepository } from '../../data/practice-result.repository';
import { LogPracticeResultComponent } from './log-practice-result.component';

describe('LogPracticeResultComponent', () => {
  it('gates required fields, preserves a failed draft, retries, and confirms', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['create', 'getTaxonomy'],
    );
    repository.getTaxonomy.and.resolveTo({
      Reading: [{ key: 'matching_headings', label: 'Matching Headings' }],
      Listening: [],
    });
    repository.create.and.rejectWith(new Error('offline'));
    await TestBed.configureTestingModule({
      imports: [LogPracticeResultComponent],
      providers: [
        provideRouter([]),
        { provide: PracticeResultRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(LogPracticeResultComponent);
    fixture.detectChanges();
    await fixture.whenStable();
    const component = fixture.componentInstance;
    expect(component.canSave).toBeFalse();

    component.source = 'Cambridge 18';
    component.score = 32;
    component.timeTakenMinutes = 60;
    component.toggleMissedType('matching_headings', true);
    expect(component.canSave).toBeTrue();
    await component.save();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="save-error"]'))
      .not.toBeNull();
    expect(component.source).toBe('Cambridge 18');

    repository.create.and.resolveTo({
      id: 'r1',
      skill: 'Reading',
      source: 'Cambridge 18',
      score: 32,
      total: 40,
      timeTakenSeconds: 3600,
      missedQuestionTypes: ['matching_headings'],
      loggedAt: '2026-07-29T10:00:00Z',
    });
    await component.retry();
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('[data-testid="confirmation"]').textContent)
      .toContain('Reading');
    expect(fixture.nativeElement.querySelector('form')).toBeNull();

    component.logAnother();
    expect(component.source).toBe('');
  });

  it('cancels without saving', async () => {
    const repository = jasmine.createSpyObj<PracticeResultRepository>(
      'PracticeResultRepository', ['create', 'getTaxonomy'],
    );
    repository.getTaxonomy.and.resolveTo({ Reading: [], Listening: [] });
    const location = jasmine.createSpyObj<Location>('Location', ['back']);
    await TestBed.configureTestingModule({
      imports: [LogPracticeResultComponent],
      providers: [
        provideRouter([]),
        { provide: PracticeResultRepository, useValue: repository },
        { provide: Location, useValue: location },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(LogPracticeResultComponent);
    fixture.detectChanges();
    fixture.componentInstance.source = 'Unsaved';
    fixture.componentInstance.cancel();
    expect(repository.create).not.toHaveBeenCalled();
    expect(location.back).toHaveBeenCalled();
  });
});
