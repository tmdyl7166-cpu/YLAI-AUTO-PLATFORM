import { generateText } from './services.js';

export async function runNLP(prompt) {
  const text = await generateText(String(prompt || ''));
  return text;
}
