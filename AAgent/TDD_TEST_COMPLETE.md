# 🧪 TDD 测试用例完整文档

## 📊 测试概览

**测试阶段**: TDD (Test-Driven Development)  
**测试框架**: Node.js 内置 `assert` 模块  
**测试文件数**: 3个核心测试套件  
**总测试用例数**: 26个  
**创建时间**: 2026-06-26

---

## 📂 测试文件结构

```
tests/
├── runTests.js                        # 测试运行器
└── unit/                              # 单元测试
    ├── expertPersona.test.js          # 专家Persona生成测试（6个用例）
    ├── discussionFlow.test.js         # 讨论流程控制测试（8个用例）
    └── consensusExtraction.test.js    # 共识分歧提取测试（10个用例）
```

---

## 🎯 测试套件 1: 专家Persona生成

**文件**: `tests/unit/expertPersona.test.js`  
**测试函数**: `generateExpertPersonas()`, `buildSystemPrompt()`  
**测试用例数**: 6个

### 测试用例清单

| # | 测试名称 | 测试目标 | 预期结果 |
|---|---------|---------|---------|
| 1 | `test_generateExpertPersonas_count` | 生成指定数量的专家 | 返回数组长度等于指定数量 |
| 2 | `test_expertPersona_requiredFields` | 专家对象包含必需字段 | 包含name/role/expertise/systemPrompt等字段 |
| 3 | `test_generateExpertPersonas_consistency` | 相同主题生成一致配置 | 相同输入产生相同角色组合 |
| 4 | `test_expertPersonas_noDuplicateRoles` | 专家角色唯一性 | 同一讨论中角色不重复 |
| 5 | `test_buildSystemPrompt_structure` | SystemPrompt结构正确 | 包含专家信息、主题、轮次等 |
| 6 | `test_participantCount_boundary` | 边界条件验证 | 3-5人范围外抛出错误 |

### 核心测试代码示例

```javascript
function test_generateExpertPersonas_count() {
    const topic = '如何设计高并发系统';
    const participantCount = 3;
    const personas = generateExpertPersonas(topic, participantCount);
    
    assert.strictEqual(personas.length, 3, '应该生成3个专家Persona');
    assert.ok(Array.isArray(personas), '返回值应该是数组');
}
```

### 待实现的函数签名

```javascript
/**
 * 生成专家Persona列表
 * @param {string} topic - 讨论主题
 * @param {number} participantCount - 参与人数（3-5人）
 * @returns {Array<Persona>} 专家Persona数组
 */
function generateExpertPersonas(topic, participantCount) {
    // 待实现
}

/**
 * 构建专家的SystemPrompt
 * @param {Object} participant - 专家信息
 * @param {Object} discussionContext - 讨论上下文
 * @param {Array} previousMessages - 之前的消息
 * @param {number} currentRound - 当前轮次
 * @returns {string} 完整的SystemPrompt
 */
function buildSystemPrompt(participant, discussionContext, previousMessages, currentRound) {
    // 待实现
}
```

---

## 🎯 测试套件 2: 讨论流程控制

**文件**: `tests/unit/discussionFlow.test.js`  
**测试类**: `DiscussionOrchestrator`  
**测试用例数**: 8个

### 测试用例清单

| # | 测试名称 | 测试目标 | 预期结果 |
|---|---------|---------|---------|
| 1 | `test_discussion_rounds` | 讨论按轮次进行 | 规划指定轮数，每轮包含所有专家 |
| 2 | `test_allParticipants_speak` | 每轮所有专家发言 | 每轮speakers列表包含所有参与者 |
| 3 | `test_speaking_order_randomized` | 发言顺序随机化 | 不同轮次发言顺序有变化 |
| 4 | `test_discussion_state_transition` | 状态转换正确 | pending → running → completed |
| 5 | `test_getNextSpeaker` | 获取下一位发言者 | 返回正确的专家对象 |
| 6 | `test_shouldEndDiscussion` | 判断讨论是否结束 | 根据轮次和消息数正确判断 |
| 7 | `test_pauseAndResume` | 暂停和恢复功能 | 状态正确切换（paused ↔ running） |
| 8 | `test_recordMessage_updateProgress` | 记录消息更新进度 | 消息计数和轮次正确更新 |

### 核心测试代码示例

```javascript
function test_discussion_rounds() {
    const maxRounds = 3;
    const participants = [
        { id: 1, name: '张伟', role: '技术架构师' },
        { id: 2, name: '李娜', role: '产品经理' },
        { id: 3, name: '王芳', role: 'UX设计师' }
    ];
    
    const orchestrator = new DiscussionOrchestrator(participants, maxRounds);
    const rounds = orchestrator.planRounds();
    
    assert.strictEqual(rounds.length, maxRounds, '应该规划3轮讨论');
    assert.strictEqual(rounds[0].speakers.length, participants.length, '第一轮所有专家都应发言');
}
```

