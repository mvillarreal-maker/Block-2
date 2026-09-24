import OpenAI from 'openai';

// Vercel Hobby tier defaults to a 10s function timeout — too short for a
// classroom-loaded local model, which can occasionally run past that under
// concurrent student traffic. Hobby allows up to 60s with this export.
export const maxDuration = 60;

function getClientAndModel() {
  const baseURL = process.env.OLLAMA_BASE_URL?.replace(/\/$/, '');
  const apiKey = process.env.VCS_API_SECRET;
  const model = process.env.OLLAMA_MODEL || 'qwen3:latest';

  if (!baseURL || !apiKey) {
    throw new Error('Missing OLLAMA_BASE_URL or VCS_API_SECRET environment variables.');
  }

  return {
    client: new OpenAI({ baseURL, apiKey }),
    model,
  };
}

export async function POST(req) {
  try {
    const body = await req.json();
    const messages = Array.isArray(body?.messages) ? body.messages : [];

    if (!messages.length) {
      return Response.json({ error: 'No messages provided.' }, { status: 400 });
    }

    const { client, model } = getClientAndModel();
    const completion = await client.chat.completions.create({
      model,
      messages,
    });

    const message = completion?.choices?.[0]?.message ?? {
      role: 'assistant',
      content: 'No response returned.',
    };

    return Response.json(message);
  } catch (error) {
    console.error('Chat API error:', error);
    return Response.json(
      {
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    );
  }
}
