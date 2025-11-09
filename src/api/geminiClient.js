export async function invokeLLM({ prompt }) {
  const res = await fetch("https://mdc-career-path-planner.onrender.com/api/invoke_llm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });

  if (!res.ok) {
    console.error("Error invoking LLM:", res.status, await res.text());
    throw new Error("Failed to get AI response");
  }

  const data = await res.json();
  console.log("AI response:", data);
  return data;
}
