'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Plane, Search, Loader2, Clock, Phone, Mail, AlertCircle, CheckCircle2, Flame, FileText, PlaneTakeoff } from 'lucide-react'
import { WorldMapSelector } from '@/components/world-map-selector'

interface TowerHour {
  day: string
  hours: string
}

interface Contact {
  type: string
  name?: string
  phone?: string
  email?: string
}

interface AirportInfo {
  airportCode: string
  airportName: string
  contacts?: Contact[]
  // Country info
  country?: string
  region?: string
  flag?: string
  // AD 2.3 OPERATIONAL HOURS section
  adAdministration?: string
  adOperator?: string
  customsAndImmigration?: string
  ats?: string
  operationalRemarks?: string
  // AD 2.2 AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA
  trafficTypes?: string
  administrativeRemarks?: string
  // AD 2.6 RESCUE AND FIREFIGHTING SERVICES
  fireFightingCategory?: string
  error?: string
}

interface NotamEntry {
  header?: string
  raw?: string
  [key: string]: string | undefined
}

interface NotamResult {
  success: boolean
  airport?: string
  entries: NotamEntry[]
  logs: string[]
  error?: string
}

interface AirportApiResponse {
  success: boolean
  airport: AirportInfo
  notams?: NotamResult
  error?: string
}

