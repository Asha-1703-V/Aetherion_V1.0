import asyncio
import json
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime
import httpx
import os
from typing import Dict, Any
import traceback

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://aetherion:aetherion_secret@postgres:5432/aetherion")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class AetherionWorker:
    def __init__(self):
        self.redis = None

    async def send_log(self, run_id: str, message: str, level: str = "INFO"):
        """Отправка лога в PostgreSQL"""
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                    INSERT INTO workflow_logs (run_id, level, message, created_at)
                    VALUES (:run_id, :level, :message, :created_at)
                """),
                {
                    "run_id": run_id,
                    "level": level,
                    "message": message,
                    "created_at": datetime.utcnow()
                }
            )
            await session.commit()

    async def update_progress(self, run_id: str, progress: int):
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE workflow_runs SET progress = :progress WHERE id = :run_id"),
                {"progress": progress, "run_id": run_id}
            )
            await session.commit()

    async def call_llm(self, prompt: str, model: str = "gpt-3.5-turbo", run_id: str = None) -> str:
        """Вызов LLM с логированием"""
        if not OPENAI_API_KEY or OPENAI_API_KEY == "sk-dummy-key-for-demo":
            await self.send_log(run_id, f"⚠️ Using mock LLM (no API key)", "WARNING")
            return f"[MOCK] AI Response to: {prompt[:100]}... (would use {model})"

        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            response = await openai.ChatCompletion.acreate(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )

            async with AsyncSessionLocal() as session:
                await session.execute(
                    text("""
                        INSERT INTO llm_call_logs (run_id, model, prompt_tokens, completion_tokens, total_tokens, cost_usd)
                        VALUES (:run_id, :model, :prompt_tokens, :completion_tokens, :total_tokens, :cost_usd)
                    """),
                    {
                        "run_id": run_id,
                        "model": model,
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                        "cost_usd": response.usage.total_tokens * 0.000002
                    }
                )
                await session.commit()

            return response.choices[0].message.content
        except Exception as e:
            await self.send_log(run_id, f"LLM Error: {e}", "ERROR")
            return f"Error calling LLM: {e}"

    async def tool_http_request(self, url: str, method: str = "GET") -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.request(method, url)
            return {"status": resp.status_code, "body": resp.text[:500]}

    async def tool_calculate(self, expression: str) -> float:
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)
        except:
            raise ValueError(f"Invalid expression: {expression}")

    async def execute_workflow(self, workflow_name: str, payload: dict, run_id: str) -> Dict[str, Any]:
        await self.send_log(run_id, f"Starting workflow: {workflow_name}", "INFO")
        await self.update_progress(run_id, 10)

        if workflow_name == "ai_chat":
            prompt = payload.get("prompt", "Hello, who are you?")
            await self.send_log(run_id, f"Sending to LLM: {prompt[:50]}...", "INFO")
            await self.update_progress(run_id, 50)
            response = await self.call_llm(prompt, run_id=run_id)
            await self.update_progress(run_id, 100)
            return {"reply": response, "model_used": "gpt-3.5-turbo"}

        elif workflow_name == "fetch_and_summarize":
            url = payload.get("url")
            if not url:
                raise ValueError("URL is required")
            await self.send_log(run_id, f"Fetching: {url}", "INFO")
            await self.update_progress(run_id, 30)
            data = await self.tool_http_request(url)
            await self.send_log(run_id, f"Fetched {len(data['body'])} chars", "INFO")
            await self.update_progress(run_id, 60)
            summary = await self.call_llm(f"Summarize this text in 2-3 sentences: {data['body'][:2000]}", run_id=run_id)
            await self.update_progress(run_id, 100)
            return {"summary": summary, "fetched_length": len(data['body'])}

        elif workflow_name == "calculator":
            expr = payload.get("expression", "2+2")
            await self.send_log(run_id, f"Calculating: {expr}", "INFO")
            await self.update_progress(run_id, 50)
            result = await self.tool_calculate(expr)
            await self.update_progress(run_id, 100)
            return {"result": result}

        elif workflow_name == "code_review":
            code = payload.get("code", "")
            await self.send_log(run_id, f"Reviewing {len(code)} chars of code", "INFO")
            await self.update_progress(run_id, 40)
            review = await self.call_llm(f"Review this code for bugs and improvements:\n\n{code}", run_id=run_id)
            await self.update_progress(run_id, 100)
            return {"review": review}

        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")

    async def process_queue(self):
        self.redis = await redis.from_url(REDIS_URL, decode_responses=True)
        last_id = "0"

        print("🧠 Aetherion Orchestrator Worker started")
        print(f"📡 Connected to Redis at {REDIS_URL}")
        print(f"💾 Database: {DATABASE_URL}")

        # Create logs table if not exists
        async with AsyncSessionLocal() as session:
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS workflow_logs (
                    id SERIAL PRIMARY KEY,
                    run_id VARCHAR NOT NULL,
                    level VARCHAR,
                    message TEXT,
                    created_at TIMESTAMP
                )
            """))
            await session.commit()

        while True:
            try:
                results = await self.redis.xread(
                    {"workflow:queue": last_id},
                    count=1,
                    block=1000
                )

                if not results:
                    continue

                for stream_name, messages in results:
                    for msg_id, data in messages:
                        run_id = data["run_id"]
                        workflow_name = data["workflow_name"]
                        payload = json.loads(data["payload"])

                        # Update status to RUNNING
                        async with AsyncSessionLocal() as session:
                            await session.execute(
                                text(
                                    "UPDATE workflow_runs SET status = 'RUNNING', started_at = :now WHERE id = :run_id"),
                                {"now": datetime.utcnow(), "run_id": run_id}
                            )
                            await session.commit()

                        try:
                            output = await self.execute_workflow(workflow_name, payload, run_id)
                            status = "SUCCESS"
                            output_data = output
                            error_msg = None
                            cost = 0.01

                            await self.send_log(run_id, "✅ Workflow completed successfully", "INFO")

                        except Exception as e:
                            status = "FAILED"
                            output_data = None
                            error_msg = f"{str(e)}\n{traceback.format_exc()}"
                            cost = 0.0
                            await self.send_log(run_id, f"❌ Workflow failed: {e}", "ERROR")

                        # Final update
                        async with AsyncSessionLocal() as session:
                            await session.execute(
                                text("""
                                    UPDATE workflow_runs 
                                    SET status = :status, 
                                        output_data = :output_data, 
                                        error_msg = :error_msg,
                                        finished_at = :now,
                                        total_cost_usd = :cost
                                    WHERE id = :run_id
                                """),
                                {
                                    "status": status,
                                    "output_data": json.dumps(output_data) if output_data else None,
                                    "error_msg": error_msg,
                                    "now": datetime.utcnow(),
                                    "cost": cost,
                                    "run_id": run_id
                                }
                            )
                            await session.commit()

                        last_id = msg_id

            except Exception as e:
                print(f"Worker error: {e}")
                await asyncio.sleep(1)


if __name__ == "__main__":
    worker = AetherionWorker()
    asyncio.run(worker.process_queue())