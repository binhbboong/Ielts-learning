import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import {
  MistakeQuickAddComponent,
  MistakeQuickAddData,
} from '../../../mistakes/pages/quick-add/mistake-quick-add.component';
import { isTextBasedQuestionType } from '../../../core/exam/question-types';
import {
  ListeningAnswerResult,
  ListeningQuestion,
  ListeningSection,
} from '../../models/listening-exercise.model';
import { ListeningPracticeFacade } from '../../state/listening-practice.facade';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

interface ListeningSectionView {
  section: ListeningSection;
  questions: { question: ListeningQuestion; flatIndex: number }[];
}

@Component({
  selector: 'app-listening-exercise',
  standalone: true,
  imports: [RouterLink, FormsModule, MistakeQuickAddComponent],
  templateUrl: './listening-exercise.component.html',
  styleUrl: './listening-exercise.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListeningExerciseComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly facade = inject(ListeningPracticeFacade);
  day = '';
  selectedAnswers: (number | string | null)[] = [];
  openQuickAddIndex: number | null = null;
  readonly isTextBasedQuestionType = isTextBasedQuestionType;

  async ngOnInit(): Promise<void> {
    this.day = this.route.snapshot.paramMap.get('day') ?? todayIso();
    await this.facade.load(this.day);
    const questionCount = this.flatQuestions.length;
    this.selectedAnswers = new Array(questionCount).fill(null);
  }

  get flatQuestions(): ListeningQuestion[] {
    return (this.facade.exercise()?.sections ?? []).flatMap((s) => s.questions);
  }

  get sectionViews(): ListeningSectionView[] {
    let index = 0;
    return (this.facade.exercise()?.sections ?? []).map((section) => ({
      section,
      questions: section.questions.map((question) => ({ question, flatIndex: index++ })),
    }));
  }

  audioUrl(order: number): string {
    return this.facade.audioUrl(this.day, order);
  }

  selectAnswer(questionIndex: number, optionIndex: number): void {
    this.selectedAnswers[questionIndex] = optionIndex;
  }

  setTextAnswer(questionIndex: number, value: string): void {
    this.selectedAnswers[questionIndex] = value;
  }

  get canSubmit(): boolean {
    return (
      this.selectedAnswers.length > 0 &&
      this.selectedAnswers.every(
        (answer) => answer !== null && !(typeof answer === 'string' && !answer.trim()),
      )
    );
  }

  async submit(): Promise<void> {
    if (!this.canSubmit) return;
    await this.facade.submit(this.selectedAnswers as (number | string)[]);
  }

  async retryScript(): Promise<void> {
    await this.facade.retryScript();
  }

  async retryAudio(): Promise<void> {
    await this.facade.retryAudio();
  }

  openQuickAdd(index: number): void {
    this.openQuickAddIndex = index;
  }

  closeQuickAdd(): void {
    this.openQuickAddIndex = null;
  }

  private displayAnswer(answer: ListeningAnswerResult, value: number | string | null): string {
    if (value === null) return '';
    if (typeof value === 'string') return value;
    return answer.options?.[value] ?? '';
  }

  quickAddData(answer: ListeningAnswerResult): MistakeQuickAddData {
    return {
      skill: 'listening',
      source: `Listening practice ${this.day}: ${answer.questionText}`,
      ownAnswer: this.displayAnswer(answer, answer.learnerAnswer),
      correctAnswer: this.displayAnswer(answer, answer.correctAnswer),
    };
  }
}
