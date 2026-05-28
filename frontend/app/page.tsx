"use client";

import { useState, useEffect } from "react";

export default function Dashboard() {
  const [workflow, setWorkflow] = useState("calculator");
  const [payload, setPayload] = useState('{"expression": "15 * 4 - 7"}');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);
  const [runs, setRuns] = useState<any[]>([]);

  useEffect(() => {
    fetchMetrics();
    fetchRuns();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchMetrics = async () => {
    try {
      const res = await fetch("/api/v1/metrics");
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      console.error("Failed to fetch metrics", e);
    }
  };

  const fetchRuns = async () => {
    try {
      const res = await fetch("/api/v1/runs?limit=10");
      const data = await res.json();
      setRuns(data);
    } catch (e) {
      console.error("Failed to fetch runs", e);
    }
  };

  const executeWorkflow = async () => {
    setLoading(true);
    setResult(null);

    try {
      let parsedPayload;
      try {
        parsedPayload = JSON.parse(payload);
      } catch {
        parsedPayload = { text: payload };
      }

      const res = await fetch("/api/v1/execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workflow_name: workflow,
          payload: parsedPayload,
          async_mode: false
        })
      });

      const data = await res.json();
      setResult(data);
      fetchMetrics();
      fetchRuns();
    } catch (error: any) {
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const workflows = [
    {
      value: "calculator",
      label: "🧮 Калькулятор",
      description: "Вычисление математических выражений",
      example: '{"expression": "15 * 4 - 7"}',
      payload: '{"expression": "15 * 4 - 7"}'
    },
    {
      value: "ai_chat",
      label: "🤖 AI Чат",
      description: "Общение с искусственным интеллектом",
      example: '{"prompt": "Расскажи шутку про программистов"}',
      payload: '{"prompt": "Расскажи шутку про программистов"}'
    },
    {
      value: "fetch_and_summarize",
      label: "🌐 Парсинг сайта",
      description: "Извлечение и суммаризация содержимого веб-страницы",
      example: '{"url": "https://example.com"}',
      payload: '{"url": "https://example.com"}'
    },
    {
      value: "code_review",
      label: "📝 Code Review",
      description: "Анализ кода на наличие ошибок",
      example: '{"code": "def divide(a,b):\\n    return a/b"}',
      payload: '{"code": "def divide(a,b):\\n    return a/b"}'
    },
    {
      value: "translator",
      label: "🌐 Переводчик",
      description: "Перевод с английского на русский и обратно",
      example: '{"text": "Hello, how are you?", "target": "ru"}',
      payload: '{"text": "Hello, how are you?", "target": "ru"}'
    }
  ];

  const currentWorkflow = workflows.find(w => w.value === workflow);

  const setExample = (workflowValue: string, payloadText: string) => {
    setWorkflow(workflowValue);
    setPayload(payloadText);
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case "SUCCESS": return "#10b981";
      case "FAILED": return "#ef4444";
      case "RUNNING": return "#f59e0b";
      default: return "#6b7280";
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      padding: "20px"
    }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{
          background: "white",
          borderRadius: "16px",
          padding: "24px 32px",
          marginBottom: "24px",
          boxShadow: "0 4px 6px rgba(0,0,0,0.1)"
        }}>
          <h1 style={{ margin: 0, color: "#667eea", fontSize: "2rem" }}>🌀 Aetherion</h1>
          <p style={{ color: "#666", marginTop: "8px" }}>Enterprise AI Orchestration Platform</p>
        </div>

        {/* Metrics Cards */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "24px"
        }}>
          <div style={{ background: "white", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#667eea" }}>{metrics?.total_runs || 0}</div>
            <div style={{ color: "#666", marginTop: "8px" }}>Всего запусков</div>
          </div>
          <div style={{ background: "white", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#ef4444" }}>{metrics?.failed_runs || 0}</div>
            <div style={{ color: "#666", marginTop: "8px" }}>Ошибок</div>
          </div>
          <div style={{ background: "white", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
            <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#10b981" }}>${(metrics?.total_cost_usd || 0).toFixed(4)}</div>
            <div style={{ color: "#666", marginTop: "8px" }}>Затраты</div>
          </div>
        </div>

        {/* Main Content */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>

          {/* Left Panel - Execute */}
          <div style={{ background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
            <h2 style={{ marginTop: 0, marginBottom: "20px", color: "#333" }}>🚀 Выполнить workflow</h2>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "bold", color: "#555" }}>Выберите тип</label>
              <div style={{ display: "grid", gap: "8px" }}>
                {workflows.map(w => (
                  <button
                    key={w.value}
                    onClick={() => {
                      setWorkflow(w.value);
                      setPayload(w.payload);
                    }}
                    style={{
                      textAlign: "left",
                      padding: "12px 16px",
                      background: workflow === w.value ? "#667eea" : "#f8f9fa",
                      color: workflow === w.value ? "white" : "#333",
                      border: "none",
                      borderRadius: "8px",
                      cursor: "pointer",
                      transition: "all 0.2s"
                    }}
                  >
                    <div style={{ fontWeight: "bold" }}>{w.label}</div>
                    <div style={{ fontSize: "12px", opacity: 0.8 }}>{w.description}</div>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", marginBottom: "8px", fontWeight: "bold", color: "#555" }}>Payload (JSON)</label>
              <textarea
                value={payload}
                onChange={(e) => setPayload(e.target.value)}
                rows={8}
                style={{
                  width: "100%",
                  padding: "12px",
                  fontFamily: "monospace",
                  fontSize: "13px",
                  borderRadius: "8px",
                  border: "1px solid #ddd",
                  resize: "vertical"
                }}
              />
            </div>

            <button
              onClick={executeWorkflow}
              disabled={loading}
              style={{
                width: "100%",
                padding: "14px",
                background: loading ? "#94a3b8" : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                fontSize: "16px",
                fontWeight: "bold",
                cursor: loading ? "not-allowed" : "pointer",
                transition: "transform 0.2s"
              }}
            >
              {loading ? "⏳ Выполнение..." : "▶ Выполнить"}
            </button>
          </div>

          {/* Right Panel - Result */}
          <div style={{ background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
            <h2 style={{ marginTop: 0, marginBottom: "20px", color: "#333" }}>📄 Результат</h2>
            {result ? (
              <pre style={{
                background: "#f8f9fa",
                padding: "16px",
                borderRadius: "8px",
                overflow: "auto",
                maxHeight: "400px",
                fontSize: "13px",
                fontFamily: "monospace"
              }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            ) : (
              <div style={{
                textAlign: "center",
                padding: "60px 20px",
                color: "#999",
                background: "#f8f9fa",
                borderRadius: "8px"
              }}>
                Выполните workflow, чтобы увидеть результат
              </div>
            )}
          </div>
        </div>

        {/* Quick Examples */}
        <div style={{ background: "white", borderRadius: "16px", padding: "24px", marginBottom: "24px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
          <h2 style={{ marginTop: 0, marginBottom: "16px", color: "#333" }}>📋 Быстрые примеры</h2>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <button
              onClick={() => setExample("calculator", '{"expression": "100 / 4 * 3"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              🧮 100 / 4 * 3
            </button>
            <button
              onClick={() => setExample("translator", '{"text": "Hello world!", "target": "ru"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              🌐 Hello world → русский
            </button>
            <button
              onClick={() => setExample("translator", '{"text": "Привет мир!", "target": "en"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              🌐 Привет мир → English
            </button>
            <button
              onClick={() => setExample("calculator", '{"expression": "2^10"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              🧮 2^10
            </button>
            <button
              onClick={() => setExample("ai_chat", '{"prompt": "Что такое микросервисы?"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              🤖 Что такое микросервисы?
            </button>
            <button
              onClick={() => setExample("ai_chat", '{"prompt": "Напиши Python функцию для сортировки списка"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              🤖 Функция сортировки
            </button>
            <button
              onClick={() => setExample("code_review", '{"code": "for i in range(10):\\n    print(i)"}')}
              style={{ padding: "8px 16px", background: "#f0f0f0", border: "none", borderRadius: "8px", cursor: "pointer" }}
            >
              📝 Review Python код
            </button>
          </div>
        </div>

        {/* Recent Runs */}
        {runs.length > 0 && (
          <div style={{ background: "white", borderRadius: "16px", padding: "24px", boxShadow: "0 4px 6px rgba(0,0,0,0.1)" }}>
            <h2 style={{ marginTop: 0, marginBottom: "16px", color: "#333" }}>📜 Последние запуски</h2>
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid #e0e0e0" }}>
                    <th style={{ textAlign: "left", padding: "12px" }}>ID</th>
                    <th style={{ textAlign: "left", padding: "12px" }}>Workflow</th>
                    <th style={{ textAlign: "left", padding: "12px" }}>Статус</th>
                    <th style={{ textAlign: "left", padding: "12px" }}>Время</th>
                  </tr>
                </thead>
                <tbody>
                  {runs.map((run: any) => (
                    <tr key={run.id} style={{ borderBottom: "1px solid #f0f0f0" }}>
                      <td style={{ padding: "12px", fontFamily: "monospace" }}>{run.id?.slice(0, 8)}...</td>
                      <td style={{ padding: "12px" }}>{run.workflow_name}</td>
                      <td style={{ padding: "12px" }}>
                        <span style={{
                          padding: "4px 12px",
                          borderRadius: "20px",
                          fontSize: "12px",
                          fontWeight: "bold",
                          background: run.status === "SUCCESS" ? "#d4edda" : "#f8d7da",
                          color: run.status === "SUCCESS" ? "#155724" : "#721c24"
                        }}>
                          {run.status}
                        </span>
                      </td>
                      <td style={{ padding: "12px" }}>{new Date(run.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}