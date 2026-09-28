import os
import asyncio
import hindsight_client_api
from hindsight_client_api.rest import ApiException
from hindsight_client_api.models import RecallRequest, RetainRequest, MemoryItem

async def test_hindsight():
    key = os.environ.get("HINDSIGHT_API_KEY")
    if not key:
        print("Missing HINDSIGHT_API_KEY")
        return
        
    config = hindsight_client_api.Configuration(host="https://api.hindsight.vectorize.io")
    config.access_token = key
    
    # Try api_key as well just in case
    config.api_key['authorization'] = key
    config.api_key_prefix['authorization'] = 'Bearer'
    
    api_client = hindsight_client_api.ApiClient(config)
    api = hindsight_client_api.MemoryApi(api_client)
    
    bank_id = "dealmind-pro"
    
    # Test Retain
    print("Testing Retain...")
    try:
        from hindsight_client_api.models import Content
        content_obj = Content(actual_instance="Test memory for hackathon") 
        item = MemoryItem(content=content_obj)
        req = RetainRequest(items=[item])
        res = await api.retain_memories(bank_id=bank_id, retain_request=req, authorization=f"Bearer {key}")
        print("Retain Success:", res)
    except ApiException as e:
        print("Retain Exception:", e.reason, e.body)
        
    # Test Recall
    print("Testing Recall...")
    try:
        req = RecallRequest(query="hackathon")
        res = await api.recall_memories(bank_id=bank_id, recall_request=req, authorization=f"Bearer {key}")
        print("Recall Success:", res)
    except ApiException as e:
        print("Recall Exception:", e.reason, e.body)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(test_hindsight())
