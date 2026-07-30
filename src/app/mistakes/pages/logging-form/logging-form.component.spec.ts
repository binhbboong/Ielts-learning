import { TestBed } from '@angular/core/testing';
import { MistakeFacade } from '../../state/mistake.facade';
import { LoggingFormComponent } from './logging-form.component';

describe('LoggingFormComponent', () => {
  let facade: jasmine.SpyObj<MistakeFacade>;

  beforeEach(() => {
    facade = jasmine.createSpyObj<MistakeFacade>('MistakeFacade', ['create']);
    facade.create.and.resolveTo({} as never);
    TestBed.configureTestingModule({
      imports: [LoggingFormComponent],
      providers: [{ provide: MistakeFacade, useValue: facade }],
    });
  });

  it('prefills editable context and renders exactly nine reasons', () => {
    const fixture = TestBed.createComponent(LoggingFormComponent);
    fixture.componentRef.setInput('initialSkill', 'reading');
    fixture.componentRef.setInput('initialSource', 'Cambridge 18');
    fixture.detectChanges();

    const skill = fixture.nativeElement.querySelector(
      '[data-testid="skill"]',
    ) as HTMLSelectElement;
    const source = fixture.nativeElement.querySelector(
      '[data-testid="source"]',
    ) as HTMLInputElement;
    const reasons = fixture.nativeElement.querySelectorAll(
      '[data-testid="reason"] option',
    );
    expect(skill.value).toBe('reading');
    expect(skill.disabled).toBeFalse();
    expect(source.value).toBe('Cambridge 18');
    expect(source.disabled).toBeFalse();
    expect(reasons.length).toBe(9);
  });

  it('saves a full entry and permits a minimal entry', async () => {
    const fixture = TestBed.createComponent(LoggingFormComponent);
    fixture.componentRef.setInput('initialSkill', 'reading');
    fixture.componentRef.setInput('initialSource', 'Book');
    fixture.detectChanges();
    const component = fixture.componentInstance;
    component.questionType = 'matching';
    component.ownAnswer = 'A';
    component.correctAnswer = 'B';
    component.explanation = 'Missed synonym';
    component.reasonCategory = 'missed_paraphrase';

    await component.save();
    expect(facade.create).toHaveBeenCalledWith({
      skill: 'reading',
      source: 'Book',
      questionType: 'matching',
      ownAnswer: 'A',
      correctAnswer: 'B',
      explanation: 'Missed synonym',
      reasonCategory: 'missed_paraphrase',
    });

    facade.create.calls.reset();
    component.questionType = '';
    component.ownAnswer = '';
    component.correctAnswer = '';
    component.explanation = '';
    component.reasonCategory = 'not_sure_other';
    await component.save();
    expect(facade.create).toHaveBeenCalledWith(
      jasmine.objectContaining({ skill: 'reading', source: 'Book' }),
    );
  });

  it('close preserves a partial entry while cancel discards it', async () => {
    const fixture = TestBed.createComponent(LoggingFormComponent);
    fixture.componentRef.setInput('initialSkill', 'listening');
    fixture.componentRef.setInput('initialSource', 'Mock');
    fixture.detectChanges();

    await fixture.componentInstance.close();
    expect(facade.create).toHaveBeenCalled();
    facade.create.calls.reset();
    fixture.componentInstance.cancel();
    expect(facade.create).not.toHaveBeenCalled();
  });

  it('unknown-answer mode clears the answer and still saves', async () => {
    const fixture = TestBed.createComponent(LoggingFormComponent);
    fixture.componentRef.setInput('initialSkill', 'writing');
    fixture.componentRef.setInput('initialSource', 'Essay');
    fixture.detectChanges();
    fixture.componentInstance.correctAnswer = 'Old';
    fixture.componentInstance.correctAnswerUnknown = true;

    await fixture.componentInstance.save();

    expect(facade.create).toHaveBeenCalledWith(
      jasmine.objectContaining({
        correctAnswer: undefined,
        reasonCategory: 'not_sure_other',
      }),
    );
  });
});
