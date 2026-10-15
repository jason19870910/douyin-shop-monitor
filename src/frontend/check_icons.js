const icons = require('@ant-design/icons');
const refreshIcons = Object.keys(icons).filter(k => k.includes('Refresh') || k.includes('refresh') || k.includes('Rest'));
console.log('Refresh-related icons:', refreshIcons);
console.log('All icon keys count:', Object.keys(icons).length);