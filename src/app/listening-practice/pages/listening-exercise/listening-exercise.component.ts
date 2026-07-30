import { ChangeDetectionStrategy, Component, OnInit, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  MistakeQuickAddComponent,
  MistakeQuickAddData,
} from '../../../mistakes/pages/quick-add/mistake-quick-add.component';
import { ListeningAnswerResult } from '../../models/listening-exercise.model';
import { ListeningPracticeFacade } from '../../state/listening-practice.facade';

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

@Component({
  selector: 'app-listening-exercise',
  standalone: true,
  imports: [RouterLink, MistakeQuickAddComponent],
  templateUrl: './listening-exercise.component.html',
  styleUrl: './listening-exercise.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListeningExerciseComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  readonly facade = inject(ListeningPracticeFacade);
  day = '';
  selectedAnswers: (number | null)[] = [];
  openQuickAddIndex: number | null = null;

  async ngOnInit(): Promise<void> {
    this.day = this.route.snapshot.paramMap.get('day') ?? todayIso();
    await this.facade.load(this.day);
    const questionCount = this.facade.exercise()?.questions.length ?? 0;
    this.selectedAnswers = new Array(questionCount).fill(null);
  }

  get audioUrl(): string {
    return this.facade.audioUrl(this.day);
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

  quickAddData(answer: ListeningAnswerResult): MistakeQuickAddData {
    return {
      skill: 'listening',
      source: `Listening practice ${this.day}: ${answer.questionText}`,
      ownAnswer: answer.options[answer.learnerAnswerIndex],
      correctAnswer: answer.options[answer.correctOptionIndex],
    };
  }
}
