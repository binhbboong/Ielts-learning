export type Skill = 'reading' | 'listening' | 'writing' | 'speaking';
export type SkillStatus = 'ready' | 'generating' | 'done' | 'failed';

export interface SkillOverviewEntry {
  day: string;
  skill: Skill;
  status: SkillStatus;
  focusReference: string | null;
  targetBand: number;
  estimatedMinutes: number;
  priority: string;
  phase: string;
  rationale: string;
  generatedPromptText: string | null;
  taskType: string | null;
}

export interface CheckpointStatus {
  day: string;
  skills: Record<Skill, boolean>;
  vocabularyQuiz: boolean;
  passedCount: number;
  requiredCount: number;
  allPassed: boolean;
}

export interface DailyOverview {
  examType: string;
  week: number;
  phase: string;
  targetBand: number;
  totalMinutes: number;
  reviewMinutes: number;
  effectiveDay: string;
  checkpoint: CheckpointStatus;
  skills: SkillOverviewEntry[];
}
