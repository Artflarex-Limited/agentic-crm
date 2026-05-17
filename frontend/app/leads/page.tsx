'use client'

import { useEffect, useState } from 'react'
import { api, type Lead, type LeadStage, type LeadSource, type Contact } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Search, Filter, Plus, X, ExternalLink, Mail, Phone, Building, Trash2 } from 'lucide-react'
import { getStoredUTM, trackLeadCreated } from '@/lib/tracking'
import { cn } from '@/lib/utils'

const STAGES: { value: LeadStage; label: string; color: string; bgColor: string }[] = [
  { value: 'new', label: 'New', color: 'text-blue-400', bgColor: 'bg-blue-400/10' },
  { value: 'contacted', label: 'Contacted', color: 'text-yellow-400', bgColor: 'bg-yellow-400/10' },
  { value: 'qualified', label: 'Qualified', color: 'text-emerald-400', bgColor: 'bg-emerald-400/10' },
  { value: 'proposal', label: 'Proposal', color: 'text-orange-400', bgColor: 'bg-orange-400/10' },
  { value: 'negotiation', label: 'Negotiation', color: 'text-purple-400', bgColor: 'bg-purple-400/10' },
  { value: 'won', label: 'Won', color: 'text-emerald-400', bgColor: 'bg-emerald-400/10' },
  { value: 'lost', label: 'Lost', color: 'text-red-400', bgColor: 'bg-red-400/10' },
]

const SOURCES: { value: LeadSource; label: string }[] = [
  { value: 'linkedin', label: 'LinkedIn' },
  { value: 'email', label: 'Email' },
  { value: 'web', label: 'Web' },
  { value: 'phone', label: 'Phone' },
  { value: 'cold_outreach', label: 'Cold Outreach' },
  { value: 'referral', label: 'Referral' },
  { value: 'other', label: 'Other' },
]

