import { clsx } from 'clsx'
import { Sun, Moon } from 'lucide-react'
import type { ConnectionStatus } from '../types'

interface Props {
    status: ConnectionStatus
    fps: number
    objectCount: number
    faceCount: number
    isDark: boolean
    onToggleTheme: () => void
}

const STATUS_CFG = {
    connected: { label: 'LIVE', dot: 'bg-neon animate-blink', text: 'text-neon', ring: 'border-neon/30 bg-neon/5' },
    connecting: { label: 'CONNECTING', dot: 'bg-yellow-400 animate-pulse', text: 'text-yellow-500', ring: 'border-yellow-400/30 bg-yellow-50 dark:bg-yellow-400/5' },
    disconnected: { label: 'OFFLINE', dot: 'bg-gray-400 dark:bg-ink-500', text: 'text-gray-500 dark:text-ink-500', ring: 'border-gray-300 dark:border-ink-700 bg-gray-50 dark:bg-ink-900' },
    error: { label: 'ERROR', dot: 'bg-red-500 animate-pulse', text: 'text-red-500', ring: 'border-red-300 dark:border-red-500/30 bg-red-50 dark:bg-red-500/5' },
}

export default function StatusBar({ status, fps, objectCount, faceCount, isDark, onToggleTheme }: Props) {
    const cfg = STATUS_CFG[status]

    return (
        <header className="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-ink-800 bg-white dark:bg-ink-950 transition-colors duration-200">
            {/* Brand */}
            <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-lg bg-gray-900 dark:bg-white flex items-center justify-center shadow-sm">
                    <svg viewBox="0 0 24 24" className="w-4 h-4 fill-current text-white dark:text-ink-950">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z" />
                    </svg>
                </div>
                <div>
                    <h1 className="text-sm font-bold tracking-tight text-gray-900 dark:text-ink-50 leading-none">AI Camera System</h1>
                    <p className="text-[10px] text-gray-400 dark:text-ink-500 leading-none mt-0.5">YOLO · Qwen3.5 · InsightFace</p>
                </div>
            </div>

            {/* Stats + badge + toggle */}
            <div className="flex items-center gap-5">
                <MiniStat label="FPS" value={fps.toFixed(1)} />
                <MiniStat label="Objects" value={String(objectCount)} />
                <MiniStat label="Faces" value={String(faceCount)} />

                {/* Connection badge */}
                <div className={clsx('flex items-center gap-2 px-3 py-1.5 rounded-full border', cfg.ring)}>
                    <span className={clsx('w-2 h-2 rounded-full flex-shrink-0', cfg.dot)} />
                    <span className={clsx('text-[10px] font-bold tracking-widest', cfg.text)}>{cfg.label}</span>
                </div>

                {/* Dark / Light toggle */}
                <button
                    onClick={onToggleTheme}
                    aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                    className={clsx(
                        'relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200',
                        'border shadow-sm hover:scale-105 active:scale-95',
                        'bg-gray-100 hover:bg-gray-200 border-gray-200',
                        'dark:bg-ink-800 dark:hover:bg-ink-700 dark:border-ink-700',
                    )}
                >
                    {isDark
                        ? <Sun className="w-4 h-4 text-amber-400" />
                        : <Moon className="w-4 h-4 text-gray-600" />
                    }
                </button>
            </div>
        </header>
    )
}

function MiniStat({ label, value }: { label: string; value: string }) {
    return (
        <div className="text-center">
            <div className="stat-label text-[9px]">{label}</div>
            <div className="text-sm font-bold text-gray-800 dark:text-ink-100 tabular-nums font-mono">{value}</div>
        </div>
    )
}
