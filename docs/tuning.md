# HiveServer2 小作业性能定位：57.2 s 到 1.6 ~ 3.2 s

> 场景：本仓库 2024 年 6 月零售数据（30 天 × 10 门店）的 Java 看板接口。
> 数据量很小，但接口最初单次响应约 **57.2 s**；定位后开启
> `hive.exec.mode.local.auto`，响应降到 **1.6 ~ 3.2 s**。
>
> 说明：以上两个数字为 README 记录的实训环境结果；本仓库没有可执行的
> Hive 集群，未在编写环境复测。

## 一、现象

- Java 看板的 7 个接口都通过 JDBC 直连 HiveServer2，查询 DWD / DWS 表。
- 单次请求耗时稳定在 57.2 s 左右，与返回行数关系不大：
  DWS 单日查询返回的行数很少，仍然要几十秒。
- 这说明瓶颈不在结果集传输，也不在 Python / 前端渲染，而在 Hive 查询执行链路。

## 二、定位过程

1. 先排除数据量与扫描量
   - ODS 整月 300 个日志文件、4972 笔有效交易，DWD / DWS 都是小表；
   - 如果是扫描或计算瓶颈，耗时应该随数据量明显变化，但实际几乎恒定。

2. 看执行计划
   - 对同一条 DWS 查询执行 `EXPLAIN` / `EXPLAIN EXTENDED`；
   - 即使 `where dt = '20240601'` 只命中一个分区，也会生成完整的 Tez / MapReduce DAG，
     而不是直接返回。

3. 看 HiveServer2 与资源调度日志
   - 时间主要花在查询编译、作业提交、资源申请、容器启动、Tez Session 初始化；
   - 真正读数据的时间占比很小；
   - 这类开销是“固定成本”，数据越少，固定成本占比越高。

4. 做对照实验
   - 同一会话先执行 `SET hive.exec.mode.local.auto=true;`，再执行原 SQL；
   - 响应从 57.2 s 降到 1.6 ~ 3.2 s；
   - 多次执行的波动来自首次编译、元数据缓存、JVM 预热等，数量级稳定。

5. 结论
   - 瓶颈是小数据量下的作业调度开销，不是 SQL 写法或数据倾斜；
   - 让小作业在本地模式执行，绕过 YARN 资源申请和容器启动。

## 三、`hive.exec.mode.local.auto` 原理

- 默认 `false`：每条 SQL 都提交到 Tez / MapReduce，向 YARN 申请容器，
  启动 ApplicationMaster、Executor / Container，再执行。
- 设为 `true` 后，Hive 在提交前估算输入数据量；输入满足阈值时改用本地模式：
  - 在 HiveServer2 所在 JVM 内以本地任务方式执行；
  - 不向 YARN 申请资源，省去调度、排队与容器启动；
  - 对小表 join、单分区聚合这类查询，固定开销明显下降。
- 触发条件由以下参数控制，具体阈值以集群 `hive-site.xml` 为准：
  - `hive.exec.mode.local.auto.inputbytes.max`：输入字节数上限；
  - `hive.exec.mode.local.auto.input.files.max`：输入文件数上限；
  - 两者都满足才会走本地模式。
- 注意：
  - 本地模式只适合小数据量，数据超过阈值会自动回到集群模式，不会拖慢大作业；
  - 它不是万能加速，对真正的大表扫描与 shuffle 没有帮助；
  - 该参数主要作用于 MapReduce 执行路径；若集群使用 Tez，需要确认当前版本是否
    支持该参数，或以实际执行引擎的本地模式 / 会话复用机制为准；
  - 在 HiveServer2 多用户环境下，本地模式会占用服务端 JVM 资源，需要结合并发量评估。

## 四、落地方式

按权限从低到高有三种方式。

1. 会话级（改动最小，适合验证）

```sql
SET hive.exec.mode.local.auto=true;
```

2. JDBC 连接级（本仓库看板场景）

Spring Boot + HikariCP 可以在每个新连接初始化时执行：

```yaml
spring:
  datasource:
    hikari:
      connection-init-sql: SET hive.exec.mode.local.auto=true
```

也可以在 JDBC URL 或 HiveConf 中传入同名参数，具体写法以集群 Hive 版本支持的方式为准。

3. 服务端级

在 HiveServer2 的 `hive-site.xml` 中设置，影响所有会话；需要集群权限，
与其他业务共用时还要评估资源影响。

> 本仓库的 `application.yml` 未提交该参数；上面的配置是按实训环境补充的参考写法。

## 五、开与不开对比

| 配置 | 单接口响应 |
|---|---|
| `hive.exec.mode.local.auto=false`（默认） | 57.2 s |
| `hive.exec.mode.local.auto=true` | 1.6 ~ 3.2 s |

耗时从数十秒级降到秒级，且数据量没有变化，说明瓶颈在作业调度而非数据计算。

## 六、还可以展开讲的优化点

### 1. 分区裁剪

- ODS 按 `dt + store_id` 两级分区，DWD 按 `dt` 分区，DWS 按 `dt` 分区；
- 看板查询固定带 `where dt = ?`，只扫一个分区；
- 月度汇总用 `dt between '20240601' and '20240630'`，不要写
  `substr(dt, 1, 6) = '202406'`，否则分区裁剪失效；
- 只 `select` 需要的列，配合 ORC 列裁剪减少 IO。

### 2. 动态分区

- `hive.exec.dynamic.partition=true` 加 `hive.exec.dynamic.partition.mode=nonstrict`
  才能不指定静态分区值；
- 一条 `INSERT OVERWRITE` 写出整月 30 个 `dt` 分区，避免 30 次小作业；
- 分区列必须是 `SELECT` 的最后一列；
- 关注 `hive.exec.max.dynamic.partitions` 与
  `hive.exec.max.dynamic.partitions.pernode`，分区很多时要调大；
- 动态分区容易产生小文件，可配合合并参数或控制 reducer 数。

### 3. 数据倾斜

- 本数据里 store001 销售额占全区 24.2%（README 结论），按 `store_id` 聚合时
  理论上会有一个 reducer 偏重；
- 但当前数据量只有 4972 笔，倾斜不是 57.2 s 的主因，应先定位再调优；
- 数据量上来后可以用：
  - `hive.groupby.skewindata=true` 做两阶段聚合；
  - 热点 key 加随机前缀 / 两阶段聚合；
  - 小维表走 Map Join（门店维表很小）。

### 4. 小文件与存储

- ODS 有 300 个日志文件，直接扫会产生大量小文件任务；
- DWD / DWS 用 ORC + Snappy，减少 IO；
- 可开启 `hive.merge.mapfiles` / `hive.merge.size.per.task` 做小文件合并；
- 看板只查 DWS 时，优先查汇总层，而不是反复扫 DWD。

### 5. HiveServer2 侧

- 连接池复用连接，避免每次请求重新建连；
- 对无聚合的明细查询，可评估 `hive.fetch.task.conversion`；
- 聚合查询仍然会起作业，不能只靠 fetch 优化；
- 多用户并发时，`local.auto` 会占用服务端资源，需要压测后决定。

## 七、一句话口径

先看执行计划和 HiveServer2 日志，确认时间花在作业提交与容器启动而不是数据扫描；
再用 `hive.exec.mode.local.auto` 做对照，开启后 57.2 s 降到 1.6 ~ 3.2 s，
说明这是小数据量下的作业调度开销。
