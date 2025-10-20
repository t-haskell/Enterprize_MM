'use client';

import { useId, useState } from 'react';

interface TooltipProps {
  label: string;
  children: React.ReactNode;
}

export function Tooltip({ label, children }: TooltipProps) {
  const tooltipId = useId();
  const [visible, setVisible] = useState(false);

  return (
    <span className="tooltip" style={{ position: 'relative' }}>
      <button
        type="button"
        aria-describedby={tooltipId}
        className="tooltip-trigger"
        onFocus={() => setVisible(true)}
        onBlur={() => setVisible(false)}
        onMouseEnter={() => setVisible(true)}
        onMouseLeave={() => setVisible(false)}
      >
        {children}
      </button>
      <span role="tooltip" id={tooltipId} className="tooltip-content" data-visible={visible}>
        {label}
      </span>
    </span>
  );
}
