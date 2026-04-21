# ROI 标注工具 Labelme 使用说明

本文档用于说明：在**还没有接入摄像头**的当前阶段，如何使用 `Labelme` 对离线图片进行 ROI 标注，以及推荐的安装方式、环境要求和实际操作步骤。

---

## 1. 先说结论

- 你**现在就可以做 ROI**，不需要等摄像头先接进来。
- 当前更推荐的做法是：**从已有离线序列里抽代表帧，用 `Labelme` 先把 ROI 多边形画出来**。
- 对当前项目来说，ROI 更适合画成 **polygon（多边形）**，而不是简单 rectangle（矩形）。
- 建议给 ROI 统一使用一个独立标签名，例如：`roi`。
- 当前仓库默认训练环境是 `yolo_code`，其 Python 版本是 `3.9.25`；但**最新 `Labelme` 已不再支持 Python 3.9**，所以**不要直接把最新 `Labelme` 装进 `yolo_code`**。

---

## 2. Labelme 是什么

`Labelme` 是一个基于 Python 和 Qt 的图形化标注工具，支持：

- polygon（多边形）
- rectangle（矩形）
- circle（圆）
- line（线）
- point（点）

对我们当前这个 ROI 任务来说，最重要的是：

- 它是**可视化 GUI 工具**，不需要你先写代码；
- 它很适合先人工把业务区域画出来；
- 标注结果会保存成 `json`，后续很容易再写脚本提取 ROI 顶点坐标，接到训练配置或预处理流程里。

---

## 3. 当前推荐环境

### 3.1 当前官方支持范围

截至 **2026-04-17**：

- `PyPI` 上最新稳定版是 `labelme 6.1.0`
- 发布时间是 **2026-04-16**
- 官方声明的 Python 要求是：`Python >= 3.10`
- `PyPI` 分类器列出了：`Python 3.10 / 3.11 / 3.12 / 3.13`

也就是说：

- `Python 3.9`：**不满足最新版本要求**
- `Python 3.10+`：满足当前官方支持范围

### 3.2 对本项目最稳妥的版本建议

结合当前项目环境和工具兼容性，**推荐使用 `Python 3.10` 单独创建一个 Labelme 环境**。

原因：

1. `Labelme` 官方已要求 `Python >= 3.10`；
2. `Python 3.10` 已经足够成熟，Windows 下也比较稳；
3. 不会污染你当前训练用的 `yolo_code` 环境；
4. 后续如果你要写小脚本读取 `Labelme json`，也很方便。

如果你已经习惯用更新版本，`Python 3.11` 也可以；但**本文档统一按 `Python 3.10` 讲解**。

> 这里“推荐 `Python 3.10` 作为当前最稳妥版本”是工程建议，不是 Labelme 官方单独写死的唯一版本结论；官方明确给出的硬约束是 `Python >= 3.10`。

---

## 4. 安装前需要什么环境

推荐准备如下环境：

- 操作系统：`Windows`
- Python：`3.10`
- 环境管理器：`Conda`（推荐）或 `uv`
- 安装方式：`pip install labelme` 或 `uv tool install labelme`

对你当前仓库最推荐的路径是：

- **训练继续用 `yolo_code`**
- **ROI 标注单独新建一个 `labelme_py310` 环境**

这样最清晰，也最不容易互相影响。

---

## 5. 推荐安装方法一：Conda 单独建环境

这是**最适合你当前项目**的安装方式。

### 5.1 创建环境

在 `PowerShell` 或 `Anaconda Prompt` 中运行：

```powershell
conda create -n labelme_py310 python=3.10 -y
```

### 5.2 激活环境

```powershell
conda activate labelme_py310
```

### 5.3 升级 pip

```powershell
python -m pip install --upgrade pip
```

### 5.4 安装 Labelme

```powershell
pip install labelme
```

### 5.5 验证安装是否成功

```powershell
python --version
labelme --help
```

你应该至少确认两件事：

- `python --version` 输出的是 `3.10.x`
- `labelme --help` 能正常打印帮助信息

### 5.6 启动 Labelme

```powershell
labelme
```

如果你的终端提示找不到 `labelme`，可以改用：

```powershell
python -m labelme
```

---

## 6. 官方新推荐安装方法二：使用 uv

`Labelme` 官方文档现在更推荐用 `uv` 来安装 Python 和工具，因为它们提到科学计算相关依赖在某些平台上可能更麻烦。

如果你想走官方推荐路径，可以这样做。

### 6.1 安装 uv

先按 `uv` 官方文档完成安装。

安装完成后验证：

```powershell
uv --version
uv run python --version
```

### 6.2 安装 Labelme

```powershell
uv tool install --upgrade labelme
```

### 6.3 启动 Labelme

