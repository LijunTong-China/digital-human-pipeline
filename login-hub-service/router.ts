import { createRouter, createWebHistory } from "/node_modules/.vite/deps/vue-router.js?v=99b192bf";
export var NavKey = /* @__PURE__ */ ((NavKey2) => {
  NavKey2["VIDEOS"] = "videos";
  return NavKey2;
})(NavKey || {});
const Videos = () => import("/src/views/Videos.vue?t=1781051563784");
const CharlesLogs = () => import("/src/views/CharlesLogs.vue");
const VideoProduction = () => import("/src/views/VideoProduction.vue");
const ZoeVideoDetail = () => import("/src/views/ZoeVideoDetail.vue");
const ZoeLogs = () => import("/src/views/ZoeLogs.vue");
const EthanPublishStats = () => import("/src/views/EthanPublishStats.vue");
const EthanVideoBoost = () => import("/src/views/EthanVideoBoost.vue");
const ImageProduction = () => import("/src/views/ImageProduction.vue");
const ImageDetail = () => import("/src/views/ImageDetail.vue");
const XhsProduction = () => import("/src/views/XhsProduction.vue");
const XhsDetail = () => import("/src/views/XhsDetail.vue");
const PublicAccount = () => import("/src/views/PublicAccount.vue");
const ChannelsAccount = () => import("/src/views/ChannelsAccount.vue");
const DouyinAccount = () => import("/src/views/DouyinAccount.vue");
const BilibiliAccount = () => import("/src/views/BilibiliAccount.vue");
const XiaohongshuAccount = () => import("/src/views/XiaohongshuAccount.vue");
const XhsImageAccount = () => import("/src/views/XhsImageAccount.vue");
const WeiboAccount = () => import("/src/views/WeiboAccount.vue");
const LoginQrcode = () => import("/src/views/LoginQrcode.vue");
const LoginCenter = () => import("/src/views/LoginCenter.vue");
const CreatorMonitor = () => import("/src/views/CreatorMonitor.vue");
const SystemStatus = () => import("/src/views/SystemStatus.vue?t=1781613898377");
const Dashboard = () => import("/src/views/Dashboard.vue?t=1785112691957");
const routes = [
  // 默认跳转
  {
    path: "/",
    redirect: "/system-status"
  },
  // ============================================================
  // 内容团队路由
  // ============================================================
  {
    path: "/charles",
    component: Videos,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/charles-logs",
    component: CharlesLogs,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe",
    component: VideoProduction,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe-logs",
    component: ZoeLogs,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe/:id",
    component: ZoeVideoDetail,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe-image",
    component: ImageProduction,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe-image/:id",
    component: ImageDetail,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe-xhs",
    component: XhsProduction,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/zoe-xhs/:id",
    component: XhsDetail,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/public-account",
    component: PublicAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    // 旧链接兼容: /public-account/economics → /public-account (双栏页同时展示两个号)
    path: "/public-account/economics",
    redirect: "/public-account"
  },
  {
    path: "/channels",
    component: ChannelsAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/douyin",
    component: DouyinAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/bilibili",
    component: BilibiliAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/xiaohongshu",
    component: XiaohongshuAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/xiaohongshu-image",
    component: XhsImageAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/weibo",
    component: WeiboAccount,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    // publisher 邮件里链接打开这个页面 (任意平台扫码: channels/douyin/xhs/mp)
    path: "/login-qrcode/:platform",
    component: LoginQrcode,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    // 登录中心 — 顶部导航入口, 所有平台登录态集中管理
    path: "/login",
    component: LoginCenter,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/ethan",
    component: EthanPublishStats,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/ethan-boost",
    component: EthanVideoBoost,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/creators",
    component: CreatorMonitor,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/system-status",
    component: SystemStatus,
    meta: { navKey: "videos" /* VIDEOS */ }
  },
  {
    path: "/dashboard",
    component: Dashboard,
    meta: { navKey: "videos" /* VIDEOS */ }
  }
];
const router = createRouter({
  history: createWebHistory(),
  routes
});
export default router;

