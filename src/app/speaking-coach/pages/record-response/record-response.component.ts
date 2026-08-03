import {
  ChangeDetectionStrategy,
  ChangeDetectorRef,
  Component,
  OnDestroy,
  OnInit,
  inject,
} from '@angular/core';
import { RouterLink } from '@angular/router';
import { DailyLessonFacade } from '../../../daily-lesson/state/daily-lesson.facade';
import { SpeakingPart } from '../../models/speaking-question.model';
import { SpeakingCoachFacade } from '../../state/speaking-coach.facade';

export type SpeakingPromptSource = 'daily' | 'bank';

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
  private readonly dailyLessonFacade = inject(DailyLessonFacade);
  selectedPart: SpeakingPart = 'PART_1';
  selectedQuestionId = '';
  promptSource: SpeakingPromptSource = 'bank';
  dailyPromptText: string | null = null;
  dailyPromptDay: string | null = null;
  dailyPromptTargetBand: number | null = null;
  dailyPromptPhase: string | null = null;
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
    if (this.dailyLessonFacade.state() === 'idle') {
      await this.dailyLessonFacade.load().catch(() => undefined);
    }
    const overview = this.dailyLessonFacade.overview();
    const entry = overview?.skills.find(
      (s) => s.skill === 'speaking' && s.generatedPromptText,
    );
    if (entry?.generatedPromptText) {
      this.dailyPromptText = entry.generatedPromptText;
      this.dailyPromptDay = entry.day;
      this.dailyPromptTargetBand = entry.targetBand;
      this.dailyPromptPhase = entry.phase;
      this.promptSource = 'daily';
    }
  }

  get filteredQuestions() {
    return this.facade.questions().filter((item) => item.part === this.selectedPart);
  }

  selectPromptSource(value: SpeakingPromptSource): void {
    this.promptSource = value;
  }

  get canSubmit(): boolean {
    const hasPrompt =
      this.promptSource === 'daily'
        ? Boolean(this.dailyPromptText)
        : Boolean(this.selectedQuestionId);
    return Boolean(hasPrompt && this.audio && this.elapsedSeconds > 0);
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
      const options =
        this.promptSource === 'daily' && this.dailyPromptText
          ? { promptText: this.dailyPromptText, day: this.dailyPromptDay ?? undefined }
          : { questionId: this.selectedQuestionId };
      await this.facade.submit(options, this.audio, this.elapsedSeconds);
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
