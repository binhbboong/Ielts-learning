import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { DayHistoryComponent } from './day-history.component';
import { StudyPlanFacade } from '../../state/study-plan.facade';
import { Task } from '../../models/task.model';

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 1,
    dayNumber: 1,
    skill: 'Grammar',
    title: 'Grammar practice',
    description: 'desc',
    estimatedMinutes: 20,
    status: 'NotStarted',
    note: '',
    updatedAt: '',
    ...overrides,
  };
}

describe('DayHistoryComponent', () => {
  let fixture: ComponentFixture<DayHistoryComponent>;
  let facadeStub: {
    currentDayNumber: ReturnType<typeof signal<number>>;
    getHistoryForDay: jasmine.Spy;
  };

  beforeEach(async () => {
    facadeStub = {
      currentDayNumber: signal(4),
      getHistoryForDay: jasmine.createSpy('getHistoryForDay').and.resolveTo([
        makeTask({ id: 1, dayNumber: 2, skill: 'Grammar', status: 'Completed' }),
        makeTask({ id: 2, dayNumber: 2, skill: 'Vocabulary', status: 'Skipped' }),
      ]),
    };

    await TestBed.configureTestingModule({
      imports: [DayHistoryComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();

    fixture = TestBed.createComponent(DayHistoryComponent);
    fixture.detectChanges();
  });

  it('renders a day selector for every past day (before the current day)', () => {
    const dayButtons = fixture.nativeElement.querySelectorAll('[data-testid^="select-day-"]');
    expect(dayButtons.length).toBe(3); // days 1, 2, 3 (current day is 4)
  });

  it("renders the selected past day's tasks with their final statuses, read-only", async () => {
    const dayTwoButton = fixture.nativeElement.querySelector(
      '[data-testid="select-day-2"]',
    ) as HTMLButtonElement;
    dayTwoButton.click();
    await fixture.whenStable();
    fixture.detectChanges();

    expect(facadeStub.getHistoryForDay).toHaveBeenCalledWith(2);
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Grammar');
    expect(text).toContain('Completed');
    expect(text).toContain('Vocabulary');
    expect(text).toContain('Skipped');

    // Strictly read-only: no mutation controls anywhere in the rendered output.
    expect(fixture.nativeElement.querySelector('button[data-testid^="status-"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('button[data-testid^="complete-"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('button[data-testid^="skip-"]')).toBeNull();
    expect(fixture.nativeElement.querySelector('textarea')).toBeNull();
    expect(fixture.nativeElement.querySelector('input')).toBeNull();
  });
});
