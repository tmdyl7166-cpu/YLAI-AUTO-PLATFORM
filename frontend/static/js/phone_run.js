// Phone analysis run entry
export async function runPhoneAnalysis(params = {}) {
  try {
    const response = await fetch('/api/phone/analyze', {
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
    console.error('Phone analysis failed:', error);
    throw error;
  }
}

export default runPhoneAnalysis;