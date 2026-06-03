# new_person_labels ROI 分组与标记方案
## 1. 本文档解决什么问题
本文档专门回答：
1. 当前 `new_person_labels` 这批 `3000+` 图片，做 ROI-aware 前最合适的 ROI 标注方式是什么；
2. 是否应该全量逐图 ROI；
3. 如果不逐图，应该怎样分组、怎样抽代表帧、怎样画 ROI；
4. 物理分组、逻辑分组、组级 ROI、逐图 ROI 之间分别是什么关系；
5. 做完 ROI 分组与标注后，后续如何衔接 `extract-roi-config` 与 `prepare-roi-aware`。
本文默认配合以下文档一起看：
- ROI 标注工具与基本操作：`backend-train-model/person-train-model/train-docs/ROI_Labelme.md`
- 当前 new labels 主线决策：`backend-train-model/person-train-model/train-docs/person_with_new_labels_decision.md`
- 当前 fullframe 上游修正方案：`backend-train-model/person-train-model/train-docs/person_with_new_labels_fullframe_fix_plan.md`
---
## 2. 先给结论
### 2.1 当前最推荐的总方案
针对当前 `3000+` 图片，**不建议默认全量逐图 ROI，也不建议默认整包 flat source 共用一个 ROI**。
当前最推荐的工程方案是：
> **先分组，再做“组级 ROI 为主、逐图 ROI 为辅”的混合标注方案。**
可以压缩成一句执行口径：
```text
先按 ROI 稳定性把 new_person_labels 分成若干小组
-> 稳定组做组级 ROI
-> 半稳定组继续细分后再做组级 ROI
-> 只有少量实在不稳定的小组才逐图 ROI
```
### 2.2 为什么不推荐一上来全量逐图
全量逐图 ROI 的主要问题不是“不能做”，而是：
1. 工作量太大；
2. 组内一致性最难控制；
3. 标注风格很容易漂；
4. 后续检查、返工与版本化维护成本高。
### 2.3 为什么也不推荐整包只画一个 ROI
`new_person_labels_flat_20260503` 如果内部混有：
- 多个摄像头；
- 多个场景；
- 多个视角；
- 多种 ROI 边界；
那么整包只画一个 ROI 的问题会很明显：
1. ROI 语义会失真；
2. keep/drop 规则会错；
3. crop 质量会不稳定；
4. prepared 数据集很容易被“错误统一 ROI”污染。
---
## 3. 当前最合适的标注策略：分层混合方案
### 3.1 总体思路
建议把当前 `3000+` 图分成三类：
| 组别 | 特征 | 推荐标注方式 |
| --- | --- | --- |
| A 类：稳定组 | 同摄像头、同视角、背景基本不变、ROI 边界稳定 | 组级 ROI |
| B 类：半稳定组 | 大体同场景，但有轻微裁切变化、抖动、光照差异 | 继续细分后做组级 ROI |
| C 类：不稳定组 | 多视角、多场景混杂，ROI 边界变化明显 | 逐图 ROI，或暂缓进入 ROI-aware v1 |
### 3.2 推荐比例
在工程上，通常建议优先争取做到：
- `70% ~ 85%` 图片：组级 ROI；
- `10% ~ 20%` 图片：细分后组级 ROI；
- `5% ~ 15%` 图片：逐图 ROI 或暂缓进入第一版 ROI-aware。
这不是硬指标，但它代表一个很实际的原则：
> **尽量让大多数图片享受“低成本 + 高一致性”的组级 ROI，只把少量真正不稳定的图片留给逐图 ROI。**
---
## 4. 物理分组、逻辑分组、组级 ROI、逐图 ROI 分别是什么
### 4.1 物理分组
物理分组解决的是：
> 文件怎么放、哪批图片先放到同一个目录里。
例如：
```text
new_person_labels_grouped/
├─ group_001_cam01_day_view1/
├─ group_002_cam01_night_view1/
├─ group_003_zoneA_far_view/
└─ group_004_zoneB_close_view/
```
### 4.2 逻辑分组
逻辑分组解决的是：
> 训练和 ROI-aware 语义上，哪些图片可以共用一个 ROI，哪些应该单独处理。
一个物理组通常会对应一个逻辑组，但不保证完全一一对应。也就是说：
- 有些物理组后续还要继续细拆；
- 有些物理组里不同图片，最终还是要逐图 ROI；
- 有些物理组可能只是临时存放结构，不一定能直接当训练用 sequence。
### 4.3 组级 ROI
组级 ROI 指的是：
> 给同一组图片共用一版 ROI。
它适合：
- 摄像头固定；
- 视角基本固定；
- 背景和作业区边界稳定；
- 大多数图片都能接受同一版 ROI。
在当前这套工具链里，`组级 ROI` 还需要额外满足一个很具体的落盘条件：
- 同一 `sequence_name` 下，`roi-json/` 里要么只保留 `1` 份主 ROI JSON；
- 要么保留多份 JSON，但它们的 `roi polygon` 顶点坐标必须完全一致；
- 这样 `extract-roi-config` 才会为这一组生成 `per_sequence` 级别的 fallback ROI。
如果你在同一组的代表帧上各自手画出“肉眼差不多、但顶点略有差别”的 polygon，工具链会把它识别成 `per_image ROI`，而不是严格意义上的组级 ROI。
### 4.4 逐图 ROI
逐图 ROI 指的是：
> 每张图片都单独画一个 ROI。
它适合：
- 组内视角变化大；
- ROI 边界变化大；
- 无法共享同一版 ROI；
- 但这批图片又确实有必要进入 ROI-aware。
---
## 5. 推荐执行顺序
### 5.1 第一步：先保留原始入口，不要直接改坏当前 fullframe 主线
当前建议把原始数据入口先视为只读：
- `../frame_label/new_person_labels/images`
- `../frame_label/new_person_labels/person_labels`
不要直接在这套原始目录上剪切 / 搬动 / 改名。更推荐：
- 新建一套 grouped 目录；
- 通过复制、软链接或后续 manifest 管理去组织 ROI-aware 版本。
这样做的好处是：
1. 不会破坏当前 fullframe 主线；
2. 后续如果分组策略改了，返工成本更低；
3. 原始数据与 ROI-aware 数据准备链更容易区分。
### 5.2 第二步：先做“轻量试分组判断”
不要上来就大规模搬文件。先做一份轻量试分组表，至少记录下面字段：
- `image_stem`
- `original_path`
- `camera_id`
- `scene_id`
- `view_id`
- `roi_stability_group`
- `comment`
这一步的目标不是先做出最终完美分组，而是先回答：
> 这批图片，按什么维度分开后最容易共用 ROI？
### 5.2A 可先用自动粗分组脚本做第一轮预分组
当前仓库已新增自动粗分组脚本：
- `backend-train-model/person-train-model/train-code/auto_group_new_person_labels_roi.py`
它的定位不是“直接替代最终人工逻辑分组”，而是：
> **先按图片分辨率 + 粗视觉特征，把 `new_person_labels` 自动拆成第一轮候选组，帮助你减少纯手工从 3000+ 图片里盲分的工作量。**
推荐命令：
```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\auto_group_new_person_labels_roi.py --clean-output --materialize-mode hardlink_or_copy --create-empty-missing-labels
```
默认会输出到：
- `backend-train-model/person-train-model/train-result/working/new_person_labels_roi_grouping/`
其中至少会包含：
- `group_manifest.csv`：逐图分组结果；
- `group_summary.json`：每组统计与代表帧；
- `grouped/`：自动生成的物理分组目录（图片和标签）。
### 5.2B 当前 `../frame_label/roi-json` 目录审核结论
截至 `2026-05-21`，对 `../frame_label/roi-json` 当前目录结构做完抽样审核后，可以把它明确理解成两部分：
1. 旧固定 sequence 的已完成 ROI 样例：
   - `group3_1 / group3_2 / group3_3`
   - 这部分目录下已经有完整 `frames/ + roi-json/`
   - 主要用于参考现有 `Labelme json` 格式和工具链衔接方式
