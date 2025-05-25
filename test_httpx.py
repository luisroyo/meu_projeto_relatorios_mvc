# test_httpx.py
import httpx
import os

print(f"--- Testando httpx.Client() ---")
print(f"Variável de ambiente HTTP_PROXY: {os.getenv('HTTP_PROXY')}")
print(f"Variável de ambiente HTTPS_PROXY: {os.getenv('HTTPS_PROXY')}")
print(f"Variável de ambiente ALL_PROXY: {os.getenv('ALL_PROXY')}")

try:
    print("Tentando: client = httpx.Client()")
    client = httpx.Client()
    print("Sucesso: httpx.Client() inicializado.")

    print("\nTentando: client_proxies_empty = httpx.Client(proxies={})")
    client_proxies_empty = httpx.Client(proxies={})
    print("Sucesso: httpx.Client(proxies={}) inicializado.")

    print("\nTentando: client_proxies_none = httpx.Client(proxies=None)")
    client_proxies_none = httpx.Client(proxies=None)
    print("Sucesso: httpx.Client(proxies=None) inicializado.")

except TypeError as te:
    print(f"\nERRO (TypeError) ao inicializar httpx.Client: {te}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"\nERRO (Outro) ao inicializar httpx.Client: {e}")
    import traceback
    traceback.print_exc()