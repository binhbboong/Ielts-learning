import { SpeakingCoachRepository } from '../data/speaking-coach.repository';
import { SpeakingCoachFacade } from './speaking-coach.facade';

describe('SpeakingCoachFacade', () => {
  it('creates, transcribes, and evaluates in separate steps', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository',
      ['create', 'transcribe', 'evaluate', 'get', 'list', 'questions'],
    );
    const processing = {
      id: 's1', questionId: 'q1', question: 'Prompt', part: 'PART_1' as const,
      audioDurationSeconds: 10, transcript: null, status: 'PROCESSING' as const,
      fluencyAndCoherence: null, lexicalResource: null,
      grammaticalRangeAndAccuracy: null, pronunciation: 'Not assessed' as const,
      errorMessage: null, createdAt: '2026-07-29T10:00:00Z',
    };
    repository.create.and.resolveTo(processing);
    repository.transcribe.and.resolveTo({ ...processing, transcript: 'My answer.' });
    repository.evaluate.and.resolveTo({ ...processing, transcript: 'My answer.',
      status: 'COMPLETED' });
    const facade = new SpeakingCoachFacade(repository);
    await facade.submit('q1', new Blob(['audio']), 10);
    expect(repository.transcribe).toHaveBeenCalledOnceWith('s1');
    expect(repository.evaluate).toHaveBeenCalledOnceWith('s1');
    expect(facade.current()?.status).toBe('COMPLETED');
  });

  it('auto-resumes processing but never auto-retries a failure', async () => {
    const repository = jasmine.createSpyObj<SpeakingCoachRepository>(
      'SpeakingCoachRepository',
      ['create', 'transcribe', 'evaluate', 'get', 'list', 'questions'],
    );
    repository.get.and.resolveTo({
      id: 's1', questionId: 'q1', question: 'Prompt', part: 'PART_1',
      audioDurationSeconds: 10, transcript: null, status: 'TRANSCRIPTION_FAILED',
      fluencyAndCoherence: null, lexicalResource: null,
      grammaticalRangeAndAccuracy: null, pronunciation: 'Not assessed',
      errorMessage: 'failed', createdAt: '2026-07-29T10:00:00Z',
    });
    const facade = new SpeakingCoachFacade(repository);
    await facade.loadSubmission('s1');
    expect(repository.transcribe).not.toHaveBeenCalled();
    expect(repository.evaluate).not.toHaveBeenCalled();
  });
});
