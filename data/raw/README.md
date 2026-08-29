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

代码许可证不授予任何第三方数据的使用或再分发权利。

