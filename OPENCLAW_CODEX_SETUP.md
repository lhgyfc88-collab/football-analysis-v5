# OpenClaw × Codex 接入说明

本方案使用 OpenClaw 官方 `@openclaw/codex` 插件。OpenClaw 负责消息入口、定时任务、审批和通知；Codex 负责在本仓库中读取代码、修改、运行检查并形成可审查的变更。

> 不要把 OpenAI、GitHub、网站或数据供应商的密钥写入本仓库。

## 1. 准备网站工作目录

在运行 OpenClaw Gateway 的电脑或服务器上克隆本仓库：

```bash
git clone https://github.com/lhgyfc88-collab/football-analysis-v5.git
cd football-analysis-v5
```

记录该目录的绝对路径，后续用它替换：

```text
/ABSOLUTE/PATH/football-analysis-v5
```

## 2. 安装并登录官方 Codex harness

```bash
openclaw plugins install @openclaw/codex
openclaw models auth login --provider openai
```

登录在本机交互完成。不要把 OAuth 凭据复制到聊天、文档或 GitHub。

## 3. 合并 OpenClaw 配置

把下面字段**合并**到 `~/.openclaw/openclaw.json`，不要覆盖原有频道、插件、Agent 或安全设置：

```json5
{
  plugins: {
    entries: {
      codex: {
        enabled: true,
        config: {
          // 与本机 Codex Desktop / CLI 共用认证和线程。
          appServer: {
            homeScope: "user",
          },
        },
      },
    },
  },

  agents: {
    defaults: {
      model: "openai/gpt-5.6-sol",
      workspace: "/ABSOLUTE/PATH/football-analysis-v5",
    },
  },

  // 使用自动审查和 workspace-write 级别，而不是无审批全权限。
  tools: {
    exec: {
      mode: "auto",
    },
  },
}
```

若现有配置中使用了 `plugins.allow`，只把 `"codex"` 追加进去，不要用单元素数组覆盖原列表：

```json5
plugins: {
  allow: [/* 原有插件 */, "codex"],
}
```

验证配置：

```bash
openclaw config validate
openclaw doctor --fix
```

Gateway 默认会监听并热加载大多数配置变更。对已经存在的聊天，执行 `/new` 或 `/reset`，让新会话重新解析 harness。

## 4. 在 OpenClaw 中验证并绑定仓库

在只有你本人可使用的 Owner 会话中依次发送：

```text
/status
/codex status
/codex models
/codex bind --cwd /ABSOLUTE/PATH/football-analysis-v5
/codex binding
```

`/status` 应显示：

```text
Runtime: OpenAI Codex
```

首次任务建议发送：

```text
先阅读仓库根目录 AGENTS.md 和 README.md。检查项目状态，不修改 main，不发布内容；只报告数据真实性、部署和自媒体内容流水线目前缺少什么。
```

## 5. 每日自媒体草稿任务

先手动运行一次下面的任务提示，确认输出符合要求：

```text
读取 AGENTS.md，并按 football-site-operator Skill 执行每日内容流程。检查当前数据源和日期，只使用可核实字段。生成：1条20至40秒短视频脚本、1篇图文、3个标题、1个网站引导语和数据不确定性说明。只生成待审核草稿，不自动发布。
```

确认无误后，可创建定时任务。以下示例每天上午 9 点运行；按实际时区、频道和接收目标调整：

```bash
openclaw cron create "0 9 * * *" \
  "读取 AGENTS.md，并按 football-site-operator Skill 执行每日内容流程。检查当前数据源，只用可核实字段，生成短视频脚本、图文、3个标题、网站引导语和不确定性说明。只生成待审核草稿，不自动发布。使用中文。" \
  --name "football-daily-content-draft" \
  --tz "America/Los_Angeles" \
  --session isolated \
  --model "openai/gpt-5.6-sol"
```

频道配置完成后，再为任务添加对应的 `--announce`、`--channel` 和 `--to` 参数，把草稿发送给你审核。

查看和测试任务：

```bash
openclaw cron list
openclaw cron run <jobId> --wait
openclaw cron runs --id <jobId> --limit 20
```

## 6. 让小龙虾调用 Codex 改网站

在已绑定仓库的 Owner 会话中使用这种指令：

```text
请让 Codex 在新分支完成以下任务：为网站增加每日内容草稿导出接口。先阅读 AGENTS.md；不得虚构伤停、战意、赔率或战绩；运行 compileall、Flask 根路由测试和新增测试；完成后展示 diff 和测试结果，不合并 main。
```

建议流程固定为：

```text
OpenClaw 收集任务 → Codex 新建分支并修改 → 自动检查 → 生成 Pull Request → 人工审核 → 合并和部署
```

不要让 OpenClaw 直接修改生产服务器文件，也不要允许它绕过 Git、测试和 Pull Request。

## 7. 安全基线

- Gateway 只放在本机、可信内网或受控 tailnet 后面，不直接裸露到公网。
- Owner 会话才允许绑定、继续、停止或更改 Codex 线程。
- 保持 `tools.exec.mode: "auto"`；不要为日常任务启用 `yolo` 或无审批的全权限模式。
- 自媒体默认只产出草稿。公开发布、付费功能、部署、数据库迁移、删除数据和密钥轮换均需人工确认。
- 第三方 Skill 按不可信代码处理；启用前检查来源和内容。
