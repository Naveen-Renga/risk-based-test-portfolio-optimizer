import { useState } from 'react';
import { api } from '../api';

export default function EventSimulation() {
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runDuplicateSimulation = async () => {
    setLoading(true);
    try {
      const res = await api.simulateDuplicate();
      setSimulationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runDelayedSimulation = async () => {
    setLoading(true);
    try {
      const res = await api.simulateDelayed();
      setSimulationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runOutOfOrderSimulation = async () => {
    setLoading(true);
    try {
      const res = await api.simulateOutOfOrder();
      setSimulationResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Event Simulation & State Machine Resilience</h1>
          <p>Demonstrating system safety against delayed, duplicate, and out-of-order event streams.</p>
        </div>
        <span className="synthetic-label">Resilience Engine</span>
      </div>

      {/* Interactive Scenario Buttons */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '12px' }}>
          ⚡ Run Required Edge-Case Resilience Simulations
        </h3>
        <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '20px' }}>
          Select a scenario button to inject abnormal event ordering into the assessment state machine and verify state integrity.
        </p>

        <div className="grid-3">
          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b', marginBottom: '6px' }}>
              Edge Case 1: Duplicate Event
            </h4>
            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '14px' }}>
              Injects duplicate <code>ANSWER_SUBMITTED</code> with identical <code>event_id</code>. Verified via Idempotency Key.
            </p>
            <button className="btn btn-primary btn-sm" style={{ width: '100%' }} onClick={runDuplicateSimulation} disabled={loading}>
              ▶️ Run Duplicate Event Simulation
            </button>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b', marginBottom: '6px' }}>
              Edge Case 2: Delayed Save Event
            </h4>
            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '14px' }}>
              Injects <code>ANSWER_SAVED</code> event arriving late after <code>SUBMIT_EXAM</code> state lock. Rejects state mutation.
            </p>
            <button className="btn btn-warning btn-sm" style={{ width: '100%' }} onClick={runDelayedSimulation} disabled={loading}>
              ▶️ Run Delayed Event Simulation
            </button>
          </div>

          <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b', marginBottom: '6px' }}>
              Edge Case 3: Out-of-Order Event
            </h4>
            <p style={{ fontSize: '12px', color: '#64748b', marginBottom: '14px' }}>
              Injects <code>ANSWER_SAVED</code> before <code>START_EXAM</code>. Invalid transition rule prevents uninitialized saves.
            </p>
            <button className="btn btn-danger btn-sm" style={{ width: '100%' }} onClick={runOutOfOrderSimulation} disabled={loading}>
              ▶️ Run Out-of-Order Simulation
            </button>
          </div>
        </div>
      </div>

      {/* Simulation Results Display */}
      {simulationResult && (
        <div>
          {/* Summary Status Banner */}
          <div className="card" style={{ marginBottom: '24px', borderLeft: `6px solid ${simulationResult.state_corrupted ? '#ef4444' : '#10b981'}` }}>
            <div className="flex-between">
              <div>
                <span className={`badge ${simulationResult.state_corrupted ? 'fail' : 'pass'}`} style={{ fontSize: '13px', padding: '4px 12px' }}>
                  {simulationResult.state_corrupted ? 'FAIL: State Corrupted' : 'PASS: State Preserved & Valid'}
                </span>
                <h2 style={{ fontSize: '20px', fontWeight: 800, marginTop: '8px' }}>
                  Scenario: {simulationResult.scenario_name}
                </h2>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '20px', fontWeight: 800 }}>State: <code>{simulationResult.final_state}</code></div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  Total Events: {simulationResult.total_events} | Processed: {simulationResult.processed_count} | Rejected: {simulationResult.rejected_count}
                </div>
              </div>
            </div>
          </div>

          {/* Event Execution Timeline Trace */}
          <div className="card">
            <h3 className="card-title" style={{ marginBottom: '16px' }}>
              📜 Injected Event Processing Trace & State Machine Step-by-Step Response
            </h3>

            <div className="event-timeline">
              {simulationResult.results?.map((res: any, idx: number) => {
                const isRejected = res.status.includes('REJECTED');
                const isProcessed = res.status === 'PROCESSED';

                return (
                  <div key={idx} className={`event-item ${isRejected ? 'rejected' : 'processed'}`}>
                    <div className="flex-between">
                      <div>
                        <strong>Event #{idx + 1}: {res.event_type}</strong> (ID: <code>{res.event_id}</code>)
                      </div>
                      <span className={`badge ${isProcessed ? 'pass' : 'fail'}`}>{res.status}</span>
                    </div>

                    <div style={{ fontSize: '12px', color: '#475569', marginTop: '6px' }}>
                      State Transition: <code>{res.previous_state}</code> ➔ <code>{res.new_state}</code>
                    </div>

                    <div style={{ fontSize: '12px', marginTop: '4px', fontWeight: 500, color: isRejected ? '#dc2626' : '#166534' }}>
                      System Action: {res.reason}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
