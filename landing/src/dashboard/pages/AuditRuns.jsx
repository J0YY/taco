import { AUDIT_RUNS, tone } from '../../data/stub.js'

export default function AuditRuns() {
  return (
    <>
      <div className="page-head">
        <h2>Audit Runs</h2>
        <p>Each run executes the policy against a task suite under counterfactual perturbations, emits failure certificates, records internal traces, and issues a binder.</p>
      </div>

      <div className="card card-flush" style={{ marginBottom: 24 }}>
        <table className="table">
          <thead>
            <tr>
              <th className="mono">run id</th>
              <th className="mono">policy</th>
              <th>task suite</th>
              <th>result</th>
              <th>certs</th>
              <th>traces</th>
              <th>binder</th>
            </tr>
          </thead>
          <tbody>
            {AUDIT_RUNS.map((r) => (
              <tr key={r.id}>
                <td className="mono">{r.id}</td>
                <td className="mono">{r.policy}</td>
                <td>{r.taskSuite}</td>
                <td><span className="status-pill"><span className={`dot ${tone[r.resultTone].dot}`} /> {r.result}</span></td>
                <td className="mono">{r.certificates}</td>
                <td className="mono">{r.traces}</td>
                <td className="text-ok">{r.binder}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="terminal">
        <div className="terminal-bar"><span className="tcap" /><span className="tcap" /><span className="tcap" /><span style={{ marginLeft: 6 }}>audit_2026_06_04_001 · log</span></div>
        <div className="terminal-body" style={{ lineHeight: 1.9 }}>
          <div><span className="text-mute">[00:00]</span> connect policy skild_vla_warehouse_v1 + warehouse_task_suite</div>
          <div><span className="text-mute">[00:11]</span> generate counterfactual scenarios … 64 candidates</div>
          <div><span className="text-mute">[02:38]</span> validate in simulation … <span className="text-ok">3 confirmed</span>, 12 non-reproducing, 49 native-pass</div>
          <div><span className="text-mute">[03:04]</span> emit failure certificates … <span className="text-ok">FR-001, FR-002, FR-003</span></div>
          <div><span className="text-mute">[03:20]</span> record internal traces … 9 traces (success / failure / mitigated × 3)</div>
          <div><span className="text-mute">[03:51]</span> issue conditional certificate … <span className="text-warn">conditional_pass</span></div>
          <div><span className="text-mute">[03:52]</span> binder issued ✓</div>
        </div>
      </div>
    </>
  )
}
