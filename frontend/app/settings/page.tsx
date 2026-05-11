'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Mail, Linkedin, Phone, Save, Check, AlertCircle, ToggleLeft, ToggleRight } from 'lucide-react'

export default function SettingsPage() {
  const [emailConfig, setEmailConfig] = useState({
    smtp_host: '',
    smtp_port: '587',
    smtp_user: '',
    smtp_pass: '',
  })
  const [linkedinConfig, setLinkedinConfig] = useState({
    cookies: '',
    apollo_key: '',
  })
  const [twilioConfig, setTwilioConfig] = useState({
    account_sid: '',
    auth_token: '',
  })
  const [outreachApproval, setOutreachApproval] = useState(true)
  const [saving, setSaving] = useState<string | null>(null)
  const [saved, setSaved] = useState<string | null>(null)

  async function handleSave(config: Record<string, string>, endpoint: string, section: string) {
    setSaving(section)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (!res.ok) throw new Error('Failed to save')
      setSaved(section)
      setTimeout(() => setSaved(null), 2000)
    } catch (e) {
      console.error('Failed to save settings', e)
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-1">Configure your integrations and preferences</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="group hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Mail className="h-4 w-4 text-blue-400" />
              </div>
              Email Configuration
            </CardTitle>
            <CardDescription>SMTP settings for outbound email campaigns</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor="smtp_host" className="text-sm font-medium">SMTP Host</Label>
                <Input
                  id="smtp_host"
                  placeholder="smtp.gmail.com"
                  value={emailConfig.smtp_host}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_host: e.target.value })}
                  className="bg-secondary/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_port" className="text-sm font-medium">SMTP Port</Label>
                <Input
                  id="smtp_port"
                  placeholder="587"
                  value={emailConfig.smtp_port}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: e.target.value })}
                  className="bg-secondary/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_user" className="text-sm font-medium">SMTP Username</Label>
                <Input
                  id="smtp_user"
                  type="email"
                  placeholder="your@email.com"
                  value={emailConfig.smtp_user}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_user: e.target.value })}
                  className="bg-secondary/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="smtp_pass" className="text-sm font-medium">SMTP Password</Label>
                <Input
                  id="smtp_pass"
                  type="password"
                  placeholder="••••••••"
                  value={emailConfig.smtp_pass}
                  onChange={(e) => setEmailConfig({ ...emailConfig, smtp_pass: e.target.value })}
                  className="bg-secondary/50"
                />
              </div>
            </div>
            <Button 
              onClick={() => handleSave(emailConfig, '/api/settings/email', 'email')} 
              disabled={saving !== null}
              className="gap-2 w-full"
            >
              {saved === 'email' ? (
                <>
                  <Check className="h-4 w-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  {saving === 'email' ? 'Saving...' : 'Save Email Settings'}
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="group hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex items-center justify-center">
                <Linkedin className="h-4 w-4 text-sky-400" />
              </div>
              LinkedIn Configuration
            </CardTitle>
            <CardDescription>Cookies and API keys for LinkedIn outreach</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="linkedin_cookies" className="text-sm font-medium">LinkedIn Cookies</Label>
                <Input
                  id="linkedin_cookies"
                  type="password"
                  placeholder="li_at=..."
                  value={linkedinConfig.cookies}
                  onChange={(e) => setLinkedinConfig({ ...linkedinConfig, cookies: e.target.value })}
                  className="bg-secondary/50 font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="apollo_key" className="text-sm font-medium">Apollo.io API Key</Label>
                <Input
                  id="apollo_key"
                  placeholder="your Apollo API key"
                  value={linkedinConfig.apollo_key}
                  onChange={(e) => setLinkedinConfig({ ...linkedinConfig, apollo_key: e.target.value })}
                  className="bg-secondary/50"
                />
              </div>
            </div>
            <Button 
              onClick={() => handleSave(linkedinConfig, '/api/settings/linkedin', 'linkedin')} 
              disabled={saving !== null}
              className="gap-2 w-full"
            >
              {saved === 'linkedin' ? (
                <>
                  <Check className="h-4 w-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  {saving === 'linkedin' ? 'Saving...' : 'Save LinkedIn Settings'}
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="group hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <Phone className="h-4 w-4 text-emerald-400" />
              </div>
              Twilio Configuration
            </CardTitle>
            <CardDescription>Phone integration for call logging</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="twilio_sid" className="text-sm font-medium">Account SID</Label>
                <Input
                  id="twilio_sid"
                  placeholder="AC..."
                  value={twilioConfig.account_sid}
                  onChange={(e) => setTwilioConfig({ ...twilioConfig, account_sid: e.target.value })}
                  className="bg-secondary/50 font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="twilio_token" className="text-sm font-medium">Auth Token</Label>
                <Input
                  id="twilio_token"
                  type="password"
                  placeholder="••••••••"
                  value={twilioConfig.auth_token}
                  onChange={(e) => setTwilioConfig({ ...twilioConfig, auth_token: e.target.value })}
                  className="bg-secondary/50"
                />
              </div>
            </div>
            <Button 
              onClick={() => handleSave(twilioConfig, '/api/settings/twilio', 'twilio')} 
              disabled={saving !== null}
              className="gap-2 w-full"
            >
              {saved === 'twilio' ? (
                <>
                  <Check className="h-4 w-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="h-4 w-4" />
                  {saving === 'twilio' ? 'Saving...' : 'Save Twilio Settings'}
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="group hover:border-primary/50 transition-all">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <AlertCircle className="h-4 w-4 text-amber-400" />
              </div>
              Outreach Approval
            </CardTitle>
            <CardDescription>Require human approval before sending outreach</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
              <div className="space-y-0.5">
                <p className="text-sm font-medium">Human-in-the-loop</p>
                <p className="text-xs text-muted-foreground">
                  When enabled, agents will pause and wait for your approval before sending outreach messages
                </p>
              </div>
              <button
                onClick={() => setOutreachApproval(!outreachApproval)}
                className={`relative p-3 rounded-full transition-all ${
                  outreachApproval ? 'bg-primary' : 'bg-secondary'
                }`}
              >
                {outreachApproval ? (
                  <ToggleRight className="h-6 w-6 text-primary-foreground" />
                ) : (
                  <ToggleLeft className="h-6 w-6 text-muted-foreground" />
                )}
              </button>
            </div>
            <div className="mt-4 flex items-center gap-2 text-sm">
              <Badge variant={outreachApproval ? 'default' : 'secondary'}>
                {outreachApproval ? 'Approval required' : 'Auto-approved'}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {outreachApproval ? 'Agents will create approval requests' : 'Agents will send automatically'}
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}