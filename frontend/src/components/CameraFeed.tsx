import { useRef, useState } from 'react'
import { AlertCircle, Camera } from 'lucide-react'
import { clsx } from 'clsx'

const STREAM_URL = import.meta.env.VITE_STREAM_URL as string

export default function CameraFeed() {
    const imgRef = useRef<HTMLImageElement>(null)
    const [streamError, setStreamError] = useState(false)
    const [loaded, setLoaded] = useState(false)

    return (
        <div className="relative w-full h-full bg-gray-100 dark:bg-ink-950 overflow-hidden rounded-2xl border border-gray-200 dark:border-ink-800 transition-colors duration-200">
            <img
                ref={imgRef}
                src={STREAM_URL}
                alt="Live camera feed with AI annotations"
                onLoad={() => { setLoaded(true); setStreamError(false) }}
                onError={() => { setStreamError(true); setLoaded(false) }}
                className={clsx(
                    'w-full h-full object-contain transition-opacity duration-300',
                    loaded ? 'opacity-100' : 'opacity-0'
                )}
            />

            {/* Loading skeleton */}
            {!loaded && !streamError && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
                    <Camera className="w-12 h-12 text-gray-300 dark:text-ink-700 animate-pulse" />
                    <div className="text-gray-400 dark:text-ink-600 text-sm font-medium">Connecting to camera…</div>
                    <div className="flex gap-1.5">
                        {[0, 1, 2].map(i => (
                            <span key={i} className="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-ink-700 animate-bounce"
                                style={{ animationDelay: `${i * 0.15}s` }} />
                        ))}
                    </div>
                </div>
            )}

            {/* Error state */}
            {streamError && (
                <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
                    <AlertCircle className="w-10 h-10 text-red-400" />
                    <div className="text-gray-500 dark:text-ink-400 text-sm">Camera stream unavailable</div>
                    <button
                        onClick={() => {
                            setStreamError(false)
                            setLoaded(false)
                            if (imgRef.current) imgRef.current.src = STREAM_URL + '?t=' + Date.now()
                        }}
                        className="mt-2 px-4 py-1.5 text-xs font-medium rounded-full
              border border-gray-300 dark:border-ink-700
              text-gray-600 dark:text-ink-400
              hover:border-gray-500 dark:hover:border-ink-500
              hover:text-gray-800 dark:hover:text-ink-200
              transition-all"
                    >
                        Retry
                    </button>
                </div>
            )}

            {/* LIVE badge */}
            {loaded && (
                <div className="absolute top-3 left-3 flex items-center gap-2 px-3 py-1.5 bg-black/60 backdrop-blur-sm rounded-full border border-white/10">
                    <span className="w-2 h-2 rounded-full bg-neon animate-blink" />
                    <span className="text-[10px] font-bold tracking-widest text-white uppercase">Live</span>
                </div>
            )}
        </div>
    )
}