function timeAgo(date: string | null): string {
  if (!date) return 'Never'
  const diff = Date.now() - new Date(date).getTime()
  const days = Math.floor(diff / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return 'Yesterday'
  if (days < 7) return `${days}d ago`
  if (days < 30) return `${Math.floor(days / 7)}w ago`
  return new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [activeTab, setActiveTab] = useState<'Overview' | 'Activity' | 'Notes'>('Overview')
  const [newLead, setNewLead] = useState({ contact: { first_name: '', last_name: '', email: '', phone: '', company: '' }, source: 'web' as LeadSource })
  const [selectedLeadIds, setSelectedLeadIds] = useState<Set<number>>(new Set())

  useEffect(() => {
    loadLeads()
  }, [])

  async function loadLeads() {
    try {
      const data = await api.leads.list()
      setLeads(data)
    } catch (e) {
      console.error('Failed to load leads', e)
    } finally {
      setLoading(false)
    }
  }

  async function handleFilterChange() {
    setLoading(true)
    try {
      const params: { stage?: LeadStage; source?: LeadSource; search?: string } = {}
      if (stageFilter) params.stage = stageFilter as LeadStage
      if (sourceFilter) params.source = sourceFilter as LeadSource
      if (search) params.search = search
      const data = await api.leads.list(params)
      setLeads(data)
    } catch (e) {
      console.error('Failed to load leads', e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      if (search || stageFilter || sourceFilter) {
        handleFilterChange()
      } else if (!search && !stageFilter && !sourceFilter) {
        loadLeads()
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [search, stageFilter, sourceFilter])

  async function handleCreateLead() {
    try {
      const contactData = { first_name: newLead.contact.first_name, last_name: newLead.contact.last_name, email: newLead.contact.email, phone: newLead.contact.phone }
      const contact = await api.contacts.create(contactData)
      const utm = getStoredUTM()
      const lead = await api.leads.create({ contact_id: contact.id, source: newLead.source, stage: 'new', score: 50 })
      trackLeadCreated({ source: newLead.source, stage: 'new', score: 50, utm })
      setShowCreateModal(false)
      setNewLead({ contact: { first_name: '', last_name: '', email: '', phone: '', company: '' }, source: 'web' })
      loadLeads()
    } catch (e) {
      console.error('Failed to create lead', e)
    }
  }

  const stageColors = Object.fromEntries(STAGES.map(s => [s.value, `${s.color} ${s.bgColor}`]))

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-12 w-32" />
        <Card className="skeleton h-96" />
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Leads</h1>
          <p className="text-muted-foreground mt-1">{leads.length} total leads</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} className="gap-2" data-tour="add-lead">
          <Plus className="h-4 w-4" />
          Add Lead
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search leads..."
                className="pl-9"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Select value={stageFilter} onValueChange={setStageFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Stage" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Stages</SelectItem>
                {STAGES.map(s => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={sourceFilter} onValueChange={setSourceFilter}>
              <SelectTrigger className="w-[160px]">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">All Sources</SelectItem>
                {SOURCES.map(s => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            {(stageFilter || sourceFilter) && (
              <Button variant="ghost" size="sm" onClick={() => { setStageFilter(''); setSourceFilter('') }} className="gap-1">
                <X className="h-3 w-3" />
                Clear
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0 overflow-auto pb-20">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="w-10">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-border bg-surface accent-accent cursor-pointer"
                    checked={selectedLeadIds.size === leads.length && leads.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedLeadIds(new Set(leads.map(l => l.id)))
                      } else {
                        setSelectedLeadIds(new Set())
                      }
                    }}
                  />
                </TableHead>
                <TableHead className="font-medium">Name</TableHead>
                <TableHead className="font-medium">Email</TableHead>
                <TableHead className="font-medium">Company</TableHead>
                <TableHead className="font-medium">Source</TableHead>
                <TableHead className="font-medium">Stage</TableHead>
                <TableHead className="font-medium">Score</TableHead>
                <TableHead className="font-medium">Last Contacted</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {leads.map(lead => {
                const stage = STAGES.find(s => s.value === lead.stage)
                return (
                  <TableRow 
                    key={lead.id} 
                    className="cursor-pointer border-b border-border/50 hover:bg-surface/50 transition-colors duration-100"
                    onClick={() => { setSelectedLead(lead); setActiveTab('Overview') }}
                  >
                    <TableCell className="w-10">
                      <input
                        type="checkbox"
                        className="h-4 w-4 rounded border-border bg-surface accent-accent cursor-pointer"
                        checked={selectedLeadIds.has(lead.id)}
                        onChange={(e) => {
                          e.stopPropagation()
                          const newSet = new Set(selectedLeadIds)
                          if (e.target.checked) {
                            newSet.add(lead.id)
                          } else {
                            newSet.delete(lead.id)
                          }
                          setSelectedLeadIds(newSet)
                        }}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-[var(--radius-md)] bg-accent/10 flex items-center justify-center">
                          <span className="text-xs font-semibold text-accent">
                            {lead.contact?.first_name?.[0]}{lead.contact?.last_name?.[0]}
                          </span>
                        </div>
                        {lead.contact?.first_name} {lead.contact?.last_name}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Mail className="h-3 w-3" />
                        {lead.contact?.email || '-'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <Building className="h-3 w-3" />
                        {lead.contact?.company_id || '-'}
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="bg-surface text-text-secondary border border-border rounded-[var(--radius-sm)] text-xs px-2 py-1">{lead.source.replace('_', ' ')}</span>
                    </TableCell>
                    <TableCell>
                      <Badge className={`${stage?.bgColor} ${stage?.color} border-0`}>
                        {stage?.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 rounded-full bg-surface overflow-hidden w-16">
                          <div 
                            className={`h-full rounded-full ${
                              lead.score >= 70 ? 'bg-success' : 
                              lead.score >= 40 ? 'bg-accent' : 'bg-danger'
                            }`} 
                            style={{ width: `${lead.score}%` }}
                          />
                        </div>
                        <span className="text-sm font-mono">{lead.score}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <span className="text-text-muted text-sm">{timeAgo(lead.last_contacted_at ?? null)}</span>
                    </TableCell>
                  </TableRow>
                )
              })}
              {leads.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-12">
                    <div className="flex flex-col items-center">
                      <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-4">
                        <Search className="h-5 w-5 text-muted-foreground" />
                      </div>
                      <p className="text-muted-foreground">No leads found</p>
                      <Button variant="link" onClick={() => setShowCreateModal(true)} className="mt-2">
                        Create your first lead
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {selectedLeadIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 px-6 py-4 rounded-[var(--radius-lg)] bg-surface border border-border shadow-[0_8px_32px_rgba(0,0,0,0.4)] animate-in slide-in-from-bottom-4 duration-200">
          <span className="text-sm font-medium text-text-primary">
            {selectedLeadIds.size} selected
          </span>
          
          <div className="h-4 w-px bg-border" />
          
          <Select
            onValueChange={async (stage) => {
              for (const id of Array.from(selectedLeadIds)) {
                try {
                  await api.leads.update(id, { stage: stage as LeadStage })
                } catch (e) {
                  console.error(`Failed to update lead ${id}`, e)
                }
              }
              setSelectedLeadIds(new Set())
              loadLeads()
            }}
          >
            <SelectTrigger className="w-[160px] h-8 text-sm">
              <SelectValue placeholder="Change stage..." />
            </SelectTrigger>
            <SelectContent>
              {STAGES.map(s => (
                <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button
            variant="destructive"
            size="sm"
            className="gap-1.5"
            onClick={async () => {
              if (!confirm(`Delete ${selectedLeadIds.size} lead(s)?`)) return
              for (const id of Array.from(selectedLeadIds)) {
                try {
                  await api.leads.delete(id)
                } catch (e) {
                  console.error(`Failed to delete lead ${id}`, e)
                }
              }
              setSelectedLeadIds(new Set())
              loadLeads()
            }}
          >
            <Trash2 className="h-3 w-3" />
            Delete
          </Button>
          
          <Button variant="ghost" size="sm" onClick={() => setSelectedLeadIds(new Set())}>
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}

      {selectedLead && (
        <Dialog open={!!selectedLead} onOpenChange={() => setSelectedLead(null)}>
          <DialogContent className="fixed inset-y-0 right-0 w-[480px] max-w-full border-l border-border bg-bg-base shadow-xl data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right duration-200 p-0 flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <div className="flex items-center gap-3">
                {selectedLead && (
                  <>
                    <div className="w-10 h-10 rounded-[var(--radius-md)] bg-accent/10 flex items-center justify-center">
                      <span className="text-sm font-semibold text-accent">
                        {selectedLead.contact?.first_name?.[0]}{selectedLead.contact?.last_name?.[0]}
                      </span>
                    </div>
                    <div>
                      <h3 className="text-base font-semibold font-display">
                        {selectedLead.contact?.first_name} {selectedLead.contact?.last_name}
                      </h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        {STAGES.find(s => s.value === selectedLead.stage) && (
                          <span className={`text-xs px-2 py-0.5 rounded-full ${STAGES.find(s => s.value === selectedLead.stage)?.bgColor} ${STAGES.find(s => s.value === selectedLead.stage)?.color} border-0`}>
                            {STAGES.find(s => s.value === selectedLead.stage)?.label}
                          </span>
                        )}
                        <span className="text-xs text-text-muted font-mono">Score: {selectedLead.score}</span>
                      </div>
                    </div>
                  </>
                )}
              </div>
              <button
                onClick={() => setSelectedLead(null)}
                className="w-8 h-8 rounded-[var(--radius-md)] bg-surface border border-border flex items-center justify-center text-text-muted hover:text-text-primary transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="flex border-b border-border">
              {(['Overview', 'Activity', 'Notes'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={cn(
                    'flex-1 py-3 text-sm font-medium transition-colors border-b-2',
                    activeTab === tab
                      ? 'text-accent border-accent'
                      : 'text-text-muted border-transparent hover:text-text-secondary'
                  )}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-6">
              {activeTab === 'Overview' && selectedLead && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <p className="text-xs text-text-muted">Email</p>
                      <p className="text-sm text-text-primary">{selectedLead.contact?.email || '—'}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-text-muted">Phone</p>
                      <p className="text-sm text-text-primary">{selectedLead.contact?.phone || '—'}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-text-muted">Source</p>
                      <p className="text-sm capitalize">{selectedLead.source.replace('_', ' ')}</p>
                    </div>
                    <div className="space-y-1">
                      <p className="text-xs text-text-muted">Created</p>
                      <p className="text-sm text-text-muted">
                        {new Date(selectedLead.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {activeTab === 'Activity' && (
                <div className="space-y-3">
                  <p className="text-sm text-text-muted">No activity recorded yet.</p>
                </div>
              )}
              {activeTab === 'Notes' && (
                <div className="space-y-3">
                  <textarea
                    className="w-full h-32 rounded-[var(--radius-md)] border border-border bg-surface p-3 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent resize-none"
                    placeholder="Add a note..."
                  />
                  <button className="px-4 py-2 rounded-[var(--radius-md)] bg-accent text-background text-sm font-medium hover:bg-accent-hover">
                    Save Note
                  </button>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-border flex gap-3">
              <Button variant="outline" className="flex-1 gap-2" onClick={() => setSelectedLead(null)}>
                <X className="h-4 w-4" />
                Close
              </Button>
              <Button className="flex-1 gap-2">
                <Mail className="h-4 w-4" />
                Send Email
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      )}

      {showCreateModal && (
        <Dialog open={showCreateModal} onOpenChange={() => setShowCreateModal(false)}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Add New Lead</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="first_name">First Name</Label>
                  <Input 
                    id="first_name" 
                    value={newLead.contact.first_name}
                    onChange={(e) => setNewLead({ ...newLead, contact: { ...newLead.contact, first_name: e.target.value } })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="last_name">Last Name</Label>
                  <Input 
                    id="last_name" 
                    value={newLead.contact.last_name}
                    onChange={(e) => setNewLead({ ...newLead, contact: { ...newLead.contact, last_name: e.target.value } })}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input 
                  id="email" 
                  type="email"
                  value={newLead.contact.email}
                  onChange={(e) => setNewLead({ ...newLead, contact: { ...newLead.contact, email: e.target.value } })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone">Phone</Label>
                <Input 
                  id="phone" 
                  value={newLead.contact.phone}
                  onChange={(e) => setNewLead({ ...newLead, contact: { ...newLead.contact, phone: e.target.value } })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="source">Source</Label>
                <Select value={newLead.source} onValueChange={(v) => setNewLead({ ...newLead, source: v as LeadSource })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {SOURCES.map(s => (
                      <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreateLead}>Create Lead</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}