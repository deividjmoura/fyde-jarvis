import requests

BASE_URL = "http://127.0.0.1:8000"

def perguntar(query: str):
    payload = {"query": query}
    
    response = requests.post(
        f"{BASE_URL}/agent/chat-test", 
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"👤 Você: {query}")
        print(f"🤖 Jarvis: {data.get('response', 'Sem resposta')}")
        print(f"🧵 Thread: {data.get('thread_id')}")
        print("-" * 80)
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")


if __name__ == "__main__":
    print("🚀 Testando Fyde Jarvis com memória persistente...\n")
    
    tests = [
        "pode me dizer tudo que já conversamos ?"
    ]
    
    for pergunta in tests:
        perguntar(pergunta)