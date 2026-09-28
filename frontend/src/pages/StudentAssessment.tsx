import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../AuthContext';
import { api } from '../api';

export default function StudentAssessment() {
  const { user } = useAuth();
  const [assessments, setAssessments] = useState<any[]>([]);
  const [selectedAssessment, setSelectedAssessment] = useState<any>(null);
  const [step, setStep] = useState<'list' | 'instructions' | 'exam' | 'result'>('list');

  // Exam state
  const [submissionId, setSubmissionId] = useState<number | null>(null);
  const [questions, setQuestions] = useState<any[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [timeLeft, setTimeLeft] = useState(0);
  const [autosaveStatus, setAutosaveStatus] = useState<'saved' | 'saving' | 'queued' | 'syncing' | 'idle'>('idle');
  const [isNetworkConnected, setIsNetworkConnected] = useState(true);
  const [resultData, setResultData] = useState<any>(null);

  // BUG 6 FIX: Queue unsaved offline answers locally
  const offlineQueueRef = useRef<Record<number, string>>({});
  const [pendingQueueCount, setPendingQueueCount] = useState(0);

  useEffect(() => {
    loadAssessments();
  }, []);

  useEffect(() => {
    let timer: any;
    if (step === 'exam' && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            handleSubmit();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [step, timeLeft]);

  // BUG 6 FIX: Auto-flush offline queue whenever network switches from disconnected to connected
  useEffect(() => {
    if (isNetworkConnected && submissionId && user && Object.keys(offlineQueueRef.current).length > 0) {
      flushOfflineQueue();
    }
  }, [isNetworkConnected]);

  const loadAssessments = async () => {
    try {
      const data = await api.getAssessments();
      setAssessments(data);
    } catch (err) {
      console.error(err);
    }
  };

  const selectAssessment = (a: any) => {
    setSelectedAssessment(a);
    setStep('instructions');
  };

  const startExam = async () => {
    if (!user || !selectedAssessment) return;
    try {
      // BUG 7 FIX: Pass user.token to startAssessment
      const [qs, sub] = await Promise.all([
        api.getQuestions(selectedAssessment.id),
        api.startAssessment(user.user_id, selectedAssessment.id, user.token),
      ]);
      setQuestions(qs);
      setSubmissionId(sub.submission_id);
      setTimeLeft(selectedAssessment.duration_minutes * 60);
      setAnswers({});
      offlineQueueRef.current = {};
      setPendingQueueCount(0);
      setCurrentIndex(0);
      setStep('exam');
    } catch (err: any) {
      alert(err.message || 'Error starting assessment');
    }
  };

  const flushOfflineQueue = async () => {
    if (!submissionId || !user) return;
    const queue = { ...offlineQueueRef.current };
    const queueEntries = Object.entries(queue);
    if (queueEntries.length === 0) return;

    setAutosaveStatus('syncing');
    try {
      for (const [qIdStr, opt] of queueEntries) {
        const qId = Number(qIdStr);
        await api.saveAnswer(submissionId, qId, opt, user.token);
        delete offlineQueueRef.current[qId];
      }
      setPendingQueueCount(Object.keys(offlineQueueRef.current).length);
      setAutosaveStatus('saved');
      setTimeout(() => setAutosaveStatus('idle'), 2500);
    } catch (err) {
      console.error('Failed to flush offline queue:', err);
      setAutosaveStatus('queued');
    }
  };

  const handleSelectAnswer = async (questionId: number, option: string) => {
    const newAnswers = { ...answers, [questionId]: option };
    setAnswers(newAnswers);

    if (!isNetworkConnected) {
      // BUG 6 FIX: Queue locally when network is disconnected
      offlineQueueRef.current[questionId] = option;
      const count = Object.keys(offlineQueueRef.current).length;
      setPendingQueueCount(count);
      setAutosaveStatus('queued');
      return;
    }

    if (submissionId && user) {
      setAutosaveStatus('saving');
      try {
        await api.saveAnswer(submissionId, questionId, option, user.token);
        setAutosaveStatus('saved');
        setTimeout(() => setAutosaveStatus('idle'), 2000);
      } catch (err) {
        console.error('Autosave failed, queuing locally:', err);
        offlineQueueRef.current[questionId] = option;
        setPendingQueueCount(Object.keys(offlineQueueRef.current).length);
        setAutosaveStatus('queued');
      }
    }
  };

  const handleToggleNetwork = () => {
    const nextState = !isNetworkConnected;
    setIsNetworkConnected(nextState);
  };

  const handleSubmit = async () => {
    if (!submissionId || !user) return;
    if (!isNetworkConnected) {
      alert('Cannot submit while network is disconnected! Please restore network connection first.');
      return;
    }

    // Flush any pending queued answers before final submit
    if (Object.keys(offlineQueueRef.current).length > 0) {
      await flushOfflineQueue();
    }

    try {
      await api.submitAssessment(submissionId, user.token);
      const fullSub = await api.getSubmission(submissionId, user.token);
      setResultData(fullSub);
      setStep('result');
    } catch (err: any) {
      alert(err.message || 'Submission failed');
    }
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // STEP 1: Assessment List
  if (step === 'list') {
    return (
      <div>
        <div className="page-header">
          <h1>Online Assessment Portal</h1>
          <p>Select an assessment to begin your test session.</p>
        </div>

        <div className="grid-3">
          {assessments.map(a => (
            <div key={a.id} className="assessment-card" onClick={() => selectAssessment(a)}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>📝</div>
              <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>{a.title}</h3>
              <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '16px' }}>{a.description}</p>
              <div className="flex-between" style={{ fontSize: '12px', color: '#475569', borderTop: '1px solid #e2e8f0', paddingTop: '12px' }}>
                <span>⏱️ {a.duration_minutes} mins</span>
                <span>❓ {a.total_questions} Questions</span>
                <span>🎯 Pass: {a.passing_score}%</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // STEP 2: Instructions
  if (step === 'instructions') {
    return (
      <div style={{ maxWidth: '700px', margin: '0 auto' }}>
        <div className="card">
          <div className="card-header">
            <h2 style={{ fontSize: '20px', fontWeight: 700 }}>Assessment Instructions</h2>
            <button className="btn btn-secondary btn-sm" onClick={() => setStep('list')}>← Back</button>
          </div>

          <div style={{ marginBottom: '20px', padding: '16px', background: '#f8fafc', borderRadius: '10px' }}>
            <h3 style={{ fontSize: '16px', color: '#1e293b' }}>{selectedAssessment?.title}</h3>
            <p style={{ color: '#64748b', fontSize: '13px', marginTop: '4px' }}>{selectedAssessment?.description}</p>
          </div>

          <div style={{ fontSize: '14px', lineHeight: 1.8, marginBottom: '24px' }}>
            <h4 style={{ fontWeight: 700, marginBottom: '8px' }}>Important Rules & Workflow:</h4>
            <ul style={{ paddingLeft: '20px', color: '#475569' }}>
              <li><strong>Time Limit:</strong> {selectedAssessment?.duration_minutes} minutes. Timer starts immediately upon launch.</li>
              <li><strong>Autosave:</strong> Every answer selection is automatically saved to the cloud.</li>
              <li><strong>Network Resilience & Offline Resync:</strong> If network drops, answers are safely queued locally and automatically synchronized upon reconnect.</li>
              <li><strong>Ownership & Security:</strong> All exam data is strictly tied to your student account context.</li>
              <li><strong>Final Submission:</strong> Click "Submit Assessment" when complete. Auto-submits on timer expiry.</li>
            </ul>
          </div>

          <div className="flex-between">
            <button className="btn btn-secondary" onClick={() => setStep('list')}>Cancel</button>
            <button className="btn btn-primary" onClick={startExam}>🚀 Start Assessment Now</button>
          </div>
        </div>
      </div>
    );
  }

  // STEP 3: Question Page (Exam Workflow)
  if (step === 'exam') {
    const currentQ = questions[currentIndex];
    const answeredCount = Object.keys(answers).length;

    return (
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Network Banner */}
        <div className={`network-banner ${isNetworkConnected ? 'connected' : 'disconnected'}`}>
          {isNetworkConnected ? (
            <span>🟢 Network Status: Connected (Autosave Active)</span>
          ) : (
            <span>🔴 Network Status: DISCONNECTED (Simulating Network Interruption — {pendingQueueCount} answers queued)</span>
          )}
          <button
            className="btn btn-sm btn-secondary"
            style={{ marginLeft: '12px' }}
            onClick={handleToggleNetwork}
          >
            Simulate {isNetworkConnected ? 'Network Disconnect' : 'Network Reconnect & Resync'}
          </button>
        </div>

        {/* Exam Header */}
        <div className="card" style={{ marginBottom: '16px', padding: '16px 20px' }}>
          <div className="flex-between">
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: 700 }}>{selectedAssessment?.title}</h3>
              <span className="autosave-indicator">
                {autosaveStatus === 'saving' && '⏳ Autosaving answer...'}
                {autosaveStatus === 'syncing' && '🔄 Resynchronizing offline queued answers to cloud...'}
                {autosaveStatus === 'queued' && `⚠️ Offline Mode: ${pendingQueueCount} answers queued locally`}
                {autosaveStatus === 'saved' && '✅ All answers synchronized & saved'}
                {autosaveStatus === 'idle' && `Answers: ${answeredCount}/${questions.length} saved`}
              </span>
            </div>

            <div className={`timer-display ${timeLeft < 300 ? 'critical' : timeLeft < 600 ? 'warning' : ''}`}>
              ⏱️ {formatTime(timeLeft)}
            </div>
          </div>
        </div>

        {/* Question Area */}
        {currentQ && (
          <div className="question-card">
            <div className="flex-between" style={{ marginBottom: '12px' }}>
              <span className="badge info">Question {currentIndex + 1} of {questions.length}</span>
              <span style={{ fontSize: '12px', color: '#64748b' }}>Marks: {currentQ.marks}</span>
            </div>

            <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '20px' }}>{currentQ.question_text}</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {['A', 'B', 'C', 'D'].map(optKey => {
                const optText = currentQ[`option_${optKey.toLowerCase()}`];
                const isSelected = answers[currentQ.id] === optKey;
                return (
                  <button
                    key={optKey}
                    className={`option-btn ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelectAnswer(currentQ.id, optKey)}
                  >
                    <strong>{optKey}.</strong> {optText}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Question Navigation & Submit */}
        <div className="card flex-between">
          <div className="flex-gap">
            <button
              className="btn btn-secondary"
              disabled={currentIndex === 0}
              onClick={() => setCurrentIndex(prev => prev - 1)}
            >
              ← Previous
            </button>
            <button
              className="btn btn-secondary"
              disabled={currentIndex === questions.length - 1}
              onClick={() => setCurrentIndex(prev => prev + 1)}
            >
              Next →
            </button>
          </div>

          {/* Question Palette */}
          <div className="flex-gap" style={{ overflowX: 'auto', maxWidth: '300px' }}>
            {questions.map((q, idx) => (
              <button
                key={q.id}
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '6px',
                  border: currentIndex === idx ? '2px solid #3b82f6' : '1px solid #cbd5e1',
                  background: answers[q.id] ? '#3b82f6' : '#f8fafc',
                  color: answers[q.id] ? 'white' : '#475569',
                  fontWeight: 600,
                  fontSize: '11px',
                  cursor: 'pointer',
                }}
                onClick={() => setCurrentIndex(idx)}
              >
                {idx + 1}
              </button>
            ))}
          </div>

          <button className="btn btn-success" onClick={handleSubmit}>
            ✅ Submit Assessment
          </button>
        </div>
      </div>
    );
  }

  // STEP 4: Result Page
  if (step === 'result' && resultData) {
    const isPassed = resultData.percentage >= (selectedAssessment?.passing_score || 50);

    return (
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        <div className="card" style={{ textAlign: 'center', padding: '36px' }}>
          <div style={{ fontSize: '56px', marginBottom: '12px' }}>{isPassed ? '🎉' : '⚠️'}</div>
          <h1 style={{ fontSize: '24px', fontWeight: 800 }}>Assessment Completed</h1>
          <p style={{ color: '#64748b', fontSize: '14px', marginBottom: '24px' }}>{selectedAssessment?.title}</p>

          <div style={{ display: 'inline-flex', gap: '24px', background: '#f8fafc', padding: '20px 32px', borderRadius: '12px', marginBottom: '28px' }}>
            <div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: '#0f172a' }}>{resultData.score} / {resultData.total_marks}</div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>Score</div>
            </div>
            <div style={{ borderLeft: '1px solid #e2e8f0' }} />
            <div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: isPassed ? '#16a34a' : '#dc2626' }}>{resultData.percentage}%</div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>Percentage</div>
            </div>
            <div style={{ borderLeft: '1px solid #e2e8f0' }} />
            <div>
              <div style={{ fontSize: '28px', fontWeight: 800, color: isPassed ? '#16a34a' : '#dc2626' }}>
                {isPassed ? 'PASSED' : 'FAILED'}
              </div>
              <div style={{ fontSize: '12px', color: '#64748b' }}>Status</div>
            </div>
          </div>

          {/* Detailed Question Review */}
          <h3 style={{ textAlign: 'left', fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Detailed Answer Breakdown</h3>
          <div style={{ textAlign: 'left', display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
            {resultData.questions?.map((q: any, i: number) => (
              <div key={q.id} style={{ padding: '14px', borderRadius: '8px', background: q.is_correct ? '#f0fdf4' : '#fef2f2', border: `1px solid ${q.is_correct ? '#bbf7d0' : '#fecaca'}` }}>
                <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px' }}>
                  {i + 1}. {q.question_text}
                </div>
                <div style={{ fontSize: '12px', color: '#475569' }}>
                  Your Answer: <strong>{q.user_answer || 'None'}</strong> | Correct Answer: <strong>{q.correct_option}</strong> ({q.is_correct ? 'Correct ✅' : 'Incorrect ❌'})
                </div>
              </div>
            ))}
          </div>

          <button className="btn btn-primary" onClick={() => setStep('list')}>Return to Assessments</button>
        </div>
      </div>
    );
  }

  return null;
}
