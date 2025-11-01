'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Plane, Search, Loader2, Clock, Phone, Mail, AlertCircle, CheckCircle2, Flame, FileText, PlaneTakeoff } from 'lucide-react'

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
  fireFightingCategory?: string
  remarks?: string
  trafficTypes?: string
  error?: string
}

export default function Home() {
  const [airportCode, setAirportCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
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
    setProgress(0)
    setError(null)
    setAirportInfo(null)

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
        body: JSON.stringify({ airportCode: airportCode.toUpperCase() })
      })

      const data: AirportInfo = await response.json()

      // Complete the progress bar
      clearInterval(progressInterval)
      setProgress(100)

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch airport information')
      }

      setAirportInfo(data)
      
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

              <Separator />

              {/* Fire Fighting Category */}
              {airportInfo.fireFightingCategory && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <Flame className="h-5 w-5 text-red-600" />
                    <h3 className="text-xl font-semibold">Fire Fighting Category</h3>
                  </div>
                  <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-red-50 to-orange-50 dark:from-red-950 dark:to-orange-950 rounded-lg border border-red-100 dark:border-red-900">
                    <Badge variant="outline" className="font-mono font-semibold text-lg">
                      Category {airportInfo.fireFightingCategory}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Traffic Types */}
              {airportInfo.trafficTypes && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <PlaneTakeoff className="h-5 w-5 text-indigo-600" />
                    <h3 className="text-xl font-semibold">Traffic Types Permitted</h3>
                  </div>
                  <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <Badge variant="outline" className="font-mono font-semibold">
                      {airportInfo.trafficTypes}
                    </Badge>
                  </div>
                </div>
              )}

              {/* Remarks */}
              {airportInfo.remarks && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <FileText className="h-5 w-5 text-indigo-600" />
                    <h3 className="text-xl font-semibold">Remarks</h3>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-950 dark:to-blue-950 rounded-lg border border-indigo-100 dark:border-indigo-900">
                    <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                      {airportInfo.remarks}
                    </p>
                  </div>
                </div>
              )}
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
