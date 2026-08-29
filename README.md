# 北京二手房价格分析

本项目使用 Python 复现并改进论文 *Research on Influencing Factors of Second-hand Housing Price in Beijing based on Linear Regression Model* 中的北京二手房价格分析。原研究主要借助 SPSS 和在线统计工具完成；本仓库将数据清洗、变量构造、统计分析和模型评估整理为透明、可重复运行的代码。

## 数据说明

- 数据来源：安居客二手房数据（论文记载采集于 2018 年）
- 本地原始文件位置：`data/raw/anjuke.csv`（不随公开仓库分发）
- 有效观测：3,000 条，7 个原始字段
- 原始 CSV 使用异常的 `CRCRLF` 换行，因此在 Excel 中会夹杂空白行并显示到约第 6001 行；这些空白行不是房源记录
- 原始数据包含 709 条额外的完全重复记录，去重后为 2,291 条唯一记录

原始文件只作输入，不在清洗过程中修改。由于数据来源的公开再分发授权尚未确认，完整 CSV 不包含在公开仓库中。请按照 [数据说明](data/raw/README.md) 将合法获得的数据放入指定目录。

## 项目结构

```text
.
├── data/
│   ├── raw/README.md          # 数据获取和放置说明
│   └── processed/             # 运行脚本后生成
├── docs/data_dictionary.md
├── notebooks/                 # 后续探索性分析
├── reports/figures/           # 后续图表输出
├── src/clean_data.py
├── src/explore.py
├── src/model.py
├── tests/test_clean_data.py
├── requirements.txt
└── README.md
```

## 运行方法

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 将合法获得的 anjuke.csv 放入 data\raw\
python src\clean_data.py
python src\explore.py
python src\model.py
python -m unittest discover -s tests -v
```

清洗脚本会生成：

- `data/processed/housing_clean.csv`：去除完全重复记录后的建模数据
- `data/processed/data_quality_summary.json`：数据规模、缺失值和重复记录摘要
- `reports/figures/`：探索性分析与模型诊断图
- `reports/model_results/`：模型指标、回归系数与特征重要性

## 当前清洗规则

1. 保留原始 CSV，不直接覆盖。
2. 删除七个原始字段均相同的完全重复行。
3. 将 `Layout` 拆分为卧室数和客厅数。
4. 将 `Region` 拆分为区县和片区；不依赖疑似被截断的第三段。
5. 将 `Year` 解释为建成年份，并以采集年份 2018 计算房龄。
6. 将 `Year = 1900` 视为未知年份占位值，不据此计算房龄。
7. 根据总价（万元）和面积计算单位面积价格（元/平方米）。

## 建模原则

- 先去除完全重复记录，再划分训练集和测试集，降低数据泄漏风险。
- `district` 使用独热编码，不把地区编号误当作连续数值。
- 户型拆分为卧室数和客厅数。
- 线性回归和 LightGBM 使用完全相同的训练/测试划分。
- 结果是相关性和预测表现，不解释为因果关系。

## 初步结果

固定随机种子为42，使用去重后的2,291条记录进行80/20训练测试划分：

| 模型 | 测试集 MAE（万元） | 测试集 RMSE（万元） | 测试集 R² |
| --- | ---: | ---: | ---: |
| 线性回归 | 358.77 | 691.09 | 0.670 |
| LightGBM | 273.00 | 664.90 | 0.694 |

LightGBM 略优于线性回归，但误差仍然较大。当前模型是研究和作品集基线，不应作为真实房产估价工具。

![各区县二手房单位面积价格中位数](reports/figures/district_median_unit_price.png)

![测试集实际总价与预测总价](reports/figures/model_predictions.png)

## 后续计划

- 对照论文表格记录复现差异
- 增加交叉验证和稳健性分析
- 完善项目结论与 GitHub 展示页面

## 许可

本仓库中的代码采用 [MIT License](LICENSE)。该许可证不适用于安居客原始数据；数据的权利和使用条件由其原始来源决定。
