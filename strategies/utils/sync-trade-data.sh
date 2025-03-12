#!/bin/bash
#######################################################################
# sync-trade-data.sh
#
# DESCRIPTION:
#   This script fetches hourly stock price data from Financial Modeling Prep API
#   and synchronizes it with a MySQL database. It's designed to be run as a cron job
#   and only adds new data that doesn't already exist in the database.
#
# USAGE:
#   ./sync-trade-data.sh [SYMBOL1 SYMBOL2 ...]
#   
#   If no symbols are provided, it will use the default symbols: AAPL, MSFT, GOOGL
#
# REQUIREMENTS:
#   - curl: For API requests
#   - jq: For JSON parsing
#   - mysql client: For database operations
#
# EXAMPLES:
#   ./sync-trade-data.sh                  # Use default symbols
#   ./sync-trade-data.sh AAPL TSLA NVDA   # Fetch specific symbols
#   
# NOTES:
#   - Configure the API key, database credentials, and other settings below
#   - The script logs all activities to a log file for tracking and debugging
#   - Designed to be idempotent - safe to run multiple times without duplicating data
#######################################################################

# Exit on error, undefined variables, and propagate pipe errors
set -euo pipefail

# API credentials
# https://financialmodelingprep.com/stable/historical-chart/1hour?symbol=AAPL&apikey=849f3a33e72d49dfe694d6eda459012d
api_url="https://financialmodelingprep.com/stable/historical-chart/1hour"
api_key="849f3a33e72d49dfe694d6eda459012d"

# MySQL credentials
username="root"
password="fsck"
database_name="price_db"

# Log file configuration
log_dir="./logs/stock-sync"
log_file="${log_dir}/stock_sync_$(date +%Y%m%d_%H%M%S).log"

# Default symbols if none provided
default_symbols=("AAPL" "MSFT" "GOOGL")

# Temporary directory for processing
temp_dir=$(mktemp -d)
trap 'rm -rf "$temp_dir"' EXIT

# Create log directory if it doesn't exist
mkdir -p "$log_dir"

# Export MySQL password to avoid warning
export MYSQL_PWD="$password"

# Initialize counters
processed_count=0
added_count=0
skipped_count=0
invalid_count=0
error_count=0

#######################################################################
# FUNCTIONS
#######################################################################

# Function to log messages
log() {
    local message="$1"
    local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $message" | tee -a "$log_file"
}

# Function to execute MySQL queries
execute_mysql() {
    local query="$1"
    mysql -u "$username" "$database_name" -e "$query" 2>> "$log_file"
    return $?
}

