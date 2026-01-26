'use client';

import { cn } from '@/lib/utils';

interface TuiKeybindProps {
  keyName: string;
  label: string;
  className?: string;
}

export function TuiKeybind({ keyName, label, className }: TuiKeybindProps) {
  return (
    <span className={cn('font-mono text-xs inline-flex items-center gap-1', className)}>
      <span className="text-[var(--tui-cyan)]">[{keyName}]</span>
      <span className="text-[var(--tui-dim)]">{label}</span>
    </span>
  );
}

interface TuiKeybindGroupProps {
  bindings: Array<{ key: string; label: string }>;
  className?: string;
}

export function TuiKeybindGroup({ bindings, className }: TuiKeybindGroupProps) {
  return (
    <div className={cn('flex items-center gap-4', className)}>
      {bindings.map((binding, i) => (
        <TuiKeybind key={i} keyName={binding.key} label={binding.label} />
      ))}
    </div>
  );
}
