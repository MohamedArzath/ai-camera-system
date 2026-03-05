import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

const STORAGE_KEY = 'ai-camera-theme'

export function useDarkMode() {
    const [theme, setTheme] = useState<Theme>(() => {
        // Default to light; restore from localStorage if previously set
        return (localStorage.getItem(STORAGE_KEY) as Theme) ?? 'light'
    })

    useEffect(() => {
        const root = document.documentElement
        if (theme === 'dark') {
            root.classList.add('dark')
        } else {
            root.classList.remove('dark')
        }
        localStorage.setItem(STORAGE_KEY, theme)
    }, [theme])

    const toggle = () => setTheme((t) => (t === 'dark' ? 'light' : 'dark'))

    return { theme, toggle, isDark: theme === 'dark' }
}
