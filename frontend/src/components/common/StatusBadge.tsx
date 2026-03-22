import { cn } from '../../utils/cn';

const statusColors: Record<string, string> = {
  success: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  running: 'bg-blue-100 text-blue-800',
  pending: 'bg-yellow-100 text-yellow-800',
  cancelled: 'bg-gray-100 text-gray-800',
};

export default function StatusBadge({ status }: { status: string }) {
  return (
    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusColors[status] || 'bg-gray-100 text-gray-600')}>
      {status}
    </span>
  );
}

export function SecurityBadge({ type }: { type: 'pii' | 'financial' | 'encrypted' }) {
  const colors = {
    pii: 'bg-red-100 text-red-700',
    financial: 'bg-orange-100 text-orange-700',
    encrypted: 'bg-blue-100 text-blue-700',
  };
  return (
    <span className={cn('px-1.5 py-0.5 rounded text-xs font-medium', colors[type])}>
      {type.toUpperCase()}
    </span>
  );
}
