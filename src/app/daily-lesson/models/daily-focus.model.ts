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
}

export interface DailyOverview {
  examType: string;
  week: number;
  phase: string;
  targetBand: number;
  totalMinutes: number;
  reviewMinutes: number;
  skills: SkillOverviewEntry[];
}
