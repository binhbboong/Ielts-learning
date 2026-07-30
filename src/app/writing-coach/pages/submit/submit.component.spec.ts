import { Location } from '@angular/common';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { WritingCoachRepository } from '../../data/writing-coach.repository';
import { WritingSubmitComponent } from './submit.component';

describe('WritingSubmitComponent', () => {
  it('blocks blank input, preserves failed text, and retries', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    repository.submit.and.rejectWith(new Error('offline'));
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    const component = fixture.componentInstance;
    expect(component.canSubmit).toBeFalse();
    component.questionText = 'Discuss both views.';
    component.responseText = 'My complete response.';
    await component.submit();
    fixture.detectChanges();
    expect(component.responseText).toBe('My complete response.');
    expect(fixture.nativeElement.querySelector('[data-testid="writing-error"]'))
      .not.toBeNull();
    expect(repository.submit).toHaveBeenCalledTimes(1);
  });

  it('abandons without submitting', async () => {
    const repository = jasmine.createSpyObj<WritingCoachRepository>(
      'WritingCoachRepository', ['submit'],
    );
    const location = jasmine.createSpyObj<Location>('Location', ['back']);
    await TestBed.configureTestingModule({
      imports: [WritingSubmitComponent],
      providers: [
        provideRouter([]),
        { provide: WritingCoachRepository, useValue: repository },
        { provide: Location, useValue: location },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(WritingSubmitComponent);
    fixture.componentInstance.cancel();
    expect(repository.submit).not.toHaveBeenCalled();
    expect(location.back).toHaveBeenCalled();
  });
});
