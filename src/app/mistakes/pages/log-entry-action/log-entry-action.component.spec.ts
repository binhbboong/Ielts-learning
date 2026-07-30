import { TestBed } from '@angular/core/testing';
import { LogEntryActionComponent } from './log-entry-action.component';

describe('LogEntryActionComponent', () => {
  for (const skill of ['reading', 'listening', 'writing', 'speaking'] as const) {
    it(`emits editable ${skill} context when opened`, () => {
      const fixture = TestBed.createComponent(LogEntryActionComponent);
      fixture.componentRef.setInput('context', {
        skill,
        source: `${skill} practice`,
      });
      const emitted = jasmine.createSpy('opened');
      fixture.componentInstance.opened.subscribe(emitted);
      fixture.detectChanges();

      fixture.nativeElement.querySelector('button').click();

      expect(emitted).toHaveBeenCalledWith({
        skill,
        source: `${skill} practice`,
      });
    });
  }
});