```powershell
uv tool run labelme
```

或者简写为：

```powershell
uvx labelme
```

### 6.4 什么时候用 uv，什么时候用 conda

如果你只是想：

- 快速装一个独立的标注工具；
- 不想自己管太多 Python 细节；

那么 `uv` 很合适。

但如果你更希望：

- 和你现有项目环境管理习惯一致；
- 明确知道当前在哪个环境里装了什么；

那么还是更推荐你用 **Conda 单独建环境**。

对当前仓库，我仍然建议优先采用 **Conda 方案**。

---

## 7. 为什么不建议直接装进 `yolo_code`

当前仓库约定的训练环境是：

- 环境名：`yolo_code`
- Python 版本：`3.9.25`

而当前最新 `Labelme` 需要：

- `Python >= 3.10`

所以如果你直接在 `yolo_code` 里执行：

```powershell
pip install labelme
```

很可能会遇到类似问题：

- 安装失败
- 提示没有匹配版本
- 或者后续为了兼容而被迫去装旧版 `Labelme`

这会带来两个问题：

1. 你后续看到的界面、命令和当前官方版本可能不一致；
2. 后续再写 ROI 处理脚本时，维护成本会变高。

因此更推荐：

- `yolo_code`：继续负责训练
- `labelme_py310`：专门负责 ROI 标注

---

## 8. ROI 标注前要先准备什么

在真正打开 `Labelme` 之前，建议先整理一批**代表帧**。

### 8.1 建议的选帧方式

对每个固定机位 / 每段序列，先选：

- 入口处有人经过的一帧
- 正常工作场景的一帧
- 光照稍有变化的一帧
- 如果画面会轻微抖动，再补 1～2 帧

通常一条固定序列，先抽 **3～5 张代表帧** 就够开始画 ROI 了。

### 8.2 为什么不用把每一帧都先标完

因为你当前要做的是：

- 先确定“业务有效区域”长什么样；
- 不是先做逐帧目标框标注。

如果摄像头位置基本固定，那么 ROI 在同一条序列里通常是**基本稳定**的。

### 8.3 建议的临时目录组织

当前仓库已经提供自动创建 ROI 标注工作区的命令。推荐先在仓库根目录执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py setup-roi-workdir
```

该命令会按 `person_project_config.json` 中的序列自动创建目录，并为每条序列抽取代表帧：

```text
backend-train-model/person-train-model/roi-work/
├─ <sequence_name>/
│  ├─ frames/
│  │  ├─ 自动抽取的代表帧 1.jpg
│  │  ├─ 自动抽取的代表帧 2.jpg
│  │  └─ 自动抽取的代表帧 3.jpg
│  ├─ roi-json/
│  └─ README.md
├─ README.md
└─ roi_work_manifest.json
```

如果你希望手工整理，也可以保持同样结构，例如：

```text
backend-train-model/person-train-model/roi-work/
├─ D15_20260119203927/
   ├─ frames/
   └─ roi-json/
└─ D02_20260123074836/
   ├─ frames/
   └─ roi-json/
