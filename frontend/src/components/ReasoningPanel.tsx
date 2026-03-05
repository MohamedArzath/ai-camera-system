import { useEffect, useRef } from 'react'
import { Brain, Clock } from 'lucide-react'

interface Props {
    reasoning: string
    timestamp: number
}

function timeSince(ts: number): string {
    if (!ts) return '—'
    const s = Math.round((Date.now() / 1000) - ts)
    if (s < 2) return 'just now'
    if (s < 60) return `${s}s ago`
    return `${Math.floor(s / 60)}m ago`
}

export default function ReasoningPanel({ reasoning, timestamp }: Props) {
    const bottomRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [reasoning])

    const isWaiting =
        reasoning.startsWith('Connecting') ||
        reasoning.startsWith('Waiting') ||
        reasoning.startsWith('VLM not')

    return (
        <div className="panel flex flex-col h-full overflow-hidden transition-colors duration-200">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-ink-800">
                <div className="flex items-center gap-2">
                    <Brain className="w-4 h-4 text-gray-400 dark:text-ink-400" />
                    <span className="text-sm font-semibold text-gray-800 dark:text-ink-100">Qwen3.5 Reasoning</span>
                </div>
                <div className="flex items-center gap-1.5 text-gray-400 dark:text-ink-500">
                    <Clock className="w-3 h-3" />
                    <span className="text-[10px] font-mono">{timeSince(timestamp)}</span>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {isWaiting ? (
                    <div className="flex items-center gap-2 text-gray-400 dark:text-ink-500">
                        <span className="text-sm">{reasoning}</span>
                        <span className="flex gap-1">
                            {[0, 1, 2].map((i) => (
                                <span
                                    key={i}
                                    className="w-1 h-1 rounded-full bg-gray-300 dark:bg-ink-600 animate-bounce"
                                    style={{ animationDelay: `${i * 0.15}s` }}
                                />
                            ))}
                        </span>
                    </div>
                ) : (
                    <div className="animate-fade-in">
                        <p className="text-sm text-gray-700 dark:text-ink-200 leading-relaxed whitespace-pre-wrap">
                            {reasoning}
                        </p>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            {/* Footer */}
            <div className="px-4 py-2 border-t border-gray-200 dark:border-ink-800 bg-gray-50 dark:bg-ink-900/50">
                <p className="text-[10px] text-gray-400 dark:text-ink-600">
                    Updated every ~3s · Model:{' '}
                    <span className="font-mono text-gray-500 dark:text-ink-500">Qwen/Qwen3.5-0.8B</span>
                </p>
            </div>
        </div>
    )
}
