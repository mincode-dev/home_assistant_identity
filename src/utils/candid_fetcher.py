"""
Simple HTTP Candid interface fetcher - no dfx required!

This utility fetches .did files directly from canisters via HTTP
and saves them to the data folder for use by the Actor Controller.
"""

import requests
import json
import os
from typing import Optional


def get_candid_interface_http(canister_id: str) -> str:
    """
    Get Candid interface via HTTP - no dfx required!
    
    Args:
        canister_id: Your canister ID
        
    Returns:
        Candid interface text or empty string if failed
    """
    
    # List of endpoints to try (in order of preference)
    endpoints = [
        # Method 1: Canister's own endpoint
        f"https://{canister_id}.ic0.app/_/candid",
        
        # Method 2: Raw endpoint
        f"https://{canister_id}.raw.ic0.app/candid",
        
        # Method 3: IC Dashboard API
        f"https://ic-api.internetcomputer.org/api/v3/canisters/{canister_id}",
        
        # Method 4: Alternative gateway
        f"https://ic0.app/_/candid?canister_id={canister_id}",
        
        # Method 5: Well-known location
        f"https://{canister_id}.ic0.app/.well-known/candid",
    ]
    
    for i, url in enumerate(endpoints, 1):
        try:
            print(f"🔍 Method {i}: Trying {url}")
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Check if this is the dashboard API (returns JSON)
                if "ic-api.internetcomputer.org" in url:
                    try:
                        data = response.json()
                        if "candid_interface" in data:
                            candid_text = data["candid_interface"]
                        elif "interface" in data:
                            candid_text = data["interface"]
                        else:
                            print(f"   ❌ No candid interface in JSON response")
                            continue
                    except json.JSONDecodeError:
                        print(f"   ❌ Invalid JSON response")
                        continue
                else:
                    # Direct text response
                    candid_text = response.text
                
                # Validate that this looks like a Candid interface
                if candid_text and ("service" in candid_text or "type" in candid_text):
                    print(f"   ✅ Success! Got {len(candid_text)} characters")
                    return candid_text
                else:
                    print(f"   ❌ Response doesn't look like Candid interface")
                    
        except requests.RequestException as e:
            print(f"   ❌ Request failed: {e}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("❌ All methods failed")
    return ""


def save_candid_to_data_folder(canister_id: str, candid_interface: str, filename: Optional[str] = None) -> str:
    """
    Save Candid interface to the data folder.
    
    Args:
        canister_id: The canister ID
        candid_interface: The Candid interface text
        filename: Optional custom filename (defaults to canister_id.did)
        
    Returns:
        Path to the saved file
    """
    # Determine the data folder path relative to this script
    script_dir = os.path.dirname(__file__)
    data_folder = os.path.join(script_dir, '..', 'data')
    
    # Create data folder if it doesn't exist
    os.makedirs(data_folder, exist_ok=True)
    
    # Generate filename if not provided
    if not filename:
        filename = f"{canister_id}.did"
    
    # Ensure .did extension
    if not filename.endswith('.did'):
        filename += '.did'
    
    file_path = os.path.join(data_folder, filename)
    
    # Save the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(candid_interface)
    
    return file_path


def fetch_and_save_candid(canister_id: str, filename: Optional[str] = None) -> bool:
    """
    Fetch Candid interface from canister and save to data folder.
    
    Args:
        canister_id: The canister ID to fetch from
        filename: Optional custom filename (defaults to canister_id.did)
        
    Returns:
        True if successful, False otherwise
    """
    print(f"🔍 Fetching Candid interface for canister: {canister_id}")
    print("=" * 60)
    
    # Fetch the Candid interface
    candid_interface = get_candid_interface_http(canister_id)
    
    if candid_interface:
        print(f"\n🎉 SUCCESS! Retrieved Candid interface")
        print(f"📄 Length: {len(candid_interface)} characters")
        
        # Save to data folder
        saved_path = save_candid_to_data_folder(canister_id, candid_interface, filename)
        print(f"💾 Saved to: {saved_path}")
        
        print("\n📄 Preview (first 500 characters):")
        print("=" * 60)
        print(candid_interface[:500])
        if len(candid_interface) > 500:
            print("... (truncated)")
        print("=" * 60)
        
        return True
    else:
        print("\n❌ Failed to retrieve Candid interface via HTTP")
        print("\n💡 Alternatives:")
        print(f"   1. Use dfx: dfx canister metadata {canister_id} candid:service --network ic")
        print(f"   2. Check if canister has public metadata enabled")
        print(f"   3. Try manual browser check: https://{canister_id}.ic0.app/_/candid")
        
        return False


def update_autonome_candid():
    """Fetch and update the M_AUTONOME_CANISTER .did file."""
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    canister_id = os.getenv('M_AUTONOME_CANISTER')
    
    if not canister_id:
        print("❌ M_AUTONOME_CANISTER not found in environment variables")
        print("💡 Make sure your .env file contains: M_AUTONOME_CANISTER=your_canister_id")
        return False
    
    print(f"🎯 Updating Candid interface for M_AUTONOME_CANISTER")
    return fetch_and_save_candid(canister_id, "m_autonome_canister.did")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Custom canister ID provided
        canister_id = sys.argv[1]
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        
        print(f"🔍 Fetching Candid interface for custom canister: {canister_id}")
        success = fetch_and_save_candid(canister_id, filename)
        
    else:
        # Default: update M_AUTONOME_CANISTER
        print("🎯 Updating M_AUTONOME_CANISTER Candid interface...")
        success = update_autonome_candid()
    
    if success:
        print("\n✅ Candid interface successfully fetched and saved!")
    else:
        print("\n❌ Failed to fetch Candid interface")
        sys.exit(1)