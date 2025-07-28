import secrets
import string

def generate_api_key(length=32):
    """Generate a secure random API key"""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key

if __name__ == "__main__":
    api_key = generate_api_key()
    print("\nGenerated API Key (copy this to your .env file):")
    print("API_KEY=" + api_key)
    print("\nExample usage:")
    print(f'curl -H "X-API-Key: {api_key}" http://localhost:8000/balances')
    print("\nMake sure to keep this key secure and never share it publicly!")