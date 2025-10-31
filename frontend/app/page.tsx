'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Plane, Search, Loader2, Clock, Phone, Mail, AlertCircle, CheckCircle2 } from 'lucide-react'

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
  towerHours: TowerHour[]
  contacts: Contact[]
  error?: string
}

export default function Home() {
  const [airportCode, setAirportCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [airportInfo, setAirportInfo] = useState<AirportInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  const searchAirport = async () => {
    if (!airportCode.trim()) {
      setError('Please enter an airport code')
      return
    }

    if (airportCode.length < 3) {
      setError('Airport code must be at least 3 characters')
      return
    }

    setLoading(true)
    setError(null)
    setAirportInfo(null)

    try {
      // Use Railway URL for production, localhost for development
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 
                     (typeof window !== 'undefined' && window.location.hostname === 'localhost' 
                       ? 'http://localhost:8080' 
                       : 'https://web-production-e7af.up.railway.app')
      const response = await fetch(`${apiUrl}/api/airport`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ airportCode: airportCode.toUpperCase() })
      })

      const data: AirportInfo = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch airport information')
      }

      setAirportInfo(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred')
    } finally {
      setLoading(false)
    }
  }

  const detectCountry = (code: string): string => {
    if (code.startsWith('K')) return 'USA 🇺🇸'
    if (code.startsWith('LF')) return 'France 🇫🇷'
    if (code.startsWith('EE')) return 'Estonia 🇪🇪'
    if (code.startsWith('EF')) return 'Finland 🇫🇮'
    if (code.startsWith('EY')) return 'Lithuania 🇱🇹'
    if (code.startsWith('EV')) return 'Latvia 🇱🇻'
    return 'Unknown'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-4">
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
              <Badge variant="outline" className="text-xs">K* - USA</Badge>
              <Badge variant="outline" className="text-xs">LF* - France</Badge>
              <Badge variant="outline" className="text-xs">EE* - Estonia</Badge>
              <Badge variant="outline" className="text-xs">EF* - Finland</Badge>
              <Badge variant="outline" className="text-xs">EY* - Lithuania</Badge>
              <Badge variant="outline" className="text-xs">EV* - Latvia</Badge>
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
                  placeholder="e.g., KJFK, EVRA, EYVI, EFHK"
                  value={airportCode}
                  onChange={(e) => setAirportCode(e.target.value.toUpperCase())}
                  onKeyPress={(e) => e.key === 'Enter' && searchAirport()}
                  className="flex-1 text-lg uppercase tracking-wider"
                  disabled={loading}
                />
                <Button 
                  onClick={searchAirport} 
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
              {airportCode && (
                <p className="text-sm text-muted-foreground">
                  Region: {detectCountry(airportCode)}
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
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-3xl mb-2">{airportInfo.airportName}</CardTitle>
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="text-lg px-3 py-1">
                      {airportInfo.airportCode}
                    </Badge>
                    <Badge variant="outline" className="text-sm">
                      {detectCountry(airportInfo.airportCode)}
                    </Badge>
                  </div>
                </div>
                <CheckCircle2 className="h-8 w-8 text-green-500" />
              </div>
            </CardHeader>

            <Separator />

            <CardContent className="space-y-6 pt-6">
              {/* Operational Hours */}
              <div>
                <div className="flex items-center gap-2 mb-4">
                  <Clock className="h-5 w-5 text-indigo-600" />
                  <h3 className="text-xl font-semibold">Operational Hours</h3>
                </div>
                {airportInfo.towerHours && airportInfo.towerHours.length > 0 ? (
                  <div className="space-y-2">
                    {airportInfo.towerHours.map((hour, idx) => (
                      <div 
                        key={idx}
                        className="flex items-center justify-between p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900"
                      >
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {hour.day}
                        </span>
                        <Badge variant="outline" className="font-mono font-semibold">
                          {hour.hours}
                        </Badge>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground italic">No operational hours available</p>
                )}
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
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <Card className="bg-white/60 backdrop-blur-sm border-0">
          <CardContent className="pt-6 text-center">
            <p className="text-sm text-muted-foreground">
              Powered by Next.js + TypeScript + shadcn/ui • Real-time AIP data scraping
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