//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbImluZGV4LnRzIl0sInNvdXJjZXNDb250ZW50IjpbImltcG9ydCB7IGNyZWF0ZVJvdXRlciwgY3JlYXRlV2ViSGlzdG9yeSB9IGZyb20gJ3Z1ZS1yb3V0ZXInXG5cbi8vIFd1Y2FpTWVkaWE6IOWGheWuueeUn+S6pyAo54Ot54K55oyW5o6YIC8g5Zu+5paHIC8g55+t6KeG6aKRIC8g6K+E6K66IC8g5Yqg54OtKSDljZXkuIDlm6LpmJ/liY3nq68uXG4vLyDkuqTmmJPlm6LpmJ8gKFRyYWRlKiDop4blm74gLyBOYXZLZXkuVFJBREUpIOW3sueJqeeQhui/geenu+WIsCBXdWNhaVRyYWRlIOmhueebriAo56uv5Y+jIDU1ODgvMzQ1NyksXG4vLyDov5novrnkuI3nlZnku7vkvZUgdHJhZGUg5q6L6aq4IOKAlCBoZWFkZXIg5Lmf5Y+q5pi+56S6XCLlhoXlrrnlm6LpmJ9cIuS4gOihjCwg5rKh5pyJ5Zui6Zif5YiH5o2i5LiL5ouJLlxuZXhwb3J0IGVudW0gTmF2S2V5IHtcbiAgVklERU9TID0gJ3ZpZGVvcydcbn1cblxuY29uc3QgVmlkZW9zID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9WaWRlb3MudnVlJylcbmNvbnN0IENoYXJsZXNMb2dzID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9DaGFybGVzTG9ncy52dWUnKVxuY29uc3QgVmlkZW9Qcm9kdWN0aW9uID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9WaWRlb1Byb2R1Y3Rpb24udnVlJylcbmNvbnN0IFpvZVZpZGVvRGV0YWlsID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9ab2VWaWRlb0RldGFpbC52dWUnKVxuY29uc3QgWm9lTG9ncyA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvWm9lTG9ncy52dWUnKVxuY29uc3QgRXRoYW5QdWJsaXNoU3RhdHMgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL0V0aGFuUHVibGlzaFN0YXRzLnZ1ZScpXG5jb25zdCBFdGhhblZpZGVvQm9vc3QgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL0V0aGFuVmlkZW9Cb29zdC52dWUnKVxuY29uc3QgSW1hZ2VQcm9kdWN0aW9uID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9JbWFnZVByb2R1Y3Rpb24udnVlJylcbmNvbnN0IEltYWdlRGV0YWlsID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9JbWFnZURldGFpbC52dWUnKVxuY29uc3QgWGhzUHJvZHVjdGlvbiA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvWGhzUHJvZHVjdGlvbi52dWUnKVxuY29uc3QgWGhzRGV0YWlsID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9YaHNEZXRhaWwudnVlJylcbi8vIOWFrOS8l+WPtyjnu4/mtY7lraYpIOiHquWKqOWMlueci+advyDigJQgS0lNSSDlhajoh6rliqggcGlwZWxpbmUgKOmAiemimCDihpIg5YaZ5paH56ugIOKGkiDphY3lm74pIOeKtuaAgSArIOaOp+WItlxuY29uc3QgUHVibGljQWNjb3VudCA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvUHVibGljQWNjb3VudC52dWUnKVxuLy8g6KeG6aKR5Y+3IChA6Lef6ZmI5Y2a5aOr5a2mQUkpIOKAlCDlgJnpgInmsaDlrqHmoLggKyA4LzEyLzE2IOiHquWKqOWPkeW4g1xuY29uc3QgQ2hhbm5lbHNBY2NvdW50ID0gKCkgPT4gaW1wb3J0KCcuLi92aWV3cy9DaGFubmVsc0FjY291bnQudnVlJylcbi8vIOaKlumfsyAoQOi3n+mZiOWNmuWjq+WtpkFJKSDigJQg5aSN55So6KeG6aKR5Y+35a6h5qC4LCDlkIzmraXmjpLov5sgOC8xMi8xNiDoh6rliqjlj5HluINcbmNvbnN0IERvdXlpbkFjY291bnQgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL0RvdXlpbkFjY291bnQudnVlJylcbi8vIELnq5kgKEDot5/pmYjljZrlo6vlraZBSSkg4oCUIOWkjeeUqOinhumikeWPt+WuoeaguCwgZGFlbW9uIOeLrOeri+aOkiAxMjozMC8xODozMC8yMTowMCDlrprml7bmipXnqL9cbmNvbnN0IEJpbGliaWxpQWNjb3VudCA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvQmlsaWJpbGlBY2NvdW50LnZ1ZScpXG4vLyDlsI/nuqLkuaYgKEDot5/pmYjljZrlo6vlraZBSSkg4oCUIOWkjeeUqOinhumikeWPt+WuoeaguCwg5ZCM5q2l5o6S6L+bIDgvMTIvMTYg6Ieq5Yqo5Y+R5biDICjop4bpopHnrJTorrApXG5jb25zdCBYaWFvaG9uZ3NodUFjY291bnQgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL1hpYW9ob25nc2h1QWNjb3VudC52dWUnKVxuLy8g5bCP57qi5Lmm5Zu+5paHIChA6Lef6ZmI5Y2a5aOr5a2mQUkpIOKAlCDlm77mlofnlJ/miJDlrozoh6rliqjlrqHmoLjpgJrov4csIGRhZW1vbiDmjpIgMTI6MzAvMTg6MDAg5a6a5pe25Y+R5biDXG5jb25zdCBYaHNJbWFnZUFjY291bnQgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL1hoc0ltYWdlQWNjb3VudC52dWUnKVxuLy8g5b6u5Y2aIChA5q+P5aSp5a2m54K55b+D55CG5a2mIC8gQOavj+WkqeWtpueCuee7j+a1juWtpikg4oCUIOS7juWFrOS8l+WPtyByZXdyaXRlIOeyvueCvOaIkOefreW+ruWNmiArIOmHkeWPpeWNoSwg6aKE6KeI5qih5byPICjov5jmsqHmjqXlhaXoh6rliqjlj5HluIMpXG5jb25zdCBXZWlib0FjY291bnQgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL1dlaWJvQWNjb3VudC52dWUnKVxuLy8gcHVibGlzaGVyIOajgOa1i+WIsOeZu+W9leaAgeWkseaViCwg6YKu5Lu26ZO+5o6l5omT5byA6L+Z5Liq6aG16Z2i5omr56CB55m75b2VXG5jb25zdCBMb2dpblFyY29kZSA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvTG9naW5RcmNvZGUudnVlJylcbi8vIOeZu+W9leS4reW/gyDigJQg5omA5pyJ5bmz5Y+w55m75b2V5oCB6ZuG5Lit566h55CGICsg5LiA6ZSu5omT5byA55m75b2V6aG1XG5jb25zdCBMb2dpbkNlbnRlciA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvTG9naW5DZW50ZXIudnVlJylcbi8vIOWvueagh+WNmuS4u+ebkeaOpyDigJQg6YeH6ZuG5oyH5a6a5oqW6Z+z5Y2a5Li76KeG6aKRICsg6Ieq5Yqo5paH5a2X56i/ICjnlKjkuo7mlLnlhpnlj4LogIMpXG5jb25zdCBDcmVhdG9yTW9uaXRvciA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvQ3JlYXRvck1vbml0b3IudnVlJylcbi8vIOezu+e7n+eKtuaAgSDigJQgNCDkuKrlkI7lj7Agc2VydmljZSDlv4Pot7PlgaXlurfluqYgKyDku4rml6Xkuqflh7pcbmNvbnN0IFN5c3RlbVN0YXR1cyA9ICgpID0+IGltcG9ydCgnLi4vdmlld3MvU3lzdGVtU3RhdHVzLnZ1ZScpXG4vLyDmlbDmja7msYfmgLvnnIvmnb8g4oCUIOS4gOihjOS4gOinhumikSwg5qiq5ZCR55yLIDMg5Liq5bmz5Y+wICjlvq7kv6Hop4bpopHlj7cgKyDmipbpn7MgKyDlsI/nuqLkuaYpICsg5Yqg54Ot5o6o6I2QXG5jb25zdCBEYXNoYm9hcmQgPSAoKSA9PiBpbXBvcnQoJy4uL3ZpZXdzL0Rhc2hib2FyZC52dWUnKVxuXG5jb25zdCByb3V0ZXMgPSBbXG4gIC8vIOm7mOiupOi3s+i9rFxuICB7XG4gICAgcGF0aDogJy8nLFxuICAgIHJlZGlyZWN0OiAnL3N5c3RlbS1zdGF0dXMnXG4gIH0sXG4gIFxuICAvLyA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cbiAgLy8g5YaF5a655Zui6Zif6Lev55SxXG4gIC8vID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuICB7XG4gICAgcGF0aDogJy9jaGFybGVzJyxcbiAgICBjb21wb25lbnQ6IFZpZGVvcyxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL2NoYXJsZXMtbG9ncycsXG4gICAgY29tcG9uZW50OiBDaGFybGVzTG9ncyxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL3pvZScsXG4gICAgY29tcG9uZW50OiBWaWRlb1Byb2R1Y3Rpb24sXG4gICAgbWV0YTogeyBuYXZLZXk6IE5hdktleS5WSURFT1MgfVxuICB9LFxuICB7XG4gICAgcGF0aDogJy96b2UtbG9ncycsXG4gICAgY29tcG9uZW50OiBab2VMb2dzLFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvem9lLzppZCcsXG4gICAgY29tcG9uZW50OiBab2VWaWRlb0RldGFpbCxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL3pvZS1pbWFnZScsXG4gICAgY29tcG9uZW50OiBJbWFnZVByb2R1Y3Rpb24sXG4gICAgbWV0YTogeyBuYXZLZXk6IE5hdktleS5WSURFT1MgfVxuICB9LFxuICB7XG4gICAgcGF0aDogJy96b2UtaW1hZ2UvOmlkJyxcbiAgICBjb21wb25lbnQ6IEltYWdlRGV0YWlsLFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvem9lLXhocycsXG4gICAgY29tcG9uZW50OiBYaHNQcm9kdWN0aW9uLFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvem9lLXhocy86aWQnLFxuICAgIGNvbXBvbmVudDogWGhzRGV0YWlsLFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvcHVibGljLWFjY291bnQnLFxuICAgIGNvbXBvbmVudDogUHVibGljQWNjb3VudCxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICAvLyDml6fpk77mjqXlhbzlrrk6IC9wdWJsaWMtYWNjb3VudC9lY29ub21pY3Mg4oaSIC9wdWJsaWMtYWNjb3VudCAo5Y+M5qCP6aG15ZCM5pe25bGV56S65Lik5Liq5Y+3KVxuICAgIHBhdGg6ICcvcHVibGljLWFjY291bnQvZWNvbm9taWNzJyxcbiAgICByZWRpcmVjdDogJy9wdWJsaWMtYWNjb3VudCcsXG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL2NoYW5uZWxzJyxcbiAgICBjb21wb25lbnQ6IENoYW5uZWxzQWNjb3VudCxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL2RvdXlpbicsXG4gICAgY29tcG9uZW50OiBEb3V5aW5BY2NvdW50LFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvYmlsaWJpbGknLFxuICAgIGNvbXBvbmVudDogQmlsaWJpbGlBY2NvdW50LFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcveGlhb2hvbmdzaHUnLFxuICAgIGNvbXBvbmVudDogWGlhb2hvbmdzaHVBY2NvdW50LFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcveGlhb2hvbmdzaHUtaW1hZ2UnLFxuICAgIGNvbXBvbmVudDogWGhzSW1hZ2VBY2NvdW50LFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvd2VpYm8nLFxuICAgIGNvbXBvbmVudDogV2VpYm9BY2NvdW50LFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIC8vIHB1Ymxpc2hlciDpgq7ku7bph4zpk77mjqXmiZPlvIDov5nkuKrpobXpnaIgKOS7u+aEj+W5s+WPsOaJq+eggTogY2hhbm5lbHMvZG91eWluL3hocy9tcClcbiAgICBwYXRoOiAnL2xvZ2luLXFyY29kZS86cGxhdGZvcm0nLFxuICAgIGNvbXBvbmVudDogTG9naW5RcmNvZGUsXG4gICAgbWV0YTogeyBuYXZLZXk6IE5hdktleS5WSURFT1MgfVxuICB9LFxuICB7XG4gICAgLy8g55m75b2V5Lit5b+DIOKAlCDpobbpg6jlr7zoiKrlhaXlj6MsIOaJgOacieW5s+WPsOeZu+W9leaAgembhuS4reeuoeeQhlxuICAgIHBhdGg6ICcvbG9naW4nLFxuICAgIGNvbXBvbmVudDogTG9naW5DZW50ZXIsXG4gICAgbWV0YTogeyBuYXZLZXk6IE5hdktleS5WSURFT1MgfVxuICB9LFxuICB7XG4gICAgcGF0aDogJy9ldGhhbicsXG4gICAgY29tcG9uZW50OiBFdGhhblB1Ymxpc2hTdGF0cyxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL2V0aGFuLWJvb3N0JyxcbiAgICBjb21wb25lbnQ6IEV0aGFuVmlkZW9Cb29zdCxcbiAgICBtZXRhOiB7IG5hdktleTogTmF2S2V5LlZJREVPUyB9XG4gIH0sXG4gIHtcbiAgICBwYXRoOiAnL2NyZWF0b3JzJyxcbiAgICBjb21wb25lbnQ6IENyZWF0b3JNb25pdG9yLFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbiAge1xuICAgIHBhdGg6ICcvc3lzdGVtLXN0YXR1cycsXG4gICAgY29tcG9uZW50OiBTeXN0ZW1TdGF0dXMsXG4gICAgbWV0YTogeyBuYXZLZXk6IE5hdktleS5WSURFT1MgfVxuICB9LFxuICB7XG4gICAgcGF0aDogJy9kYXNoYm9hcmQnLFxuICAgIGNvbXBvbmVudDogRGFzaGJvYXJkLFxuICAgIG1ldGE6IHsgbmF2S2V5OiBOYXZLZXkuVklERU9TIH1cbiAgfSxcbl1cblxuY29uc3Qgcm91dGVyID0gY3JlYXRlUm91dGVyKHtcbiAgaGlzdG9yeTogY3JlYXRlV2ViSGlzdG9y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