import { defineConfig } from 'vitepress'
import { fileURLToPath } from 'url'
import { dirname, resolve } from 'path'

const __dirname = dirname(fileURLToPath(import.meta.url))

export default defineConfig({
  lang: 'zh-CN',
  title: '抖音电商数据监控平台',
  description: '项目文档中心 - 架构设计、API 规范、运维手册、测试策略、风险管理',

  // 部署基础路径
  base: '/docs/',

  // 最后更新时间
  lastUpdated: true,
  lastUpdatedText: '最后更新',

  // 清单
  cleanUrls: true,

  // 头部元素
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['meta', { name: 'theme-color', content: '#1890ff' }],
  ],

  // Markdown 配置
  markdown: {
    lineNumbers: true,
    anchor: { slugify: (s) => s.toLowerCase().replace(/\s+/g, '-') },
    toc: { level: [2, 3] },
    // 代码组
    codeTransformers: [],
    // 数学公式
    math: true,
    // 图表
    mermaid: true,
  },

  // Vue 配置
  vue: {
    template: {
      compilerOptions: {
        isCustomElement: (tag) => tag.startsWith('mermaid'),
      },
    },
  },

  // 主题配置
  themeConfig: {
    // Logo
    logo: '/logo.svg',

    // 站点标题
    siteTitle: '抖音电商数据监控平台',

    // 导航栏
    nav: [
      { text: '首页', link: '/' },
      { text: '项目治理', link: '/governance/PROJECT_CHARTER', activeMatch: '^/governance/' },
      { text: '架构设计', link: '/architecture/ARCHITECTURE', activeMatch: '^/architecture/' },
      { text: 'API 规范', link: '/api/API_SPEC', activeMatch: '^/api/' },
      { text: '运维手册', link: '/operations/RUNBOOK', activeMatch: '^/operations/' },
      { text: '质量测试', link: '/quality/TESTING', activeMatch: '^/quality/' },
      { text: '风险合规', link: '/risk/RISK_REGISTER', activeMatch: '^/risk/' },
      { text: '开发规范', link: '/development/CODING_STANDARDS', activeMatch: '^/development/' },
      { text: '参考资料', link: '/reference/GLOSSARY', activeMatch: '^/reference/' },
      { text: 'ADR', link: '/adr/DECISIONS', activeMatch: '^/adr/' },
      {
        text: '更多',
        items: [
          { text: '术语表', link: '/reference/GLOSSARY' },
          { text: '常见问题', link: '/reference/FAQ' },
          { text: '故障排查', link: '/reference/TROUBLESHOOTING' },
        ],
      },
    ],

    // 侧边栏
    sidebar: {
      '/governance/': [
        { text: '项目治理', items: [
          { text: '项目章程与沟通计划', link: '/governance/PROJECT_CHARTER' },
        ]},
      ],
      '/requirements/': [
        { text: '需求规格', items: [
          { text: '需求规格说明书', link: '/requirements/REQUIREMENTS' },
          { text: '用户故事', link: '/requirements/USER_STORIES' },
          { text: '验收标准', link: '/requirements/ACCEPTANCE_CRITERIA' },
        ]},
      ],
      '/architecture/': [
        { text: '架构设计', items: [
          { text: '系统架构总览', link: '/architecture/ARCHITECTURE' },
          { text: '详细设计文档', link: '/architecture/DESIGN' },
          { text: '前端设计文档', link: '/architecture/FRONTEND_DESIGN' },
        ]},
        { text: '历史归档（旧架构，仅供参考）', items: [
          { text: '数据流设计', link: '/architecture/archive/DATA_FLOW' },
          { text: '安全架构', link: '/architecture/archive/SECURITY_ARCHITECTURE' },
          { text: '部署架构', link: '/architecture/archive/DEPLOYMENT_ARCHITECTURE' },
        ]},
      ],
      '/api/': [
        { text: 'API 规范', items: [
          { text: 'API 规范总览', link: '/api/API_SPEC' },
        ]},
      ],
      '/operations/': [
        { text: '运维手册', items: [
          { text: '运维手册', link: '/operations/RUNBOOK' },
          { text: '安全加固指南', link: '/operations/SECURITY_HARDENING' },
          { text: '故障应急预案', link: '/operations/INCIDENT_RESPONSE' },
          { text: '备份恢复策略', link: '/operations/BACKUP_RECOVERY' },
          { text: '监控告警规范', link: '/operations/MONITORING_ALERTING' },
        ]},
      ],
      '/quality/': [
        { text: '质量测试', items: [
          { text: '测试与质量保障规范', link: '/quality/TESTING' },
        ]},
      ],
      '/risk/': [
        { text: '风险合规', items: [
          { text: '风险登记册与事件管理', link: '/risk/RISK_REGISTER' },
        ]},
      ],
      '/development/': [
        { text: '开发规范', items: [
          { text: '编码规范', link: '/development/CODING_STANDARDS' },
          { text: 'Git 工作流规范', link: '/development/GIT_WORKFLOW' },
          { text: '贡献指南', link: '/development/CONTRIBUTING' },
        ]},
      ],
      '/reference/': [
        { text: '参考资料', items: [
          { text: '术语表', link: '/reference/GLOSSARY' },
          { text: '常见问题', link: '/reference/FAQ' },
          { text: '故障排查指南', link: '/reference/TROUBLESHOOTING' },
          { text: '权限矩阵', link: '/reference/PERMISSION' },
        ]},
      ],
      '/adr/': [
        { text: '架构决策记录', items: [
          { text: 'ADR 列表', link: '/adr/DECISIONS' },
        ]},
      ],
    },

    // 社交链接
    socialLinks: [
      { icon: 'github', link: 'https://github.com/your-org/douyin-monitor' },
    ],

    // 页脚
    footer: {
      message: '基于 MIT 许可发布',
      copyright: 'Copyright © 2026 抖音电商数据监控平台项目组',
    },

    // 搜索
    search: {
      provider: 'local',
      options: {
        detailedView: true,
      },
    },

    // 编辑链接
    editLink: {
      pattern: 'https://github.com/your-org/douyin-monitor/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页',
    },

    // 碳广告
    carbonAds: false,

    // 大纲
    outline: {
      level: [2, 3],
      label: '页面大纲',
    },

    // 上一页/下一页
    docFooter: {
      prev: '上一页',
      next: '下一页',
    },

    // 返回顶部
    returnToTopLabel: '返回顶部',

    // 深色模式
    darkModeSwitchLabel: '切换深色模式',
    lightModeSwitchLabel: '切换浅色模式',

    // 侧边栏菜单标签
    sidebarMenuLabel: '菜单',
  },

  // Vite 配置
  vite: {
    resolve: {
      alias: {
        '@': resolve(__dirname, '../'),
      },
    },
    server: {
      port: 5173,
      host: true,
    },
  },

  // 忽略模板目录
  srcExclude: ['templates/**', 'scripts/**'],

  // 忽略死链接检查 (外部链接和源码引用)
  ignoreDeadLinks: true,

  // 构建配置
  build: {
    target: 'es2020',
    outDir: '../dist',
    assetsDir: 'assets',
    minify: 'terser',
  },
})