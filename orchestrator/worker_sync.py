import json
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import httpx
import os
import time
import traceback

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://aetherion:aetherion_secret@postgres:5432/aetherion")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

print(f"Connecting to DB: {DATABASE_URL}")
print(f"Connecting to Redis: {REDIS_URL}")

# Синхронный движок с psycopg2
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


class AetherionWorker:
    def __init__(self):
        self.redis = None

    def call_free_ai(self, prompt: str, run_id: str = None) -> str:
        """Бесплатный AI через OpenRouter"""
        api_key = os.getenv("OPENROUTER_API_KEY", "")

        if not api_key:
            self.send_log(run_id, "⚠️ No OpenRouter API key, using mock", "WARNING")
            return f"[MOCK] AI would respond to: {prompt[:100]}..."

        try:
            response = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",  # бесплатная модель
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=30.0
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                self.send_log(run_id, f"AI API error: {response.status_code}", "ERROR")
                return f"Error: {response.status_code}"

        except Exception as e:
            self.send_log(run_id, f"AI call failed: {e}", "ERROR")
            return f"Error: {e}"

    def send_log(self, run_id: str, message: str, level: str = "INFO"):
        try:
            with SessionLocal() as session:
                session.execute(
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
                session.commit()
        except Exception as e:
            print(f"Error sending log: {e}")

    def update_progress(self, run_id: str, progress: int):
        try:
            with SessionLocal() as session:
                session.execute(
                    text("UPDATE workflow_runs SET progress = :progress WHERE id = :run_id"),
                    {"progress": progress, "run_id": run_id}
                )
                session.commit()
        except Exception as e:
            print(f"Error updating progress: {e}")

    def tool_http_request(self, url: str, method: str = "GET") -> dict:
        with httpx.Client(timeout=10.0) as client:
            resp = client.request(method, url)
            return {"status": resp.status_code, "body": resp.text[:500]}

    def tool_calculate(self, expression: str) -> float:
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
        try:
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            return float(result)
        except:
            raise ValueError(f"Invalid expression: {expression}")

    def execute_workflow(self, workflow_name: str, payload: dict, run_id: str) -> dict:
        self.send_log(run_id, f"Starting workflow: {workflow_name}", "INFO")
        self.update_progress(run_id, 10)

        if workflow_name == "calculator":
            expr = payload.get("expression", "2+2")
            self.send_log(run_id, f"Calculating: {expr}", "INFO")
            self.update_progress(run_id, 50)
            result = self.tool_calculate(expr)
            self.update_progress(run_id, 100)
            return {"result": result}


        elif workflow_name == "ai_chat":
            prompt = payload.get("prompt", "Hello, who are you?")
            self.send_log(run_id, f"Sending to AI: {prompt[:50]}...", "INFO")
            self.update_progress(run_id, 50)
            response = self.call_free_ai(prompt, run_id=run_id)  # ← используем бесплатный AI
            self.update_progress(run_id, 100)
            return {"reply": response, "model_used": "free-ai"}

        elif workflow_name == "fetch_and_summarize":
            url = payload.get("url", "https://example.com")
            self.send_log(run_id, f"Fetching: {url}", "INFO")
            self.update_progress(run_id, 50)
            data = self.tool_http_request(url)
            self.update_progress(run_id, 100)
            return {"summary": f"Fetched {len(data['body'])} chars from {url}", "length": len(data['body'])}


        elif workflow_name == "code_review":
            code = payload.get("code", "")
            self.send_log(run_id, f"Reviewing {len(code)} chars of code", "INFO")
            self.update_progress(run_id, 40)
            review = self.call_free_ai(f"Review this code for bugs and improvements:\n\n{code}", run_id=run_id)
            self.update_progress(run_id, 100)
            return {"review": review}

        elif workflow_name == "translator":
            text = payload.get("text", "")
            source_lang = payload.get("source", "auto")  # auto, en, ru
            target_lang = payload.get("target", "en")  # en, ru

            from deep_translator import GoogleTranslator

            self.send_log(run_id, f"Translating: {text[:50]}... from {source_lang} to {target_lang}", "INFO")
            self.update_progress(run_id, 50)

            try:
                translated = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
                self.update_progress(run_id, 100)
                return {
                    "original": text,
                    "translated": translated,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                }
            except Exception as e:
                raise ValueError(f"Translation error: {e}")

        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")

    def process_queue(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        last_id = "0"

        print("🧠 Aetherion Orchestrator Worker started")
        print(f"📡 Connected to Redis")
        print(f"💾 Database connected")

        # Create logs table if not exists
        try:
            with SessionLocal() as session:
                session.execute(text("""
                    CREATE TABLE IF NOT EXISTS workflow_logs (
                        id SERIAL PRIMARY KEY,
                        run_id VARCHAR NOT NULL,
                        level VARCHAR,
                        message TEXT,
                        created_at TIMESTAMP
                    )
                """))
                session.commit()
                print("✅ Tables ready")
        except Exception as e:
            print(f"Table creation error: {e}")

        print("✅ Worker ready, waiting for tasks...")

        while True:
            try:
                results = self.redis.xread({"workflow:queue": last_id}, count=1, block=1000)

                if not results:
                    continue

                for stream_name, messages in results:
                    for msg_id, data in messages:
                        run_id = data["run_id"]
                        workflow_name = data["workflow_name"]
                        payload = json.loads(data["payload"])

                        print(f"📨 Received task: {workflow_name} (run_id: {run_id[:8]}...)")

                        # Update status to RUNNING
                        try:
                            with SessionLocal() as session:
                                session.execute(
                                    text(
                                        "UPDATE workflow_runs SET status = 'RUNNING', started_at = :now WHERE id = :run_id"),
                                    {"now": datetime.utcnow(), "run_id": run_id}
                                )
                                session.commit()
                        except Exception as e:
                            print(f"Error updating status: {e}")

                        try:
                            output = self.execute_workflow(workflow_name, payload, run_id)
                            status = "SUCCESS"
                            output_data = output
                            error_msg = None

                            self.send_log(run_id, "✅ Workflow completed successfully", "INFO")
                            print(f"✅ Task completed: {run_id[:8]}...")

                        except Exception as e:
                            status = "FAILED"
                            output_data = None
                            error_msg = f"{str(e)}\n{traceback.format_exc()}"
                            self.send_log(run_id, f"❌ Workflow failed: {e}", "ERROR")
                            print(f"❌ Task failed: {run_id[:8]}... - {e}")

                        # Final update
                        try:
                            with SessionLocal() as session:
                                session.execute(
                                    text("""
                                        UPDATE workflow_runs 
                                        SET status = :status, 
                                            output_data = :output_data, 
                                            error_msg = :error_msg,
                                            finished_at = :now
                                        WHERE id = :run_id
                                    """),
                                    {
                                        "status": status,
                                        "output_data": json.dumps(output_data) if output_data else None,
                                        "error_msg": error_msg,
                                        "now": datetime.utcnow(),
                                        "run_id": run_id
                                    }
                                )
                                session.commit()
                        except Exception as e:
                            print(f"Error final update: {e}")

                        last_id = msg_id

            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(1)


if __name__ == "__main__":
    worker = AetherionWorker()
    worker.process_queue()