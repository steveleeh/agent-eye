# Agent-Eye 👁️

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/steveleeh/agent-eye/pulls)

🌐 **[English](README.md)**

**Agent-Eye** 是一个专为 AI 生成代码（Design-to-Code / Figma-to-Code）和自动化 UI 测试场景设计的**智能图像差异与布局偏差分析引擎**。

传统的像素级比对（Pixel-by-Pixel Diffing）在面对微小的对准偏差、字体防锯齿渲染差异或浏览器视口缩放时极其脆弱，容易导致“整页全红误报”。Agent-Eye 借鉴了传统计算机视觉（CV）技术，通过 **结构相似度算法（SSIM）** 结合**形态学组件聚类**，能够像人类测试员一样感知界面的“结构级”错位、缺失与偏差，并以高精度的坐标框（Bounding Box）进行定量数据输出。

---

## ✨ 核心特性

* 🧠 **人眼级结构感知 (SSIM)**：使用结构相似度（SSIM）算法，评估局部纹理、亮度和对比度，天然过滤字体抗锯齿噪声、次像素渲染差异及环境微小色差。
* 📦 **组件级视觉聚类 (Semantic Clustering)**：内置形态学膨胀与边界框合并算法，自动将零散的像素级差异点聚合成直观的“UI组件/区块”边界框。
* 📐 **自动对齐与缩放 (Canvas Alignment)**：支持自动白色边框填充（Padding）与缩放（Resize）模式，完美适配因浏览器滚动条、不同分辨率截图带来的尺寸差异。
* 🎨 **专业级可视化仪表盘 (Technical Dashboard)**：
  * 生成带**严重等级（Critical / Warning / Info）标注**的坐标框截图。
  * 输出三栏合一的暗黑主题分析仪表盘：`[设计稿] | [标注截图与红墨水差异] | [高表现力差异热力图]`。
* 🤖 **AI 自动修复友好 (VLM/LLM Friendly)**：不仅有直观的可视化图片，还能直接输出结构化的 **JSON 差异坐标报告**。AI 智能体（Agent）可直接解析坐标并针对性地自我修正 CSS。

---

## 🛠️ 处理流程 (Pipeline Overview)

```
[设计稿 Mockup] ───┐
                    ├──► [尺寸对齐与预处理] ──► [计算 SSIM 矩阵] ──► [二值化阈值过滤]
[生成截图 Screen] ──┘
                                                                           │
                                                                           ▼
[JSON 数据报告] ◄─── [指标计算与评级] ◄─── [组件边界框聚类] ◄─── [形态学膨胀/膨胀闭合]
       &
[可视化仪表盘]
```

---

## 📦 安装与快速开始 (Installation & Quick Start)

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/steveleeh/agent-eye.git
cd agent-eye