### 待实现的类结构

```javascript
class DiscussionOrchestrator {
    constructor(participants, maxRounds) {}
    
    planRounds() {}                    // 规划讨论轮次
    start() {}                         // 启动讨论
    pause() {}                         // 暂停讨论
    resume() {}                        // 恢复讨论
    complete() {}                      // 完成讨论
    getNextSpeaker() {}                // 获取下一位发言者
    shouldEnd() {}                     // 判断是否应结束
    recordMessage(message) {}          // 记录消息
    getProgress() {}                   // 获取进度信息
    getState() {}                      // 获取当前状态
}
```

---

## 🎯 测试套件 3: 共识与分歧提取

**文件**: `tests/unit/consensusExtraction.test.js`  
**测试函数**: `extractConsensus()`, `detectDivergence()`, `analyzeAgreement()`等  
**测试用例数**: 10个

### 测试用例清单

| # | 测试名称 | 测试目标 | 预期结果 |
|---|---------|---------|---------|
| 1 | `test_extractConsensus_simpleKeywords` | 提取共识关键词 | 识别高频出现的核心词汇 |
| 2 | `test_detectDivergence_obvious` | 检测明显分歧 | 识别对立观点和分歧主题 |
| 3 | `test_analyzeAgreement_level` | 计算一致性程度 | 返回0-1之间的一致性分数 |
| 4 | `test_identifyAgreementKeywords` | 识别同意/反对关键词 | 正确分类"同意"/"反对"短语 |
| 5 | `test_generateConsensusSummary` | 生成共识摘要 | 输出摘要文本和关键要点列表 |
| 6 | `test_extractKeyPoints_deduplicate` | 提取并去重要点 | 3-5个不重复的关键要点 |
| 7 | `test_analyzeOpinionEvolution` | 分析意见演变 | 检测意见是否趋向收敛 |
| 8 | `test_handleEmptyOrInvalidInput` | 处理异常输入 | 空数组/null不会崩溃 |
| 9 | `test_chineseKeywordExtraction` | 中文关键词提取 | 正确提取中文术语和概念 |
| 10 | `test_consensusConfidenceScore` | 共识置信度评分 | 返回0-1之间的置信度分数 |

### 核心测试代码示例

```javascript
function test_extractConsensus_simpleKeywords() {
    const messages = [
        { participant: { name: '张伟' }, content: '我认为应该采用微服务架构' },
        { participant: { name: '李娜' }, content: '我同意，微服务架构确实是个好方案' },
        { participant: { name: '王芳' }, content: '微服务架构可以提升系统的可维护性' }
    ];
    
    const consensus = extractConsensus(messages);
    
    assert.ok(consensus.keywords.includes('微服务架构'), '应该识别出共识关键词');
    assert.ok(consensus.agreementLevel >= 0.8, '一致性程度应该较高（>=80%）');
}
```

### 待实现的函数签名

```javascript
/**
 * 从消息中提取共识
 * @param {Array<Message>} messages - 消息列表
 * @returns {Object} { keywords: string[], agreementLevel: number }
 */
function extractConsensus(messages) {}

/**
 * 检测分歧
 * @param {Array<Message>} messages - 消息列表
 * @returns {Object} { hasDivergence: boolean, topics: string[] }
 */
function detectDivergence(messages) {}

/**
 * 分析意见一致性
 * @param {Array<Message>} messages - 消息列表
 * @returns {Object} { level: number, majorityOpinion: string, supportCount: number }
 */
function analyzeAgreement(messages) {}

/**
 * 生成共识摘要
 * @param {Array<Message>} messages - 消息列表
 * @returns {Object} { summary: string, keyPoints: string[] }
 */
function generateConsensusSummary(messages) {}

/**
 * 提取关键要点
 * @param {Array<Message>} messages - 消息列表
 * @returns {Array<string>} 关键要点列表（3-5个）
 */
function extractKeyPoints(messages) {}

/**
 * 计算共识置信度
 * @param {Array<Message>} messages - 消息列表
 * @returns {number} 置信度分数（0-1）
 */
function calculateConfidenceScore(messages) {}
```

---

## 🔧 测试运行指南

### 1. 安装依赖

```bash
# 无需额外安装，使用Node.js内置assert模块
npm install  # 安装项目依赖即可
```

### 2. 运行测试

#### 方式1：运行测试运行器
```bash
node tests/runTests.js
```

#### 方式2：运行单个测试文件
```bash
node tests/unit/expertPersona.test.js
node tests/unit/discussionFlow.test.js
node tests/unit/consensusExtraction.test.js
```

