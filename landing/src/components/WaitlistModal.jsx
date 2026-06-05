import { useState } from 'react'

// Self-contained "Start new audit" button that opens a waitlist modal.
// Demo only: accepts an email, shows success, does not call any backend.
export default function WaitlistButton({ label = 'Start new audit', className = 'btn btn-primary btn-sm' }) {
  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState('')
  const [done, setDone] = useState(false)

  const close = () => { setOpen(false); setDone(false); setEmail('') }
  const valid = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)
  const submit = (e) => { e.preventDefault(); if (valid) setDone(true) }

  return (
    <>
      <button type="button" className={className} onClick={() => setOpen(true)}>{label}</button>
      {open && (
        <div className="modal-overlay" onClick={close} role="dialog" aria-modal="true" aria-label="Join the waitlist">
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={close} aria-label="Close">×</button>
            {!done ? (
              <>
                <div className="eyebrow" style={{ marginBottom: 12 }}>Join the waitlist</div>
                <h3 className="modal-title">Start a new audit</h3>
                <p className="modal-body">
                  This is a demo. Live audit runs are gated behind the waitlist. Drop your
                  email and we will reach out when self-serve audits open up.
                </p>
                <form onSubmit={submit} className="modal-form">
                  <input
                    className="text-input"
                    type="email"
                    inputMode="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    autoFocus
                  />
                  <button type="submit" className="btn btn-primary" disabled={!valid}>Join waitlist</button>
                </form>
              </>
            ) : (
              <>
                <div className="eyebrow" style={{ marginBottom: 12 }}>You are on the list</div>
                <h3 className="modal-title">Thanks, we will be in touch.</h3>
                <p className="modal-body">
                  We saved <span className="mono">{email}</span> for the audit waitlist. Nothing
                  else happens in this demo.
                </p>
                <button className="btn btn-secondary" onClick={close}>Close</button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