```

这不是硬性要求，但这样后续最清楚。

---

## 9. 如何启动 Labelme 并打开图片

### 9.1 打开软件

如果你用 Conda：

```powershell
conda activate labelme_py310
labelme
```

### 9.2 直接打开某个图片目录

例如：

```powershell
labelme D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\roi-work\D15_20260119203927\frames
```

### 9.3 指定标注输出目录

更推荐直接指定一个单独输出目录，例如：

```powershell
labelme D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\roi-work\D15_20260119203927\frames --output D:\University-Competition\Innovation_Entrepreneurship\MyProgram\yolov8-program\backend-train-model\person-train-model\roi-work\D15_20260119203927\roi-json
```

这样图片和 `json` 会分开，比较干净。

### 9.4 预先限制标签为 `roi`

你可以直接只给它一个标签：

```powershell
labelme D:\path\to\frames --output D:\path\to\roi-json --labels roi
```

这样做的好处是：

- 标注时不容易手误输错标签名；
- 后续脚本读取时也更统一。

---

## 10. 用 Labelme 进行 ROI 标注的详细步骤

下面按最实用的方式来讲。

### 10.1 打开代表帧目录

在 `Labelme` 中打开某一条序列的 `frames` 目录。

打开后你会看到：

- 当前图片显示区域
- 图片列表
- 已标注形状列表
- 菜单栏 / 工具栏

### 10.2 选择 polygon 工具

对于 ROI，推荐使用：

- **Create Polygon**

不推荐默认用 rectangle，原因是加油站业务区域通常不是很规整，矩形很容易：

- 包进太多无关背景；
- 或者切掉真实有效区域的边角。

### 10.3 开始画 ROI

在图上沿着你真正关心的业务区域边界，依次点击多个顶点。

建议你画的是：

- 人可能进入并需要参与后续检测/判断的区域；
- 不是“当前这张图里人在哪里”，而是“业务上哪里算有效区域”。

一个典型思路是：

- 从入口边缘开始；
- 沿地面可通行区边界走；
- 绕开明显无关的远处道路、天空、屋顶、大面积背景；
- 最后闭合成一个多边形。

### 10.4 完成多边形并命名标签

闭合多边形后，软件会要求你输入标签名。

这里统一填写：

```text
roi
```

建议不要写成：

- `ROI`
- `region`
- `person_roi`
- `roi1`

除非你后面明确要做多类别、多区域区分；否则统一用 `roi` 最省事。

### 10.5 调整顶点

如果某个点画歪了，可以进入编辑状态后拖动顶点微调。

建议：

- 顶点不要太少，避免边界过于粗糙；
- 也不要多到几十个点，避免后续维护困难；
- 一般一个 ROI 多边形控制在 **6～12 个点** 比较合适。

### 10.6 保存标注

完成后点击保存。

保存后，`Labelme` 会为当前图片生成一个对应的 `json` 文件。

如果你打开的是：

```text
0001.jpg
```

那么通常会得到类似：

```text
0001.json
```

### 10.7 标下一张图

切到同一序列的下一张代表帧后，继续检查：

- 如果机位基本没变，ROI 应该和上一张非常接近；
- 如果画面略有抖动或裁切变化，就做小幅调整；
- 如果你发现“原来画得太紧 / 太松”，要回头统一修正这一序列的 ROI 口径。

---

## 11. 当前项目里，ROI 应该怎么画

这一部分最重要，决定后面数据集是否真的有用。

### 11.1 ROI 画的是“业务有效区域”，不是“当前有人区域”

不要按“这张图里人站在哪里”去画。

应该按：

- 哪些区域里的人员，后续需要进入 `person -> ROI -> personcrop -> clothes` 链路；
- 哪些区域只是背景、路过区、远处无关区域。

### 11.2 先画宽一点，保守一点

当前还没有正式摄像头接入时，更推荐你先画**保守宽 ROI**：

- 先去掉最明显无关的区域；
- 不要一上来就卡得特别死。

更具体地说：

- **可以先去掉**：远处道路、天空、墙外、几乎不可能成为业务目标的区域；
- **先保留**：人员有可能经过、停留、进入判断链路的边缘区域。

### 11.3 同一固定机位，ROI 口径要一致

如果几张图来自同一个固定视角：

- 尽量保持同一条序列的 ROI 形状和边界口径一致；
- 不要这张图包得很大，下一张图又缩得很小。

### 11.4 如果有多个不连通有效区域

如果一张图里存在多个彼此分离、但都属于有效业务区域的位置，可以：

- 画多个 polygon；
- 标签都使用 `roi`

但要注意：

- 后续脚本必须支持“多 polygon 合并为一个 ROI 区域”的处理逻辑。

如果你当前还没准备写这部分脚本，建议先从**单 ROI 多边形**开始，降低复杂度。

### 11.5 不要把 ROI 画到人框上

ROI 的作用是约束“区域”，不是代替“目标框”。

所以：

- ROI 画的是区域边界；
- 人框依然是后续 `person` 检测的框；
- 这两者不要混成一个东西。

---

## 12. Labelme 标完后会产出什么

`Labelme` 的核心产物是 `json` 文件。

其中最关键的信息通常会包括：

- `imagePath`
- `imageHeight`
- `imageWidth`
- `shapes`

ROI 多边形通常会以这样的结构出现在 `shapes` 里：

```json
{
  "label": "roi",
  "points": [
    [120.5, 860.0],
    [410.0, 650.0],
    [980.0, 640.0],
    [1450.0, 870.0],
    [1460.0, 1070.0],
    [100.0, 1075.0]
  ],
  "group_id": null,
  "shape_type": "polygon",
  "flags": {}
}
```

后续你真正需要拿去做配置或脚本处理的，主要就是：

- `label`
- `points`
- `shape_type`

也就是说，后面如果要把 ROI 接进训练准备流程，本质上就是：

1. 读取这些 `json`
2. 找到 `label == "roi"` 的 polygon
3. 取出 `points`
4. 变成项目配置或预处理脚本可读的格式

---

## 13. 给你一套最实用的当前工作流

如果你现在就想开始干，不要想太复杂，直接按下面做。

### 步骤 1：每条序列先抽 3～5 张代表帧

如果你已经为每张图片都导出了 ROI JSON，就不需要再抽代表帧；代表帧只用于“还没开始画 ROI、且固定机位 ROI 基本稳定”的场景。

例如：

- `D15_20260119203927`
- `D02_20260123074836`

每条序列先抽几张就够。若采用逐图 ROI，则直接使用每张图片对应的 Labelme JSON。

### 步骤 2：每条序列单独建一个 ROI 标注目录

推荐直接运行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py setup-roi-workdir
```

