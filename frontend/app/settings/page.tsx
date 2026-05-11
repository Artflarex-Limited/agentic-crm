'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Save, Mail, Linkedin, Phone } from 'lucide-react'

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
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  async function handleSave(config: Record<string, string>, endpoint: string) {
    setSaving(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      if (!res.ok) throw new Error('Failed to save')
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch (e) {
      console.error('Failed to save settings', e)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight">Settings</h2>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Configuration
          </CardTitle>
          <CardDescription>SMTP settings for outbound email campaigns</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="smtp_host">SMTP Host</Label>
              <Input
                id="smtp_host"
                placeholder="smtp.gmail.com"
                value={emailConfig.smtp_host}
                onChange={(e) => setEmailConfig({ ...emailConfig, smtp_host: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_port">SMTP Port</Label>
              <Input
                id="smtp_port"
                placeholder="587"
                value={emailConfig.smtp_port}
                onChange={(e) => setEmailConfig({ ...emailConfig, smtp_port: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_user">SMTP Username</Label>
              <Input
                id="smtp_user"
                type="email"
                placeholder="your@email.com"
                value={emailConfig.smtp_user}
                onChange={(e) => setEmailConfig({ ...emailConfig, smtp_user: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="smtp_pass">SMTP Password</Label>
              <Input
                id="smtp_pass"
                type="password"
                placeholder="••••••••"
                value={emailConfig.smtp_pass}
                onChange={(e) => setEmailConfig({ ...emailConfig, smtp_pass: e.target.value })}
              />
            </div>
          </div>
          <Button onClick={() => handleSave(emailConfig, '/api/settings/email')} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saved ? 'Saved!' : 'Save Email Settings'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Linkedin className="h-5 w-5" />
            LinkedIn Configuration
          </CardTitle>
          <CardDescription>Cookies and API keys for LinkedIn outreach</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="linkedin_cookies">LinkedIn Cookies</Label>
              <Input
                id="linkedin_cookies"
                type="password"
                placeholder="li_at=..."
                value={linkedinConfig.cookies}
                onChange={(e) => setLinkedinConfig({ ...linkedinConfig, cookies: e.target.value })}
              />
            </div>
            <div className="space-y-2 md:col-span-2">
              <Label htmlFor="apollo_key">Apollo.io API Key</Label>
              <Input
                id="apollo_key"
                placeholder="your Apollo API key"
                value={linkedinConfig.apollo_key}
                onChange={(e) => setLinkedinConfig({ ...linkedinConfig, apollo_key: e.target.value })}
              />
            </div>
          </div>
          <Button onClick={() => handleSave(linkedinConfig, '/api/settings/linkedin')} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saved ? 'Saved!' : 'Save LinkedIn Settings'}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Phone className="h-5 w-5" />
            Twilio Configuration
          </CardTitle>
          <CardDescription>Phone integration for call logging</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="twilio_sid">Account SID</Label>
              <Input
                id="twilio_sid"
                placeholder="AC..."
                value={twilioConfig.account_sid}
                onChange={(e) => setTwilioConfig({ ...twilioConfig, account_sid: e.target.value })}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="twilio_token">Auth Token</Label>
              <Input
                id="twilio_token"
                type="password"
                placeholder="••••••••"
                value={twilioConfig.auth_token}
                onChange={(e) => setTwilioConfig({ ...twilioConfig, auth_token: e.target.value })}
              />
            </div>
          </div>
          <Button onClick={() => handleSave(twilioConfig, '/api/settings/twilio')} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saved ? 'Saved!' : 'Save Twilio Settings'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}