import CameraFeed from './components/CameraFeed'
import StatusBar from './components/StatusBar'
import DetectionList from './components/DetectionList'
import ReasoningPanel from './components/ReasoningPanel'
import ModelHealthPanel from './components/ModelHealthPanel'
import { useDetectionWebSocket } from './hooks/useDetectionWebSocket'
import { useModelHealth } from './hooks/useModelHealth'
import { useDarkMode } from './hooks/useDarkMode'

export default function App() {
    const { data, status } = useDetectionWebSocket()
    const { health, error: healthError } = useModelHealth()
    const { isDark, toggle } = useDarkMode()

    return (
        <div className="flex flex-col h-screen bg-gray-50 dark:bg-ink-950 text-gray-900 dark:text-ink-100 overflow-hidden transition-colors duration-200">
            {/* ── Top Status Bar ──────────────────────────────────────────────── */}
            <StatusBar
                status={status}
                fps={data.fps}
                objectCount={data.detections.length}
                faceCount={data.faces.length}
                isDark={isDark}
                onToggleTheme={toggle}
            />

            {/* ── Main Layout ─────────────────────────────────────────────────── */}
            <div className="flex flex-1 gap-4 p-4 overflow-hidden min-h-0">

                {/* ── Left sidebar ─────────────────────────────────────────────── */}
                <aside className="w-72 flex-shrink-0 flex flex-col gap-4 overflow-hidden">
                    <ModelHealthPanel health={health} error={healthError} />
                    <div className="flex-1 min-h-0 overflow-hidden">
                        <DetectionList detections={data.detections} faces={data.faces} />
                    </div>
                </aside>

                {/* ── Centre: camera feed ──────────────────────────────────────── */}
                <main className="flex-1 min-w-0 flex flex-col gap-4 overflow-hidden">
                    <div className="flex-1 min-h-0">
                        <CameraFeed />
                    </div>

                    {/* Stats Row */}
                    <div className="flex-shrink-0 grid grid-cols-3 gap-3">
                        <StatCard label="Objects Detected" value={String(data.detections.length)} sub="this frame" />
                        <StatCard label="Faces Detected" value={String(data.faces.length)} sub="this frame" />
                        <StatCard label="Live FPS" value={data.fps.toFixed(1)} sub="inference" mono />
                    </div>
                </main>

                {/* ── Right sidebar: VLM reasoning ─────────────────────────────── */}
                <aside className="w-80 flex-shrink-0 overflow-hidden">
                    <ReasoningPanel reasoning={data.reasoning} timestamp={data.frame_timestamp} />
                </aside>
            </div>
        </div>
    )
}

function StatCard({ label, value, sub, mono }: { label: string; value: string; sub: string; mono?: boolean }) {
    return (
        <div className="panel px-4 py-3 flex items-center justify-between transition-colors duration-200">
            <div>
                <div className="stat-label text-[9px]">{label}</div>
                <div className="text-xs text-gray-400 dark:text-ink-500 mt-0.5">{sub}</div>
            </div>
            <div className={`text-3xl font-bold text-gray-900 dark:text-ink-50 tabular-nums ${mono ? 'font-mono' : ''}`}>
                {value}
            </div>
        </div>
    )
}
