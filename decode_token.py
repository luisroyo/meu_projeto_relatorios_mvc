import jwt
import json

# Token gerado pela API
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE3NTQ0MzIwNTF9.1rT_j6savn1J7pzDgN9gYak4RmRBTg1OGHQv_XWP9YA"

# Decodificar sem verificar a assinatura (apenas para ver o conteúdo)
try:
    decoded = jwt.decode(token, options={"verify_signature": False})
    print("Token decodificado:")
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print(f"Erro ao decodificar: {e}") 