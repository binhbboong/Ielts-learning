import {
  ChangeDetectionStrategy,
  Component,
  Input,
  OnDestroy,
  OnInit,
  computed,
  signal,
} from '@angular/core';

/**
 * A non-blocking countdown for standard/advanced-tier Reading/Listening
 * exercises (docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md,
 * reading-practice/listening-practice Specification.md revision 2 FR-19/
 * FR-23). Purely visual pacing aid: it never disables the form, never
 * auto-submits, and simply holds at 00:00 once it reaches zero.
 */
@Component({
  selector: 'app-countdown-timer',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="countdown-timer" role="timer" [attr.aria-label]="'Time remaining ' + displayTime()">
      <span class="countdown-timer__label">Time remaining</span>
      <span class="countdown-timer__value" data-testid="countdown-timer-value">{{ displayTime() }}</span>
    </div>
  `,
  styles: [`
    .countdown-timer {
      display: inline-flex;
      align-items: baseline;
      gap: 0.4rem;
      padding: 0.4rem 0.75rem;
      border: 1px solid #ccc;
      border-radius: 0.375rem;
      background: #f9fafb;
      font-variant-numeric: tabular-nums;
    }

    .countdown-timer__label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #666;
    }

    .countdown-timer__value {
      font-weight: 700;
    }
  `],
})
export class CountdownTimerComponent implements OnInit, OnDestroy {
  @Input({ required: true }) minutes = 0;

  private readonly remainingSecondsSignal = signal(0);
  private intervalId?: ReturnType<typeof setInterval>;

  readonly remainingSeconds = this.remainingSecondsSignal.asReadonly();
  readonly displayTime = computed(() => {
    const total = this.remainingSecondsSignal();
    const mm = Math.floor(total / 60).toString().padStart(2, '0');
    const ss = (total % 60).toString().padStart(2, '0');
    return `${mm}:${ss}`;
  });

  ngOnInit(): void {
    this.remainingSecondsSignal.set(Math.max(0, Math.round(this.minutes * 60)));
    this.intervalId = setInterval(() => this.tick(), 1000);
  }

  ngOnDestroy(): void {
    if (this.intervalId !== undefined) {
      clearInterval(this.intervalId);
    }
  }

  private tick(): void {
    this.remainingSecondsSignal.update((seconds) => Math.max(0, seconds - 1));
  }
}
