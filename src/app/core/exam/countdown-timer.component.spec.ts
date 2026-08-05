import { TestBed } from '@angular/core/testing';
import { CountdownTimerComponent } from './countdown-timer.component';

describe('CountdownTimerComponent', () => {
  beforeEach(() => {
    jasmine.clock().install();
  });

  afterEach(() => {
    jasmine.clock().uninstall();
  });

  async function setUp(minutes: number) {
    await TestBed.configureTestingModule({
      imports: [CountdownTimerComponent],
    }).compileComponents();
    const fixture = TestBed.createComponent(CountdownTimerComponent);
    fixture.componentInstance.minutes = minutes;
    fixture.detectChanges();
    return fixture;
  }

  it('starts at the given number of minutes converted to seconds', async () => {
    const fixture = await setUp(1);
    expect(fixture.componentInstance.remainingSeconds()).toBe(60);
    expect(fixture.componentInstance.displayTime()).toBe('01:00');
  });

  it('counts down by one second per tick', async () => {
    const fixture = await setUp(1);

    jasmine.clock().tick(3000);

    expect(fixture.componentInstance.remainingSeconds()).toBe(57);
    expect(fixture.componentInstance.displayTime()).toBe('00:57');
  });

  it('holds at zero instead of going negative once time runs out', async () => {
    const fixture = await setUp(0.05); // 3 seconds

    jasmine.clock().tick(10000);

    expect(fixture.componentInstance.remainingSeconds()).toBe(0);
    expect(fixture.componentInstance.displayTime()).toBe('00:00');
  });

  it('stops ticking after the component is destroyed', async () => {
    const fixture = await setUp(1);
    jasmine.clock().tick(2000);
    expect(fixture.componentInstance.remainingSeconds()).toBe(58);

    fixture.destroy();
    jasmine.clock().tick(5000);

    expect(fixture.componentInstance.remainingSeconds()).toBe(58);
  });

  it('renders the display time in the template', async () => {
    const fixture = await setUp(2);
    fixture.detectChanges();

    const value = fixture.nativeElement.querySelector('[data-testid="countdown-timer-value"]');
    expect(value.textContent.trim()).toBe('02:00');
  });
});
