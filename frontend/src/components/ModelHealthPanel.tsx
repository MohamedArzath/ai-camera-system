import { clsx } from 'clsx'
import { Cpu, Eye, Shield, Activity, Monitor } from 'lucide-react'
import type { ModelHealth } from '../types'

interface Props {
    health: ModelHealth | null
    error: boolean
}

const STATUS_DOT: Record<string, string> = {
    loaded: 'bg-emerald-500',
    not_loaded: 'bg-red-500',
}

function ModelRow({
    icon, name, status, device,
}: {
    icon: React.ReactNode
    name: string
    status: string | undefined
    device?: string
}) {
    const dot = STATUS_DOT[status ?? ''] ?? 'bg-gray-300 dark:bg-ink-600'
    const statusText = status === 'loaded' ? 'loaded' : status === 'not_loaded' ? 'not loaded' : '—'

    return (
        <div className="py-2 border-b border-gray-100 dark:border-ink-800/60 last:border-0">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-gray-600 dark:text-ink-300">
                    <span className="text-gray-400 dark:text-ink-500">{icon}</span>
                    <span className="text-xs font-medium">{name}</span>
                </div>
                <div className="flex items-center gap-1.5">
                    <span className={clsx('w-1.5 h-1.5 rounded-full', dot)} />
                    <span className={clsx(
                        'text-[10px] font-mono',
                        status === 'loaded' ? 'text-emerald-600 dark:text-emerald-400' : 'text-gray-400 dark:text-ink-500'
                    )}>
                        {statusText}
                    </span>
                </div>
            </div>
            {device && (
                <div className="flex items-center gap-1.5 mt-0.5 ml-5">
                    <Monitor className="w-2.5 h-2.5 text-gray-300 dark:text-ink-600 flex-shrink-0" />
                    <span className="text-[9px] font-mono text-gray-400 dark:text-ink-600 truncate">{device}</span>
                </div>
            )}
        </div>
    )
}

export default function ModelHealthPanel({ health, error }: Props) {
    if (error || !health) {
        return (
            <div className="panel px-4 py-3 transition-colors duration-200">
                <div className="flex items-center gap-2 text-gray-400 dark:text-ink-600 text-xs">
                    <Activity className="w-3.5 h-3.5" />
                    <span>Backend unreachable</span>
                </div>
            </div>
        )
    }

    // Device info from extended health fields (may not exist on older backends)
    const ext = health as ModelHealth & {
        yolo_device?: string
        qwen_device?: string
        insightface_device?: string
        cuda_available?: boolean
        mps_available?: boolean
    }

    return (
        <div className="panel px-4 py-3 transition-colors duration-200">
            {/* Header row */}
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Activity className="w-3.5 h-3.5 text-gray-400 dark:text-ink-400" />
                    <span className="text-xs font-semibold text-gray-700 dark:text-ink-300">Model Status</span>
                </div>
                <span className={clsx('badge border text-[10px]',
                    health.worker_running
                        ? 'bg-neon/10 text-green-700 dark:text-neon border-neon/20'
                        : 'bg-gray-100 dark:bg-ink-800 text-gray-500 dark:text-ink-500 border-gray-200 dark:border-ink-700'
                )}>
                    {health.worker_running ? 'Worker running' : 'Worker stopped'}
                </span>
            </div>

            {/* GPU availability pill */}
            {(ext.cuda_available !== undefined || ext.mps_available !== undefined) && (
                <div className="mb-2 flex gap-2">
                    <span className={clsx('badge border text-[9px]',
                        ext.cuda_available
                            ? 'bg-violet-50 dark:bg-violet-900/20 text-violet-700 dark:text-violet-400 border-violet-200 dark:border-violet-700/30'
                            : 'bg-gray-50 dark:bg-ink-800 text-gray-400 dark:text-ink-600 border-gray-200 dark:border-ink-700'
                    )}>
                        CUDA {ext.cuda_available ? '✓' : '✗'}
                    </span>
                    <span className={clsx('badge border text-[9px]',
                        ext.mps_available
                            ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-700/30'
                            : 'bg-gray-50 dark:bg-ink-800 text-gray-400 dark:text-ink-600 border-gray-200 dark:border-ink-700'
                    )}>
                        MPS {ext.mps_available ? '✓' : '✗'}
                    </span>
                </div>
            )}

            <ModelRow icon={<Eye className="w-3 h-3" />} name="YOLO" status={health.yolo} device={ext.yolo_device} />
            <ModelRow icon={<Cpu className="w-3 h-3" />} name="Qwen3.5" status={health.qwen} device={ext.qwen_device} />
            <ModelRow icon={<Shield className="w-3 h-3" />} name="InsightFace" status={health.insightface} device={ext.insightface_device} />
        </div>
    )
}
