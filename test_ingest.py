import requests

# Test text file upload
print("Testing text file upload...")
with open('test.txt', 'rb') as f:
    response = requests.post('http://localhost:8080/ingest', files={'file': f})
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

print("Test completed!")
