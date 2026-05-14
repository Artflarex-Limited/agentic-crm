'use client'

import { useEffect, useRef, type FormEvent } from 'react'
import { identifyHubSpotContact, getStoredUTM, trackFormSubmission, trackRFQGenerated } from '@/lib/tracking'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface HubSpotFormProps {
  formId: string
  portalId: string
  title?: string
  onSubmit?: (data: Record<string, string>) => void
  onSuccess?: (email: string) => void
  isRFQForm?: boolean
}

export function HubSpotForm({
  formId,
  portalId,
  title = 'Contact Us',
  onSubmit,
  onSuccess,
  isRFQForm = false,
}: HubSpotFormProps) {
  const formRef = useRef<HTMLFormElement>(null)

  useEffect(() => {
    const storedUTM = getStoredUTM()
    if (formRef.current && storedUTM.utm_source) {
      const utmSourceInput = formRef.current.querySelector<HTMLInputElement>('input[name="utm_source"]')
      if (utmSourceInput) utmSourceInput.value = storedUTM.utm_source || ''
    }
  }, [])

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const data: Record<string, string> = {}
    const formData = new FormData(form)
    formData.forEach((value, key) => {
      data[key] = value.toString()
    })

    if (isRFQForm) {
      const utm = getStoredUTM()
      trackRFQGenerated(utm)
    }

    onSubmit?.(data)

    const email = data['email'] || data['email_address'] || ''
    if (email) {
      identifyHubSpotContact(email, data)
    }

    const script = document.createElement('script')
    script.src = `https://js.hsforms.net/forms/embed/v2/form.js?portalId=${portalId}&formId=${formId}`
    script.async = true
    script.defer = true
    script.onload = () => {
      if (typeof window !== 'undefined' && (window as unknown as { hbspt?: { forms?: { create: (config: unknown) => void } } }).hbspt) {
        ;(window as unknown as { hbspt: { forms: { create: (config: unknown) => void } } }).hbspt.forms.create({
          portalId,
          formId,
          target: `#hs-form-${formId}`,
          values: data,
        })
      }
      trackFormSubmission(`hubspot_form_${formId}`, true)
      onSuccess?.(email)
    }
    document.head.appendChild(script)
    trackFormSubmission(`hubspot_form_${formId}`, true)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <form
          ref={formRef}
          id={`hs-form-${formId}`}
          onSubmit={handleSubmit}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label htmlFor="firstname">First Name</Label>
            <Input
              id="firstname"
              name="firstname"
              type="text"
              placeholder="John"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="lastname">Last Name</Label>
            <Input
              id="lastname"
              name="lastname"
              type="text"
              placeholder="Doe"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              name="email"
              type="email"
              placeholder="john@company.com"
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="company">Company</Label>
            <Input
              id="company"
              name="company"
              type="text"
              placeholder="Acme Inc"
            />
          </div>
          <div className="space-y-2" style={{ display: 'none' }}>
            <Input
              id="utm_source"
              name="utm_source"
              type="text"
              autoComplete="off"
            />
          </div>
          <Button type="submit" className="w-full">
            Submit
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}

export function HubSpotInlineForm({
  formId,
  portalId,
  onSuccess,
}: {
  formId: string
  portalId: string
  onSuccess?: (email: string) => void
}) {
  useEffect(() => {
    const script = document.createElement('script')
    script.src = `https://js.hsforms.net/forms/embed/v2/form.js?portalId=${portalId}&formId=${formId}`
    script.async = true
    script.defer = true
    document.head.appendChild(script)

    const storedUTM = getStoredUTM()
    if (storedUTM.utm_source) {
      const sourceInput = document.querySelector<HTMLInputElement>(`#hs-form-${formId} input[name="utm_source"]`)
      if (sourceInput) sourceInput.value = storedUTM.utm_source || ''
    }

    return () => {
      document.head.removeChild(script)
    }
  }, [formId, portalId])

  return (
    <div
      id={`hs-form-${formId}`}
      className="hubspot-form-container"
      data-utm-source={getStoredUTM().utm_source}
    />
  )
}