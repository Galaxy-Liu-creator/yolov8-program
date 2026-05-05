
# 从 `inspection-flask_old` 的 YOLOv5 工服线得到的经验

## 1. 本文目的

本文用于审查 `inspection-flask_old/` 中与工服检测相关的旧版 YOLOv5 代码，回答三个问题：

1. 旧代码里到底保留了哪些 YOLOv5 训练 / 推理线索；
2. 旧代码里的工服检测实际是怎样跑的；
3. 对当前 `backend-train-model/` 下的 YOLOv8 工服训练，哪些地方最有借鉴意义，哪些地方不宜直接照搬。

本文重点关注的是**能被当前 clothes 训练线复用的经验**，而不是把旧系统整套在线链路直接搬回来。

---

## 2. 先说结论

先给结论，再看证据：

1. `inspection-flask_old` **没有完整保留**旧版 YOLOv5 的训练仓库状态；我找到了大量**推理代码、模型权重、模型结构 yaml**，但**没有找到可直接复现的 train/val 脚本、dataset yaml、split manifest 或正式评估报告**。
2. 旧系统里“工服检测准确度看起来高”，**很可能不只是 YOLOv5 版本本身的功劳**，更重要的是它采用了：
   - `person -> cloth` 的两阶段链路；
   - 对当前人框做**白底保留人体区域**的输入改造；
   - `coat / cloth / shirt` 的细粒度衣物标签；
   - 以及后续“衣物框中心是否落在该 person 内”的规则判断。
3. 因此，对当前 YOLOv8 工服训练最值得借鉴的，不是简单地说“换回 YOLOv5”，而是：
   - **优先做 person-guided clothes 路线验证**，但第一步应优先做**不依赖当前 person 预测质量的 oracle 版验证**；
   - 优先解决**小目标有效像素不足**的问题；
   - 再决定是否要换更大模型、更多类别或更大输入尺寸。

一句话说：

> 旧线最值得学的是“先把工服检测问题变成更容易的问题”，而不是“YOLOv5 天生就比 YOLOv8 更准”。

---

## 3. 实际审查到的关键文件与证据

### 3.1 直接相关文件

- `inspection-flask_old/settings.py`
  - 定义了旧系统工服检测权重与推理阈值：
    - `CLOTH_WEIGHT = weights/police_uniform.pt`
    - `IMGSZ = 640`
    - `CLOTH_CONF = 0.45`

- `inspection-flask_old/utils/models.py`
  - 旧系统真实生产推理入口之一。
  - `get_cloth_detect_model()` 从 `settings.CLOTH_WEIGHT` 加载工服模型。
  - `seek_targets()` / `seek_target()` 的推理设置为：
    - `letterbox(..., auto=False, stride=32)`
    - `conf_thres = 0.25`
    - `iou_thres = 0.45`
    - `augment=True`

- `inspection-flask_old/applications/common/hk_custom_threading_plus.py`
  - 在线主链路代码。
  - `common_target()` 中先做人检测，再对每个 `person` 调 `add_white_background()`，然后把**只保留该人的白底全图**送进 `cloth_detect_model`。
  - 这说明旧系统的工服检测**不是纯 fullframe clothes detect**，而是**person-guided 的二阶段检测**。

- `inspection-flask_old/test_main_for_cloth.py`
  - 离线测试脚本，和线上逻辑一致：
    - 先 `seek_targets(person_detect_model, ...)`
    - 再对每个 person 生成白底图
    - 再跑 `cloth_detect_model`
  - 这进一步证明旧工服线不是简单整帧检测。

- `inspection-flask_old/applications/common/logic_judge.py`
  - 旧系统的工服标签语义不是单类 `clothes`，而是：
    - `coat`
    - `cloth`
    - `shirt`
  - `judging_cloth()` 的判断逻辑是：
    - 先确认这个人是需要检查的正式民警；
    - 再看是否存在衣物框，其**中心点**落在该 `person` 框内；
    - 有则认为“穿了警服”，否则触发“未穿警服”违规。

