#!/usr/bin/env python3
"""
Script to build comprehensive country mapping from JSON file
Maps countries to ICAO prefixes and flag emojis
"""

import json
import re
from pathlib import Path

# Comprehensive ICAO prefix mapping for all countries
# Based on ICAO location indicator standards
ICAO_PREFIX_MAPPING = {
    # Asia
    'Afghanistan': 'OA',
    'Armenia': 'UD',
    'Azerbaijan': 'UB',
    'Bahrain': 'OB',
    'Bangladesh': 'VG',
    'Bhutan': 'VQ',
    'Brunei': 'WBA',
    'Cambodia': 'VDP',
    'China': 'ZB',  # ZB, ZG, ZH, ZJ, ZL, ZP, ZS, ZU, ZW, ZY
    'Cyprus': 'LC',
    'East Timor (Timor-Leste)': 'WP',
    'Georgia': 'UG',
    'Hong Kong': 'VH',
    'India': 'VI',
    'Indonesia': 'WI',  # WAAA, WABB, etc.
    'Iran': 'OII',
    'Iraq': 'OR',
    'Israel': 'LL',
    'Japan': 'RJ',
    'Jordan': 'OJ',
    'Kazakhstan': 'UA',
    'Kuwait': 'OK',
    'Kyrgyzstan': 'UO',
    'Laos': 'VL',
    'Lebanon': 'OL',
    'Macau': 'VM',
    'Malaysia': 'WM',
    'Maldives': 'VR',
    'Mongolia': 'ZM',
    'Myanmar (Burma)': 'VY',
    'Nepal': 'VN',
    'North Korea': 'ZK',
    'Oman': 'OO',
    'Pakistan': 'OP',
    'Philippines': 'RP',
    'Qatar': 'OT',
    'Saudi Arabia': 'OE',
    'Singapore': 'WS',
    'South Korea': 'RK',
    'Sri Lanka': 'VC',
    'Syria': 'OS',
    'Taiwan': 'RC',
    'Tajikistan': 'UT',
    'Thailand': 'VT',
    'Turkmenistan': 'UT',
    'United Arab Emirates': 'OM',
    'Uzbekistan': 'UZ',
    'Vietnam': 'VV',
    'Yemen': 'OY',
    
    # Europe
    'Albania': 'LA',
    'Andorra': 'LE',
    'Austria': 'LO',
    'Belarus': 'UM',
    'Belgium': 'EB',
    'Bosnia and Herzegovina': 'LQ',
    'Bulgaria': 'LZ',
    'Croatia': 'LD',
    'Czech Republic': 'LK',
    'Denmark': 'EK',
    'Estonia': 'EE',
    'Finland': 'EF',
    'France': 'LF',
    'Germany': 'ED',
    'Greece': 'LG',
    'Hungary': 'LH',
    'Iceland': 'BI',
    'Ireland': 'EI',
    'Italy': 'LI',
    'Kosovo': 'BK',
    'Latvia': 'EV',
    'Lithuania': 'EY',
    'Liechtenstein': 'LS',
    'Luxembourg': 'EL',
    'Malta': 'LM',
    'Moldova': 'LU',
    'Monaco': 'LF',
    'Montenegro': 'LY',
    'Netherlands': 'EH',
    'North Macedonia': 'LW',
    'Norway': 'EN',
    'Poland': 'EP',
    'Portugal': 'LP',
    'Romania': 'LR',
    'Russia': 'UU',  # UU, UUEE, etc.
    'San Marino': 'LID',
    'Serbia': 'LY',
    'Slovakia': 'LZ',
    'Slovenia': 'LJ',
    'Spain': 'LE',
    'Sweden': 'ES',
    'Switzerland': 'LS',
    'Turkey': 'LT',
    'Ukraine': 'UK',
    'United Kingdom': 'EG',
    'Vatican City': 'LV',
    
    # Africa
    'Algeria': 'DA',
    'Angola': 'FN',
    'Benin': 'DB',
    'Botswana': 'FB',
    'Burkina Faso': 'DF',
    'Burundi': 'HB',
    'Cabo Verde': 'GV',
    'Cameroon': 'FK',
    'Central African Republic': 'FE',
    'Chad': 'FT',
    'Comoros': 'FM',
    'Congo': 'FC',
    'Djibouti': 'HD',
    'Egypt': 'HE',
    'Equatorial Guinea': 'FG',
    'Eritrea': 'HH',
    'Eswatini': 'FD',
    'Ethiopia': 'HA',
    'Gabon': 'FO',
    'Gambia': 'GB',
    'Ghana': 'DG',
    'Guinea': 'GU',
    'Guinea-Bissau': 'GG',
    "Ivory Coast (Côte d'Ivoire)": 'DI',
    'Kenya': 'HK',
    'Lesotho': 'FX',
    'Liberia': 'GL',
    'Libya': 'HL',
    'Madagascar': 'FM',
    'Malawi': 'FW',
    'Mali': 'GA',
    'Mauritania': 'GQ',
    'Mauritius': 'FI',
    'Morocco': 'GM',
    'Mozambique': 'FQ',
    'Namibia': 'FY',
    'Niger': 'DR',
    'Nigeria': 'DN',
    'Rwanda': 'HR',
    "São Tomé and Príncipe": 'FP',
    'Senegal': 'GO',
    'Seychelles': 'FS',
    'Sierra Leone': 'GF',
    'Somalia': 'HC',
    'South Africa': 'FA',
    'South Sudan': 'HSS',
    'Sudan': 'HS',
    'Tanzania': 'HT',
    'Togo': 'DX',
    'Tunisia': 'DT',
    'Uganda': 'HU',
    'Zambia': 'FL',
    'Zimbabwe': 'FV',
    
    # North America
    'Antigua and Barbuda': 'TAPA',
    'Bahamas': 'MY',
    'Barbados': 'TBPB',
    'Belize': 'MZ',
    'Canada': 'C',
    'Costa Rica': 'MR',
    'Cuba': 'MU',
    'Dominica': 'TD',
    'Dominican Republic': 'MD',
    'El Salvador': 'MS',
    'Grenada': 'TGPY',
    'Guatemala': 'MG',
    'Haiti': 'MT',
    'Honduras': 'MH',
    'Jamaica': 'MK',
    'Mexico': 'MM',
    'Nicaragua': 'MN',
    'Panama': 'MP',
    'Saint Kitts and Nevis': 'TK',
    'Saint Lucia': 'TL',
    'Saint Vincent and the Grenadines': 'TV',
    'Trinidad and Tobago': 'TT',
    'United States of America': 'K',
    
    # South America
    'Argentina': 'SA',
    'Bolivia': 'SL',
    'Brazil': 'SB',
    'Chile': 'SC',
    'Colombia': 'SK',
    'Ecuador': 'SE',
    'Guyana': 'SY',
    'Paraguay': 'SG',
    'Peru': 'SP',
    'Suriname': 'SM',
    'Uruguay': 'SU',
    'Venezuela': 'SV',
    
    # Australia and Oceania
    'Australia': 'Y',
    'Fiji': 'NF',
    'Kiribati': 'NG',
    'Marshall Islands': 'PK',
    'Micronesia': 'PT',
    'Nauru': 'AN',
    'New Zealand': 'NZ',
    'Palau': 'PT',
    'Papua New Guinea': 'AY',
    'Samoa': 'NS',
    'Solomon Islands': 'AG',
    'Tonga': 'NT',
    'Tuvalu': 'NG',
    'Vanuatu': 'NI',
}

