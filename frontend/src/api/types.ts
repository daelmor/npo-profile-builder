// TypeScript mirror of the backend Pydantic schemas (app/schemas).

export type FieldStatus = 'extracted' | 'inferred' | 'user_provided' | 'missing'

export interface TrackedField<T> {
  value: T | null
  status: FieldStatus
  confidence: number | null
  source_quote: string | null
  source_chunk_id: number | null
  notes: string | null
}

export interface NonprofitProfile {
  // Identity
  legal_name: TrackedField<string>
  aka: TrackedField<string[]>
  country: TrackedField<string>
  region: TrackedField<string>
  year_founded: TrackedField<number>
  website: TrackedField<string>
  registration_id: TrackedField<string>
  // Mission & programs
  mission_statement: TrackedField<string>
  cause_areas: TrackedField<string[]>
  target_populations: TrackedField<string[]>
  theory_of_change: TrackedField<string>
  // Scale & stage
  annual_budget_band: TrackedField<string>
  staff_count: TrackedField<number>
  volunteer_count: TrackedField<number>
  growth_stage: TrackedField<string>
  // Impact
  key_outcomes: TrackedField<string[]>
  evidence_standard: TrackedField<string>
  notable_results: TrackedField<string[]>
  // Funding
  current_funders: TrackedField<string[]>
  funding_gaps: TrackedField<string[]>
}

export type ProfileFieldKey = keyof NonprofitProfile

export interface Completeness {
  total: number
  extracted: number
  inferred: number
  user_provided: number
  missing: number
}

export interface SourceInfo {
  id: string
  filename: string | null
  char_count: number
  chunk_count: number
}

export interface ProfileDetail {
  id: string
  created_at: string
  updated_at: string
  source: SourceInfo
  completeness: Completeness
  profile: NonprofitProfile
}

export interface ProfileSummary {
  id: string
  legal_name: string | null
  country: string | null
  cause_areas: string[]
  completeness: Completeness
  created_at: string
}