# 安装所需的核心图像处理模块
pip install -r requirements.txt
```

### 2. 运行演示测试 (Run Demo)

项目自带测试图像发生器。只需运行以下命令，即可在 `test_data/` 目录中自动创建一组“模拟设计图”与带有位置偏移、文字拼写错误、色彩变化、内容缺失的“模拟截图”，并自动运行完整的比对闭环：

```bash
python run.py --test
```

运行完成后，您的目录下会生成三个文件：
* `diff_report.json` — 包含所有差异区域 of 偏差坐标和比对得分。
* `diff_annotated.png` — 圈出错误区域并带有严重评级的截图。
* `diff_panel.png` — 三合一的对比看板。

---

## 🖥️ 命令行参数说明 (CLI Usage)

```bash
python run.py --mockup <设计稿路径> --screenshot <截图路径> [选项...]
```

### 可用选项：

| 参数 | 类型 | 默认值 | 描述 |
| :--- | :---: | :---: | :--- |
| `--mockup` | `str` | - | 原始设计稿图像的绝对或相对路径。 |
| `--screenshot`| `str` | - | AI 生成代码运行后的浏览器截图路径。 |
| `--align` | `str` | `pad` | 当图片大小不一致时的对齐模式：`pad`（白色填充，保留比例）或 `resize`（拉伸/压缩）。 |
| `--threshold` | `int` | `30` | 差异敏感度阈值 (0-255)。越低越敏感，默认 `30`（约 12% 差异度）。 |
| `--dilation` | `int` | `18` | 形态学膨胀核心尺寸（像素）。值越大，越倾向于把相邻的错位聚合成一个大框。 |
| `--min-area` | `int` | `35` | 最小噪音过滤面积（像素）。小于此面积的细微斑点会被过滤。 |
| `--merge-dist`| `int` | `20` | 合并相邻边界框的最大距离阈值（像素）。 |
| `--out-panel` | `str` | `diff_panel.png`| 生成的 Side-by-Side 仪表盘的保存路径。 |
| `--out-json` | `str` | `diff_report.json`| 保存差异数据的 JSON 报告路径。 |

---

## 🐍 开发者 programmatic 调用 API (Python API)

您也可以把 Agent-Eye 当作一个标准的 Python 模块直接集成到您自己的测试系统或大模型工作流（Agent Workflow）中：

```python
from agent_eye import ImageCompareEngine, ImageCompareVisualizer
import cv2

# 1. 初始化引擎（配置参数）
engine = ImageCompareEngine(
    threshold=30,      # 相似度差异敏感度
    dilation_size=18,  # 视觉区域合并膨胀率
    min_area=35,       # 过滤微小杂音
    merge_dist=20      # 框体合并最大像素跨度
)

# 2. 传入图片进行对比
results = engine.compare("path/to/design.png", "path/to/screenshot.png", align_method="pad")

# 3. 读取比对总体数据
print(f"整体 SSIM 相似度: {results['overall_similarity'] * 100:.2f}%")
print(f"差异区域总数: {len(results['regions'])}")

# 4. 遍历检测出的视觉偏移区域
for reg in results["regions"]:
    print(f"区域 ID: #{reg['id']} | 严重级别: {reg['severity']}")
    print(f"坐标框 [x, y, w, h]: {reg['box']}")
    print(f"区域内异常率: {reg['mismatch_ratio'] * 100:.1f}%")
    print(f"均值颜色绝对误差 (MAE): {reg['mean_color_diff']:.2f}")

# 5. 生成可视化大图并保存
annotated_img = ImageCompareVisualizer.draw_annotated_image(
    results["img2_aligned"], 
    results["regions"], 
    thresh_mask=results["thresh_mask"]
)
cv2.imwrite("annotated_output.png", annotated_img)
```

---

## 📊 JSON 报告结构示例 (Report Schema)

Agent-Eye 生成的 `diff_report.json` 能够为您的大模型/视觉模型直接提供精准的“Debug 依据”：

```json
{
    "overall_similarity_score": 0.9686,
    "overall_mismatch_percentage": 3.512,
    "regions_detected_count": 5,
    "mismatched_regions": [
        {
            "id": 2,
            "box": [59, 219, 174, 54],
            "mismatch_ratio": 0.4082,
            "mean_color_diff": 55.018,
            "severity": "Critical"
        },
        {
            "id": 3,
            "box": [459, 158, 178, 37],
            "mismatch_ratio": 0.3831,
            "mean_color_diff": 9.413,
            "severity": "Warning"
        }
    ]
}
```

*   `box`: `[x, y, width, height]` 指明了该偏差在对齐图像上的确切位置。
*   `mismatch_ratio`: 该区域内有多少比例的像素发生了实质性偏移（0.0 到 1.0）。
*   `severity`: 严重级别（**Critical / Warning / Info**）。系统根据异常面积 and 颜色漂移值综合计算得出。

---

## 📄 许可证 (License)

本项目采用 [MIT 许可证](LICENSE) 开源。欢迎大家自由使用、修改并提交 Pull Requests！
