import { TestBed } from '@angular/core/testing';
import { MistakeRepository } from '../../data/mistake.repository';
import { MistakeQuickAddComponent } from './mistake-quick-add.component';

describe('MistakeQuickAddComponent', () => {
  async function setUp() {
    const repository = jasmine.createSpyObj<MistakeRepository>(
      'MistakeRepository', ['create'],
    );
    repository.create.and.resolveTo({
      id: 'm1', skill: 'reading', questionType: null, source: 'Today\'s passage, Q1',
      ownAnswer: 'A', correctAnswer: 'C', explanation: null,
      reasonCategory: 'not_sure_other', loggedAt: '2026-07-30T10:00:00Z', isIncomplete: false,
    });
    await TestBed.configureTestingModule({
      imports: [MistakeQuickAddComponent],
      providers: [{ provide: MistakeRepository, useValue: repository }],
    }).compileComponents();
    const fixture = TestBed.createComponent(MistakeQuickAddComponent);
    fixture.componentInstance.data = {
      skill: 'reading',
      source: "Today's passage, Q1",
      ownAnswer: 'A',
      correctAnswer: 'C',
    };
    return { fixture, component: fixture.componentInstance, repository };
  }

  it('requires no re-entry of already-known fields', async () => {
    const { component } = await setUp();
    expect(component.data.ownAnswer).toBe('A');
    expect(component.data.correctAnswer).toBe('C');
    expect(component.selectedReason).toBeNull();
  });

  it('saves with the selected reason pre-filled from the known data', async () => {
    const { component, repository } = await setUp();
    component.selectedReason = 'missed_paraphrase';

    await component.save();

    expect(repository.create).toHaveBeenCalledWith({
      skill: 'reading',
      source: "Today's passage, Q1",
      ownAnswer: 'A',
      correctAnswer: 'C',
      reasonCategory: 'missed_paraphrase',
    });
  });

  it('saves without a reason when skipped', async () => {
    const { component, repository } = await setUp();

    await component.save();

    expect(repository.create).toHaveBeenCalledWith({
      skill: 'reading',
      source: "Today's passage, Q1",
      ownAnswer: 'A',
      correctAnswer: 'C',
      reasonCategory: undefined,
    });
  });

  it('emits saved after a successful save', async () => {
    const { component } = await setUp();
    const savedSpy = jasmine.createSpy();
    component.saved.subscribe(savedSpy);

    await component.save();

    expect(savedSpy).toHaveBeenCalled();
  });

  it('emits cancelled without saving', async () => {
    const { component, repository } = await setUp();
    const cancelledSpy = jasmine.createSpy();
    component.cancelled.subscribe(cancelledSpy);

    component.cancel();

    expect(cancelledSpy).toHaveBeenCalled();
    expect(repository.create).not.toHaveBeenCalled();
  });
});
