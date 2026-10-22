# 数据源与版本

本仓库只提交来源清单和审计代码。下载文件保留在忽略目录 `data/`；可逐项复核 `config/sources.lock.json` 的URL、提交、大小及哈希。

| 来源 | 实际审计范围 | 固定版本 | 上游入口 |
|---|---|---|---|
| FIREBALL | 作者仓库的1场战斗，raw.jsonl与filtered_triples.jsonl | `02a040bdfc9de5c7da271ca7faad56be090669ba` | [仓库](https://github.com/zhudotexe/FIREBALL)、[ACL 2023论文](https://aclanthology.org/2023.acl-long.229/) |
| CRD3 | 清洗后的C1E001一集 | `7fd4515eea411f0f9c5d0a03a8b6b8b2da464e81` | [仓库](https://github.com/RevanthRameshkumar/CRD3)、[ACL 2020论文](https://aclanthology.org/2020.acl-main.459/) |
| FIREBALL预处理代码 | normalize、finetune_prep、子模块配置 | `b3f9b5eca6dbbe1b7504c14dcbc055687bd4c7b4` | [仓库](https://github.com/zhudotexe/FIREBALL-data-processing) |
| Avrae | 上述子模块固定的combatant及builders文件 | `e1e361d73b8fc6dad0ed7633eb354a71b069daaa` | [固定源码](https://github.com/avrae/avrae/tree/e1e361d73b8fc6dad0ed7633eb354a71b069daaa) |

FIREBALL仓库标注CC BY 4.0，同时README写有research purposes only；本项目保留其原始LICENSE与README供使用者核验，不将其解释成额外的数据发布授权。CRD3仓库标注CC BY-SA 4.0。预处理代码及Avrae的使用遵从各自上游许可；这里不重新发布其源码，只按固定哈希获取所需文件。

FIREBALL论文作者为 Andrew Zhu、Karmanya Aggarwal、Alexander Feng、Lara J. Martin、Chris Callison-Burch；CRD3论文作者为 Revanth Rameshkumar、Peter Bailey。论文分别发表于ACL 2023与ACL 2020。当前工作是原始样本和源码核查，不宣称已完整复现论文。

## 扩展入口（尚未完成本地审计）

[作者HF发布](https://huggingface.co/datasets/lara-martin/FIREBALL)提供filtered文件。2026-10-22本机两次小文件下载连接超时；这不是数据未公开的证据。HF加载脚本的TRAIN标签不能替代原论文划分。后续必须保留源文件/会话ID，并检查参与者和campaign重叠。

综艺、影视、小说等候选素材还需要核查可用性、身份、时间线、动作和授权；当前仓库不包含这些素材的采集器或标注数据。
