import { Injectable } from '@angular/core';
import { firstValueFrom } from 'rxjs';
import { ApiClient } from '../../core/api/api-client';
import {
  CheckpointStatus,
  DailyOverview,
  SkillOverviewEntry,
} from '../models/daily-focus.model';

function checkpoint(value: any): CheckpointStatus {
  return {
    day: value.day,
    skills: value.skills,
    vocabularyQuiz: value.vocabulary_quiz,
    passedCount: value.passed_count,
    requiredCount: value.required_count,
    allPassed: value.all_passed,
  };
}

function entry(value: any): SkillOverviewEntry {
  return {
    day: value.day,
    skill: value.skill,
    status: value.status,
    focusReference: value.focus_reference,
    targetBand: value.target_band,
    estimatedMinutes: value.estimated_minutes,
    priority: value.priority,
    phase: value.phase,
    rationale: value.rationale,
    generatedPromptText: value.generated_prompt_text ?? null,
  };
}

@Injectable({ providedIn: 'root' })
export class DailyLessonRepository {
  constructor(private readonly api: ApiClient) {}

  async getOverview(): Promise<DailyOverview> {
    const value = await firstValueFrom(
      this.api.get<any>('/api/daily-lesson/overview'),
    );
    return {
      examType: value.exam_type,
      week: value.week,
      phase: value.phase,
      targetBand: value.target_band,
      totalMinutes: value.total_minutes,
      reviewMinutes: value.review_minutes,
      effectiveDay: value.effective_day,
      checkpoint: checkpoint(value.checkpoint),
      skills: (value.skills ?? []).map(entry),
    };
  }

  async retry(skill: string, day: string): Promise<SkillOverviewEntry> {
    return entry(
      await firstValueFrom(
        this.api.post<any>(`/api/daily-lesson/${skill}/retry?day=${day}`, {}),
      ),
    );
  }
}
