export type SpeakingPart = 'PART_1' | 'PART_2' | 'PART_3';

export interface SpeakingQuestion {
  id: string;
  part: SpeakingPart;
  prompt: string;
}
