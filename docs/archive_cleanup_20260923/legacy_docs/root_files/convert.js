const fs = require('fs');
const path = require('path');
const { marked } = require('marked');

// 配置 marked
marked.use({ gfm: true, breaks: true });

const files = [
  'PROJECT_TECH_DOCS.md',
  'API_REFERENCE.md',
  'DEPLOYMENT_GUIDE.md',
  'NGINX_WLJKDOC.md'
];

const template = (content) => `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Project Docs</title><style>body{max-width:800px;margin:0 auto;padding:20px;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;line-height:1.6;color:#333}pre{background:#f4f4f4;padding:12px;border-radius:4px;overflow:auto}code{background:#f4f4f4;padding:2px 4px;border-radius:3px}table{border-collapse:collapse;width:100%;margin:20px 0}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f2f2f2}</style></head><body>${content}</body></html>`;

files.forEach(file => {
  const md = fs.readFileSync(file, 'utf8');
  const html = template(marked(md));
  fs.writeFileSync(file.replace('.md', '.html'), html);
  console.log('Converted:', file);
});
