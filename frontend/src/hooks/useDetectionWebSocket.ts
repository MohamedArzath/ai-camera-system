import { useEffect, useRef, useState, useCallback } from 'react'
import type { ConnectionStatus, InferenceData } from '../types'

// Use the Vite dev‑proxy path so we don't need CORS on the WS directly.
// In production, point to ws://YOUR_VPS:8001/api/ws
const WS_URL = (() => {
    const envUrl = import.meta.env.VITE_WS_URL as string | undefined
    if (envUrl) return envUrl
    // Derive from the current page host (works in dev proxy + production)
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    return `${proto}://${window.location.host}/api/ws`
})()

const RECONNECT_DELAY = Number(import.meta.env.VITE_WS_RECONNECT_DELAY ?? 3000)

const INITIAL_DATA: InferenceData = {
    detections: [],
    faces: [],
    reasoning: 'Waiting for first frame…',
    fps: 0,
    frame_timestamp: 0,
}

export function useDetectionWebSocket() {
    const [data, setData] = useState<InferenceData>(INITIAL_DATA)
    const [status, setStatus] = useState<ConnectionStatus>('connecting')

    // generation counter — incremented on every new connection attempt;
    // stale callbacks check their captured gen value so they self-discard
    // (handles React StrictMode double-mount, manual retries, etc.)
    const genRef = useRef(0)
    const wsRef = useRef<WebSocket | null>(null)
    const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

    const connect = useCallback(() => {
        // cancel any pending reconnect
        if (reconnectTimer.current) {
            clearTimeout(reconnectTimer.current)
            reconnectTimer.current = null
        }

        // close any existing socket cleanly before opening a new one
        if (wsRef.current) {
            wsRef.current.onopen = null
            wsRef.current.onmessage = null
            wsRef.current.onerror = null
            wsRef.current.onclose = null
            wsRef.current.close()
            wsRef.current = null
        }

        const gen = ++genRef.current   // bump generation
        const ws = new WebSocket(WS_URL)
        wsRef.current = ws

        setStatus('connecting')

        ws.onopen = () => {
            if (genRef.current !== gen) return
            setStatus('connected')
        }

        ws.onmessage = (event) => {
            if (genRef.current !== gen) return
            try {
                const parsed = JSON.parse(event.data) as InferenceData
                setData(parsed)
            } catch {
                // ignore malformed frames
            }
        }

        ws.onerror = () => {
            if (genRef.current !== gen) return
            setStatus('error')
        }

        ws.onclose = () => {
            if (genRef.current !== gen) return
            setStatus('disconnected')
            reconnectTimer.current = setTimeout(() => connect(), RECONNECT_DELAY)
        }
    }, []) // stable — no deps, uses refs only

    useEffect(() => {
        connect()

        return () => {
            // Invalidate the current generation so in-flight callbacks are ignored
            genRef.current++

            if (reconnectTimer.current) {
                clearTimeout(reconnectTimer.current)
                reconnectTimer.current = null
            }

            if (wsRef.current) {
                wsRef.current.onopen = null
                wsRef.current.onmessage = null
                wsRef.current.onerror = null
                wsRef.current.onclose = null
                wsRef.current.close()
                wsRef.current = null
            }
        }
    }, [connect])

    return { data, status }
}
