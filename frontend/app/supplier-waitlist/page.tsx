'use client'

import React, { useState } from 'react'
import { Bot, CheckCircle } from 'lucide-react'

interface FormData {
  company_name: string
  country: string
  business_email: string
  phone: string
  website: string
  industry: string
  production_capacity: string
  certifications: string[]
  exporting_to_eu: boolean
  description: string
}

interface FormErrors {
  company_name?: string
  country?: string
  business_email?: string
  industry?: string
  production_capacity?: string
}

export default function SupplierWaitlistPage() {
  const [formData, setFormData] = useState<FormData>({
    company_name: '',
    country: '',
    business_email: '',
    phone: '',
    website: '',
    industry: '',
    production_capacity: '',
    certifications: [],
    exporting_to_eu: false,
    description: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [waitlistPosition, setWaitlistPosition] = useState<number>(0)

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    if (!formData.company_name || formData.company_name.length < 2) {
      newErrors.company_name = 'Company name must be at least 2 characters'
    }

    if (!formData.country) {
      newErrors.country = 'Please select a country'
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!formData.business_email || !emailRegex.test(formData.business_email)) {
      newErrors.business_email = 'Please enter a valid business email'
    }

    if (!formData.industry) {
      newErrors.industry = 'Please select an industry'
    }

    if (!formData.production_capacity) {
      newErrors.production_capacity = 'Please select production capacity'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }))
    }
  }

  const handleCheckboxChange = (value: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      certifications: checked
        ? [...prev.certifications, value]
        : prev.certifications.filter(c => c !== value)
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) return

    setIsSubmitting(true)

    try {
      await new Promise(resolve => setTimeout(resolve, 1500))

      const position = Math.floor(Math.random() * 500) + 100
      setWaitlistPosition(position)
      setIsSubmitted(true)
    } catch (error) {
      console.error('Form submission failed:', error)
    } finally {
      setIsSubmitting(false)
    }
  }
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
              <Bot className="h-4 w-4 text-white" />
            </div>
            <span className="text-lg font-semibold text-slate-900">Agentic CRM</span>
          </div>
          <a
            href="#waitlist-form"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 transition-colors"
          >
            Join Waitlist
          </a>
        </div>
      </nav>

      <section className="relative overflow-hidden py-24 md:py-32 bg-gradient-to-b from-slate-50 to-white">
        <div className="absolute inset-0 opacity-40" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, #cbd5e1 1px, transparent 0)', backgroundSize: '24px 24px' }} />
        <div className="max-w-6xl mx-auto px-6 relative z-10">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 leading-tight">
              Connecting Turkish & EU Suppliers to AI-Powered Procurement
            </h1>
            <p className="text-lg md:text-xl text-slate-600 mb-10">
              Be first to access our network of verified manufacturers. Join the waitlist for early access.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-8 mb-10">
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                500+ Suppliers
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                24/7 AI Matching
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-700">
                <svg className="w-5 h-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                EU GDPR Compliant
              </div>
            </div>
            <a
              href="#waitlist-form"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-indigo-500 text-white font-semibold hover:bg-indigo-600 transition-all hover:scale-[1.02] active:scale-[0.98] text-lg"
            >
              Join the Waitlist
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" /></svg>
            </a>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-16">Why Join Our Network?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all">
              <div className="w-14 h-14 rounded-xl bg-indigo-100 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Verified Suppliers</h3>
              <p className="text-slate-600">Every supplier is vetted by our team. No fraud, no risk — only trusted partners in our network.</p>
            </div>
            <div className="p-8 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all">
              <div className="w-14 h-14 rounded-xl bg-indigo-100 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">AI Matching</h3>
              <p className="text-slate-600">Our AI analyzes your capabilities and automatically matches you with relevant RFQs from buyers.</p>
            </div>
            <div className="p-8 rounded-2xl border border-slate-200 hover:border-indigo-300 hover:shadow-lg transition-all">
              <div className="w-14 h-14 rounded-xl bg-indigo-100 flex items-center justify-center mb-6">
                <svg className="w-7 h-7 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>
              </div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Fast Onboarding</h3>
              <p className="text-slate-600">Get verified and active in under 48 hours. Our streamlined process removes all friction.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-slate-50">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-slate-900 text-center mb-16">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">1</div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Submit Details</h3>
              <p className="text-slate-600">Fill out the supplier form in under 5 minutes. No lengthy paperwork.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">2</div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Get Verified</h3>
              <p className="text-slate-600">Our team reviews and verifies your business credentials and capabilities.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center text-2xl font-bold mx-auto mb-6">3</div>
              <h3 className="text-xl font-semibold text-slate-900 mb-3">Access Network</h3>
              <p className="text-slate-600">Start receiving AI-matched RFQs from verified buyers across the EU.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-24 bg-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-16 items-center mb-24">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 mb-6">Reach EU Buyers</h2>
              <p className="text-slate-600 text-lg mb-6">
                Expand your customer base beyond Turkey. Our platform connects you directly with procurement teams across the European Union, opening doors to new revenue streams.
              </p>
              <ul className="space-y-3">
                <li className="flex items-center gap-3 text-slate-700">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Direct access to enterprise buyers
                </li>
                <li className="flex items-center gap-3 text-slate-700">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Multi-language support
                </li>
                <li className="flex items-center gap-3 text-slate-700">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  EU compliance built-in
                </li>
              </ul>
            </div>
            <div className="h-64 bg-gradient-to-br from-indigo-100 to-indigo-200 rounded-2xl flex items-center justify-center">
              <svg className="w-32 h-32 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
          </div>
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div className="h-64 bg-gradient-to-br from-emerald-100 to-emerald-200 rounded-2xl flex items-center justify-center order-2 md:order-1">
              <svg className="w-32 h-32 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" /></svg>
            </div>
            <div className="order-1 md:order-2">
              <h2 className="text-3xl font-bold text-slate-900 mb-6">AI-Powered Matching</h2>
              <p className="text-slate-600 text-lg mb-6">
                Our intelligent system analyzes thousands of data points to find the perfect buyer-supplier matches. Stop wasting time on cold leads — every connection is qualified by our AI.
              </p>
              <ul className="space-y-3">
                <li className="flex items-center gap-3 text-slate-700">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Automatic capability mapping
                </li>
                <li className="flex items-center gap-3 text-slate-700">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Real-time RFQ prioritization
                </li>
                <li className="flex items-center gap-3 text-slate-700">
                  <svg className="w-5 h-5 text-emerald-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  90%+ match accuracy
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section id="waitlist-form" className="py-24 bg-slate-50">
        <div className="max-w-2xl mx-auto px-6">
          <div className="bg-white rounded-2xl shadow-xl p-8 md:p-12">
            {isSubmitted ? (
              <div className="text-center py-12">
                <div className="w-20 h-20 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-6">
                  <CheckCircle className="w-10 h-10 text-emerald-500" />
                </div>
                <h2 className="text-3xl font-bold text-slate-900 mb-4">You're on the list!</h2>
                <p className="text-slate-600 mb-6">We'll be in touch soon with updates about our launch.</p>
                <div className="inline-flex items-center gap-2 px-6 py-3 bg-indigo-50 rounded-xl">
                  <span className="text-sm text-slate-600">Your position:</span>
                  <span className="text-2xl font-bold text-indigo-600">#{waitlistPosition}</span>
                </div>
              </div>
            ) : (
              <>
                <div className="text-center mb-10">
                  <h2 className="text-3xl font-bold text-slate-900 mb-4">Join the Supplier Waitlist</h2>
                  <p className="text-slate-600">Be among the first to access our network when we launch.</p>
                </div>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div>
                    <label htmlFor="company_name" className="block text-sm font-medium text-slate-700 mb-2">Company Name *</label>
                    <input
                      type="text"
                      id="company_name"
                      name="company_name"
                      required
                      minLength={2}
                      value={formData.company_name}
                      onChange={handleInputChange}
                      className={`w-full h-11 px-4 rounded-lg border ${errors.company_name ? 'border-red-500 focus:ring-red-500' : 'border-slate-300 focus:ring-indigo-500'} focus:outline-none focus:ring-2 focus:border-indigo-500`}
                      placeholder="Acme Manufacturing"
                    />
                    {errors.company_name && <p className="mt-1 text-sm text-red-500">{errors.company_name}</p>}
                  </div>
                  <div>
                    <label htmlFor="country" className="block text-sm font-medium text-slate-700 mb-2">Country *</label>
                    <select
                      id="country"
                      name="country"
                      required
                      value={formData.country}
                      onChange={handleInputChange}
                      className={`w-full h-11 px-4 rounded-lg border ${errors.country ? 'border-red-500 focus:ring-red-500' : 'border-slate-300 focus:ring-indigo-500'} focus:outline-none focus:ring-2 focus:border-indigo-500 bg-white`}
                    >
                      <option value="">Select country</option>
                      <optgroup label="Turkey">
                        <option value="TR">Turkey</option>
                      </optgroup>
                      <optgroup label="European Union">
                        <option value="AT">Austria</option>
                        <option value="BE">Belgium</option>
                        <option value="BG">Bulgaria</option>
                        <option value="HR">Croatia</option>
                        <option value="CY">Cyprus</option>
                        <option value="CZ">Czech Republic</option>
                        <option value="DK">Denmark</option>
                        <option value="EE">Estonia</option>
                        <option value="FI">Finland</option>
                        <option value="FR">France</option>
                        <option value="DE">Germany</option>
                        <option value="GR">Greece</option>
                        <option value="HU">Hungary</option>
                        <option value="IE">Ireland</option>
                        <option value="IT">Italy</option>
                        <option value="LV">Latvia</option>
                        <option value="LT">Lithuania</option>
                        <option value="LU">Luxembourg</option>
                        <option value="MT">Malta</option>
                        <option value="NL">Netherlands</option>
                        <option value="PL">Poland</option>
                        <option value="PT">Portugal</option>
                        <option value="RO">Romania</option>
                        <option value="SK">Slovakia</option>
                        <option value="SI">Slovenia</option>
                        <option value="ES">Spain</option>
                        <option value="SE">Sweden</option>
                      </optgroup>
                    </select>
                    {errors.country && <p className="mt-1 text-sm text-red-500">{errors.country}</p>}
                  </div>
                  <div>
                    <label htmlFor="business_email" className="block text-sm font-medium text-slate-700 mb-2">Business Email *</label>
                    <input
                      type="email"
                      id="business_email"
                      name="business_email"
                      required
                      value={formData.business_email}
                      onChange={handleInputChange}
                      className={`w-full h-11 px-4 rounded-lg border ${errors.business_email ? 'border-red-500 focus:ring-red-500' : 'border-slate-300 focus:ring-indigo-500'} focus:outline-none focus:ring-2 focus:border-indigo-500`}
                      placeholder="contact@company.com"
                    />
                    {errors.business_email && <p className="mt-1 text-sm text-red-500">{errors.business_email}</p>}
                  </div>
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-slate-700 mb-2">Phone Number</label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      className="w-full h-11 px-4 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="+90 212 555 0100"
                    />
                  </div>
                  <div>
                    <label htmlFor="website" className="block text-sm font-medium text-slate-700 mb-2">Company Website</label>
                    <input
                      type="url"
                      id="website"
                      name="website"
                      value={formData.website}
                      onChange={handleInputChange}
                      className="w-full h-11 px-4 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="https://www.company.com"
                    />
                  </div>
                  <div>
                    <label htmlFor="industry" className="block text-sm font-medium text-slate-700 mb-2">Industry / Category *</label>
                    <select
                      id="industry"
                      name="industry"
                      required
                      value={formData.industry}
                      onChange={handleInputChange}
                      className={`w-full h-11 px-4 rounded-lg border ${errors.industry ? 'border-red-500 focus:ring-red-500' : 'border-slate-300 focus:ring-indigo-500'} focus:outline-none focus:ring-2 focus:border-indigo-500 bg-white`}
                    >
                      <option value="">Select industry</option>
                      <option value="electronics">Electronics & Components</option>
                      <option value="automotive">Automotive Parts</option>
                      <option value="textile">Textile & Garments</option>
                      <option value="food">Food & Beverages</option>
                      <option value="machinery">Machinery & Equipment</option>
                      <option value="chemicals">Chemicals & Materials</option>
                      <option value="furniture">Furniture & Fixtures</option>
                      <option value="other">Other</option>
                    </select>
                    {errors.industry && <p className="mt-1 text-sm text-red-500">{errors.industry}</p>}
                  </div>
                  <div>
                    <label htmlFor="production_capacity" className="block text-sm font-medium text-slate-700 mb-2">Annual Production Capacity *</label>
                    <select
                      id="production_capacity"
                      name="production_capacity"
                      required
                      value={formData.production_capacity}
                      onChange={handleInputChange}
                      className={`w-full h-11 px-4 rounded-lg border ${errors.production_capacity ? 'border-red-500 focus:ring-red-500' : 'border-slate-300 focus:ring-indigo-500'} focus:outline-none focus:ring-2 focus:border-indigo-500 bg-white`}
                    >
                      <option value="">Select capacity range</option>
                      <option value="under_100k">Under $100K</option>
                      <option value="100k_500k">$100K - $500K</option>
                      <option value="500k_1m">$500K - $1M</option>
                      <option value="1m_5m">$1M - $5M</option>
                      <option value="5m_10m">$5M - $10M</option>
                      <option value="over_10m">Over $10M</option>
                    </select>
                    {errors.production_capacity && <p className="mt-1 text-sm text-red-500">{errors.production_capacity}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-3">Certifications (optional)</label>
                    <div className="grid grid-cols-2 gap-3">
                      {['CE', 'ISO9001', 'ISO14001', 'IATF16949'].map(cert => (
                        <label key={cert} className="flex items-center gap-2 cursor-pointer">
                          <input
                            type="checkbox"
                            name="certifications"
                            value={cert}
                            checked={formData.certifications.includes(cert)}
                            onChange={(e) => handleCheckboxChange(cert, e.target.checked)}
                            className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500"
                          />
                          <span className="text-sm text-slate-700">{cert}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        name="exporting_to_eu"
                        checked={formData.exporting_to_eu}
                        onChange={(e) => setFormData(prev => ({ ...prev, exporting_to_eu: e.target.checked }))}
                        className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-slate-700">Currently exporting to EU countries</span>
                    </label>
                  </div>
                  <div>
                    <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-2">Brief Company Description</label>
                    <textarea
                      id="description"
                      name="description"
                      rows={3}
                      maxLength={500}
                      value={formData.description}
                      onChange={handleInputChange}
                      className="w-full px-4 py-3 rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                      placeholder="Tell us about your company, products, and capabilities..."
                    />
                    <p className="mt-1 text-xs text-slate-500 text-right">{formData.description.length}/500</p>
                  </div>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full h-12 rounded-xl bg-indigo-500 text-white font-semibold hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isSubmitting ? (
                      <>
                        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                        </svg>
                        Submitting...
                      </>
                    ) : 'Submit Application'}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </section>

      <footer className="py-12 bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <span className="text-sm font-medium">Agentic CRM — Connecting Suppliers Globally</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-slate-400">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
            <p className="text-sm text-slate-400">© 2026 Artflarex Solutions</p>
          </div>
        </div>
      </footer>
    </div>
  )
}