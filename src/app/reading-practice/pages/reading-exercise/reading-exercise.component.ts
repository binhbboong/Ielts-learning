import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  MistakeQuickAddComponent,
  MistakeQuickAddData,
} from '../../../mistakes/pages/quick-add/mistake-quick-add.component';
import { ReadingAnswerResult } from '../../models/reading-exercise.model';
import { ReadingPracticeFacade } from '../../state/reading-practice.facade';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

@Component({
  selector: 'app-reading-exercise',
  standalone: true,
  imports: [RouterLink, MistakeQuickAddComponent],
  templateUrl: './reading-exercise.component.html',
  styleUrl: './reading-exercise.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ReadingExerciseComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly facade = inject(ReadingPracticeFacade);
  selectedAnswers: (number | null)[] = [];
  openQuickAddIndex: number | null = null;

  async ngOnInit(): Promise<void> {
    const day = this.route.snapshot.paramMap.get('day') ?? todayIso();
    await this.facade.load(day);
    const questionCount = this.facade.exercise()?.questions.length ?? 0;
    this.selectedAnswers = new Array(questionCount).fill(null);
  }

  selectAnswer(questionIndex: number, optionIndex: number): void {
    this.selectedAnswers[questionIndex] = optionIndex;
  }

  get canSubmit(): boolean {
    return (
      this.selectedAnswers.length > 0 &&
      this.selectedAnswers.every((answer) => answer !== null)
    );
  }

  async submit(): Promise<void> {
    if (!this.canSubmit) return;
    await this.facade.submit(this.selectedAnswers as number[]);
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

  quickAddData(answer: ReadingAnswerResult): MistakeQuickAddData {
    const day = this.facade.result()?.day ?? this.facade.exercise()?.day ?? '';
    return {
      skill: 'reading',
      source: `Reading practice ${day}: ${answer.questionText}`,
      ownAnswer: answer.options[answer.learnerAnswerIndex],
      correctAnswer: answer.options[answer.correctOptionIndex],
    };
  }
}
