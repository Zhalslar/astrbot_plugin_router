
<div align="center">

![:name](https://count.getloli.com/@astrbot_plugin_router?name=astrbot_plugin_router&theme=minecraft&padding=6&offset=0&align=top&scale=1&pixelated=1&darkmode=auto)

# astrbot_plugin_router

_✨ 模型路由插件 ✨_  

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![AstrBot](https://img.shields.io/badge/AstrBot-3.4%2B-orange.svg)](https://github.com/Soulter/AstrBot)
[![GitHub](https://img.shields.io/badge/作者-Zhalslar-blue)](https://github.com/Zhalslar)

</div>

## 🤝 介绍

给不同用户路由到不同模型，闲聊者用反应快的模型，开发者用干活强的模型

## 📦 安装

在astrbot的插件市场搜索astrbot_plugin_router，点击安装即可

## ⌨️ 使用说明

| 命令 | 说明 |
|:-----|:-----|
| `查看路由` | 查看自己的路由提供商和模型 |
| `查看路由 @某人` | 查看被提及用户的路由提供商和模型 |
| `添加路由 @某人 序号` | 管理员按 `provider` 列出的 LLM 序号添加或替换用户路由 |
| `删除路由 @某人` | 管理员删除该用户的全部路由条目 |

未匹配启用条目或提供商无效时，指令会说明不路由的原因。提及多个用户时查看第一个用户，唤醒机器人的 @ 不作为查询目标。

先发送 `provider` 查看「LLM Providers」列表，再发送例如 `添加路由 @某人 2`，即可将该用户路由到列表中的第 2 个模型。序号从 1 开始，按执行命令时的模型列表解析，保存的是提供商 ID。

添加会替换该用户已有的全部路由条目并启用新路由；删除也会移除禁用的条目。两条命令均需明确 @ 用户，自动忽略唤醒机器人的 @，提及多个用户时只处理第一个。变更会保存到插件配置并立即生效，无需重新加载插件。

在插件配置页面的「模型路由配置」中添加路由条目：

| 配置项 | 说明 |
|:-------|:-----|
| 用户ID（`user_id`） | 消息发送者的唯一标识，私聊和群聊均按发送者匹配 |
| 启用（`enabled`） | 是否启用此条路由，关闭后跳过该条目 |
| LLM提供商（`provider_id`） | 要使用的对话模型提供商 ID，可在配置页面直接选择 |

配置保存在 `data/config/astrbot_plugin_router_config.json`，结构如下：

```json
{
  "entry_storage": [
    {
      "__template_key": "default",
      "user_id": "123456789",
      "enabled": true,
      "provider_id": "your-provider-id"
    }
  ]
}
```

- 管理员和普通用户使用相同的匹配规则，未匹配的用户沿用 AstrBot 原有的模型选择。
- 同一用户配置多条路由时，使用从上到下第一条已启用的匹配条目。
- 提供商留空、不存在或不是对话模型时，不修改本次消息原有的模型选择。
- 命中有效路由时，该条目优先于本次消息和会话原有的模型选择，但不修改会话配置，也不影响同一群聊中的其他用户。
- 插件只负责选择提供商，不额外发送模型探测请求，也不提供模型故障重试或自动切换功能。

## 👥 贡献指南

- 🌟 Star 这个项目！（点右上角的星星，感谢支持！）
- 🐛 提交 Issue 报告问题
- 💡 提出新功能建议
- 🔧 提交 Pull Request 改进代码

## 📌 注意事项

- 想第一时间得到反馈的可以来作者的插件反馈群（QQ群）：460973561（不点star不给进）
