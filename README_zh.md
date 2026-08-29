# 北京二手房价格分析

[![Tests](https://github.com/xvbohan92-ai/beijing-secondhand-housing-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/xvbohan92-ai/beijing-secondhand-housing-analysis/actions/workflows/ci.yml)

本项目将早期主要依赖 SPSS 和在线统计工具的北京二手房研究，重构为可检查的 Python 数据清洗、特征工程、探索分析和模型评估流程。

[English README](README.md) · [已执行 Notebook](notebooks/01_reproducible_analysis.ipynb) · [数据字典](docs/data_dictionary.md)

## 关键结果

- 3,000 条原始有效房源，覆盖北京 17 个地区
- 发现 709 条完全重复记录，去重后使用 2,291 条建模
- 固定 80/20 划分下，LightGBM 测试集 R² 为 0.694、MAE 为 273 万元
- 相同固定划分下，LightGBM 的 MAE 比线性回归低 23.9%
- 增加均值预测基线和确定性的五折交叉验证
- 单元测试、端到端样例测试和 GitHub Actions CI

上述 R² 和 MAE 只对应 `random_state=42` 的一次固定划分。交叉验证均值与标准差见 `reports/model_results/cross_validation_summary.csv`。

五折交叉验证显示，LightGBM 的平均 MAE 最低（252.05 万元），而线性回归的平均 RMSE 更低、平均 R² 更高（0.789 对 0.752）。因此目前不能声称某一个模型在所有指标上都稳定胜出。

## 复现范围

**代码流程可以复现；完整研究结果需要合法获得的源数据。**

由于源数据的公开再分发授权尚未确认，仓库不包含完整 CSV。用于生成当前结果的文件 SHA-256 为：

```text
7f20e81711ea0e25caf27cdb47d72ca8227f7a3872d331613448a514d0e98240
```

仓库提供 12 行合成样例 `data/sample/anjuke_synthetic.csv`，任何人都可以用它运行完整流程和测试。样例只用于验证代码，不能用于解释研究结论。

## 运行

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python src\clean_data.py --input data\sample\anjuke_synthetic.csv
python src\explore.py
python src\model.py
python -m unittest discover -s tests -v
```

若要复现完整结果，请把合法获得且校验值一致的文件放到 `data/raw/anjuke.csv`，再使用清洗脚本的默认输入运行。

## 方法和限制

- 在划分训练集前删除完全重复记录，降低数据泄漏风险。
- 地区使用独热编码，不把行政区编号误作连续变量。
- 比较 DummyRegressor、线性回归和 LightGBM。
- 固定测试集结果与五折交叉验证结果分开报告。
- 结果反映预测相关性，不代表因果关系，也不能作为真实房产估价。
- 数据缺少装修、朝向、地铁距离、挂牌时间等重要变量。

代码采用 [MIT License](LICENSE)；该许可证不适用于第三方原始数据。
