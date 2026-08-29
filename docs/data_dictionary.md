# 数据字典

## 原始字段

| 字段 | 类型 | 含义 | 处理说明 |
| --- | --- | --- | --- |
| `Floor` | 整数 | 所在楼层 | 保留为 `floor` |
| `Garden` | 文本 | 小区名称 | 保留为 `garden` |
| `Layout` | 文本 | 户型，如 `3室2厅` | 拆分为 `bedrooms`、`living_rooms` |
| `Price` | 数值 | 房源总价，推测单位为万元 | 保留为 `price_wan` |
| `Region` | 文本 | 区县、片区及截断位置文本 | 提取 `district`、`subdistrict` |
| `Size` | 整数 | 建筑面积，平方米 | 保留为 `size_sqm` |
| `Year` | 整数 | 建成年份 | 保留为 `construction_year` |

## 派生字段

| 字段 | 含义 | 计算方式 |
| --- | --- | --- |
| `bedrooms` | 卧室数 | 从 `Layout` 提取“室”前数字 |
| `living_rooms` | 客厅数 | 从 `Layout` 提取“厅”前数字；缺少“厅”时记为 0 |
| `district` | 区县 | `Region` 第一段 |
| `subdistrict` | 片区 | `Region` 第二段 |
| `building_age_2018` | 截至2018年的房龄 | `2018 - construction_year` |
| `unit_price_yuan_sqm` | 单位面积价格 | `price_wan × 10000 ÷ size_sqm` |

## 已知限制

- 数据没有房源唯一 ID、网页链接或抓取时间，无法确认字段相同的记录是否一定是同一挂牌房源。
- `Region` 第三段疑似被截断，因此不作为可靠的地理层级。
- `Year = 1900` 很可能是未知年份的占位值。
- 数据来源授权及公开再分发条件尚未核实。

