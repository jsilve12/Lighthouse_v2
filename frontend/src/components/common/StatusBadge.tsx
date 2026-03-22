import { cn } from '../../utils/cn';

const statusColors: Record<string, string> = {
  success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  failed: 'bg-red-500/10 text-red-400 border-red-500/20',
  running: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  pending: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  cancelled: 'bg-[#1a1a25] text-[#6b6b7b] border-[#2a2a35]',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn('px-2 py-0.5 rounded border text-[11px] font-medium', statusColors[status] || 'bg-[#1a1a25] text-[#6b6b7b] border-[#2a2a35]')}>
      {status}
    </span>
  );
}

export function SecurityBadge({ type }: { type: 'pii' | 'financial' | 'encrypted' }) {
  const config = {
    pii: { bg: 'bg-red-500/10 text-red-400 border-red-500/20', label: 'PII' },
    financial: { bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20', label: 'FIN' },
    encrypted: { bg: 'bg-blue-500/10 text-blue-400 border-blue-500/20', label: 'ENC' },
  };
  const { bg, label } = config[type];
  return (
    <span className={cn('px-1.5 py-0.5 rounded border text-[10px] font-medium tracking-wide', bg)}>
      {label}
    </span>
  );
}