### 3.2 旧版权重与模型规模线索

在 `inspection-flask_old/weights/` 中能看到：

- `police_uniform.pt`：`175079131` bytes
- `yolov5x.pt`：`176120518` bytes
- `zj_yici_230426.pt`：`94097707` bytes
- `yolov5l.pt`：`94562742` bytes

这给出两个很强的间接线索：

1. `police_uniform.pt` 的体积与 `yolov5x.pt` 非常接近，**大概率是 x 级别或接近 x 级别的自定义工服模型**；
2. `zj_yici_230426.pt` 与 `yolov5l.pt` 体积非常接近，**大概率是 l 级别或接近 l 级别的人检测模型**。

这意味着旧系统并不是“一个很轻的小模型到处跑”，而更像是：

- 一次人检测：接近 `yolov5l`
- 二次工服检测：接近 `yolov5x`

所以旧线“看起来很准”，也可能部分来自：

- **给工服检测阶段更大的模型容量**；
- 同时又先用 person 阶段把问题空间缩小了。

### 3.3 关于“训练代码”和“数据切分方法”的结论

这部分要明确区分“找到的”和“没找到的”。

#### 已找到的

- 旧仓库里保留了 YOLOv5 的模型源码与结构 yaml：
  - `inspection-flask_old/yolov5_module/models/*.yaml`
  - `inspection-flask_old/yolov5_module/models/hub/*.yaml`
- 也保留了旧部署阶段直接使用的自定义权重：
  - `police_uniform.pt`
  - `zj_yici_230426.pt`
  - `zj_erci_230324.pt`

#### 未找到的

在 `inspection-flask_old/` 范围内，**没有找到**下面这些可直接复现实验的关键文件：

- 明确的 `train.py`
- 明确的 `val.py`
- 工服数据集 `data.yaml`
- train/val/test 图片清单
- 数据切分脚本或 split manifest
- 旧版正式评估报告（例如 mAP 报告 json / csv）

另外只看到了一个：

- `inspection-flask_old/weights/test.txt`

但该文件是空文件，**不能提供任何 test split 信息**。

因此当前最严谨的判断是：

> 旧仓库保留下来的是**部署与推理链路**，而不是一份可直接还原训练集切分方法的完整训练工程。

所以如果你问“旧 YOLOv5 当时到底怎么切 train/val/test”，当前这份代码仓库**无法给出可核实的唯一答案**。

---

## 4. 旧版工服检测到底是 fullframe，还是 person-crop？

结论很明确：

> 旧版工服检测主线**不是单纯 fullframe**，也不是极窄的 tight crop，而是**person-guided 的白底保留人体区域输入**。

具体做法来自：

- `test_main_for_cloth.py:add_white_background()`
- `applications/common/hk_custom_threading_plus.py:add_white_background()`

它的逻辑是：

1. 先检测出 `person`；
2. 创建一张与原图同尺寸的白底图；
3. 只把该 `person` 框区域从原图拷贝到白底图；
4. 用这张图去跑工服模型。

这条路线介于两种极端之间：

- 不是直接拿整帧做工服检测；
- 也不是只拿很紧的人体 crop 去做检测；
- 而是**既保留 person 的局部上下文，又最大幅度去掉了背景干扰**。

对当前“小目标工服检测”问题来说，这一点非常关键，因为它说明旧系统是在**输入设计层**先帮模型减难度。

---

## 5. 旧线为什么“看起来准确度高”

基于现有代码证据，我认为旧线准确度观感较好的原因，按可信度排序，更像是下面这些：

### 5.1 第一主因：两阶段 person-guided 检测把搜索空间大幅缩小了

当前人框先出来，再做工服检测，相当于把：

- 大面积背景
- 路面
- 油枪
- 车辆
- 招牌
- 非人体区域

