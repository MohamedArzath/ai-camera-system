// Detection and face result types mirroring the backend Pydantic models

export interface BoundingBox {
    x1: number
    y1: number
    x2: number
    y2: number
}

export interface Detection {
    label: string
    confidence: number
    bbox: BoundingBox
    class_id: number
    track_id: number | null
}

export interface Face {
    confidence: number
    bbox: BoundingBox
}

export interface InferenceData {
    detections: Detection[]
    faces: Face[]
    reasoning: string
    fps: number
    frame_timestamp: number
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error'

export interface ModelHealth {
    yolo: string
    qwen: string
    insightface: string
    worker_running: boolean
    fps: number
}