export default function Home() {
  const [airportCode, setAirportCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [airportInfo, setAirportInfo] = useState<AirportInfo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notamResult, setNotamResult] = useState<NotamResult | null>(null)
  const [notamDialogOpen, setNotamDialogOpen] = useState(false)

  const searchAirport = async (code?: string) => {
    const codeToSearch = code || airportCode
    if (!codeToSearch.trim()) {
      setError('Please enter an airport code')
      return
    }

    if (codeToSearch.length < 3) {
      setError('Airport code must be at least 3 characters')
      return
    }

    setLoading(true)
    setProgress(0)
    setError(null)
    setAirportInfo(null)
    setNotamResult(null)
    setNotamDialogOpen(false)
    
    // Update airportCode state if code was provided
    if (code) {
      setAirportCode(code)
    }

    // Simulate progress updates
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return 90
        return prev + 10
      })
    }, 200)

    try {
      // Hardcode Railway URL for production
      const apiUrl = 'https://web-production-e7af.up.railway.app'
      const response = await fetch(`${apiUrl}/api/airport`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ airportCode: codeToSearch.toUpperCase() })
      })

      const data: AirportApiResponse = await response.json()

      // Complete the progress bar
      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok || !data.success) {
        throw new Error(data.error || 'Failed to fetch airport information')
      }

      setAirportInfo(data.airport)
      setNotamResult(data.notams ?? null)
      
      // Small delay to show completion
      setTimeout(() => {
        setLoading(false)
        setProgress(0)
      }, 300)
    } catch (err) {
      clearInterval(progressInterval)
      setProgress(0)
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
      setLoading(false)
    }
  }

  const [detectedCountry, setDetectedCountry] = useState<string>('')

  // Detect country from airport code using API
  const detectCountry = async (code: string) => {
    if (!code || code.length < 2) {
      setDetectedCountry('')
      return
    }

    try {
      const apiUrl = 'https://web-production-e7af.up.railway.app'
      const response = await fetch(`${apiUrl}/api/country`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ airportCode: code })
      })

      const data = await response.json()
      
      if (data.success && data.country) {
        const countryDisplay = `${data.country} ${data.flag || ''}`
        setDetectedCountry(countryDisplay)
      } else {
        setDetectedCountry('Unknown')
      }
    } catch (err) {
      console.error('Failed to detect country:', err)
      setDetectedCountry('Unknown')
    }
  }

  // Get country display string
  const getCountryDisplay = (code: string): string => {
    if (detectedCountry) return detectedCountry
    // Fallback for known prefixes
    if (code.startsWith('K')) return 'USA 🇺🇸'
    if (code.startsWith('LF')) return 'France 🇫🇷'
    if (code.startsWith('LO')) return 'Austria 🇦🇹'
    if (code.startsWith('LK')) return 'Czech Republic 🇨🇿'
    if (code.startsWith('EK')) return 'Denmark 🇩🇰'
    if (code.startsWith('EI')) return 'Ireland 🇮🇪'
    if (code.startsWith('LI')) return 'Italy 🇮🇹'
    return 'Unknown'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <Card className="w-full max-w-md shadow-2xl border-2 border-blue-200 bg-white dark:bg-gray-800">
            <CardContent className="pt-12 pb-8 px-8">
              <div className="flex flex-col items-center space-y-6">
                {/* Flying Plane Animation */}
                <div className="relative w-32 h-32 flex items-center justify-center">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full animate-pulse"></div>
                  <div className="absolute inset-2 bg-gradient-to-tr from-blue-400 to-indigo-500 rounded-full"></div>
                  <Plane className="absolute w-16 h-16 text-white" style={{ 
                    animation: 'fly 2s ease-in-out infinite'
                  }} />
                </div>
                {/* Loading Text */}
                <div className="text-center space-y-2">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                    Searching for Airport Info...
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400">
                    Please wait while we fetch the data
                  </p>
                </div>
                {/* Progress Bar */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-full transition-all duration-500 ease-out relative overflow-hidden"
                       style={{ width: `${progress}%` }}>
                    {/* Shimmer effect */}
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 text-center">
                    {progress < 90 ? `${progress}%` : 'Almost there...'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      
      <div className="w-full max-w-4xl space-y-6">
        {/* Header Card */}
        <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm dark:bg-gray-800/80">
          <CardHeader className="text-center pb-6">
            <div className="flex items-center justify-center gap-3 mb-4">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl">
                <Plane className="w-8 h-8 text-white" />
              </div>
              <CardTitle className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Airport AIP Lookup
              </CardTitle>
            </div>
            <CardDescription className="text-lg">
              Enter an ICAO airport code to get operational hours and contact information
            </CardDescription>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              <WorldMapSelector onAirportSelect={(code) => {
                setAirportCode(code)
                setError(null)
                // Auto-search with the selected code
                searchAirport(code)
              }} />
            </div>
            <div className="flex flex-wrap justify-center gap-2 mt-4">
              <Badge variant="outline" className="text-xs">K* - USA</Badge>
              <Badge variant="outline" className="text-xs">LF* - France</Badge>
              <Badge variant="outline" className="text-xs">LM* - Malta</Badge>
              <Badge variant="outline" className="text-xs">LG* - Greece</Badge>
              <Badge variant="outline" className="text-xs">EE* - Estonia</Badge>
              <Badge variant="outline" className="text-xs">EF* - Finland</Badge>
              <Badge variant="outline" className="text-xs">EY* - Lithuania</Badge>
              <Badge variant="outline" className="text-xs">EV* - Latvia</Badge>
              <Badge variant="outline" className="text-xs">OA* - Afghanistan</Badge>
              <Badge variant="outline" className="text-xs">HA* - Ethiopia</Badge>
            </div>
          </CardHeader>

          {/* Search Section */}
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="airport-code" className="text-base font-semibold">
                Airport Code
              </Label>
              <div className="flex gap-2">
                <Input
                  id="airport-code"
                  type="text"
                  placeholder="e.g., KJFK, LOWW, LKPR, EKCH"
                  value={airportCode}
                  onChange={(e) => {
                    const code = e.target.value.toUpperCase()
                    setAirportCode(code)
                    if (code.length >= 3) {
                      detectCountry(code)
                    } else {
                      setDetectedCountry('')
                    }
                  }}
                  onKeyPress={(e) => e.key === 'Enter' && searchAirport()}
                  className="flex-1 text-lg uppercase tracking-wider"
                  disabled={loading}
                />
                <Button 
                  onClick={() => searchAirport()} 
                  disabled={loading || !airportCode.trim()}
                  size="lg"
                  className="px-8"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="mr-2 h-5 w-5" />
                      Search
                    </>
                  )}
                </Button>
              </div>
              {airportCode && detectedCountry && (
                <p className="text-sm text-muted-foreground">
                  Region: {detectedCountry}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50 dark:bg-red-950 dark:border-red-900">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                <p className="text-red-700 dark:text-red-400 font-medium">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Display */}
        {airportInfo && !error && (
          <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm dark:bg-gray-800/80">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-3xl mb-2">{airportInfo.airportName}</CardTitle>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="text-lg px-3 py-1">
                      {airportInfo.airportCode}
                    </Badge>
                    {airportInfo.country && (
                      <Badge variant="outline" className="text-sm">
                        {airportInfo.country} {airportInfo.flag || ''}
                      </Badge>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {notamResult ? (
                    notamResult.success ? (
                      <Dialog open={notamDialogOpen} onOpenChange={setNotamDialogOpen}>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm" className="gap-2">
                            <FileText className="h-4 w-4" />
                            {notamResult.entries.length > 0
                              ? `View NOTAMs (${notamResult.entries.length})`
                              : 'View NOTAM logs'}
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-3xl max-h-[85vh] overflow-y-auto space-y-6">
                          <DialogHeader>
                            <DialogTitle>NOTAMs for {airportInfo.airportCode}</DialogTitle>
                            <DialogDescription>
                              {notamResult.entries.length > 0
                                ? `${notamResult.entries.length} NOTAM${notamResult.entries.length === 1 ? '' : 's'} fetched from the FAA portal.`
                                : 'No NOTAMs were returned for this query. Review the logs below for additional context.'}
                            </DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            {notamResult.entries.length > 0 ? (
                              notamResult.entries.map((entry, idx) => {
                                const detailEntries = Object.entries(entry).filter(
                                  ([key, value]) =>
                                    value &&
                                    key !== 'header' &&
                                    key !== 'raw'
                                ) as [string, string][]

                                return (
                                  <div
                                    key={`${entry.header || 'notam'}-${idx}`}
                                    className="rounded-lg border bg-background p-4 shadow-sm space-y-3"
                                  >
                                    <div className="flex items-start justify-between gap-3">
                                      <div>
                                        <h4 className="text-lg font-semibold">
                                          {entry.header || `NOTAM ${idx + 1}`}
                                        </h4>
                                        {entry.Location && (
                                          <p className="text-sm text-muted-foreground">
                                            Location: {entry.Location}
                                          </p>
                                        )}
                                      </div>
                                      {entry['Start Date/Time'] && (
                                        <Badge variant="outline" className="text-xs">
                                          Effective: {entry['Start Date/Time']}
                                        </Badge>
                                      )}
                                    </div>
                                    {entry.raw && (
                                      <p className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground">
                                        {entry.raw}
                                      </p>
                                    )}
                                    {detailEntries.length > 0 && (
                                      <div className="grid gap-2 text-sm">
                                        {detailEntries.map(([key, value]) => (
                                          <div
                                            key={key}
                                            className="flex items-baseline gap-2"
                                          >
                                            <span className="w-48 font-medium text-muted-foreground">
                                              {key}:
                                            </span>
                                            <span className="flex-1 text-foreground">
                                              {value}
                                            </span>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                )
                              })
                            ) : (
                              <p className="text-sm text-muted-foreground">
                                No NOTAM entries were returned for this airport code.
                              </p>
                            )}
                          </div>
                          {notamResult.logs.length > 0 && (
                            <div>
                              <h4 className="text-sm font-semibold text-muted-foreground mb-2">
                                Execution log
                              </h4>
                              <div className="max-h-48 overflow-y-auto rounded-md border bg-muted/30 p-3 text-xs font-mono space-y-1">
                                {notamResult.logs.map((entry, idx) => (
                                  <div key={idx} className="whitespace-pre-wrap">
                                    {entry}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </DialogContent>
                      </Dialog>
                    ) : (
                      <span className="text-sm text-red-500">
                        NOTAM fetch failed{notamResult.error ? `: ${notamResult.error}` : ''}
                      </span>
                    )
                  ) : null}
                  <CheckCircle2 className="h-8 w-8 text-green-500" />
                </div>
              </div>
            </CardHeader>

            <Separator />

            <CardContent className="space-y-6 pt-6">
              {/* AD 2.3 OPERATIONAL HOURS Section */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="h-5 w-5 text-indigo-600" />
                  <h3 className="text-xl font-semibold">AD 2.3 OPERATIONAL HOURS</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <span className="font-medium text-gray-900 dark:text-gray-100">AD Administration</span>
                    <Badge variant="outline" className="font-mono font-semibold">
                      {airportInfo.adAdministration || 'NIL'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <span className="font-medium text-gray-900 dark:text-gray-100">AD Operator</span>
                    <Badge variant="outline" className="font-mono font-semibold">
                      {airportInfo.adOperator || 'NIL'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <span className="font-medium text-gray-900 dark:text-gray-100">Customs and Immigration</span>
                    <Badge variant="outline" className="font-mono font-semibold">
                      {airportInfo.customsAndImmigration || 'NIL'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <span className="font-medium text-gray-900 dark:text-gray-100">ATS</span>
                    <Badge variant="outline" className="font-mono font-semibold">
                      {airportInfo.ats || 'NIL'}
                    </Badge>
                  </div>
                  {airportInfo.operationalRemarks && airportInfo.operationalRemarks !== 'NIL' && (
                    <div className="p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                      <span className="font-medium text-gray-900 dark:text-gray-100">Remarks: </span>
                      <span className="text-sm text-gray-700 dark:text-gray-300">{airportInfo.operationalRemarks}</span>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* Contacts */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Phone className="h-5 w-5 text-indigo-600" />
                  <h3 className="text-xl font-semibold">Contacts</h3>
                </div>
                {airportInfo.contacts && airportInfo.contacts.length > 0 ? (
                  <div className="space-y-4">
                    {airportInfo.contacts.map((contact, idx) => (
                      <div 
                        key={idx}
                        className="p-4 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900"
                      >
                        <div className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                          {contact.type}
                        </div>
                        <div className="space-y-1">
                          {contact.name && (
                            <div className="flex items-center gap-2 text-sm">
                              <span className="text-muted-foreground">{contact.name}</span>
        </div>
                          )}
                          {contact.phone && (
                            <div className="flex items-center gap-2 text-sm">
                              <Phone className="h-4 w-4 text-indigo-600" />
                              <a 
                                href={`tel:${contact.phone}`}
                                className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors"
                              >
                                {contact.phone}
                              </a>
                            </div>
                          )}
                          {contact.email && (
                            <div className="flex items-center gap-2 text-sm">
                              <Mail className="h-4 w-4 text-indigo-600" />
                              <a 
                                href={`mailto:${contact.email}`}
                                className="text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium transition-colors break-all"
                              >
                                {contact.email}
          </a>
        </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground italic">No contact information available</p>
                )}
              </div>

              <Separator />

              {/* AD 2.2 AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <PlaneTakeoff className="h-5 w-5 text-indigo-600" />
                  <h3 className="text-xl font-semibold">AD 2.2 AERODROME GEOGRAPHICAL AND ADMINISTRATIVE DATA</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <span className="font-medium text-gray-900 dark:text-gray-100">Types of traffic permitted (IFR/VFR)</span>
                    <Badge variant="outline" className="font-mono font-semibold">
                      {airportInfo.trafficTypes || 'Not specified'}
                    </Badge>
                  </div>
                  {airportInfo.administrativeRemarks && airportInfo.administrativeRemarks !== 'NIL' && (
                    <div className="p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                      <span className="font-medium text-gray-900 dark:text-gray-100">Remarks: </span>
                      <span className="text-sm text-gray-700 dark:text-gray-300">{airportInfo.administrativeRemarks}</span>
                    </div>
                  )}
                </div>
              </div>

              <Separator />

              {/* AD 2.6 RESCUE AND FIREFIGHTING SERVICES */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Flame className="h-5 w-5 text-red-600" />
                  <h3 className="text-xl font-semibold">AD 2.6 RESCUE AND FIRE FIGHTING SERVICES</h3>
                </div>
                <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950 rounded-lg border border-red-100 dark:border-red-900">
                  <span className="font-medium text-gray-900 dark:text-gray-100">AD category for fire fighting: </span>
                  <Badge variant="outline" className="font-mono font-semibold">
                    {airportInfo.fireFightingCategory || 'Not specified'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <Card className="bg-white/60 backdrop-blur-sm border-0">
          <CardContent className="pt-6 text-center">
            <div className="flex flex-col items-center gap-2">
              <div className="flex items-center gap-2">
                <img src="/verxyl-logo.png" alt="Verxyl" className="h-10 w-auto opacity-80 hover:opacity-100 transition-opacity" />
              </div>
              <p className="text-sm text-muted-foreground">
                Created by Verxyl
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
