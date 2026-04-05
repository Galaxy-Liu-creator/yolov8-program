# `backend-train-model` 落地执行清单（TODO List）

本文档用于把 `backend-train-model/docs/pipeline_roadmap.md` 中的阶段性建议，进一步落成**可以逐步执行的待办清单**。

它回答的不是“理想上怎么做”，而是：

- 现在先做什么
- 下一步做什么
- 每一步要产出什么
- 哪些步骤属于训练问题，哪些属于链路问题

---

## 0. 当前推荐总路线

当前最推荐的执行顺序是：

```text
阶段 1：先训稳 clothes baseline
阶段 2：补 person 数据资产
阶段 3：训练 / 固化 person 模型
阶段 4：启用 personcrop，重训 clothes
阶段 5：离线搭建完整链路
阶段 6：接实时摄像头上线
```

当前推荐训练的模型数量是：

1. **`clothes/workwear` 检测模型**
2. **`person` 检测模型**

当前不建议一开始新增第三个模型。

`ROI / area / stay / temporal / alarm` 当前更建议继续作为：

- 规则层
- 链路层
- 阈值配置层

而不是直接并入一个训练模型。

---

## 1. P0：先把当前 `clothes` baseline 固定下来

### 1.1 目标

先用当前已有数据，得到一个可复现、可对比的 `clothes` 基线模型。

### 1.2 当前状态

当前仓库已经具备下面这些条件：

- `clothes` 数据入口已配置
- 数据审计命令可运行
- `fullframe` / `personcrop` 两种 prepare 模式已具备
- 训练 / 评估 / 导出流程已具备

### 1.3 待办项

- [ ] 确认 `docs/dataset.md` 与真实数据路径仍一致
- [ ] 保持当前 `clothes` 标签体系不变，不急着混入 `person`
- [ ] 先跑一次 `audit`，确认数据质量
- [ ] 跑一次 `fullframe` baseline 训练
- [ ] 跑一次 baseline 评估
- [ ] 导出 baseline 权重和报告
- [ ] 单独整理一份 baseline 误报 / 漏报样本清单

### 1.4 推荐命令

#### 数据审计

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py audit
```

#### 生成 `fullframe` 数据集

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode fullframe --overwrite
```

#### 训练 `fullframe` baseline

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode fullframe
```

#### 评估当前 best 权重

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py evaluate
```

