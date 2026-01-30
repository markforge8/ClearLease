import requests
import json

# Test analyze endpoint
print("Testing analyze endpoint...")

# Test data
payload = {
    "contract_text": "This is a test contract. It contains some terms and conditions."
}

# Headers (add authorization if needed)
headers = {
    "Content-Type": "application/json"
}

# Send request
try:
    response = requests.post(
        "http://localhost:8080/analyze",
        json=payload,
        headers=headers
    )
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    # Get analysis_id if available
    analysis_id = response.json().get('analysis_id')
    if analysis_id:
        print(f"Analysis ID: {analysis_id}")
    else:
        print("No analysis_id returned (user not logged in)")
        
except Exception as e:
    print(f"Error: {e}")

print("Test completed!")