统统先从工服检测的搜索空间里排掉了。

这对于工服这种通常贴在人身上、而且在 fullframe 下可能偏小的目标，非常有利。

### 5.2 第二主因：白底保留人体区域的输入方式，对小目标和复杂背景都更友好

这种输入方式的好处是：

- 比整帧检测更少背景噪声；
- 比 tight crop 更保留人体上下文；
- 对衣服框的定位更稳定；
- 对远景 / 小目标人，只要 person 一阶段能框住，二阶段看到的“有效衣物像素占比”会明显提高。

### 5.3 第三主因：旧线不是一类 `clothes`，而是多类衣物部件

旧逻辑里明确消费：

- `coat`
- `cloth`
- `shirt`

这意味着旧模型未必是在直接学“这个人穿没穿工服”，而更像是在学“这些工服组成件是否存在”。

这种标签设计在某些场景下比单类 `clothes` 更容易学，因为监督更细。

当然，它也有代价：

- 标注成本更高；
- 类间边界更复杂；
- 后处理需要再做规则合并。

### 5.4 第四主因：旧线工服阶段很可能用了更大的模型

从权重体积看，`police_uniform.pt` 非常接近 `yolov5x.pt`。

这说明旧系统在线上工服阶段并不保守，反而可能是：

> 先用 person 阶段缩小搜索空间，再把更大的模型容量留给二阶段工服检测。

因此如果只看最终效果，很容易误以为“YOLOv5 本身更强”，但其实更可能是：

- 路线更有利；
- 模型也更大；
- 规则也更多。

### 5.5 第五主因：旧系统的“准确度”包含规则层收益，不等价于纯检测 AP

旧系统后面还有：

- 是否正式民警的人脸条件
- 衣物框中心是否落入 person 框内
- 违规触发规则

所以旧系统线上“看起来很准”，未必等价于：

> 它的底层 clothes detector 在标准 holdout 上，纯 `mAP50-95` 一定比当前 YOLOv8 fullframe 更高。

这两者不能直接画等号。

---

## 6. 对当前 YOLOv8 工服训练最有借鉴意义的点

这里重点回答：当前 `backend-train-model/` 下的 clothes 训练，最应该借鉴什么。

### 6.1 最该借鉴的是“路线”，不是“版本号”

如果当前问题是：

- fullframe 下工服目标偏小；
- 背景复杂；
- 目标附着在 person 上；

那么第一优先级不是“换回 YOLOv5”，而是：

> 先做 `person-guided clothes` 的对照实验。

但这里必须把 `person-guided clothes` 再拆细一点，否则很容易把两类问题混在一起：

1. **fullframe clothes**
   - 直接整帧做 clothes 检测；
   - 不依赖 person 上游；
   - 这是当前最干净的 clothes baseline。

2. **oracle personcrop clothes**
   - 用 **GT person 框**，或用当前 person 预测后再做**人工快速修框**，来生成 person crop / 白底保留人体区域图；
   - 它的作用不是模拟真实部署，而是先回答一个更基础的问题：
     > 如果 person 框本身是可靠的，`person-guided clothes` 这条路线到底值不值得做？

3. **pred-personcrop clothes**
   - 直接使用当前 person 模型预测框生成 clothes 输入；
   - 这条线最接近真实部署链路；
   - 但它会同时受到 `person recall`、`person 框偏移`、`person 裁剪过紧` 的影响。

因此，当前仓库里已经提过、但还没成为主线的方向：

- `personcrop clothes`

确实比单纯改模型版本更接近旧线真正有效的部分；但在当前阶段，更合理的优先级不是：

> 直接上 `pred-personcrop clothes` 主线。

而是：

> 先用 `oracle personcrop clothes` 或 `oracle white-background person-preserved clothes` 验证路线本身是否成立。

原因是：当前 person 线本身仍然存在 recall 与高 IoU 框质量的瓶颈，如果直接用“当前 person 预测框 -> clothes 训练/评估”，一旦结果不好，就很难判断问题到底来自：

