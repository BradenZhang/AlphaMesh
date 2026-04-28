# MVP Scope

AlphaMesh MVP 的目标是交付一个可运行、可测试、可扩展的工程脚手架，而不是完整生产级交易系统。

## 当前包含

- FastAPI 后端和 Swagger 文档。
- Mock 行情、K 线、基本面和账户快照。
- LLM Research Agent，默认使用 Mock LLM Provider。
- 两个示例策略。
- 简单回测指标。
- 基础风控规则。
- 模板化信号解释。
- manual 与 paper_auto 自动化流程。
- Paper order 持久化和只读查询。
- Docker Compose 启动前端、后端和 PostgreSQL。

## 当前不包含

- 不接真实券商交易账户。
- 不调用真实东方财富、同花顺、长桥、富途牛牛或 IBKR API。
- 不处理真实资金。
- 不实现生产级撮合、订单状态同步、权限系统或审计系统。
- 不承诺策略有效性、收益率或风险控制效果。
- 不提供生产级交易界面。

## live_auto 边界

`live_auto` 默认关闭。即使通过配置开启，MVP 也没有真实券商实现，不应被用于任何真实交易场景。