# Country flag emojis (ISO 3166-1 alpha-2 country codes to emoji)
# Using flag emoji Unicode ranges
FLAG_EMOJIS = {
    'Afghanistan': '🇦🇫',
    'Albania': '🇦🇱',
    'Algeria': '🇩🇿',
    'Andorra': '🇦🇩',
    'Angola': '🇦🇴',
    'Antigua and Barbuda': '🇦🇬',
    'Argentina': '🇦🇷',
    'Armenia': '🇦🇲',
    'Australia': '🇦🇺',
    'Austria': '🇦🇹',
    'Azerbaijan': '🇦🇿',
    'Bahamas': '🇧🇸',
    'Bahrain': '🇧🇭',
    'Bangladesh': '🇧🇩',
    'Barbados': '🇧🇧',
    'Belarus': '🇧🇾',
    'Belgium': '🇧🇪',
    'Belize': '🇧🇿',
    'Benin': '🇧🇯',
    'Bhutan': '🇧🇹',
    'Bolivia': '🇧🇴',
    'Bosnia and Herzegovina': '🇧🇦',
    'Botswana': '🇧🇼',
    'Brazil': '🇧🇷',
    'Bulgaria': '🇧🇬',
    'Brunei': '🇧🇳',
    'Burkina Faso': '🇧🇫',
    'Burundi': '🇧🇮',
    'Cabo Verde': '🇨🇻',
    'Cambodia': '🇰🇭',
    'Cameroon': '🇨🇲',
    'Canada': '🇨🇦',
    'Central African Republic': '🇨🇫',
    'Chad': '🇹🇩',
    'Chile': '🇨🇱',
    'China': '🇨🇳',
    'Colombia': '🇨🇴',
    'Comoros': '🇰🇲',
    'Congo': '🇨🇬',
    'Costa Rica': '🇨🇷',
    'Croatia': '🇭🇷',
    'Cuba': '🇨🇺',
    'Cyprus': '🇨🇾',
    'Czech Republic': '🇨🇿',
    'Denmark': '🇩🇰',
    'Djibouti': '🇩🇯',
    'Dominica': '🇩🇲',
    'Dominican Republic': '🇩🇴',
    'East Timor (Timor-Leste)': '🇹🇱',
    'Ecuador': '🇪🇨',
    'Egypt': '🇪🇬',
    'El Salvador': '🇸🇻',
    'Equatorial Guinea': '🇬🇶',
    'Eritrea': '🇪🇷',
    'Estonia': '🇪🇪',
    'Eswatini': '🇸🇿',
    'Ethiopia': '🇪🇹',
    'Fiji': '🇫🇯',
    'Finland': '🇫🇮',
    'France': '🇫🇷',
    'Gabon': '🇬🇦',
    'Gambia': '🇬🇲',
    'Georgia': '🇬🇪',
    'Germany': '🇩🇪',
    'Ghana': '🇬🇭',
    'Greece': '🇬🇷',
    'Grenada': '🇬🇩',
    'Guatemala': '🇬🇹',
    'Guinea': '🇬🇳',
    'Guinea-Bissau': '🇬🇼',
    'Guyana': '🇬🇾',
    'Haiti': '🇭🇹',
    'Honduras': '🇭🇳',
    'Hong Kong': '🇭🇰',
    'Hungary': '🇭🇺',
    'Iceland': '🇮🇸',
    'India': '🇮🇳',
    'Indonesia': '🇮🇩',
    'Iran': '🇮🇷',
    'Iraq': '🇮🇶',
    'Ireland': '🇮🇪',
    'Israel': '🇮🇱',
    'Italy': '🇮🇹',
    "Ivory Coast (Côte d'Ivoire)": '🇨🇮',
    'Jamaica': '🇯🇲',
    'Japan': '🇯🇵',
    'Jordan': '🇯🇴',
    'Kazakhstan': '🇰🇿',
    'Kenya': '🇰🇪',
    'Kiribati': '🇰🇮',
    'Kosovo': '🇽🇰',
    'Kuwait': '🇰🇼',
    'Kyrgyzstan': '🇰🇬',
    'Laos': '🇱🇦',
    'Latvia': '🇱🇻',
    'Lebanon': '🇱🇧',
    'Lesotho': '🇱🇸',
    'Liberia': '🇱🇷',
    'Libya': '🇱🇾',
    'Liechtenstein': '🇱🇮',
    'Lithuania': '🇱🇹',
    'Luxembourg': '🇱🇺',
    'Macau': '🇲🇴',
    'Madagascar': '🇲🇬',
    'Malawi': '🇲🇼',
    'Malaysia': '🇲🇾',
    'Maldives': '🇲🇻',
    'Mali': '🇲🇱',
    'Malta': '🇲🇹',
    'Marshall Islands': '🇲🇭',
    'Mauritania': '🇲🇷',
    'Mauritius': '🇲🇺',
    'Mexico': '🇲🇽',
    'Micronesia': '🇫🇲',
    'Moldova': '🇲🇩',
    'Monaco': '🇲🇨',
    'Mongolia': '🇲🇳',
    'Montenegro': '🇲🇪',
    'Morocco': '🇲🇦',
    'Mozambique': '🇲🇿',
    'Myanmar (Burma)': '🇲🇲',
    'Namibia': '🇳🇦',
    'Nauru': '🇳🇷',
    'Nepal': '🇳🇵',
    'Netherlands': '🇳🇱',
    'New Zealand': '🇳🇿',
    'Nicaragua': '🇳🇮',
    'Niger': '🇳🇪',
    'Nigeria': '🇳🇬',
    'North Korea': '🇰🇵',
    'North Macedonia': '🇲🇰',
    'Norway': '🇳🇴',
    'Oman': '🇴🇲',
    'Pakistan': '🇵🇰',
    'Palau': '🇵🇼',
    'Panama': '🇵🇦',
    'Papua New Guinea': '🇵🇬',
    'Paraguay': '🇵🇾',
    'Peru': '🇵🇪',
    'Philippines': '🇵🇭',
    'Poland': '🇵🇱',
    'Portugal': '🇵🇹',
    'Qatar': '🇶🇦',
    'Romania': '🇷🇴',
    'Russia': '🇷🇺',
    'Rwanda': '🇷🇼',
    'Saint Kitts and Nevis': '🇰🇳',
    'Saint Lucia': '🇱🇨',
    'Saint Vincent and the Grenadines': '🇻🇨',
    'Samoa': '🇼🇸',
    'San Marino': '🇸🇲',
    "São Tomé and Príncipe": '🇸🇹',
    'Saudi Arabia': '🇸🇦',
    'Senegal': '🇸🇳',
    'Serbia': '🇷🇸',
    'Seychelles': '🇸🇨',
    'Sierra Leone': '🇸🇱',
    'Singapore': '🇸🇬',
    'Slovakia': '🇸🇰',
    'Slovenia': '🇸🇮',
    'Solomon Islands': '🇸🇧',
    'Somalia': '🇸🇴',
    'South Africa': '🇿🇦',
    'South Korea': '🇰🇷',
    'South Sudan': '🇸🇸',
    'Spain': '🇪🇸',
    'Sri Lanka': '🇱🇰',
    'Sudan': '🇸🇩',
    'Suriname': '🇸🇷',
    'Sweden': '🇸🇪',
    'Switzerland': '🇨🇭',
    'Syria': '🇸🇾',
    'Taiwan': '🇹🇼',
    'Tajikistan': '🇹🇯',
    'Tanzania': '🇹🇿',
    'Thailand': '🇹🇭',
    'Togo': '🇹🇬',
    'Tonga': '🇹🇴',
    'Trinidad and Tobago': '🇹🇹',
    'Tunisia': '🇹🇳',
    'Turkey': '🇹🇷',
    'Turkmenistan': '🇹🇲',
    'Tuvalu': '🇹🇻',
    'Uganda': '🇺🇬',
    'Ukraine': '🇺🇦',
    'United Arab Emirates': '🇦🇪',
    'United Kingdom': '🇬🇧',
    'United States of America': '🇺🇸',
    'Uruguay': '🇺🇾',
    'Uzbekistan': '🇺🇿',
    'Vanuatu': '🇻🇺',
    'Vatican City': '🇻🇦',
    'Venezuela': '🇻🇪',
    'Vietnam': '🇻🇳',
    'Yemen': '🇾🇪',
    'Zambia': '🇿🇲',
    'Zimbabwe': '🇿🇼',
}

