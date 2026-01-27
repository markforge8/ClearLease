import jwt
import os
from datetime import datetime, timedelta

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 获取 JWT secret
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-jwt-secret")
print(f"Using JWT secret: {SUPABASE_JWT_SECRET}")

# 生成测试 token
def generate_test_token():
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    
    # 使用 HS256 算法生成 token
    token = jwt.encode(payload, SUPABASE_JWT_SECRET, algorithm="HS256")
    print(f"Generated token: {token}")
    
    # 解码 header 查看算法
    import base64
    import json
    header_encoded = token.split('.')[0]
    padding = '=' * ((4 - len(header_encoded) % 4) % 4)
    header_decoded = base64.urlsafe_b64decode(header_encoded + padding)
    header = json.loads(header_decoded)
    print(f"Token algorithm: {header.get('alg')}")
    
    return token

# 测试解码 token
def test_decode_token(token):
    try:
        payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
        print(f"Decoded payload: {payload}")
        return True
    except Exception as e:
        print(f"Error decoding token: {e}")
        return False

if __name__ == "__main__":
    print("Testing JWT generation and decoding...")
    token = generate_test_token()
    print("\nTesting token decoding...")
    success = test_decode_token(token)
    print(f"\nTest {'passed' if success else 'failed'}")
