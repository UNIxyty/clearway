-- Create airport_cache table for Supabase
CREATE TABLE IF NOT EXISTS airport_cache (
    id SERIAL PRIMARY KEY,
    airport_code VARCHAR(10) NOT NULL,
    airport_name TEXT,
    tower_hours JSONB,
    contacts JSONB,
    date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_airport_cache_code_date ON airport_cache(airport_code, date);
CREATE INDEX IF NOT EXISTS idx_airport_cache_date ON airport_cache(date);

-- Enable Row Level Security (RLS)
ALTER TABLE airport_cache ENABLE ROW LEVEL SECURITY;

-- Create policy to allow all operations (adjust as needed for your security requirements)
CREATE POLICY "Allow all operations on airport_cache" ON airport_cache
    FOR ALL USING (true);

-- Create a function to automatically clean up old records
CREATE OR REPLACE FUNCTION cleanup_old_airport_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM airport_cache WHERE date < CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

-- Optional: Create a scheduled job to run cleanup daily
-- This would need to be set up in your Supabase dashboard or via cron
-- SELECT cron.schedule('cleanup-airport-cache', '0 0 * * *', 'SELECT cleanup_old_airport_cache();');



