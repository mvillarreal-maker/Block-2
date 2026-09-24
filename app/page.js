'use client';

import { useState } from 'react';

export default function Home() {
  const [topic, setTopic] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!topic.trim()) return;

    setLoading(true);
    setResponse('');

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [
            {
              role: 'user',
              content: `Explain the topic "${topic}" in exactly 3 bullet points. Keep each bullet brief and informative.`,
            },
          ],
        }),
      });
      const data = await res.json();
      setResponse(data.content || 'No response received.');
    } catch (err) {
      setResponse('Error: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 700, margin: '4rem auto', padding: '0 1rem', fontFamily: 'sans-serif' }}>
      <h1>Course Companion</h1>
      <p>Type a topic and get a 3-point explanation.</p>

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: '0.75rem', marginTop: '1.5rem' }}>
        <label htmlFor="topic" style={{ fontWeight: 600 }}>
          Topic
        </label>
        <input
          id="topic"
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. photosynthesis"
          style={{ padding: '0.75rem', fontSize: '1rem' }}
        />
        <button type="submit" disabled={loading} style={{ padding: '0.75rem 1rem', fontSize: '1rem' }}>
          {loading ? 'Thinking...' : 'Explain'}
        </button>
      </form>

      {response && (
        <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#f5f5f5', borderRadius: '8px', whiteSpace: 'pre-wrap' }}>
          {response}
        </div>
      )}
    </main>
  );
}
