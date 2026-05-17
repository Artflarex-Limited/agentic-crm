export { AgenticCRM, AgenticCRMError, getAuthToken } from './client'
export type { SDKConfig } from './config'
export { LeadsClient } from './leads'
export type { CreateLeadInput, UpdateLeadInput } from './leads'
export { ContactsClient } from './contacts'
export type { CreateContactInput, UpdateContactInput } from './contacts'
export { DealsClient } from './deals'
export type { CreateDealInput, UpdateDealInput } from './deals'
export { AgentsClient } from './agents'
export type { CreateAgentInput, UpdateAgentInput } from './agents'
export { ActivitiesClient } from './activities'
export type { CreateActivityInput } from './activities'
export { SequencesClient } from './sequences'
export type { CreateSequenceInput, UpdateSequenceInput } from './sequences'

import { AgenticCRM } from './client'
import { LeadsClient } from './leads'
import { ContactsClient } from './contacts'
import { DealsClient } from './deals'
import { AgentsClient } from './agents'
import { ActivitiesClient } from './activities'
import { SequencesClient } from './sequences'

export function createClient(config?: ConstructorParameters<typeof AgenticCRM>[0]) {
  const client = new AgenticCRM(config)
  return {
    leads: new LeadsClient(client),
    contacts: new ContactsClient(client),
    deals: new DealsClient(client),
    agents: new AgentsClient(client),
    activities: new ActivitiesClient(client),
    sequences: new SequencesClient(client),
  }
}

export const sdk = createClient()