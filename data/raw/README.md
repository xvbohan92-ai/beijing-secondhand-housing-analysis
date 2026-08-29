# 原始数据说明

公开仓库不分发完整的 `anjuke.csv`，因为数据来源的公开再分发授权尚未确认。

在本地复现时，请将合法获得的数据保存为：

```text
data/raw/anjuke.csv
```

文件应包含以下七列，顺序如下：

```text
Floor,Garden,Layout,Price,Region,Size,Year
```

项目使用的本地文件包含3,000条有效房源记录。原 CSV 的异常换行会使 Excel 显示约6,001行，但其中约一半为空白行。

用于生成仓库结果的文件 SHA-256 为：

```text
7f20e81711ea0e25caf27cdb47d72ca8227f7a3872d331613448a514d0e98240
```

可使用 PowerShell 的 `Get-FileHash data/raw/anjuke.csv -Algorithm SHA256` 核对。公开的 `data/sample/anjuke_synthetic.csv` 仅用于验证端到端流程，不代表真实房源，也不能复现论文数值。

代码许可证不授予任何第三方数据的使用或再分发权利。