- clothes 路线本身不行；
- 还是 person 上游先把人漏掉了；
- 或者 person 框把衣物关键区域裁坏了。

### 6.2 可以直接借鉴“白底保留人体区域”的输入设计

旧线不是普通 crop，而是：

- 保留与原图同尺寸的 canvas
- 将 person 外区域置白
- 只保留当前人的视觉信息

这对当前 YOLOv8 很值得做一个**单因子对照**。但为了避免被当前 person 上游污染，第一轮更建议这样设计：

1. fullframe clothes
2. oracle tight person crop clothes
3. oracle white-background person-preserved clothes

三条线用**同一份 split / holdout** 对比，能更清楚看出：

- 真正起作用的是缩小背景；
- 还是提高衣物像素占比；
- 还是保留人体上下文。

这里“oracle”非常重要。它意味着：

- 先不要让当前 person 模型质量决定实验成败；
- 先把路线本身验证清楚；
- 只有当 oracle 版本已经能稳定优于 fullframe，才值得继续推进自动化 `pred-personcrop` 版。

### 6.3 当前小目标问题下，person-guided 路线比继续盲目放大 `imgsz` 更值得优先做

旧线给出的经验是：

> 当目标天然附着在人身上时，与其不断放大全图输入尺寸，不如先让衣物检测器“只看人附近”。

原因是：

- 放大全图会同时放大背景和无关区域；
- person-guided 会优先提高衣物相关像素密度；
- 对小目标更友好。

但这里的“优先做”并不等于：

> 现在立刻直接把当前 person 模型预测框当成 clothes 主线输入。

更准确的优先顺序应是：

1. 先验证输入路线本身值不值；
2. 再评估当前 person 上游能不能支撑这条路线；
3. 最后再考虑是否需要更大模型或更大 `imgsz`。

也就是说，当前更值得优先做的是：

- **oracle person-guided 路线验证**；

而不是：

- **直接把 `pred-personcrop clothes` 当作下一条默认主线**。

### 6.4 多类衣物标签值得作为“候选方案”，但不建议直接默认切过去

旧线使用了 `coat / cloth / shirt` 三类衣物部件，这提示一个可能方向：

> 如果当前单类 `clothes` 的漏检集中在“服装款式差异太大、局部特征不稳定”，那可以考虑把标签粒度适当拆细。

但这件事不应直接默认照搬，原因是：

- 当前仓库正式 clothes 线已经稳定在单类 `clothes`；
- 一旦拆类，需要重做标注规范、评估口径和后处理合并；
- 如果现有误差主因其实是小目标像素不足，而不是语义混类，那么拆类未必是第一优先级。

因此更合理的做法是：

- 先做误差复盘；
- 如果确认特定服装组成件经常漏掉，再把“细粒度多类工服”作为候选实验，而不是默认主线。

### 6.5 “更大模型”可以借鉴，但要放在 person-guided 路线之后

旧线很可能在工服阶段用了接近 `yolov5x` 级别的模型。

这说明：

- 更大模型不是不能试；
- 但它在旧线里并不是单独发挥作用，而是和 person-guided 输入一起工作的。

因此当前更合理的借鉴方式是：

1. 先固定路线（例如 personcrop / white-background person-preserved）；
2. 再做 `n -> s -> m` 或更高容量模型的单因子对照；
3. 不要在 fullframe 小目标问题还没拆清楚时，就直接把“换大模型”当第一优先级。

### 6.6 可以借鉴“双阈值思路”，但不要和 mAP 口径混在一起

旧线里同时存在：

- 检测阶段阈值：`conf_thres=0.25`、`iou_thres=0.45`
- 业务配置阈值：`CLOTH_CONF=0.45`

这说明旧线其实区分了两类问题：

1. 模型候选输出怎么保留；
2. 业务最终怎么触发。

