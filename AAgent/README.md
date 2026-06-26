# 🎭 AI圆桌讨论 Web App MVP

> 让多位AI专家为您的问题展开深度圆桌讨论，生成高质量共识

## 📋 项目简介

这是一个基于 **SDD + DDD + TDD** 工程化流程开发的AI圆桌讨论系统。用户可以创建讨论主题，选择3-5位AI专家（基于Claude API），观看他们实时进行多轮讨论，最终生成共识摘要。

### 核心特性

- 🤖 **多AI专家协作**：支持3-5位不同角色的AI专家参与讨论
- 📡 **实时流式显示**：使用SSE技术实时推送讨论内容
- 🎯 **自动生成共识**：讨论结束后自动提炼关键要点
- 🌙 **沉浸式深色UI**：圆桌风格的现代化界面设计
- 💾 **本地持久化**：使用SQLite存储所有讨论记录

## 🛠️ 技术栈

### 前端
- **纯HTML + CSS + JavaScript**（无框架依赖）
- **Tailwind CSS**（CDN方式引入）
- **EventSource API**（SSE客户端）

### 后端
- **Node.js + Express**
- **better-sqlite3**（SQLite数据库）
- **SSE**（Server-Sent Events）
- **Anthropic Claude API**

## 📦 项目结构

```
ai-roundtable/
├── backend/                    # 后端服务
│   ├── index.js               # Express服务器入口
│   ├── db/                    # 数据库相关
│   │   ├── schema.sql         # 数据库表结构
│   │   ├── init.js            # 数据库初始化脚本
│   │   └── database.js        # 数据库连接模块
│   ├── routes/                # API路由（待实现）
│   ├── services/              # 业务逻辑层（待实现）
│   ├── models/                # 数据模型（待实现）
│   └── config/                # 配置文件
│       └── experts.json       # 预设专家模板
│
├── frontend/                   # 前端静态文件
│   ├── index.html             # 首页（讨论列表）
│   ├── discussion.html        # 讨论室页面
│   ├── css/
│   │   └── style.css          # 自定义样式
│   └── js/
│       ├── api.js             # API调用封装
│       ├── home.js            # 首页逻辑
│       └── discussion.js      # 讨论室逻辑
│
├── package.json               # 项目依赖配置
├── .env.example               # 环境变量模板
├── .gitignore                 # Git忽略配置
└── README.md                  # 项目说明文档
```

## 🚀 快速开始

### 1. 环境要求

- **Node.js** >= 18.0.0
- **npm** 或 **yarn**
- **Claude API Key**（从 [Anthropic](https://console.anthropic.com/) 获取）

### 2. 安装依赖

```bash
npm install
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并填入您的配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
PORT=3000
NODE_ENV=development
ANTHROPIC_API_KEY=your_actual_api_key_here
MAX_ROUNDS=3
```

### 4. 初始化数据库

```bash
npm run init-db
```

执行成功后会在项目根目录生成 `database.sqlite` 文件。

### 5. 启动服务器

```bash
# 开发模式（支持热重载）
npm run dev

# 生产模式
npm start
```

### 6. 访问应用

打开浏览器访问：[http://localhost:3000](http://localhost:3000)

## 📖 使用指南

### 创建讨论

1. 点击首页右上角的 **"➕ 创建新讨论"** 按钮
2. 输入讨论主题（必填）和详细描述（可选）
3. 选择3-5位AI专家参与讨论
4. 点击 **"创建并启动讨论"**

### 观看讨论

- 讨论创建后会自动跳转到讨论室页面
- AI专家会依次发言，共进行3轮讨论
- 实时显示每位专家的观点和见解
- 讨论结束后自动生成共识摘要

### 浏览历史

- 首页展示所有历史讨论
- 支持按状态筛选（待启动/进行中/已完成）
- 点击卡片查看讨论详情和回放

## 🎨 预设专家角色

系统预设了8位不同领域的AI专家：

| 专家 | 角色 | 专业领域 |
|-----|------|---------|
| 张伟 | 技术架构师 | 分布式系统、微服务架构 |
| 李娜 | 产品经理 | 用户需求、产品规划 |
| 王芳 | UX设计师 | 交互设计、用户体验 |
| 陈强 | 数据科学家 | 数据分析、机器学习 |
| 刘敏 | 安全专家 | 网络安全、数据保护 |
| 周杰 | 商业分析师 | 市场分析、ROI评估 |
| 赵丽 | 前端专家 | Web性能、工程化 |
| 孙涛 | DevOps工程师 | CI/CD、自动化运维 |

## 🗄️ 数据库设计

### 核心表结构

- **discussions**: 讨论主表（主题、状态、时间戳）
- **participants**: 参与专家表（名称、角色、Persona提示词）
- **messages**: 消息表（发言内容、轮次）
- **consensus**: 共识表（摘要、关键要点）

详细Schema请查看 `backend/db/schema.sql`

## 🔌 API接口

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/discussions` | 获取讨论列表 |
| GET | `/api/discussions/:id` | 获取讨论详情 |
| POST | `/api/discussions` | 创建新讨论 |
| POST | `/api/discussions/:id/start` | 启动讨论 |
| GET | `/api/expert-templates` | 获取专家模板 |

### SSE接口

| 路径 | 事件类型 | 说明 |
|------|---------|------|
| `/api/discussions/:id/events` | `message` | 专家发言 |
| | `consensus` | 生成共识 |
| | `complete` | 讨论完成 |

## 🧪 测试（待实现）

```bash
npm test
```

## 📝 开发计划

### 已完成 ✅

- [x] SDD阶段：PRD文档、数据模型设计
- [x] 项目初始化：目录结构、依赖配置
- [x] 数据库设计：Schema + 初始化脚本
- [x] 前端页面：首页 + 讨论室（静态）
- [x] 前端逻辑：API封装、UI交互

### 进行中 🚧

- [ ] DD阶段：后端API实现
- [ ] AI服务集成：Claude API调用
- [ ] SSE实时推送：讨论流程编排
- [ ] TDD阶段：单元测试 + 集成测试

### 待实现 📋

- [ ] 讨论暂停/继续功能
- [ ] 导出讨论记录（Markdown/PDF）
- [ ] 自定义专家角色
- [ ] 讨论主题推荐
- [ ] 多语言支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 开源协议

MIT License

## 👤 作者

AI开发实习生远程作业项目

---

⭐ 如果这个项目对您有帮助，请给它一个Star！
