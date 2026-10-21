export interface StreamStep { afterMs: number; event: unknown } // a typed ChatEvent / CaseEvent payload
export interface StreamScript { thread?: string; steps: StreamStep[]; dropAfterMs?: number; useFrames?: boolean }