#### 导出当前 best 权重

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py export
```

### 1.5 阶段产物

- `backend-train-model/artifacts/prepared/fullframe/sequence_contiguous/dataset.yaml`
- `backend-train-model/artifacts/runs/.../weights/best.pt`
- `backend-train-model/artifacts/reports/*_train.json`
- `backend-train-model/artifacts/reports/*_evaluate.json`
- `backend-train-model/artifacts/export/workwear_detect_yolov8.pt`

### 1.6 完成标准

只有当下面几个问题都能回答时，才算完成本阶段：

- 当前 `clothes` 模型最容易漏掉哪些姿态
- 当前 `clothes` 模型最容易误报哪些目标
- `fullframe` 方案在你现场图像上是否能先跑通
- 当前 baseline 是否已经可复现

---

## 2. P1：补 `person` 数据资产，但先不要污染当前 `clothes` 主标签

### 2.1 目标

建立后续 `person` 模型训练所需的数据基础。

### 2.2 关键原则

当前推荐的是：

- **同图可双标**
- **标签目录先分离**

也就是说，可以使用同一批图片，同时维护：

- 一套 `clothes` 标签
- 一套 `person` 标签

但当前不建议直接把它们混进同一个训练标签目录。

### 2.3 推荐的数据组织方式

推荐选择以下两种方式之一：

#### 方案 A：同图双标，双标签目录

- `clothes` 标签继续沿用当前目录
- `person` 标签新建独立目录

#### 方案 B：单独建立 `person` 数据集

- 为 `person` 任务单独维护图片与标签
- 如果后续需要，也可混入通用行人数据再微调

### 2.4 待办项

- [ ] 为当前三段序列补全 `person` 框
- [ ] 确认 `person` 的标注规则统一
- [ ] 确认图片与 `person` 标签仍按同名配对
- [ ] 确认三段序列之间图片命名无冲突
- [ ] 确认 `person` 标签不覆盖 / 不污染现有 `clothes` 主标签
- [ ] 选定未来 `person` 数据的存放目录
- [ ] 为 `person` 数据补 1 组示例文件与标注说明

### 2.5 本阶段建议新增的文档 / 资产

- [ ] 新增 `person` 数据说明文档
- [ ] 新增 `person` 示例图片
- [ ] 新增 `person` 示例标注

### 2.6 完成标准

只有当下面条件成立时，才进入下一阶段：

- 你手里已经有可训练的 `person` 标签数据
- `person` 的标注规则已经稳定
- `person` 数据与 `clothes` 数据的边界已经清楚

---

## 3. P2：训练并固化 `person` 模型

### 3.1 目标

得到一份可复用的 `person` 权重文件，作为完整业务链路的上游入口。

### 3.2 为什么这个阶段重要

当前 `backend-train-model` 的 `auto` 模式，并不是看“数据里有没有 `person` 标签”，而是看：

- **有没有可用的 `person` 模型权重**

所以，只有完成这个阶段之后，`auto` 才真正有机会默认落到 `personcrop`。

### 3.3 待办项

- [ ] 确定 `person` 训练任务使用的类别定义
- [ ] 确定 `person` 任务的训练脚本方案
- [ ] 用 `person` 数据完成一次 baseline 训练
- [ ] 完成一次 `person` 模型评估
- [ ] 选出当前最稳的 `person` 权重
- [ ] 把最终权重固定到项目约定位置

### 3.4 权重目标位置

当前推荐目标位置为：

```text
backend-train-model/weights/person_detect_yolov8.pt
```

达到这个状态后：

- `backend-train-model` 的 `auto` 模式
- `personcrop` 数据准备
- `inspection-flask` 的链路复核

才真正具备稳定前提。

### 3.5 本阶段执行建议

本阶段不强求你立刻把 `person` 训练流程硬塞进现有 `train_workwear.py`。

更推荐的顺序是：

1. 先把 `person` 权重训练出来
2. 再决定是否要把 `person` 训练脚本并入仓库

这样做更稳，因为当前现有训练脚本天然偏向 `clothes/workwear` 任务。

### 3.6 完成标准

- 已有一份可用的 `person_detect_yolov8.pt`
- 已在你当前现场画面上做过基本可用性验证
- 已知 `person` 模型的主要误检 / 漏检类型

---

## 4. P3：启用 `personcrop`，重训 `clothes` 模型

### 4.1 目标

在已有 `person` 权重的前提下，让 `clothes` 检测训练更贴近真实业务推理链路。

### 4.2 待办项

- [ ] 把 `person` 权重放到默认候选位置，或训练时显式传入 `--person-model`
- [ ] 用 `auto` 再跑一次 `prepare`
- [ ] 确认本轮 `prepare` 实际已解析到 `personcrop`
- [ ] 基于 `personcrop` 数据再训一版 `clothes` 模型
- [ ] 保留与 `fullframe` baseline 的可比报告
- [ ] 对比两种方案的误报 / 漏报差异

### 4.3 推荐命令

#### 自动选择模式

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode auto --overwrite
```

#### 显式指定 `personcrop`

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py prepare --mode personcrop --person-model backend-train-model\weights\person_detect_yolov8.pt --overwrite
```

#### 基于 `personcrop` 数据训练

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\train_workwear.py train --mode auto --person-model backend-train-model\weights\person_detect_yolov8.pt
```

### 4.4 对比时重点观察什么

- [ ] 小目标工服检出是否更稳
- [ ] 背景误报是否更少
- [ ] `person` 漏检是否把下游误差放大
- [ ] 站姿、弯腰、遮挡时是否更稳定

### 4.5 完成标准

只有当你能明确回答：

- `fullframe` 更好，还是 `personcrop` 更好
- 哪一种更贴合你的现场误报结构

才建议进入完整链路阶段。

---

## 5. P4：离线搭建完整链路

### 5.1 目标

在没有实时摄像头接入的情况下，先用序列帧把完整业务链路跑通。

### 5.2 推荐链路

```text
序列帧
-> person
-> track_id / trajectory
-> ROI / area / stay filtering
-> candidate worker
-> clothes
-> temporal verification
-> alarm
```

### 5.3 待办项

- [ ] 确认每个摄像头 / 序列对应的 ROI 区域
- [ ] 确认面积过滤阈值
- [ ] 确认停留时长阈值
- [ ] 确认连续多帧告警阈值
- [ ] 选定离线回放验证的样本序列
- [ ] 输出链路级误报 / 漏报清单
- [ ] 记录每个场景的推荐阈值

### 5.4 当前仓库建议的链路职责划分

#### 模型层

- `person`：做人检测
- `clothes`：做工服检测

#### 规则层

- ROI
- area
- stay
- temporal

#### 输出层

- 告警
- 证据图
- 运行日志

### 5.5 本阶段最重要的产物

- [ ] 各场景 ROI 配置
- [ ] 各场景阈值配置
- [ ] 链路级复核报告
- [ ] 误报样本库
- [ ] 漏报样本库

### 5.6 完成标准

- 不接实时摄像头时，完整链路已经能离线跑通
- 误报 / 漏报已经可以定位到具体链路阶段
- 你已经知道后续该优先补哪一层

---

## 6. P5：接实时摄像头上线

### 6.1 目标

把已经通过离线验证的链路接到真实视频流。

### 6.2 待办项

- [ ] 接入单路摄像头做灰度验证
- [ ] 调整该摄像头的 ROI
- [ ] 调整 area / stay / temporal 阈值
- [ ] 观察告警稳定性
- [ ] 保存线上误报 / 漏报样本
- [ ] 形成首轮线上参数建议

### 6.3 注意事项

- 不建议一上来多路同时上线
- 不建议在链路未离线稳定前直接追实时告警
- 不建议把线上问题全部归咎于检测模型

很多线上问题，本质上更可能出在：

- ROI 画法
- 时序窗口
- 候选目标阈值
- 场景差异

---

## 7. 哪些事情现在不要做

下面这些事情，当前都不建议抢跑：

- [ ] 不要立刻把当前 `clothes` 主标签整体改成多类混标
- [ ] 不要一开始就追求“一个模型吃掉整条业务链路”
- [ ] 不要在还没有 `person` 权重时，就假设 `auto` 一定能自动切到 `personcrop`
- [ ] 不要在没有离线链路验证前就直接多路接实时摄像头
- [ ] 不要把 ROI、时序告警这些规则问题误当成纯训练问题

---

## 8. 最推荐的近期执行顺序

如果只考虑“接下来一两周最值得做什么”，当前最推荐的顺序是：

### 第一优先级

- [ ] 跑通并固定 `fullframe clothes` baseline
- [ ] 整理 baseline 的误报 / 漏报样本

### 第二优先级

- [ ] 补 `person` 标签
- [ ] 建立独立 `person` 数据资产

### 第三优先级

- [ ] 训练并固化 `person` 模型
- [ ] 将其放到 `backend-train-model/weights/person_detect_yolov8.pt`

### 第四优先级

- [ ] 跑通 `personcrop clothes`
- [ ] 比较 `fullframe` 与 `personcrop`

### 第五优先级

- [ ] 离线搭建完整链路
- [ ] 再接实时摄像头

---

## 9. 里程碑检查表

### 里程碑 A：`clothes` baseline 完成

- [ ] 有稳定可复现的 `clothes` best 权重
- [ ] 有评估报告
- [ ] 有误报 / 漏报清单

### 里程碑 B：`person` 数据资产完成

- [ ] 有独立 `person` 标签
- [ ] 有统一标注规则
- [ ] 有示例文件

### 里程碑 C：`person` 模型完成

- [ ] 有 `person_detect_yolov8.pt`
- [ ] 已做过基础可用性验证

### 里程碑 D：`personcrop clothes` 对比完成

- [ ] 已训练 `personcrop` 版本
- [ ] 已与 `fullframe` 做对比
- [ ] 已选出当前更优方案

### 里程碑 E：完整链路离线跑通

- [ ] 已具备 `person + clothes + ROI + temporal`
- [ ] 已能离线回放
- [ ] 已有链路级误报 / 漏报复盘

### 里程碑 F：上线灰度准备完成

- [ ] 已完成单路摄像头验证
- [ ] 已有场景配置
- [ ] 已形成首轮上线参数

---

## 10. 一句话执行建议

如果要把整份清单压缩成一句话，那就是：

> **先把 `clothes` 训练做成稳定 baseline，再独立补齐 `person` 数据并训练 `person` 模型，随后用两模型加规则层搭建完整链路；在没有实时视频接入时，优先完成离线链路回放，而不是一开始就试图训练一个吃掉全部业务逻辑的大模型。**

