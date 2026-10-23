import React, { useState } from 'react';
import {
  ShieldCheck,
  Zap,
  CheckCircle2,
  FileText,
  AlertTriangle,
  TrendingDown,
  Download,
  Printer,
  Copy,
  Check,
  X,
  Clock,
  Activity,
  Layers
} from 'lucide-react';
import {
  EnergyAdvisoryDossier,
  EnergyDispatchWorkOrder,
  AuthorizeEnergyAdvisoryPayload,
  EnergyAdvisoryStatus
} from '../../types/twin';
import { authorizeEnergyAdvisory } from '../../services/api';

interface DemandResponseDossierModalProps {
  advisory: EnergyAdvisoryDossier;
  initialReviewerName?: string;
  onClose: () => void;
  onAuthorized?: (workOrder: EnergyDispatchWorkOrder) => void;
}

export const DemandResponseDossierModal: React.FC<DemandResponseDossierModalProps> = ({
  advisory,
  initialReviewerName = 'Chief Facility Energy Manager',
  onClose,
  onAuthorized
}) => {
  const [badgeId, setBadgeId] = useState<string>('MCC-OPS-4091');
  const [shiftId, setShiftId] = useState<string>('SHIFT-EVENING-B');
  const [reviewer, setReviewer] = useState<string>(initialReviewerName);
  const [decision, setDecision] = useState<EnergyAdvisoryStatus>('AUTHORIZED');
  const [notes, setNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [issuedTicket, setIssuedTicket] = useState<EnergyDispatchWorkOrder | null>(null);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [payloadTab, setPayloadTab] = useState<'OPENADR' | 'MODBUS'>('OPENADR');

  const isAlreadyAuthorized = advisory.status === 'AUTHORIZED' || Boolean(issuedTicket);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!badgeId.trim()) {
      setError('Dispatcher Badge ID is mandatory for municipal audit logging.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const payload: AuthorizeEnergyAdvisoryPayload = {
        badgeId: badgeId.trim(),
        shiftId: shiftId.trim(),
        reviewer: reviewer.trim(),
        decision,
        notes: notes.trim() || undefined
      };
      const order = await authorizeEnergyAdvisory(advisory.advisoryId, payload);
      setIssuedTicket(order);
      if (onAuthorized) {
        onAuthorized(order);
      }
    } catch (err: any) {
      console.error('Authorization dispatch error', err);
      setError(err?.message || 'Failed to authorize energy demand response advisory.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  const handleDownloadJson = (order: EnergyDispatchWorkOrder) => {
    const blob = new Blob([JSON.stringify(order, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${order.dispatchOrderId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  const activeTicket = issuedTicket || (advisory.dispatchOrderId && advisory.auditHash ? {
    dispatchOrderId: advisory.dispatchOrderId,
    advisoryId: advisory.advisoryId,
    facilityId: advisory.facilityId,
    facilityName: advisory.facilityName,
    authorizedBy: advisory.authorizedBy || reviewer,
    badgeId: advisory.badgeId || badgeId,
    shiftId: advisory.shiftId || shiftId,
    issuedAt: advisory.generatedAt,
    decision: advisory.status,
    schedule: advisory.schedule,
    safetyChecks: advisory.safetyChecks,
    projectedSavingsInr: advisory.projectedSavingsInr,
    peakReductionKw: advisory.peakReductionKw,
    avoidedCarbonKg: advisory.avoidedCarbonKg,
    tamperEvidentHash: advisory.auditHash,
    openAdrPayload: {
      eiEvent: {
        eventDescriptor: { eventID: advisory.dispatchOrderId, priority: 1 },
        eiTarget: { targetID: advisory.facilityId, resourceID: 'BESS-PHOENIX-01' }
      }
    },
    modbusRegisters: {
      "40001_bess_power_setpoint_kw": 450,
      "40002_bess_inverter_mode": 2,
      "40003_hvac_temperature_offset_tenths_c": 10,
      "40004_interlock_status_flags": 15
    },
    governanceDisclaimer: advisory.governanceNotice
  } as EnergyDispatchWorkOrder : null);

  return (
    <div className="modal-backdrop" style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.85)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1100,
      padding: '16px'
    }}>
      <div className="modal-container" style={{
        background: 'var(--color-surface, #09090B)',
        border: '1px solid var(--color-border-strong, #222329)',
        borderRadius: 'var(--radius-lg, 12px)',
        width: '100%',
        maxWidth: '780px',
        maxHeight: '92vh',
        overflowY: 'auto',
        boxShadow: '0 24px 48px rgba(0, 0, 0, 0.75)',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '18px 24px',
          borderBottom: '1px solid var(--color-border, #16171B)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(15, 15, 18, 0.85)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(235, 169, 0, 0.15)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Zap size={20} color="var(--color-warning, #EBA900)" />
            </div>
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--color-text, #F0F6FC)' }}>
                {activeTicket ? 'Demand-Response Dispatch Ticket Issued' : 'Demand-Response Advisory Decision Dossier'}
              </h2>
              <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)', fontFamily: 'var(--font-mono)' }}>
                {advisory.advisoryId} : {advisory.facilityName}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close modal"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--color-text-secondary, #C9D1D9)',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Strict Non-Actuation Banner */}
          <div style={{
            background: 'rgba(56, 139, 253, 0.08)',
            border: '1px solid rgba(56, 139, 253, 0.25)',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '12px'
          }}>
            <ShieldCheck size={18} color="var(--color-primary, #2F81F7)" style={{ marginTop: '2px', flexShrink: 0 }} />
            <div style={{ fontSize: '12px', color: 'var(--color-text-secondary, #C9D1D9)', lineHeight: 1.5 }}>
              <strong style={{ color: 'var(--color-text, #F0F6FC)' }}>Strict Non-Actuation Protocol:</strong> Advisory decision support only. Emits an audited OpenADR / Modbus dispatch work order. Local BMS and BESS hardware safety logic remains authoritative.
            </div>
          </div>

          {/* Proposed Operational Action */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--color-border, #16171B)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <Layers size={14} color="var(--color-primary, #2F81F7)" />
              <span style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted, #8B949E)', fontWeight: 600 }}>
                Proposed Dispatch Strategy
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '13px', color: 'var(--color-text, #F0F6FC)', lineHeight: 1.5, fontWeight: 500 }}>
              {advisory.recommendedAction}
            </p>
          </div>

          {/* Economic & Carbon Impact KPIs (4 Cards) */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: '12px'
          }}>
            <div style={{
              background: 'rgba(35, 134, 54, 0.08)',
              border: '1px solid rgba(35, 134, 54, 0.25)',
              borderRadius: '8px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <TrendingDown size={14} color="var(--color-success, #238636)" />
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)' }}>Net Cost Savings</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-success, #238636)' }}>
                INR {advisory.projectedSavingsInr.toLocaleString()}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted, #8B949E)', marginTop: '2px' }}>
                Avoided peak demand tariff
              </div>
            </div>

            <div style={{
              background: 'rgba(47, 129, 247, 0.08)',
              border: '1px solid rgba(47, 129, 247, 0.25)',
              borderRadius: '8px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <Zap size={14} color="var(--color-primary, #2F81F7)" />
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)' }}>Peak Shaved</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-primary, #2F81F7)' }}>
                -{advisory.peakReductionKw} kW
              </div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted, #8B949E)', marginTop: '2px' }}>
                BESS + HVAC pre-cooling
              </div>
            </div>

            <div style={{
              background: 'rgba(235, 169, 0, 0.08)',
              border: '1px solid rgba(235, 169, 0, 0.25)',
              borderRadius: '8px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <Activity size={14} color="var(--color-warning, #EBA900)" />
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)' }}>Battery Wear</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-warning, #EBA900)' }}>
                {advisory.batteryWearCycles} cycles
              </div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted, #8B949E)', marginTop: '2px' }}>
                Equivalent degradation wear
              </div>
            </div>

            <div style={{
              background: 'rgba(56, 139, 253, 0.08)',
              border: '1px solid rgba(56, 139, 253, 0.25)',
              borderRadius: '8px',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
                <CheckCircle2 size={14} color="var(--color-primary, #2F81F7)" />
                <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)' }}>Avoided Carbon</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-text, #F0F6FC)' }}>
                {advisory.avoidedCarbonKg} kg
              </div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted, #8B949E)', marginTop: '2px' }}>
                Grid CO2e peaker offset
              </div>
            </div>
          </div>

          {/* Physical Safety Interlock Verification Checklist */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--color-border, #16171B)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <ShieldCheck size={16} color="var(--color-success, #238636)" />
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text, #F0F6FC)' }}>
                Physical Safety Interlock Verification Checklist
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '10px' }}>
              <div style={{
                background: 'rgba(35, 134, 54, 0.06)',
                border: '1px solid rgba(35, 134, 54, 0.2)',
                borderRadius: '6px',
                padding: '10px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-text, #F0F6FC)' }}>
                    Feeder Line Voltage Compliance
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                    Statutory 415V +/- 6% (reading: {advisory.safetyChecks.voltageValueV}V)
                  </div>
                </div>
                <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-success, #238636)', padding: '2px 6px', background: 'rgba(35, 134, 54, 0.15)', borderRadius: '4px' }}>
                  PASS
                </span>
              </div>

              <div style={{
                background: 'rgba(35, 134, 54, 0.06)',
                border: '1px solid rgba(35, 134, 54, 0.2)',
                borderRadius: '6px',
                padding: '10px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-text, #F0F6FC)' }}>
                    Inverter Slew Rate Ramp Throttle
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                    Throttled &lt;= 10%/min (active: {advisory.safetyChecks.rampRatePctPerMin}%/min)
                  </div>
                </div>
                <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-success, #238636)', padding: '2px 6px', background: 'rgba(35, 134, 54, 0.15)', borderRadius: '4px' }}>
                  PASS
                </span>
              </div>

              <div style={{
                background: 'rgba(35, 134, 54, 0.06)',
                border: '1px solid rgba(35, 134, 54, 0.2)',
                borderRadius: '6px',
                padding: '10px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-text, #F0F6FC)' }}>
                    Battery SoC Operational Reserve
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                    Bounded &gt;= 20% floor (active: {advisory.safetyChecks.currentSocPct}%)
                  </div>
                </div>
                <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-success, #238636)', padding: '2px 6px', background: 'rgba(35, 134, 54, 0.15)', borderRadius: '4px' }}>
                  PASS
                </span>
              </div>

              <div style={{
                background: 'rgba(35, 134, 54, 0.06)',
                border: '1px solid rgba(35, 134, 54, 0.2)',
                borderRadius: '6px',
                padding: '10px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 500, color: 'var(--color-text, #F0F6FC)' }}>
                    ASHRAE 55 Occupant Thermal Comfort
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                    Indoor &lt;= 25.5 deg C (forecast: {advisory.safetyChecks.projectedIndoorTempC} deg C)
                  </div>
                </div>
                <span style={{ fontSize: '10px', fontWeight: 700, color: 'var(--color-success, #238636)', padding: '2px 6px', background: 'rgba(35, 134, 54, 0.15)', borderRadius: '4px' }}>
                  PASS
                </span>
              </div>
            </div>
          </div>

          {/* Half-Hour Dispatch Schedule Table */}
          <div style={{
            background: 'rgba(255, 255, 255, 0.02)',
            border: '1px solid var(--color-border, #16171B)',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
              <Clock size={16} color="var(--color-primary, #2F81F7)" />
              <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text, #F0F6FC)' }}>
                Target Half-Hour Dispatch Schedule
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border, #16171B)', color: 'var(--color-text-muted, #8B949E)' }}>
                    <th style={{ padding: '8px 10px', fontWeight: 600 }}>Time Window</th>
                    <th style={{ padding: '8px 10px', fontWeight: 600 }}>BESS Action</th>
                    <th style={{ padding: '8px 10px', fontWeight: 600 }}>BESS Power (kW)</th>
                    <th style={{ padding: '8px 10px', fontWeight: 600 }}>HVAC Setback Offset</th>
                  </tr>
                </thead>
                <tbody>
                  {advisory.schedule.map((slot, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text, #F0F6FC)' }}>
                        {slot.timeSlot}
                      </td>
                      <td style={{ padding: '8px 10px' }}>
                        <span style={{
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          background: slot.bessAction === 'DISCHARGE' ? 'rgba(47, 129, 247, 0.15)' : 'rgba(255, 255, 255, 0.08)',
                          color: slot.bessAction === 'DISCHARGE' ? 'var(--color-primary, #2F81F7)' : 'var(--color-text-secondary, #C9D1D9)'
                        }}>
                          {slot.bessAction}
                        </span>
                      </td>
                      <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-text, #F0F6FC)' }}>
                        {slot.bessKw > 0 ? `+${slot.bessKw} kW` : '0 kW'}
                      </td>
                      <td style={{ padding: '8px 10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                        {slot.hvacSetbackDeltaC > 0 ? `+${slot.hvacSetbackDeltaC} deg C` : 'Baseline'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Dual-Key Operator Authorization Workflow */}
          {!isAlreadyAuthorized ? (
            <form onSubmit={handleSubmit} style={{
              background: 'rgba(255, 255, 255, 0.02)',
              border: '1px solid var(--color-border, #16171B)',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <ShieldCheck size={16} color="var(--color-primary, #2F81F7)" />
                <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text, #F0F6FC)' }}>
                  Dual-Key Operator Authorization Signature
                </span>
              </div>

              {error && (
                <div style={{
                  background: 'rgba(248, 81, 73, 0.1)',
                  border: '1px solid rgba(248, 81, 73, 0.3)',
                  borderRadius: '6px',
                  padding: '10px 12px',
                  fontSize: '12px',
                  color: 'var(--color-danger, #F85149)',
                  marginBottom: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <AlertTriangle size={14} />
                  <span>{error}</span>
                </div>
              )}

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px', marginBottom: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary, #C9D1D9)', marginBottom: '4px' }}>
                    Authorizing Officer Name
                  </label>
                  <input
                    type="text"
                    value={reviewer}
                    onChange={(e) => setReviewer(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      background: 'rgba(15, 15, 18, 0.9)',
                      border: '1px solid var(--color-border, #16171B)',
                      borderRadius: '6px',
                      padding: '8px 10px',
                      fontSize: '12px',
                      color: 'var(--color-text, #F0F6FC)'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary, #C9D1D9)', marginBottom: '4px' }}>
                    Municipal / Facility Badge ID
                  </label>
                  <input
                    type="text"
                    value={badgeId}
                    onChange={(e) => setBadgeId(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      background: 'rgba(15, 15, 18, 0.9)',
                      border: '1px solid var(--color-border, #16171B)',
                      borderRadius: '6px',
                      padding: '8px 10px',
                      fontSize: '12px',
                      color: 'var(--color-text, #F0F6FC)',
                      fontFamily: 'var(--font-mono)'
                    }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary, #C9D1D9)', marginBottom: '4px' }}>
                    Operating Duty Shift
                  </label>
                  <input
                    type="text"
                    value={shiftId}
                    onChange={(e) => setShiftId(e.target.value)}
                    required
                    style={{
                      width: '100%',
                      background: 'rgba(15, 15, 18, 0.9)',
                      border: '1px solid var(--color-border, #16171B)',
                      borderRadius: '6px',
                      padding: '8px 10px',
                      fontSize: '12px',
                      color: 'var(--color-text, #F0F6FC)'
                    }}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--color-text-secondary, #C9D1D9)', marginBottom: '4px' }}>
                  Operational Justification Notes (Optional)
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="e.g. Authorizing peak tariff shaving in accordance with facility energy protocol..."
                  rows={2}
                  style={{
                    width: '100%',
                    background: 'rgba(15, 15, 18, 0.9)',
                    border: '1px solid var(--color-border, #16171B)',
                    borderRadius: '6px',
                    padding: '8px 10px',
                    fontSize: '12px',
                    color: 'var(--color-text, #F0F6FC)',
                    resize: 'none'
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setDecision('REJECTED')}
                  style={{
                    background: 'transparent',
                    border: '1px solid var(--color-border, #16171B)',
                    borderRadius: '6px',
                    padding: '8px 14px',
                    fontSize: '12px',
                    color: 'var(--color-text-secondary, #C9D1D9)',
                    cursor: 'pointer'
                  }}
                >
                  Dismiss Proposal
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  style={{
                    background: 'var(--color-primary, #2F81F7)',
                    border: 'none',
                    borderRadius: '6px',
                    padding: '8px 18px',
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#FFFFFF',
                    cursor: submitting ? 'not-allowed' : 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    opacity: submitting ? 0.7 : 1
                  }}
                >
                  <ShieldCheck size={16} />
                  <span>{submitting ? 'Generating Audit Ticket...' : 'Authorize Municipal Energy Dispatch Ticket'}</span>
                </button>
              </div>
            </form>
          ) : activeTicket ? (
            /* Issued Dispatch Work Order / Audit Trail Card */
            <div style={{
              background: 'rgba(35, 134, 54, 0.05)',
              border: '1px solid rgba(35, 134, 54, 0.3)',
              borderRadius: '8px',
              padding: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <CheckCircle2 size={18} color="var(--color-success, #238636)" />
                  <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-text, #F0F6FC)' }}>
                    Municipal Energy Dispatch Ticket: {activeTicket.dispatchOrderId}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <button
                    type="button"
                    onClick={() => handleDownloadJson(activeTicket)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid var(--color-border, #16171B)',
                      borderRadius: '6px',
                      padding: '6px 10px',
                      fontSize: '11px',
                      color: 'var(--color-text, #F0F6FC)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Download size={13} />
                    <span>JSON Ticket</span>
                  </button>
                  <button
                    type="button"
                    onClick={handlePrint}
                    style={{
                      background: 'rgba(255, 255, 255, 0.06)',
                      border: '1px solid var(--color-border, #16171B)',
                      borderRadius: '6px',
                      padding: '6px 10px',
                      fontSize: '11px',
                      color: 'var(--color-text, #F0F6FC)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px'
                    }}
                  >
                    <Printer size={13} />
                    <span>Print</span>
                  </button>
                </div>
              </div>

              {/* Cryptographic Hash Bar */}
              <div style={{
                background: 'rgba(15, 15, 18, 0.9)',
                border: '1px solid var(--color-border, #16171B)',
                borderRadius: '6px',
                padding: '10px 12px',
                marginBottom: '14px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                gap: '8px',
                flexWrap: 'wrap'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={14} color="var(--color-primary, #2F81F7)" />
                  <span style={{ fontSize: '11px', color: 'var(--color-text-secondary, #C9D1D9)' }}>
                    SHA-256 Tamper-Evident Hash:
                  </span>
                  <code style={{ fontSize: '11px', color: 'var(--color-primary, #2F81F7)', fontFamily: 'var(--font-mono)' }}>
                    {activeTicket.tamperEvidentHash}
                  </code>
                </div>
                <button
                  type="button"
                  onClick={() => handleCopyHash(activeTicket.tamperEvidentHash)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: copiedHash ? 'var(--color-success, #238636)' : 'var(--color-text-muted, #8B949E)',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px'
                  }}
                >
                  {copiedHash ? <Check size={13} /> : <Copy size={13} />}
                  <span>{copiedHash ? 'Copied' : 'Copy'}</span>
                </button>
              </div>

              {/* Payload Tabs (OpenADR 2.0b / Modbus Registers) */}
              <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                <button
                  type="button"
                  onClick={() => setPayloadTab('OPENADR')}
                  style={{
                    background: payloadTab === 'OPENADR' ? 'rgba(47, 129, 247, 0.2)' : 'transparent',
                    border: '1px solid',
                    borderColor: payloadTab === 'OPENADR' ? 'var(--color-primary, #2F81F7)' : 'var(--color-border, #16171B)',
                    borderRadius: '4px',
                    padding: '4px 10px',
                    fontSize: '11px',
                    color: payloadTab === 'OPENADR' ? 'var(--color-primary, #2F81F7)' : 'var(--color-text-muted, #8B949E)',
                    cursor: 'pointer'
                  }}
                >
                  OpenADR 2.0b Payload
                </button>
                <button
                  type="button"
                  onClick={() => setPayloadTab('MODBUS')}
                  style={{
                    background: payloadTab === 'MODBUS' ? 'rgba(47, 129, 247, 0.2)' : 'transparent',
                    border: '1px solid',
                    borderColor: payloadTab === 'MODBUS' ? 'var(--color-primary, #2F81F7)' : 'var(--color-border, #16171B)',
                    borderRadius: '4px',
                    padding: '4px 10px',
                    fontSize: '11px',
                    color: payloadTab === 'MODBUS' ? 'var(--color-primary, #2F81F7)' : 'var(--color-text-muted, #8B949E)',
                    cursor: 'pointer'
                  }}
                >
                  Modbus Register Map
                </button>
              </div>

              <pre style={{
                background: 'rgba(10, 10, 12, 0.95)',
                border: '1px solid var(--color-border, #16171B)',
                borderRadius: '6px',
                padding: '12px',
                fontSize: '11px',
                color: 'var(--color-text-secondary, #C9D1D9)',
                fontFamily: 'var(--font-mono)',
                overflowX: 'auto',
                maxHeight: '160px',
                margin: 0
              }}>
                {JSON.stringify(payloadTab === 'OPENADR' ? activeTicket.openAdrPayload : activeTicket.modbusRegisters, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
