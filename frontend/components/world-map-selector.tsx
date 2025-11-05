'use client'

import { useState, useEffect } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Globe, MapPin } from 'lucide-react'

interface AirportCode {
  country: string
  region: string
  airports: string[]
}

interface AirportCodes {
  [prefix: string]: AirportCode
}

interface CountryData {
  name: string
  prefix: string
  emoji: string
  airports: string[]
  region: string
}

// Country to emoji mapping
const COUNTRY_EMOJIS: { [key: string]: string } = {
  'Afghanistan': '🇦🇫',
  'Andorra': '🇦🇩',
  'Angola': '🇦🇴',
  'Antigua and Barbuda': '🇦🇬',
  'Armenia': '🇦🇲',
  'Austria': '🇦🇹',
  'Azerbaijan': '🇦🇿',
  'Bahrain': '🇧🇭',
  'Bhutan': '🇧🇹',
  'Bosnia and Herzegovina': '🇧🇦',
  'Bulgaria': '🇧🇬',
  'Canada': '🇨🇦',
  'Cabo Verde': '🇨🇻',
  'Chile': '🇨🇱',
  'Costa Rica': '🇨🇷',
  'Croatia': '🇭🇷',
  'Cuba': '🇨🇺',
  'Czech Republic': '🇨🇿',
  'Denmark': '🇩🇰',
  'Djibouti': '🇩🇯',
  'Ecuador': '🇪🇨',
  'El Salvador': '🇸🇻',
  'Estonia': '🇪🇪',
  'Ethiopia': '🇪🇹',
  'Finland': '🇫🇮',
  'France': '🇫🇷',
  'Georgia': '🇬🇪',
  'Greece': '🇬🇷',
  'Guatemala': '🇬🇹',
  'Haiti': '🇭🇹',
  'Honduras': '🇭🇳',
  'Hong Kong': '🇭🇰',
  'Hungary': '🇭🇺',
  'India': '🇮🇳',
  'Iran': '🇮🇷',
  'Ireland': '🇮🇪',
  'Israel': '🇮🇱',
  'Italy': '🇮🇹',
  'Kazakhstan': '🇰🇿',
  'Kosovo': '🇽🇰',
  'Kyrgyzstan': '🇰🇬',
  'Latvia': '🇱🇻',
  'Libya': '🇱🇾',
  'Macao': '🇲🇴',
  'Malaysia': '🇲🇾',
  'Malta': '🇲🇹',
  'Maldives': '🇲🇻',
  'Mongolia': '🇲🇳',
  'Nepal': '🇳🇵',
  'Norway': '🇳🇴',
  'Oman': '🇴🇲',
  'Poland': '🇵🇱',
  'Portugal': '🇵🇹',
  'Saint Vincent and the Grenadines': '🇻🇨',
  'Saudi Arabia': '🇸🇦',
  'Seychelles': '🇸🇨',
  'Singapore': '🇸🇬',
  'South Africa': '🇿🇦',
  'South Korea': '🇰🇷',
  'South Sudan': '🇸🇸',
  'Sudan': '🇸🇩',
  'Sweden': '🇸🇪',
  'Taiwan': '🇹🇼',
  'Thailand': '🇹🇭',
  'Timor': '🇹🇱',
  'Timor-Leste': '🇹🇱',
  'Trinidad and Tobago': '🇹🇹',
  'Ukraine': '🇺🇦',
  'United Arab Emirates': '🇦🇪',
  'United Kingdom': '🇬🇧',
  'USA': '🇺🇸',
  'United States of America': '🇺🇸',
}

