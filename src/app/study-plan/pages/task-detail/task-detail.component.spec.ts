import { ComponentFixture, TestBed } from '@angular/core/testing';
import { TaskDetailComponent } from './task-detail.component';
import { StudyPlanFacade } from '../../state/study-plan.facade';
import { Task } from '../../models/task.model';

function makeTask(overrides: Partial<Task> = {}): Task {
  return {
    id: 1,
    dayNumber: 3,
    skill: 'Grammar',
    title: 'Present Perfect',
    description: 'Study present perfect forms.',
    estimatedMinutes: 25,
    status: 'NotStarted',
    note: 'original note',
    updatedAt: '',
    ...overrides,
  };
}

describe('TaskDetailComponent — render and edit note', () => {
  let fixture: ComponentFixture<TaskDetailComponent>;
  let facadeStub: { updateNote: jasmine.Spy };
  let task: Task;

  beforeEach(async () => {
    task = makeTask();
    facadeStub = { updateNote: jasmine.createSpy('updateNote').and.resolveTo(undefined) };

    await TestBed.configureTestingModule({
      imports: [TaskDetailComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();

    fixture = TestBed.createComponent(TaskDetailComponent);
    fixture.componentInstance.task = task;
    fixture.componentInstance.ngOnChanges();
    fixture.detectChanges();
  });

  it("renders the task's existing fields", () => {
    const text = fixture.nativeElement.textContent as string;
    expect(text).toContain('Present Perfect');
    const descriptionField = fixture.nativeElement.querySelector(
      '[data-testid="description-field"]',
    ) as HTMLTextAreaElement;
    expect(descriptionField.value).toBe('Study present perfect forms.');
    const estimatedField = fixture.nativeElement.querySelector(
      '[data-testid="estimated-minutes-field"]',
    ) as HTMLInputElement;
    expect(estimatedField.value).toBe('25');
    const noteField = fixture.nativeElement.querySelector(
      '[data-testid="note-field"]',
    ) as HTMLTextAreaElement;
    expect(noteField.value).toBe('original note');
  });

  it('calls facade.updateNote(taskId, text) when the note is edited then Save is clicked', () => {
    const noteField = fixture.nativeElement.querySelector(
      '[data-testid="note-field"]',
    ) as HTMLTextAreaElement;
    noteField.value = 'an edited note';
    noteField.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const saveButton = fixture.nativeElement.querySelector(
      '[data-testid="save-note"]',
    ) as HTMLButtonElement;
    saveButton.click();

    expect(facadeStub.updateNote).toHaveBeenCalledWith(1, 'an edited note');
  });

  it('discards the edit and leaves the persisted note unchanged when Cancel is clicked', () => {
    const noteField = fixture.nativeElement.querySelector(
      '[data-testid="note-field"]',
    ) as HTMLTextAreaElement;
    noteField.value = 'a discarded edit';
    noteField.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const cancelButton = fixture.nativeElement.querySelector(
      '[data-testid="cancel-note"]',
    ) as HTMLButtonElement;
    cancelButton.click();
    fixture.detectChanges();

    expect(facadeStub.updateNote).not.toHaveBeenCalled();
    const noteFieldAfter = fixture.nativeElement.querySelector(
      '[data-testid="note-field"]',
    ) as HTMLTextAreaElement;
    expect(noteFieldAfter.value).toBe('original note');
  });
});

describe('TaskDetailComponent — edit description and estimated time', () => {
  let fixture: ComponentFixture<TaskDetailComponent>;
  let facadeStub: { updateTaskDetails: jasmine.Spy };
  let task: Task;

  beforeEach(async () => {
    task = makeTask({ description: 'old description', estimatedMinutes: 20 });
    facadeStub = {
      updateTaskDetails: jasmine.createSpy('updateTaskDetails').and.resolveTo(undefined),
    };

    await TestBed.configureTestingModule({
      imports: [TaskDetailComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();

    fixture = TestBed.createComponent(TaskDetailComponent);
    fixture.componentInstance.task = task;
    fixture.componentInstance.ngOnChanges();
    fixture.detectChanges();
  });

  it('calls facade.updateTaskDetails with the edited values when Save is clicked', () => {
    const descriptionField = fixture.nativeElement.querySelector(
      '[data-testid="description-field"]',
    ) as HTMLTextAreaElement;
    descriptionField.value = 'new description';
    descriptionField.dispatchEvent(new Event('input'));

    const estimatedField = fixture.nativeElement.querySelector(
      '[data-testid="estimated-minutes-field"]',
    ) as HTMLInputElement;
    estimatedField.value = '35';
    estimatedField.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const saveButton = fixture.nativeElement.querySelector(
      '[data-testid="save-details"]',
    ) as HTMLButtonElement;
    saveButton.click();

    expect(facadeStub.updateTaskDetails).toHaveBeenCalledWith(1, {
      description: 'new description',
      estimatedMinutes: 35,
    });
  });

  it('leaves persisted values unchanged when Cancel is clicked', () => {
    const descriptionField = fixture.nativeElement.querySelector(
      '[data-testid="description-field"]',
    ) as HTMLTextAreaElement;
    descriptionField.value = 'a discarded description';
    descriptionField.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    const cancelButton = fixture.nativeElement.querySelector(
      '[data-testid="cancel-details"]',
    ) as HTMLButtonElement;
    cancelButton.click();
    fixture.detectChanges();

    expect(facadeStub.updateTaskDetails).not.toHaveBeenCalled();
    const descriptionFieldAfter = fixture.nativeElement.querySelector(
      '[data-testid="description-field"]',
    ) as HTMLTextAreaElement;
    expect(descriptionFieldAfter.value).toBe('old description');
  });
});

describe('TaskDetailComponent — status control', () => {
  let fixture: ComponentFixture<TaskDetailComponent>;
  let facadeStub: { setStatus: jasmine.Spy };

  beforeEach(async () => {
    const task = makeTask({ status: 'NotStarted' });
    facadeStub = { setStatus: jasmine.createSpy('setStatus').and.resolveTo(undefined) };

    await TestBed.configureTestingModule({
      imports: [TaskDetailComponent],
      providers: [{ provide: StudyPlanFacade, useValue: facadeStub }],
    }).compileComponents();

    fixture = TestBed.createComponent(TaskDetailComponent);
    fixture.componentInstance.task = task;
    fixture.componentInstance.ngOnChanges();
    fixture.detectChanges();
  });

  it('invokes facade.setStatus with the expected task id/value for each of the three states', () => {
    for (const status of ['Completed', 'Skipped', 'NotStarted'] as const) {
      const button = fixture.nativeElement.querySelector(
        `[data-testid="status-${status}"]`,
      ) as HTMLButtonElement;
      button.click();
      expect(facadeStub.setStatus).toHaveBeenCalledWith(1, status);
    }
  });
});
