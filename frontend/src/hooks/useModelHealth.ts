import { useEffect, useState, useCallback } from 'react'
import type { ModelHealth } from '../types'

const API_URL = import.meta.env.VITE_API_URL as string

export function useModelHealth(interval = 5000) {
    const [health, setHealth] = useState<ModelHealth | null>(null)
    const [error, setError] = useState(false)

    const fetch_ = useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/api/detect/health`)
            if (res.ok) {
                const data = await res.json() as ModelHealth
                setHealth(data)
                setError(false)
            } else {
                setError(true)
            }
        } catch {
            setError(true)
        }
    }, [])

    useEffect(() => {
        fetch_()
        const id = setInterval(fetch_, interval)
        return () => clearInterval(id)
    }, [fetch_, interval])

    return { health, error }
}