2. 本轮 `new_person_labels` 待做 ROI 的正式工作目录：
   - `group_0001 ~ group_0006`
   - 这 `6` 组下面已经是标准的 `frames/ + roi-json/` 结构
   - `frames/` 里是当前组的全部图片，`roi-json/` 当前留空，正适合直接开始本轮标注
当前 `new_person_labels` 这 `6` 组的规模分别是：
- `group_0001`：`272`
- `group_0002`：`449`
- `group_0003`：`127`
- `group_0004`：`387`
- `group_0005`：`582`
- `group_0006`：`690`
总计仍然是：
- 总图片数：`2507`
- 总组数：`6`
- 其中：
  - `1280 x 720`：`1` 组，共 `272` 张；
  - `1920 x 1080`：`5` 组，共 `2235` 张。
结合首帧 / 四分位帧 / 中位帧 / 后四分位帧 / 尾帧的抽样结果，当前目录审核结论是：
1. `group_0001` 画面稳定、分辨率独立，可以直接视为 `A 类稳定组`；
2. `group_0002` 与 `group_0003` 虽然同为 `1920x1080`，但构图边界和可用作业区并不相同，继续分开是合理的；
3. `group_0004 / group_0005 / group_0006` 都属于近景油岛类画面，但对应的岛位和画面布局不同，第一轮先分开做 ROI 更稳妥；
4. 当前没有看到“同一组内部明显混入多个视角 / 多个场景，必须先继续细拆才能开始 ROI”的强信号。
因此，**当前这版 `group_0001 ~ group_0006` 分组整体上是合理的，可以直接进入第一轮组级 ROI 标注**。
当前更推荐的实际执行口径不是“先继续拆组”，而是：
- **先按这 `6` 个组直接做第一轮组级 ROI；**
- **再通过抽检结果决定是否把个别组降级为 `B 类` 继续细拆。**
### 5.3 第三步：再做物理分组
当你已经能大致回答“哪些图片属于同一摄像头 / 场景 / 视角”后，再开始物理分组。
推荐目录结构例如：
```text
new_person_labels_grouped/
├─ group_001_cam01_day_view1/
│  ├─ images/
│  └─ labels/
├─ group_002_cam01_night_view1/
│  ├─ images/
│  └─ labels/
├─ group_003_zoneA_far_view/
│  ├─ images/
│  └─ labels/
└─ group_004_mixed_hard_cases/
   ├─ images/
   └─ labels/
```
### 5.4 第四步：每个物理组再判断 A / B / C 类
分完物理组后，不要默认每组都能直接共用一个 ROI。
你还需要判断：
- 这是稳定组（A）？
- 半稳定组（B）？
- 还是不稳定组（C）？
然后再决定它应该走：
- 组级 ROI；
- 继续细分；
- 逐图 ROI；
- 或暂缓纳入 ROI-aware 第一版。
---
## 6. 具体怎么判断“能不能共用一个 ROI”
建议用下面 5 条去判断。
如果一组图片满足下面 `5 条里的 4 条`，通常可以先按组做 ROI：
1. 同一摄像头；
2. 同一视角；
3. 背景和作业区边界基本一致；
4. 图像尺寸与裁切方式基本一致；
5. 你画出一版 ROI 后，随机抽查该组 `10~20` 张图，`80%` 以上都能接受。
如果做不到，就继续拆组。
---
## 7. A 类稳定组：如果不是逐图，应该具体怎么做
这是当前最推荐大量使用的方案。
### 7.1 每组先抽代表帧
每个稳定组建议：
- 至少抽 `5` 张；
- 一般不超过 `10` 张。
抽样时优先覆盖：
- 正常工作场景；
- 入口边缘；
- 轻微光照变化；
- 轻微裁切变化；
- 边界位置最容易出问题的图。
### 7.1A 当前 `new_person_labels` 六个组的直接可用代表帧
下面这批代表帧不是按固定间隔机械抽样，而是结合当前组内的构图稳定性、车辆占位、人靠近 ROI 边界、近景遮挡和视角边缘变化人工挑出的第一轮代表帧。它们的目标是覆盖“这一组里会影响 ROI 画法的主要变化”，而不是单纯均匀铺满时间轴。
| 组 ID | 当前判断 | 主标注帧 | 代表帧清单 |
| --- | --- | --- | --- |
| `group_0001` | `A` | `02372.jpg` | `02236.jpg, 02275.jpg, 02313.jpg, 02372.jpg, 02439.jpg, 02473.jpg, 02507.jpg` |
| `group_0002` | `A` | `00225.jpg` | `00001.jpg, 00057.jpg, 00169.jpg, 00225.jpg, 00281.jpg, 00337.jpg, 00449.jpg` |
| `group_0003` | `A` | `00513.jpg` | `00450.jpg, 00466.jpg, 00497.jpg, 00513.jpg, 00529.jpg, 00544.jpg, 00576.jpg` |
| `group_0004` | `A` | `00770.jpg` | `00577.jpg, 00625.jpg, 00673.jpg, 00770.jpg, 00818.jpg, 00867.jpg, 00963.jpg` |
| `group_0005` | `A` | `01255.jpg` | `00964.jpg, 01037.jpg, 01109.jpg, 01255.jpg, 01327.jpg, 01400.jpg, 01545.jpg` |
| `group_0006` | `A` | `01891.jpg` | `01546.jpg, 01632.jpg, 01718.jpg, 01891.jpg, 01977.jpg, 02063.jpg, 02235.jpg` |
补充判断说明：
- `group_0001`：独立 `1280x720` 机位，补进了车头切入、人员靠右边界和下方车辆进入的变化帧；
- `group_0002`：远景大场地，补进了人员靠左下 / 中央通行和空场景尾帧；
- `group_0003`：补进了左下大车占边、人员走到中区和空场景尾帧；
- `group_0004`：补进了左侧大车遮挡、近景人员靠柱和空场景收尾帧；
- `group_0005`：补进了右侧车辆靠近、多人分布和尾帧车辆占位变化；
- `group_0006`：补进了左下近景人员、中心走位和右侧车辆停靠变化。
### 7.2 用 Labelme 给代表帧画 ROI
建议统一：
- `polygon`
- 标签名：`roi`
当前阶段仍建议先画：
> **保守宽 ROI**
也就是：
- 先去掉最明显无关区域；
- 不要一上来卡得特别紧；
- 避免因为 ROI 过紧，进一步伤害上游 person Recall。
### 7.2A 当前目录的组级 ROI 标注落地步骤
对 `group_0001 ~ group_0006`，当前建议严格按下面顺序做：
1. 逐组打开 `frames/` 目录，输出到对应的 `roi-json/` 目录，例如：
```powershell
labelme ..\frame_label\roi-json\group_0001\frames --output ..\frame_label\roi-json\group_0001\roi-json --labels roi
```
2. 先在该组的“主标注帧”上画出第一版 ROI 模板：
   - `group_0001 -> 02372.jpg`
   - `group_0002 -> 00225.jpg`
   - `group_0003 -> 00513.jpg`
   - `group_0004 -> 00770.jpg`
   - `group_0005 -> 01255.jpg`
   - `group_0006 -> 01891.jpg`
