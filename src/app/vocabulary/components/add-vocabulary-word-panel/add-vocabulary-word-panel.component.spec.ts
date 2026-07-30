import { TestBed } from '@angular/core/testing';
import { VocabularyFacade } from '../../state/vocabulary.facade';
import { AddVocabularyWordPanelComponent } from './add-vocabulary-word-panel.component';

describe('AddVocabularyWordPanelComponent', () => {
  let facade: jasmine.SpyObj<VocabularyFacade>;

  beforeEach(() => {
    facade = jasmine.createSpyObj<VocabularyFacade>('VocabularyFacade', ['addWord']);
    facade.addWord.and.resolveTo({} as never);
    TestBed.configureTestingModule({
      imports: [AddVocabularyWordPanelComponent],
      providers: [{ provide: VocabularyFacade, useValue: facade }],
    });
  });

  it('disables save until word and meaning are non-empty', () => {
    const fixture = TestBed.createComponent(AddVocabularyWordPanelComponent);
    fixture.detectChanges();
    const button = fixture.nativeElement.querySelector(
      '[data-testid="save-word"]',
    ) as HTMLButtonElement;
    expect(button.disabled).toBeTrue();
    fixture.componentInstance.word = 'ubiquitous';
    fixture.componentInstance.meaning = 'everywhere';
    fixture.detectChanges();
    expect(button.disabled).toBeFalse();
  });

  it('shows confirmation on success', async () => {
    const fixture = TestBed.createComponent(AddVocabularyWordPanelComponent);
    fixture.componentInstance.word = 'ubiquitous';
    fixture.componentInstance.meaning = 'everywhere';
    await fixture.componentInstance.save();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('Added to your review schedule');
  });

  it('preserves all fields and permits retry after failure', async () => {
    facade.addWord.and.rejectWith(new Error('offline'));
    const fixture = TestBed.createComponent(AddVocabularyWordPanelComponent);
    const component = fixture.componentInstance;
    Object.assign(component, {
      word: 'word',
      meaning: 'meaning',
      example: 'example',
      topic: 'topic',
    });
    await component.save();
    expect(component.word).toBe('word');
    expect(component.meaning).toBe('meaning');
    expect(component.example).toBe('example');
    expect(component.topic).toBe('topic');
    expect(component.saving).toBeFalse();
    expect(component.errorMessage).toContain('try again');
  });
});
