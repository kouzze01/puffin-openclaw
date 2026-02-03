-- Add trade_size_usdt column to bot_settings if it doesn't exist
ALTER TABLE bot_settings 
ADD COLUMN IF NOT EXISTS trade_size_usdt NUMERIC NOT NULL DEFAULT 20.0;
