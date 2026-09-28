from dotenv import load_dotenv
load_dotenv()
import asyncio
import os
import json
from openai import AsyncOpenAI
from app.db import get_conn
import logging

import hindsight_client_api
from hindsight_client_api.models import RecallRequest, RetainRequest, MemoryItem, Content

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HINDSIGHT_API_KEY = os.environ.get("HINDSIGHT_API_KEY")
BANK_ID = os.environ.get("DEALMIND_BANK_ID", "dealmind-pro")

client = AsyncOpenAI(api_key=GROQ_API_KEY or "dummy", base_url="https://api.groq.com/openai/v1")

def get_hindsight_api():
    config = hindsight_client_api.Configuration(host="https://api.hindsight.vectorize.io")
    config.access_token = HINDSIGHT_API_KEY
    config.api_key['authorization'] = HINDSIGHT_API_KEY
    config.api_key_prefix['authorization'] = 'Bearer'
    api_client = hindsight_client_api.ApiClient(config)
    return hindsight_client_api.MemoryApi(api_client)

async def search_hindsight(query: str, limit: int = 3):
    if not HINDSIGHT_API_KEY:
        logger.warning("No HINDSIGHT_API_KEY found. Skipping memory recall.")
        return []
        
    try:
        api = get_hindsight_api()
        req = RecallRequest(query=query)
        res = await api.recall_memories(bank_id=BANK_ID, recall_request=req, authorization=f"Bearer {HINDSIGHT_API_KEY}")
        
        memories = []
        if hasattr(res, 'results') and res.results:
            for r in res.results:
                if hasattr(r, 'text') and r.text:
                    memories.append(r.text)
                elif hasattr(r, 'content') and hasattr(r.content, 'actual_instance'):
                    memories.append(r.content.actual_instance)
                elif hasattr(r, 'content'):
                    memories.append(str(r.content))
                    
        await api.api_client.close()
        return memories[:limit]
    except Exception as e:
        logger.error(f"Hindsight recall error: {e}")
        try:
            await api.api_client.close()
        except:
            pass
        return []

async def save_novel_solution(deal_company: str, solution: str):
    if not HINDSIGHT_API_KEY:
        return "Error: HINDSIGHT_API_KEY missing."
        
    try:
        api = get_hindsight_api()
        content_text = f"Novel solution successfully applied for {deal_company}: {solution}"
        content_obj = Content(actual_instance=content_text) 
        item = MemoryItem(content=content_obj)
        req = RetainRequest(items=[item])
        
        await api.retain_memories(bank_id=BANK_ID, retain_request=req, authorization=f"Bearer {HINDSIGHT_API_KEY}")
        await api.api_client.close()
        return "Saved to Hindsight Memory successfully!"
    except Exception as e:
        logger.error(f"Hindsight retain error: {e}")
        try:
            await api.api_client.close()
        except:
            pass
        return f"Error saving: {str(e)}"

async def analyze_chat_stream(query: str, active_deal_id: str = None):
    try:
        yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing query...'})}\n\n"
        
        conn = get_conn()
        deals = [dict(row) for row in conn.execute("SELECT * FROM deals").fetchall()]
        
        context_str = "ALL DEALS OVERVIEW:\n"
        active_deal = None
        for d in deals:
            context_str += f"- [{d['id']}] {d['company']} | Stage: {d['stage']} | Value: ${d['value']}\n"
            if d['blocker']: context_str += f"  Blocker: {d['blocker']}\n"
            if d['success_reason']: context_str += f"  Success Reason: {d['success_reason']}\n"
            if active_deal_id and d['id'] == active_deal_id:
                active_deal = d
                
        if active_deal:
            transcripts = [dict(row) for row in conn.execute("SELECT * FROM transcripts WHERE deal_id=?", (active_deal_id,)).fetchall()]
            context_str += f"\nACTIVE DEAL TRANSCRIPTS ({active_deal['company']}):\n"
            for t in transcripts:
                context_str += f"[{t['date']}] {t['content']}\n"
        conn.close()

        yield f"data: {json.dumps({'type': 'status', 'message': 'Querying Hindsight Memory...'})}\n\n"
        search_q = query
        if active_deal and active_deal['blocker']:
            search_q += f" {active_deal['blocker']}"
            
        memories = await search_hindsight(search_q, limit=3)
        if memories:
            yield f"data: {json.dumps({'type': 'memory', 'memories': memories})}\n\n"
            # Send a visible chat bubble to emphasize Hindsight
            mem_alert = "🧠 **HINDSIGHT MEMORY MATCH**\n\nI found relevant historical playbooks in our Vectorize memory bank:\n\n"
            for m in memories:
                mem_alert += f"- {m}\n"
            mem_alert += "\n*Synthesizing a personalized strategy based on these past wins...*"
            yield f"data: {json.dumps({'type': 'chunk', 'content': mem_alert + chr(10) + chr(10)})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'memory', 'memories': []})}\n\n"
            
        mem_context = "\n".join(memories) if memories else "No relevant past memories found."

        sys_prompt = f"""You are DealMind, an elite AI Sales Agent.
You have access to the company's CRM data and Hindsight memory (past successful tactics).

CRM CONTEXT:
{context_str}

HINDSIGHT MEMORIES (What worked in the past):
{mem_context}

RULES:
1. Answer the user's question directly and conversationally in a sales-oriented tone.
2. If they ask about a stuck deal, use Hindsight Memory to suggest a solution. If no memory exists or the previous solution was rejected, generate a fresh, highly tactical market-based sales solution to overcome the blocker.
3. If they ask why a deal was successful, refer to the 'Success Reason' in the CRM context.
4. Format your response nicely using Markdown (bullet points, bold text).
"""

        yield f"data: {json.dumps({'type': 'status', 'message': 'Synthesizing response...'})}\n\n"
        
        stream = await client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": query}
            ],
            stream=True
        )
        
        full_response = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                text = chunk.choices[0].delta.content
                full_response += text
                yield f"data: {json.dumps({'type': 'chunk', 'content': text})}\n\n"
                await asyncio.sleep(0.01)
                
        # Always offer the feedback buttons if the active deal is Stalled
        if active_deal and active_deal['stage'] == 'Stalled':
            yield f"data: {json.dumps({'type': 'solution_proposed', 'deal': active_deal['company'], 'solution_text': full_response})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