3. 再用同组其余 `6` 张代表帧做校验，重点看车辆停靠、人走到边界、近景遮挡和空场景时，当前 polygon 是否仍然成立；
4. 如果其余代表帧也都能接受，**最终落盘时不要留下多份“略有差别”的 polygon**；
5. 对当前工具链，组级 ROI 的安全落盘方式只有两种：
   - `roi-json/` 里只保留 `1` 份主标注帧 JSON；
   - 或保留多份 JSON，但这些 JSON 的 `roi polygon` 必须来自同一版模板复制，顶点坐标完全一致。
换句话说，代表帧在这里的主要作用是：
- 帮你确认“这一组能不能共用一版 ROI”；
- 不是要求你把 `7` 张代表帧都手画成 `7` 个轻微不同的 ROI。
如果 `7` 张代表帧里有 `2` 张及以上明显不适配当前 ROI 模板，就先不要硬做组级 ROI，而是把该组降级成 `B 类` 再细拆。
### 7.3 固化为该组的组级 ROI
如果代表帧之间的 ROI 差异很小，就可以把这一版 ROI 作为该组的“组级 ROI 模板”。
对当前 `new_person_labels` 六组，建议把“固化成功”的判断标准写得更明确一点：
1. `group_000X/roi-json/` 中最终用于提取配置的 JSON，必须能代表同组共用的那一版 ROI；
2. 跑完 `extract-roi-config` 后，`roi_config.fullframe_with_new_labels.generated.json` 里的 `per_sequence` 应该出现对应的 `group_000X`；
3. 同时 `summary.sequence_unique_polygon_counts.group_000X` 应该为 `1`。
推荐自检命令：
```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --project-config backend-train-model\person-train-model\person_project_config.fullframe_with_new_labels.json --overwrite
```
如果你发现某个 `group_000X` 没有进入 `per_sequence`，而是只出现在 `per_image`，优先检查的不是训练脚本，而是：
- 是否在同一组里留下了多份略有差异的 JSON；
- 是否不小心把校验帧当成逐图 ROI 保存了下来。
### 7.4 做组内抽检
画完代表帧后，不要立即结束。建议回看该组额外 `10~20` 张图，检查：
1. 有没有明显漏掉应该保留的作业区；
2. 有没有明显吃进去太多无关背景；
3. 在不同图片里偏差是不是仍然很小。
如果 `80%` 以上图片都能接受，就保留组级 ROI。
如果偏差还是很大，说明这一组不够稳定，需要继续拆组。
对当前这 `6` 个组，建议抽检时优先补看：
- `group_0001`：尾帧附近是否出现右侧边缘漏裁或过裁；
- `group_0002`：左侧建筑边缘和远端道路区域是否被不必要纳入；
- `group_0003`：下方车辆近景遮挡时，ROI 下边界是否仍保持一致；
- `group_0004`：左右大车靠边停靠时，ROI 是否过度贴车体而不是围绕作业区；
- `group_0005`：右侧玻璃反光区域是否被误当成有效区域；
- `group_0006`：左下角立柱 / 人员近景区域是否需要比 `group_0005` 更保守一点。
---
## 8. B 类半稳定组：应该具体怎么做
半稳定组不要直接全量逐图。先再拆一层。
### 8.1 优先细分的维度
可以优先尝试按下面方式继续拆：
- 白天 / 夜晚；
- 左偏 / 右偏；
- 远景 / 近景；
- 同一大场景下的不同构图版本。
### 8.2 拆完后再回到 A 类流程
只要拆完后组内 ROI 基本稳定，就按照第 7 节回到组级 ROI 流程。
### 8.3 只有拆不动时才逐图
如果拆完后仍然变化很大，才把这一小组升级到逐图 ROI。
---
## 9. C 类不稳定组：什么时候才逐图 ROI
下面这些情况，建议直接逐图，不要再强求共用 ROI：
1. 同一组里视角变化特别大；
2. ROI 边界随图片明显平移或缩放；
3. 实际上混了多个摄像头；
4. 组级 ROI 在大于 `20%` 图片上明显不合适；
5. 数量不大，但业务上很重要。
### 9.1 逐图 ROI 的工作方式
如果某批图最终要逐图 ROI，建议不要“每张从零开始乱画”，而是：
1. 先找到最接近的一版组级 ROI；
2. 逐图时基于该 ROI 做微调；
3. 尽量保持同类场景的边界语义一致。
这样可以降低标注风格漂移风险。
### 9.2 什么时候可以暂缓纳入 ROI-aware 第一版
如果某批图：
- 非常混乱；
- ROI 变化大；
- 逐图成本过高；
- 占比又不大；
那么当前完全可以：
> **先保留在 fullframe 训练里，不强行塞进 ROI-aware v1。**
这不是偷懒，而是合理控制第一版 ROI-aware 的工程风险。
---
## 10. 推荐的整体实施比例与节奏
### 10.1 不要把“ROI-aware 第一版必须覆盖 3000+ 全量”当硬目标
当前更推荐的节奏是：
1. 先让大部分稳定场景进入 ROI-aware；
2. 先把第一版链路跑通；
3. 再逐步扩展到半稳定组和不稳定组。
也就是说：
> **ROI-aware 第一版不一定非要覆盖 3000+ 全量。**
### 10.2 推荐的实施节奏
```text
第一轮：稳定组先做组级 ROI
-> 第二轮：半稳定组继续细分并补 ROI
-> 第三轮：少量不稳定组逐图 ROI 或决定暂缓
-> 第四轮：再统一进入版本化 ROI-aware 数据准备
```
---
## 11. 标注一致性要求
无论是组级 ROI 还是逐图 ROI，都建议遵守下面这些一致性要求：
1. ROI 画的是“业务有效区域”，不是“这张图里人站在哪里”；
2. 同类场景尽量保持边界松紧一致；
3. 不要这批图画得特别宽，另一批图又特别紧；
4. 当前第一版仍优先保守宽一点，不要过度极限贴边；
5. 如果一组图里反复出现明显不一致，优先怀疑“这组本来就不该共用 ROI”，而不是继续硬画。
---
## 12. 后续如何衔接现有工具链
### 12.1 旧固定 sequence
旧 `group3_1 / group3_2 / group3_3` 的 7 条固定 sequence，仍然可以继续沿用现有：
- `setup-roi-workdir`
- `extract-roi-config`
- `prepare-roi-aware`
### 12.2 new_person_labels
对于 `new_person_labels`，建议后续：
1. 先完成本文这套分组和标注；
2. 再为 ROI-aware 新建独立版本化配置；
3. 使用独立的：
   - `ROI work root`
   - `ROI config output path`
   - `ROI-aware prepared output root`
   - `recommended_run_name`
4. 不要直接覆盖当前 `fullframe_with_new_labels` 产物。
---
## 13. 当前最推荐的具体方案
针对你现在这批 `3000+` 图片，当前最推荐的执行方式是：
> **先做轻量试分组 -> 再做物理分组 -> 稳定组用组级 ROI -> 半稳定组继续拆分 -> 只有少量实在不稳定的组才逐图 ROI。**
如果只压缩成一句话：
> **最好的 ROI 标注方式不是“3000+ 全量逐图”，而是“先分组、后组级 ROI、最后对少量不稳定组逐图补位”的混合方案。**
---
## 14. 一句话执行口径
> **当前 `new_person_labels` 做 ROI-aware 时，优先使用“组级 ROI 为主、逐图 ROI 为辅”的分层混合方案：先按摄像头 / 场景 / 视角 / ROI 稳定性分组，稳定组用组级 ROI，半稳定组继续细分，只有少量实在无法稳定归组的图片才逐图 ROI；不要默认全量逐图，也不要默认整包 flat source 共用一个 ROI。**

