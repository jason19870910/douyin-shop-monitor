import '@ant-design/icons';
const fs = await import('fs');
const path = await import('path');
const iconsPath = path.dirname(fs.realpathSync('check_icons.cjs')) + '/node_modules/@ant-design/icons';
console.log('Using ES module approach');