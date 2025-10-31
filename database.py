#!/usr/bin/env python3
"""
Database module for caching airport data in Supabase
"""

import os
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class AirportCache:
    def __init__(self):
        """Initialize Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.warning("Supabase credentials not found. Caching disabled.")
            self.client = None
        else:
            try:
                self.client: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                self.client = None
    
    def get_cached_airport(self, airport_code: str) -> Optional[Dict]:
        """Get cached airport data for today"""
        if not self.client:
            return None
        
        try:
            today = date.today().isoformat()
            result = self.client.table('airport_cache').select('*').eq('airport_code', airport_code.upper()).eq('date', today).execute()
            
            if result.data:
                cached_data = result.data[0]
                logger.info(f"Found cached data for {airport_code}")
                return {
                    'airportCode': cached_data['airport_code'],
                    'airportName': cached_data['airport_name'],
                    'towerHours': json.loads(cached_data['tower_hours']),
                    'contacts': json.loads(cached_data['contacts']),
                    'cached': True
                }
            return None
        except Exception as e:
            logger.error(f"Error getting cached airport data: {e}")
            return None
    
    def cache_airport(self, airport_code: str, airport_data: Dict) -> bool:
        """Cache airport data for today"""
        if not self.client:
            return False
        
        try:
            # First, delete any existing cache for this airport today
            self.delete_old_cache(airport_code)
            
            # Insert new cache entry
            cache_data = {
                'airport_code': airport_code.upper(),
                'airport_name': airport_data.get('airportName', ''),
                'tower_hours': json.dumps(airport_data.get('towerHours', [])),
                'contacts': json.dumps(airport_data.get('contacts', [])),
                'date': date.today().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            
            result = self.client.table('airport_cache').insert(cache_data).execute()
            logger.info(f"Cached data for {airport_code}")
            return True
        except Exception as e:
            logger.error(f"Error caching airport data: {e}")
            return False
    
    def delete_old_cache(self, airport_code: str = None) -> bool:
        """Delete old cache entries (older than today)"""
        if not self.client:
            return False
        
        try:
            today = date.today().isoformat()
            query = self.client.table('airport_cache').delete().lt('date', today)
            
            if airport_code:
                query = query.eq('airport_code', airport_code.upper())
            
            result = query.execute()
            logger.info(f"Deleted old cache entries")
            return True
        except Exception as e:
            logger.error(f"Error deleting old cache: {e}")
            return False
    
    def cleanup_daily(self) -> bool:
        """Clean up all old cache entries (run daily)"""
        return self.delete_old_cache()

# Global cache instance
airport_cache = AirportCache()
