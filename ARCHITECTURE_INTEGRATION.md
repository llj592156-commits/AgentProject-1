# 架构整合说明文档

## 整合后的三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                    节点层 (Nodes)                            │
│  LangGraph + 路由策略 + 技能编排                              │
│                                                             │
│  RouterNode ─────────────────────────────────┐              │
│    ├─ 使用 RoutingStrategyRegistry           │              │
│    └─ LLM 判断用户意图                        │              │
│                                              ↓              │
│  LLMTripPlannerNode ─────────────────> SkillOrchestrator   │
│    ├─ 调用 PlanningSkill                    │              │
│    └─ LLM + MCP 工具生成行程                  │              │
│                                                             │
│  TurkishAirlinesNode ─────────────────> MCPClientPool      │
│    ├─ LLM Agent + MCP 工具                   │              │
│    └─ 土耳其航空专属服务                     │              │
├─────────────────────────────────────────────────────────────┤
│                  编排层 (Orchestration)                       │
│  策略模式 + 技能调度                                          │
│                                                             │
│  RoutingStrategyRegistry                                    │
│    ├─ IntentBasedRoutingStrategy (基于意图路由)             │
│    ├─ KeywordBasedRoutingStrategy (基于关键词路由)          │
│    └─ PriorityRoutingStrategy (基于优先级路由)              │
│                                                             │
│  SkillOrchestrator                                          │
│    ├─ PlanningSkill (规划技能)                              │
│    ├─ BookingSkill (预订技能)                               │
│    ├─ InfoSkill (信息技能)                                  │
│    └─ ConversationSkill (对话技能)                          │
├─────────────────────────────────────────────────────────────┤
│                    工具层 (Tools)                            │
│  MCP 连接管理                                                 │
│                                                             │
│  MCPClientPool                                              │
│    ├─ flights MCP Server (航班服务)                         │
│    ├─ hotels MCP Server (酒店服务)                          │
│    └─ weather MCP Server (天气服务)                         │
├─────────────────────────────────────────────────────────────┤
│                MCP 服务器 (外部进程)                            │
│  mock_thy_server.py     - 土耳其航空航班服务                 │
│  hotel_server.py        - 酒店搜索/预订服务                  │
│  weather_server.py      - 天气查询/预报服务                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据流示例：用户请求规划旅行

```
1. 用户输入："帮我规划 6 月 1 日去巴黎的旅行，预算 1000 欧元"
   ↓

2. RouterNode.async_run(state)
   ├─ LLM 分析意图 → RoutingDecision(travel_planner)
   ├─ state.routing_decision = RoutingDecision
   └─ 返回 state
   ↓

3. TravelPlannerGraph._decide_next_route(state)
   ├─ RoutingStrategyRegistry.execute(state)
   ├─ IntentBasedRoutingStrategy 匹配 "travel_planner"
   └─ 返回 "extract_trip_params_node"
   ↓

4. ExtractTripParamsNode.async_run(state)
   ├─ LLM 提取参数 → TravelParams(origin, destination, date_from, date_to, budget)
   ├─ state.travel_params = TravelParams
   └─ 返回 state
   ↓

5. TravelPlannerGraph._should_fix_trip_params(state)
   ├─ 检查 missing_trip_params
   └─ 返回 "llm_trip_planner_node" (参数完整)
   ↓

6. LLMTripPlannerNode.async_run(state)
   ├─ SkillOrchestrator.execute(state, "planning")
   │   └─ PlanningSkill.execute(context)
   │       ├─ context.get_tool("mcp_pool")
   │       ├─ MCPClientPool.get_tools()
   │       │   ├─ flights: search_flights()
   │       │   ├─ hotels: search_hotels()
   │       │   └─ weather: get_weather()
   │       └─ 返回 SkillResult(data={...})
   │
   ├─ _format_planning_response(data)
   └─ state.messages.append(response)
   ↓

7. 返回最终响应给用户
```

---

## 文件修改清单

### 已修改的文件

| 文件 | 修改内容 |
|------|----------|
| `main.py` | 新增路由策略和技能编排器初始化 |
| `node_factory.py` | 新增 routing_registry 和 skill_orchestrator 注入 |
| `router_node.py` | 新增 routing_registry 参数（保留未来扩展） |
| `llm_trip_planner_node.py` | 使用 SkillOrchestrator 调用 PlanningSkill |
| `travel_planner_graph.py` | _decide_next_route 使用 RoutingStrategyRegistry |

