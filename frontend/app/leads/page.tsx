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
import { Search, Filter, Plus, X, ExternalLink, Mail, Phone, Building } from 'lucide-react'

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

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newLead, setNewLead] = useState({ contact: { first_name: '', last_name: '', email: '', phone: '', company: '' }, source: 'web' as LeadSource })

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
      await api.leads.create({ contact_id: contact.id, source: newLead.source, stage: 'new', score: 50 })
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
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
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
                    className="cursor-pointer hover:bg-secondary/30 transition-colors"
                    onClick={() => setSelectedLead(lead)}
                  >
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <span className="text-xs font-medium text-primary">
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
                      <Badge variant="outline" className="font-normal">{lead.source.replace('_', ' ')}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge className={`${stage?.bgColor} ${stage?.color} border-0`}>
                        {stage?.label}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-secondary">
                          <div 
                            className={`h-full rounded-full ${
                              lead.score >= 70 ? 'bg-emerald-400' : 
                              lead.score >= 40 ? 'bg-amber-400' : 'bg-red-400'
                            }`} 
                            style={{ width: `${lead.score}%` }}
                          />
                        </div>
                        <span className="text-sm font-mono">{lead.score}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {lead.last_contacted_at
                        ? new Date(lead.last_contacted_at).toLocaleDateString()
                        : 'Never'}
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

      {selectedLead && (
        <Dialog open={!!selectedLead} onOpenChange={() => setSelectedLead(null)}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <span className="text-sm font-medium text-primary">
                    {selectedLead.contact?.first_name?.[0]}{selectedLead.contact?.last_name?.[0]}
                  </span>
                </div>
                {selectedLead.contact?.first_name} {selectedLead.contact?.last_name}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Email</p>
                  <p className="text-sm font-medium">{selectedLead.contact?.email || 'Not provided'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Phone</p>
                  <p className="text-sm font-medium">{selectedLead.contact?.phone || 'Not provided'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Company</p>
                  <p className="text-sm font-medium">{selectedLead.contact?.company_id ? `Company #${selectedLead.contact.company_id}` : 'Not provided'}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-xs text-muted-foreground">Source</p>
                  <Badge variant="outline">{selectedLead.source.replace('_', ' ')}</Badge>
                </div>
              </div>
              <div className="flex items-center justify-between pt-4 border-t">
                <div className="flex items-center gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Stage</p>
                    <Badge className={stageColors[selectedLead.stage]}>
                      {STAGES.find(s => s.value === selectedLead.stage)?.label}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground">Score</p>
                    <p className="text-sm font-mono font-medium">{selectedLead.score}</p>
                  </div>
                </div>
                {selectedLead.contact?.linkedin_url && (
                  <Button variant="outline" size="sm" asChild>
                    <a href={selectedLead.contact.linkedin_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      LinkedIn
                    </a>
                  </Button>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedLead(null)}>Close</Button>
              <Button>Edit Lead</Button>
            </DialogFooter>
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