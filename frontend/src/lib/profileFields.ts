// Display metadata for the NonprofitProfile fields: section grouping + labels.

import type { ProfileFieldKey } from '../api/types'

export const PROFILE_SECTIONS: { title: string; fields: ProfileFieldKey[] }[] = [
  {
    title: 'Identity',
    fields: ['legal_name', 'aka', 'country', 'region', 'year_founded', 'website', 'registration_id'],
  },
  {
    title: 'Mission & programs',
    fields: ['mission_statement', 'cause_areas', 'target_populations', 'theory_of_change'],
  },
  {
    title: 'Scale & stage',
    fields: ['annual_budget_band', 'staff_count', 'volunteer_count', 'growth_stage'],
  },
  { title: 'Impact', fields: ['key_outcomes', 'evidence_standard', 'notable_results'] },
  { title: 'Funding', fields: ['current_funders', 'funding_gaps'] },
]

export const FIELD_LABELS: Record<ProfileFieldKey, string> = {
  legal_name: 'Legal name',
  aka: 'Also known as',
  country: 'Country',
  region: 'Region',
  year_founded: 'Year founded',
  website: 'Website',
  registration_id: 'Registration / tax ID',
  mission_statement: 'Mission',
  cause_areas: 'Cause areas',
  target_populations: 'Target populations',
  theory_of_change: 'Theory of change',
  annual_budget_band: 'Annual budget',
  staff_count: 'Staff',
  volunteer_count: 'Volunteers',
  growth_stage: 'Growth stage',
  key_outcomes: 'Key outcomes',
  evidence_standard: 'Evidence standard',
  notable_results: 'Notable results',
  current_funders: 'Current funders',
  funding_gaps: 'Funding gaps',
}
