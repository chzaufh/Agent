# TDD测试与实现指南

## 📋 测试套件说明

已创建完整的pytest测试套件，覆盖所有核心功能模块。

### 测试文件列表

1. **test_expert_service.py** - 专家生成服务测试
   - ✅ 专家Persona生成
   - ✅ 基于主题的智能选择
   - ✅ SystemPrompt构建
   - ✅ 参数验证和边界测试

2. **test_ai_service.py** - AI调用服务测试
   - ✅ AI响应生成
   - ✅ 共识提取
   - ✅ 错误处理
   - ✅ JSON解析fallback

3. **test_moderator_service.py** - 主持人服务测试
   - ✅ 讨论流程控制
   - ✅ 消息管理
   - ✅ 状态更新
   - ✅ 共识生成

4. **test_sse_service.py** - SSE推送服务测试
   - ✅ 连接管理
   - ✅ 事件广播
   - ✅ 多客户端支持

5. **test_api_routes.py** - API路由测试
   - ✅ 专家模板API
   - ✅ 讨论管理API
   - ✅ 健康检查API
   - ✅ 参数验证

---

## 🚀 运行测试

### 1. 安装测试依赖

```bash
cd backend
pip install -r requirements-test.txt
```

### 2. 运行所有测试

```bash
# 方法1：使用pytest
pytest tests/ -v

# 方法2：使用测试入口脚本
python tests/run_all_tests.py

# 方法3：运行单个测试文件
pytest tests/test_expert_service.py -v
```

### 3. 生成覆盖率报告

```bash
pytest tests/ --cov=services --cov=routes --cov-report=html
# 报告生成在 htmlcov/index.html
```

---

## 📊 TDD开发流程

### 阶段1：红灯（测试失败）✅

所有测试已编写完成，现在运行测试会看到一些测试通过，一些可能失败。

### 阶段2：绿灯（实现功能）✅

核心功能已实现：
- ✅ `services/expert.py` - 专家生成逻辑
- ✅ `services/ai_service.py` - AI调用（已改为通义千问）
- ✅ `services/moderator.py` - 讨论主持
- ✅ `services/sse_service.py` - 实时推送
- ✅ `routes/experts.py` - 专家模板路由
- ✅ `routes/discussions.py` - 讨论管理路由

### 阶段3：重构（优化代码）

运行测试后，根据测试结果进行优化：

```bash
# 1. 运行测试，查看哪些失败
pytest tests/ -v

# 2. 修复失败的测试

# 3. 重新运行确认通过
pytest tests/ -v

# 4. 检查覆盖率
pytest tests/ --cov --cov-report=term-missing
```

---

## 🔧 当前系统状态

### ✅ 已实现的功能

1. **后端核心服务**
   - ✅ 专家模板管理（8位预设专家）
   - ✅ 智能专家选择（基于主题关键词）
   - ✅ AI对话生成（通义千问）
   - ✅ 讨论流程控制（3轮讨论）
   - ✅ 消息持久化（SQLite）
   - ✅ 共识提取（AI自动生成）
   - ✅ SSE实时推送（多客户端）

2. **API接口**
   - ✅ GET /api/expert-templates - 获取专家模板
   - ✅ GET /api/discussions - 获取讨论列表
   - ✅ POST /api/discussions - 创建讨论
   - ✅ POST /api/discussions/:id/start - 启动讨论
   - ✅ GET /api/discussions/:id/events - SSE事件流

3. **前端功能**
   - ✅ 专家选择界面
   - ✅ 讨论创建表单
   - ✅ 实时消息展示
   - ✅ 打字机效果
   - ✅ 共识展示

### 🔧 需要验证的功能

运行测试来验证所有功能是否正常工作：

```bash
# 进入backend目录
cd backend

# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov httpx

# 运行测试
pytest tests/ -v --tb=short
```

---

## 📝 测试结果预期

运行测试后，你应该看到：

```
test_expert_service.py::TestExpertGeneration::test_generate_expert_personas_valid_input PASSED
test_expert_service.py::TestExpertGeneration::test_generate_expert_personas_min_count PASSED
test_expert_service.py::TestExpertGeneration::test_generate_expert_personas_max_count PASSED
...

test_moderator_service.py::TestModeratorInitialization::test_moderator_creation PASSED
test_moderator_service.py::TestModeratorDiscussionFlow::test_load_discussion PASSED
...

test_api_routes.py::TestExpertTemplatesAPI::test_get_expert_templates PASSED
test_api_routes.py::TestDiscussionsAPI::test_create_discussion PASSED
...

======================== XX passed in X.XXs ========================
```

---

## 🐛 如果测试失败

### 1. 查看详细错误信息

```bash
pytest tests/test_xxx.py -v --tb=long
```

### 2. 运行单个测试

```bash
pytest tests/test_expert_service.py::TestExpertGeneration::test_generate_expert_personas_valid_input -v
```

### 3. 使用调试模式

```python
# 在测试代码中添加
import pdb; pdb.set_trace()
```

---

## 📦 下一步行动

1. **运行测试验证功能**
   ```bash
   cd d:\AAgent\backend
   pip install -r requirements-test.txt
   pytest tests/ -v
   ```

2. **修复任何失败的测试**

3. **检查代码覆盖率**
   ```bash
   pytest tests/ --cov --cov-report=html
   # 打开 htmlcov/index.html 查看报告
   ```

4. **启动服务器测试E2E功能**
   ```bash
   python main.py
   # 浏览器访问 http://localhost:8000
   ```

---

## 🎯 成功标准

- ✅ 所有单元测试通过
- ✅ 代码覆盖率 > 80%
- ✅ API接口正常工作
- ✅ SSE实时推送正常
- ✅ 前端可以创建和查看讨论
- ✅ AI专家正常对话
- ✅ 共识正确生成

---

**现在就运行测试，让我们看看结果！** 🚀
