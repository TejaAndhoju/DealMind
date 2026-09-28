import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

import hindsight_client_api
from hindsight_client_api.models import RetainRequest, MemoryItem, Content

async def seed_memories():
    key = os.environ.get("HINDSIGHT_API_KEY")
    bank_id = os.environ.get("DEALMIND_BANK_ID", "dealmind-pro")
    
    if not key:
        print("No HINDSIGHT_API_KEY found")
        return

    config = hindsight_client_api.Configuration(host="https://api.hindsight.vectorize.io")
    config.access_token = key
    config.api_key['authorization'] = key
    config.api_key_prefix['authorization'] = 'Bearer'
    
    api_client = hindsight_client_api.ApiClient(config)
    api = hindsight_client_api.MemoryApi(api_client)

    memories = [
        "When a prospect pushes back hard on upfront costs and wants Net-90 terms (like Oscorp), structure a milestone-based payment plan tied to deployment phases. This neutralizes the risk of upfront costs and gets the deal signed.",
        "If a prospect is worried about migration downtime and system outages (like InGen Technologies), provide a dedicated technical account manager for the first 30 days and run the migration over the weekend at no extra cost to alleviate fears.",
        "To overcome vendor lock-in fears (like with Cyberdyne Systems), provide a source-code escrow agreement and standardize our data export APIs to give the CTO peace of mind.",
        "When a prospect's compliance policy mandates an on-prem deployment that we don't natively offer (like Umbrella Corp), solve it by offering a dedicated single-tenant AWS VPC with direct peering to their network. This usually satisfies their security team."
    ]

    items = []
    for mem in memories:
        print(f"Queueing: {mem}")
        content_obj = Content(actual_instance=mem)
        items.append(MemoryItem(content=content_obj))
        
    req = RetainRequest(items=items)
    print("Ingesting...")
    try:
        res = await api.retain_memories(bank_id=bank_id, retain_request=req, authorization=f"Bearer {key}")
        print("Ingestion complete!", res)
    except Exception as e:
        print("Error during ingestion:", e)
    finally:
        await api_client.close()

if __name__ == "__main__":
    asyncio.run(seed_memories())
