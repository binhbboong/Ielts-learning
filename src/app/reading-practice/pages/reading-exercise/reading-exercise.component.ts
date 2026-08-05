import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  MistakeQuickAddComponent,
  MistakeQuickAddData,
} from '../../../mistakes/pages/quick-add/mistake-quick-add.component';
import { CountdownTimerComponent } from '../../../core/exam/countdown-timer.component';
import { isTextBasedQuestionType } from '../../../core/exam/question-types';
import { isBeginnerPhase } from '../../../core/exam/phase-tier';
import {
  ReadingAnswerResult,
  ReadingPassage,
  ReadingQuestion,
} from '../../models/reading-exercise.model';
import { ReadingPracticeFacade } from '../../state/reading-practice.facade';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

interface PassageSection {
  passage: ReadingPassage;
  questions: { question: ReadingQuestion; flatIndex: number }[];
}

@Component({
  selector: 'app-reading-exercise',
  standalone: true,
  imports: [RouterLink, FormsModule, MistakeQuickAddComponent, CountdownTimerComponent],
  templateUrl: './reading-exercise.component.html',
  styleUrl: './reading-exercise.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReadingExerciseComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly facade = inject(ReadingPracticeFacade);
  selectedAnswers: (number | string | null)[] = [];
  openQuickAddIndex: number | null = null;
  readonly isTextBasedQuestionType = isTextBasedQuestionType;

  get showTimer(): boolean {
    const exercise = this.facade.exercise();
    return Boolean(
      exercise && !isBeginnerPhase(exercise.phase) && exercise.targetMinutes,
    );
  }

  async ngOnInit(): Promise<void> {
    const day = this.route.snapshot.paramMap.get('day') ?? todayIso();
    await this.facade.load(day);
    const questionCount = this.flatQuestions.length;
    this.selectedAnswers = new Array(questionCount).fill(null);
  }

  get flatQuestions(): ReadingQuestion[] {
    return (this.facade.exercise()?.passages ?? []).flatMap((p) => p.questions);
  }

  get passageSections(): PassageSection[] {
    let index = 0;
    return (this.facade.exercise()?.passages ?? []).map((passage) => ({
      passage,
      questions: passage.questions.map((question) => ({ question, flatIndex: index++ })),
    }));
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

  async retry(): Promise<void> {
    await this.facade.retry();
  }

  openQuickAdd(index: number): void {
    this.openQuickAddIndex = index;
  }

  closeQuickAdd(): void {
    this.openQuickAddIndex = null;
  }

  private displayAnswer(answer: ReadingAnswerResult, value: number | string | null): string {
    if (value === null) return '';
    if (typeof value === 'string') return value;
    return answer.options?.[value] ?? '';
  }

  quickAddData(answer: ReadingAnswerResult): MistakeQuickAddData {
    const day = this.facade.result()?.day ?? this.facade.exercise()?.day ?? '';
    return {
      skill: 'reading',
      source: `Reading practice ${day}: ${answer.questionText}`,
      ownAnswer: this.displayAnswer(answer, answer.learnerAnswer),
      correctAnswer: this.displayAnswer(answer, answer.correctAnswer),
    };
  }
}
