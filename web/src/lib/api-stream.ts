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
  streamUrl: string;
  accessToken: string;
}

export async function runWorkflowStream({ workflow_id, user_id, input, onEvent, streamUrl, accessToken }: RunOptions) {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
  };

  const response = await fetch(streamUrl, {
    method: 'POST',
    headers,
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

    // Process all complete lines (keep incomplete line in buffer)
    buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.startsWith('data:')) {
        // SSE format: data: {json}
        const jsonStr = trimmed.substring(5).trim();
        if (jsonStr) {
          try {
            const event = JSON.parse(jsonStr);
            onEvent(event);
          } catch (e) {
            console.error("Failed to parse SSE event", jsonStr, e);
          }
        }
      }
    }
  }
}