# Function to check if a record exists in the database
record_exists() {
    local symbol="$1"
    local date="$2"
    
    local result=$(mysql -u "$username" "$database_name" -N -s -e "
        SELECT COUNT(*) FROM stock_prices 
        WHERE symbol='$symbol' AND date='$date'")
    
    if [ "$result" -gt 0 ]; then
        return 0  # Record exists
    else
        return 1  # Record does not exist
    fi
}

# Function to clean and validate price data
validate_price() {
    local price="$1"
    local field="$2"
    local symbol="$3"
    
    # Check if value is numeric
    if [[ ! "$price" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        log "WARNING: Invalid $field value '$price' for $symbol - setting to 0"
        echo "0.00"
        ((invalid_count++))
    else
        echo "$price"
    fi
}

# Function to process a single stock record
process_record() {
    local symbol="$1"
    local record="$2"
    
    # Extract data from JSON
    local date=$(echo "$record" | jq -r '.date')
    local open=$(echo "$record" | jq -r '.open')
    local high=$(echo "$record" | jq -r '.high')
    local low=$(echo "$record" | jq -r '.low')
    local close=$(echo "$record" | jq -r '.close')
    local volume=$(echo "$record" | jq -r '.volume')
    
    # Validate price data
    open=$(validate_price "$open" "open" "$symbol")
    high=$(validate_price "$high" "high" "$symbol")
    low=$(validate_price "$low" "low" "$symbol")
    close=$(validate_price "$close" "close" "$symbol")
    
    # Validate volume (should be a non-negative integer)
    if [[ ! "$volume" =~ ^[0-9]+$ ]]; then
        log "WARNING: Invalid volume value '$volume' for $symbol at $date - setting to 0"
        volume="0"
        ((invalid_count++))
    fi
    
    ((processed_count++))
    
    # Check if record already exists in the database
    if record_exists "$symbol" "$date"; then
        log "SKIPPED: Record for $symbol at $date already exists"
        ((skipped_count++))
        return
    fi
    
    # Insert the new record
    local query="
        INSERT INTO stock_prices (symbol, date, open, high, low, close, volume) 
        VALUES ('$symbol', '$date', $open, $high, $low, $close, $volume);"
    
    if execute_mysql "$query"; then
        log "ADDED: New record for $symbol at $date"
        ((added_count++))
    else
        log "ERROR: Failed to insert record for $symbol at $date"
        ((error_count++))
    fi
}

# Function to fetch and process data for a symbol
process_symbol() {
    local symbol="$1"
    log "Processing symbol: $symbol"
    
    # Reset counters for this symbol
    local symbol_processed=0
    local symbol_added=0
    local symbol_skipped=0
    local symbol_invalid=0
    local symbol_error=0
    
    # Create temporary counter files for this symbol
    local symbol_processed_file="${temp_dir}/${symbol}_processed"
    local symbol_added_file="${temp_dir}/${symbol}_added"
    local symbol_skipped_file="${temp_dir}/${symbol}_skipped"
    local symbol_invalid_file="${temp_dir}/${symbol}_invalid"
    local symbol_error_file="${temp_dir}/${symbol}_error"
    
    # Initialize counter files
    echo 0 > "$symbol_processed_file"
    echo 0 > "$symbol_added_file"
    echo 0 > "$symbol_skipped_file"
    echo 0 > "$symbol_invalid_file"
    echo 0 > "$symbol_error_file"
    
    # Fetch data from the API
    local api_response_file="${temp_dir}/${symbol}_response.json"
    local api_endpoint="${api_url}?symbol=${symbol}&apikey=${api_key}"
    
    log "Fetching data from: ${api_url}?symbol=${symbol}"
    
    # Use curl to fetch the data
    if ! curl -s -o "$api_response_file" "$api_endpoint"; then
        log "ERROR: Failed to fetch data for $symbol"
        ((error_count++))
        return
    fi
    
    # Check if the API response is valid JSON
    if ! jq empty "$api_response_file" 2>/dev/null; then
        log "ERROR: Invalid JSON response for $symbol"
        ((error_count++))
        return
    fi
    
    # Count the records in the response
    local record_count=$(jq -r '. | length' "$api_response_file" 2>/dev/null)
    if [[ ! "$record_count" =~ ^[0-9]+$ ]]; then
        log "ERROR: Could not determine record count for $symbol"
        ((error_count++))
        return
    fi
    
    log "Retrieved $record_count records for $symbol"
    
    # Process each record with error handling
    set +e  # Temporarily disable exit on error
    while read -r record; do
        if [[ -n "$record" ]]; then
            # Process the record
            process_record "$symbol" "$record"
        else
            log "WARNING: Empty record encountered for $symbol"
            ((invalid_count++))
        fi
    done < <(jq -c '.[]' "$api_response_file" 2>/dev/null)
    set -e  # Re-enable exit on error
}

#######################################################################
# MAIN SCRIPT
#######################################################################

log "Starting stock data synchronization"

# Create the table if it doesn't exist
log "Ensuring database table exists"
execute_mysql "
CREATE TABLE IF NOT EXISTS stock_prices (
    id BIGINT AUTO_INCREMENT PRIMARY KEY, 
    symbol VARCHAR(10) NOT NULL,  
    date DATETIME NOT NULL,  
    open DECIMAL(10,2) NOT NULL,  
    high DECIMAL(10,2) NOT NULL,  
    low DECIMAL(10,2) NOT NULL,     
    close DECIMAL(10,2) NOT NULL,
    volume BIGINT NOT NULL,      
    
    -- Indexes for fast queries
    INDEX idx_symbol_date (symbol, date) 
);"

# Determine which symbols to process
symbols=()
if [ $# -gt 0 ]; then
    # Use provided symbols
    symbols=("$@")
else
    # Use default symbols
    symbols=("${default_symbols[@]}")
fi

log "Will process ${#symbols[@]} symbols: ${symbols[*]}"

# Process each symbol
for symbol in "${symbols[@]}"; do
    process_symbol "$symbol"
done

# Log the final results
log "==== SYNC COMPLETED ===="
log "Processed records: $processed_count"
log "Added records: $added_count"
log "Skipped records: $skipped_count"
log "Invalid values: $invalid_count"
log "Errors: $error_count"
log "========================"

exit 0