对当前 clothes 线的借鉴是：

- `mAP` 评估口径要和业务阈值区分；
- 逐图 FP/FN 复盘时，要额外保留一套接近线上阈值的统计口径。

---

## 7. 当前不宜直接照搬的地方

### 7.1 不宜把“旧线更准”直接归因于 YOLOv5 架构本身

当前代码证据更支持：

- person-guided
- 白底保留人体区域
- 多类衣物标签
- 更大模型
- 规则后处理

共同塑造了旧线的效果。

因此不能简单得出：

> YOLOv5 一定比当前 YOLOv8 clothes 训练方案更强。

### 7.2 不宜照搬未知的旧 split

因为当前旧仓库里**没有保留可核实的 split 文件和 dataset yaml**，所以不能把一个不存在的“旧切分方法”当成当前推荐方案。

当前更稳妥的做法仍然是：

- 继续沿用当前仓库已经显式固化的 split / holdout；
- 确保不同路线对照时只改一个变量。

### 7.3 不宜把旧在线规则链直接等同于当前离线检测 baseline

旧系统最终判断的是：

- 某个正式民警
- 是否有衣物部件框
- 且框中心是否落在人框内

这是“检测 + 业务规则”的复合能力。

而当前 `backend-train-model` 下的 clothes baseline，本质上是：

- 单独评估 clothes detector 的检测能力。

两者不能直接用“线上观感”一比一替代。

### 7.4 不宜一上来就把当前单类 `clothes` 主线改成多类

旧线的 `coat / cloth / shirt` 值得参考，但当前更建议先做：

- person-guided 路线对照；
- 小目标误差复盘；

只有当这些证据都指向“类别粒度不足”时，再考虑拆类。

---

## 8. 对当前 `backend-train-model` 的建议执行顺序

结合旧线经验与当前仓库现状，我建议当前 clothes 线按下面顺序推进：

### 第一步：保留当前 fullframe baseline，不直接推翻

当前正式 baseline 已经固定在：

- `backend-train-model/All-train-model/00_CURRENT_BASELINE/`

先保留它作为统一对照，不直接因为“旧线观感更准”就推翻现有基线。

### 第二步：先对当前 fullframe clothes 的 hard cases 做定向复盘

在是否推进 `person-guided clothes` 之前，先看当前 fullframe clothes 的 hardest cases 到底集中在哪：

- 远景 / 小人
- 复杂背景
- person 与背景颜色相近
- 多人同框、衣物互相干扰
- person 只露出半身 / 侧身

如果 hard cases 的主体并不集中在这些“人相关小目标场景”，那 `person-guided clothes` 的优先级就不应被抬得太高。

### 第三步：把 `oracle person-guided clothes` 提升为最高优先级对照，而不是直接上 `pred-personcrop`

如果复盘确认：当前 clothes 的误差主体确实与“小目标 person 附着目标”高度相关，那么建议新增或优先推进两条 **oracle** 路线：

1. `oracle personcrop clothes`
2. `oracle white-background person-preserved clothes`

这里的 `oracle` 可以通过两种方式得到：

1. 直接使用现有标注中的 person GT 框；
2. 先用当前 best person 模型预测，再对小规模样本做人工快速修框。

这样做的目的不是模拟最终部署，而是把实验问题先收敛成：

> 当 person 框是可靠的，person-guided clothes 到底能不能解决当前 fullframe 小目标瓶颈？

并和当前 fullframe clothes 用**同一份 holdout** 做对照。

### 第四步：先只做“路线单因子”，不要同时改大模型和大尺寸

建议先固定：

- split 不变
- holdout 不变
- 类别定义先不变
- 评估口径不变

只比较：

- fullframe
- oracle personcrop
- oracle white-background person-preserved

否则后面很难知道收益到底来自哪一个变量。

### 第五步：先判断“路线值不值”，再判断“当前 person 能不能撑住”