把：

- 图片放到 `frames/`
- `json` 输出到 `roi-json/`

如果已经有现成目录，也可以直接复用。例如当前逐图 ROI JSON 可直接放在 / 读取自：

```text
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\D04_20260123074846\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\D05_20260123074841\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_1\clo\D15_20260123074848\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_2\clo\1\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_2\clo\D15_20260119203927\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_3\clo\D02_20260123070624\roi-json
D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes\group3_3\clo\D02_20260123074836\roi-json
```

此时不用复制到 `backend-train-model/person-train-model/roi-work/`，直接在提取命令里传公共根目录即可：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-json-root D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes --overwrite
```

### 步骤 3：用 `Labelme` 只画一个标签：`roi`

不要一开始设计太多复杂标签。

### 步骤 4：优先画 polygon，先保守宽一点

先把明显无关区域裁掉，不要上来就极限贴边。

### 步骤 5：每条序列先完成一个 ROI 版本

先拿一版可用 ROI，不要一开始追求特别完美。

### 步骤 6：后续再把 ROI json 转成项目配置

当前仓库已经提供转换与数据集生成脚本。完成 `json` 标注后，在仓库根目录执行：

```powershell
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py extract-roi-config --roi-json-root D:\University-Competition\Innovation_Entrepreneurship\MyProgram\all_labels\clothes --overwrite
D:\Miniconda3_python\envs\yolo_code\python.exe backend-train-model\person-train-model\train-code\run_person_flow.py prepare-roi-aware --overwrite
```

默认会生成：

- ROI 配置：`backend-train-model/person-train-model/train-result/working/roi/roi_config.generated.json`
- ROI-aware 数据集：`backend-train-model/person-train-model/train-result/prepared/person_roi_aware/sequence_contiguous/dataset.yaml`

---

## 14. 常见问题

### 14.1 报错：装不上 `labelme`

先检查：

```powershell
python --version
```

如果你看到的是：

```text
Python 3.9.x
```

那大概率就是 Python 太旧了。  
请直接新建 `Python 3.10` 环境，不要在原环境里硬怼。

### 14.2 报错：`labelme` 命令找不到

可以改用：

```powershell
python -m labelme
```

如果这样能启动，说明是命令路径问题，不是软件没装上。

### 14.3 ROI 到底用矩形还是多边形

当前项目更推荐：

- **多边形 ROI**

只有在以下情况下，才可以先用矩形凑合：

- 你的有效区域本来就近似矩形；
- 你只是想快速做一个 very early smoke check。

### 14.4 还没接摄像头，ROI 现在画了有没有用

有用。

你现在画的不是“最终上线 ROI”，而是：

- **训练 ROI / 临时 ROI / 离线 ROI**

它的作用是：

- 先验证 ROI-aware 数据准备和训练路线；
- 先降低全图无关区域对 `person` 检测的干扰；
- 为后续正式接入摄像头后的 ROI 固化做准备。

---

## 15. 当前推荐命令清单

### 15.1 推荐 Conda 安装

```powershell
conda create -n labelme_py310 python=3.10 -y
conda activate labelme_py310
python -m pip install --upgrade pip
pip install labelme
labelme --help
```

### 15.2 打开一个图片目录并输出 json

```powershell
labelme D:\path\to\frames --output D:\path\to\roi-json --labels roi
```

### 15.3 如果 `labelme` 命令不可用

```powershell
python -m labelme D:\path\to\frames --output D:\path\to\roi-json --labels roi
```

### 15.4 如果你想走官方 uv 路线

```powershell
uv tool install --upgrade labelme
uvx labelme
```

---

## 16. 信息来源与更新时间

本文档中的安装和版本结论，核对时间为 **2026-04-17**。

主要参考：

- Labelme 官方安装文档：`https://labelme.io/docs/install-labelme-terminal`
- Labelme 官方入门文档：`https://labelme.io/docs/starter-guide`
- Labelme 官方使用页：`https://labelme.io/docs/annotate-image`
- Labelme `PyPI` 项目页：`https://pypi.org/project/labelme/`

其中：

- “当前最新稳定版 `labelme 6.1.0`、发布时间 `2026-04-16`、要求 `Python >= 3.10`”来自 `PyPI`；
- “官方当前推荐使用 `uv` 安装 Labelme”来自 Labelme 官方安装文档；
- “推荐本项目优先使用独立 `Python 3.10` Conda 环境”是结合当前仓库 `yolo_code = Python 3.9.25` 的工程建议。
