export type StreamEvent = 
  | { type: 'node_active'; node_id: string; agent_name: string }
  | { type: 'node_complete'; node_id: string; output: string }
  | { type: 'workflow_complete'; final_output: string }
  | { type: 'error'; content: string };

interface RunOptions {
  workflow_id: string;
  user_id: string;
  input: string;
  onEvent: (event: StreamEvent) => void;
}

export async function runWorkflowStream({ workflow_id, user_id, input, onEvent }: RunOptions) {
  const response = await fetch('http://localhost:8000/api/run_stream', { // Connect to stream endpoint
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflow_id, user_id, input })
  });

  if (!response.body) throw new Error("No response body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    
    // Process all complete lines
    buffer = lines.pop() || ''; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.trim()) {
        try {
          const event = JSON.parse(line);
          onEvent(event);
        } catch (e) {
          console.error("Failed to parse event", line, e);
        }
      }
    }
  }
}
