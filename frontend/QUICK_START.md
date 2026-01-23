# 快速启动指南

## 安装依赖

```bash
npm install
```

或使用 pnpm（推荐，更快）：

```bash
pnpm install
```

## 开发模式

```bash
npm run dev
```

访问: http://localhost:3080

## 构建生产版本

```bash
npm run build
```

构建产物将输出到 `../backend/static/` 目录

## 预览生产构建

```bash
npm run preview
```

## 当前状态

✅ 已完成：
- 项目架构和配置
- 状态管理（Pinia stores）
- WebSocket 集成
- 基础 UI 组件
- 4个视图页面（Dashboard、PhotoGallery、VideoLibrary、Settings）

⏳ 待完成：
- VideoStream 组件（视频流显示）
- VirtualJoystick 组件（虚拟摇杆）
- PTControl 组件（云台控制）
- 更多控制组件

## 注意事项

1. 目前前端是独立运行的，后端 API 还未实现
2. 可以先运行前端查看 UI 效果
3. WebSocket 连接会失败（显示 "Disconnected from rover"），这是正常的
4. 要完整运行需要启动后端服务器（Flask）

## 技术栈

- Vue 3.4+ (Composition API)
- Vite 5.0+
- Tailwind CSS 3.4+
- Pinia (状态管理)
- Socket.IO Client (WebSocket)
- Axios (HTTP 客户端)
