import sys
import base64
import json

def decode_jwt_header(token):
    try:
        # 分割 JWT 为三部分
        parts = token.split('.')
        if len(parts) != 3:
            print("Invalid JWT format")
            return
        
        # 获取 header 部分并解码
        header_encoded = parts[0]
        # 补充 base64 填充
        padding = '=' * ((4 - len(header_encoded) % 4) % 4)
        header_decoded = base64.urlsafe_b64decode(header_encoded + padding)
        header = json.loads(header_decoded)
        
        print("JWT Header:")
        print(json.dumps(header, indent=2))
        print(f"\nAlgorithm used: {header.get('alg')}")
        
    except Exception as e:
        print(f"Error decoding JWT: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python decode_jwt_header.py <JWT token>")
        sys.exit(1)
    
    token = sys.argv[1]
    decode_jwt_header(token)
