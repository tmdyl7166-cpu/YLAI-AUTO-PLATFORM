// Demo module run entry
export async function runDemo(params = {}) {
  try {
    const response = await fetch('/api/demo/run', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(params)
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Demo run failed:', error);
    throw error;
  }
}

export default runDemo;