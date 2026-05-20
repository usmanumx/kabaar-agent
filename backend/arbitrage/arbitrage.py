#!/usr/bin/env python3
"""
arbitrage.py
Commodity matching and arbitrage logic for KabaarAgent.
Calculates optimal commercial recycling yard buyer based on distance, material support, minimum batch size, and payout rates.
"""

import json
import math
import os
import sys
import argparse

# Default coordinates for seller (mocked)
DEFAULT_LAT = 33.60
DEFAULT_LNG = 73.06
MAX_DISTANCE_KM = 5.0

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth's surface
    using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in kilometers

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def load_market_rates(filepath=None):
    """
    Load market rates and yard details from JSON file.
    """
    if filepath is None:
        # Resolve path relative to this script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(current_dir, 'market_rates.json')

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Market rates file not found at {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_arbitrage(scrap_items, seller_lat=DEFAULT_LAT, seller_lng=DEFAULT_LNG, market_rates_path=None):
    """
    Core arbitrage logic to select the optimal recycling yard and calculate valuation.
    
    Parameters:
      scrap_items (list): List of dicts representing parsed scrap items, e.g.
                          [{"material": "Copper", "weight_kg": 15.0}, ...]
      seller_lat (float): Seller latitude.
      seller_lng (float): Seller longitude.
      market_rates_path (str): Path to market_rates.json.
      
    Returns:
      dict: JSON response containing coordinates, yards breakdown, selection, total valuation, and justification logs.
    """
    try:
        rates_data = load_market_rates(market_rates_path)
    except Exception as e:
        return {
            "error": f"Failed to load market rates: {str(e)}"
        }

    currency = rates_data.get("currency", "PKR")
    base_rates = rates_data.get("base_rates", {})
    yards = rates_data.get("recycling_yards", [])

    # Calculate total weight per material in the scrap items
    aggregated_items = {}
    total_input_weight = 0.0
    for item in scrap_items:
        material = item.get("material")
        weight = float(item.get("weight_kg", 0.0))
        if not material or weight <= 0:
            continue
        aggregated_items[material] = aggregated_items.get(material, 0.0) + weight
        total_input_weight += weight

    justification_log = []
    justification_log.append(f"Negotiation Agent initiated. Analyzing scrap batch of {total_input_weight:.2f} kg across materials: {list(aggregated_items.keys())}.")
    justification_log.append(f"Seller location: ({seller_lat:.4f}, {seller_lng:.4f}). Max distance threshold: {MAX_DISTANCE_KM} km.")

    yard_results = []
    selected_yard = None
    max_valuation = -1.0
    optimal_yard_details = None

    for yard in yards:
        name = yard.get("name")
        location = yard.get("location")
        coords = yard.get("coordinates", {})
        yard_lat = coords.get("latitude")
        yard_lng = coords.get("longitude")
        buys = yard.get("buys", [])
        min_batch_kg = float(yard.get("min_batch_kg", 0.0))
        payout_premium = float(yard.get("payout_premium", 0.0))

        # 1. Distance check
        dist = haversine_distance(seller_lat, seller_lng, yard_lat, yard_lng)
        in_range = dist <= MAX_DISTANCE_KM

        # 2. Check bought materials and calculate batch weight for this yard
        bought_items = {}
        yard_batch_weight = 0.0
        for mat, weight in aggregated_items.items():
            if mat in buys:
                bought_items[mat] = weight
                yard_batch_weight += weight

        # 3. Batch size validation
        batch_size_met = yard_batch_weight >= min_batch_kg

        # Payout calculation if eligible
        valuation_details = {}
        total_yard_payout = 0.0
        is_eligible = False
        reasons = []

        if not in_range:
            reasons.append(f"Out of range: distance is {dist:.2f} km (limit: {MAX_DISTANCE_KM} km)")
        if not bought_items:
            reasons.append(f"Does not purchase any materials in this scrap batch (Buys: {buys})")
        elif not batch_size_met:
            reasons.append(f"Minimum batch size of {min_batch_kg} kg not met for accepted items (Batch weight: {yard_batch_weight:.2f} kg, required: {min_batch_kg:.2f} kg)")

        if in_range and bought_items and batch_size_met:
            is_eligible = True
            justification_log.append(f"[{name}] Eligible. Distance: {dist:.2f} km. Accepted batch weight: {yard_batch_weight:.2f} kg (min required: {min_batch_kg} kg).")
            # Calculate itemized payouts
            for mat, weight in bought_items.items():
                base_rate = base_rates.get(mat, 0.0)
                effective_rate = base_rate * (1 + payout_premium)
                item_payout = weight * effective_rate
                total_yard_payout += item_payout
                valuation_details[mat] = {
                    "weight_kg": weight,
                    "base_rate": base_rate,
                    "effective_rate": effective_rate,
                    "payout": item_payout
                }
                justification_log.append(f"  - {mat}: {weight:.2f} kg @ {effective_rate:.2f} {currency}/kg (Base: {base_rate:.2f}, Premium: +{payout_premium*100:.1f}%) = {item_payout:.2f} {currency}")
            justification_log.append(f"  - Total potential payout for [{name}]: {total_yard_payout:.2f} {currency}")
        else:
            justification_log.append(f"[{name}] Ineligible. Distance: {dist:.2f} km. Reasons: {', '.join(reasons)}")

        result_entry = {
            "name": name,
            "location": location,
            "distance_km": dist,
            "is_eligible": is_eligible,
            "reasons": reasons,
            "total_payout_pkr": total_yard_payout if is_eligible else 0.0,
            "itemized_valuation": valuation_details if is_eligible else {}
        }
        yard_results.append(result_entry)

        if is_eligible and total_yard_payout > max_valuation:
            max_valuation = total_yard_payout
            selected_yard = name
            optimal_yard_details = {
                "name": name,
                "location": location,
                "distance_km": dist,
                "payout_premium": payout_premium,
                "total_payout_pkr": total_yard_payout,
                "itemized_valuation": valuation_details
            }

    # Selection & Negotiation Justification Summary
    if selected_yard:
        justification_log.append(f"Decision: Selected [{selected_yard}] as the optimal buyer with total payout of {max_valuation:.2f} {currency}.")
        # Compare with runner up if any
        other_eligible = [y for y in yard_results if y["is_eligible"] and y["name"] != selected_yard]
        if other_eligible:
            runner_up = max(other_eligible, key=lambda x: x["total_payout_pkr"])
            diff = max_valuation - runner_up["total_payout_pkr"]
            justification_log.append(f"Justification: [{selected_yard}] outperforms [{runner_up['name']}] by {diff:.2f} {currency} due to premium pricing / batch match.")
        else:
            justification_log.append(f"Justification: [{selected_yard}] is the only eligible buyer within {MAX_DISTANCE_KM} km satisfying minimum batch size requirements.")
    else:
        justification_log.append("Decision: No recycling yards are eligible. No selection made.")

    eligible_yards = [y for y in yard_results if y["is_eligible"]]
    ineligible_yards = [y for y in yard_results if not y["is_eligible"]]

    return {
        "seller_coordinates": {
            "latitude": seller_lat,
            "longitude": seller_lng
        },
        "total_input_weight_kg": total_input_weight,
        "eligible_yards": eligible_yards,
        "ineligible_yards": ineligible_yards,
        "selected_yard": optimal_yard_details,
        "total_valuation_pkr": max(0.0, max_valuation),
        "currency": currency,
        "negotiation_justification_log": "\n".join(justification_log)
    }

def main():
    parser = argparse.ArgumentParser(description="KabaarAgent Arbitrage & Matching Tool")
    parser.add_argument("--items", type=str, help="JSON string of parsed scrap items, e.g. '[{\"material\":\"Copper\",\"weight_kg\":12.5}]'")
    parser.add_argument("--items-file", type=str, help="Path to a JSON file containing the parsed scrap items")
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Seller latitude")
    parser.add_argument("--lng", type=float, default=DEFAULT_LNG, help="Seller longitude")
    parser.add_argument("--rates", type=str, help="Path to market_rates.json")

    args = parser.parse_args()

    # Parse items
    scrap_items = []
    if args.items:
        try:
            scrap_items = json.loads(args.items)
        except Exception as e:
            print(json.dumps({"error": f"Invalid JSON in --items: {str(e)}"}), file=sys.stderr)
            sys.exit(1)
    elif args.items_file:
        try:
            with open(args.items_file, 'r', encoding='utf-8') as f:
                scrap_items = json.load(f)
        except Exception as e:
            print(json.dumps({"error": f"Failed to read --items-file: {str(e)}"}), file=sys.stderr)
            sys.exit(1)
    else:
        # Try reading from stdin if it's not a tty
        if not sys.stdin.isatty():
            try:
                stdin_data = sys.stdin.read().strip()
                if stdin_data:
                    scrap_items = json.loads(stdin_data)
            except Exception as e:
                print(json.dumps({"error": f"Failed to parse stdin JSON: {str(e)}"}), file=sys.stderr)
                sys.exit(1)
        else:
            # If no inputs, run with a mocked default list for demonstration
            scrap_items = [
                {"material": "Copper", "weight_kg": 15.0},
                {"material": "Iron", "weight_kg": 8.0},
                {"material": "Aluminum", "weight_kg": 2.5}
            ]

    result = run_arbitrage(scrap_items, args.lat, args.lng, args.rates)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
