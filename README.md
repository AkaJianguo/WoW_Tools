# WoW_Tools

按你提供的结构初始化完成的项目骨架，分为：

- `collector/`：WCL 数据采集与分析区
- `data/`：原始数据、报告与日志目录

## 目录结构

```text
WoW_Tools/
├── .env
├── .gitignore
├── pyproject.toml
├── collector/
│   └── wcl_collector.py
├── data/
│   ├── reports/
│   └── logs/
├── analysis/
│   ├── analyze_321.py
│   └── analyze_sequences.py
├── core/
│   ├── scanner.py
│   ├── logic_engine.py
│   └── execution_engine.py
├── config/
│   └── spells.json
├── tests/
│   └── test_burst.py
└── main.py
```

## 快速试跑

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
./.venv/bin/python3 collector/wcl_collector.py ABCdefG123 --metadata-only
./.venv/bin/python3 analysis/analyze_321.py
```

## WCL 采集前准备

`collector/wcl_collector.py` 现在通过 `.env` 或系统环境变量读取凭证，不再把密钥写在源码里。

先在项目根目录创建 `.env`：

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
cp .env.example .env
```

然后编辑 `.env`，填入你的真实凭证：

```dotenv
WCL_CLIENT_ID=你的 Client ID
WCL_CLIENT_SECRET=你的 Client Secret
```

也可以继续使用 shell 导出环境变量（会覆盖 `.env` 同名变量）：

```bash
./.venv/bin/python3 collector/wcl_collector.py ABCdefG123
```

## WCL 真实采集流程

### 1. 只拉取报告元数据（推荐先看 fight 列表）

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
./.venv/bin/python3 collector/wcl_collector.py ABCdefG123 --metadata-only
```

输出 JSON 中会包含：

- 报告起止时间
- `fight_count`
- 每个 fight 的 `id`、`name`、`start_time`、`end_time`

### 2. 抓取指定 fight 的真实事件

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
./.venv/bin/python3 collector/wcl_collector.py ABCdefG123 --fight-id 3 --data-type Casts
```

### 3. 按时间范围抓取事件

`start-ms` / `end-ms` 是**相对报告起点**的毫秒值。

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
./.venv/bin/python3 collector/wcl_collector.py ABCdefG123 --start-ms 0 --end-ms 600000 --data-type Casts
```

### 4. 大报告分窗抓取

为避免单次事件查询过大，采集器默认按 `10` 分钟窗口分段抓取，并在单窗内继续按 `nextPageTimestamp` 自动翻页。

你也可以手动调大/调小：

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
./.venv/bin/python3 collector/wcl_collector.py ABCdefG123 --window-ms 300000 --max-pages-per-window 200
```

### 5. 分析采集结果

```bash
cd "/Users/wangjianguo/Desktop/WCL/WoW_Tools"
./.venv/bin/python3 collector/wcl_analyzer.py data/reports/report_ABCdefG123_casts_fight-3.json
```

分析输出会汇总：

- 报告代码
- dataType
- fight 数量 / 选中的 fight
- window 数、分页数、事件数
- 是否有分页/窗口警告

如需确认 IDE 使用的是项目虚拟环境解释器，可检查：

```bash
./.venv/bin/python3 --version
/usr/local/bin/python3.13 --version
```

## 说明

- 当前代码是可运行脚手架，便于你后续继续填充真实逻辑。
- `.venv/` 保持原状，没有做手动修改。
- `wcl_collector.py` 现已接入真实的 WCL OAuth + GraphQL 采集流程。
- 默认输出目录是 `data/reports/`，文件名会包含报告代码、dataType 和抓取范围。
- 若报告过大，采集结果中的 `event_fetch.warnings` 会记录窗口分页被截断等提示。

