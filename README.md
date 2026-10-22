# Interaction-to-agents

从真实对话与交互记录构建可追溯的多智能体研究数据：数据源核查、角色与行动标注准备、信息可见性审计和协作决策评测。

Turning real-world interaction records into traceable datasets for multi-agent research.

目前代码实现的是 **FIREBALL 单场战斗与 CRD3 单集的可复现数据审计**。协作策略训练、跨会话评测和最终研究任务尚未完成。

## 当前实现

| 工具 | 用途 |
|---|---|
| `scripts/fetch_sources.py` | 按固定 Git 提交/对象下载作者公开小样本与源码，核验大小、SHA256、Git blob SHA1 |
| `scripts/audit_schema.py` | 核对事件、动作、前后状态的连接关系和 CRD3 转写结构 |
| `scripts/audit_visibility.py` | 检查隐藏生命值的显示差异，分开导出行动前输入与目标/结果，执行75项边界扰动检查 |
| `scripts/check_inputs.py` | 独立检查原始消息边界，并拒绝人为注入的当前动作 |
| `scripts/run_audits.py` | 顺序运行上述三个本地审计阶段 |

## 快速复现

Python 3.9+，仅使用标准库；移植版本在 Python 3.9.7 / Windows 上运行通过。不需要 GPU、模型、付费 API 或第三方 Python 包。

```bash
git clone https://github.com/rabbityi1999/Interaction-to-agents.git
cd Interaction-to-agents
python -B scripts/fetch_sources.py --data-dir data
python -B scripts/run_audits.py --data-dir data --output-dir outputs/reproduction
```

下载器访问公开 GitHub blob API，固定清单为12个文件，约2.4MB；不是下载全量 FIREBALL/CRD3。它复用已通过哈希检查的本地文件，不需要令牌。遇到网络或API限流错误时会停止；已有文件保留，下次执行继续核验。

输出目录若已存在，运行器会拒绝覆盖。重新实验时指定新的 `--output-dir`。不要使用 `python -O`，审计依赖断言检查。

输出中的 `visibility/inputs.jsonl` 与 `visibility/targets_results.jsonl` 通过 sample_id 对应；逐条数据和上游源码仅保存在本地的 `data/`、`outputs/`，不随本仓库发布。

## 已验证的结果

| 检查 | 固定样本结果 |
|---|---|
| FIREBALL 原始事件 / 三元组 | 342 / 25，均来自同一场战斗 |
| 动作交互ID对齐 | 25/25 |
| command 日志在结果状态之后记录 | 25/25；不能以该日志作为行动前历史的截止点 |
| 规范化状态保留隐藏角色精确HP | 25/25；其中20个行动者不是该角色控制者 |
| 未来文本、目标文本、结构化状态扰动 | 75/75不改变所导出的输入 |
| 独立输入核查 | 25条通过；当前动作注入负对照被拒绝 |
| CRD3 C1E001 | 2,160轮、4,693个转写片段 |

这些是数据工程检查，不是模型准确率或泛化指标。规范化全局状态与公共角色观测的差异，不等于原论文实验错误；也不能据此证明玩家绝对不知道某个数值。现有输入是记录到的频道历史，角色可见性仍待核验。

参见 [研究记录](docs/WORK_LOG.md)、[数据源与版本](docs/DATA_SOURCES.md)、[复现边界](docs/REPRODUCIBILITY.md) 和 [汇总结果](results/reference_summary.json)。

## 数据与授权

原始数据、论文PDF、逐条对话结果、模型权重和凭据不入库。公开数据与上游代码各自的许可仍然适用；下载清单并不转授其权利，详见 [数据源说明](docs/DATA_SOURCES.md)。
