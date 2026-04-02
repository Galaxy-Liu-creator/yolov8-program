# Claude Code 仓库说明

当任务涉及数据集、标注、训练配置、数据转换或样本分析时，请按以下顺序读取：

1. `AGENTS.md`
2. `docs/dataset.md`
3. `docs/dataset_examples/sample_001.jpg`
4. `docs/dataset_examples/sample_001.txt`

## 处理原则

- 默认整个数据集与示例文件使用相同的标注规则，除非 `docs/dataset.md` 明确说明存在例外。
- 不要只根据图片内容猜测标签格式。
- 如果需要修改代码以适配数据集，先以 `docs/dataset.md` 中的“任务类型”“类别表”“标注格式”“路径规则”为准。
- 如果示例文件不存在，先指出缺少示例，不要自行脑补完整数据格式。

## Python 环境约定

- 本仓库默认使用 Conda 环境 `yolo_code` 作为 Python 解释器环境。
- 当前约定的 Python 版本为 `3.9.25`。
- 如无特殊说明，Claude 在生成命令、脚本或环境相关建议时，均默认以该环境为准；与 Codex 协作时也应遵循同一约定。