#### 方式3：使用npm脚本
```bash
# 在package.json中添加
"scripts": {
  "test": "node tests/runTests.js",
  "test:persona": "node tests/unit/expertPersona.test.js",
  "test:flow": "node tests/unit/discussionFlow.test.js",
  "test:consensus": "node tests/unit/consensusExtraction.test.js"
}

# 然后运行
npm test
npm run test:persona
```

### 3. 当前状态

⚠️ **注意**: 测试文件中的断言目前已注释，因为实现代码尚未完成。

**开发流程**:
1. ✅ 编写测试用例（已完成）
2. ⏳ 实现功能代码（下一步）
3. ⏳ 取消注释断言
4. ⏳ 运行测试确保通过
5. ⏳ 重构优化代码

---

## 📈 测试覆盖目标

### 核心功能模块

| 模块 | 测试用例数 | 覆盖率目标 |
|------|-----------|-----------|
| 专家Persona生成 | 6个 | 90%+ |
| 讨论流程控制 | 8个 | 85%+ |
| 共识分歧提取 | 10个 | 80%+ |
| **总计** | **24个** | **85%+** |

---

## 🎯 测试设计原则

### 1. **FIRST原则**
- **Fast** (快速): 单个测试 < 100ms
- **Independent** (独立): 测试间无依赖
- **Repeatable** (可重复): 结果一致
- **Self-validating** (自验证): 通过/失败明确
- **Timely** (及时): 代码前编写

### 2. **测试金字塔**
```
       /\
      /  \  E2E测试（少量）
     /----\
    / 集成 \ 集成测试（适量）
   /--------\
  / 单元测试 \ 单元测试（大量）✅ 当前阶段
 /------------\
```

### 3. **边界值测试**
- 最小值（3位专家）
- 最大值（5位专家）
- 边界外（2位、6位应报错）
- 空值/null处理

### 4. **等价类划分**
- 有效输入类
- 无效输入类
- 异常情况类

---

## 🛠️ 下一步：实现代码

### 优先级排序

#### 🔥 高优先级（立即实现）
1. **专家Persona生成**
   - 文件: `backend/services/expertPersonaService.js`
   - 函数: `generateExpertPersonas()`, `buildSystemPrompt()`
   
2. **讨论流程控制**
   - 文件: `backend/services/discussionOrchestrator.js`
   - 类: `DiscussionOrchestrator`

#### 🟡 中优先级（核心功能）
3. **共识分歧提取**
   - 文件: `backend/services/consensusService.js`
   - 函数: `extractConsensus()`, `detectDivergence()`, `analyzeAgreement()`

#### 🟢 低优先级（优化增强）
4. 性能优化
5. 错误处理完善
6. 日志记录

---

## 📊 测试统计

### 当前状态

| 指标 | 数值 |
|------|------|
| 测试文件数 | 3个 |
| 测试用例总数 | 24个 |
| 代码行数 | ~800行 |
| 断言数量 | ~60个（已注释） |
| 覆盖的函数 | 15个 |
| 覆盖的类 | 1个 |

### 预期输出示例

```bash
========================================
🧪 测试套件：专家Persona生成
========================================

📝 测试1：生成指定数量的专家Persona
   ✅ 通过：生成的专家数量正确

📝 测试2：专家Persona包含必需字段
   ✅ 通过：所有必需字段存在且非空

📝 测试3：相同主题生成一致的专家配置
   ✅ 通过：相同主题生成一致的专家配置

...

========================================
✅ 所有测试通过！
========================================
```

---

## 🎉 总结

### ✅ 已完成
1. ✅ 创建测试目录结构
2. ✅ 编写24个测试用例
3. ✅ 定义15个待实现函数/方法
4. ✅ 建立TDD开发流程
5. ✅ 编写测试文档

### 🎯 测试覆盖的核心能力
- ✅ 专家角色自动匹配
- ✅ SystemPrompt动态生成
- ✅ 讨论轮次规划
- ✅ 状态机管理
- ✅ 共识关键词提取
- ✅ 分歧检测
- ✅ 意见一致性分析

### 📝 下一步行动
1. **立即开始**: 实现 `expertPersonaService.js`
2. **跟随测试**: 每实现一个函数，取消注释对应测试
3. **红绿重构**: 测试失败(红) → 实现代码(绿) → 重构优化
4. **持续集成**: 每次提交前运行所有测试

---

**文件位置**: `d:\AAgent\tests/`  
**文档生成时间**: 2026-06-26  
**TDD阶段**: 测试用例编写完成 ✅  
**下一阶段**: 实现代码以通过测试 ⏳

🎉 **TDD测试用例已全部完成！现在可以开始实现代码，让测试逐一通过。**
