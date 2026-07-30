export const ALLOWED_SKILLS = [
  'Grammar',
  'Vocabulary',
  'Listening',
  'Reading',
  'Speaking',
  'Writing',
  'Review',
] as const;

export type Skill = (typeof ALLOWED_SKILLS)[number];

export type TaskStatus = 'NotStarted' | 'Completed' | 'Skipped';

export interface Task {
  id: number;
  dayNumber: number;
  skill: Skill;
  title: string;
  description: string;
  estimatedMinutes: number;
  status: TaskStatus;
  note: string;
  updatedAt: string;
}