### 新增的文件

| 文件 | 作用 |
|------|------|
| `mcp_server/hotel_server.py` | 酒店 MCP 服务 |
| `mcp_server/weather_server.py` | 天气 MCP 服务 |
| `mcp_server/__init__.py` | 包导出 |

---

## 关键集成点

### 1. RouterNode → RoutingStrategyRegistry

```python
# RouterNode 构造函数
def __init__(
    self,
    prompt_templates: PromptTemplates,
    llm_models: LLMs,
    routing_registry: RoutingStrategyRegistry | None = None,  # ← 注入
):
    self._routing_registry = routing_registry

# TravelPlannerGraph 使用
def _decide_next_route(self, state):
    if self._nf._routing_registry:
        return self._nf._routing_registry.execute(state)  # ← 调用策略
```

---

### 2. LLMTripPlannerNode → SkillOrchestrator

```python
# LLMTripPlannerNode 构造函数
def __init__(
    self,
    prompt_templates: PromptTemplates,
    llm_models: LLMs,
    skill_orchestrator: SkillOrchestrator | None = None,  # ← 注入
):
    self._skill_orchestrator = skill_orchestrator

# 使用技能编排器
async def async_run(self, state):
    if self._skill_orchestrator:
        result = await self._skill_orchestrator.execute(
            state=state,
            skill_name="planning",  # ← 调用技能
        )
```

---

### 3. SkillOrchestrator → MCPClientPool

```python
# main.py 初始化
skill_orchestrator = _get_or_create_skill_orchestrator()
skill_orchestrator.register_tool("mcp_pool", mcp_pool)  # ← 注册工具

# PlanningSkill 使用
async def execute(self, context):
    mcp_tools = context.get_tool("mcp_pool")  # ← 获取工具
    tools = await mcp_tools.get_tools()
```

---

## 启动说明

### 1. 启动 MCP 服务器（独立进程）

```bash
# 航班服务
python mock_thy_server.py

# 酒店服务
python src/travel_planner/mcp_server/hotel_server.py

# 天气服务
python src/travel_planner/mcp_server/weather_server.py
```

### 2. 启动应用

```bash
# 设置环境变量
export OPENAI_API_KEY="your-key"
export LANGFUSE_SECRET_KEY="..."
export LANGFUSE_PUBLIC_KEY="..."

# 运行 Reflex UI
reflex run
```

---

## 配置说明

### MCP 服务器配置

在 `main.py` 中自动配置：

```python
_mcp_pool.register_connection(MCPConnection(
    name="flights",
    transport="stdio",
    command=sys.executable,
    args=["mock_thy_server.py"],
))
```

### 路由策略配置

在 `main.py` 中自动注册：

```python
_routing_registry.register(
    IntentBasedRoutingStrategy(intent_map={
        "travel_planner": "extract_trip_params_node",
        "chitchat": "chitchat_node",
        "escalation": "escalation_node",
        "turkish_airlines": "turkish_airlines_node",
    })
)
```

### 技能注册

在 `main.py` 中自动注册：

```python
_skill_orchestrator.register_skill(PlanningSkill())
_skill_orchestrator.register_skill(ConversationSkill())
_skill_orchestrator.register_skill(InfoSkill())
_skill_orchestrator.register_skill(BookingSkill())
```

---

## 架构优势

| 优势 | 说明 |
|------|------|
| **职责分离** | 节点层处理流程，编排层处理调度，工具层处理连接 |
| **可扩展性** | 新增技能无需修改节点，新增 MCP 服务器无需修改代码 |
| **可测试性** | 每层可独立 Mock 测试 |
| **配置化** | 路由策略可通过配置修改，无需改代码 |
| **LLM 自主调用** | MCP 工具由 LLM 自主决定调用，无需硬编码 |

---

## 下一步优化建议

1. **完善技能层** - 让 PlanningSkill 真正调用 MCP 工具
2. **修复 State 模型** - 添加缺失字段支持 state_updates
3. **并行执行** - 实现 execute_plan 的并行调用
4. **更多路由策略** - 添加 KeywordBased、PriorityBased 策略
