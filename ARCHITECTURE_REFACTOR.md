# 分层架构重构文档

## 重构概述

本次重构将原有的扁平化节点架构重构为三层架构：**工具层 → 能力层 → 编排层**

---

## 架构对比

### 重构前
```
用户请求 → RouterNode → [业务节点] → 结束
```
- 节点直接依赖外部 API（MCP、HTTP 调用）
- 职责混乱：节点既是业务逻辑又是工具调用
- 难以复用和测试

### 重构后
```
┌─────────────────────────────────────────┐
│           编排层 (Orchestration)         │
│  - SkillOrchestrator (技能调度)          │
│  - RoutingStrategy (路由策略)            │
│  - ExecutionPlan (执行计划)             │
├─────────────────────────────────────────┤
│           能力层 (Capability)            │
│  - PlanningSkill (规划技能)             │
│  - BookingSkill (预订技能)              │
│  - InfoSkill (信息技能)                 │
│  - ConversationSkill (对话技能)         │
├─────────────────────────────────────────┤
│            工具层 (Tool)                 │
│  - MCPClientPool (MCP 连接池)            │
│  - APIGateway (API 网关)                 │
│  - BaseTool (工具基类)                  │
└─────────────────────────────────────────┘
```

---

## 新增目录结构

```
src/travel_planner/
├── tools/                    # 工具层（新增）
│   ├── __init__.py
│   ├── base_tool.py          # 工具基类（重试、缓存）
│   ├── mcp_client.py         # MCP 连接管理
│   └── api_gateway.py        # 第三方 API 网关
├── skills/                   # 能力层（新增）
│   ├── __init__.py
│   ├── base_skill.py         # 技能基类
│   ├── planning_skill.py     # 规划技能
│   ├── booking_skill.py      # 预订技能
│   ├── info_skill.py         # 信息技能
│   └── conversation_skill.py # 对话技能
├── orchestration/            # 编排层（新增）
│   ├── __init__.py
│   ├── orchestrator.py       # 技能编排器
│   └── strategy.py           # 路由策略
├── nodes/                    # 节点层（重构）
│   ├── node_factory.py       # 支持工具注入
│   └── turkish_airlines_node.py # 使用 MCP 池
└── main.py                   # 入口（工具层初始化）
```

---

## 核心变更

### 1. 工具层（Tool Layer）

**base_tool.py**
- `BaseTool`: 提供重试、缓存、标准化结果
- `ToolResult`: 统一返回格式
- `ToolConfig`: 可配置超时、重试、缓存

**mcp_client.py**
- `MCPClientPool`: 集中管理 MCP 连接
- `MCPConnection`: 连接配置
- `TurkishAirlinesMCPConfig`: THY 专用配置

**api_gateway.py**
- `APIGateway`: 统一第三方 API 访问
- `AmadeusClient`: 航班搜索
- `OpenWeatherClient`: 天气查询

### 2. 能力层（Capability Layer）

**base_skill.py**
- `BaseSkill`: 技能基类
- `SkillContext`: 执行上下文
- `SkillResult`: 技能执行结果

**planning_skill.py**
- 整合航班、酒店、天气数据
- 生成完整行程规划

**booking_skill.py**
- 预留预订接口
- 可扩展真实 API 集成

**info_skill.py**
- 天气、签证、货币等信息收集

**conversation_skill.py**
- 闲聊和升级处理

### 3. 编排层（Orchestration Layer）

**orchestrator.py**
- `SkillOrchestrator`: 技能调度核心
- `SkillRegistry`: 技能注册表
- `ExecutionPlan`: 执行计划定义

**strategy.py**
- `RoutingStrategy`: 路由策略基类
- `IntentBasedRoutingStrategy`: 基于意图路由
- `KeywordBasedRoutingStrategy`: 基于关键词路由
- `PriorityRoutingStrategy`: 基于优先级路由
- `RoutingStrategyRegistry`: 策略注册表

---

## 重构的收益

| 维度 | 重构前 | 重构后 |
|------|--------|--------|
| **可测试性** | 节点耦合外部调用，难测试 | 工具可 Mock，技能可独立测试 |
| **可扩展性** | 新增功能需修改节点 | 新增技能/工具，无需修改现有代码 |
| **可复用性** | 逻辑分散在节点中 | 工具和技能可跨节点复用 |
| **配置化** | 硬编码路由逻辑 | 策略模式支持动态路由 |
| ** observability** | 日志分散 | 统一的执行日志和状态追踪 |

---

## 迁移指南

### 现有节点迁移步骤

1. **识别工具依赖**
   - 检查节点直接调用的外部服务
   - 封装为 `BaseTool` 子类

2. **提取业务逻辑**
   - 将节点核心逻辑移至 `BaseSkill` 子类
   - 节点保留适配层

3. **更新 NodeFactory**
   - 注入工具层依赖
   - 支持测试时替换 Mock

### 示例：迁移 TurkishAirlinesNode

**重构前**（节点直接管理 MCP）：
```python
class TurkishAirlinesNode(BaseNode):
    def __init__(self, ...):
        self.mcp_client = None  # 节点自己管理
    
    async def _initialize_mcp_client(self):
        # 直接创建 MultiServerMCPClient
```

**重构后**（使用工具层）：
```python
class TurkishAirlinesNode(BaseNode):
    def __init__(self, ..., mcp_pool: MCPClientPool):
        self._mcp_pool = mcp_pool  # 依赖注入
    
    async def _ensure_agent_initialized(self):
        tools = await self._mcp_pool.get_tools()
```

---

## 下一步计划

### Phase 1: 工具层 ✅
- [x] 创建 `BaseTool` 抽象
- [x] 实现 `MCPClientPool`
- [x] 实现 `APIGateway`
- [x] 重构 `TurkishAirlinesNode`

### Phase 2: 能力层 ✅
- [x] 创建 `BaseSkill` 抽象
- [x] 实现 `PlanningSkill`
- [x] 实现 `BookingSkill`
- [x] 实现 `InfoSkill`
- [x] 实现 `ConversationSkill`

### Phase 3: 编排层 ✅
- [x] 创建 `SkillOrchestrator`
- [x] 创建 `SkillRegistry`
- [x] 实现路由策略模式

### Phase 4: 节点层适配（待完成）
- [ ] 重构 `RouterNode` 使用策略模式
- [ ] 重构 `LLMTripPlannerNode` 使用 `PlanningSkill`
- [ ] 更新 `TravelPlannerGraph` 支持技能编排

---

## 架构演进路线

```
当前：三层架构基础完成
  ↓
短期：节点层适配
  - 节点调用技能而非直接实现逻辑
  - 路由策略可配置化
  ↓
中期：事件驱动增强
  - 添加事件总线
  - 支持并行技能执行
  ↓
长期：插件化架构
  - 第三方可插拔技能
  - 动态技能发现
```

---

## 验证与测试

运行以下命令验证语法：
```bash
cd src/travel_planner
python -m py_compile tools/*.py skills/*.py orchestration/*.py
```

后续工作：
- 添加单元测试（Mock 工具层）
- 添加集成测试（真实 API）
- 性能基准测试
