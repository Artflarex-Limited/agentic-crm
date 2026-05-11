'use client'

import { useEffect, useState } from 'react'
import { api, type Lead, type LeadStage, type LeadSource } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Search, Filter } from 'lucide-react'

const STAGES: { value: LeadStage; label: string }[] = [
  { value: 'new', label: 'New' },
  { value: 'contacted', label: 'Contacted' },
  { value: 'qualified', label: 'Qualified' },
  { value: 'proposal', label: 'Proposal' },
  { value: 'negotiation', label: 'Negotiation' },
  { value: 'won', label: 'Won' },
  { value: 'lost', label: 'Lost' },
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

const stageColors: Record<LeadStage, string> = {
  new: 'bg-blue-100 text-blue-800',
  contacted: 'bg-yellow-100 text-yellow-800',
  qualified: 'bg-green-100 text-green-800',
  proposal: 'bg-orange-100 text-orange-800',
  negotiation: 'bg-purple-100 text-purple-800',
  won: 'bg-green-200 text-green-900',
  lost: 'bg-red-100 text-red-800',
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [stageFilter, setStageFilter] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<string>('')

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
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [search, stageFilter, sourceFilter])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">Leads</h2>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
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
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Company</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Stage</TableHead>
                <TableHead>Score</TableHead>
                <TableHead>Last Contacted</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {leads.map(lead => (
                <TableRow key={lead.id}>
                  <TableCell className="font-medium">
                    {lead.contact?.first_name} {lead.contact?.last_name}
                  </TableCell>
                  <TableCell>{lead.contact?.email || '-'}</TableCell>
                  <TableCell>{lead.contact?.company?.name || '-'}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{lead.source}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={stageColors[lead.stage]}>{lead.stage}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={lead.score >= 70 ? 'default' : 'secondary'}>
                      {lead.score}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {lead.last_contacted_at
                      ? new Date(lead.last_contacted_at).toLocaleDateString()
                      : 'Never'}
                  </TableCell>
                </TableRow>
              ))}
              {leads.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                    No leads found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}