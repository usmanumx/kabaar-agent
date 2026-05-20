import os
import json
import hmac
import hashlib
from datetime import datetime, timedelta

def sign_transaction(transaction_id: str, items: list, valuation: float, yard_name: str) -> str:
    """
    Generates a mock cryptographic signature of the transaction details
    using HMAC-SHA256 with a pre-shared backend secret key.
    """
    secret_key = b"kabaar_agent_secure_key_2026"
    
    # Deterministic payload construction
    payload_dict = {
        "transaction_id": transaction_id,
        "total_valuation": valuation,
        "optimal_yard_name": yard_name,
        # Hash items to ensure integrity of material list
        "items_hash": hashlib.sha256(json.dumps(items, sort_keys=True).encode('utf-8')).hexdigest()
    }
    
    payload_data = json.dumps(payload_dict, sort_keys=True).encode('utf-8')
    signature = hmac.new(secret_key, payload_data, hashlib.sha256).hexdigest()
    return f"sig_v2_{signature[:32]}"

def log_to_trace(transaction_id: str, message: str, level: str = "INFO"):
    """
    Appends a structured system execution trace log to the central backend log file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{level}] [OPS] [Tx: {transaction_id}] - {message}\n"
    
    # Resolve the path to backend/execution_trace.log
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    trace_log_path = os.path.join(backend_dir, "execution_trace.log")
    
    try:
        with open(trace_log_path, "a") as log_file:
            log_file.write(log_line)
    except Exception as e:
        # Fallback to console printing if file write fails
        print(f"Failed to write to execution trace log: {e}")

def commit_transaction(transaction_id: str, items: list, arbitrage_result: dict) -> dict:
    """
    Step 3/4 of the pipeline: committing operations ledger.
    - Performs cryptographic signing of the transaction details.
    - Appends the transaction details to the payout ledger.
    - Generates a pickup logistics receipt payload.
    - Appends traces to the central backend log.
    """
    log_to_trace(transaction_id, "Initializing operations ledger commit pipeline")
    
    # Extract transaction values
    valuation = arbitrage_result.get("total_valuation", 0.0)
    optimal_yard = arbitrage_result.get("optimal_yard", {})
    yard_name = optimal_yard.get("name", "Unknown Yard")
    yard_location = optimal_yard.get("location", "Location Pending")
    
    log_to_trace(transaction_id, f"Targeting optimal yard: {yard_name}")
    
    # 1. Cryptographic transactional signing
    log_to_trace(transaction_id, "Signing transaction pipeline payload...")
    digital_signature = sign_transaction(transaction_id, items, valuation, yard_name)
    log_to_trace(transaction_id, f"Signature generated: {digital_signature}")
    
    # 2. Construct automated pickup logistics receipt
    log_to_trace(transaction_id, "Constructing logistics receipt and scheduling pickup...")
    booking_time = datetime.utcnow().isoformat() + "Z"
    
    # Schedule pickup for tomorrow morning between 9 AM and 12 PM
    tomorrow = datetime.now() + timedelta(days=1)
    pickup_window = f"{tomorrow.strftime('%Y-%m-%d')} 09:00 AM - 12:00 PM"
    
    receipt = {
        "logistics_details": {
            "carrier": "KabaarAgent Fleet Dispatch",
            "service_tier": "Standard Commercial Scrap Pickup",
            "pickup_status": "SCHEDULED",
            "destination_yard": yard_name,
            "destination_address": yard_location
        },
        "scheduling": {
            "booking_time": booking_time,
            "estimated_pickup_window": pickup_window,
            "dispatch_notes": "Please keep the scrap materials segregated by metal/material type for verification upon pickup."
        },
        "transaction_summary": {
            "transaction_id": transaction_id,
            "valuation_pkr": valuation,
            "currency": "PKR",
            "item_count": len(items),
            "items": items,
            "digital_signature": digital_signature
        }
    }
    
    # 3. Update local mock manifest payout_ledger.json
    ledger_dir = os.path.dirname(os.path.abspath(__file__))
    ledger_path = os.path.join(ledger_dir, "payout_ledger.json")
    
    log_to_trace(transaction_id, f"Accessing local payout ledger at: {ledger_path}")
    
    # Initialize payout_ledger.json as a JSON list if it doesn't exist
    if not os.path.exists(ledger_path):
        log_to_trace(transaction_id, "Payout ledger does not exist. Initializing new ledger manifest.", level="WARNING")
        try:
            with open(ledger_path, "w") as f:
                json.dump([], f, indent=2)
        except Exception as e:
            log_to_trace(transaction_id, f"Error initializing ledger: {str(e)}", level="ERROR")
            raise e
            
    # Read existing entries, append new, write back
    try:
        with open(ledger_path, "r") as f:
            ledger_data = json.load(f)
            
        if not isinstance(ledger_data, list):
            log_to_trace(transaction_id, "Ledger format invalid (not a list). Resetting to list.", level="WARNING")
            ledger_data = []
            
        ledger_entry = {
            "transaction_id": transaction_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "items": items,
            "total_valuation": valuation,
            "optimal_yard": optimal_yard,
            "digital_signature": digital_signature,
            "receipt": receipt
        }
        
        ledger_data.append(ledger_entry)
        
        with open(ledger_path, "w") as f:
            json.dump(ledger_data, f, indent=2)
            
        log_to_trace(transaction_id, f"Successfully committed transaction entry to ledger. Total records: {len(ledger_data)}")
        
    except Exception as e:
        log_to_trace(transaction_id, f"Failed updating payout ledger: {str(e)}", level="ERROR")
        raise e
        
    log_to_trace(transaction_id, "Ledger commit operation completed successfully")
    
    return {
        "receipt": receipt
    }
