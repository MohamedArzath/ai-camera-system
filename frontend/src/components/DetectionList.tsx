import { clsx } from 'clsx'
import { Box, User } from 'lucide-react'
import type { Detection, Face } from '../types'

interface Props {
    detections: Detection[]
    faces: Face[]
}

function confClass(c: number) {
    if (c >= 0.75) return 'bg-emerald-50 dark:bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30'
    if (c >= 0.50) return 'bg-amber-50 dark:bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/30'
    return 'bg-red-50 dark:bg-red-500/15 text-red-700 dark:text-red-400 border-red-200 dark:border-red-500/30'
}

function barColor(c: number) {
    if (c >= 0.75) return 'bg-emerald-500'
    if (c >= 0.50) return 'bg-amber-500'
    return 'bg-red-500'
}

function ConfBar({ value }: { value: number }) {
    return (
        <div className="flex items-center gap-2 mt-1.5">
            <div className="flex-1 h-1 bg-gray-200 dark:bg-ink-800 rounded-full overflow-hidden">
                <div
                    className={clsx('h-full rounded-full transition-all duration-500', barColor(value))}
                    style={{ width: `${(value * 100).toFixed(0)}%` }}
                />
            </div>
            <span className="text-[10px] font-mono text-gray-400 dark:text-ink-500 w-9 text-right">
                {(value * 100).toFixed(0)}%
            </span>
        </div>
    )
}

export default function DetectionList({ detections, faces }: Props) {
    const total = detections.length + faces.length

    return (
        <div className="panel flex flex-col h-full overflow-hidden transition-colors duration-200">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-ink-800">
                <div className="flex items-center gap-2">
                    <Box className="w-4 h-4 text-gray-400 dark:text-ink-400" />
                    <span className="text-sm font-semibold text-gray-800 dark:text-ink-100">Detections</span>
                </div>
                <span className="badge bg-gray-100 dark:bg-ink-800 text-gray-600 dark:text-ink-300 border border-gray-200 dark:border-ink-700">
                    {total} objects
                </span>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {total === 0 && (
                    <div className="flex flex-col items-center justify-center h-32 gap-2 text-gray-300 dark:text-ink-600">
                        <Box className="w-8 h-8 opacity-40" />
                        <p className="text-xs">No objects detected</p>
                    </div>
                )}

                {detections.map((det, i) => (
                    <div
                        key={`det-${i}-${det.label}`}
                        className="flex flex-col p-3 rounded-xl bg-gray-50 dark:bg-ink-800/60 border border-gray-200 dark:border-ink-700/50 animate-fade-in hover:border-gray-300 dark:hover:border-ink-600 transition-all"
                    >
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2 min-w-0">
                                <span className="w-5 h-5 flex-shrink-0 rounded-md bg-gray-200 dark:bg-ink-700 flex items-center justify-center">
                                    <Box className="w-3 h-3 text-gray-500 dark:text-ink-400" />
                                </span>
                                <div className="min-w-0">
                                    <span className="text-sm font-semibold text-gray-800 dark:text-ink-50 capitalize truncate block">
                                        {det.label}
                                    </span>
                                    {det.track_id != null && (
                                        <span className="text-[9px] text-gray-400 dark:text-ink-600 font-mono">#{det.track_id}</span>
                                    )}
                                </div>
                            </div>
                            <span className={clsx('badge border flex-shrink-0', confClass(det.confidence))}>
                                {(det.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                        <ConfBar value={det.confidence} />
                        <div className="mt-1.5 text-[10px] text-gray-400 dark:text-ink-600 font-mono">
                            [{det.bbox.x1}, {det.bbox.y1}] → [{det.bbox.x2}, {det.bbox.y2}]
                        </div>
                    </div>
                ))}

                {faces.map((face, i) => (
                    <div
                        key={`face-${i}`}
                        className="flex flex-col p-3 rounded-xl bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-900/50 animate-fade-in"
                    >
                        <div className="flex items-start justify-between gap-2">
                            <div className="flex items-center gap-2">
                                <span className="w-5 h-5 flex-shrink-0 rounded-md bg-teal-100 dark:bg-teal-900/50 flex items-center justify-center">
                                    <User className="w-3 h-3 text-teal-600 dark:text-teal-400" />
                                </span>
                                <span className="text-sm font-semibold text-teal-700 dark:text-teal-300">Face</span>
                            </div>
                            <span className="badge bg-teal-100 dark:bg-teal-900/40 text-teal-700 dark:text-teal-400 border border-teal-200 dark:border-teal-700/30">
                                {(face.confidence * 100).toFixed(0)}%
                            </span>
                        </div>
                        <ConfBar value={face.confidence} />
                        <div className="mt-1.5 text-[10px] text-gray-400 dark:text-ink-600 font-mono">
                            [{face.bbox.x1}, {face.bbox.y1}] → [{face.bbox.x2}, {face.bbox.y2}]
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
