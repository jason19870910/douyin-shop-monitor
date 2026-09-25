import { marked } from 'marked';

describe('Markdown conversion', () => {
  test('converts simple markdown to HTML', () => {
    const md = '# Hello\n\nThis is **bold** text.';
    const html = marked.parse(md);
    expect(html).toContain('<h1>Hello</h1>');
    expect(html).toContain('<strong>bold</strong>');
  });

  test('handles code blocks', () => {
    const md = '```js\nconst x = 1;\n```';
    const html = marked.parse(md);
    expect(html).toContain('<code');
    expect(html).toContain('const x = 1;');
  });
});