# @freely-labs/agent-eye 👁️

[![npm version](https://img.shields.io/npm/v/@freely-labs/agent-eye.svg)](https://www.npmjs.com/package/@freely-labs/agent-eye)
[![npm downloads](https://img.shields.io/npm/dm/@freely-labs/agent-eye.svg)](https://www.npmjs.com/package/@freely-labs/agent-eye)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/steveleeh/agent-eye/pulls)

🌐 **[English](README.md)**

**Agent-Eye** (`@freely-labs/agent-eye`) 是一个专为 AI 生成代码（Design-to-Code / Figma-to-Code）和自动化 UI 测试场景设计的**智能图像差异与布局偏差分析引擎**。

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
* 🔒 **零冲突沙箱环境隔离**：npm 包在安装时会自动在 package 内部创建一个独立的 Python 虚拟环境 (`.venv/`)，并将所需的 OpenCV 等库独立装载在内，保持您的全局 Python 环境极其干净！

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

### A. Node.js / 前端开发生态 (`npm`)

如果您使用的是 JavaScript/TypeScript、前端测试框架（Playwright, Puppeteer, Cypress）、或者基于 Node 的 AI 编程助手（如 Cursor, Windsurf, Claude Code）：

#### 1. 全局安装
```bash
npm install -g @freely-labs/agent-eye
```
*(在安装过程中，安装脚本会自动在本地创建 Python 虚拟环境并装载所需的核心依赖，免去手动配置的烦恼)。*

#### 2. 在终端中全局运行
```bash
# 运行内置的合成图像测试套件
agent-eye --test

# 对比您自己的设计稿与截图
agent-eye --mockup mockup.png --screenshot screenshot.png
```

#### 3. 免安装即开即用 (npx)
```bash
npx @freely-labs/agent-eye --test
```

---

### B. Python / AI 开发者生态 (`pip`)

如果您正在构建基于 Python 的 AI 智能体应用（如 LangChain、CrewAI、AutoGPT）或者需要将本工具作为 Python 库进行二次开发：

#### 1. 克隆与本地安装
```bash
# 克隆项目
git clone https://github.com/steveleeh/agent-eye.git
cd agent-eye

# 以可编辑或标准全局方式安装 Python 模块
pip install .
```

#### 2. 全局运行终端指令
```bash
agent-eye --test
```

---

## 🖥️ 命令行参数说明 (CLI Usage)

```bash
agent-eye --mockup <设计稿路径> --screenshot <截图路径> [选项...]
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
*   `severity`: 严重级别（**Critical / Warning / Info**）。系统根据异常面积和颜色漂移值综合计算得出。

---

## 📄 许可证 (License)

本项目采用 [MIT 许可证](LICENSE) 开源。欢迎大家自由使用、修改并提交 Pull Requests！