// Common ICAO to IATA and airport name mapping
const AIRPORT_INFO: { [key: string]: { iata?: string; name: string } } = {
  // Latvia
  'EVRA': { iata: 'RIX', name: 'Riga' },
  'EVVA': { iata: 'VNT', name: 'Ventspils' },
  'EVLA': { iata: 'LPX', name: 'Liepaja' },
  // Finland
  'EFHK': { iata: 'HEL', name: 'Helsinki' },
  'EFTU': { iata: 'TMP', name: 'Tampere' },
  'EFRO': { iata: 'RVN', name: 'Rovaniemi' },
  // Estonia
  'EETN': { iata: 'TLL', name: 'Tallinn' },
  // Lithuania
  'EYVI': { iata: 'VNO', name: 'Vilnius' },
  'EYKA': { iata: 'KUN', name: 'Kaunas' },
  // UK
  'EGLL': { iata: 'LHR', name: 'London Heathrow' },
  'EGKK': { iata: 'LGW', name: 'London Gatwick' },
  'EGSS': { iata: 'STN', name: 'London Stansted' },
  // France
  'LFPG': { iata: 'CDG', name: 'Paris Charles de Gaulle' },
  'LFPO': { iata: 'ORY', name: 'Paris Orly' },
  // USA
  'KJFK': { iata: 'JFK', name: 'New York JFK' },
  'KLAX': { iata: 'LAX', name: 'Los Angeles' },
  'KORD': { iata: 'ORD', name: 'Chicago O\'Hare' },
  // Italy
  'LIRF': { iata: 'FCO', name: 'Rome Fiumicino' },
  'LIMC': { iata: 'MXP', name: 'Milan Malpensa' },
  // Germany
  'EDDF': { iata: 'FRA', name: 'Frankfurt' },
  'EDDM': { iata: 'MUC', name: 'Munich' },
  // Spain
  'LEMD': { iata: 'MAD', name: 'Madrid' },
  'LEBL': { iata: 'BCN', name: 'Barcelona' },
  // Greece
  'LGAV': { iata: 'ATH', name: 'Athens' },
  // Bulgaria
  'LBSF': { iata: 'SOF', name: 'Sofia' },
  // Czech Republic
  'LKPR': { iata: 'PRG', name: 'Prague' },
  // Denmark
  'EKCH': { iata: 'CPH', name: 'Copenhagen' },
  // Ireland
  'EIDW': { iata: 'DUB', name: 'Dublin' },
  // Austria
  'LOWW': { iata: 'VIE', name: 'Vienna' },
  // Poland
  'EPWA': { iata: 'WAW', name: 'Warsaw' },
  // Portugal
  'LPPT': { iata: 'LIS', name: 'Lisbon' },
  // Sweden
  'ESSA': { iata: 'ARN', name: 'Stockholm Arlanda' },
  // Norway
  'ENGM': { iata: 'OSL', name: 'Oslo' },
  // Add more as needed
}

// Region to display name mapping
const REGION_NAMES: { [key: string]: string } = {
  'ASIA': 'Asia',
  'EUROPE': 'Europe',
  'AFRICA': 'Africa',
  'NORTH_AMERICA': 'North America',
  'SOUTH_AMERICA': 'South America',
  'OCEANIA': 'Oceania',
}

interface WorldMapSelectorProps {
  onAirportSelect?: (airportCode: string) => void
}

