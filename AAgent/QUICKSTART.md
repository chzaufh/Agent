# 🚀 AI圆桌讨论系统 - 快速启动指南

## 📦 已创建的项目文件清单

### ✅ 根目录文件
- `package.json` - 项目依赖和脚本配置
- `.env.example` - 环境变量模板
- `.gitignore` - Git忽略规则
- `README.md` - 项目说明文档

### ✅ 后端文件 (backend/)
- `index.js` - Express服务器主入口
- `db/schema.sql` - 数据库表结构（4张表 + 索引 + 触发器）
- `db/init.js` - 数据库初始化脚本
- `db/database.js` - 数据库连接模块
- `config/experts.json` - 8位预设AI专家模板

### ✅ 前端文件 (frontend/)
- `index.html` - 首页（讨论列表）
- `discussion.html` - 讨论室页面
- `css/style.css` - 自定义样式（深色主题）
- `js/api.js` - API调用封装
- `js/home.js` - 首页逻辑
- `js/discussion.js` - 讨论室逻辑

---

## 🎯 下一步：初始化项目

### 步骤1：安装依赖

在项目根目录执行：

```bash
npm install
```

这将安装以下依赖：
- express (Web服务器)
- better-sqlite3 (SQLite数据库)
- cors (跨域支持)
- dotenv (环境变量管理)
- @anthropic-ai/sdk (Claude API)

### 步骤2：配置环境变量

复制环境变量模板并编辑：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

编辑 `.env` 文件，填入您的Claude API密钥：

```env
PORT=3000
NODE_ENV=development
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx  # ⚠️ 请替换为您的实际API密钥
MAX_ROUNDS=3
MAX_PARTICIPANTS=5
MIN_PARTICIPANTS=3
```

> 💡 获取API密钥：访问 https://console.anthropic.com/

### 步骤3：初始化数据库

```bash
npm run init-db
```

执行成功后会看到：

```
📦 开始初始化数据库...
✅ 数据库表结构创建成功！

📊 已创建的表:
  - discussions
  - participants
  - messages
  - consensus

📇 已创建的索引:
  - idx_discussions_status
  - idx_discussions_created_at
  - idx_participants_discussion
  - idx_messages_discussion_round
  - idx_messages_participant
  - idx_consensus_discussion

⚡ 已创建的触发器:
  - update_discussion_timestamp
  - update_discussion_on_message
  - update_discussion_on_consensus

✨ 数据库初始化完成！
```

### 步骤4：启动服务器

```bash
# 开发模式（推荐）
npm run dev

# 或生产模式
npm start
```

看到以下输出表示启动成功：

```
==================================================
🚀 AI圆桌讨论系统已启动
==================================================
📍 服务地址: http://localhost:3000
🌍 环境: development
📊 API文档: http://localhost:3000/api/health
==================================================
✅ 数据库连接成功
```

### 步骤5：访问应用

在浏览器中打开：

```
http://localhost:3000
```

---

## 📝 当前项目状态

### ✅ 已完成（SDD阶段）

1. **PRD文档** - 完整的产品需求文档（包含用户故事、数据模型、API设计）
2. **系统设计文档** - OpenAPI风格的接口定义、Expert Persona生成逻辑
3. **项目初始化** - 完整的目录结构和基础文件
4. **数据库设计** - 4张表 + 索引 + 触发器的完整Schema
5. **前端框架** - 首页和讨论室的HTML/CSS/JS（静态版本）
6. **配置文件** - 8位预设专家模板、环境变量模板

### 🚧 待实现（DD + TDD阶段）

#### 后端核心功能
- [ ] `backend/routes/discussions.js` - 讨论相关API路由
- [ ] `backend/routes/experts.js` - 专家模板API路由
- [ ] `backend/services/aiService.js` - Claude API调用服务
- [ ] `backend/services/discussionService.js` - 讨论编排服务
- [ ] `backend/services/sseService.js` - SSE事件推送服务
- [ ] `backend/models/Discussion.js` - 讨论领域模型
- [ ] `backend/models/Participant.js` - 参与者领域模型

#### 测试文件
- [ ] `tests/unit/aiService.test.js` - AI服务单元测试
- [ ] `tests/integration/api.test.js` - API集成测试

---

## 🔧 常见问题排查

### 问题1：`npm install` 失败

**原因**：better-sqlite3 需要编译本地模块

**解决方案**：
```bash
# Windows需要安装构建工具
npm install --global windows-build-tools

# 或使用预编译版本
npm install better-sqlite3 --build-from-source=false
```

### 问题2：数据库初始化失败

**原因**：文件权限或路径问题

**解决方案**：
```bash
# 确保在项目根目录执行
cd d:\AAgent
npm run init-db
```

### 问题3：Claude API调用失败

**原因**：API密钥未配置或无效

**解决方案**：
1. 检查 `.env` 文件中的 `ANTHROPIC_API_KEY`
2. 确认API密钥有效且有足够额度
3. 检查网络连接

### 问题4：前端页面无法访问

**原因**：服务器未启动或端口被占用

**解决方案**：
```bash
# 检查3000端口是否被占用
netstat -ano | findstr :3000

# 或修改 .env 中的 PORT 配置
PORT=8080
```

---

## 📚 下一步开发计划

### DD阶段（Domain Design）

1. **创建领域模型** (1-2天)
   - Discussion聚合根
   - Participant实体
   - Message实体
   - Consensus值对象

2. **实现业务服务** (2-3天)
   - AI调用服务（Claude API集成）
   - 讨论编排服务（多轮对话逻辑）
   - SSE推送服务（实时事件流）

3. **实现API路由** (1-2天)
   - REST接口实现
   - SSE端点实现
   - 错误处理和验证

### TDD阶段（Test-Driven Development）

1. **单元测试** (1-2天)
   - AI服务测试
   - 讨论编排逻辑测试
   - 数据库操作测试

2. **集成测试** (1天)
   - API端到端测试
   - SSE事件流测试

---

## 🎉 祝贺！

项目基础框架已完成，所有SDD阶段的文件都已创建完毕。

**准备好进入DD阶段了吗？** 请告知下一步需求，我们将继续实现后端核心功能！

---

**项目位置**: `d:\AAgent`
**文档日期**: 2026-06-26
