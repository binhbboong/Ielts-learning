import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { DailyChecklistComponent } from './daily-checklist.component';
import { StudyPlanFacade } from '../../state/study-plan.facade';
import { Task } from '../../models/task.model';

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 1,
    dayNumber: 3,
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

describe('DailyChecklistComponent', () => {
  let fixture: ComponentFixture<DailyChecklistComponent>;
  let facadeStub: {
    tasks: ReturnType<typeof signal<Task[]>>;
    currentDayNumber: ReturnType<typeof signal<number>>;
    loadCurrentDay: jasmine.Spy;
  };

  beforeEach(async () => {
    const tasks = signal<Task[]>([
      makeTask({ id: 1, skill: 'Grammar', status: 'Completed' }),
      makeTask({ id: 2, skill: 'Vocabulary', status: 'Skipped' }),
      makeTask({ id: 3, skill: 'Listening', status: 'NotStarted' }),
    ]);
    facadeStub = {
      tasks,
      currentDayNumber: signal(3),
      loadCurrentDay: jasmine.createSpy('loadCurrentDay').and.resolveTo(undefined),
    };

    await TestBed.configureTestingModule({
      imports: [DailyChecklistComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();

    fixture = TestBed.createComponent(DailyChecklistComponent);
    fixture.detectChanges();
  });

  it('renders every task with its skill tag and status', () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Grammar');
    expect(text).toContain('Vocabulary');
    expect(text).toContain('Listening');
    expect(text).toContain('Completed');
    expect(text).toContain('Skipped');
    expect(text).toContain('Not Started');
  });

  it('shows the completed/total count matching Completed+Skipped tasks out of the total', () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('2 / 3');
  });
});

describe('DailyChecklistComponent — status controls', () => {
  let fixture: ComponentFixture<DailyChecklistComponent>;
  let facadeStub: {
    tasks: ReturnType<typeof signal<Task[]>>;
    currentDayNumber: ReturnType<typeof signal<number>>;
    loadCurrentDay: jasmine.Spy;
    setStatus: jasmine.Spy;
  };

  beforeEach(async () => {
    const tasks = signal<Task[]>([
      makeTask({ id: 1, skill: 'Grammar', status: 'NotStarted' }),
    ]);
    facadeStub = {
      tasks,
      currentDayNumber: signal(3),
      loadCurrentDay: jasmine.createSpy('loadCurrentDay').and.resolveTo(undefined),
      setStatus: jasmine.createSpy('setStatus').and.callFake(() => {
        tasks.set([makeTask({ id: 1, skill: 'Grammar', status: 'Completed' })]);
        return Promise.resolve();
      }),
    };

    await TestBed.configureTestingModule({
      imports: [DailyChecklistComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();

    fixture = TestBed.createComponent(DailyChecklistComponent);
    fixture.detectChanges();
  });

  it('invokes facade.setStatus with the expected task id/value for each control', () => {
    const completeButton = fixture.nativeElement.querySelector(
      '[data-testid="complete-1"]',
    ) as HTMLButtonElement;
    completeButton.click();
    expect(facadeStub.setStatus).toHaveBeenCalledWith(1, 'Completed');
  });

  it('re-renders the completed/total count synchronously after a status change through the facade', () => {
    const completeButton = fixture.nativeElement.querySelector(
      '[data-testid="complete-1"]',
    ) as HTMLButtonElement;
    completeButton.click();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('1 / 1');
  });
});

describe('DailyChecklistComponent — move to next day', () => {
  it('renders the blocked-reason message naming unresolved tasks when the facade returns a blocked result', async () => {
    const tasks = signal<Task[]>([makeTask({ id: 2, status: 'NotStarted' })]);
    const facadeStub = {
      tasks,
      currentDayNumber: signal(3),
      loadCurrentDay: jasmine.createSpy('loadCurrentDay').and.resolveTo(undefined),
      setStatus: jasmine.createSpy('setStatus'),
      moveToNextDay: jasmine
        .createSpy('moveToNextDay')
        .and.resolveTo({ success: false, unresolvedTaskIds: [2] }),
    };

    await TestBed.configureTestingModule({
      imports: [DailyChecklistComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();
    const fixture = TestBed.createComponent(DailyChecklistComponent);
    fixture.detectChanges();

    const moveButton = fixture.nativeElement.querySelector(
      '[data-testid="move-to-next-day"]',
    ) as HTMLButtonElement;
    moveButton.click();
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('2');
    expect(facadeStub.currentDayNumber()).toBe(3);
  });

  it('advances the displayed current day when the facade returns success', async () => {
    const tasks = signal<Task[]>([makeTask({ id: 1, status: 'Completed' })]);
    const currentDayNumber = signal(3);
    const facadeStub = {
      tasks,
      currentDayNumber,
      loadCurrentDay: jasmine.createSpy('loadCurrentDay').and.resolveTo(undefined),
      setStatus: jasmine.createSpy('setStatus'),
      moveToNextDay: jasmine.createSpy('moveToNextDay').and.callFake(() => {
        currentDayNumber.set(4);
        return Promise.resolve({ success: true });
      }),
    };

    await TestBed.configureTestingModule({
      imports: [DailyChecklistComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();
    const fixture = TestBed.createComponent(DailyChecklistComponent);
    fixture.detectChanges();

    const moveButton = fixture.nativeElement.querySelector(
      '[data-testid="move-to-next-day"]',
    ) as HTMLButtonElement;
    moveButton.click();
    await fixture.whenStable();
    fixture.detectChanges();

    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Day 4 of 180');
  });
});