export function WorldMapSelector({ onAirportSelect }: WorldMapSelectorProps) {
  const [open, setOpen] = useState(false)
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null)
  const [airportCodes, setAirportCodes] = useState<AirportCodes>({})
  const [loading, setLoading] = useState(true)
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null)

  useEffect(() => {
    // Load airport codes
    fetch('/assets/airport_codes.json')
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`)
        }
        return res.json()
      })
      .then(data => {
        setAirportCodes(data.codes || {})
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load airport codes:', err)
        // Try alternative path
        fetch('/airport_codes.json')
          .then(res => res.json())
          .then(data => {
            setAirportCodes(data.codes || {})
            setLoading(false)
          })
          .catch(err2 => {
            console.error('Failed to load airport codes from alternative path:', err2)
            setLoading(false)
          })
      })
  }, [])

  const regions = ['EUROPE', 'ASIA', 'AFRICA', 'NORTH_AMERICA', 'SOUTH_AMERICA', 'OCEANIA']
  
  const getCountriesByRegion = (region: string): CountryData[] => {
    const countries: CountryData[] = []
    Object.entries(airportCodes).forEach(([prefix, data]) => {
      if (data.region === region) {
        countries.push({
          name: data.country,
          prefix,
          emoji: COUNTRY_EMOJIS[data.country] || '🌍',
          airports: data.airports,
          region: data.region,
        })
      }
    })
    return countries.sort((a, b) => a.name.localeCompare(b.name))
  }

  const getAirportDisplay = (icaoCode: string): string => {
    const info = AIRPORT_INFO[icaoCode]
    if (info) {
      return info.iata 
        ? `${icaoCode} - ${info.name} (${info.iata})`
        : `${icaoCode} - ${info.name}`
    }
    // Fallback: try to infer from code pattern or use code only
    return `${icaoCode}`
  }

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        variant="outline"
        className="gap-2"
      >
        <Globe className="h-4 w-4" />
        Browse by Region
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className={`max-w-7xl w-[95vw] ${selectedRegion ? 'h-[90vh]' : 'max-h-[95vh]'} flex flex-col`}>
          <DialogHeader className="flex-shrink-0">
            <DialogTitle className="flex items-center gap-2 text-2xl">
              <MapPin className="h-6 w-6" />
              Browse Airports by Region
            </DialogTitle>
            <DialogDescription>
              Select a continent to view countries and their airports. Hover over a country to see airport codes.
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-muted-foreground">Loading airport data...</p>
                </div>
              </div>
            ) : selectedRegion ? (
              <div className="flex flex-col flex-1 min-h-0">
                <Button
                  variant="ghost"
                  onClick={() => setSelectedRegion(null)}
                  className="mb-4 flex-shrink-0"
                >
                  ← Back to Regions
                </Button>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 overflow-y-auto flex-1 pb-4">
                {getCountriesByRegion(selectedRegion).map((country) => (
                  <div
                    key={country.prefix}
                    className="relative p-4 border rounded-lg hover:border-blue-500 hover:shadow-lg transition-all cursor-pointer"
                    onMouseEnter={() => setHoveredCountry(country.prefix)}
                    onMouseLeave={() => setHoveredCountry(null)}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-2xl">{country.emoji}</span>
                      <div>
                        <div className="font-semibold">{country.name}</div>
                        <div className="text-xs text-muted-foreground">{country.prefix}</div>
                      </div>
                    </div>
                    {hoveredCountry === country.prefix && (
                      <div className="absolute top-full left-0 right-0 mt-2 p-4 bg-white dark:bg-gray-800 border-2 border-blue-500 rounded-lg shadow-2xl z-50 max-h-96 overflow-y-auto min-w-[300px]">
                        <div className="text-sm font-semibold mb-3 text-gray-900 dark:text-gray-100 flex items-center gap-2">
                          <span>{country.emoji}</span>
                          <span>Airports ({country.airports.length})</span>
                        </div>
                        <div className="grid grid-cols-1 gap-1.5 max-h-80 overflow-y-auto">
                          {country.airports.map((airport) => (
                            <div
                              key={airport}
                              className="text-xs font-mono cursor-pointer p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                              onClick={() => {
                                if (onAirportSelect) {
                                  onAirportSelect(airport)
                                  setOpen(false)
                                }
                              }}
                            >
                              {getAirportDisplay(airport)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    <div className="text-xs text-muted-foreground">
                      {country.airports.length} airport{country.airports.length !== 1 ? 's' : ''}
                    </div>
                  </div>
                ))}
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-6 py-4 overflow-y-auto">
              {regions.map((region) => {
                const countries = getCountriesByRegion(region)
                if (countries.length === 0) return null

                return (
                  <button
                    key={region}
                    onClick={() => setSelectedRegion(region)}
                    className="group relative p-6 border-2 rounded-xl hover:border-blue-500 hover:shadow-xl transition-all bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900"
                  >
                    <div className="text-center">
                      <div className="text-4xl mb-2">
                        {region === 'EUROPE' && '🇪🇺'}
                        {region === 'ASIA' && '🌏'}
                        {region === 'AFRICA' && '🌍'}
                        {region === 'NORTH_AMERICA' && '🌎'}
                        {region === 'SOUTH_AMERICA' && '🌎'}
                        {region === 'OCEANIA' && '🌏'}
                      </div>
                      <div className="text-xl font-bold mb-1">{REGION_NAMES[region] || region}</div>
                      <div className="text-sm text-muted-foreground">
                        {countries.length} countr{countries.length !== 1 ? 'ies' : 'y'}
                      </div>
                      <div className="text-xs text-muted-foreground mt-2">
                        {countries.reduce((sum, c) => sum + c.airports.length, 0)} airports
                      </div>
                    </div>
                    <div className="absolute inset-0 bg-blue-500/0 group-hover:bg-blue-500/5 rounded-xl transition-colors"></div>
                  </button>
                )
              })}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}