完成 oracle 对照后，先不要立刻进入大规模自动化，而是先做一个判断：

#### 情况 A：oracle 版本没有明显优于 fullframe

这说明：

- 旧 YOLOv5 线的收益未必主要来自 person-guided 输入；
- 或者当前 clothes 线的主矛盾并不在“整帧看得太杂”；
- 这时就不应该继续把大量精力投入到 `pred-personcrop clothes` 上。

#### 情况 B：oracle 版本明显优于 fullframe

这说明：

> `person-guided clothes` 路线本身是有潜力的，下一步才值得去研究“当前 person 上游会把这个潜力吃掉多少”。

这时再进入：

- `pred-personcrop clothes`
- person 框误差与 clothes 指标损失的关系分析
- 是否需要进一步补强 person 上游

### 第六步：只有在 oracle 版本胜出后，才推进真实 `pred-personcrop clothes`

这一步才是最接近真实部署链路的版本：

1. 用当前 best person 模型自动出框；
2. 自动生成 person crop / 白底保留人体区域图；
3. 训练或评估 clothes；
4. 与 oracle 版本做差值对比。

这时你真正能回答的问题是：

> 当前 clothes 路线的理论收益有多少？其中又有多少被 person 上游的 recall / 框偏移 / 裁剪误差吃掉了？

这个差值非常关键，因为它决定你下一步是：

- 优先继续补强 person；
- 还是继续优化 clothes；
- 还是暂时回到 fullframe。

### 第七步：如果 person-guided 路线胜出，再做模型容量对照

如果 person-guided 方案确实更适合当前工服小目标问题，再继续：

- `n / s / m` 或更高容量模型对照；
- 必要时再评估是否要放大 `imgsz`。

这比现在直接继续在 fullframe 上堆 `imgsz` 更像是从旧线真正学到东西。

### 第八步：只有在误差复盘明确需要时，才考虑细粒度服装标签

如果后续误差分析显示：

- 某些工服款式总是漏；
- 局部特征确实比整体 `clothes` 更有判别性；

再考虑参考旧线的 `coat / cloth / shirt` 思路，做细粒度多类或多任务方案。

### 第九步：如果后续还需要更严格的链路验证，再做端到端线上近似实验

当下面几件事都已经成立时：

1. fullframe baseline 已经固定；
2. oracle person-guided 路线已证明确实有效；
3. pred-personcrop 版本也已完成并量化了上游损失；

这时才值得去做更接近旧系统的端到端实验，例如：

- person -> white-background person-preserved -> clothes -> 规则判断

这样才能把“检测器收益”和“规则链收益”分开看，不至于像旧仓库那样，只留下线上观感，却难以反推到底是哪一层带来了提升。

---

## 9. 最终结论

这次从 `inspection-flask_old` 审查出来的最关键经验，不是“旧 YOLOv5 的训练脚本怎么写”，因为那部分并没有完整保留下来；真正保留下来并且最有价值的，是它的**检测路线设计**：

> 旧系统不是拿整帧硬做工服检测，而是先做人，再把当前人的区域以白底保留的方式送给工服模型；同时它用更细的衣物标签和规则合并，进一步降低了问题难度。

所以对当前 YOLOv8 clothes 训练，最值得优先借鉴的是：

1. **优先做不依赖当前 person 预测质量的 oracle person-guided 工服对照实验**；
2. **优先解决小目标有效像素和背景干扰问题**；
3. **先证明路线值不值，再决定是否值得为它继续补强 person 上游**；
4. **在路线稳定后再谈更大模型、更多类别或更大输入尺寸**。

如果后续 `oracle person-guided clothes` 在统一 holdout 上确实优于当前 fullframe baseline，那么这才算真正把旧 YOLOv5 线里最有价值的经验迁移到了当前仓库；而不是只在“当前 person 上游还不稳定”的条件下，过早把 `pred-personcrop clothes` 当成最终结论。