def load_json_countries():
    """Load all countries from the JSON file"""
    json_path = Path(__file__).parent / 'assets' / 'aip_countries_full.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_complete_mapping():
    """Build complete country mapping with ICAO prefixes and flags"""
    countries_data = load_json_countries()
    
    mapping = {}
    missing_prefixes = []
    missing_flags = []
    
    for country_data in countries_data:
        country_name = country_data.get('country', '').strip()
        region = country_data.get('region', 'UNKNOWN')
        aip_type = country_data.get('type', 'Unknown')
        link = country_data.get('link', '')
        
        # Get ICAO prefix - try exact match first, then normalized match
        icao_prefix = ICAO_PREFIX_MAPPING.get(country_name)
        if not icao_prefix:
            # Try normalized match (handle special characters)
            country_normalized = country_name.replace('’', "'").replace('–', '-').replace('—', '-')
            icao_prefix = ICAO_PREFIX_MAPPING.get(country_normalized)
        if not icao_prefix:
            # Try case-insensitive match
            for key, value in ICAO_PREFIX_MAPPING.items():
                key_normalized = key.replace('’', "'").replace('–', '-').replace('—', '-')
                if key_normalized.upper() == country_name.upper() or key.upper() == country_name.upper():
                    icao_prefix = value
                    break
        if not icao_prefix:
            # Try partial match (e.g., "Ivory Coast" matches "Ivory Coast (Côte d'Ivoire)")
            country_upper = country_name.upper()
            for key, value in ICAO_PREFIX_MAPPING.items():
                key_upper = key.upper()
                if country_upper in key_upper or key_upper in country_upper:
                    icao_prefix = value
                    break
        
        if not icao_prefix:
            # Try to find prefix by checking if country name matches any key
            # (for countries that might have different name variations)
            missing_prefixes.append(country_name)
            # Continue to next country instead of skipping
            continue
        
        # Get flag emoji - try exact match first, then case-insensitive
        flag_emoji = FLAG_EMOJIS.get(country_name, '🏳️')
        if flag_emoji == '🏳️':
            # Try case-insensitive match
            for key, value in FLAG_EMOJIS.items():
                if key.upper() == country_name.upper():
                    flag_emoji = value
                    break
            if flag_emoji == '🏳️':
                missing_flags.append(country_name)
        
        mapping[country_name] = {
            'prefix': icao_prefix,
            'flag': flag_emoji,
            'region': region,
            'type': aip_type,
            'link': link
        }
    
    print(f"Successfully mapped {len(mapping)} countries")
    if missing_prefixes:
        print(f"\nMissing ICAO prefixes for {len(missing_prefixes)} countries:")
        for country in missing_prefixes[:10]:
            print(f"  - {country}")
    if missing_flags:
        print(f"\nMissing flags for {len(missing_flags)} countries:")
        for country in missing_flags[:10]:
            print(f"  - {country}")
    
    return mapping

if __name__ == '__main__':
    mapping = build_complete_mapping()
    print(f"\nTotal countries mapped: {len(mapping)}")

