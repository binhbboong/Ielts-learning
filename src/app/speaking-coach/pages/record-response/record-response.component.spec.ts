import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { SpeakingCoachRepository } from '../../data/speaking-coach.repository';
import { RecordResponseComponent } from './record-response.component';

describe('RecordResponseComponent', () => {
  it('requires a question and recording before submit', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository', ['questions'],
    );
    repository.questions.and.resolveTo([]);
    await TestBed.configureTestingModule({
      imports: [RecordResponseComponent],
      providers: [
        provideRouter([]),
        { provide: SpeakingCoachRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(RecordResponseComponent);
    fixture.detectChanges();
    expect(fixture.componentInstance.canSubmit).toBeFalse();
    fixture.componentInstance.audio = new Blob(['audio']);
    fixture.componentInstance.elapsedSeconds = 10;
    expect(fixture.componentInstance.canSubmit).toBeFalse();
    fixture.componentInstance.selectedQuestionId = 'q1';
    expect(fixture.componentInstance.canSubmit).toBeTrue();
  });

  it('stops and warns at the 120-second cap', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository', ['questions'],
    );
    repository.questions.and.resolveTo([]);
    await TestBed.configureTestingModule({
      imports: [RecordResponseComponent],
      providers: [
        provideRouter([]),
        { provide: SpeakingCoachRepository, useValue: repository },
      ],
    }).compileComponents();
    const fixture = TestBed.createComponent(RecordResponseComponent);
    const component = fixture.componentInstance;
    const stop = spyOn(component, 'stopRecording');
    component.elapsedSeconds = 119;
    component.advanceRecordingClock();
    expect(stop).toHaveBeenCalled();
    expect(component.recordingError).toContain('120-second limit');
  });
});
