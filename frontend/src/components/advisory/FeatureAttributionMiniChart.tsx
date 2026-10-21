import React from 'react';
import { BarChart3 } from 'lucide-react';
import { FeatureAttribution } from '../../types/twin';

interface FeatureAttributionMiniChartProps {
  features: FeatureAttribution[];
}

export const FeatureAttributionMiniChart: React.FC<FeatureAttributionMiniChartProps> = ({ features }) => {
  if (!features || features.length === 0) {
    return null;
  }

  // Find max absolute impact to normalize bar lengths
  const maxAbsImpact = Math.max(...features.map(f => Math.abs(f.impact)), 1.0);

  return (
    <div className="xai-attribution-panel" style={{
      background: 'rgba(9, 9, 11, 0.65)',
      border: '1px solid var(--color-border-strong, #222329)',
      borderRadius: 'var(--radius-md, 8px)',
      padding: '12px 14px',
      marginTop: '12px'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <BarChart3 size={14} color="var(--color-primary, #2F81F7)" />
          <span style={{ fontSize: '11px', fontWeight: 700, letterSpacing: '0.04em', textTransform: 'uppercase', color: 'var(--color-text-secondary, #C9D1D9)' }}>
            Top-5 TreeSHAP Feature Attributions
          </span>
        </div>
        <span style={{ fontSize: '10px', color: 'var(--color-text-muted, #8B949E)', fontFamily: 'var(--font-mono)' }}>
          Explainable AI (XAI)
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {features.slice(0, 5).map((f, idx) => {
          const isPositive = f.impact >= 0;
          const absPercent = Math.min(100, Math.round((Math.abs(f.impact) / maxAbsImpact) * 100));
          const barColor = isPositive ? 'var(--color-primary, #2F81F7)' : '#F85149';
          const badgeColor = isPositive ? 'rgba(47, 129, 247, 0.15)' : 'rgba(248, 81, 73, 0.15)';
          const textColor = isPositive ? '#58A6FF' : '#FF7B72';

          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11px' }}>
              <span style={{
                width: '180px',
                color: 'var(--color-text-secondary, #C9D1D9)',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                flexShrink: 0
              }}>
                {f.feature}
              </span>

              {/* Bar track */}
              <div style={{
                flex: 1,
                height: '8px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '4px',
                position: 'relative',
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${absPercent}%`,
                  height: '100%',
                  background: barColor,
                  borderRadius: '4px',
                  transition: 'width 250ms ease-in-out'
                }} />
              </div>

              {/* Value pill */}
              <span style={{
                minWidth: '48px',
                textAlign: 'right',
                fontFamily: 'var(--font-mono)',
                fontSize: '11px',
                fontWeight: 600,
                color: textColor,
                background: badgeColor,
                padding: '1px 6px',
                borderRadius: '4px',
                flexShrink: 0
              }}>
                {isPositive ? `+${f.impact.toFixed(0)}%` : `${f.impact.toFixed(0)}%`}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
