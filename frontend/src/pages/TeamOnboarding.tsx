import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import '../styles/team-onboarding.css'

interface TeamMember {
  email: string
  name: string
  role: 'cs_manager' | 'ceo' | 'other'
}

const TeamOnboarding: React.FC = () => {
  const navigate = useNavigate()
  const [members, setMembers] = useState<TeamMember[]>([
    { email: '', name: '', role: 'cs_manager' }
  ])
  const [invitedCount, setInvitedCount] = useState(0)
  const [step, setStep] = useState<'form' | 'sent' | 'dashboard'>('form')

  const handleAddMember = () => {
    setMembers([...members, { email: '', name: '', role: 'cs_manager' }])
  }

  const handleRemoveMember = (idx: number) => {
    setMembers(members.filter((_, i) => i !== idx))
  }

  const handleMemberChange = (idx: number, field: keyof TeamMember, value: string) => {
    const newMembers = [...members]
    newMembers[idx][field] = value as any
    setMembers(newMembers)
  }

  const handleInvite = async () => {
    const validMembers = members.filter(m => m.email)

    try {
      const response = await fetch('/api/teams/invite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          members: validMembers
        }),
      })

      if (response.ok) {
        setInvitedCount(validMembers.length)
        setStep('sent')
        setTimeout(() => {
          navigate('/dashboard')
        }, 3000)
      }
    } catch (err) {
      console.error('Failed to invite team', err)
    }
  }

  const handleSkip = () => {
    navigate('/dashboard')
  }

  return (
    <div className="team-onboarding-container">
      {step === 'form' && (
        <>
          {/* HEADER */}
          <div className="team-header">
            <h1>👥 Invite Your Team</h1>
            <p>Let your Customer Success team see churn predictions. Collaborate on retention.</p>
          </div>

          {/* BENEFITS */}
          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">👀</div>
              <h3>Share Visibility</h3>
              <p>Everyone sees same risk scores in real-time</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🎯</div>
              <h3>Collaborate</h3>
              <p>Assign customers, track actions taken</p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">📈</div>
              <h3>Track Success</h3>
              <p>See saved customers together</p>
            </div>
          </div>

          {/* INVITE FORM */}
          <div className="invite-form-container">
            <div className="form-content">
              <h2>Who should have access?</h2>
              <p className="form-description">
                Invite your CS team, managers, and anyone involved in retention
              </p>

              <div className="member-list">
                {members.map((member, idx) => (
                  <div key={idx} className="member-row">
                    <div className="member-inputs">
                      <input
                        type="email"
                        placeholder="Email address"
                        value={member.email}
                        onChange={(e) => handleMemberChange(idx, 'email', e.target.value)}
                        className="member-email"
                      />
                      <input
                        type="text"
                        placeholder="Name (optional)"
                        value={member.name}
                        onChange={(e) => handleMemberChange(idx, 'name', e.target.value)}
                        className="member-name"
                      />
                      <select
                        value={member.role}
                        onChange={(e) => handleMemberChange(idx, 'role', e.target.value)}
                        className="member-role"
                      >
                        <option value="cs_manager">CS Manager</option>
                        <option value="ceo">CEO</option>
                        <option value="other">Other</option>
                      </select>
                    </div>

                    {members.length > 1 && (
                      <button
                        className="remove-btn"
                        onClick={() => handleRemoveMember(idx)}
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>

              <button className="add-member-btn" onClick={handleAddMember}>
                + Add Another Team Member
              </button>

              {/* ACTIONS */}
              <div className="form-actions">
                <button className="button primary large" onClick={handleInvite}>
                  Send Invites ({members.filter(m => m.email).length})
                </button>
                <button className="button secondary" onClick={handleSkip}>
                  Skip for now
                </button>
              </div>
            </div>
          </div>

          {/* TIPS */}
          <div className="tips-section">
            <h3>💡 Pro Tips</h3>
            <ul>
              <li><strong>Invite your VP Customer Success first</strong> - They see highest ROI</li>
              <li><strong>Include support team</strong> - They catch issues early</li>
              <li><strong>Permissions scale automatically</strong> - Managers can see all, CSMs see their customers</li>
              <li><strong>Mobile access included</strong> - Team can check predictions anywhere</li>
            </ul>
          </div>
        </>
      )}

      {step === 'sent' && (
        <div className="sent-state">
          <div className="sent-animation">
            <div className="checkmark">✓</div>
          </div>
          <h2>Invites Sent! 🎉</h2>
          <p>{invitedCount} team members will receive email invitations</p>
          <p className="sent-subtext">They'll be able to see churn predictions as soon as they join.</p>

          <div className="sent-info">
            <div className="info-card">
              <h3>📧 Email Sent</h3>
              <p>Invitations sent to {invitedCount} team members</p>
            </div>
            <div className="info-card">
              <h3>⏱️ Instant Access</h3>
              <p>They'll have access as soon as they sign up</p>
            </div>
            <div className="info-card">
              <h3>🔗 Dashboard</h3>
              <p>Redirecting you to your dashboard...</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default TeamOnboarding
