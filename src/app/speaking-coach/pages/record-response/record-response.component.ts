import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { SpeakingPart } from '../../models/speaking-question.model';
import { SpeakingCoachFacade } from '../../state/speaking-coach.facade';

@Component({
  selector: 'app-record-response',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './record-response.component.html',
  styleUrl: './record-response.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RecordResponseComponent implements OnInit, OnDestroy {
  private readonly cdr = inject(ChangeDetectorRef);
  readonly facade = inject(SpeakingCoachFacade);
  selectedPart: SpeakingPart = 'PART_1';
  selectedQuestionId = '';
  recording = false;
  elapsedSeconds = 0;
  audio: Blob | null = null;
  recordingError = '';
  private recorder: MediaRecorder | null = null;
  private stream: MediaStream | null = null;
  private chunks: Blob[] = [];
  private timer: ReturnType<typeof setInterval> | null = null;

  async ngOnInit(): Promise<void> {
    try {
      await this.facade.loadQuestions();
    } catch {
      this.recordingError = 'Questions could not be loaded.';
    }
  }

  get filteredQuestions() {
    return this.facade.questions().filter((item) => item.part === this.selectedPart);
  }

  get canSubmit(): boolean {
    return Boolean(this.selectedQuestionId && this.audio && this.elapsedSeconds > 0);
  }

  changePart(value: SpeakingPart): void {
    this.selectedPart = value;
    this.selectedQuestionId = '';
  }

  async startRecording(): Promise<void> {
    this.recordingError = '';
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === 'undefined') {
      this.recordingError = 'Audio recording is not supported in this browser.';
      return;
    }
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.chunks = [];
      this.elapsedSeconds = 0;
      this.audio = null;
      this.recorder = new MediaRecorder(this.stream);
      this.recorder.ondataavailable = (event) => {
        if (event.data.size) this.chunks.push(event.data);
      };
      this.recorder.onstop = () => {
        this.audio = new Blob(this.chunks, { type: this.recorder?.mimeType || 'audio/webm' });
        this.recording = false;
        this.stopTimer();
        this.stream?.getTracks().forEach((track) => track.stop());
        this.cdr.markForCheck();
      };
      this.recorder.start();
      this.recording = true;
      this.timer = setInterval(() => {
        this.advanceRecordingClock();
        this.cdr.markForCheck();
      }, 1000);
    } catch {
      this.recordingError = 'Microphone access was not available.';
    }
  }

  stopRecording(): void {
    if (this.recorder?.state === 'recording') this.recorder.stop();
  }

  advanceRecordingClock(): void {
    this.elapsedSeconds += 1;
    if (this.elapsedSeconds >= 120) {
      this.recordingError = 'Recording stopped at the 120-second limit.';
      this.stopRecording();
    }
  }

  async submit(): Promise<void> {
    if (!this.canSubmit || !this.audio) return;
    try {
      await this.facade.submit(
        this.selectedQuestionId,
        this.audio,
        this.elapsedSeconds,
      );
    } catch {
      this.recordingError = 'The recording could not be submitted.';
    }
  }

  ngOnDestroy(): void {
    this.stopTimer();
    if (this.recorder?.state === 'recording') this.recorder.stop();
    this.stream?.getTracks().forEach((track) => track.stop());
  }

  private stopTimer(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
  }
}
