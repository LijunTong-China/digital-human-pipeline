import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/views/Dashboard.vue");import { ref, computed, watch, onMounted, onUnmounted } from "/node_modules/.vite/deps/vue.js?v=99b192bf"
import { useRoute, useRouter } from "/node_modules/.vite/deps/vue-router.js?v=99b192bf"
import { API_BASE_URL } from "/src/utils/apiConfig.js"
import AppHeader from "/src/components/AppHeader.vue"


const _sfc_main = {
  __name: 'Dashboard',
  setup(__props, { expose: __expose }) {
  __expose();

const route = useRoute()
const router = useRouter()

const RANGES = [
  { key: 'today', label: '今天' },
  { key: '3d', label: '近 3 天' },
  { key: '7d', label: '近 7 天' },
  { key: '30d', label: '近 30 天' },
  { key: 'all', label: '全部' },
]

const TARGET_PLATFORMS = [
  { key: 'weixin', label: '微信视频号' },
  { key: 'douyin', label: '抖音' },
  { key: 'xiaohongshu', label: '小红书' },
  { key: 'instagram', label: 'Instagram' },
]

const range = ref(route.query.range || '7d')
// 默认按"最近发布"从新到旧排. 用户主诉求是"今天发了什么 / 昨天发了什么", 时间序最直观.
// 想看点赞率/总点赞排, 用顶部下拉切就行.
const sort = ref(route.query.sort || 'published_at')
// onlyDead = 只显示"任一平台被判 dead"的行 (限流嫌疑视频). 前端本地筛选, 不重新请求接口.
const onlyDead = ref(route.query.only_dead === '1')
const rawVideos = ref([])  // 接口返回的原始 videos, 不带 onlyDead 筛选
const videos = ref([])     // 应用 onlyDead 筛选之后实际展示的列表
const pagination = ref(null)
const currentPage = ref(1)
const loading = ref(false)
const errorMsg = ref('')
const boostSummary = ref(null)
// 微信豆 -> 人民币 汇率. 安卓/Web 充值 1元=10豆 (官方价), iOS 充值 1元=7豆 (Apple 抽成).
// 默认 10, 用户主要走 Web 充值.
const coinsPerYuan = ref(10)

const PLATFORM_LABELS = {
  weixin: '微信视频号 (微信豆)',
  douyin: '抖音 (DOU+)',
  xiaohongshu: '小红书 (加热)',
}
function platformLabel(p) { return PLATFORM_LABELS[p] || p }

const PLATFORM_SHORT = {
  weixin: '视频号',
  douyin: '抖音',
  xiaohongshu: '小红书',
}
function platformShort(p) { return PLATFORM_SHORT[p] || p }

// 微信豆 / 抖音 cost_amount 单位都是 元. 微信豆订单页很多 cost=0
// (小额尝试 / 或者订单页没回填), 这里依然按"元"显示, 便于和真实花的钱对齐.
function formatCost(cost, platform) {
  if (cost == null) return '-'
  if (cost === 0) return '¥0'
  return '¥' + Number(cost).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

function setRange(key) {
  range.value = key
  router.replace({ query: { ...route.query, range: key } })
  fetchData(1)
}

async function fetchData(page = 1) {
  loading.value = true
  errorMsg.value = ''
  try {
    const params = new URLSearchParams({
      range: range.value,
      sort: sort.value,
      page: String(page),
      page_size: '20',
    })
    const res = await fetch(`${API_BASE_URL}/api/zhihu/cross-platform-stats?${params}`)
    const json = await res.json()
    if (json.code !== 200 && json.code !== 0) {
      errorMsg.value = `加载失败: ${json.msg || '未知错误'}`
      rawVideos.value = []
      videos.value = []
      pagination.value = null
      return
    }
    rawVideos.value = json.data?.videos || []
    applyOnlyDeadFilter()
    pagination.value = json.data?.pagination || null
    currentPage.value = page
  } catch (e) {
    errorMsg.value = `网络错误: ${e?.message || e}`
  } finally {
    loading.value = false
  }
}

// 应用 onlyDead 筛选. 前端本地筛 (后端不分页时已经返回全部, 重新分页意义不大,
// 走"先按数据排序拿到当页 → 用户切只看限流嫌疑 → 客户端过滤"的链路).
function applyOnlyDeadFilter() {
  if (onlyDead.value) {
    videos.value = rawVideos.value.filter(v =>
      v.has_dead_platform || v.top_boost_level === 'dead'
    )
  } else {
    videos.value = rawVideos.value
  }
}

function toggleOnlyDead() {
  onlyDead.value = !onlyDead.value
  router.replace({
    query: { ...route.query, only_dead: onlyDead.value ? '1' : undefined },
  })
  applyOnlyDeadFilter()
}

function changePage(p) {
  if (pagination.value && p >= 1 && p <= pagination.value.total_pages) {
    fetchData(p)
  }
}

async function fetchBoostSummary() {
  try {
    const params = new URLSearchParams({ coins_per_yuan: String(coinsPerYuan.value) })
    const res = await fetch(`${API_BASE_URL}/api/zhihu/boost-summary?${params}`)
    const json = await res.json()
    if (json.code !== 200 && json.code !== 0) return
    boostSummary.value = json.data
  } catch (e) {
    // 静默失败, 不影响主表格
  }
}

function getPlatformLevelClass(video, platformKey) {
  const lv = video.platforms?.[platformKey]?.boost_score?.level
  return lv ? `cell-${lv}` : 'cell-empty'
}

function topLevelTooltip(v) {
  const reasons = []
  for (const p of TARGET_PLATFORMS) {
    const data = v.platforms?.[p.key]
    if (data?.boost_score?.reason) {
      reasons.push(`${p.label}: ${data.boost_score.reason}`)
    }
  }
  return reasons.join('\n') || '取最高等级'
}

function levelText(lv) {
  if (lv === 'must') return '⭐⭐ 必投'
  if (lv === 'good') return '⭐ 值投'
  if (lv === 'skip') return '✗ 别投'
  if (lv === 'dead') return '🚫 限流'
  return '— 观望'
}

// 用户视频在哪些平台被判 dead — 用于 "部分平台限流" 徽章的 tooltip.
function deadPlatformTooltip(v) {
  const lines = []
  for (const p of TARGET_PLATFORMS) {
    const data = v.platforms?.[p.key]
    if (data?.boost_score?.level === 'dead') {
      lines.push(`${p.label}: ${data.boost_score.reason || '限流嫌疑'}`)
    }
  }
  return lines.join('\n') || '至少一个平台限流嫌疑'
}

// 平台硬信号短文本. forbidden/deleted 已经在 lvl-dead 里红色显示了, 这里不重复.
const PLATFORM_STATUS_TEXT = {
  reviewing: '审核中',
  private: '私密',
  recommended_blocked: '推荐受限',
}
function platformStatusText(s) {
  return PLATFORM_STATUS_TEXT[s] || ''
}
// forbidden/deleted 已经被后端覆盖到 boost_score.level=dead, 这里只展示
// reviewing/private/recommended_blocked (不影响 level 但用户需要知道).
function shouldShowPlatformStatus(platData) {
  const s = platData?.platform_status
  return s && PLATFORM_STATUS_TEXT[s]
}

function boostStatusText(s) {
  const m = { pending: '待提交', submitted: '已提交', active: '加热中', completed: '已完成', failed: '失败' }
  return m[s] || s
}

function formatNum(n) {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function formatPercent(r) {
  if (!r) return '0%'
  return (r * 100).toFixed(1) + '%'
}

function formatDateTime(s) {
  if (!s) return ''
  const d = new Date(s)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day} ${hh}:${mm}`
}

// ============================================================
// 批量加热: 多选 + 弹窗 + batch API + 轮询
// ============================================================

const selectedArticleIds = ref(new Set())  // Set<article_id>, 跨页保留

function toggleRowSelected(articleId, checked) {
  const s = new Set(selectedArticleIds.value)
  if (checked) s.add(articleId)
  else s.delete(articleId)
  selectedArticleIds.value = s
}

function toggleSelectAll(checked) {
  const s = new Set(selectedArticleIds.value)
  for (const v of videos.value) {
    if (checked) s.add(v.article_id)
    else s.delete(v.article_id)
  }
  selectedArticleIds.value = s
}

const isAllSelected = computed(() => {
  if (videos.value.length === 0) return false
  return videos.value.every(v => selectedArticleIds.value.has(v.article_id))
})
const isPartialSelected = computed(() => {
  const some = videos.value.some(v => selectedArticleIds.value.has(v.article_id))
  return some && !isAllSelected.value
})

// 弹窗状态
const batchModalOpen = ref(false)
const batchSubmitting = ref(false)
const batchForm = ref({
  platform: 'weixin',
  amount: 500,
  duration: 24,
  goal: 'follower',
  audienceGroupId: null,
  targetCreators: '',
  audiencePkgName: 'AI技术达人组合',
  submit: false,
  force: false,
})

// 跟后端 enum 对齐
const WEIXIN_DURATIONS = [6, 8, 12, 24]
const DOUYIN_DURATIONS = [2, 6, 12, 18, 24]
const WEIXIN_GOALS = [
  { key: 'smart',    label: '智能加热' },
  { key: 'likes',    label: '点赞数' },
  { key: 'follower', label: '关注数' },
  { key: 'play',     label: '播放数' },
]
const DOUYIN_GOALS = [
  { key: 'follower',    label: '粉丝量' },
  { key: 'interaction', label: '互动量' },
  { key: 'play',        label: '播放量' },
  { key: 'home',        label: '主页访问' },
  { key: 'fans_show',   label: '粉丝展示' },
]

const currentDurations = computed(() =>
  batchForm.value.platform === 'weixin' ? WEIXIN_DURATIONS : DOUYIN_DURATIONS
)
const currentGoals = computed(() =>
  batchForm.value.platform === 'weixin' ? WEIXIN_GOALS : DOUYIN_GOALS
)

// 当前弹窗选中视频 (从 rawVideos 取, 跨页保留)
const selectedVideosForModal = computed(() =>
  rawVideos.value.filter(v => selectedArticleIds.value.has(v.article_id))
)

function getVpId(video, platform) {
  // 后端 get_cross_platform_stats 返回字段叫 publish_id (= video_publish.id), 不是 video_publish_id
  return video.platforms?.[platform]?.publish_id || null
}
function canBoostOnPlatform(video, platform) {
  const vpid = getVpId(video, platform)
  if (!vpid) return false
  // weixin 还要求 object_id 不为空 / 没下架; douyin 要求 published_link 含 aweme_id.
  // 这里前端粗判, 真校验后端做 (rejected 列表会回来).
  const data = video.platforms[platform]
  if (data.platform_status === 'forbidden' || data.platform_status === 'deleted'
      || data.platform_status === 'recommended_blocked') return false
  return true
}

function openBatchBoostModal() {
  if (selectedArticleIds.value.size === 0) return
  // 重置 weixin/douyin 默认值
  if (batchForm.value.platform === 'weixin') {
    batchForm.value.duration = 24
    batchForm.value.goal = 'follower'
  } else {
    batchForm.value.duration = 24
    batchForm.value.goal = 'follower'
  }
  batchModalOpen.value = true
}
function closeBatchModal() {
  batchModalOpen.value = false
}

// 平台切换时同步默认值
function _onPlatformChange() {
  if (batchForm.value.platform === 'weixin') {
    if (!WEIXIN_DURATIONS.includes(batchForm.value.duration)) batchForm.value.duration = 24
    if (!WEIXIN_GOALS.some(g => g.key === batchForm.value.goal)) batchForm.value.goal = 'follower'
  } else {
    if (!DOUYIN_DURATIONS.includes(batchForm.value.duration)) batchForm.value.duration = 24
    if (!DOUYIN_GOALS.some(g => g.key === batchForm.value.goal)) batchForm.value.goal = 'follower'
  }
}
// 平台切换时, 自动校正不合法的 duration/goal 默认值
watch(() => batchForm.value.platform, _onPlatformChange)

// batch 任务进度
const batchJob = ref(null)  // { platform, inserted: [boost_id], rejected: [...], items: [...] }
let batchPollTimer = null

async function submitBatchBoost() {
  if (batchSubmitting.value) return
  if (selectedVideosForModal.value.length === 0) return
  batchSubmitting.value = true
  try {
    const platform = batchForm.value.platform
    const targetCreators = batchForm.value.targetCreators
      ? batchForm.value.targetCreators.split(',').map(s => s.trim()).filter(Boolean)
      : []
    const orders = []
    for (const v of selectedVideosForModal.value) {
      const vpid = getVpId(v, platform)
      if (!vpid) continue  // 前端跳过没在该平台发布的, 后端也会 reject 但不浪费一次 round-trip
      const o = {
        platform,
        video_publish_id: vpid,
        boost_amount: batchForm.value.amount,
        boost_duration: batchForm.value.duration,
        goal: batchForm.value.goal,
        force: batchForm.value.force,
      }
      if (platform === 'weixin') o.target_creators = targetCreators
      else o.audience_pkg_name = batchForm.value.audiencePkgName
      orders.push(o)
    }
    if (orders.length === 0) {
      alert('选中的视频在所选平台都没有发布记录, 无法投放')
      batchSubmitting.value = false
      return
    }
    const res = await fetch(`${API_BASE_URL}/api/zhihu/video-boost/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json; charset=utf-8' },
      body: JSON.stringify({ orders, submit: batchForm.value.submit }),
    })
    const json = await res.json()
    if (json.code !== 200 && json.code !== 0) {
      alert(`提交失败: ${json.msg || '未知错误'}`)
      return
    }
    batchJob.value = {
      platform,
      submit: batchForm.value.submit,
      inserted: json.data.inserted_boost_ids || [],
      rejected: json.data.rejected || [],
      items: (json.data.inserted_boost_ids || []).map(bid => ({
        boost_id: bid, boost_status: 'pending', order_id: null,
        error_message: null, video_title: '加载中...',
      })),
    }
    closeBatchModal()
    selectedArticleIds.value = new Set()  // 清空已选
    startBatchPolling()
  } catch (e) {
    alert(`提交异常: ${e?.message || e}`)
  } finally {
    batchSubmitting.value = false
  }
}

async function pollBatchOnce() {
  if (!batchJob.value || batchJob.value.inserted.length === 0) return
  try {
    const ids = batchJob.value.inserted.join(',')
    const res = await fetch(`${API_BASE_URL}/api/zhihu/video-boost/list?boost_ids=${ids}`)
    const json = await res.json()
    if (json.code !== 200 && json.code !== 0) return
    const items = json.data.items || []
    // 按 inserted 顺序排序展示
    const byId = new Map(items.map(it => [it.boost_id, it]))
    batchJob.value.items = batchJob.value.inserted.map(bid => byId.get(bid) || {
      boost_id: bid, boost_status: 'pending', order_id: null,
      error_message: null, video_title: '?',
    })
    // 全部跑完就停止轮询 (失败/成功/超时 都算 terminal)
    const allDone = batchJob.value.items.every(
      it => it.boost_status === 'submitted' || it.boost_status === 'failed'
            || it.boost_status === 'completed' || it.boost_status === 'cancelled'
            // dry-run 完了状态会停在 pending+error_message='[dry-run OK]...', 也算 terminal
            || (it.boost_status === 'pending' && it.error_message && it.error_message.startsWith('[dry-run'))
    )
    if (allDone) stopBatchPolling()
  } catch (e) {
    // 静默, 下一次再 try
  }
}

function startBatchPolling() {
  stopBatchPolling()
  pollBatchOnce()
  batchPollTimer = setInterval(pollBatchOnce, 4000)
}
function stopBatchPolling() {
  if (batchPollTimer) { clearInterval(batchPollTimer); batchPollTimer = null }
}
function closeBatchJob() {
  stopBatchPolling()
  batchJob.value = null
}

// 投放群 (可复用定向人群): 看板展示 + 建单弹窗选群. 数据源 boost_audience_groups 表.
const audienceGroups = ref([])
async function fetchAudienceGroups() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/zhihu/boost-audience-groups`)
    const json = await res.json()
    if (json.code !== 200 && json.code !== 0) return
    audienceGroups.value = json.data?.groups || []
  } catch (e) {
    // 静默失败, 不影响主流程
  }
}

// 选投放群: 把群成员昵称填进 targetCreators (逗号分隔). 选"自定义"(null) 不动.
function applyAudienceGroup() {
  const gid = batchForm.value.audienceGroupId
  if (!gid) return
  const g = audienceGroups.value.find(x => x.id === gid)
  if (g) batchForm.value.targetCreators = (g.creators || []).join(',')
}

// 排除标题关键词: 标题含这些词的视频禁止加热投放. 数据源 boost_excluded_keywords 表,
// 建单 API (_validate_and_insert_pending) 和 auto_boost 候选过滤都读它, 保存即生效.
const excludedKeywords = ref([])
const newKeyword = ref('')
const kwSaving = ref(false)
async function fetchExcludedKeywords() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/zhihu/boost-excluded-keywords`)
    const json = await res.json()
    if (json.code !== 200 && json.code !== 0) return
    excludedKeywords.value = json.data?.keywords || []
  } catch (e) {
    // 静默失败, 不影响主流程
  }
}
async function addExcludedKeyword() {
  const kw = newKeyword.value.trim()
  if (!kw || kwSaving.value) return
  kwSaving.value = true
  try {
    const res = await fetch(`${API_BASE_URL}/api/zhihu/boost-excluded-keywords`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword: kw }),
    })
    const json = await res.json()
    if (json.code === 200 || json.code === 0) {
      newKeyword.value = ''
      await fetchExcludedKeywords()
    } else {
      alert(json.msg || '添加失败')
    }
  } catch (e) {
    alert(`添加失败: ${e.message || e}`)
  } finally {
    kwSaving.value = false
  }
}
async function removeExcludedKeyword(k) {
  if (!confirm(`删除排除词 "${k.keyword}"? 删除后标题含它的视频又可以被加热投放了`)) return
  try {
    const res = await fetch(`${API_BASE_URL}/api/zhihu/boost-excluded-keywords?id=${k.id}`,
                            { method: 'DELETE' })
    const json = await res.json()
    if (json.code === 200 || json.code === 0) {
      await fetchExcludedKeywords()
    } else {
      alert(json.msg || '删除失败')
    }
  } catch (e) {
    alert(`删除失败: ${e.message || e}`)
  }
}

onMounted(() => {
  fetchData(1)
  fetchBoostSummary()
  fetchAudienceGroups()
  fetchExcludedKeywords()
})
onUnmounted(() => {
  stopBatchPolling()
})

const __returned__ = { route, router, RANGES, TARGET_PLATFORMS, range, sort, onlyDead, rawVideos, videos, pagination, currentPage, loading, errorMsg, boostSummary, coinsPerYuan, PLATFORM_LABELS, platformLabel, PLATFORM_SHORT, platformShort, formatCost, setRange, fetchData, applyOnlyDeadFilter, toggleOnlyDead, changePage, fetchBoostSummary, getPlatformLevelClass, topLevelTooltip, levelText, deadPlatformTooltip, PLATFORM_STATUS_TEXT, platformStatusText, shouldShowPlatformStatus, boostStatusText, formatNum, formatPercent, formatDateTime, selectedArticleIds, toggleRowSelected, toggleSelectAll, isAllSelected, isPartialSelected, batchModalOpen, batchSubmitting, batchForm, WEIXIN_DURATIONS, DOUYIN_DURATIONS, WEIXIN_GOALS, DOUYIN_GOALS, currentDurations, currentGoals, selectedVideosForModal, getVpId, canBoostOnPlatform, openBatchBoostModal, closeBatchModal, _onPlatformChange, batchJob, get batchPollTimer() { return batchPollTimer }, set batchPollTimer(v) { batchPollTimer = v }, submitBatchBoost, pollBatchOnce, startBatchPolling, stopBatchPolling, closeBatchJob, audienceGroups, fetchAudienceGroups, applyAudienceGroup, excludedKeywords, newKeyword, kwSaving, fetchExcludedKeywords, addExcludedKeyword, removeExcludedKeyword, ref, computed, watch, onMounted, onUnmounted, get useRoute() { return useRoute }, get useRouter() { return useRouter }, get API_BASE_URL() { return API_BASE_URL }, AppHeader }
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true })
return __returned__
}

}
import { createVNode as _createVNode, createCommentVNode as _createCommentVNode, createElementVNode as _createElementVNode, renderList as _renderList, Fragment as _Fragment, openBlock as _openBlock, createElementBlock as _createElementBlock, toDisplayString as _toDisplayString, normalizeClass as _normalizeClass, vModelSelect as _vModelSelect, withDirectives as _withDirectives, createTextVNode as _createTextVNode, vModelText as _vModelText, withKeys as _withKeys, resolveComponent as _resolveComponent, withCtx as _withCtx, vModelRadio as _vModelRadio, vModelCheckbox as _vModelCheckbox, withModifiers as _withModifiers, createStaticVNode as _createStaticVNode } from "/node_modules/.vite/deps/vue.js?v=99b192bf"

const _hoisted_1 = { class: "dashboard-page" }
const _hoisted_2 = { class: "page-header" }
const _hoisted_3 = { class: "header-actions" }
const _hoisted_4 = { class: "filter-group" }
const _hoisted_5 = ["onClick"]
const _hoisted_6 = { class: "filter-group" }
const _hoisted_7 = { class: "filter-group" }
const _hoisted_8 = ["disabled"]
const _hoisted_9 = ["disabled", "title"]
const _hoisted_10 = {
  key: 0,
  class: "audience-groups-card"
}
const _hoisted_11 = { class: "ag-list" }
const _hoisted_12 = { class: "ag-item-head" }
const _hoisted_13 = { class: "ag-name" }
const _hoisted_14 = {
  key: 0,
  class: "ag-badge"
}
const _hoisted_15 = { class: "ag-count" }
const _hoisted_16 = { class: "ag-desc" }
const _hoisted_17 = { class: "ag-creators" }
const _hoisted_18 = { class: "excluded-kw-card" }
const _hoisted_19 = { class: "kw-body" }
const _hoisted_20 = { class: "kw-list" }
const _hoisted_21 = ["title", "onClick"]
const _hoisted_22 = {
  key: 0,
  class: "kw-empty"
}
const _hoisted_23 = { class: "kw-add" }
const _hoisted_24 = ["disabled"]
const _hoisted_25 = {
  key: 1,
  class: "boost-summary-card"
}
const _hoisted_26 = { class: "boost-summary-head" }
const _hoisted_27 = { class: "boost-summary-controls" }
const _hoisted_28 = {
  key: 0,
  class: "boost-empty"
}
const _hoisted_29 = {
  key: 1,
  class: "boost-platforms"
}
const _hoisted_30 = { class: "pcard-head" }
const _hoisted_31 = { class: "pcard-name" }
const _hoisted_32 = {
  key: 0,
  class: "pcard-period"
}
const _hoisted_33 = { class: "pcard-grid" }
const _hoisted_34 = { class: "pmetric" }
const _hoisted_35 = { class: "pmetric-num" }
const _hoisted_36 = { class: "pmetric" }
const _hoisted_37 = { class: "pmetric-num" }
const _hoisted_38 = { class: "pmetric pmetric-cost" }
const _hoisted_39 = { class: "pmetric-num" }
const _hoisted_40 = { class: "pmetric-label" }
const _hoisted_41 = {
  key: 0,
  class: "pmetric-sub"
}
const _hoisted_42 = { class: "pmetric" }
const _hoisted_43 = { class: "pmetric-num" }
const _hoisted_44 = { class: "pmetric" }
const _hoisted_45 = { class: "pmetric-num" }
const _hoisted_46 = { class: "pmetric pmetric-follow" }
const _hoisted_47 = { class: "pmetric-num" }
const _hoisted_48 = { class: "pmetric pmetric-roi" }
const _hoisted_49 = { class: "pmetric-num" }
const _hoisted_50 = { class: "pmetric pmetric-roi" }
const _hoisted_51 = { class: "pmetric-num" }
const _hoisted_52 = {
  key: 2,
  class: "boost-top",
  open: ""
}
const _hoisted_53 = { class: "boost-top-table" }
const _hoisted_54 = { class: "td-left td-time" }
const _hoisted_55 = { class: "td-left title-cell" }
const _hoisted_56 = ["href"]
const _hoisted_57 = { key: 1 }
const _hoisted_58 = { class: "cell-cost" }
const _hoisted_59 = {
  key: 0,
  class: "cost-coins"
}
const _hoisted_60 = { class: "cell-follow" }
const _hoisted_61 = { class: "td-left td-meta" }
const _hoisted_62 = {
  key: 3,
  class: "boost-top"
}
const _hoisted_63 = { class: "boost-top-table" }
const _hoisted_64 = { class: "title-cell" }
const _hoisted_65 = ["href"]
const _hoisted_66 = { key: 1 }
const _hoisted_67 = { class: "cell-follow" }
const _hoisted_68 = {
  key: 2,
  class: "error-banner"
}
const _hoisted_69 = {
  key: 3,
  class: "dashboard-table"
}
const _hoisted_70 = { class: "table-row table-head" }
const _hoisted_71 = { class: "col-check" }
const _hoisted_72 = ["checked", ".indeterminate"]
const _hoisted_73 = { class: "col-check" }
const _hoisted_74 = ["checked", "onChange"]
const _hoisted_75 = { class: "col-video" }
const _hoisted_76 = { class: "video-title-row" }
const _hoisted_77 = ["title"]
const _hoisted_78 = ["title"]
const _hoisted_79 = { class: "video-meta" }
const _hoisted_80 = { key: 0 }
const _hoisted_81 = { key: 1 }
const _hoisted_82 = { class: "col-totals" }
const _hoisted_83 = { class: "total-line" }
const _hoisted_84 = { class: "metric" }
const _hoisted_85 = { class: "metric-num" }
const _hoisted_86 = { class: "metric" }
const _hoisted_87 = { class: "metric-num" }
const _hoisted_88 = { class: "total-line" }
const _hoisted_89 = { class: "metric" }
const _hoisted_90 = { class: "metric-num" }
const _hoisted_91 = { class: "metric" }
const _hoisted_92 = { class: "plat-line" }
const _hoisted_93 = ["title"]
const _hoisted_94 = ["title"]
const _hoisted_95 = ["href"]
const _hoisted_96 = { class: "plat-line" }
const _hoisted_97 = { class: "metric" }
const _hoisted_98 = { class: "metric-num" }
const _hoisted_99 = { class: "metric" }
const _hoisted_100 = { class: "metric-num" }
const _hoisted_101 = { class: "plat-line" }
const _hoisted_102 = { class: "metric" }
const _hoisted_103 = { class: "metric-num" }
const _hoisted_104 = { class: "metric" }
const _hoisted_105 = {
  key: 0,
  class: "plat-line"
}
const _hoisted_106 = {
  key: 1,
  class: "plat-empty"
}
const _hoisted_107 = {
  key: 4,
  class: "loading"
}
const _hoisted_108 = {
  key: 5,
  class: "empty"
}
const _hoisted_109 = { class: "modal-card" }
const _hoisted_110 = { class: "modal-head" }
const _hoisted_111 = { class: "modal-body" }
const _hoisted_112 = { class: "modal-row" }
const _hoisted_113 = { class: "radio-inline" }
const _hoisted_114 = { class: "radio-inline" }
const _hoisted_115 = { class: "modal-row" }
const _hoisted_116 = { class: "modal-videos" }
const _hoisted_117 = { class: "modal-video-status" }
const _hoisted_118 = {
  key: 0,
  class: "ok-mark"
}
const _hoisted_119 = {
  key: 1,
  class: "skip-mark",
  title: "该视频在所选平台没发布, batch 跳过"
}
const _hoisted_120 = { class: "modal-video-title" }
const _hoisted_121 = { class: "modal-video-vpid" }
const _hoisted_122 = {
  key: 0,
  class: "modal-empty"
}
const _hoisted_123 = { class: "modal-row" }
const _hoisted_124 = { class: "modal-unit" }
const _hoisted_125 = { class: "modal-row" }
const _hoisted_126 = ["value"]
const _hoisted_127 = { class: "modal-row" }
const _hoisted_128 = ["value"]
const _hoisted_129 = {
  key: 0,
  class: "modal-row"
}
const _hoisted_130 = ["value"]
const _hoisted_131 = {
  key: 1,
  class: "modal-row"
}
const _hoisted_132 = {
  key: 2,
  class: "modal-row"
}
const _hoisted_133 = { class: "modal-row" }
const _hoisted_134 = { class: "check-inline" }
const _hoisted_135 = {
  key: 0,
  class: "modal-warn"
}
const _hoisted_136 = { class: "check-inline" }
const _hoisted_137 = { class: "modal-footer" }
const _hoisted_138 = ["disabled"]
const _hoisted_139 = {
  key: 7,
  class: "batch-job-card"
}
const _hoisted_140 = { class: "batch-job-head" }
const _hoisted_141 = {
  key: 0,
  class: "batch-rejected-num"
}
const _hoisted_142 = { class: "boost-top-table" }
const _hoisted_143 = { class: "td-left title-cell" }
const _hoisted_144 = { class: "td-left" }
const _hoisted_145 = { class: "td-left" }
const _hoisted_146 = { class: "td-left" }
const _hoisted_147 = {
  key: 8,
  class: "pagination"
}
const _hoisted_148 = ["disabled"]
const _hoisted_149 = { class: "page-info" }
const _hoisted_150 = ["disabled"]

function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_router_link = _resolveComponent("router-link")

  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createVNode($setup["AppHeader"]),
    _createElementVNode("div", _hoisted_1, [
      _createCommentVNode(" 顶部筛选条 "),
      _createElementVNode("div", _hoisted_2, [
        _cache[21] || (_cache[21] = _createElementVNode("div", { class: "header-left" }, [
          _createElementVNode("h1", { class: "page-title" }, "数据汇总看板"),
          _createElementVNode("span", { class: "page-subtitle" }, "一行一视频, 横向看 3 个平台 (微信视频号 + 抖音 + 小红书)")
        ], -1 /* CACHED */)),
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("div", _hoisted_4, [
            _cache[18] || (_cache[18] = _createElementVNode("span", { class: "filter-label" }, "范围:", -1 /* CACHED */)),
            (_openBlock(), _createElementBlock(_Fragment, null, _renderList($setup.RANGES, (r) => {
              return _createElementVNode("button", {
                key: r.key,
                class: _normalizeClass(["chip", { active: $setup.range === r.key }]),
                onClick: $event => ($setup.setRange(r.key))
              }, _toDisplayString(r.label), 11 /* TEXT, CLASS, PROPS */, _hoisted_5)
            }), 64 /* STABLE_FRAGMENT */))
          ]),
          _createElementVNode("div", _hoisted_6, [
            _cache[20] || (_cache[20] = _createElementVNode("span", { class: "filter-label" }, "排序:", -1 /* CACHED */)),
            _withDirectives(_createElementVNode("select", {
              "onUpdate:modelValue": _cache[0] || (_cache[0] = $event => (($setup.sort) = $event)),
              onChange: _cache[1] || (_cache[1] = $event => ($setup.fetchData(1))),
              class: "select"
            }, [...(_cache[19] || (_cache[19] = [
              _createStaticVNode("<option value=\"published_at\" data-v-7f773d42>视频号发布时间</option><option value=\"likes_ratio\" data-v-7f773d42>点赞率</option><option value=\"likes\" data-v-7f773d42>总点赞</option><option value=\"views\" data-v-7f773d42>总浏览</option><option value=\"comments\" data-v-7f773d42>总评论</option>", 5)
            ]))], 544 /* NEED_HYDRATION, NEED_PATCH */), [
              [_vModelSelect, $setup.sort]
            ])
          ]),
          _createElementVNode("div", _hoisted_7, [
            _createElementVNode("button", {
              class: _normalizeClass(["chip chip-danger", { active: $setup.onlyDead }]),
              onClick: $setup.toggleOnlyDead,
              title: "只看疑似限流/僵尸视频 (发布 24h+ 但 views 极低)"
            }, " 只看限流嫌疑 ", 2 /* CLASS */)
          ]),
          _createElementVNode("button", {
            class: "btn-secondary",
            disabled: $setup.loading,
            onClick: _cache[2] || (_cache[2] = $event => ($setup.fetchData($setup.currentPage)))
          }, _toDisplayString($setup.loading ? '加载中...' : '刷新'), 9 /* TEXT, PROPS */, _hoisted_8),
          _createElementVNode("button", {
            class: "btn-primary",
            disabled: $setup.selectedArticleIds.size === 0,
            onClick: $setup.openBatchBoostModal,
            title: $setup.selectedArticleIds.size === 0 ? '先勾选要批量加热的视频' : ''
          }, " 批量加热" + _toDisplayString($setup.selectedArticleIds.size > 0 ? ` (${$setup.selectedArticleIds.size} 选中)` : ''), 9 /* TEXT, PROPS */, _hoisted_9)
        ])
      ]),
      _createCommentVNode(" 加热推荐档位说明 (折叠) "),
      _cache[68] || (_cache[68] = _createStaticVNode("<details class=\"rules-card\" data-v-7f773d42><summary data-v-7f773d42>加热推荐规则 (点开看)</summary><div class=\"rules-grid\" data-v-7f773d42><div class=\"rule-row\" data-v-7f773d42><span class=\"lvl-badge lvl-must\" data-v-7f773d42>必投</span> 点赞率 ≥ 5% 或 评论率 ≥ 1% — 推荐投 500 豆</div><div class=\"rule-row\" data-v-7f773d42><span class=\"lvl-badge lvl-good\" data-v-7f773d42>值投</span> 点赞率 ≥ 3% 或 24h 内冷启动给力 (微信≥500/抖音≥2000) — 推荐投 200 豆</div><div class=\"rule-row\" data-v-7f773d42><span class=\"lvl-badge lvl-watch\" data-v-7f773d42>观望</span> 数据中规中矩, 再等等</div><div class=\"rule-row\" data-v-7f773d42><span class=\"lvl-badge lvl-skip\" data-v-7f773d42>别投</span> 浏览量 ≥ 200 但点赞率 &lt; 1% — 别浪费豆</div><div class=\"rule-row\" data-v-7f773d42><span class=\"lvl-badge lvl-dead\" data-v-7f773d42>限流嫌疑</span> 发布 24h+ 但 views 极低 (微信&lt;50 / 抖音&lt;100, 小红书流量抖动大不参与判定) — 复盘选题/标题/敏感词, 别再投钱</div></div></details>", 1)),
      _createCommentVNode(" 视频号投放群 (可复用定向人群): 建单时直接选群, auto_boost 用 ★默认 群 "),
      ($setup.audienceGroups.length > 0)
        ? (_openBlock(), _createElementBlock("div", _hoisted_10, [
            _cache[22] || (_cache[22] = _createElementVNode("div", { class: "ag-head" }, [
              _createElementVNode("h2", { class: "card-title" }, "视频号投放群"),
              _createElementVNode("span", { class: "ag-hint" }, "建好可复用: 批量加热弹窗里选\"投放群\"即可, 自动投放用 ★默认 群")
            ], -1 /* CACHED */)),
            _createElementVNode("div", _hoisted_11, [
              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.audienceGroups, (g) => {
                return (_openBlock(), _createElementBlock("div", {
                  key: g.id,
                  class: _normalizeClass(["ag-item", { 'ag-default': g.is_default }])
                }, [
                  _createElementVNode("div", _hoisted_12, [
                    _createElementVNode("span", _hoisted_13, _toDisplayString(g.name), 1 /* TEXT */),
                    (g.is_default)
                      ? (_openBlock(), _createElementBlock("span", _hoisted_14, "★ 自动投放默认"))
                      : _createCommentVNode("v-if", true),
                    _createElementVNode("span", _hoisted_15, _toDisplayString(g.creator_count) + " 人", 1 /* TEXT */)
                  ]),
                  _createElementVNode("div", _hoisted_16, _toDisplayString(g.description), 1 /* TEXT */),
                  _createElementVNode("div", _hoisted_17, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList(g.creators, (c) => {
                      return (_openBlock(), _createElementBlock("span", {
                        key: c,
                        class: "ag-creator"
                      }, _toDisplayString(c), 1 /* TEXT */))
                    }), 128 /* KEYED_FRAGMENT */))
                  ])
                ], 2 /* CLASS */))
              }), 128 /* KEYED_FRAGMENT */))
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 排除标题关键词: 标题含这些词的视频禁止加热投放 (建单拒单 + 自动投放跳过) "),
      _createElementVNode("div", _hoisted_18, [
        _cache[23] || (_cache[23] = _createElementVNode("div", { class: "ag-head" }, [
          _createElementVNode("h2", { class: "card-title" }, "排除标题关键词"),
          _createElementVNode("span", { class: "ag-hint" }, "标题含这些词的视频禁止加热投放: 批量/自动建单直接拒, 保存后立刻生效")
        ], -1 /* CACHED */)),
        _createElementVNode("div", _hoisted_19, [
          _createElementVNode("div", _hoisted_20, [
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.excludedKeywords, (k) => {
              return (_openBlock(), _createElementBlock("span", {
                key: k.id,
                class: "kw-chip"
              }, [
                _createTextVNode(_toDisplayString(k.keyword) + " ", 1 /* TEXT */),
                _createElementVNode("button", {
                  class: "kw-del",
                  title: `删除 ${k.keyword}`,
                  onClick: $event => ($setup.removeExcludedKeyword(k))
                }, "×", 8 /* PROPS */, _hoisted_21)
              ]))
            }), 128 /* KEYED_FRAGMENT */)),
            ($setup.excludedKeywords.length === 0)
              ? (_openBlock(), _createElementBlock("span", _hoisted_22, "暂无排除词"))
              : _createCommentVNode("v-if", true)
          ]),
          _createElementVNode("div", _hoisted_23, [
            _withDirectives(_createElementVNode("input", {
              type: "text",
              "onUpdate:modelValue": _cache[3] || (_cache[3] = $event => (($setup.newKeyword) = $event)),
              maxlength: "50",
              placeholder: "添加排除词, 如: 京东方",
              onKeyup: _withKeys($setup.addExcludedKeyword, ["enter"])
            }, null, 544 /* NEED_HYDRATION, NEED_PATCH */), [
              [_vModelText, $setup.newKeyword]
            ]),
            _createElementVNode("button", {
              class: "btn-secondary",
              disabled: !$setup.newKeyword.trim() || $setup.kwSaving,
              onClick: $setup.addExcludedKeyword
            }, _toDisplayString($setup.kwSaving ? '保存中...' : '添加'), 9 /* TEXT, PROPS */, _hoisted_24)
          ])
        ])
      ]),
      _createCommentVNode(" 投放历史性价比卡片 "),
      ($setup.boostSummary)
        ? (_openBlock(), _createElementBlock("div", _hoisted_25, [
            _createElementVNode("div", _hoisted_26, [
              _cache[26] || (_cache[26] = _createElementVNode("h2", { class: "card-title" }, "投放历史性价比", -1 /* CACHED */)),
              _createElementVNode("div", _hoisted_27, [
                _cache[25] || (_cache[25] = _createElementVNode("span", { class: "boost-rate-label" }, "微信豆汇率:", -1 /* CACHED */)),
                _withDirectives(_createElementVNode("select", {
                  "onUpdate:modelValue": _cache[4] || (_cache[4] = $event => (($setup.coinsPerYuan) = $event)),
                  onChange: $setup.fetchBoostSummary,
                  class: "select-mini"
                }, [...(_cache[24] || (_cache[24] = [
                  _createElementVNode("option", { value: 10 }, "安卓/Web: 1元 = 10豆 (推荐)", -1 /* CACHED */),
                  _createElementVNode("option", { value: 7 }, "iOS: 1元 = 7豆", -1 /* CACHED */)
                ]))], 544 /* NEED_HYDRATION, NEED_PATCH */), [
                  [
                    _vModelSelect,
                    $setup.coinsPerYuan,
                    void 0,
                    { number: true }
                  ]
                ])
              ])
            ]),
            _cache[39] || (_cache[39] = _createElementVNode("div", { class: "card-hint" }, " 数据源: 各平台订单管理页 scrape 回灌. 微信豆 ÷ 汇率 = 真实人民币花费. ", -1 /* CACHED */)),
            _createCommentVNode(" 注意: 后台同步加热订单时遇到登录失效, 不再在看板上显示 banner.\n           daemon 检测到登录态丢了会直接发邮件提醒 (附二维码截图, 6h 去重),\n           见 wucai_videos5/zoe/quant/auto_comment_reply.py::_maybe_sync_boost_orders. "),
            _createCommentVNode(" 视频号待支付订单不再在看板上展示扫码入口: 批量建好后直接邮件通知,\n           用户登录视频号助手订单页扫码付款 (见 auto_boost_weixin._send_summary_email). "),
            ($setup.boostSummary.platform_summary.length === 0)
              ? (_openBlock(), _createElementBlock("div", _hoisted_28, [...(_cache[27] || (_cache[27] = [
                  _createTextVNode(" 暂无投放历史. 跑一次: ", -1 /* CACHED */),
                  _createElementVNode("code", null, "python wucai_videos5/ethan/weixin_boost_history_importer.py", -1 /* CACHED */),
                  _createTextVNode(" 把微信视频号订单页抓回来. ", -1 /* CACHED */)
                ]))]))
              : (_openBlock(), _createElementBlock("div", _hoisted_29, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.boostSummary.platform_summary, (ps) => {
                    return (_openBlock(), _createElementBlock("div", {
                      key: ps.platform,
                      class: "boost-pcard"
                    }, [
                      _createElementVNode("div", _hoisted_30, [
                        _createElementVNode("span", _hoisted_31, _toDisplayString($setup.platformLabel(ps.platform)), 1 /* TEXT */),
                        (ps.first_boost_at)
                          ? (_openBlock(), _createElementBlock("span", _hoisted_32, _toDisplayString(ps.first_boost_at) + " ~ " + _toDisplayString(ps.last_boost_at), 1 /* TEXT */))
                          : _createCommentVNode("v-if", true)
                      ]),
                      _createElementVNode("div", _hoisted_33, [
                        _createElementVNode("div", _hoisted_34, [
                          _createElementVNode("div", _hoisted_35, _toDisplayString(ps.order_count), 1 /* TEXT */),
                          _cache[28] || (_cache[28] = _createElementVNode("div", { class: "pmetric-label" }, "投放单数", -1 /* CACHED */))
                        ]),
                        _createElementVNode("div", _hoisted_36, [
                          _createElementVNode("div", _hoisted_37, _toDisplayString(ps.video_count), 1 /* TEXT */),
                          _cache[29] || (_cache[29] = _createElementVNode("div", { class: "pmetric-label" }, "投放视频数", -1 /* CACHED */))
                        ]),
                        _createElementVNode("div", _hoisted_38, [
                          _createElementVNode("div", _hoisted_39, _toDisplayString($setup.formatCost(ps.total_cost, ps.platform)), 1 /* TEXT */),
                          _createElementVNode("div", _hoisted_40, [
                            _cache[30] || (_cache[30] = _createTextVNode(" 累计花费 ", -1 /* CACHED */)),
                            (ps.platform === 'weixin' && ps.total_cost_coins != null)
                              ? (_openBlock(), _createElementBlock("span", _hoisted_41, "(" + _toDisplayString($setup.formatNum(ps.total_cost_coins)) + " 豆)", 1 /* TEXT */))
                              : _createCommentVNode("v-if", true)
                          ])
                        ]),
                        _createElementVNode("div", _hoisted_42, [
                          _createElementVNode("div", _hoisted_43, _toDisplayString($setup.formatNum(ps.total_play)), 1 /* TEXT */),
                          _cache[31] || (_cache[31] = _createElementVNode("div", { class: "pmetric-label" }, "总播放", -1 /* CACHED */))
                        ]),
                        _createElementVNode("div", _hoisted_44, [
                          _createElementVNode("div", _hoisted_45, _toDisplayString($setup.formatNum(ps.total_like)), 1 /* TEXT */),
                          _cache[32] || (_cache[32] = _createElementVNode("div", { class: "pmetric-label" }, "总点赞", -1 /* CACHED */))
                        ]),
                        _createElementVNode("div", _hoisted_46, [
                          _createElementVNode("div", _hoisted_47, _toDisplayString($setup.formatNum(ps.total_follow)), 1 /* TEXT */),
                          _cache[33] || (_cache[33] = _createElementVNode("div", { class: "pmetric-label" }, "涨粉", -1 /* CACHED */))
                        ]),
                        _createElementVNode("div", _hoisted_48, [
                          _createElementVNode("div", _hoisted_49, _toDisplayString(ps.cost_per_follow != null ? '¥' + ps.cost_per_follow : '-'), 1 /* TEXT */),
                          _cache[34] || (_cache[34] = _createElementVNode("div", { class: "pmetric-label" }, "每涨 1 粉成本", -1 /* CACHED */))
                        ]),
                        _createElementVNode("div", _hoisted_50, [
                          _createElementVNode("div", _hoisted_51, _toDisplayString(ps.cost_per_like != null ? '¥' + ps.cost_per_like : '-'), 1 /* TEXT */),
                          _cache[35] || (_cache[35] = _createElementVNode("div", { class: "pmetric-label" }, "每个赞成本", -1 /* CACHED */))
                        ])
                      ])
                    ]))
                  }), 128 /* KEYED_FRAGMENT */))
                ])),
            _createCommentVNode(" 最近 N 天订单明细 (默认展开, 因为这是\"昨天投了什么 现在跑得怎么样\"主诉求) "),
            ($setup.boostSummary.recent_orders && $setup.boostSummary.recent_orders.length > 0)
              ? (_openBlock(), _createElementBlock("details", _hoisted_52, [
                  _createElementVNode("summary", null, " 最近 " + _toDisplayString($setup.boostSummary.recent_days || 7) + " 天投放明细 (" + _toDisplayString($setup.boostSummary.recent_orders.length) + " 单) — 看 active 单实时进度 ", 1 /* TEXT */),
                  _createElementVNode("table", _hoisted_53, [
                    _cache[36] || (_cache[36] = _createElementVNode("thead", null, [
                      _createElementVNode("tr", null, [
                        _createElementVNode("th", { class: "th-left" }, "投放时间"),
                        _createElementVNode("th", null, "平台"),
                        _createElementVNode("th", null, "状态"),
                        _createElementVNode("th", { class: "th-left" }, "视频"),
                        _createElementVNode("th", null, "已花"),
                        _createElementVNode("th", null, "播放"),
                        _createElementVNode("th", null, "赞"),
                        _createElementVNode("th", null, "评"),
                        _createElementVNode("th", null, "粉"),
                        _createElementVNode("th", null, "单粉成本"),
                        _createElementVNode("th", { class: "th-left" }, "数据更新")
                      ])
                    ], -1 /* CACHED */)),
                    _createElementVNode("tbody", null, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.boostSummary.recent_orders, (o) => {
                        return (_openBlock(), _createElementBlock("tr", {
                          key: o.boost_id,
                          class: _normalizeClass(['order-row', 'order-' + o.boost_status])
                        }, [
                          _createElementVNode("td", _hoisted_54, _toDisplayString(o.boost_started_at || '-'), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString($setup.platformShort(o.platform)), 1 /* TEXT */),
                          _createElementVNode("td", null, [
                            _createElementVNode("span", {
                              class: _normalizeClass(["boost-tag", 'boost-' + o.boost_status])
                            }, _toDisplayString($setup.boostStatusText(o.boost_status)), 3 /* TEXT, CLASS */)
                          ]),
                          _createElementVNode("td", _hoisted_55, [
                            (o.video_url)
                              ? (_openBlock(), _createElementBlock("a", {
                                  key: 0,
                                  href: o.video_url,
                                  target: "_blank"
                                }, _toDisplayString(o.video_title || '(无标题)'), 9 /* TEXT, PROPS */, _hoisted_56))
                              : (_openBlock(), _createElementBlock("span", _hoisted_57, _toDisplayString(o.video_title || '(无标题)'), 1 /* TEXT */))
                          ]),
                          _createElementVNode("td", _hoisted_58, [
                            _createTextVNode(_toDisplayString($setup.formatCost(o.cost_amount, o.platform)) + " ", 1 /* TEXT */),
                            (o.platform === 'weixin' && o.cost_coins != null)
                              ? (_openBlock(), _createElementBlock("span", _hoisted_59, " (" + _toDisplayString($setup.formatNum(o.cost_coins)) + " 豆) ", 1 /* TEXT */))
                              : _createCommentVNode("v-if", true)
                          ]),
                          _createElementVNode("td", null, _toDisplayString($setup.formatNum(o.play_count)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString($setup.formatNum(o.like_count)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString($setup.formatNum(o.comment_count)), 1 /* TEXT */),
                          _createElementVNode("td", _hoisted_60, _toDisplayString($setup.formatNum(o.follow_count)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString(o.cost_per_follow != null ? '¥' + o.cost_per_follow : '-'), 1 /* TEXT */),
                          _createElementVNode("td", _hoisted_61, _toDisplayString(o.stats_updated_at || '-'), 1 /* TEXT */)
                        ], 2 /* CLASS */))
                      }), 128 /* KEYED_FRAGMENT */))
                    ])
                  ])
                ]))
              : _createCommentVNode("v-if", true),
            ($setup.boostSummary.top_videos_by_follow_aggregated.length > 0)
              ? (_openBlock(), _createElementBlock("details", _hoisted_62, [
                  _cache[38] || (_cache[38] = _createElementVNode("summary", null, "涨粉 Top 20 视频 (累计) — 看看哪些视频值得继续投", -1 /* CACHED */)),
                  _createElementVNode("table", _hoisted_63, [
                    _cache[37] || (_cache[37] = _createElementVNode("thead", null, [
                      _createElementVNode("tr", null, [
                        _createElementVNode("th", null, "视频"),
                        _createElementVNode("th", null, "平台"),
                        _createElementVNode("th", null, "投放次数"),
                        _createElementVNode("th", null, "累计花费"),
                        _createElementVNode("th", null, "总播放"),
                        _createElementVNode("th", null, "总点赞"),
                        _createElementVNode("th", null, "涨粉"),
                        _createElementVNode("th", null, "每涨 1 粉成本")
                      ])
                    ], -1 /* CACHED */)),
                    _createElementVNode("tbody", null, [
                      (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.boostSummary.top_videos_by_follow_aggregated, (v) => {
                        return (_openBlock(), _createElementBlock("tr", {
                          key: v.platform + '-' + v.video_publish_id
                        }, [
                          _createElementVNode("td", _hoisted_64, [
                            (v.video_url)
                              ? (_openBlock(), _createElementBlock("a", {
                                  key: 0,
                                  href: v.video_url,
                                  target: "_blank"
                                }, _toDisplayString(v.video_title || '(无标题)'), 9 /* TEXT, PROPS */, _hoisted_65))
                              : (_openBlock(), _createElementBlock("span", _hoisted_66, _toDisplayString(v.video_title || '(无标题)'), 1 /* TEXT */))
                          ]),
                          _createElementVNode("td", null, _toDisplayString($setup.platformLabel(v.platform)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString(v.boost_count), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString($setup.formatCost(v.total_cost, v.platform)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString($setup.formatNum(v.total_play)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString($setup.formatNum(v.total_like)), 1 /* TEXT */),
                          _createElementVNode("td", _hoisted_67, _toDisplayString($setup.formatNum(v.total_follow)), 1 /* TEXT */),
                          _createElementVNode("td", null, _toDisplayString(v.cost_per_follow != null ? '¥' + v.cost_per_follow : '-'), 1 /* TEXT */)
                        ]))
                      }), 128 /* KEYED_FRAGMENT */))
                    ])
                  ])
                ]))
              : _createCommentVNode("v-if", true)
          ]))
        : _createCommentVNode("v-if", true),
      ($setup.errorMsg)
        ? (_openBlock(), _createElementBlock("div", _hoisted_68, _toDisplayString($setup.errorMsg), 1 /* TEXT */))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 表头 (5 列: 选中 + 视频信息 + 跨平台 + 3 个平台) "),
      ($setup.videos.length > 0)
        ? (_openBlock(), _createElementBlock("div", _hoisted_69, [
            _createElementVNode("div", _hoisted_70, [
              _createElementVNode("div", _hoisted_71, [
                _createElementVNode("input", {
                  type: "checkbox",
                  checked: $setup.isAllSelected,
                  ".indeterminate": $setup.isPartialSelected,
                  onChange: _cache[5] || (_cache[5] = $event => ($setup.toggleSelectAll($event.target.checked))),
                  title: "全选/全不选当前页"
                }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_72)
              ]),
              _cache[40] || (_cache[40] = _createElementVNode("div", { class: "col-video" }, "视频", -1 /* CACHED */)),
              _cache[41] || (_cache[41] = _createElementVNode("div", { class: "col-totals" }, "跨平台合计", -1 /* CACHED */)),
              (_openBlock(), _createElementBlock(_Fragment, null, _renderList($setup.TARGET_PLATFORMS, (p) => {
                return _createElementVNode("div", {
                  key: p.key,
                  class: "col-platform"
                }, _toDisplayString(p.label), 1 /* TEXT */)
              }), 64 /* STABLE_FRAGMENT */))
            ]),
            _createCommentVNode(" 数据行 "),
            (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.videos, (v) => {
              return (_openBlock(), _createElementBlock("div", {
                key: v.article_id,
                class: _normalizeClass(["table-row data-row", [
             'top-' + v.top_boost_level,
             { 'row-has-dead': v.has_dead_platform && v.top_boost_level !== 'dead',
               'row-selected': $setup.selectedArticleIds.has(v.article_id) }
           ]])
              }, [
                _createCommentVNode(" 选中列 "),
                _createElementVNode("div", _hoisted_73, [
                  _createElementVNode("input", {
                    type: "checkbox",
                    checked: $setup.selectedArticleIds.has(v.article_id),
                    onChange: $event => ($setup.toggleRowSelected(v.article_id, $event.target.checked))
                  }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_74)
                ]),
                _createCommentVNode(" 视频列 "),
                _createElementVNode("div", _hoisted_75, [
                  _createElementVNode("div", _hoisted_76, [
                    _createElementVNode("span", {
                      class: _normalizeClass(["lvl-badge", 'lvl-' + v.top_boost_level]),
                      title: $setup.topLevelTooltip(v)
                    }, _toDisplayString($setup.levelText(v.top_boost_level)), 11 /* TEXT, CLASS, PROPS */, _hoisted_77),
                    _createCommentVNode(" 有任一平台 dead 但综合等级是 good/must 的, 额外挂个红色提醒徽章 "),
                    (v.has_dead_platform && v.top_boost_level !== 'dead')
                      ? (_openBlock(), _createElementBlock("span", {
                          key: 0,
                          class: "lvl-badge lvl-dead small",
                          title: $setup.deadPlatformTooltip(v)
                        }, "部分平台限流", 8 /* PROPS */, _hoisted_78))
                      : _createCommentVNode("v-if", true),
                    _createVNode(_component_router_link, {
                      to: `/zoe/${v.article_id}`,
                      class: "video-title-link"
                    }, {
                      default: _withCtx(() => [
                        _createTextVNode(_toDisplayString(v.video_title || '(无标题)'), 1 /* TEXT */)
                      ]),
                      _: 2 /* DYNAMIC */
                    }, 1032 /* PROPS, DYNAMIC_SLOTS */, ["to"])
                  ]),
                  _createElementVNode("div", _hoisted_79, [
                    _createCommentVNode(" 显示时间和排序键对齐: 优先展示微信视频号的发布时间 (排序就是按这个),\n                 没发微信的才 fallback 到 4 平台中最早一次的 \"首发\" 时间, 避免看起来像没排序. "),
                    (v.platforms.weixin?.published_at)
                      ? (_openBlock(), _createElementBlock("span", _hoisted_80, " 视频号 " + _toDisplayString($setup.formatDateTime(v.platforms.weixin.published_at)), 1 /* TEXT */))
                      : (v.first_published_at)
                        ? (_openBlock(), _createElementBlock("span", _hoisted_81, "首发 " + _toDisplayString($setup.formatDateTime(v.first_published_at)), 1 /* TEXT */))
                        : _createCommentVNode("v-if", true)
                  ])
                ]),
                _createCommentVNode(" 跨平台合计 "),
                _createElementVNode("div", _hoisted_82, [
                  _createElementVNode("div", _hoisted_83, [
                    _createElementVNode("span", _hoisted_84, [
                      _createElementVNode("span", _hoisted_85, _toDisplayString($setup.formatNum(v.total_views)), 1 /* TEXT */),
                      _cache[42] || (_cache[42] = _createElementVNode("span", { class: "metric-label" }, "浏览", -1 /* CACHED */))
                    ]),
                    _createElementVNode("span", _hoisted_86, [
                      _createElementVNode("span", _hoisted_87, _toDisplayString($setup.formatNum(v.total_likes)), 1 /* TEXT */),
                      _cache[43] || (_cache[43] = _createElementVNode("span", { class: "metric-label" }, "点赞", -1 /* CACHED */))
                    ])
                  ]),
                  _createElementVNode("div", _hoisted_88, [
                    _createElementVNode("span", _hoisted_89, [
                      _createElementVNode("span", _hoisted_90, _toDisplayString($setup.formatNum(v.total_comments)), 1 /* TEXT */),
                      _cache[44] || (_cache[44] = _createElementVNode("span", { class: "metric-label" }, "评论", -1 /* CACHED */))
                    ]),
                    _createElementVNode("span", _hoisted_91, [
                      _createElementVNode("span", {
                        class: _normalizeClass(["metric-num ratio-num", { hot: v.total_likes_ratio >= 0.03 }])
                      }, _toDisplayString($setup.formatPercent(v.total_likes_ratio)), 3 /* TEXT, CLASS */),
                      _cache[45] || (_cache[45] = _createElementVNode("span", { class: "metric-label" }, "赞率", -1 /* CACHED */))
                    ])
                  ])
                ]),
                _createCommentVNode(" 各平台列 "),
                (_openBlock(), _createElementBlock(_Fragment, null, _renderList($setup.TARGET_PLATFORMS, (p) => {
                  return _createElementVNode("div", {
                    key: p.key,
                    class: _normalizeClass(["col-platform", ['plat-cell', $setup.getPlatformLevelClass(v, p.key)]])
                  }, [
                    (v.platforms[p.key])
                      ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                          _createElementVNode("div", _hoisted_92, [
                            _createElementVNode("span", {
                              class: _normalizeClass(["lvl-badge small", 'lvl-' + (v.platforms[p.key].boost_score?.level || 'watch')]),
                              title: v.platforms[p.key].boost_score?.reason
                            }, _toDisplayString($setup.levelText(v.platforms[p.key].boost_score?.level)), 11 /* TEXT, CLASS, PROPS */, _hoisted_93),
                            _createCommentVNode(" 平台硬信号 (reviewing/private/recommended_blocked 这种, dead/forbidden 已经在 lvl-badge 里显示了) "),
                            ($setup.shouldShowPlatformStatus(v.platforms[p.key]))
                              ? (_openBlock(), _createElementBlock("span", {
                                  key: 0,
                                  class: _normalizeClass(["status-tag", 'status-' + v.platforms[p.key].platform_status]),
                                  title: v.platforms[p.key].platform_status_desc || ''
                                }, _toDisplayString($setup.platformStatusText(v.platforms[p.key].platform_status)), 11 /* TEXT, CLASS, PROPS */, _hoisted_94))
                              : _createCommentVNode("v-if", true),
                            (v.platforms[p.key].published_link)
                              ? (_openBlock(), _createElementBlock("a", {
                                  key: 1,
                                  href: v.platforms[p.key].published_link,
                                  target: "_blank",
                                  class: "plat-link",
                                  title: '打开发布链接'
                                }, "↗", 8 /* PROPS */, _hoisted_95))
                              : _createCommentVNode("v-if", true)
                          ]),
                          _createElementVNode("div", _hoisted_96, [
                            _createElementVNode("span", _hoisted_97, [
                              _createElementVNode("span", _hoisted_98, _toDisplayString($setup.formatNum(v.platforms[p.key].views)), 1 /* TEXT */),
                              _cache[46] || (_cache[46] = _createElementVNode("span", { class: "metric-label" }, "浏览", -1 /* CACHED */))
                            ]),
                            _createElementVNode("span", _hoisted_99, [
                              _createElementVNode("span", _hoisted_100, _toDisplayString($setup.formatNum(v.platforms[p.key].likes)), 1 /* TEXT */),
                              _cache[47] || (_cache[47] = _createElementVNode("span", { class: "metric-label" }, "赞", -1 /* CACHED */))
                            ])
                          ]),
                          _createElementVNode("div", _hoisted_101, [
                            _createElementVNode("span", _hoisted_102, [
                              _createElementVNode("span", _hoisted_103, _toDisplayString($setup.formatNum(v.platforms[p.key].comments)), 1 /* TEXT */),
                              _cache[48] || (_cache[48] = _createElementVNode("span", { class: "metric-label" }, "评论", -1 /* CACHED */))
                            ]),
                            _createElementVNode("span", _hoisted_104, [
                              _createElementVNode("span", {
                                class: _normalizeClass(["metric-num ratio-num", { hot: (v.platforms[p.key].boost_score?.likes_ratio || 0) >= 0.03 }])
                              }, _toDisplayString($setup.formatPercent(v.platforms[p.key].boost_score?.likes_ratio || 0)), 3 /* TEXT, CLASS */),
                              _cache[49] || (_cache[49] = _createElementVNode("span", { class: "metric-label" }, "赞率", -1 /* CACHED */))
                            ])
                          ]),
                          (v.platforms[p.key].latest_boost_status)
                            ? (_openBlock(), _createElementBlock("div", _hoisted_105, [
                                _createElementVNode("span", {
                                  class: _normalizeClass(["boost-tag", 'boost-' + v.platforms[p.key].latest_boost_status])
                                }, " 加热: " + _toDisplayString($setup.boostStatusText(v.platforms[p.key].latest_boost_status)), 3 /* TEXT, CLASS */)
                              ]))
                            : _createCommentVNode("v-if", true)
                        ], 64 /* STABLE_FRAGMENT */))
                      : (_openBlock(), _createElementBlock("div", _hoisted_106, "未发布"))
                  ], 2 /* CLASS */)
                }), 64 /* STABLE_FRAGMENT */))
              ], 2 /* CLASS */))
            }), 128 /* KEYED_FRAGMENT */))
          ]))
        : _createCommentVNode("v-if", true),
      ($setup.loading)
        ? (_openBlock(), _createElementBlock("div", _hoisted_107, "加载中..."))
        : _createCommentVNode("v-if", true),
      (!$setup.loading && $setup.videos.length === 0 && !$setup.errorMsg)
        ? (_openBlock(), _createElementBlock("div", _hoisted_108, " 所选时间范围内没有发布数据 "))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 批量加热弹窗 "),
      ($setup.batchModalOpen)
        ? (_openBlock(), _createElementBlock("div", {
            key: 6,
            class: "modal-mask",
            onClick: _withModifiers($setup.closeBatchModal, ["self"])
          }, [
            _createElementVNode("div", _hoisted_109, [
              _createElementVNode("div", _hoisted_110, [
                _createElementVNode("h3", null, "批量加热 — " + _toDisplayString($setup.selectedVideosForModal.length) + " 个视频", 1 /* TEXT */),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: $setup.closeBatchModal
                }, "×")
              ]),
              _createElementVNode("div", _hoisted_111, [
                _createCommentVNode(" 平台选择 "),
                _createElementVNode("div", _hoisted_112, [
                  _cache[52] || (_cache[52] = _createElementVNode("label", null, "平台", -1 /* CACHED */)),
                  _createElementVNode("div", null, [
                    _createElementVNode("label", _hoisted_113, [
                      _withDirectives(_createElementVNode("input", {
                        type: "radio",
                        value: "weixin",
                        "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => (($setup.batchForm.platform) = $event))
                      }, null, 512 /* NEED_PATCH */), [
                        [_vModelRadio, $setup.batchForm.platform]
                      ]),
                      _cache[50] || (_cache[50] = _createTextVNode(" 微信视频号 (微信豆, 提交后需要手机扫码) ", -1 /* CACHED */))
                    ]),
                    _createElementVNode("label", _hoisted_114, [
                      _withDirectives(_createElementVNode("input", {
                        type: "radio",
                        value: "douyin",
                        "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => (($setup.batchForm.platform) = $event))
                      }, null, 512 /* NEED_PATCH */), [
                        [_vModelRadio, $setup.batchForm.platform]
                      ]),
                      _cache[51] || (_cache[51] = _createTextVNode(" 抖音 DOU+ (账户余额扣款, 全自动) ", -1 /* CACHED */))
                    ])
                  ])
                ]),
                _createCommentVNode(" 选中的视频清单 "),
                _createElementVNode("div", _hoisted_115, [
                  _cache[53] || (_cache[53] = _createElementVNode("label", null, "选中视频", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_116, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.selectedVideosForModal, (v) => {
                      return (_openBlock(), _createElementBlock("div", {
                        key: v.article_id,
                        class: _normalizeClass(["modal-video-line", { 'video-skip': !$setup.canBoostOnPlatform(v, $setup.batchForm.platform) }])
                      }, [
                        _createElementVNode("span", _hoisted_117, [
                          ($setup.canBoostOnPlatform(v, $setup.batchForm.platform))
                            ? (_openBlock(), _createElementBlock("span", _hoisted_118, "✓"))
                            : (_openBlock(), _createElementBlock("span", _hoisted_119, "✗"))
                        ]),
                        _createElementVNode("span", _hoisted_120, _toDisplayString(v.video_title || '(无标题)'), 1 /* TEXT */),
                        _createElementVNode("span", _hoisted_121, " vp_id=" + _toDisplayString($setup.getVpId(v, $setup.batchForm.platform) || '-'), 1 /* TEXT */)
                      ], 2 /* CLASS */))
                    }), 128 /* KEYED_FRAGMENT */)),
                    ($setup.selectedVideosForModal.length === 0)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_122, " 没选中任何视频 "))
                      : _createCommentVNode("v-if", true)
                  ])
                ]),
                _createCommentVNode(" 投放参数 "),
                _createElementVNode("div", _hoisted_123, [
                  _cache[54] || (_cache[54] = _createElementVNode("label", null, "每单金额", -1 /* CACHED */)),
                  _createElementVNode("div", null, [
                    _withDirectives(_createElementVNode("input", {
                      type: "number",
                      "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => (($setup.batchForm.amount) = $event)),
                      min: "100",
                      step: "100",
                      class: "modal-input"
                    }, null, 512 /* NEED_PATCH */), [
                      [
                        _vModelText,
                        $setup.batchForm.amount,
                        void 0,
                        { number: true }
                      ]
                    ]),
                    _createElementVNode("span", _hoisted_124, _toDisplayString($setup.batchForm.platform === 'weixin' ? '微信豆 (500/1000 预设, 其他走自定义)' : '元 (DOU+ 起投 100)'), 1 /* TEXT */)
                  ])
                ]),
                _createElementVNode("div", _hoisted_125, [
                  _cache[55] || (_cache[55] = _createElementVNode("label", null, "时长", -1 /* CACHED */)),
                  _withDirectives(_createElementVNode("select", {
                    "onUpdate:modelValue": _cache[9] || (_cache[9] = $event => (($setup.batchForm.duration) = $event)),
                    class: "modal-select"
                  }, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.currentDurations, (h) => {
                      return (_openBlock(), _createElementBlock("option", {
                        key: h,
                        value: h
                      }, _toDisplayString(h) + " 小时", 9 /* TEXT, PROPS */, _hoisted_126))
                    }), 128 /* KEYED_FRAGMENT */))
                  ], 512 /* NEED_PATCH */), [
                    [
                      _vModelSelect,
                      $setup.batchForm.duration,
                      void 0,
                      { number: true }
                    ]
                  ])
                ]),
                _createElementVNode("div", _hoisted_127, [
                  _cache[56] || (_cache[56] = _createElementVNode("label", null, "优先目标", -1 /* CACHED */)),
                  _withDirectives(_createElementVNode("select", {
                    "onUpdate:modelValue": _cache[10] || (_cache[10] = $event => (($setup.batchForm.goal) = $event)),
                    class: "modal-select"
                  }, [
                    (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.currentGoals, (g) => {
                      return (_openBlock(), _createElementBlock("option", {
                        key: g.key,
                        value: g.key
                      }, _toDisplayString(g.label), 9 /* TEXT, PROPS */, _hoisted_128))
                    }), 128 /* KEYED_FRAGMENT */))
                  ], 512 /* NEED_PATCH */), [
                    [_vModelSelect, $setup.batchForm.goal]
                  ])
                ]),
                _createCommentVNode(" weixin 专有: 投放群 (选群自动填成员) + target_creators 微调 "),
                ($setup.batchForm.platform === 'weixin')
                  ? (_openBlock(), _createElementBlock("div", _hoisted_129, [
                      _cache[58] || (_cache[58] = _createElementVNode("label", null, [
                        _createTextVNode("投放群"),
                        _createElementVNode("br"),
                        _createElementVNode("span", { class: "modal-hint" }, "(选群自动填成员)")
                      ], -1 /* CACHED */)),
                      _withDirectives(_createElementVNode("select", {
                        "onUpdate:modelValue": _cache[11] || (_cache[11] = $event => (($setup.batchForm.audienceGroupId) = $event)),
                        onChange: $setup.applyAudienceGroup,
                        class: "modal-select modal-input-wide"
                      }, [
                        _cache[57] || (_cache[57] = _createElementVNode("option", { value: null }, "自定义 / 不定向", -1 /* CACHED */)),
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.audienceGroups, (g) => {
                          return (_openBlock(), _createElementBlock("option", {
                            key: g.id,
                            value: g.id
                          }, _toDisplayString(g.name) + " (" + _toDisplayString(g.creator_count) + "人)" + _toDisplayString(g.is_default ? ' ★默认' : '') + " — " + _toDisplayString(g.description), 9 /* TEXT, PROPS */, _hoisted_130))
                        }), 128 /* KEYED_FRAGMENT */))
                      ], 544 /* NEED_HYDRATION, NEED_PATCH */), [
                        [
                          _vModelSelect,
                          $setup.batchForm.audienceGroupId,
                          void 0,
                          { number: true }
                        ]
                      ])
                    ]))
                  : _createCommentVNode("v-if", true),
                ($setup.batchForm.platform === 'weixin')
                  ? (_openBlock(), _createElementBlock("div", _hoisted_131, [
                      _cache[59] || (_cache[59] = _createElementVNode("label", null, [
                        _createTextVNode("相似博主定向"),
                        _createElementVNode("br"),
                        _createElementVNode("span", { class: "modal-hint" }, "(逗号分隔, 留空 = 默认人群)")
                      ], -1 /* CACHED */)),
                      _withDirectives(_createElementVNode("input", {
                        type: "text",
                        "onUpdate:modelValue": _cache[12] || (_cache[12] = $event => (($setup.batchForm.targetCreators) = $event)),
                        placeholder: "例: 极客时间,InfoQ,量子位,机器之心",
                        class: "modal-input modal-input-wide"
                      }, null, 512 /* NEED_PATCH */), [
                        [_vModelText, $setup.batchForm.targetCreators]
                      ])
                    ]))
                  : _createCommentVNode("v-if", true),
                _createCommentVNode(" douyin 专有: audience_pkg_name "),
                ($setup.batchForm.platform === 'douyin')
                  ? (_openBlock(), _createElementBlock("div", _hoisted_132, [
                      _cache[60] || (_cache[60] = _createElementVNode("label", null, "定向包名", -1 /* CACHED */)),
                      _withDirectives(_createElementVNode("input", {
                        type: "text",
                        "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => (($setup.batchForm.audiencePkgName) = $event)),
                        placeholder: "doujia 后台已建的定向包名",
                        class: "modal-input modal-input-wide"
                      }, null, 512 /* NEED_PATCH */), [
                        [_vModelText, $setup.batchForm.audiencePkgName]
                      ])
                    ]))
                  : _createCommentVNode("v-if", true),
                _createElementVNode("div", _hoisted_133, [
                  _cache[62] || (_cache[62] = _createElementVNode("label", null, "开关", -1 /* CACHED */)),
                  _createElementVNode("div", null, [
                    _createElementVNode("label", _hoisted_134, [
                      _withDirectives(_createElementVNode("input", {
                        type: "checkbox",
                        "onUpdate:modelValue": _cache[14] || (_cache[14] = $event => (($setup.batchForm.submit) = $event))
                      }, null, 512 /* NEED_PATCH */), [
                        [_vModelCheckbox, $setup.batchForm.submit]
                      ]),
                      _createTextVNode(" 真投 (扣" + _toDisplayString($setup.batchForm.platform === 'weixin' ? '微信豆' : '账户余额') + "!) ", 1 /* TEXT */),
                      ($setup.batchForm.submit)
                        ? (_openBlock(), _createElementBlock("span", _hoisted_135, "⚠ 真投开启"))
                        : _createCommentVNode("v-if", true)
                    ]),
                    _createElementVNode("label", _hoisted_136, [
                      _withDirectives(_createElementVNode("input", {
                        type: "checkbox",
                        "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => (($setup.batchForm.force) = $event))
                      }, null, 512 /* NEED_PATCH */), [
                        [_vModelCheckbox, $setup.batchForm.force]
                      ]),
                      _cache[61] || (_cache[61] = _createTextVNode(" force (同视频有未结束订单也强行新建) ", -1 /* CACHED */))
                    ])
                  ])
                ])
              ]),
              _createElementVNode("div", _hoisted_137, [
                _createElementVNode("button", {
                  class: "btn-secondary",
                  onClick: $setup.closeBatchModal
                }, "取消"),
                _createElementVNode("button", {
                  class: "btn-primary",
                  disabled: $setup.batchSubmitting || $setup.selectedVideosForModal.length === 0,
                  onClick: $setup.submitBatchBoost
                }, _toDisplayString($setup.batchSubmitting ? '提交中...' : ($setup.batchForm.submit ? '真投' : 'Dry-run')), 9 /* TEXT, PROPS */, _hoisted_138)
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 批量任务进度 "),
      ($setup.batchJob)
        ? (_openBlock(), _createElementBlock("div", _hoisted_139, [
            _createElementVNode("div", _hoisted_140, [
              _createElementVNode("h3", null, [
                _createTextVNode("批量任务 " + _toDisplayString($setup.batchJob.platform) + " — 入队 " + _toDisplayString($setup.batchJob.inserted.length) + " 单 ", 1 /* TEXT */),
                ($setup.batchJob.rejected.length > 0)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_141, " (拒绝 " + _toDisplayString($setup.batchJob.rejected.length) + " 单) ", 1 /* TEXT */))
                  : _createCommentVNode("v-if", true)
              ]),
              _createElementVNode("button", {
                class: "modal-close",
                onClick: $setup.closeBatchJob
              }, "×")
            ]),
            _cache[67] || (_cache[67] = _createElementVNode("div", { class: "card-hint" }, " 每 4 秒轮询一次状态. weixin 订单提交后停在\"待支付\", 登录视频号助手订单页扫码付款. ", -1 /* CACHED */)),
            _createElementVNode("table", _hoisted_142, [
              _cache[66] || (_cache[66] = _createElementVNode("thead", null, [
                _createElementVNode("tr", null, [
                  _createElementVNode("th", null, "boost_id"),
                  _createElementVNode("th", { class: "th-left" }, "视频"),
                  _createElementVNode("th", null, "状态"),
                  _createElementVNode("th", null, "order_id"),
                  _createElementVNode("th", { class: "th-left" }, "备注 (错误信息)")
                ])
              ], -1 /* CACHED */)),
              _createElementVNode("tbody", null, [
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.batchJob.items, (item) => {
                  return (_openBlock(), _createElementBlock("tr", {
                    key: item.boost_id,
                    class: _normalizeClass('order-' + item.boost_status)
                  }, [
                    _createElementVNode("td", null, _toDisplayString(item.boost_id), 1 /* TEXT */),
                    _createElementVNode("td", _hoisted_143, _toDisplayString(item.video_title || '-'), 1 /* TEXT */),
                    _createElementVNode("td", null, [
                      _createElementVNode("span", {
                        class: _normalizeClass(["boost-tag", 'boost-' + item.boost_status])
                      }, _toDisplayString($setup.boostStatusText(item.boost_status)), 3 /* TEXT, CLASS */)
                    ]),
                    _createElementVNode("td", null, _toDisplayString(item.order_id || '-'), 1 /* TEXT */),
                    _createElementVNode("td", _hoisted_144, _toDisplayString(item.error_message || '-'), 1 /* TEXT */)
                  ], 2 /* CLASS */))
                }), 128 /* KEYED_FRAGMENT */)),
                (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.batchJob.rejected, (rej) => {
                  return (_openBlock(), _createElementBlock("tr", {
                    key: 'rej-' + rej.index,
                    class: "order-failed"
                  }, [
                    _cache[63] || (_cache[63] = _createElementVNode("td", null, "-", -1 /* CACHED */)),
                    _createElementVNode("td", _hoisted_145, "vp_id=" + _toDisplayString(rej.video_publish_id), 1 /* TEXT */),
                    _cache[64] || (_cache[64] = _createElementVNode("td", null, [
                      _createElementVNode("span", { class: "boost-tag boost-failed" }, "校验拒绝")
                    ], -1 /* CACHED */)),
                    _cache[65] || (_cache[65] = _createElementVNode("td", null, "-", -1 /* CACHED */)),
                    _createElementVNode("td", _hoisted_146, _toDisplayString(rej.error), 1 /* TEXT */)
                  ]))
                }), 128 /* KEYED_FRAGMENT */))
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 分页 "),
      ($setup.pagination && $setup.pagination.total_pages > 1)
        ? (_openBlock(), _createElementBlock("div", _hoisted_147, [
            _createElementVNode("button", {
              class: "page-btn",
              disabled: $setup.pagination.page === 1,
              onClick: _cache[16] || (_cache[16] = $event => ($setup.changePage($setup.pagination.page - 1)))
            }, "上一页", 8 /* PROPS */, _hoisted_148),
            _createElementVNode("span", _hoisted_149, " 第 " + _toDisplayString($setup.pagination.page) + " / " + _toDisplayString($setup.pagination.total_pages) + " 页 (共 " + _toDisplayString($setup.pagination.total) + " 条) ", 1 /* TEXT */),
            _createElementVNode("button", {
              class: "page-btn",
              disabled: $setup.pagination.page >= $setup.pagination.total_pages,
              onClick: _cache[17] || (_cache[17] = $event => ($setup.changePage($setup.pagination.page + 1)))
            }, "下一页", 8 /* PROPS */, _hoisted_150)
          ]))
        : _createCommentVNode("v-if", true)
    ])
  ], 64 /* STABLE_FRAGMENT */))
}

import "/src/views/Dashboard.vue?t=1785112691957&vue&type=style&index=0&scoped=7f773d42&lang.css"

_sfc_main.__hmrId = "7f773d42"
typeof __VUE_HMR_RUNTIME__ !== 'undefined' && __VUE_HMR_RUNTIME__.createRecord(_sfc_main.__hmrId, _sfc_main)
import.meta.hot.on('file-changed', ({ file }) => {
  __VUE_HMR_RUNTIME__.CHANGED_FILE = file
})
import.meta.hot.accept(mod => {
  if (!mod) return
  const { default: updated, _rerender_only } = mod
  if (_rerender_only) {
    __VUE_HMR_RUNTIME__.rerender(updated.__hmrId, updated.render)
  } else {
    __VUE_HMR_RUNTIME__.reload(updated.__hmrId, updated)
  }
})
import _export_sfc from "/@id/__x00__plugin-vue:export-helper"
export default /*#__PURE__*/_export_sfc(_sfc_main, [['render',_sfc_render],['__scopeId',"data-v-7f773d42"],['__file',"C:/WucaiMedia/client/src/views/Dashboard.vue"]])
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6W10sInNvdXJjZXMiOlsiRGFzaGJvYXJkLnZ1ZSJdLCJzb3VyY2VzQ29udGVudCI6WyI8dGVtcGxhdGU+XG4gIDxBcHBIZWFkZXIgLz5cbiAgPGRpdiBjbGFzcz1cImRhc2hib2FyZC1wYWdlXCI+XG4gICAgPCEtLSDpobbpg6jnrZvpgInmnaEgLS0+XG4gICAgPGRpdiBjbGFzcz1cInBhZ2UtaGVhZGVyXCI+XG4gICAgICA8ZGl2IGNsYXNzPVwiaGVhZGVyLWxlZnRcIj5cbiAgICAgICAgPGgxIGNsYXNzPVwicGFnZS10aXRsZVwiPuaVsOaNruaxh+aAu+eci+advzwvaDE+XG4gICAgICAgIDxzcGFuIGNsYXNzPVwicGFnZS1zdWJ0aXRsZVwiPuS4gOihjOS4gOinhumikSwg5qiq5ZCR55yLIDMg5Liq5bmz5Y+wICjlvq7kv6Hop4bpopHlj7cgKyDmipbpn7MgKyDlsI/nuqLkuaYpPC9zcGFuPlxuICAgICAgPC9kaXY+XG4gICAgICA8ZGl2IGNsYXNzPVwiaGVhZGVyLWFjdGlvbnNcIj5cbiAgICAgICAgPGRpdiBjbGFzcz1cImZpbHRlci1ncm91cFwiPlxuICAgICAgICAgIDxzcGFuIGNsYXNzPVwiZmlsdGVyLWxhYmVsXCI+6IyD5Zu0Ojwvc3Bhbj5cbiAgICAgICAgICA8YnV0dG9uIHYtZm9yPVwiciBpbiBSQU5HRVNcIiA6a2V5PVwici5rZXlcIlxuICAgICAgICAgICAgICAgICAgY2xhc3M9XCJjaGlwXCIgOmNsYXNzPVwieyBhY3RpdmU6IHJhbmdlID09PSByLmtleSB9XCJcbiAgICAgICAgICAgICAgICAgIEBjbGljaz1cInNldFJhbmdlKHIua2V5KVwiPnt7IHIubGFiZWwgfX08L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJmaWx0ZXItZ3JvdXBcIj5cbiAgICAgICAgICA8c3BhbiBjbGFzcz1cImZpbHRlci1sYWJlbFwiPuaOkuW6jzo8L3NwYW4+XG4gICAgICAgICAgPHNlbGVjdCB2LW1vZGVsPVwic29ydFwiIEBjaGFuZ2U9XCJmZXRjaERhdGEoMSlcIiBjbGFzcz1cInNlbGVjdFwiPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cInB1Ymxpc2hlZF9hdFwiPuinhumikeWPt+WPkeW4g+aXtumXtDwvb3B0aW9uPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cImxpa2VzX3JhdGlvXCI+54K56LWe546HPC9vcHRpb24+XG4gICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwibGlrZXNcIj7mgLvngrnotZ48L29wdGlvbj5cbiAgICAgICAgICAgIDxvcHRpb24gdmFsdWU9XCJ2aWV3c1wiPuaAu+a1j+iniDwvb3B0aW9uPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cImNvbW1lbnRzXCI+5oC76K+E6K66PC9vcHRpb24+XG4gICAgICAgICAgPC9zZWxlY3Q+XG4gICAgICAgIDwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwiZmlsdGVyLWdyb3VwXCI+XG4gICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImNoaXAgY2hpcC1kYW5nZXJcIiA6Y2xhc3M9XCJ7IGFjdGl2ZTogb25seURlYWQgfVwiXG4gICAgICAgICAgICAgICAgICBAY2xpY2s9XCJ0b2dnbGVPbmx5RGVhZFwiXG4gICAgICAgICAgICAgICAgICB0aXRsZT1cIuWPqueci+eWkeS8vOmZkOa1gS/lg7XlsLjop4bpopEgKOWPkeW4gyAyNGgrIOS9hiB2aWV3cyDmnoHkvY4pXCI+XG4gICAgICAgICAgICDlj6rnnIvpmZDmtYHlq4znlpFcbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxidXR0b24gY2xhc3M9XCJidG4tc2Vjb25kYXJ5XCIgOmRpc2FibGVkPVwibG9hZGluZ1wiIEBjbGljaz1cImZldGNoRGF0YShjdXJyZW50UGFnZSlcIj5cbiAgICAgICAgICB7eyBsb2FkaW5nID8gJ+WKoOi9veS4rS4uLicgOiAn5Yi35pawJyB9fVxuICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImJ0bi1wcmltYXJ5XCJcbiAgICAgICAgICAgICAgICA6ZGlzYWJsZWQ9XCJzZWxlY3RlZEFydGljbGVJZHMuc2l6ZSA9PT0gMFwiXG4gICAgICAgICAgICAgICAgQGNsaWNrPVwib3BlbkJhdGNoQm9vc3RNb2RhbFwiXG4gICAgICAgICAgICAgICAgOnRpdGxlPVwic2VsZWN0ZWRBcnRpY2xlSWRzLnNpemUgPT09IDAgPyAn5YWI5Yu+6YCJ6KaB5om56YeP5Yqg54Ot55qE6KeG6aKRJyA6ICcnXCI+XG4gICAgICAgICAg5om56YeP5Yqg54Ote3sgc2VsZWN0ZWRBcnRpY2xlSWRzLnNpemUgPiAwID8gYCAoJHtzZWxlY3RlZEFydGljbGVJZHMuc2l6ZX0g6YCJ5LitKWAgOiAnJyB9fVxuICAgICAgICA8L2J1dHRvbj5cbiAgICAgIDwvZGl2PlxuICAgIDwvZGl2PlxuXG4gICAgPCEtLSDliqDng63mjqjojZDmoaPkvY3or7TmmI4gKOaKmOWPoCkgLS0+XG4gICAgPGRldGFpbHMgY2xhc3M9XCJydWxlcy1jYXJkXCI+XG4gICAgICA8c3VtbWFyeT7liqDng63mjqjojZDop4TliJkgKOeCueW8gOeciyk8L3N1bW1hcnk+XG4gICAgICA8ZGl2IGNsYXNzPVwicnVsZXMtZ3JpZFwiPlxuICAgICAgICA8ZGl2IGNsYXNzPVwicnVsZS1yb3dcIj48c3BhbiBjbGFzcz1cImx2bC1iYWRnZSBsdmwtbXVzdFwiPuW/heaKlTwvc3Bhbj4g54K56LWe546HIOKJpSA1JSDmiJYg6K+E6K66546HIOKJpSAxJSDigJQg5o6o6I2Q5oqVIDUwMCDosYY8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cInJ1bGUtcm93XCI+PHNwYW4gY2xhc3M9XCJsdmwtYmFkZ2UgbHZsLWdvb2RcIj7lgLzmipU8L3NwYW4+IOeCuei1nueOhyDiiaUgMyUg5oiWIDI0aCDlhoXlhrflkK/liqjnu5nlipsgKOW+ruS/oeKJpTUwMC/mipbpn7PiiaUyMDAwKSDigJQg5o6o6I2Q5oqVIDIwMCDosYY8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cInJ1bGUtcm93XCI+PHNwYW4gY2xhc3M9XCJsdmwtYmFkZ2UgbHZsLXdhdGNoXCI+6KeC5pybPC9zcGFuPiDmlbDmja7kuK3op4TkuK3nn6ksIOWGjeetieetiTwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwicnVsZS1yb3dcIj48c3BhbiBjbGFzcz1cImx2bC1iYWRnZSBsdmwtc2tpcFwiPuWIq+aKlTwvc3Bhbj4g5rWP6KeI6YePIOKJpSAyMDAg5L2G54K56LWe546HICZsdDsgMSUg4oCUIOWIq+a1qui0ueixhjwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwicnVsZS1yb3dcIj48c3BhbiBjbGFzcz1cImx2bC1iYWRnZSBsdmwtZGVhZFwiPumZkOa1geWrjOeWkTwvc3Bhbj4g5Y+R5biDIDI0aCsg5L2GIHZpZXdzIOaegeS9jiAo5b6u5L+hJmx0OzUwIC8g5oqW6Z+zJmx0OzEwMCwg5bCP57qi5Lmm5rWB6YeP5oqW5Yqo5aSn5LiN5Y+C5LiO5Yik5a6aKSDigJQg5aSN55uY6YCJ6aKYL+agh+mimC/mlY/mhJ/or40sIOWIq+WGjeaKlemSsTwvZGl2PlxuICAgICAgPC9kaXY+XG4gICAgPC9kZXRhaWxzPlxuXG4gICAgPCEtLSDop4bpopHlj7fmipXmlL7nvqQgKOWPr+WkjeeUqOWumuWQkeS6uue+pCk6IOW7uuWNleaXtuebtOaOpemAiee+pCwgYXV0b19ib29zdCDnlKgg4piF6buY6K6kIOe+pCAtLT5cbiAgICA8ZGl2IHYtaWY9XCJhdWRpZW5jZUdyb3Vwcy5sZW5ndGggPiAwXCIgY2xhc3M9XCJhdWRpZW5jZS1ncm91cHMtY2FyZFwiPlxuICAgICAgPGRpdiBjbGFzcz1cImFnLWhlYWRcIj5cbiAgICAgICAgPGgyIGNsYXNzPVwiY2FyZC10aXRsZVwiPuinhumikeWPt+aKleaUvue+pDwvaDI+XG4gICAgICAgIDxzcGFuIGNsYXNzPVwiYWctaGludFwiPuW7uuWlveWPr+WkjeeUqDog5om56YeP5Yqg54Ot5by556qX6YeM6YCJXCLmipXmlL7nvqRcIuWNs+WPrywg6Ieq5Yqo5oqV5pS+55SoIOKYhem7mOiupCDnvqQ8L3NwYW4+XG4gICAgICA8L2Rpdj5cbiAgICAgIDxkaXYgY2xhc3M9XCJhZy1saXN0XCI+XG4gICAgICAgIDxkaXYgdi1mb3I9XCJnIGluIGF1ZGllbmNlR3JvdXBzXCIgOmtleT1cImcuaWRcIiBjbGFzcz1cImFnLWl0ZW1cIlxuICAgICAgICAgICAgIDpjbGFzcz1cInsgJ2FnLWRlZmF1bHQnOiBnLmlzX2RlZmF1bHQgfVwiPlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJhZy1pdGVtLWhlYWRcIj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwiYWctbmFtZVwiPnt7IGcubmFtZSB9fTwvc3Bhbj5cbiAgICAgICAgICAgIDxzcGFuIHYtaWY9XCJnLmlzX2RlZmF1bHRcIiBjbGFzcz1cImFnLWJhZGdlXCI+4piFIOiHquWKqOaKleaUvum7mOiupDwvc3Bhbj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwiYWctY291bnRcIj57eyBnLmNyZWF0b3JfY291bnQgfX0g5Lq6PC9zcGFuPlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJhZy1kZXNjXCI+e3sgZy5kZXNjcmlwdGlvbiB9fTwvZGl2PlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJhZy1jcmVhdG9yc1wiPlxuICAgICAgICAgICAgPHNwYW4gdi1mb3I9XCJjIGluIGcuY3JlYXRvcnNcIiA6a2V5PVwiY1wiIGNsYXNzPVwiYWctY3JlYXRvclwiPnt7IGMgfX08L3NwYW4+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgIDwvZGl2PlxuICAgICAgPC9kaXY+XG4gICAgPC9kaXY+XG5cbiAgICA8IS0tIOaOkumZpOagh+mimOWFs+mUruivjTog5qCH6aKY5ZCr6L+Z5Lqb6K+N55qE6KeG6aKR56aB5q2i5Yqg54Ot5oqV5pS+ICjlu7rljZXmi5LljZUgKyDoh6rliqjmipXmlL7ot7Pov4cpIC0tPlxuICAgIDxkaXYgY2xhc3M9XCJleGNsdWRlZC1rdy1jYXJkXCI+XG4gICAgICA8ZGl2IGNsYXNzPVwiYWctaGVhZFwiPlxuICAgICAgICA8aDIgY2xhc3M9XCJjYXJkLXRpdGxlXCI+5o6S6Zmk5qCH6aKY5YWz6ZSu6K+NPC9oMj5cbiAgICAgICAgPHNwYW4gY2xhc3M9XCJhZy1oaW50XCI+5qCH6aKY5ZCr6L+Z5Lqb6K+N55qE6KeG6aKR56aB5q2i5Yqg54Ot5oqV5pS+OiDmibnph48v6Ieq5Yqo5bu65Y2V55u05o6l5ouSLCDkv53lrZjlkI7nq4vliLvnlJ/mlYg8L3NwYW4+XG4gICAgICA8L2Rpdj5cbiAgICAgIDxkaXYgY2xhc3M9XCJrdy1ib2R5XCI+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJrdy1saXN0XCI+XG4gICAgICAgICAgPHNwYW4gdi1mb3I9XCJrIGluIGV4Y2x1ZGVkS2V5d29yZHNcIiA6a2V5PVwiay5pZFwiIGNsYXNzPVwia3ctY2hpcFwiPlxuICAgICAgICAgICAge3sgay5rZXl3b3JkIH19XG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwia3ctZGVsXCIgOnRpdGxlPVwiYOWIoOmZpCAke2sua2V5d29yZH1gXCIgQGNsaWNrPVwicmVtb3ZlRXhjbHVkZWRLZXl3b3JkKGspXCI+w5c8L2J1dHRvbj5cbiAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgPHNwYW4gdi1pZj1cImV4Y2x1ZGVkS2V5d29yZHMubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJrdy1lbXB0eVwiPuaaguaXoOaOkumZpOivjTwvc3Bhbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJrdy1hZGRcIj5cbiAgICAgICAgICA8aW5wdXQgdHlwZT1cInRleHRcIiB2LW1vZGVsPVwibmV3S2V5d29yZFwiIG1heGxlbmd0aD1cIjUwXCJcbiAgICAgICAgICAgICAgICAgcGxhY2Vob2xkZXI9XCLmt7vliqDmjpLpmaTor40sIOWmgjog5Lqs5Lic5pa5XCJcbiAgICAgICAgICAgICAgICAgQGtleXVwLmVudGVyPVwiYWRkRXhjbHVkZWRLZXl3b3JkXCIgLz5cbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuLXNlY29uZGFyeVwiIDpkaXNhYmxlZD1cIiFuZXdLZXl3b3JkLnRyaW0oKSB8fCBrd1NhdmluZ1wiXG4gICAgICAgICAgICAgICAgICBAY2xpY2s9XCJhZGRFeGNsdWRlZEtleXdvcmRcIj5cbiAgICAgICAgICAgIHt7IGt3U2F2aW5nID8gJ+S/neWtmOS4rS4uLicgOiAn5re75YqgJyB9fVxuICAgICAgICAgIDwvYnV0dG9uPlxuICAgICAgICA8L2Rpdj5cbiAgICAgIDwvZGl2PlxuICAgIDwvZGl2PlxuXG4gICAgPCEtLSDmipXmlL7ljoblj7LmgKfku7fmr5TljaHniYcgLS0+XG4gICAgPGRpdiB2LWlmPVwiYm9vc3RTdW1tYXJ5XCIgY2xhc3M9XCJib29zdC1zdW1tYXJ5LWNhcmRcIj5cbiAgICAgIDxkaXYgY2xhc3M9XCJib29zdC1zdW1tYXJ5LWhlYWRcIj5cbiAgICAgICAgPGgyIGNsYXNzPVwiY2FyZC10aXRsZVwiPuaKleaUvuWOhuWPsuaAp+S7t+avlDwvaDI+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJib29zdC1zdW1tYXJ5LWNvbnRyb2xzXCI+XG4gICAgICAgICAgPHNwYW4gY2xhc3M9XCJib29zdC1yYXRlLWxhYmVsXCI+5b6u5L+h6LGG5rGH546HOjwvc3Bhbj5cbiAgICAgICAgICA8c2VsZWN0IHYtbW9kZWwubnVtYmVyPVwiY29pbnNQZXJZdWFuXCIgQGNoYW5nZT1cImZldGNoQm9vc3RTdW1tYXJ5XCIgY2xhc3M9XCJzZWxlY3QtbWluaVwiPlxuICAgICAgICAgICAgPG9wdGlvbiA6dmFsdWU9XCIxMFwiPuWuieWNky9XZWI6IDHlhYMgPSAxMOixhiAo5o6o6I2QKTwvb3B0aW9uPlxuICAgICAgICAgICAgPG9wdGlvbiA6dmFsdWU9XCI3XCI+aU9TOiAx5YWDID0gN+ixhjwvb3B0aW9uPlxuICAgICAgICAgIDwvc2VsZWN0PlxuICAgICAgICA8L2Rpdj5cbiAgICAgIDwvZGl2PlxuICAgICAgPGRpdiBjbGFzcz1cImNhcmQtaGludFwiPlxuICAgICAgICDmlbDmja7mupA6IOWQhOW5s+WPsOiuouWNleeuoeeQhumhtSBzY3JhcGUg5Zue54GMLiDlvq7kv6HosYYgw7cg5rGH546HID0g55yf5a6e5Lq65rCR5biB6Iqx6LS5LlxuICAgICAgPC9kaXY+XG5cbiAgICAgIDwhLS0g5rOo5oSPOiDlkI7lj7DlkIzmraXliqDng63orqLljZXml7bpgYfliLDnmbvlvZXlpLHmlYgsIOS4jeWGjeWcqOeci+adv+S4iuaYvuekuiBiYW5uZXIuXG4gICAgICAgICAgIGRhZW1vbiDmo4DmtYvliLDnmbvlvZXmgIHkuKLkuobkvJrnm7TmjqXlj5Hpgq7ku7bmj5DphpIgKOmZhOS6jOe7tOeggeaIquWbviwgNmgg5Y676YeNKSxcbiAgICAgICAgICAg6KeBIHd1Y2FpX3ZpZGVvczUvem9lL3F1YW50L2F1dG9fY29tbWVudF9yZXBseS5weTo6X21heWJlX3N5bmNfYm9vc3Rfb3JkZXJzLiAtLT5cblxuICAgICAgPCEtLSDop4bpopHlj7flvoXmlK/ku5jorqLljZXkuI3lho3lnKjnnIvmnb/kuIrlsZXnpLrmiavnoIHlhaXlj6M6IOaJuemHj+W7uuWlveWQjuebtOaOpemCruS7tumAmuefpSxcbiAgICAgICAgICAg55So5oi355m75b2V6KeG6aKR5Y+35Yqp5omL6K6i5Y2V6aG15omr56CB5LuY5qy+ICjop4EgYXV0b19ib29zdF93ZWl4aW4uX3NlbmRfc3VtbWFyeV9lbWFpbCkuIC0tPlxuXG4gICAgICA8ZGl2IHYtaWY9XCJib29zdFN1bW1hcnkucGxhdGZvcm1fc3VtbWFyeS5sZW5ndGggPT09IDBcIiBjbGFzcz1cImJvb3N0LWVtcHR5XCI+XG4gICAgICAgIOaaguaXoOaKleaUvuWOhuWPsi4g6LeR5LiA5qyhOlxuICAgICAgICA8Y29kZT5weXRob24gd3VjYWlfdmlkZW9zNS9ldGhhbi93ZWl4aW5fYm9vc3RfaGlzdG9yeV9pbXBvcnRlci5weTwvY29kZT5cbiAgICAgICAg5oqK5b6u5L+h6KeG6aKR5Y+36K6i5Y2V6aG15oqT5Zue5p2lLlxuICAgICAgPC9kaXY+XG4gICAgICA8ZGl2IHYtZWxzZSBjbGFzcz1cImJvb3N0LXBsYXRmb3Jtc1wiPlxuICAgICAgICA8ZGl2IHYtZm9yPVwicHMgaW4gYm9vc3RTdW1tYXJ5LnBsYXRmb3JtX3N1bW1hcnlcIiA6a2V5PVwicHMucGxhdGZvcm1cIiBjbGFzcz1cImJvb3N0LXBjYXJkXCI+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cInBjYXJkLWhlYWRcIj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwicGNhcmQtbmFtZVwiPnt7IHBsYXRmb3JtTGFiZWwocHMucGxhdGZvcm0pIH19PC9zcGFuPlxuICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJwY2FyZC1wZXJpb2RcIiB2LWlmPVwicHMuZmlyc3RfYm9vc3RfYXRcIj5cbiAgICAgICAgICAgICAge3sgcHMuZmlyc3RfYm9vc3RfYXQgfX0gfiB7eyBwcy5sYXN0X2Jvb3N0X2F0IH19XG4gICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cInBjYXJkLWdyaWRcIj5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljXCI+XG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljLW51bVwiPnt7IHBzLm9yZGVyX2NvdW50IH19PC9kaXY+XG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljLWxhYmVsXCI+5oqV5pS+5Y2V5pWwPC9kaXY+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljXCI+XG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljLW51bVwiPnt7IHBzLnZpZGVvX2NvdW50IH19PC9kaXY+XG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljLWxhYmVsXCI+5oqV5pS+6KeG6aKR5pWwPC9kaXY+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljIHBtZXRyaWMtY29zdFwiPlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYy1udW1cIj57eyBmb3JtYXRDb3N0KHBzLnRvdGFsX2Nvc3QsIHBzLnBsYXRmb3JtKSB9fTwvZGl2PlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYy1sYWJlbFwiPlxuICAgICAgICAgICAgICAgIOe0r+iuoeiKsei0uVxuICAgICAgICAgICAgICAgIDxzcGFuIHYtaWY9XCJwcy5wbGF0Zm9ybSA9PT0gJ3dlaXhpbicgJiYgcHMudG90YWxfY29zdF9jb2lucyAhPSBudWxsXCJcbiAgICAgICAgICAgICAgICAgICAgICBjbGFzcz1cInBtZXRyaWMtc3ViXCI+KHt7IGZvcm1hdE51bShwcy50b3RhbF9jb3N0X2NvaW5zKSB9fSDosYYpPC9zcGFuPlxuICAgICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBtZXRyaWNcIj5cbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBtZXRyaWMtbnVtXCI+e3sgZm9ybWF0TnVtKHBzLnRvdGFsX3BsYXkpIH19PC9kaXY+XG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljLWxhYmVsXCI+5oC75pKt5pS+PC9kaXY+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljXCI+XG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbWV0cmljLW51bVwiPnt7IGZvcm1hdE51bShwcy50b3RhbF9saWtlKSB9fTwvZGl2PlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYy1sYWJlbFwiPuaAu+eCuei1njwvZGl2PlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYyBwbWV0cmljLWZvbGxvd1wiPlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYy1udW1cIj57eyBmb3JtYXROdW0ocHMudG90YWxfZm9sbG93KSB9fTwvZGl2PlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYy1sYWJlbFwiPua2qOeyiTwvZGl2PlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYyBwbWV0cmljLXJvaVwiPlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwicG1ldHJpYy1udW1cIj57eyBwcy5jb3N0X3Blcl9mb2xsb3cgIT0gbnVsbCA/ICfCpScgKyBwcy5jb3N0X3Blcl9mb2xsb3cgOiAnLScgfX08L2Rpdj5cbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBtZXRyaWMtbGFiZWxcIj7mr4/mtqggMSDnsonmiJDmnKw8L2Rpdj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBtZXRyaWMgcG1ldHJpYy1yb2lcIj5cbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBtZXRyaWMtbnVtXCI+e3sgcHMuY29zdF9wZXJfbGlrZSAhPSBudWxsID8gJ8KlJyArIHBzLmNvc3RfcGVyX2xpa2UgOiAnLScgfX08L2Rpdj5cbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBtZXRyaWMtbGFiZWxcIj7mr4/kuKrotZ7miJDmnKw8L2Rpdj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICA8L2Rpdj5cbiAgICAgIDwvZGl2PlxuXG4gICAgICA8IS0tIOacgOi/kSBOIOWkqeiuouWNleaYjue7hiAo6buY6K6k5bGV5byALCDlm6DkuLrov5nmmK9cIuaYqOWkqeaKleS6huS7gOS5iCDnjrDlnKjot5HlvpfmgI7kuYjmoLdcIuS4u+ivieaxgikgLS0+XG4gICAgICA8ZGV0YWlscyB2LWlmPVwiYm9vc3RTdW1tYXJ5LnJlY2VudF9vcmRlcnMgJiYgYm9vc3RTdW1tYXJ5LnJlY2VudF9vcmRlcnMubGVuZ3RoID4gMFwiXG4gICAgICAgICAgICAgICBjbGFzcz1cImJvb3N0LXRvcFwiIG9wZW4+XG4gICAgICAgIDxzdW1tYXJ5PlxuICAgICAgICAgIOacgOi/kSB7eyBib29zdFN1bW1hcnkucmVjZW50X2RheXMgfHwgNyB9fSDlpKnmipXmlL7mmI7nu4ZcbiAgICAgICAgICAoe3sgYm9vc3RTdW1tYXJ5LnJlY2VudF9vcmRlcnMubGVuZ3RoIH19IOWNlSkg4oCUIOeciyBhY3RpdmUg5Y2V5a6e5pe26L+b5bqmXG4gICAgICAgIDwvc3VtbWFyeT5cbiAgICAgICAgPHRhYmxlIGNsYXNzPVwiYm9vc3QtdG9wLXRhYmxlXCI+XG4gICAgICAgICAgPHRoZWFkPlxuICAgICAgICAgICAgPHRyPlxuICAgICAgICAgICAgICA8dGggY2xhc3M9XCJ0aC1sZWZ0XCI+5oqV5pS+5pe26Ze0PC90aD5cbiAgICAgICAgICAgICAgPHRoPuW5s+WPsDwvdGg+XG4gICAgICAgICAgICAgIDx0aD7nirbmgIE8L3RoPlxuICAgICAgICAgICAgICA8dGggY2xhc3M9XCJ0aC1sZWZ0XCI+6KeG6aKRPC90aD5cbiAgICAgICAgICAgICAgPHRoPuW3suiKsTwvdGg+XG4gICAgICAgICAgICAgIDx0aD7mkq3mlL48L3RoPlxuICAgICAgICAgICAgICA8dGg+6LWePC90aD5cbiAgICAgICAgICAgICAgPHRoPuivhDwvdGg+XG4gICAgICAgICAgICAgIDx0aD7nsok8L3RoPlxuICAgICAgICAgICAgICA8dGg+5Y2V57KJ5oiQ5pysPC90aD5cbiAgICAgICAgICAgICAgPHRoIGNsYXNzPVwidGgtbGVmdFwiPuaVsOaNruabtOaWsDwvdGg+XG4gICAgICAgICAgICA8L3RyPlxuICAgICAgICAgIDwvdGhlYWQ+XG4gICAgICAgICAgPHRib2R5PlxuICAgICAgICAgICAgPHRyIHYtZm9yPVwibyBpbiBib29zdFN1bW1hcnkucmVjZW50X29yZGVyc1wiIDprZXk9XCJvLmJvb3N0X2lkXCJcbiAgICAgICAgICAgICAgICA6Y2xhc3M9XCJbJ29yZGVyLXJvdycsICdvcmRlci0nICsgby5ib29zdF9zdGF0dXNdXCI+XG4gICAgICAgICAgICAgIDx0ZCBjbGFzcz1cInRkLWxlZnQgdGQtdGltZVwiPnt7IG8uYm9vc3Rfc3RhcnRlZF9hdCB8fCAnLScgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgcGxhdGZvcm1TaG9ydChvLnBsYXRmb3JtKSB9fTwvdGQ+XG4gICAgICAgICAgICAgIDx0ZD5cbiAgICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cImJvb3N0LXRhZ1wiIDpjbGFzcz1cIidib29zdC0nICsgby5ib29zdF9zdGF0dXNcIj5cbiAgICAgICAgICAgICAgICAgIHt7IGJvb3N0U3RhdHVzVGV4dChvLmJvb3N0X3N0YXR1cykgfX1cbiAgICAgICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICAgIDwvdGQ+XG4gICAgICAgICAgICAgIDx0ZCBjbGFzcz1cInRkLWxlZnQgdGl0bGUtY2VsbFwiPlxuICAgICAgICAgICAgICAgIDxhIHYtaWY9XCJvLnZpZGVvX3VybFwiIDpocmVmPVwiby52aWRlb191cmxcIiB0YXJnZXQ9XCJfYmxhbmtcIj5cbiAgICAgICAgICAgICAgICAgIHt7IG8udmlkZW9fdGl0bGUgfHwgJyjml6DmoIfpopgpJyB9fVxuICAgICAgICAgICAgICAgIDwvYT5cbiAgICAgICAgICAgICAgICA8c3BhbiB2LWVsc2U+e3sgby52aWRlb190aXRsZSB8fCAnKOaXoOagh+mimCknIH19PC9zcGFuPlxuICAgICAgICAgICAgICA8L3RkPlxuICAgICAgICAgICAgICA8dGQgY2xhc3M9XCJjZWxsLWNvc3RcIj5cbiAgICAgICAgICAgICAgICB7eyBmb3JtYXRDb3N0KG8uY29zdF9hbW91bnQsIG8ucGxhdGZvcm0pIH19XG4gICAgICAgICAgICAgICAgPHNwYW4gdi1pZj1cIm8ucGxhdGZvcm0gPT09ICd3ZWl4aW4nICYmIG8uY29zdF9jb2lucyAhPSBudWxsXCIgY2xhc3M9XCJjb3N0LWNvaW5zXCI+XG4gICAgICAgICAgICAgICAgICAoe3sgZm9ybWF0TnVtKG8uY29zdF9jb2lucykgfX0g6LGGKVxuICAgICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgICAgPC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IGZvcm1hdE51bShvLnBsYXlfY291bnQpIH19PC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IGZvcm1hdE51bShvLmxpa2VfY291bnQpIH19PC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IGZvcm1hdE51bShvLmNvbW1lbnRfY291bnQpIH19PC90ZD5cbiAgICAgICAgICAgICAgPHRkIGNsYXNzPVwiY2VsbC1mb2xsb3dcIj57eyBmb3JtYXROdW0oby5mb2xsb3dfY291bnQpIH19PC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IG8uY29zdF9wZXJfZm9sbG93ICE9IG51bGwgPyAnwqUnICsgby5jb3N0X3Blcl9mb2xsb3cgOiAnLScgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQgY2xhc3M9XCJ0ZC1sZWZ0IHRkLW1ldGFcIj57eyBvLnN0YXRzX3VwZGF0ZWRfYXQgfHwgJy0nIH19PC90ZD5cbiAgICAgICAgICAgIDwvdHI+XG4gICAgICAgICAgPC90Ym9keT5cbiAgICAgICAgPC90YWJsZT5cbiAgICAgIDwvZGV0YWlscz5cblxuICAgICAgPGRldGFpbHMgdi1pZj1cImJvb3N0U3VtbWFyeS50b3BfdmlkZW9zX2J5X2ZvbGxvd19hZ2dyZWdhdGVkLmxlbmd0aCA+IDBcIiBjbGFzcz1cImJvb3N0LXRvcFwiPlxuICAgICAgICA8c3VtbWFyeT7mtqjnsokgVG9wIDIwIOinhumikSAo57Sv6K6hKSDigJQg55yL55yL5ZOq5Lqb6KeG6aKR5YC85b6X57un57ut5oqVPC9zdW1tYXJ5PlxuICAgICAgICA8dGFibGUgY2xhc3M9XCJib29zdC10b3AtdGFibGVcIj5cbiAgICAgICAgICA8dGhlYWQ+XG4gICAgICAgICAgICA8dHI+XG4gICAgICAgICAgICAgIDx0aD7op4bpopE8L3RoPlxuICAgICAgICAgICAgICA8dGg+5bmz5Y+wPC90aD5cbiAgICAgICAgICAgICAgPHRoPuaKleaUvuasoeaVsDwvdGg+XG4gICAgICAgICAgICAgIDx0aD7ntK/orqHoirHotLk8L3RoPlxuICAgICAgICAgICAgICA8dGg+5oC75pKt5pS+PC90aD5cbiAgICAgICAgICAgICAgPHRoPuaAu+eCuei1njwvdGg+XG4gICAgICAgICAgICAgIDx0aD7mtqjnsok8L3RoPlxuICAgICAgICAgICAgICA8dGg+5q+P5raoIDEg57KJ5oiQ5pysPC90aD5cbiAgICAgICAgICAgIDwvdHI+XG4gICAgICAgICAgPC90aGVhZD5cbiAgICAgICAgICA8dGJvZHk+XG4gICAgICAgICAgICA8dHIgdi1mb3I9XCJ2IGluIGJvb3N0U3VtbWFyeS50b3BfdmlkZW9zX2J5X2ZvbGxvd19hZ2dyZWdhdGVkXCIgOmtleT1cInYucGxhdGZvcm0gKyAnLScgKyB2LnZpZGVvX3B1Ymxpc2hfaWRcIj5cbiAgICAgICAgICAgICAgPHRkIGNsYXNzPVwidGl0bGUtY2VsbFwiPlxuICAgICAgICAgICAgICAgIDxhIHYtaWY9XCJ2LnZpZGVvX3VybFwiIDpocmVmPVwidi52aWRlb191cmxcIiB0YXJnZXQ9XCJfYmxhbmtcIj57eyB2LnZpZGVvX3RpdGxlIHx8ICco5peg5qCH6aKYKScgfX08L2E+XG4gICAgICAgICAgICAgICAgPHNwYW4gdi1lbHNlPnt7IHYudmlkZW9fdGl0bGUgfHwgJyjml6DmoIfpopgpJyB9fTwvc3Bhbj5cbiAgICAgICAgICAgICAgPC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IHBsYXRmb3JtTGFiZWwodi5wbGF0Zm9ybSkgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgdi5ib29zdF9jb3VudCB9fTwvdGQ+XG4gICAgICAgICAgICAgIDx0ZD57eyBmb3JtYXRDb3N0KHYudG90YWxfY29zdCwgdi5wbGF0Zm9ybSkgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgZm9ybWF0TnVtKHYudG90YWxfcGxheSkgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgZm9ybWF0TnVtKHYudG90YWxfbGlrZSkgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQgY2xhc3M9XCJjZWxsLWZvbGxvd1wiPnt7IGZvcm1hdE51bSh2LnRvdGFsX2ZvbGxvdykgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgdi5jb3N0X3Blcl9mb2xsb3cgIT0gbnVsbCA/ICfCpScgKyB2LmNvc3RfcGVyX2ZvbGxvdyA6ICctJyB9fTwvdGQ+XG4gICAgICAgICAgICA8L3RyPlxuICAgICAgICAgIDwvdGJvZHk+XG4gICAgICAgIDwvdGFibGU+XG4gICAgICA8L2RldGFpbHM+XG4gICAgPC9kaXY+XG5cbiAgICA8ZGl2IHYtaWY9XCJlcnJvck1zZ1wiIGNsYXNzPVwiZXJyb3ItYmFubmVyXCI+e3sgZXJyb3JNc2cgfX08L2Rpdj5cblxuICAgIDwhLS0g6KGo5aS0ICg1IOWIlzog6YCJ5LitICsg6KeG6aKR5L+h5oGvICsg6Leo5bmz5Y+wICsgMyDkuKrlubPlj7ApIC0tPlxuICAgIDxkaXYgdi1pZj1cInZpZGVvcy5sZW5ndGggPiAwXCIgY2xhc3M9XCJkYXNoYm9hcmQtdGFibGVcIj5cbiAgICAgIDxkaXYgY2xhc3M9XCJ0YWJsZS1yb3cgdGFibGUtaGVhZFwiPlxuICAgICAgICA8ZGl2IGNsYXNzPVwiY29sLWNoZWNrXCI+XG4gICAgICAgICAgPGlucHV0IHR5cGU9XCJjaGVja2JveFwiXG4gICAgICAgICAgICAgICAgIDpjaGVja2VkPVwiaXNBbGxTZWxlY3RlZFwiXG4gICAgICAgICAgICAgICAgIDppbmRldGVybWluYXRlLnByb3A9XCJpc1BhcnRpYWxTZWxlY3RlZFwiXG4gICAgICAgICAgICAgICAgIEBjaGFuZ2U9XCJ0b2dnbGVTZWxlY3RBbGwoJGV2ZW50LnRhcmdldC5jaGVja2VkKVwiXG4gICAgICAgICAgICAgICAgIHRpdGxlPVwi5YWo6YCJL+WFqOS4jemAieW9k+WJjemhtVwiIC8+XG4gICAgICAgIDwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwiY29sLXZpZGVvXCI+6KeG6aKRPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJjb2wtdG90YWxzXCI+6Leo5bmz5Y+w5ZCI6K6hPC9kaXY+XG4gICAgICAgIDxkaXYgdi1mb3I9XCJwIGluIFRBUkdFVF9QTEFURk9STVNcIiA6a2V5PVwicC5rZXlcIiBjbGFzcz1cImNvbC1wbGF0Zm9ybVwiPlxuICAgICAgICAgIHt7IHAubGFiZWwgfX1cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cblxuICAgICAgPCEtLSDmlbDmja7ooYwgLS0+XG4gICAgICA8ZGl2IHYtZm9yPVwidiBpbiB2aWRlb3NcIiA6a2V5PVwidi5hcnRpY2xlX2lkXCJcbiAgICAgICAgICAgY2xhc3M9XCJ0YWJsZS1yb3cgZGF0YS1yb3dcIlxuICAgICAgICAgICA6Y2xhc3M9XCJbXG4gICAgICAgICAgICAgJ3RvcC0nICsgdi50b3BfYm9vc3RfbGV2ZWwsXG4gICAgICAgICAgICAgeyAncm93LWhhcy1kZWFkJzogdi5oYXNfZGVhZF9wbGF0Zm9ybSAmJiB2LnRvcF9ib29zdF9sZXZlbCAhPT0gJ2RlYWQnLFxuICAgICAgICAgICAgICAgJ3Jvdy1zZWxlY3RlZCc6IHNlbGVjdGVkQXJ0aWNsZUlkcy5oYXModi5hcnRpY2xlX2lkKSB9XG4gICAgICAgICAgIF1cIj5cbiAgICAgICAgPCEtLSDpgInkuK3liJcgLS0+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJjb2wtY2hlY2tcIj5cbiAgICAgICAgICA8aW5wdXQgdHlwZT1cImNoZWNrYm94XCJcbiAgICAgICAgICAgICAgICAgOmNoZWNrZWQ9XCJzZWxlY3RlZEFydGljbGVJZHMuaGFzKHYuYXJ0aWNsZV9pZClcIlxuICAgICAgICAgICAgICAgICBAY2hhbmdlPVwidG9nZ2xlUm93U2VsZWN0ZWQodi5hcnRpY2xlX2lkLCAkZXZlbnQudGFyZ2V0LmNoZWNrZWQpXCIgLz5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDwhLS0g6KeG6aKR5YiXIC0tPlxuICAgICAgICA8ZGl2IGNsYXNzPVwiY29sLXZpZGVvXCI+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cInZpZGVvLXRpdGxlLXJvd1wiPlxuICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJsdmwtYmFkZ2VcIiA6Y2xhc3M9XCInbHZsLScgKyB2LnRvcF9ib29zdF9sZXZlbFwiXG4gICAgICAgICAgICAgICAgICA6dGl0bGU9XCJ0b3BMZXZlbFRvb2x0aXAodilcIj57eyBsZXZlbFRleHQodi50b3BfYm9vc3RfbGV2ZWwpIH19PC9zcGFuPlxuICAgICAgICAgICAgPCEtLSDmnInku7vkuIDlubPlj7AgZGVhZCDkvYbnu7zlkIjnrYnnuqfmmK8gZ29vZC9tdXN0IOeahCwg6aKd5aSW5oyC5Liq57qi6Imy5o+Q6YaS5b6956ugIC0tPlxuICAgICAgICAgICAgPHNwYW4gdi1pZj1cInYuaGFzX2RlYWRfcGxhdGZvcm0gJiYgdi50b3BfYm9vc3RfbGV2ZWwgIT09ICdkZWFkJ1wiXG4gICAgICAgICAgICAgICAgICBjbGFzcz1cImx2bC1iYWRnZSBsdmwtZGVhZCBzbWFsbFwiXG4gICAgICAgICAgICAgICAgICA6dGl0bGU9XCJkZWFkUGxhdGZvcm1Ub29sdGlwKHYpXCI+6YOo5YiG5bmz5Y+w6ZmQ5rWBPC9zcGFuPlxuICAgICAgICAgICAgPHJvdXRlci1saW5rIDp0bz1cImAvem9lLyR7di5hcnRpY2xlX2lkfWBcIiBjbGFzcz1cInZpZGVvLXRpdGxlLWxpbmtcIj5cbiAgICAgICAgICAgICAge3sgdi52aWRlb190aXRsZSB8fCAnKOaXoOagh+mimCknIH19XG4gICAgICAgICAgICA8L3JvdXRlci1saW5rPlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJ2aWRlby1tZXRhXCI+XG4gICAgICAgICAgICA8IS0tIOaYvuekuuaXtumXtOWSjOaOkuW6j+mUruWvuem9kDog5LyY5YWI5bGV56S65b6u5L+h6KeG6aKR5Y+355qE5Y+R5biD5pe26Ze0ICjmjpLluo/lsLHmmK/mjInov5nkuKopLFxuICAgICAgICAgICAgICAgICDmsqHlj5Hlvq7kv6HnmoTmiY0gZmFsbGJhY2sg5YiwIDQg5bmz5Y+w5Lit5pyA5pep5LiA5qyh55qEIFwi6aaW5Y+RXCIg5pe26Ze0LCDpgb/lhY3nnIvotbfmnaXlg4/msqHmjpLluo8uIC0tPlxuICAgICAgICAgICAgPHNwYW4gdi1pZj1cInYucGxhdGZvcm1zLndlaXhpbj8ucHVibGlzaGVkX2F0XCI+XG4gICAgICAgICAgICAgIOinhumikeWPtyB7eyBmb3JtYXREYXRlVGltZSh2LnBsYXRmb3Jtcy53ZWl4aW4ucHVibGlzaGVkX2F0KSB9fVxuICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgPHNwYW4gdi1lbHNlLWlmPVwidi5maXJzdF9wdWJsaXNoZWRfYXRcIj7pppblj5Ege3sgZm9ybWF0RGF0ZVRpbWUodi5maXJzdF9wdWJsaXNoZWRfYXQpIH19PC9zcGFuPlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICA8L2Rpdj5cblxuICAgICAgICA8IS0tIOi3qOW5s+WPsOWQiOiuoSAtLT5cbiAgICAgICAgPGRpdiBjbGFzcz1cImNvbC10b3RhbHNcIj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwidG90YWwtbGluZVwiPlxuICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJtZXRyaWNcIj48c3BhbiBjbGFzcz1cIm1ldHJpYy1udW1cIj57eyBmb3JtYXROdW0odi50b3RhbF92aWV3cykgfX08L3NwYW4+PHNwYW4gY2xhc3M9XCJtZXRyaWMtbGFiZWxcIj7mtY/op4g8L3NwYW4+PC9zcGFuPlxuICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJtZXRyaWNcIj48c3BhbiBjbGFzcz1cIm1ldHJpYy1udW1cIj57eyBmb3JtYXROdW0odi50b3RhbF9saWtlcykgfX08L3NwYW4+PHNwYW4gY2xhc3M9XCJtZXRyaWMtbGFiZWxcIj7ngrnotZ48L3NwYW4+PC9zcGFuPlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJ0b3RhbC1saW5lXCI+XG4gICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1ldHJpY1wiPjxzcGFuIGNsYXNzPVwibWV0cmljLW51bVwiPnt7IGZvcm1hdE51bSh2LnRvdGFsX2NvbW1lbnRzKSB9fTwvc3Bhbj48c3BhbiBjbGFzcz1cIm1ldHJpYy1sYWJlbFwiPuivhOiuujwvc3Bhbj48L3NwYW4+XG4gICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1ldHJpY1wiPjxzcGFuIGNsYXNzPVwibWV0cmljLW51bSByYXRpby1udW1cIiA6Y2xhc3M9XCJ7IGhvdDogdi50b3RhbF9saWtlc19yYXRpbyA+PSAwLjAzIH1cIj5cbiAgICAgICAgICAgICAge3sgZm9ybWF0UGVyY2VudCh2LnRvdGFsX2xpa2VzX3JhdGlvKSB9fVxuICAgICAgICAgICAgPC9zcGFuPjxzcGFuIGNsYXNzPVwibWV0cmljLWxhYmVsXCI+6LWe546HPC9zcGFuPjwvc3Bhbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG5cbiAgICAgICAgPCEtLSDlkITlubPlj7DliJcgLS0+XG4gICAgICAgIDxkaXYgdi1mb3I9XCJwIGluIFRBUkdFVF9QTEFURk9STVNcIiA6a2V5PVwicC5rZXlcIlxuICAgICAgICAgICAgIGNsYXNzPVwiY29sLXBsYXRmb3JtXCJcbiAgICAgICAgICAgICA6Y2xhc3M9XCJbJ3BsYXQtY2VsbCcsIGdldFBsYXRmb3JtTGV2ZWxDbGFzcyh2LCBwLmtleSldXCI+XG4gICAgICAgICAgPHRlbXBsYXRlIHYtaWY9XCJ2LnBsYXRmb3Jtc1twLmtleV1cIj5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJwbGF0LWxpbmVcIj5cbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJsdmwtYmFkZ2Ugc21hbGxcIiA6Y2xhc3M9XCInbHZsLScgKyAodi5wbGF0Zm9ybXNbcC5rZXldLmJvb3N0X3Njb3JlPy5sZXZlbCB8fCAnd2F0Y2gnKVwiXG4gICAgICAgICAgICAgICAgICAgIDp0aXRsZT1cInYucGxhdGZvcm1zW3Aua2V5XS5ib29zdF9zY29yZT8ucmVhc29uXCI+XG4gICAgICAgICAgICAgICAge3sgbGV2ZWxUZXh0KHYucGxhdGZvcm1zW3Aua2V5XS5ib29zdF9zY29yZT8ubGV2ZWwpIH19XG4gICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgICAgPCEtLSDlubPlj7Dnoazkv6Hlj7cgKHJldmlld2luZy9wcml2YXRlL3JlY29tbWVuZGVkX2Jsb2NrZWQg6L+Z56eNLCBkZWFkL2ZvcmJpZGRlbiDlt7Lnu4/lnKggbHZsLWJhZGdlIOmHjOaYvuekuuS6hikgLS0+XG4gICAgICAgICAgICAgIDxzcGFuIHYtaWY9XCJzaG91bGRTaG93UGxhdGZvcm1TdGF0dXModi5wbGF0Zm9ybXNbcC5rZXldKVwiXG4gICAgICAgICAgICAgICAgICAgIGNsYXNzPVwic3RhdHVzLXRhZ1wiIDpjbGFzcz1cIidzdGF0dXMtJyArIHYucGxhdGZvcm1zW3Aua2V5XS5wbGF0Zm9ybV9zdGF0dXNcIlxuICAgICAgICAgICAgICAgICAgICA6dGl0bGU9XCJ2LnBsYXRmb3Jtc1twLmtleV0ucGxhdGZvcm1fc3RhdHVzX2Rlc2MgfHwgJydcIj5cbiAgICAgICAgICAgICAgICB7eyBwbGF0Zm9ybVN0YXR1c1RleHQodi5wbGF0Zm9ybXNbcC5rZXldLnBsYXRmb3JtX3N0YXR1cykgfX1cbiAgICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgICA8YSB2LWlmPVwidi5wbGF0Zm9ybXNbcC5rZXldLnB1Ymxpc2hlZF9saW5rXCJcbiAgICAgICAgICAgICAgICAgOmhyZWY9XCJ2LnBsYXRmb3Jtc1twLmtleV0ucHVibGlzaGVkX2xpbmtcIiB0YXJnZXQ9XCJfYmxhbmtcIlxuICAgICAgICAgICAgICAgICBjbGFzcz1cInBsYXQtbGlua1wiIDp0aXRsZT1cIifmiZPlvIDlj5HluIPpk77mjqUnXCI+4oaXPC9hPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwicGxhdC1saW5lXCI+XG4gICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibWV0cmljXCI+PHNwYW4gY2xhc3M9XCJtZXRyaWMtbnVtXCI+e3sgZm9ybWF0TnVtKHYucGxhdGZvcm1zW3Aua2V5XS52aWV3cykgfX08L3NwYW4+PHNwYW4gY2xhc3M9XCJtZXRyaWMtbGFiZWxcIj7mtY/op4g8L3NwYW4+PC9zcGFuPlxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1ldHJpY1wiPjxzcGFuIGNsYXNzPVwibWV0cmljLW51bVwiPnt7IGZvcm1hdE51bSh2LnBsYXRmb3Jtc1twLmtleV0ubGlrZXMpIH19PC9zcGFuPjxzcGFuIGNsYXNzPVwibWV0cmljLWxhYmVsXCI+6LWePC9zcGFuPjwvc3Bhbj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInBsYXQtbGluZVwiPlxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1ldHJpY1wiPjxzcGFuIGNsYXNzPVwibWV0cmljLW51bVwiPnt7IGZvcm1hdE51bSh2LnBsYXRmb3Jtc1twLmtleV0uY29tbWVudHMpIH19PC9zcGFuPjxzcGFuIGNsYXNzPVwibWV0cmljLWxhYmVsXCI+6K+E6K66PC9zcGFuPjwvc3Bhbj5cbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJtZXRyaWNcIj5cbiAgICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1ldHJpYy1udW0gcmF0aW8tbnVtXCIgOmNsYXNzPVwieyBob3Q6ICh2LnBsYXRmb3Jtc1twLmtleV0uYm9vc3Rfc2NvcmU/Lmxpa2VzX3JhdGlvIHx8IDApID49IDAuMDMgfVwiPlxuICAgICAgICAgICAgICAgICAge3sgZm9ybWF0UGVyY2VudCh2LnBsYXRmb3Jtc1twLmtleV0uYm9vc3Rfc2NvcmU/Lmxpa2VzX3JhdGlvIHx8IDApIH19XG4gICAgICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibWV0cmljLWxhYmVsXCI+6LWe546HPC9zcGFuPlxuICAgICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDxkaXYgdi1pZj1cInYucGxhdGZvcm1zW3Aua2V5XS5sYXRlc3RfYm9vc3Rfc3RhdHVzXCIgY2xhc3M9XCJwbGF0LWxpbmVcIj5cbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJib29zdC10YWdcIiA6Y2xhc3M9XCInYm9vc3QtJyArIHYucGxhdGZvcm1zW3Aua2V5XS5sYXRlc3RfYm9vc3Rfc3RhdHVzXCI+XG4gICAgICAgICAgICAgICAg5Yqg54OtOiB7eyBib29zdFN0YXR1c1RleHQodi5wbGF0Zm9ybXNbcC5rZXldLmxhdGVzdF9ib29zdF9zdGF0dXMpIH19XG4gICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvdGVtcGxhdGU+XG4gICAgICAgICAgPGRpdiB2LWVsc2UgY2xhc3M9XCJwbGF0LWVtcHR5XCI+5pyq5Y+R5biDPC9kaXY+XG4gICAgICAgIDwvZGl2PlxuICAgICAgPC9kaXY+XG4gICAgPC9kaXY+XG5cbiAgICA8ZGl2IHYtaWY9XCJsb2FkaW5nXCIgY2xhc3M9XCJsb2FkaW5nXCI+5Yqg6L295LitLi4uPC9kaXY+XG4gICAgPGRpdiB2LWlmPVwiIWxvYWRpbmcgJiYgdmlkZW9zLmxlbmd0aCA9PT0gMCAmJiAhZXJyb3JNc2dcIiBjbGFzcz1cImVtcHR5XCI+XG4gICAgICDmiYDpgInml7bpl7TojIPlm7TlhoXmsqHmnInlj5HluIPmlbDmja5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g5om56YeP5Yqg54Ot5by556qXIC0tPlxuICAgIDxkaXYgdi1pZj1cImJhdGNoTW9kYWxPcGVuXCIgY2xhc3M9XCJtb2RhbC1tYXNrXCIgQGNsaWNrLnNlbGY9XCJjbG9zZUJhdGNoTW9kYWxcIj5cbiAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1jYXJkXCI+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1oZWFkXCI+XG4gICAgICAgICAgPGgzPuaJuemHj+WKoOeDrSDigJQge3sgc2VsZWN0ZWRWaWRlb3NGb3JNb2RhbC5sZW5ndGggfX0g5Liq6KeG6aKRPC9oMz5cbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwibW9kYWwtY2xvc2VcIiBAY2xpY2s9XCJjbG9zZUJhdGNoTW9kYWxcIj7DlzwvYnV0dG9uPlxuICAgICAgICA8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWJvZHlcIj5cbiAgICAgICAgICA8IS0tIOW5s+WPsOmAieaLqSAtLT5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtcm93XCI+XG4gICAgICAgICAgICA8bGFiZWw+5bmz5Y+wPC9sYWJlbD5cbiAgICAgICAgICAgIDxkaXY+XG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cInJhZGlvLWlubGluZVwiPlxuICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwicmFkaW9cIiB2YWx1ZT1cIndlaXhpblwiIHYtbW9kZWw9XCJiYXRjaEZvcm0ucGxhdGZvcm1cIiAvPlxuICAgICAgICAgICAgICAgIOW+ruS/oeinhumikeWPtyAo5b6u5L+h6LGGLCDmj5DkuqTlkI7pnIDopoHmiYvmnLrmiavnoIEpXG4gICAgICAgICAgICAgIDwvbGFiZWw+XG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cInJhZGlvLWlubGluZVwiPlxuICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwicmFkaW9cIiB2YWx1ZT1cImRvdXlpblwiIHYtbW9kZWw9XCJiYXRjaEZvcm0ucGxhdGZvcm1cIiAvPlxuICAgICAgICAgICAgICAgIOaKlumfsyBET1UrICjotKbmiLfkvZnpop3miaPmrL4sIOWFqOiHquWKqClcbiAgICAgICAgICAgICAgPC9sYWJlbD5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvZGl2PlxuXG4gICAgICAgICAgPCEtLSDpgInkuK3nmoTop4bpopHmuIXljZUgLS0+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLXJvd1wiPlxuICAgICAgICAgICAgPGxhYmVsPumAieS4reinhumikTwvbGFiZWw+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtdmlkZW9zXCI+XG4gICAgICAgICAgICAgIDxkaXYgdi1mb3I9XCJ2IGluIHNlbGVjdGVkVmlkZW9zRm9yTW9kYWxcIiA6a2V5PVwidi5hcnRpY2xlX2lkXCJcbiAgICAgICAgICAgICAgICAgICBjbGFzcz1cIm1vZGFsLXZpZGVvLWxpbmVcIlxuICAgICAgICAgICAgICAgICAgIDpjbGFzcz1cInsgJ3ZpZGVvLXNraXAnOiAhY2FuQm9vc3RPblBsYXRmb3JtKHYsIGJhdGNoRm9ybS5wbGF0Zm9ybSkgfVwiPlxuICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibW9kYWwtdmlkZW8tc3RhdHVzXCI+XG4gICAgICAgICAgICAgICAgICA8dGVtcGxhdGUgdi1pZj1cImNhbkJvb3N0T25QbGF0Zm9ybSh2LCBiYXRjaEZvcm0ucGxhdGZvcm0pXCI+XG4gICAgICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwib2stbWFya1wiPuKckzwvc3Bhbj5cbiAgICAgICAgICAgICAgICAgIDwvdGVtcGxhdGU+XG4gICAgICAgICAgICAgICAgICA8dGVtcGxhdGUgdi1lbHNlPlxuICAgICAgICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cInNraXAtbWFya1wiIHRpdGxlPVwi6K+l6KeG6aKR5Zyo5omA6YCJ5bmz5Y+w5rKh5Y+R5biDLCBiYXRjaCDot7Pov4dcIj7inJc8L3NwYW4+XG4gICAgICAgICAgICAgICAgICA8L3RlbXBsYXRlPlxuICAgICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1vZGFsLXZpZGVvLXRpdGxlXCI+e3sgdi52aWRlb190aXRsZSB8fCAnKOaXoOagh+mimCknIH19PC9zcGFuPlxuICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibW9kYWwtdmlkZW8tdnBpZFwiPlxuICAgICAgICAgICAgICAgICAgdnBfaWQ9e3sgZ2V0VnBJZCh2LCBiYXRjaEZvcm0ucGxhdGZvcm0pIHx8ICctJyB9fVxuICAgICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICAgIDxkaXYgdi1pZj1cInNlbGVjdGVkVmlkZW9zRm9yTW9kYWwubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJtb2RhbC1lbXB0eVwiPlxuICAgICAgICAgICAgICAgIOayoemAieS4reS7u+S9leinhumikVxuICAgICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvZGl2PlxuXG4gICAgICAgICAgPCEtLSDmipXmlL7lj4LmlbAgLS0+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLXJvd1wiPlxuICAgICAgICAgICAgPGxhYmVsPuavj+WNlemHkeminTwvbGFiZWw+XG4gICAgICAgICAgICA8ZGl2PlxuICAgICAgICAgICAgICA8aW5wdXQgdHlwZT1cIm51bWJlclwiIHYtbW9kZWwubnVtYmVyPVwiYmF0Y2hGb3JtLmFtb3VudFwiXG4gICAgICAgICAgICAgICAgICAgICBtaW49XCIxMDBcIiBzdGVwPVwiMTAwXCIgY2xhc3M9XCJtb2RhbC1pbnB1dFwiIC8+XG4gICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibW9kYWwtdW5pdFwiPlxuICAgICAgICAgICAgICAgIHt7IGJhdGNoRm9ybS5wbGF0Zm9ybSA9PT0gJ3dlaXhpbicgPyAn5b6u5L+h6LGGICg1MDAvMTAwMCDpooTorr4sIOWFtuS7lui1sOiHquWumuS5iSknIDogJ+WFgyAoRE9VKyDotbfmipUgMTAwKScgfX1cbiAgICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPC9kaXY+XG5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtcm93XCI+XG4gICAgICAgICAgICA8bGFiZWw+5pe26ZW/PC9sYWJlbD5cbiAgICAgICAgICAgIDxzZWxlY3Qgdi1tb2RlbC5udW1iZXI9XCJiYXRjaEZvcm0uZHVyYXRpb25cIiBjbGFzcz1cIm1vZGFsLXNlbGVjdFwiPlxuICAgICAgICAgICAgICA8b3B0aW9uIHYtZm9yPVwiaCBpbiBjdXJyZW50RHVyYXRpb25zXCIgOmtleT1cImhcIiA6dmFsdWU9XCJoXCI+e3sgaCB9fSDlsI/ml7Y8L29wdGlvbj5cbiAgICAgICAgICAgIDwvc2VsZWN0PlxuICAgICAgICAgIDwvZGl2PlxuXG4gICAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLXJvd1wiPlxuICAgICAgICAgICAgPGxhYmVsPuS8mOWFiOebruaghzwvbGFiZWw+XG4gICAgICAgICAgICA8c2VsZWN0IHYtbW9kZWw9XCJiYXRjaEZvcm0uZ29hbFwiIGNsYXNzPVwibW9kYWwtc2VsZWN0XCI+XG4gICAgICAgICAgICAgIDxvcHRpb24gdi1mb3I9XCJnIGluIGN1cnJlbnRHb2Fsc1wiIDprZXk9XCJnLmtleVwiIDp2YWx1ZT1cImcua2V5XCI+e3sgZy5sYWJlbCB9fTwvb3B0aW9uPlxuICAgICAgICAgICAgPC9zZWxlY3Q+XG4gICAgICAgICAgPC9kaXY+XG5cbiAgICAgICAgICA8IS0tIHdlaXhpbiDkuJPmnIk6IOaKleaUvue+pCAo6YCJ576k6Ieq5Yqo5aGr5oiQ5ZGYKSArIHRhcmdldF9jcmVhdG9ycyDlvq7osIMgLS0+XG4gICAgICAgICAgPGRpdiB2LWlmPVwiYmF0Y2hGb3JtLnBsYXRmb3JtID09PSAnd2VpeGluJ1wiIGNsYXNzPVwibW9kYWwtcm93XCI+XG4gICAgICAgICAgICA8bGFiZWw+5oqV5pS+576kPGJyIC8+PHNwYW4gY2xhc3M9XCJtb2RhbC1oaW50XCI+KOmAiee+pOiHquWKqOWhq+aIkOWRmCk8L3NwYW4+PC9sYWJlbD5cbiAgICAgICAgICAgIDxzZWxlY3Qgdi1tb2RlbC5udW1iZXI9XCJiYXRjaEZvcm0uYXVkaWVuY2VHcm91cElkXCIgQGNoYW5nZT1cImFwcGx5QXVkaWVuY2VHcm91cFwiXG4gICAgICAgICAgICAgICAgICAgIGNsYXNzPVwibW9kYWwtc2VsZWN0IG1vZGFsLWlucHV0LXdpZGVcIj5cbiAgICAgICAgICAgICAgPG9wdGlvbiA6dmFsdWU9XCJudWxsXCI+6Ieq5a6a5LmJIC8g5LiN5a6a5ZCRPC9vcHRpb24+XG4gICAgICAgICAgICAgIDxvcHRpb24gdi1mb3I9XCJnIGluIGF1ZGllbmNlR3JvdXBzXCIgOmtleT1cImcuaWRcIiA6dmFsdWU9XCJnLmlkXCI+XG4gICAgICAgICAgICAgICAge3sgZy5uYW1lIH19ICh7eyBnLmNyZWF0b3JfY291bnQgfX3kurope3sgZy5pc19kZWZhdWx0ID8gJyDimIXpu5jorqQnIDogJycgfX0g4oCUIHt7IGcuZGVzY3JpcHRpb24gfX1cbiAgICAgICAgICAgICAgPC9vcHRpb24+XG4gICAgICAgICAgICA8L3NlbGVjdD5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8ZGl2IHYtaWY9XCJiYXRjaEZvcm0ucGxhdGZvcm0gPT09ICd3ZWl4aW4nXCIgY2xhc3M9XCJtb2RhbC1yb3dcIj5cbiAgICAgICAgICAgIDxsYWJlbD7nm7jkvLzljZrkuLvlrprlkJE8YnIgLz48c3BhbiBjbGFzcz1cIm1vZGFsLWhpbnRcIj4o6YCX5Y+35YiG6ZqULCDnlZnnqbogPSDpu5jorqTkurrnvqQpPC9zcGFuPjwvbGFiZWw+XG4gICAgICAgICAgICA8aW5wdXQgdHlwZT1cInRleHRcIiB2LW1vZGVsPVwiYmF0Y2hGb3JtLnRhcmdldENyZWF0b3JzXCJcbiAgICAgICAgICAgICAgICAgICBwbGFjZWhvbGRlcj1cIuS+izog5p6B5a6i5pe26Ze0LEluZm9RLOmHj+WtkOS9jSzmnLrlmajkuYvlv4NcIlxuICAgICAgICAgICAgICAgICAgIGNsYXNzPVwibW9kYWwtaW5wdXQgbW9kYWwtaW5wdXQtd2lkZVwiIC8+XG4gICAgICAgICAgPC9kaXY+XG5cbiAgICAgICAgICA8IS0tIGRvdXlpbiDkuJPmnIk6IGF1ZGllbmNlX3BrZ19uYW1lIC0tPlxuICAgICAgICAgIDxkaXYgdi1pZj1cImJhdGNoRm9ybS5wbGF0Zm9ybSA9PT0gJ2RvdXlpbidcIiBjbGFzcz1cIm1vZGFsLXJvd1wiPlxuICAgICAgICAgICAgPGxhYmVsPuWumuWQkeWMheWQjTwvbGFiZWw+XG4gICAgICAgICAgICA8aW5wdXQgdHlwZT1cInRleHRcIiB2LW1vZGVsPVwiYmF0Y2hGb3JtLmF1ZGllbmNlUGtnTmFtZVwiXG4gICAgICAgICAgICAgICAgICAgcGxhY2Vob2xkZXI9XCJkb3VqaWEg5ZCO5Y+w5bey5bu655qE5a6a5ZCR5YyF5ZCNXCJcbiAgICAgICAgICAgICAgICAgICBjbGFzcz1cIm1vZGFsLWlucHV0IG1vZGFsLWlucHV0LXdpZGVcIiAvPlxuICAgICAgICAgIDwvZGl2PlxuXG4gICAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLXJvd1wiPlxuICAgICAgICAgICAgPGxhYmVsPuW8gOWFszwvbGFiZWw+XG4gICAgICAgICAgICA8ZGl2PlxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJjaGVjay1pbmxpbmVcIj5cbiAgICAgICAgICAgICAgICA8aW5wdXQgdHlwZT1cImNoZWNrYm94XCIgdi1tb2RlbD1cImJhdGNoRm9ybS5zdWJtaXRcIiAvPlxuICAgICAgICAgICAgICAgIOecn+aKlSAo5omje3sgYmF0Y2hGb3JtLnBsYXRmb3JtID09PSAnd2VpeGluJyA/ICflvq7kv6HosYYnIDogJ+i0puaIt+S9meminScgfX0hKVxuICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibW9kYWwtd2FyblwiIHYtaWY9XCJiYXRjaEZvcm0uc3VibWl0XCI+4pqgIOecn+aKleW8gOWQrzwvc3Bhbj5cbiAgICAgICAgICAgICAgPC9sYWJlbD5cbiAgICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiY2hlY2staW5saW5lXCI+XG4gICAgICAgICAgICAgICAgPGlucHV0IHR5cGU9XCJjaGVja2JveFwiIHYtbW9kZWw9XCJiYXRjaEZvcm0uZm9yY2VcIiAvPlxuICAgICAgICAgICAgICAgIGZvcmNlICjlkIzop4bpopHmnInmnKrnu5PmnZ/orqLljZXkuZ/lvLrooYzmlrDlu7opXG4gICAgICAgICAgICAgIDwvbGFiZWw+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1mb290ZXJcIj5cbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuLXNlY29uZGFyeVwiIEBjbGljaz1cImNsb3NlQmF0Y2hNb2RhbFwiPuWPlua2iDwvYnV0dG9uPlxuICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJidG4tcHJpbWFyeVwiIDpkaXNhYmxlZD1cImJhdGNoU3VibWl0dGluZyB8fCBzZWxlY3RlZFZpZGVvc0Zvck1vZGFsLmxlbmd0aCA9PT0gMFwiXG4gICAgICAgICAgICAgICAgICBAY2xpY2s9XCJzdWJtaXRCYXRjaEJvb3N0XCI+XG4gICAgICAgICAgICB7eyBiYXRjaFN1Ym1pdHRpbmcgPyAn5o+Q5Lqk5LitLi4uJyA6IChiYXRjaEZvcm0uc3VibWl0ID8gJ+ecn+aKlScgOiAnRHJ5LXJ1bicpIH19XG4gICAgICAgICAgPC9idXR0b24+XG4gICAgICAgIDwvZGl2PlxuICAgICAgPC9kaXY+XG4gICAgPC9kaXY+XG5cbiAgICA8IS0tIOaJuemHj+S7u+WKoei/m+W6piAtLT5cbiAgICA8ZGl2IHYtaWY9XCJiYXRjaEpvYlwiIGNsYXNzPVwiYmF0Y2gtam9iLWNhcmRcIj5cbiAgICAgIDxkaXYgY2xhc3M9XCJiYXRjaC1qb2ItaGVhZFwiPlxuICAgICAgICA8aDM+5om56YeP5Lu75YqhIHt7IGJhdGNoSm9iLnBsYXRmb3JtIH19IOKAlCDlhaXpmJ8ge3sgYmF0Y2hKb2IuaW5zZXJ0ZWQubGVuZ3RoIH19IOWNlVxuICAgICAgICAgICAgPHNwYW4gdi1pZj1cImJhdGNoSm9iLnJlamVjdGVkLmxlbmd0aCA+IDBcIiBjbGFzcz1cImJhdGNoLXJlamVjdGVkLW51bVwiPlxuICAgICAgICAgICAgICAo5ouS57udIHt7IGJhdGNoSm9iLnJlamVjdGVkLmxlbmd0aCB9fSDljZUpXG4gICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgIDwvaDM+XG4gICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cImNsb3NlQmF0Y2hKb2JcIj7DlzwvYnV0dG9uPlxuICAgICAgPC9kaXY+XG4gICAgICA8ZGl2IGNsYXNzPVwiY2FyZC1oaW50XCI+XG4gICAgICAgIOavjyA0IOenkui9ruivouS4gOasoeeKtuaAgS4gd2VpeGluIOiuouWNleaPkOS6pOWQjuWBnOWcqFwi5b6F5pSv5LuYXCIsIOeZu+W9leinhumikeWPt+WKqeaJi+iuouWNlemhteaJq+eggeS7mOasvi5cbiAgICAgIDwvZGl2PlxuICAgICAgPHRhYmxlIGNsYXNzPVwiYm9vc3QtdG9wLXRhYmxlXCI+XG4gICAgICAgIDx0aGVhZD5cbiAgICAgICAgICA8dHI+XG4gICAgICAgICAgICA8dGg+Ym9vc3RfaWQ8L3RoPlxuICAgICAgICAgICAgPHRoIGNsYXNzPVwidGgtbGVmdFwiPuinhumikTwvdGg+XG4gICAgICAgICAgICA8dGg+54q25oCBPC90aD5cbiAgICAgICAgICAgIDx0aD5vcmRlcl9pZDwvdGg+XG4gICAgICAgICAgICA8dGggY2xhc3M9XCJ0aC1sZWZ0XCI+5aSH5rOoICjplJnor6/kv6Hmga8pPC90aD5cbiAgICAgICAgICA8L3RyPlxuICAgICAgICA8L3RoZWFkPlxuICAgICAgICA8dGJvZHk+XG4gICAgICAgICAgPHRyIHYtZm9yPVwiaXRlbSBpbiBiYXRjaEpvYi5pdGVtc1wiIDprZXk9XCJpdGVtLmJvb3N0X2lkXCIgOmNsYXNzPVwiJ29yZGVyLScgKyBpdGVtLmJvb3N0X3N0YXR1c1wiPlxuICAgICAgICAgICAgPHRkPnt7IGl0ZW0uYm9vc3RfaWQgfX08L3RkPlxuICAgICAgICAgICAgPHRkIGNsYXNzPVwidGQtbGVmdCB0aXRsZS1jZWxsXCI+e3sgaXRlbS52aWRlb190aXRsZSB8fCAnLScgfX08L3RkPlxuICAgICAgICAgICAgPHRkPlxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cImJvb3N0LXRhZ1wiIDpjbGFzcz1cIidib29zdC0nICsgaXRlbS5ib29zdF9zdGF0dXNcIj5cbiAgICAgICAgICAgICAgICB7eyBib29zdFN0YXR1c1RleHQoaXRlbS5ib29zdF9zdGF0dXMpIH19XG4gICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgIDwvdGQ+XG4gICAgICAgICAgICA8dGQ+e3sgaXRlbS5vcmRlcl9pZCB8fCAnLScgfX08L3RkPlxuICAgICAgICAgICAgPHRkIGNsYXNzPVwidGQtbGVmdFwiPnt7IGl0ZW0uZXJyb3JfbWVzc2FnZSB8fCAnLScgfX08L3RkPlxuICAgICAgICAgIDwvdHI+XG4gICAgICAgICAgPHRyIHYtZm9yPVwicmVqIGluIGJhdGNoSm9iLnJlamVjdGVkXCIgOmtleT1cIidyZWotJyArIHJlai5pbmRleFwiIGNsYXNzPVwib3JkZXItZmFpbGVkXCI+XG4gICAgICAgICAgICA8dGQ+LTwvdGQ+XG4gICAgICAgICAgICA8dGQgY2xhc3M9XCJ0ZC1sZWZ0XCI+dnBfaWQ9e3sgcmVqLnZpZGVvX3B1Ymxpc2hfaWQgfX08L3RkPlxuICAgICAgICAgICAgPHRkPjxzcGFuIGNsYXNzPVwiYm9vc3QtdGFnIGJvb3N0LWZhaWxlZFwiPuagoemqjOaLkue7nTwvc3Bhbj48L3RkPlxuICAgICAgICAgICAgPHRkPi08L3RkPlxuICAgICAgICAgICAgPHRkIGNsYXNzPVwidGQtbGVmdFwiPnt7IHJlai5lcnJvciB9fTwvdGQ+XG4gICAgICAgICAgPC90cj5cbiAgICAgICAgPC90Ym9keT5cbiAgICAgIDwvdGFibGU+XG4gICAgPC9kaXY+XG5cbiAgICA8IS0tIOWIhumhtSAtLT5cbiAgICA8ZGl2IHYtaWY9XCJwYWdpbmF0aW9uICYmIHBhZ2luYXRpb24udG90YWxfcGFnZXMgPiAxXCIgY2xhc3M9XCJwYWdpbmF0aW9uXCI+XG4gICAgICA8YnV0dG9uIGNsYXNzPVwicGFnZS1idG5cIiA6ZGlzYWJsZWQ9XCJwYWdpbmF0aW9uLnBhZ2UgPT09IDFcIlxuICAgICAgICAgICAgICBAY2xpY2s9XCJjaGFuZ2VQYWdlKHBhZ2luYXRpb24ucGFnZSAtIDEpXCI+5LiK5LiA6aG1PC9idXR0b24+XG4gICAgICA8c3BhbiBjbGFzcz1cInBhZ2UtaW5mb1wiPlxuICAgICAgICDnrKwge3sgcGFnaW5hdGlvbi5wYWdlIH19IC8ge3sgcGFnaW5hdGlvbi50b3RhbF9wYWdlcyB9fSDpobVcbiAgICAgICAgKOWFsSB7eyBwYWdpbmF0aW9uLnRvdGFsIH19IOadoSlcbiAgICAgIDwvc3Bhbj5cbiAgICAgIDxidXR0b24gY2xhc3M9XCJwYWdlLWJ0blwiIDpkaXNhYmxlZD1cInBhZ2luYXRpb24ucGFnZSA+PSBwYWdpbmF0aW9uLnRvdGFsX3BhZ2VzXCJcbiAgICAgICAgICAgICAgQGNsaWNrPVwiY2hhbmdlUGFnZShwYWdpbmF0aW9uLnBhZ2UgKyAxKVwiPuS4i+S4gOmhtTwvYnV0dG9uPlxuICAgIDwvZGl2PlxuICA8L2Rpdj5cbjwvdGVtcGxhdGU+XG5cbjxzY3JpcHQgc2V0dXA+XG5pbXBvcnQgeyByZWYsIGNvbXB1dGVkLCB3YXRjaCwgb25Nb3VudGVkLCBvblVubW91bnRlZCB9IGZyb20gJ3Z1ZSdcbmltcG9ydCB7IHVzZVJvdXRlLCB1c2VSb3V0ZXIgfSBmcm9tICd2dWUtcm91dGVyJ1xuaW1wb3J0IHsgQVBJX0JBU0VfVVJMIH0gZnJvbSAnLi4vdXRpbHMvYXBpQ29uZmlnJ1xuaW1wb3J0IEFwcEhlYWRlciBmcm9tICcuLi9jb21wb25lbnRzL0FwcEhlYWRlci52dWUnXG5cbmNvbnN0IHJvdXRlID0gdXNlUm91dGUoKVxuY29uc3Qgcm91dGVyID0gdXNlUm91dGVyKClcblxuY29uc3QgUkFOR0VTID0gW1xuICB7IGtleTogJ3RvZGF5JywgbGFiZWw6ICfku4rlpKknIH0sXG4gIHsga2V5OiAnM2QnLCBsYWJlbDogJ+i/kSAzIOWkqScgfSxcbiAgeyBrZXk6ICc3ZCcsIGxhYmVsOiAn6L+RIDcg5aSpJyB9LFxuICB7IGtleTogJzMwZCcsIGxhYmVsOiAn6L+RIDMwIOWkqScgfSxcbiAgeyBrZXk6ICdhbGwnLCBsYWJlbDogJ+WFqOmDqCcgfSxcbl1cblxuY29uc3QgVEFSR0VUX1BMQVRGT1JNUyA9IFtcbiAgeyBrZXk6ICd3ZWl4aW4nLCBsYWJlbDogJ+W+ruS/oeinhumikeWPtycgfSxcbiAgeyBrZXk6ICdkb3V5aW4nLCBsYWJlbDogJ+aKlumfsycgfSxcbiAgeyBrZXk6ICd4aWFvaG9uZ3NodScsIGxhYmVsOiAn5bCP57qi5LmmJyB9LFxuICB7IGtleTogJ2luc3RhZ3JhbScsIGxhYmVsOiAnSW5zdGFncmFtJyB9LFxuXVxuXG5jb25zdCByYW5nZSA9IHJlZihyb3V0ZS5xdWVyeS5yYW5nZSB8fCAnN2QnKVxuLy8g6buY6K6k5oyJXCLmnIDov5Hlj5HluINcIuS7juaWsOWIsOaXp+aOki4g55So5oi35Li76K+J5rGC5pivXCLku4rlpKnlj5Hkuobku4DkuYggLyDmmKjlpKnlj5Hkuobku4DkuYhcIiwg5pe26Ze05bqP5pyA55u06KeCLlxuLy8g5oOz55yL54K56LWe546HL+aAu+eCuei1nuaOkiwg55So6aG26YOo5LiL5ouJ5YiH5bCx6KGMLlxuY29uc3Qgc29ydCA9IHJlZihyb3V0ZS5xdWVyeS5zb3J0IHx8ICdwdWJsaXNoZWRfYXQnKVxuLy8gb25seURlYWQgPSDlj6rmmL7npLpcIuS7u+S4gOW5s+WPsOiiq+WIpCBkZWFkXCLnmoTooYwgKOmZkOa1geWrjOeWkeinhumikSkuIOWJjeerr+acrOWcsOetm+mAiSwg5LiN6YeN5paw6K+35rGC5o6l5Y+jLlxuY29uc3Qgb25seURlYWQgPSByZWYocm91dGUucXVlcnkub25seV9kZWFkID09PSAnMScpXG5jb25zdCByYXdWaWRlb3MgPSByZWYoW10pICAvLyDmjqXlj6Pov5Tlm57nmoTljp/lp4sgdmlkZW9zLCDkuI3luKYgb25seURlYWQg562b6YCJXG5jb25zdCB2aWRlb3MgPSByZWYoW10pICAgICAvLyDlupTnlKggb25seURlYWQg562b6YCJ5LmL5ZCO5a6e6ZmF5bGV56S655qE5YiX6KGoXG5jb25zdCBwYWdpbmF0aW9uID0gcmVmKG51bGwpXG5jb25zdCBjdXJyZW50UGFnZSA9IHJlZigxKVxuY29uc3QgbG9hZGluZyA9IHJlZihmYWxzZSlcbmNvbnN0IGVycm9yTXNnID0gcmVmKCcnKVxuY29uc3QgYm9vc3RTdW1tYXJ5ID0gcmVmKG51bGwpXG4vLyDlvq7kv6HosYYgLT4g5Lq65rCR5biBIOaxh+eOhy4g5a6J5Y2TL1dlYiDlhYXlgLwgMeWFgz0xMOixhiAo5a6Y5pa55Lu3KSwgaU9TIOWFheWAvCAx5YWDPTfosYYgKEFwcGxlIOaKveaIkCkuXG4vLyDpu5jorqQgMTAsIOeUqOaIt+S4u+imgei1sCBXZWIg5YWF5YC8LlxuY29uc3QgY29pbnNQZXJZdWFuID0gcmVmKDEwKVxuXG5jb25zdCBQTEFURk9STV9MQUJFTFMgPSB7XG4gIHdlaXhpbjogJ+W+ruS/oeinhumikeWPtyAo5b6u5L+h6LGGKScsXG4gIGRvdXlpbjogJ+aKlumfsyAoRE9VKyknLFxuICB4aWFvaG9uZ3NodTogJ+Wwj+e6ouS5piAo5Yqg54OtKScsXG59XG5mdW5jdGlvbiBwbGF0Zm9ybUxhYmVsKHApIHsgcmV0dXJuIFBMQVRGT1JNX0xBQkVMU1twXSB8fCBwIH1cblxuY29uc3QgUExBVEZPUk1fU0hPUlQgPSB7XG4gIHdlaXhpbjogJ+inhumikeWPtycsXG4gIGRvdXlpbjogJ+aKlumfsycsXG4gIHhpYW9ob25nc2h1OiAn5bCP57qi5LmmJyxcbn1cbmZ1bmN0aW9uIHBsYXRmb3JtU2hvcnQocCkgeyByZXR1cm4gUExBVEZPUk1fU0hPUlRbcF0gfHwgcCB9XG5cbi8vIOW+ruS/oeixhiAvIOaKlumfsyBjb3N0X2Ftb3VudCDljZXkvY3pg73mmK8g5YWDLiDlvq7kv6HosYborqLljZXpobXlvojlpJogY29zdD0wXG4vLyAo5bCP6aKd5bCd6K+VIC8g5oiW6ICF6K6i5Y2V6aG15rKh5Zue5aGrKSwg6L+Z6YeM5L6d54S25oyJXCLlhYNcIuaYvuekuiwg5L6/5LqO5ZKM55yf5a6e6Iqx55qE6ZKx5a+56b2QLlxuZnVuY3Rpb24gZm9ybWF0Q29zdChjb3N0LCBwbGF0Zm9ybSkge1xuICBpZiAoY29zdCA9PSBudWxsKSByZXR1cm4gJy0nXG4gIGlmIChjb3N0ID09PSAwKSByZXR1cm4gJ8KlMCdcbiAgcmV0dXJuICfCpScgKyBOdW1iZXIoY29zdCkudG9Mb2NhbGVTdHJpbmcoJ3poLUNOJywgeyBtYXhpbXVtRnJhY3Rpb25EaWdpdHM6IDIgfSlcbn1cblxuZnVuY3Rpb24gc2V0UmFuZ2Uoa2V5KSB7XG4gIHJhbmdlLnZhbHVlID0ga2V5XG4gIHJvdXRlci5yZXBsYWNlKHsgcXVlcnk6IHsgLi4ucm91dGUucXVlcnksIHJhbmdlOiBrZXkgfSB9KVxuICBmZXRjaERhdGEoMSlcbn1cblxuYXN5bmMgZnVuY3Rpb24gZmV0Y2hEYXRhKHBhZ2UgPSAxKSB7XG4gIGxvYWRpbmcudmFsdWUgPSB0cnVlXG4gIGVycm9yTXNnLnZhbHVlID0gJydcbiAgdHJ5IHtcbiAgICBjb25zdCBwYXJhbXMgPSBuZXcgVVJMU2VhcmNoUGFyYW1zKHtcbiAgICAgIHJhbmdlOiByYW5nZS52YWx1ZSxcbiAgICAgIHNvcnQ6IHNvcnQudmFsdWUsXG4gICAgICBwYWdlOiBTdHJpbmcocGFnZSksXG4gICAgICBwYWdlX3NpemU6ICcyMCcsXG4gICAgfSlcbiAgICBjb25zdCByZXMgPSBhd2FpdCBmZXRjaChgJHtBUElfQkFTRV9VUkx9L2FwaS96aGlodS9jcm9zcy1wbGF0Zm9ybS1zdGF0cz8ke3BhcmFtc31gKVxuICAgIGNvbnN0IGpzb24gPSBhd2FpdCByZXMuanNvbigpXG4gICAgaWYgKGpzb24uY29kZSAhPT0gMjAwICYmIGpzb24uY29kZSAhPT0gMCkge1xuICAgICAgZXJyb3JNc2cudmFsdWUgPSBg5Yqg6L295aSx6LSlOiAke2pzb24ubXNnIHx8ICfmnKrnn6XplJnor68nfWBcbiAgICAgIHJhd1ZpZGVvcy52YWx1ZSA9IFtdXG4gICAgICB2aWRlb3MudmFsdWUgPSBbXVxuICAgICAgcGFnaW5hdGlvbi52YWx1ZSA9IG51bGxcbiAgICAgIHJldHVyblxuICAgIH1cbiAgICByYXdWaWRlb3MudmFsdWUgPSBqc29uLmRhdGE/LnZpZGVvcyB8fCBbXVxuICAgIGFwcGx5T25seURlYWRGaWx0ZXIoKVxuICAgIHBhZ2luYXRpb24udmFsdWUgPSBqc29uLmRhdGE/LnBhZ2luYXRpb24gfHwgbnVsbFxuICAgIGN1cnJlbnRQYWdlLnZhbHVlID0gcGFnZVxuICB9IGNhdGNoIChlKSB7XG4gICAgZXJyb3JNc2cudmFsdWUgPSBg572R57uc6ZSZ6K+vOiAke2U/Lm1lc3NhZ2UgfHwgZX1gXG4gIH0gZmluYWxseSB7XG4gICAgbG9hZGluZy52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cblxuLy8g5bqU55SoIG9ubHlEZWFkIOetm+mAiS4g5YmN56uv5pys5Zyw562bICjlkI7nq6/kuI3liIbpobXml7blt7Lnu4/ov5Tlm57lhajpg6gsIOmHjeaWsOWIhumhteaEj+S5ieS4jeWkpyxcbi8vIOi1sFwi5YWI5oyJ5pWw5o2u5o6S5bqP5ou/5Yiw5b2T6aG1IOKGkiDnlKjmiLfliIflj6rnnIvpmZDmtYHlq4znlpEg4oaSIOWuouaIt+err+i/h+a7pFwi55qE6ZO+6LevKS5cbmZ1bmN0aW9uIGFwcGx5T25seURlYWRGaWx0ZXIoKSB7XG4gIGlmIChvbmx5RGVhZC52YWx1ZSkge1xuICAgIHZpZGVvcy52YWx1ZSA9IHJhd1ZpZGVvcy52YWx1ZS5maWx0ZXIodiA9PlxuICAgICAgdi5oYXNfZGVhZF9wbGF0Zm9ybSB8fCB2LnRvcF9ib29zdF9sZXZlbCA9PT0gJ2RlYWQnXG4gICAgKVxuICB9IGVsc2Uge1xuICAgIHZpZGVvcy52YWx1ZSA9IHJhd1ZpZGVvcy52YWx1ZVxuICB9XG59XG5cbmZ1bmN0aW9uIHRvZ2dsZU9ubHlEZWFkKCkge1xuICBvbmx5RGVhZC52YWx1ZSA9ICFvbmx5RGVhZC52YWx1ZVxuICByb3V0ZXIucmVwbGFjZSh7XG4gICAgcXVlcnk6IHsgLi4ucm91dGUucXVlcnksIG9ubHlfZGVhZDogb25seURlYWQudmFsdWUgPyAnMScgOiB1bmRlZmluZWQgfSxcbiAgfSlcbiAgYXBwbHlPbmx5RGVhZEZpbHRlcigpXG59XG5cbmZ1bmN0aW9uIGNoYW5nZVBhZ2UocCkge1xuICBpZiAocGFnaW5hdGlvbi52YWx1ZSAmJiBwID49IDEgJiYgcCA8PSBwYWdpbmF0aW9uLnZhbHVlLnRvdGFsX3BhZ2VzKSB7XG4gICAgZmV0Y2hEYXRhKHApXG4gIH1cbn1cblxuYXN5bmMgZnVuY3Rpb24gZmV0Y2hCb29zdFN1bW1hcnkoKSB7XG4gIHRyeSB7XG4gICAgY29uc3QgcGFyYW1zID0gbmV3IFVSTFNlYXJjaFBhcmFtcyh7IGNvaW5zX3Blcl95dWFuOiBTdHJpbmcoY29pbnNQZXJZdWFuLnZhbHVlKSB9KVxuICAgIGNvbnN0IHJlcyA9IGF3YWl0IGZldGNoKGAke0FQSV9CQVNFX1VSTH0vYXBpL3poaWh1L2Jvb3N0LXN1bW1hcnk/JHtwYXJhbXN9YClcbiAgICBjb25zdCBqc29uID0gYXdhaXQgcmVzLmpzb24oKVxuICAgIGlmIChqc29uLmNvZGUgIT09IDIwMCAmJiBqc29uLmNvZGUgIT09IDApIHJldHVyblxuICAgIGJvb3N0U3VtbWFyeS52YWx1ZSA9IGpzb24uZGF0YVxuICB9IGNhdGNoIChlKSB7XG4gICAgLy8g6Z2Z6buY5aSx6LSlLCDkuI3lvbHlk43kuLvooajmoLxcbiAgfVxufVxuXG5mdW5jdGlvbiBnZXRQbGF0Zm9ybUxldmVsQ2xhc3ModmlkZW8sIHBsYXRmb3JtS2V5KSB7XG4gIGNvbnN0IGx2ID0gdmlkZW8ucGxhdGZvcm1zPy5bcGxhdGZvcm1LZXldPy5ib29zdF9zY29yZT8ubGV2ZWxcbiAgcmV0dXJuIGx2ID8gYGNlbGwtJHtsdn1gIDogJ2NlbGwtZW1wdHknXG59XG5cbmZ1bmN0aW9uIHRvcExldmVsVG9vbHRpcCh2KSB7XG4gIGNvbnN0IHJlYXNvbnMgPSBbXVxuICBmb3IgKGNvbnN0IHAgb2YgVEFSR0VUX1BMQVRGT1JNUykge1xuICAgIGNvbnN0IGRhdGEgPSB2LnBsYXRmb3Jtcz8uW3Aua2V5XVxuICAgIGlmIChkYXRhPy5ib29zdF9zY29yZT8ucmVhc29uKSB7XG4gICAgICByZWFzb25zLnB1c2goYCR7cC5sYWJlbH06ICR7ZGF0YS5ib29zdF9zY29yZS5yZWFzb259YClcbiAgICB9XG4gIH1cbiAgcmV0dXJuIHJlYXNvbnMuam9pbignXFxuJykgfHwgJ+WPluacgOmrmOetiee6pydcbn1cblxuZnVuY3Rpb24gbGV2ZWxUZXh0KGx2KSB7XG4gIGlmIChsdiA9PT0gJ211c3QnKSByZXR1cm4gJ+KtkOKtkCDlv4XmipUnXG4gIGlmIChsdiA9PT0gJ2dvb2QnKSByZXR1cm4gJ+KtkCDlgLzmipUnXG4gIGlmIChsdiA9PT0gJ3NraXAnKSByZXR1cm4gJ+KclyDliKvmipUnXG4gIGlmIChsdiA9PT0gJ2RlYWQnKSByZXR1cm4gJ/Cfmqsg6ZmQ5rWBJ1xuICByZXR1cm4gJ+KAlCDop4LmnJsnXG59XG5cbi8vIOeUqOaIt+inhumikeWcqOWTquS6m+W5s+WPsOiiq+WIpCBkZWFkIOKAlCDnlKjkuo4gXCLpg6jliIblubPlj7DpmZDmtYFcIiDlvr3nq6DnmoQgdG9vbHRpcC5cbmZ1bmN0aW9uIGRlYWRQbGF0Zm9ybVRvb2x0aXAodikge1xuICBjb25zdCBsaW5lcyA9IFtdXG4gIGZvciAoY29uc3QgcCBvZiBUQVJHRVRfUExBVEZPUk1TKSB7XG4gICAgY29uc3QgZGF0YSA9IHYucGxhdGZvcm1zPy5bcC5rZXldXG4gICAgaWYgKGRhdGE/LmJvb3N0X3Njb3JlPy5sZXZlbCA9PT0gJ2RlYWQnKSB7XG4gICAgICBsaW5lcy5wdXNoKGAke3AubGFiZWx9OiAke2RhdGEuYm9vc3Rfc2NvcmUucmVhc29uIHx8ICfpmZDmtYHlq4znlpEnfWApXG4gICAgfVxuICB9XG4gIHJldHVybiBsaW5lcy5qb2luKCdcXG4nKSB8fCAn6Iez5bCR5LiA5Liq5bmz5Y+w6ZmQ5rWB5auM55aRJ1xufVxuXG4vLyDlubPlj7Dnoazkv6Hlj7fnn63mlofmnKwuIGZvcmJpZGRlbi9kZWxldGVkIOW3sue7j+WcqCBsdmwtZGVhZCDph4znuqLoibLmmL7npLrkuoYsIOi/memHjOS4jemHjeWkjS5cbmNvbnN0IFBMQVRGT1JNX1NUQVRVU19URVhUID0ge1xuICByZXZpZXdpbmc6ICflrqHmoLjkuK0nLFxuICBwcml2YXRlOiAn56eB5a+GJyxcbiAgcmVjb21tZW5kZWRfYmxvY2tlZDogJ+aOqOiNkOWPl+mZkCcsXG59XG5mdW5jdGlvbiBwbGF0Zm9ybVN0YXR1c1RleHQocykge1xuICByZXR1cm4gUExBVEZPUk1fU1RBVFVTX1RFWFRbc10gfHwgJydcbn1cbi8vIGZvcmJpZGRlbi9kZWxldGVkIOW3sue7j+iiq+WQjuerr+imhuebluWIsCBib29zdF9zY29yZS5sZXZlbD1kZWFkLCDov5nph4zlj6rlsZXnpLpcbi8vIHJldmlld2luZy9wcml2YXRlL3JlY29tbWVuZGVkX2Jsb2NrZWQgKOS4jeW9seWTjSBsZXZlbCDkvYbnlKjmiLfpnIDopoHnn6XpgZMpLlxuZnVuY3Rpb24gc2hvdWxkU2hvd1BsYXRmb3JtU3RhdHVzKHBsYXREYXRhKSB7XG4gIGNvbnN0IHMgPSBwbGF0RGF0YT8ucGxhdGZvcm1fc3RhdHVzXG4gIHJldHVybiBzICYmIFBMQVRGT1JNX1NUQVRVU19URVhUW3NdXG59XG5cbmZ1bmN0aW9uIGJvb3N0U3RhdHVzVGV4dChzKSB7XG4gIGNvbnN0IG0gPSB7IHBlbmRpbmc6ICflvoXmj5DkuqQnLCBzdWJtaXR0ZWQ6ICflt7Lmj5DkuqQnLCBhY3RpdmU6ICfliqDng63kuK0nLCBjb21wbGV0ZWQ6ICflt7LlrozmiJAnLCBmYWlsZWQ6ICflpLHotKUnIH1cbiAgcmV0dXJuIG1bc10gfHwgc1xufVxuXG5mdW5jdGlvbiBmb3JtYXROdW0obikge1xuICBpZiAoIW4pIHJldHVybiAnMCdcbiAgaWYgKG4gPj0gMTAwMDApIHJldHVybiAobiAvIDEwMDAwKS50b0ZpeGVkKDEpICsgJ+S4hydcbiAgcmV0dXJuIFN0cmluZyhuKVxufVxuXG5mdW5jdGlvbiBmb3JtYXRQZXJjZW50KHIpIHtcbiAgaWYgKCFyKSByZXR1cm4gJzAlJ1xuICByZXR1cm4gKHIgKiAxMDApLnRvRml4ZWQoMSkgKyAnJSdcbn1cblxuZnVuY3Rpb24gZm9ybWF0RGF0ZVRpbWUocykge1xuICBpZiAoIXMpIHJldHVybiAnJ1xuICBjb25zdCBkID0gbmV3IERhdGUocylcbiAgY29uc3QgbW9udGggPSBTdHJpbmcoZC5nZXRNb250aCgpICsgMSkucGFkU3RhcnQoMiwgJzAnKVxuICBjb25zdCBkYXkgPSBTdHJpbmcoZC5nZXREYXRlKCkpLnBhZFN0YXJ0KDIsICcwJylcbiAgY29uc3QgaGggPSBTdHJpbmcoZC5nZXRIb3VycygpKS5wYWRTdGFydCgyLCAnMCcpXG4gIGNvbnN0IG1tID0gU3RyaW5nKGQuZ2V0TWludXRlcygpKS5wYWRTdGFydCgyLCAnMCcpXG4gIHJldHVybiBgJHtkLmdldEZ1bGxZZWFyKCl9LSR7bW9udGh9LSR7ZGF5fSAke2hofToke21tfWBcbn1cblxuLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG4vLyDmibnph4/liqDng606IOWkmumAiSArIOW8ueeqlyArIGJhdGNoIEFQSSArIOi9ruivolxuLy8gPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG5cbmNvbnN0IHNlbGVjdGVkQXJ0aWNsZUlkcyA9IHJlZihuZXcgU2V0KCkpICAvLyBTZXQ8YXJ0aWNsZV9pZD4sIOi3qOmhteS/neeVmVxuXG5mdW5jdGlvbiB0b2dnbGVSb3dTZWxlY3RlZChhcnRpY2xlSWQsIGNoZWNrZWQpIHtcbiAgY29uc3QgcyA9IG5ldyBTZXQoc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlKVxuICBpZiAoY2hlY2tlZCkgcy5hZGQoYXJ0aWNsZUlkKVxuICBlbHNlIHMuZGVsZXRlKGFydGljbGVJZClcbiAgc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlID0gc1xufVxuXG5mdW5jdGlvbiB0b2dnbGVTZWxlY3RBbGwoY2hlY2tlZCkge1xuICBjb25zdCBzID0gbmV3IFNldChzZWxlY3RlZEFydGljbGVJZHMudmFsdWUpXG4gIGZvciAoY29uc3QgdiBvZiB2aWRlb3MudmFsdWUpIHtcbiAgICBpZiAoY2hlY2tlZCkgcy5hZGQodi5hcnRpY2xlX2lkKVxuICAgIGVsc2Ugcy5kZWxldGUodi5hcnRpY2xlX2lkKVxuICB9XG4gIHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZSA9IHNcbn1cblxuY29uc3QgaXNBbGxTZWxlY3RlZCA9IGNvbXB1dGVkKCgpID0+IHtcbiAgaWYgKHZpZGVvcy52YWx1ZS5sZW5ndGggPT09IDApIHJldHVybiBmYWxzZVxuICByZXR1cm4gdmlkZW9zLnZhbHVlLmV2ZXJ5KHYgPT4gc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmhhcyh2LmFydGljbGVfaWQpKVxufSlcbmNvbnN0IGlzUGFydGlhbFNlbGVjdGVkID0gY29tcHV0ZWQoKCkgPT4ge1xuICBjb25zdCBzb21lID0gdmlkZW9zLnZhbHVlLnNvbWUodiA9PiBzZWxlY3RlZEFydGljbGVJZHMudmFsdWUuaGFzKHYuYXJ0aWNsZV9pZCkpXG4gIHJldHVybiBzb21lICYmICFpc0FsbFNlbGVjdGVkLnZhbHVlXG59KVxuXG4vLyDlvLnnqpfnirbmgIFcbmNvbnN0IGJhdGNoTW9kYWxPcGVuID0gcmVmKGZhbHNlKVxuY29uc3QgYmF0Y2hTdWJtaXR0aW5nID0gcmVmKGZhbHNlKVxuY29uc3QgYmF0Y2hGb3JtID0gcmVmKHtcbiAgcGxhdGZvcm06ICd3ZWl4aW4nLFxuICBhbW91bnQ6IDUwMCxcbiAgZHVyYXRpb246IDI0LFxuICBnb2FsOiAnZm9sbG93ZXInLFxuICBhdWRpZW5jZUdyb3VwSWQ6IG51bGwsXG4gIHRhcmdldENyZWF0b3JzOiAnJyxcbiAgYXVkaWVuY2VQa2dOYW1lOiAnQUnmioDmnK/ovr7kurrnu4TlkIgnLFxuICBzdWJtaXQ6IGZhbHNlLFxuICBmb3JjZTogZmFsc2UsXG59KVxuXG4vLyDot5/lkI7nq68gZW51bSDlr7npvZBcbmNvbnN0IFdFSVhJTl9EVVJBVElPTlMgPSBbNiwgOCwgMTIsIDI0XVxuY29uc3QgRE9VWUlOX0RVUkFUSU9OUyA9IFsyLCA2LCAxMiwgMTgsIDI0XVxuY29uc3QgV0VJWElOX0dPQUxTID0gW1xuICB7IGtleTogJ3NtYXJ0JywgICAgbGFiZWw6ICfmmbrog73liqDng60nIH0sXG4gIHsga2V5OiAnbGlrZXMnLCAgICBsYWJlbDogJ+eCuei1nuaVsCcgfSxcbiAgeyBrZXk6ICdmb2xsb3dlcicsIGxhYmVsOiAn5YWz5rOo5pWwJyB9LFxuICB7IGtleTogJ3BsYXknLCAgICAgbGFiZWw6ICfmkq3mlL7mlbAnIH0sXG5dXG5jb25zdCBET1VZSU5fR09BTFMgPSBbXG4gIHsga2V5OiAnZm9sbG93ZXInLCAgICBsYWJlbDogJ+eyieS4nemHjycgfSxcbiAgeyBrZXk6ICdpbnRlcmFjdGlvbicsIGxhYmVsOiAn5LqS5Yqo6YePJyB9LFxuICB7IGtleTogJ3BsYXknLCAgICAgICAgbGFiZWw6ICfmkq3mlL7ph48nIH0sXG4gIHsga2V5OiAnaG9tZScsICAgICAgICBsYWJlbDogJ+S4u+mhteiuv+mXricgfSxcbiAgeyBrZXk6ICdmYW5zX3Nob3cnLCAgIGxhYmVsOiAn57KJ5Lid5bGV56S6JyB9LFxuXVxuXG5jb25zdCBjdXJyZW50RHVyYXRpb25zID0gY29tcHV0ZWQoKCkgPT5cbiAgYmF0Y2hGb3JtLnZhbHVlLnBsYXRmb3JtID09PSAnd2VpeGluJyA/IFdFSVhJTl9EVVJBVElPTlMgOiBET1VZSU5fRFVSQVRJT05TXG4pXG5jb25zdCBjdXJyZW50R29hbHMgPSBjb21wdXRlZCgoKSA9PlxuICBiYXRjaEZvcm0udmFsdWUucGxhdGZvcm0gPT09ICd3ZWl4aW4nID8gV0VJWElOX0dPQUxTIDogRE9VWUlOX0dPQUxTXG4pXG5cbi8vIOW9k+WJjeW8ueeql+mAieS4reinhumikSAo5LuOIHJhd1ZpZGVvcyDlj5YsIOi3qOmhteS/neeVmSlcbmNvbnN0IHNlbGVjdGVkVmlkZW9zRm9yTW9kYWwgPSBjb21wdXRlZCgoKSA9PlxuICByYXdWaWRlb3MudmFsdWUuZmlsdGVyKHYgPT4gc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmhhcyh2LmFydGljbGVfaWQpKVxuKVxuXG5mdW5jdGlvbiBnZXRWcElkKHZpZGVvLCBwbGF0Zm9ybSkge1xuICAvLyDlkI7nq68gZ2V0X2Nyb3NzX3BsYXRmb3JtX3N0YXRzIOi/lOWbnuWtl+auteWPqyBwdWJsaXNoX2lkICg9IHZpZGVvX3B1Ymxpc2guaWQpLCDkuI3mmK8gdmlkZW9fcHVibGlzaF9pZFxuICByZXR1cm4gdmlkZW8ucGxhdGZvcm1zPy5bcGxhdGZvcm1dPy5wdWJsaXNoX2lkIHx8IG51bGxcbn1cbmZ1bmN0aW9uIGNhbkJvb3N0T25QbGF0Zm9ybSh2aWRlbywgcGxhdGZvcm0pIHtcbiAgY29uc3QgdnBpZCA9IGdldFZwSWQodmlkZW8sIHBsYXRmb3JtKVxuICBpZiAoIXZwaWQpIHJldHVybiBmYWxzZVxuICAvLyB3ZWl4aW4g6L+Y6KaB5rGCIG9iamVjdF9pZCDkuI3kuLrnqbogLyDmsqHkuIvmnrY7IGRvdXlpbiDopoHmsYIgcHVibGlzaGVkX2xpbmsg5ZCrIGF3ZW1lX2lkLlxuICAvLyDov5nph4zliY3nq6/nspfliKQsIOecn+agoemqjOWQjuerr+WBmiAocmVqZWN0ZWQg5YiX6KGo5Lya5Zue5p2lKS5cbiAgY29uc3QgZGF0YSA9IHZpZGVvLnBsYXRmb3Jtc1twbGF0Zm9ybV1cbiAgaWYgKGRhdGEucGxhdGZvcm1fc3RhdHVzID09PSAnZm9yYmlkZGVuJyB8fCBkYXRhLnBsYXRmb3JtX3N0YXR1cyA9PT0gJ2RlbGV0ZWQnXG4gICAgICB8fCBkYXRhLnBsYXRmb3JtX3N0YXR1cyA9PT0gJ3JlY29tbWVuZGVkX2Jsb2NrZWQnKSByZXR1cm4gZmFsc2VcbiAgcmV0dXJuIHRydWVcbn1cblxuZnVuY3Rpb24gb3BlbkJhdGNoQm9vc3RNb2RhbCgpIHtcbiAgaWYgKHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZS5zaXplID09PSAwKSByZXR1cm5cbiAgLy8g6YeN572uIHdlaXhpbi9kb3V5aW4g6buY6K6k5YC8XG4gIGlmIChiYXRjaEZvcm0udmFsdWUucGxhdGZvcm0gPT09ICd3ZWl4aW4nKSB7XG4gICAgYmF0Y2hGb3JtLnZhbHVlLmR1cmF0aW9uID0gMjRcbiAgICBiYXRjaEZvcm0udmFsdWUuZ29hbCA9ICdmb2xsb3dlcidcbiAgfSBlbHNlIHtcbiAgICBiYXRjaEZvcm0udmFsdWUuZHVyYXRpb24gPSAyNFxuICAgIGJhdGNoRm9ybS52YWx1ZS5nb2FsID0gJ2ZvbGxvd2VyJ1xuICB9XG4gIGJhdGNoTW9kYWxPcGVuLnZhbHVlID0gdHJ1ZVxufVxuZnVuY3Rpb24gY2xvc2VCYXRjaE1vZGFsKCkge1xuICBiYXRjaE1vZGFsT3Blbi52YWx1ZSA9IGZhbHNlXG59XG5cbi8vIOW5s+WPsOWIh+aNouaXtuWQjOatpem7mOiupOWAvFxuZnVuY3Rpb24gX29uUGxhdGZvcm1DaGFuZ2UoKSB7XG4gIGlmIChiYXRjaEZvcm0udmFsdWUucGxhdGZvcm0gPT09ICd3ZWl4aW4nKSB7XG4gICAgaWYgKCFXRUlYSU5fRFVSQVRJT05TLmluY2x1ZGVzKGJhdGNoRm9ybS52YWx1ZS5kdXJhdGlvbikpIGJhdGNoRm9ybS52YWx1ZS5kdXJhdGlvbiA9IDI0XG4gICAgaWYgKCFXRUlYSU5fR09BTFMuc29tZShnID0+IGcua2V5ID09PSBiYXRjaEZvcm0udmFsdWUuZ29hbCkpIGJhdGNoRm9ybS52YWx1ZS5nb2FsID0gJ2ZvbGxvd2VyJ1xuICB9IGVsc2Uge1xuICAgIGlmICghRE9VWUlOX0RVUkFUSU9OUy5pbmNsdWRlcyhiYXRjaEZvcm0udmFsdWUuZHVyYXRpb24pKSBiYXRjaEZvcm0udmFsdWUuZHVyYXRpb24gPSAyNFxuICAgIGlmICghRE9VWUlOX0dPQUxTLnNvbWUoZyA9PiBnLmtleSA9PT0gYmF0Y2hGb3JtLnZhbHVlLmdvYWwpKSBiYXRjaEZvcm0udmFsdWUuZ29hbCA9ICdmb2xsb3dlcidcbiAgfVxufVxuLy8g5bmz5Y+w5YiH5o2i5pe2LCDoh6rliqjmoKHmraPkuI3lkIjms5XnmoQgZHVyYXRpb24vZ29hbCDpu5jorqTlgLxcbndhdGNoKCgpID0+IGJhdGNoRm9ybS52YWx1ZS5wbGF0Zm9ybSwgX29uUGxhdGZvcm1DaGFuZ2UpXG5cbi8vIGJhdGNoIOS7u+WKoei/m+W6plxuY29uc3QgYmF0Y2hKb2IgPSByZWYobnVsbCkgIC8vIHsgcGxhdGZvcm0sIGluc2VydGVkOiBbYm9vc3RfaWRdLCByZWplY3RlZDogWy4uLl0sIGl0ZW1zOiBbLi4uXSB9XG5sZXQgYmF0Y2hQb2xsVGltZXIgPSBudWxsXG5cbmFzeW5jIGZ1bmN0aW9uIHN1Ym1pdEJhdGNoQm9vc3QoKSB7XG4gIGlmIChiYXRjaFN1Ym1pdHRpbmcudmFsdWUpIHJldHVyblxuICBpZiAoc2VsZWN0ZWRWaWRlb3NGb3JNb2RhbC52YWx1ZS5sZW5ndGggPT09IDApIHJldHVyblxuICBiYXRjaFN1Ym1pdHRpbmcudmFsdWUgPSB0cnVlXG4gIHRyeSB7XG4gICAgY29uc3QgcGxhdGZvcm0gPSBiYXRjaEZvcm0udmFsdWUucGxhdGZvcm1cbiAgICBjb25zdCB0YXJnZXRDcmVhdG9ycyA9IGJhdGNoRm9ybS52YWx1ZS50YXJnZXRDcmVhdG9yc1xuICAgICAgPyBiYXRjaEZvcm0udmFsdWUudGFyZ2V0Q3JlYXRvcnMuc3BsaXQoJywnKS5tYXAocyA9PiBzLnRyaW0oKSkuZmlsdGVyKEJvb2xlYW4pXG4gICAgICA6IFtdXG4gICAgY29uc3Qgb3JkZXJzID0gW11cbiAgICBmb3IgKGNvbnN0IHYgb2Ygc2VsZWN0ZWRWaWRlb3NGb3JNb2RhbC52YWx1ZSkge1xuICAgICAgY29uc3QgdnBpZCA9IGdldFZwSWQodiwgcGxhdGZvcm0pXG4gICAgICBpZiAoIXZwaWQpIGNvbnRpbnVlICAvLyDliY3nq6/ot7Pov4fmsqHlnKjor6XlubPlj7Dlj5HluIPnmoQsIOWQjuerr+S5n+S8miByZWplY3Qg5L2G5LiN5rWq6LS55LiA5qyhIHJvdW5kLXRyaXBcbiAgICAgIGNvbnN0IG8gPSB7XG4gICAgICAgIHBsYXRmb3JtLFxuICAgICAgICB2aWRlb19wdWJsaXNoX2lkOiB2cGlkLFxuICAgICAgICBib29zdF9hbW91bnQ6IGJhdGNoRm9ybS52YWx1ZS5hbW91bnQsXG4gICAgICAgIGJvb3N0X2R1cmF0aW9uOiBiYXRjaEZvcm0udmFsdWUuZHVyYXRpb24sXG4gICAgICAgIGdvYWw6IGJhdGNoRm9ybS52YWx1ZS5nb2FsLFxuICAgICAgICBmb3JjZTogYmF0Y2hGb3JtLnZhbHVlLmZvcmNlLFxuICAgICAgfVxuICAgICAgaWYgKHBsYXRmb3JtID09PSAnd2VpeGluJykgby50YXJnZXRfY3JlYXRvcnMgPSB0YXJnZXRDcmVhdG9yc1xuICAgICAgZWxzZSBvLmF1ZGllbmNlX3BrZ19uYW1lID0gYmF0Y2hGb3JtLnZhbHVlLmF1ZGllbmNlUGtnTmFtZVxuICAgICAgb3JkZXJzLnB1c2gobylcbiAgICB9XG4gICAgaWYgKG9yZGVycy5sZW5ndGggPT09IDApIHtcbiAgICAgIGFsZXJ0KCfpgInkuK3nmoTop4bpopHlnKjmiYDpgInlubPlj7Dpg73msqHmnInlj5HluIPorrDlvZUsIOaXoOazleaKleaUvicpXG4gICAgICBiYXRjaFN1Ym1pdHRpbmcudmFsdWUgPSBmYWxzZVxuICAgICAgcmV0dXJuXG4gICAgfVxuICAgIGNvbnN0IHJlcyA9IGF3YWl0IGZldGNoKGAke0FQSV9CQVNFX1VSTH0vYXBpL3poaWh1L3ZpZGVvLWJvb3N0L2JhdGNoYCwge1xuICAgICAgbWV0aG9kOiAnUE9TVCcsXG4gICAgICBoZWFkZXJzOiB7ICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbjsgY2hhcnNldD11dGYtOCcgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHsgb3JkZXJzLCBzdWJtaXQ6IGJhdGNoRm9ybS52YWx1ZS5zdWJtaXQgfSksXG4gICAgfSlcbiAgICBjb25zdCBqc29uID0gYXdhaXQgcmVzLmpzb24oKVxuICAgIGlmIChqc29uLmNvZGUgIT09IDIwMCAmJiBqc29uLmNvZGUgIT09IDApIHtcbiAgICAgIGFsZXJ0KGDmj5DkuqTlpLHotKU6ICR7anNvbi5tc2cgfHwgJ+acquefpemUmeivryd9YClcbiAgICAgIHJldHVyblxuICAgIH1cbiAgICBiYXRjaEpvYi52YWx1ZSA9IHtcbiAgICAgIHBsYXRmb3JtLFxuICAgICAgc3VibWl0OiBiYXRjaEZvcm0udmFsdWUuc3VibWl0LFxuICAgICAgaW5zZXJ0ZWQ6IGpzb24uZGF0YS5pbnNlcnRlZF9ib29zdF9pZHMgfHwgW10sXG4gICAgICByZWplY3RlZDoganNvbi5kYXRhLnJlamVjdGVkIHx8IFtdLFxuICAgICAgaXRlbXM6IChqc29uLmRhdGEuaW5zZXJ0ZWRfYm9vc3RfaWRzIHx8IFtdKS5tYXAoYmlkID0+ICh7XG4gICAgICAgIGJvb3N0X2lkOiBiaWQsIGJvb3N0X3N0YXR1czogJ3BlbmRpbmcnLCBvcmRlcl9pZDogbnVsbCxcbiAgICAgICAgZXJyb3JfbWVzc2FnZTogbnVsbCwgdmlkZW9fdGl0bGU6ICfliqDovb3kuK0uLi4nLFxuICAgICAgfSkpLFxuICAgIH1cbiAgICBjbG9zZUJhdGNoTW9kYWwoKVxuICAgIHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZSA9IG5ldyBTZXQoKSAgLy8g5riF56m65bey6YCJXG4gICAgc3RhcnRCYXRjaFBvbGxpbmcoKVxuICB9IGNhdGNoIChlKSB7XG4gICAgYWxlcnQoYOaPkOS6pOW8guW4uDogJHtlPy5tZXNzYWdlIHx8IGV9YClcbiAgfSBmaW5hbGx5IHtcbiAgICBiYXRjaFN1Ym1pdHRpbmcudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbmFzeW5jIGZ1bmN0aW9uIHBvbGxCYXRjaE9uY2UoKSB7XG4gIGlmICghYmF0Y2hKb2IudmFsdWUgfHwgYmF0Y2hKb2IudmFsdWUuaW5zZXJ0ZWQubGVuZ3RoID09PSAwKSByZXR1cm5cbiAgdHJ5IHtcbiAgICBjb25zdCBpZHMgPSBiYXRjaEpvYi52YWx1ZS5pbnNlcnRlZC5qb2luKCcsJylcbiAgICBjb25zdCByZXMgPSBhd2FpdCBmZXRjaChgJHtBUElfQkFTRV9VUkx9L2FwaS96aGlodS92aWRlby1ib29zdC9saXN0P2Jvb3N0X2lkcz0ke2lkc31gKVxuICAgIGNvbnN0IGpzb24gPSBhd2FpdCByZXMuanNvbigpXG4gICAgaWYgKGpzb24uY29kZSAhPT0gMjAwICYmIGpzb24uY29kZSAhPT0gMCkgcmV0dXJuXG4gICAgY29uc3QgaXRlbXMgPSBqc29uLmRhdGEuaXRlbXMgfHwgW11cbiAgICAvLyDmjIkgaW5zZXJ0ZWQg6aG65bqP5o6S5bqP5bGV56S6XG4gICAgY29uc3QgYnlJZCA9IG5ldyBNYXAoaXRlbXMubWFwKGl0ID0+IFtpdC5ib29zdF9pZCwgaXRdKSlcbiAgICBiYXRjaEpvYi52YWx1ZS5pdGVtcyA9IGJhdGNoSm9iLnZhbHVlLmluc2VydGVkLm1hcChiaWQgPT4gYnlJZC5nZXQoYmlkKSB8fCB7XG4gICAgICBib29zdF9pZDogYmlkLCBib29zdF9zdGF0dXM6ICdwZW5kaW5nJywgb3JkZXJfaWQ6IG51bGwsXG4gICAgICBlcnJvcl9tZXNzYWdlOiBudWxsLCB2aWRlb190aXRsZTogJz8nLFxuICAgIH0pXG4gICAgLy8g5YWo6YOo6LeR5a6M5bCx5YGc5q2i6L2u6K+iICjlpLHotKUv5oiQ5YqfL+i2heaXtiDpg73nrpcgdGVybWluYWwpXG4gICAgY29uc3QgYWxsRG9uZSA9IGJhdGNoSm9iLnZhbHVlLml0ZW1zLmV2ZXJ5KFxuICAgICAgaXQgPT4gaXQuYm9vc3Rfc3RhdHVzID09PSAnc3VibWl0dGVkJyB8fCBpdC5ib29zdF9zdGF0dXMgPT09ICdmYWlsZWQnXG4gICAgICAgICAgICB8fCBpdC5ib29zdF9zdGF0dXMgPT09ICdjb21wbGV0ZWQnIHx8IGl0LmJvb3N0X3N0YXR1cyA9PT0gJ2NhbmNlbGxlZCdcbiAgICAgICAgICAgIC8vIGRyeS1ydW4g5a6M5LqG54q25oCB5Lya5YGc5ZyoIHBlbmRpbmcrZXJyb3JfbWVzc2FnZT0nW2RyeS1ydW4gT0tdLi4uJywg5Lmf566XIHRlcm1pbmFsXG4gICAgICAgICAgICB8fCAoaXQuYm9vc3Rfc3RhdHVzID09PSAncGVuZGluZycgJiYgaXQuZXJyb3JfbWVzc2FnZSAmJiBpdC5lcnJvcl9tZXNzYWdlLnN0YXJ0c1dpdGgoJ1tkcnktcnVuJykpXG4gICAgKVxuICAgIGlmIChhbGxEb25lKSBzdG9wQmF0Y2hQb2xsaW5nKClcbiAgfSBjYXRjaCAoZSkge1xuICAgIC8vIOmdmem7mCwg5LiL5LiA5qyh5YaNIHRyeVxuICB9XG59XG5cbmZ1bmN0aW9uIHN0YXJ0QmF0Y2hQb2xsaW5nKCkge1xuICBzdG9wQmF0Y2hQb2xsaW5nKClcbiAgcG9sbEJhdGNoT25jZSgpXG4gIGJhdGNoUG9sbFRpbWVyID0gc2V0SW50ZXJ2YWwocG9sbEJhdGNoT25jZSwgNDAwMClcbn1cbmZ1bmN0aW9uIHN0b3BCYXRjaFBvbGxpbmcoKSB7XG4gIGlmIChiYXRjaFBvbGxUaW1lcikgeyBjbGVhckludGVydmFsKGJhdGNoUG9sbFRpbWVyKTsgYmF0Y2hQb2xsVGltZXIgPSBudWxsIH1cbn1cbmZ1bmN0aW9uIGNsb3NlQmF0Y2hKb2IoKSB7XG4gIHN0b3BCYXRjaFBvbGxpbmcoKVxuICBiYXRjaEpvYi52YWx1ZSA9IG51bGxcbn1cblxuLy8g5oqV5pS+576kICjlj6/lpI3nlKjlrprlkJHkurrnvqQpOiDnnIvmnb/lsZXnpLogKyDlu7rljZXlvLnnqpfpgInnvqQuIOaVsOaNrua6kCBib29zdF9hdWRpZW5jZV9ncm91cHMg6KGoLlxuY29uc3QgYXVkaWVuY2VHcm91cHMgPSByZWYoW10pXG5hc3luYyBmdW5jdGlvbiBmZXRjaEF1ZGllbmNlR3JvdXBzKCkge1xuICB0cnkge1xuICAgIGNvbnN0IHJlcyA9IGF3YWl0IGZldGNoKGAke0FQSV9CQVNFX1VSTH0vYXBpL3poaWh1L2Jvb3N0LWF1ZGllbmNlLWdyb3Vwc2ApXG4gICAgY29uc3QganNvbiA9IGF3YWl0IHJlcy5qc29uKClcbiAgICBpZiAoanNvbi5jb2RlICE9PSAyMDAgJiYganNvbi5jb2RlICE9PSAwKSByZXR1cm5cbiAgICBhdWRpZW5jZUdyb3Vwcy52YWx1ZSA9IGpzb24uZGF0YT8uZ3JvdXBzIHx8IFtdXG4gIH0gY2F0Y2ggKGUpIHtcbiAgICAvLyDpnZnpu5jlpLHotKUsIOS4jeW9seWTjeS4u+a1geeoi1xuICB9XG59XG5cbi8vIOmAieaKleaUvue+pDog5oqK576k5oiQ5ZGY5pi156ew5aGr6L+bIHRhcmdldENyZWF0b3JzICjpgJflj7fliIbpmpQpLiDpgIlcIuiHquWumuS5iVwiKG51bGwpIOS4jeWKqC5cbmZ1bmN0aW9uIGFwcGx5QXVkaWVuY2VHcm91cCgpIHtcbiAgY29uc3QgZ2lkID0gYmF0Y2hGb3JtLnZhbHVlLmF1ZGllbmNlR3JvdXBJZFxuICBpZiAoIWdpZCkgcmV0dXJuXG4gIGNvbnN0IGcgPSBhdWRpZW5jZUdyb3Vwcy52YWx1ZS5maW5kKHggPT4geC5pZCA9PT0gZ2lkKVxuICBpZiAoZykgYmF0Y2hGb3JtLnZhbHVlLnRhcmdldENyZWF0b3JzID0gKGcuY3JlYXRvcnMgfHwgW10pLmpvaW4oJywnKVxufVxuXG4vLyDmjpLpmaTmoIfpopjlhbPplK7or406IOagh+mimOWQq+i/meS6m+ivjeeahOinhumikeemgeatouWKoOeDreaKleaUvi4g5pWw5o2u5rqQIGJvb3N0X2V4Y2x1ZGVkX2tleXdvcmRzIOihqCxcbi8vIOW7uuWNlSBBUEkgKF92YWxpZGF0ZV9hbmRfaW5zZXJ0X3BlbmRpbmcpIOWSjCBhdXRvX2Jvb3N0IOWAmemAiei/h+a7pOmDveivu+Wugywg5L+d5a2Y5Y2z55Sf5pWILlxuY29uc3QgZXhjbHVkZWRLZXl3b3JkcyA9IHJlZihbXSlcbmNvbnN0IG5ld0tleXdvcmQgPSByZWYoJycpXG5jb25zdCBrd1NhdmluZyA9IHJlZihmYWxzZSlcbmFzeW5jIGZ1bmN0aW9uIGZldGNoRXhjbHVkZWRLZXl3b3JkcygpIHtcbiAgdHJ5IHtcbiAgICBjb25zdCByZXMgPSBhd2FpdCBmZXRjaChgJHtBUElfQkFTRV9VUkx9L2FwaS96aGlodS9ib29zdC1leGNsdWRlZC1rZXl3b3Jkc2ApXG4gICAgY29uc3QganNvbiA9IGF3YWl0IHJlcy5qc29uKClcbiAgICBpZiAoanNvbi5jb2RlICE9PSAyMDAgJiYganNvbi5jb2RlICE9PSAwKSByZXR1cm5cbiAgICBleGNsdWRlZEtleXdvcmRzLnZhbHVlID0ganNvbi5kYXRhPy5rZXl3b3JkcyB8fCBbXVxuICB9IGNhdGNoIChlKSB7XG4gICAgLy8g6Z2Z6buY5aSx6LSlLCDkuI3lvbHlk43kuLvmtYHnqItcbiAgfVxufVxuYXN5bmMgZnVuY3Rpb24gYWRkRXhjbHVkZWRLZXl3b3JkKCkge1xuICBjb25zdCBrdyA9IG5ld0tleXdvcmQudmFsdWUudHJpbSgpXG4gIGlmICgha3cgfHwga3dTYXZpbmcudmFsdWUpIHJldHVyblxuICBrd1NhdmluZy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCByZXMgPSBhd2FpdCBmZXRjaChgJHtBUElfQkFTRV9VUkx9L2FwaS96aGlodS9ib29zdC1leGNsdWRlZC1rZXl3b3Jkc2AsIHtcbiAgICAgIG1ldGhvZDogJ1BPU1QnLFxuICAgICAgaGVhZGVyczogeyAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nIH0sXG4gICAgICBib2R5OiBKU09OLnN0cmluZ2lmeSh7IGtleXdvcmQ6IGt3IH0pLFxuICAgIH0pXG4gICAgY29uc3QganNvbiA9IGF3YWl0IHJlcy5qc29uKClcbiAgICBpZiAoanNvbi5jb2RlID09PSAyMDAgfHwganNvbi5jb2RlID09PSAwKSB7XG4gICAgICBuZXdLZXl3b3JkLnZhbHVlID0gJydcbiAgICAgIGF3YWl0IGZldGNoRXhjbHVkZWRLZXl3b3JkcygpXG4gICAgfSBlbHNlIHtcbiAgICAgIGFsZXJ0KGpzb24ubXNnIHx8ICfmt7vliqDlpLHotKUnKVxuICAgIH1cbiAgfSBjYXRjaCAoZSkge1xuICAgIGFsZXJ0KGDmt7vliqDlpLHotKU6ICR7ZS5tZXNzYWdlIHx8IGV9YClcbiAgfSBmaW5hbGx5IHtcbiAgICBrd1NhdmluZy52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cbmFzeW5jIGZ1bmN0aW9uIHJlbW92ZUV4Y2x1ZGVkS2V5d29yZChrKSB7XG4gIGlmICghY29uZmlybShg5Yig6Zmk5o6S6Zmk6K+NIFwiJHtrLmtleXdvcmR9XCI/IOWIoOmZpOWQjuagh+mimOWQq+Wug+eahOinhumikeWPiOWPr+S7peiiq+WKoOeDreaKleaUvuS6hmApKSByZXR1cm5cbiAgdHJ5IHtcbiAgICBjb25zdCByZXMgPSBhd2FpdCBmZXRjaChgJHtBUElfQkFTRV9VUkx9L2FwaS96aGlodS9ib29zdC1leGNsdWRlZC1rZXl3b3Jkcz9pZD0ke2suaWR9YCxcbiAgICAgICAgICAgICAgICAgICAgICAgICAgICB7IG1ldGhvZDogJ0RFTEVURScgfSlcbiAgICBjb25zdCBqc29uID0gYXdhaXQgcmVzLmpzb24oKVxuICAgIGlmIChqc29uLmNvZGUgPT09IDIwMCB8fCBqc29uLmNvZGUgPT09IDApIHtcbiAgICAgIGF3YWl0IGZldGNoRXhjbHVkZWRLZXl3b3JkcygpXG4gICAgfSBlbHNlIHtcbiAgICAgIGFsZXJ0KGpzb24ubXNnIHx8ICfliKDpmaTlpLHotKUnKVxuICAgIH1cbiAgfSBjYXRjaCAoZSkge1xuICAgIGFsZXJ0KGDliKDpmaTlpLHotKU6ICR7ZS5tZXNzYWdlIHx8IGV9YClcbiAgfVxufVxuXG5vbk1vdW50ZWQoKCkgPT4ge1xuICBmZXRjaERhdGEoMSlcbiAgZmV0Y2hCb29zdFN1bW1hcnkoKVxuICBmZXRjaEF1ZGllbmNlR3JvdXBzKClcbiAgZmV0Y2hFeGNsdWRlZEtleXdvcmRzKClcbn0pXG5vblVubW91bnRlZCgoKSA9PiB7XG4gIHN0b3BCYXRjaFBvbGxpbmcoKVxufSlcbjwvc2NyaXB0PlxuXG48c3R5bGUgc2NvcGVkPlxuLmRhc2hib2FyZC1wYWdlIHtcbiAgbWF4LXdpZHRoOiAxNDgwcHg7XG4gIG1hcmdpbjogMCBhdXRvO1xuICBwYWRkaW5nOiAyNHB4IDMycHggNjBweDtcbn1cblxuLnBhZ2UtaGVhZGVyIHtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xuICBhbGlnbi1pdGVtczogZmxleC1zdGFydDtcbiAgZmxleC13cmFwOiB3cmFwO1xuICBnYXA6IDE2cHg7XG4gIG1hcmdpbi1ib3R0b206IDE2cHg7XG59XG5cbi5oZWFkZXItbGVmdCB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG4gIGdhcDogNHB4O1xufVxuXG4ucGFnZS10aXRsZSB7IG1hcmdpbjogMDsgZm9udC1zaXplOiAxLjZyZW07IGZvbnQtd2VpZ2h0OiA3MDA7IGNvbG9yOiAjMmMzZTUwOyB9XG4ucGFnZS1zdWJ0aXRsZSB7IGNvbG9yOiAjODg4OyBmb250LXNpemU6IDAuODVyZW07IH1cblxuLmhlYWRlci1hY3Rpb25zIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiAxNnB4O1xuICBmbGV4LXdyYXA6IHdyYXA7XG59XG5cbi5maWx0ZXItZ3JvdXAgeyBkaXNwbGF5OiBmbGV4OyBhbGlnbi1pdGVtczogY2VudGVyOyBnYXA6IDZweDsgfVxuLmZpbHRlci1sYWJlbCB7IGZvbnQtc2l6ZTogMC44NXJlbTsgY29sb3I6ICM2NjY7IH1cblxuLmNoaXAge1xuICBwYWRkaW5nOiA0cHggMTJweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2QwZDdkZTtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogMTRweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDAuODVyZW07XG4gIGNvbG9yOiAjNTU1O1xuICB0cmFuc2l0aW9uOiBhbGwgMC4xNXM7XG59XG4uY2hpcDpob3ZlciB7IGJvcmRlci1jb2xvcjogIzE4OTBmZjsgY29sb3I6ICMxODkwZmY7IH1cbi5jaGlwLmFjdGl2ZSB7IGJhY2tncm91bmQ6ICMxODkwZmY7IGNvbG9yOiAjZmZmOyBib3JkZXItY29sb3I6ICMxODkwZmY7IH1cbi8qIOmZkOa1geWrjOeWkeetm+mAiSBjaGlwIOeUqOe6ouiJsuiwgywg5o+Q56S655So5oi36L+Z5piv6LSf6Z2i562b6YCJICovXG4uY2hpcC5jaGlwLWRhbmdlciB7IGJvcmRlci1jb2xvcjogI2ZmYTM5ZTsgY29sb3I6ICNjZjEzMjI7IH1cbi5jaGlwLmNoaXAtZGFuZ2VyOmhvdmVyIHsgYm9yZGVyLWNvbG9yOiAjY2YxMzIyOyB9XG4uY2hpcC5jaGlwLWRhbmdlci5hY3RpdmUgeyBiYWNrZ3JvdW5kOiAjY2YxMzIyOyBjb2xvcjogI2ZmZjsgYm9yZGVyLWNvbG9yOiAjY2YxMzIyOyB9XG5cbi5zZWxlY3Qge1xuICBwYWRkaW5nOiA0cHggMTBweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2QwZDdkZTtcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xuICBmb250LXNpemU6IDAuODVyZW07XG4gIGJhY2tncm91bmQ6ICNmZmY7XG59XG5cbi5idG4tc2Vjb25kYXJ5IHtcbiAgcGFkZGluZzogNnB4IDE2cHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNkMGQ3ZGU7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGJvcmRlci1yYWRpdXM6IDZweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDAuODVyZW07XG59XG4uYnRuLXNlY29uZGFyeTpob3Zlcjpub3QoOmRpc2FibGVkKSB7IGJvcmRlci1jb2xvcjogIzE4OTBmZjsgY29sb3I6ICMxODkwZmY7IH1cbi5idG4tc2Vjb25kYXJ5OmRpc2FibGVkIHsgb3BhY2l0eTogMC41OyBjdXJzb3I6IG5vdC1hbGxvd2VkOyB9XG5cbi5idG4tcHJpbWFyeSB7XG4gIHBhZGRpbmc6IDZweCAxNnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZmE4YzE2O1xuICBiYWNrZ3JvdW5kOiAjZmE4YzE2O1xuICBjb2xvcjogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMC44NXJlbTtcbiAgZm9udC13ZWlnaHQ6IDUwMDtcbn1cbi5idG4tcHJpbWFyeTpob3Zlcjpub3QoOmRpc2FibGVkKSB7IGJhY2tncm91bmQ6ICNkNDZiMDg7IGJvcmRlci1jb2xvcjogI2Q0NmIwODsgfVxuLmJ0bi1wcmltYXJ5OmRpc2FibGVkIHsgb3BhY2l0eTogMC40OyBjdXJzb3I6IG5vdC1hbGxvd2VkOyBiYWNrZ3JvdW5kOiAjY2NjOyBib3JkZXItY29sb3I6ICNjY2M7IH1cblxuLnJ1bGVzLWNhcmQge1xuICBiYWNrZ3JvdW5kOiAjZmFmYmZjO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZTFlNGU4O1xuICBib3JkZXItcmFkaXVzOiA4cHg7XG4gIHBhZGRpbmc6IDhweCAxNnB4O1xuICBtYXJnaW4tYm90dG9tOiAxNnB4O1xuICBmb250LXNpemU6IDAuODVyZW07XG59XG4ucnVsZXMtY2FyZCBzdW1tYXJ5IHsgY3Vyc29yOiBwb2ludGVyOyB1c2VyLXNlbGVjdDogbm9uZTsgY29sb3I6ICM1NTU7IH1cbi5ydWxlcy1ncmlkIHsgbWFyZ2luLXRvcDogMTBweDsgZGlzcGxheTogZmxleDsgZmxleC1kaXJlY3Rpb246IGNvbHVtbjsgZ2FwOiA2cHg7IH1cbi5ydWxlLXJvdyB7IGRpc3BsYXk6IGZsZXg7IGFsaWduLWl0ZW1zOiBjZW50ZXI7IGdhcDogOHB4OyBjb2xvcjogIzQ0NDsgfVxuXG4uZXJyb3ItYmFubmVyIHtcbiAgcGFkZGluZzogMTBweCAxNHB4O1xuICBiYWNrZ3JvdW5kOiAjZmZmMWYwO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZmZjY2M3O1xuICBjb2xvcjogI2NmMTMyMjtcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xuICBtYXJnaW4tYm90dG9tOiAxMnB4O1xufVxuXG4uZGFzaGJvYXJkLXRhYmxlIHtcbiAgZGlzcGxheTogZmxleDtcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcbiAgZ2FwOiA4cHg7XG59XG5cbi50YWJsZS1yb3cge1xuICBkaXNwbGF5OiBncmlkO1xuICAvKiBjaGVja2JveCArIOinhumikeS/oeaBryArIOi3qOW5s+WPsOWQiOiuoSArIDMg5bmz5Y+wICovXG4gIGdyaWQtdGVtcGxhdGUtY29sdW1uczogMzZweCAyLjRmciAxZnIgMS40ZnIgMS40ZnIgMS40ZnI7XG4gIGdhcDogOHB4O1xuICBwYWRkaW5nOiAxMnB4IDE0cHg7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlOGVhZWQ7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgYWxpZ24taXRlbXM6IHN0cmV0Y2g7XG59XG5cbi5jb2wtY2hlY2sge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBqdXN0aWZ5LWNvbnRlbnQ6IGNlbnRlcjtcbn1cbi5jb2wtY2hlY2sgaW5wdXRbdHlwZT1cImNoZWNrYm94XCJdIHtcbiAgd2lkdGg6IDE2cHg7XG4gIGhlaWdodDogMTZweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xufVxuXG4ucm93LXNlbGVjdGVkIHtcbiAgYmFja2dyb3VuZDogI2ZmZmJlNiAhaW1wb3J0YW50O1xuICBib3JkZXItY29sb3I6ICNmZmU1OGYgIWltcG9ydGFudDtcbn1cblxuLnRhYmxlLWhlYWQge1xuICBiYWNrZ3JvdW5kOiAjZjVmN2ZhO1xuICBmb250LXNpemU6IDAuOHJlbTtcbiAgZm9udC13ZWlnaHQ6IDYwMDtcbiAgY29sb3I6ICM2NjY7XG4gIGxldHRlci1zcGFjaW5nOiAwLjVweDtcbiAgcGFkZGluZzogOHB4IDE0cHg7XG59XG5cbi5kYXRhLXJvdyB7IHRyYW5zaXRpb246IGJveC1zaGFkb3cgMC4xNXM7IH1cbi5kYXRhLXJvdzpob3ZlciB7IGJveC1zaGFkb3c6IDAgMnB4IDhweCByZ2JhKDAsMCwwLDAuMDYpOyB9XG4uZGF0YS1yb3cudG9wLW11c3QgeyBib3JkZXItbGVmdDogNHB4IHNvbGlkICNmNTIyMmQ7IH1cbi5kYXRhLXJvdy50b3AtZ29vZCB7IGJvcmRlci1sZWZ0OiA0cHggc29saWQgI2ZhOGMxNjsgfVxuLmRhdGEtcm93LnRvcC1za2lwIHsgYm9yZGVyLWxlZnQ6IDRweCBzb2xpZCAjYmZiZmJmOyBvcGFjaXR5OiAwLjg1OyB9XG4vKiDmlbTooYzku7vkuIDlubPlj7AgZGVhZCwg5Y2z5L6/57u85ZCI5pivIGdvb2QvbXVzdCwg5Lmf5Yqg5bem5L6n57Sr57qi6Imy5o+Q56S65p2hICjot58gdG9wLW11c3Qg57qi5Yy65YiGKSAqL1xuLmRhdGEtcm93LnRvcC1kZWFkIHtcbiAgYm9yZGVyLWxlZnQ6IDRweCBzb2xpZCAjY2YxMzIyO1xuICBiYWNrZ3JvdW5kOiBsaW5lYXItZ3JhZGllbnQoOTBkZWcsIHJnYmEoMjU1LCA3NywgNzksIDAuMDYpIDAlLCAjZmZmIDgwJSk7XG59XG4uZGF0YS1yb3cucm93LWhhcy1kZWFkIHsgYm9yZGVyLWxlZnQ6IDRweCBzb2xpZCAjYzQxZDdmOyB9XG5cbi5jb2wtdmlkZW8ge1xuICBkaXNwbGF5OiBmbGV4O1xuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICBnYXA6IDRweDtcbiAgbWluLXdpZHRoOiAwO1xufVxuXG4udmlkZW8tdGl0bGUtcm93IHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA4cHg7XG4gIGZsZXgtd3JhcDogd3JhcDtcbn1cblxuLnZpZGVvLXRpdGxlLWxpbmsge1xuICBjb2xvcjogIzE4OTBmZjtcbiAgdGV4dC1kZWNvcmF0aW9uOiBub25lO1xuICBmb250LXdlaWdodDogNTAwO1xuICBmb250LXNpemU6IDAuOTVyZW07XG4gIHdoaXRlLXNwYWNlOiBub3dyYXA7XG4gIG92ZXJmbG93OiBoaWRkZW47XG4gIHRleHQtb3ZlcmZsb3c6IGVsbGlwc2lzO1xufVxuLnZpZGVvLXRpdGxlLWxpbms6aG92ZXIgeyB0ZXh0LWRlY29yYXRpb246IHVuZGVybGluZTsgfVxuXG4udmlkZW8tbWV0YSB7IGNvbG9yOiAjOTk5OyBmb250LXNpemU6IDAuNzhyZW07IH1cblxuLmNvbC10b3RhbHMsIC5jb2wtcGxhdGZvcm0ge1xuICBkaXNwbGF5OiBmbGV4O1xuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICBnYXA6IDRweDtcbiAgZm9udC1zaXplOiAwLjg1cmVtO1xufVxuXG4udG90YWwtbGluZSwgLnBsYXQtbGluZSB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogMTJweDtcbiAgZmxleC13cmFwOiB3cmFwO1xufVxuXG4ubWV0cmljIHtcbiAgZGlzcGxheTogaW5saW5lLWZsZXg7XG4gIGFsaWduLWl0ZW1zOiBiYXNlbGluZTtcbiAgZ2FwOiAzcHg7XG59XG4ubWV0cmljLW51bSB7IGZvbnQtd2VpZ2h0OiA2MDA7IGNvbG9yOiAjMmMzZTUwOyB9XG4ubWV0cmljLWxhYmVsIHsgZm9udC1zaXplOiAwLjcycmVtOyBjb2xvcjogIzk5OTsgfVxuXG4ucmF0aW8tbnVtLmhvdCB7IGNvbG9yOiAjZmE1NDFjOyB9XG5cbi5sdmwtYmFkZ2Uge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG4gIHBhZGRpbmc6IDJweCA4cHg7XG4gIGJvcmRlci1yYWRpdXM6IDEwcHg7XG4gIGZvbnQtc2l6ZTogMC43MnJlbTtcbiAgZm9udC13ZWlnaHQ6IDYwMDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgY3Vyc29yOiBoZWxwO1xufVxuLmx2bC1iYWRnZS5zbWFsbCB7IHBhZGRpbmc6IDFweCA2cHg7IGZvbnQtc2l6ZTogMC42OHJlbTsgfVxuLmx2bC1tdXN0IHsgYmFja2dyb3VuZDogI2ZmZjFmMDsgY29sb3I6ICNjZjEzMjI7IGJvcmRlcjogMXB4IHNvbGlkICNmZmEzOWU7IH1cbi5sdmwtZ29vZCB7IGJhY2tncm91bmQ6ICNmZmY3ZTY7IGNvbG9yOiAjZDQ2YjA4OyBib3JkZXI6IDFweCBzb2xpZCAjZmZkNTkxOyB9XG4ubHZsLXdhdGNoIHsgYmFja2dyb3VuZDogI2Y1ZjVmNTsgY29sb3I6ICM4ODg7IGJvcmRlcjogMXB4IHNvbGlkICNkOWQ5ZDk7IH1cbi5sdmwtc2tpcCB7IGJhY2tncm91bmQ6ICNmYWZhZmE7IGNvbG9yOiAjYmZiZmJmOyBib3JkZXI6IDFweCBzb2xpZCAjZjBmMGYwOyB9XG4vKiBkZWFkID0g6ZmQ5rWB5auM55aRLiDnlKjmnIDphpLnm67nmoTnuq/nuqIsIOi3nyBtdXN0IOeahOa1hee6ouWMuuWIhuW8gCAobXVzdCDmmK8gXCLlvLrkv6Hlj7fmraPlkJFcIiwgZGVhZCDmmK8gXCLlvLrkv6Hlj7fotJ/lkJFcIikgKi9cbi5sdmwtZGVhZCB7XG4gIGJhY2tncm91bmQ6ICNjZjEzMjI7XG4gIGNvbG9yOiAjZmZmO1xuICBib3JkZXI6IDFweCBzb2xpZCAjY2YxMzIyO1xuICBmb250LXdlaWdodDogNzAwO1xufVxuXG4ucGxhdC1jZWxsIHsgcGFkZGluZzogNnB4IDhweDsgYm9yZGVyLXJhZGl1czogNnB4OyB9XG4uY2VsbC1tdXN0IHsgYmFja2dyb3VuZDogcmdiYSgyNTUsIDc3LCA3OSwgMC4wNCk7IH1cbi5jZWxsLWdvb2QgeyBiYWNrZ3JvdW5kOiByZ2JhKDI1MCwgMTQwLCAyMiwgMC4wNCk7IH1cbi5jZWxsLWVtcHR5IHsgYmFja2dyb3VuZDogdHJhbnNwYXJlbnQ7IH1cbi8qIOW5s+WPsOagvOWtkCBkZWFkIOWKoOe6ouiJsuiDjOaZrywg6K6p6K+l5qC85Zyo5pW06KGM6YeM6Z2e5bi456qB5Ye6ICovXG4uY2VsbC1kZWFkIHtcbiAgYmFja2dyb3VuZDogcmdiYSgyMDcsIDE5LCAzNCwgMC4wOCk7XG4gIGJvcmRlcjogMXB4IHNvbGlkIHJnYmEoMjA3LCAxOSwgMzQsIDAuMjUpO1xufVxuXG4ucGxhdC1saW5rIHtcbiAgY29sb3I6ICMxODkwZmY7XG4gIHRleHQtZGVjb3JhdGlvbjogbm9uZTtcbiAgZm9udC1zaXplOiAwLjlyZW07XG59XG4ucGxhdC1saW5rOmhvdmVyIHsgdGV4dC1kZWNvcmF0aW9uOiB1bmRlcmxpbmU7IH1cblxuLnBsYXQtZW1wdHkge1xuICBjb2xvcjogI2NjYztcbiAgZm9udC1zaXplOiAwLjc4cmVtO1xuICBmb250LXN0eWxlOiBpdGFsaWM7XG59XG5cbi5ib29zdC10YWcge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG4gIHBhZGRpbmc6IDFweCA2cHg7XG4gIGZvbnQtc2l6ZTogMC43cmVtO1xuICBib3JkZXItcmFkaXVzOiAxMHB4O1xuICBiYWNrZ3JvdW5kOiAjZjBmNWZmO1xuICBjb2xvcjogIzJmNTRlYjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2FkYzZmZjtcbn1cbi5ib29zdC10YWcuYm9vc3QtYWN0aXZlIHsgYmFja2dyb3VuZDogI2ZmZjdlNjsgY29sb3I6ICNkNDZiMDg7IGJvcmRlci1jb2xvcjogI2ZmZDU5MTsgfVxuLmJvb3N0LXRhZy5ib29zdC1jb21wbGV0ZWQgeyBiYWNrZ3JvdW5kOiAjZjZmZmVkOyBjb2xvcjogIzM4OWUwZDsgYm9yZGVyLWNvbG9yOiAjYjdlYjhmOyB9XG4uYm9vc3QtdGFnLmJvb3N0LWZhaWxlZCB7IGJhY2tncm91bmQ6ICNmZmYxZjA7IGNvbG9yOiAjY2YxMzIyOyBib3JkZXItY29sb3I6ICNmZmEzOWU7IH1cbi5ib29zdC10YWcuYm9vc3QtYXdhaXQtcXIge1xuICBiYWNrZ3JvdW5kOiAjZmZmMGY2OyBjb2xvcjogI2M0MWQ3ZjsgYm9yZGVyLWNvbG9yOiAjZmZhZGQyO1xuICBtYXJnaW4tbGVmdDogNHB4OyBmb250LXdlaWdodDogNjAwO1xufVxuXG4vKiDns7vnu5/nuqfnmbvlvZXmgIHlkYroraYgYmFubmVyOiDlkI7lj7DlkIzmraXliqDng63orqLljZXml7blj5HnjrDmn5DlubPlj7AgOTIyMiBjaHJvbWUg5rKh55m75b2VICovXG4vKiDlvoXmiYvmnLrmiavnoIEgYmFubmVyOiDphpLnm67nsonnuqIsIOW8uuWItuiuqeeUqOaIt+azqOaEj+WIsCAqL1xuLnFyLXBlbmRpbmctYmFubmVyIHtcbiAgbWFyZ2luOiAxMnB4IDA7XG4gIHBhZGRpbmc6IDEycHggMTZweDtcbiAgYmFja2dyb3VuZDogbGluZWFyLWdyYWRpZW50KDkwZGVnLCAjZmZmMGY2IDAlLCAjZmZmN2U2IDEwMCUpO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZmZhZGQyO1xuICBib3JkZXItbGVmdDogNHB4IHNvbGlkICNjNDFkN2Y7XG4gIGJvcmRlci1yYWRpdXM6IDZweDtcbn1cbi5xci1wZW5kaW5nLXRleHQge1xuICBmb250LXNpemU6IDAuOTJyZW07XG4gIGNvbG9yOiAjNTMxZGFiO1xuICBtYXJnaW4tYm90dG9tOiA4cHg7XG59XG4ucXItcGVuZGluZy10ZXh0IGIgeyBjb2xvcjogI2M0MWQ3ZjsgZm9udC1zaXplOiAxLjA1cmVtOyBwYWRkaW5nOiAwIDJweDsgfVxuLnFyLXBlbmRpbmctYmFkZ2Uge1xuICBkaXNwbGF5OiBpbmxpbmUtYmxvY2s7XG4gIHBhZGRpbmc6IDJweCA4cHg7XG4gIG1hcmdpbi1yaWdodDogOHB4O1xuICBiYWNrZ3JvdW5kOiAjYzQxZDdmO1xuICBjb2xvcjogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXNpemU6IDAuNzVyZW07XG4gIGZvbnQtd2VpZ2h0OiA2MDA7XG4gIHZlcnRpY2FsLWFsaWduOiAxcHg7XG59XG4ucXItcGVuZGluZy1saXN0IHtcbiAgZGlzcGxheTogZmxleDtcbiAgZmxleC13cmFwOiB3cmFwO1xuICBnYXA6IDZweDtcbn1cbi5xci1wZW5kaW5nLWl0ZW0gLnFyLWJ0biB7XG4gIG1heC13aWR0aDogMzIwcHg7XG4gIG92ZXJmbG93OiBoaWRkZW47XG4gIHRleHQtb3ZlcmZsb3c6IGVsbGlwc2lzO1xuICB3aGl0ZS1zcGFjZTogbm93cmFwO1xufVxuXG4vKiByZWNlbnRfb3JkZXJzIOihqOmHjOeahOW+heaJq+eggeihjOWKoOW3pui+ueahhiArIOa1heW6leiJsiwg6LefIGFjdGl2ZSDkuIDmoLfphpLnm64gKi9cbi5ib29zdC10b3AtdGFibGUgLm9yZGVyLWF3YWl0LXFyIHRkOmZpcnN0LWNoaWxkIHsgYm9yZGVyLWxlZnQ6IDNweCBzb2xpZCAjYzQxZDdmOyB9XG4uYm9vc3QtdG9wLXRhYmxlIC5vcmRlci1hd2FpdC1xciB7IGJhY2tncm91bmQ6IHJnYmEoMTk2LCAyOSwgMTI3LCAwLjA1KTsgfVxuXG4vKiDlubPlj7Dnoazkv6Hlj7fnn63moIfnrb4gKHJldmlld2luZy9wcml2YXRlL3JlY29tbWVuZGVkX2Jsb2NrZWQsIOS4jeWIsCBkZWFkIOS9huimgeiuqeeUqOaIt+efpemBkykgKi9cbi5zdGF0dXMtdGFnIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xuICBwYWRkaW5nOiAxcHggNnB4O1xuICBmb250LXNpemU6IDAuN3JlbTtcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xuICBib3JkZXI6IDFweCBzb2xpZCB0cmFuc3BhcmVudDtcbiAgY3Vyc29yOiBoZWxwO1xufVxuLnN0YXR1cy10YWcuc3RhdHVzLXJldmlld2luZyB7IGJhY2tncm91bmQ6ICNmZmY3ZTY7IGNvbG9yOiAjZDQ2YjA4OyBib3JkZXItY29sb3I6ICNmZmQ1OTE7IH1cbi5zdGF0dXMtdGFnLnN0YXR1cy1wcml2YXRlIHsgYmFja2dyb3VuZDogI2YwZjVmZjsgY29sb3I6ICMyZjU0ZWI7IGJvcmRlci1jb2xvcjogI2FkYzZmZjsgfVxuLnN0YXR1cy10YWcuc3RhdHVzLXJlY29tbWVuZGVkX2Jsb2NrZWQgeyBiYWNrZ3JvdW5kOiAjZmZmMWYwOyBjb2xvcjogI2NmMTMyMjsgYm9yZGVyLWNvbG9yOiAjZmZhMzllOyB9XG5cbi5sb2FkaW5nLCAuZW1wdHkge1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIHBhZGRpbmc6IDQwcHg7XG4gIGNvbG9yOiAjOTk5O1xuICBmb250LXNpemU6IDAuOTVyZW07XG59XG5cbi5wYWdpbmF0aW9uIHtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogMTZweDtcbiAgbWFyZ2luLXRvcDogMjRweDtcbn1cbi5wYWdlLWJ0biB7XG4gIHBhZGRpbmc6IDZweCAxNnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDBkN2RlO1xuICBiYWNrZ3JvdW5kOiAjZmZmO1xuICBib3JkZXItcmFkaXVzOiA2cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAwLjg1cmVtO1xufVxuLnBhZ2UtYnRuOmhvdmVyOm5vdCg6ZGlzYWJsZWQpIHsgYm9yZGVyLWNvbG9yOiAjMTg5MGZmOyBjb2xvcjogIzE4OTBmZjsgfVxuLnBhZ2UtYnRuOmRpc2FibGVkIHsgb3BhY2l0eTogMC40OyBjdXJzb3I6IG5vdC1hbGxvd2VkOyB9XG4ucGFnZS1pbmZvIHsgY29sb3I6ICM2NjY7IGZvbnQtc2l6ZTogMC44NXJlbTsgfVxuXG4vKiA9PT0g5oqV5pS+5oCn5Lu35q+U5Y2h54mHID09PSAqL1xuLmJvb3N0LXN1bW1hcnktY2FyZCB7XG4gIGJhY2tncm91bmQ6IGxpbmVhci1ncmFkaWVudCgxODBkZWcsICNmZmY4ZjEgMCUsICNmZmZmZmYgMTAwJSk7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmQ5YjM7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgcGFkZGluZzogMTZweCAyMHB4O1xuICBtYXJnaW46IDEycHggMCAyMHB4O1xufVxuXG4vKiDop4bpopHlj7fmipXmlL7nvqTljaHniYcgKi9cbi5hdWRpZW5jZS1ncm91cHMtY2FyZCB7XG4gIGJhY2tncm91bmQ6ICNmNmZhZmY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNjZmUzZmY7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgcGFkZGluZzogMTRweCAxOHB4O1xuICBtYXJnaW46IDEycHggMCAxNnB4O1xufVxuLmFnLWhlYWQgeyBkaXNwbGF5OiBmbGV4OyBhbGlnbi1pdGVtczogYmFzZWxpbmU7IGdhcDogMTJweDsgbWFyZ2luLWJvdHRvbTogMTBweDsgZmxleC13cmFwOiB3cmFwOyB9XG4uYWctaGludCB7IGNvbG9yOiAjODg4OyBmb250LXNpemU6IDAuOHJlbTsgfVxuLmFnLWxpc3QgeyBkaXNwbGF5OiBmbGV4OyBnYXA6IDEycHg7IGZsZXgtd3JhcDogd3JhcDsgfVxuLmFnLWl0ZW0ge1xuICBmbGV4OiAxIDEgMjgwcHg7IG1pbi13aWR0aDogMjYwcHg7XG4gIGJhY2tncm91bmQ6ICNmZmY7IGJvcmRlcjogMXB4IHNvbGlkICNlM2VlZmM7IGJvcmRlci1yYWRpdXM6IDZweDsgcGFkZGluZzogMTBweCAxMnB4O1xufVxuLmFnLWl0ZW0uYWctZGVmYXVsdCB7IGJvcmRlci1jb2xvcjogIzE2NzdmZjsgYm94LXNoYWRvdzogMCAwIDAgMXB4ICMxNjc3ZmYzMzsgfVxuLmFnLWl0ZW0taGVhZCB7IGRpc3BsYXk6IGZsZXg7IGFsaWduLWl0ZW1zOiBjZW50ZXI7IGdhcDogOHB4OyBtYXJnaW4tYm90dG9tOiA0cHg7IH1cbi5hZy1uYW1lIHsgZm9udC13ZWlnaHQ6IDYwMDsgY29sb3I6ICMxZjNhNWY7IH1cbi5hZy1iYWRnZSB7IGZvbnQtc2l6ZTogMC43cmVtOyBjb2xvcjogIzE2NzdmZjsgYmFja2dyb3VuZDogI2U2ZjBmZjsgYm9yZGVyLXJhZGl1czogNHB4OyBwYWRkaW5nOiAxcHggNnB4OyB9XG4uYWctY291bnQgeyBtYXJnaW4tbGVmdDogYXV0bzsgY29sb3I6ICM5OTk7IGZvbnQtc2l6ZTogMC43OHJlbTsgfVxuLmFnLWRlc2MgeyBjb2xvcjogIzc3NzsgZm9udC1zaXplOiAwLjhyZW07IG1hcmdpbi1ib3R0b206IDZweDsgfVxuLmFnLWNyZWF0b3JzIHsgZGlzcGxheTogZmxleDsgZ2FwOiA2cHg7IGZsZXgtd3JhcDogd3JhcDsgfVxuLmFnLWNyZWF0b3IgeyBmb250LXNpemU6IDAuNzhyZW07IGNvbG9yOiAjM2I1YjgwOyBiYWNrZ3JvdW5kOiAjZWVmNGZiOyBib3JkZXItcmFkaXVzOiA0cHg7IHBhZGRpbmc6IDJweCA3cHg7IH1cblxuLyog5o6S6Zmk5qCH6aKY5YWz6ZSu6K+N5Y2h54mHICovXG4uZXhjbHVkZWQta3ctY2FyZCB7XG4gIGJhY2tncm91bmQ6ICNmZmY3ZjQ7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmQ5Yzc7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgcGFkZGluZzogMTRweCAxOHB4O1xuICBtYXJnaW46IDEycHggMCAxNnB4O1xufVxuLmt3LWJvZHkgeyBkaXNwbGF5OiBmbGV4OyBhbGlnbi1pdGVtczogY2VudGVyOyBnYXA6IDE2cHg7IGZsZXgtd3JhcDogd3JhcDsgfVxuLmt3LWxpc3QgeyBkaXNwbGF5OiBmbGV4OyBnYXA6IDhweDsgZmxleC13cmFwOiB3cmFwOyBmbGV4OiAxIDEgMzAwcHg7IH1cbi5rdy1jaGlwIHtcbiAgZGlzcGxheTogaW5saW5lLWZsZXg7IGFsaWduLWl0ZW1zOiBjZW50ZXI7IGdhcDogNHB4O1xuICBmb250LXNpemU6IDAuODJyZW07IGNvbG9yOiAjOGEzYTEyO1xuICBiYWNrZ3JvdW5kOiAjZmZlOWRlOyBib3JkZXI6IDFweCBzb2xpZCAjZmZjNGE4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7IHBhZGRpbmc6IDNweCA2cHggM3B4IDlweDtcbn1cbi5rdy1kZWwge1xuICBib3JkZXI6IG5vbmU7IGJhY2tncm91bmQ6IHRyYW5zcGFyZW50OyBjb2xvcjogI2M0NTAwMDtcbiAgZm9udC1zaXplOiAwLjk1cmVtOyBsaW5lLWhlaWdodDogMTsgY3Vyc29yOiBwb2ludGVyOyBwYWRkaW5nOiAwIDJweDtcbn1cbi5rdy1kZWw6aG92ZXIgeyBjb2xvcjogI2ZmMjIwMDsgfVxuLmt3LWVtcHR5IHsgY29sb3I6ICNhYWE7IGZvbnQtc2l6ZTogMC44NXJlbTsgfVxuLmt3LWFkZCB7IGRpc3BsYXk6IGZsZXg7IGdhcDogOHB4OyB9XG4ua3ctYWRkIGlucHV0IHtcbiAgcGFkZGluZzogNXB4IDEwcHg7IGJvcmRlcjogMXB4IHNvbGlkICNmZmM0YTg7IGJvcmRlci1yYWRpdXM6IDRweDtcbiAgZm9udC1zaXplOiAwLjg1cmVtOyB3aWR0aDogMjAwcHg7XG59XG4ua3ctYWRkIGlucHV0OmZvY3VzIHsgb3V0bGluZTogbm9uZTsgYm9yZGVyLWNvbG9yOiAjZmY4YTUwOyB9XG4uYm9vc3Qtc3VtbWFyeS1oZWFkIHtcbiAgZGlzcGxheTogZmxleDsganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuOyBhbGlnbi1pdGVtczogY2VudGVyO1xuICBtYXJnaW4tYm90dG9tOiA0cHg7XG59XG4uY2FyZC10aXRsZSB7IG1hcmdpbjogMDsgZm9udC1zaXplOiAxLjA1cmVtOyBjb2xvcjogI2M0NTAwMDsgZm9udC13ZWlnaHQ6IDYwMDsgfVxuLmNhcmQtaGludCB7IGNvbG9yOiAjODg4OyBmb250LXNpemU6IDAuOHJlbTsgbWFyZ2luLWJvdHRvbTogMTJweDsgfVxuLmJvb3N0LXN1bW1hcnktY29udHJvbHMge1xuICBkaXNwbGF5OiBmbGV4OyBhbGlnbi1pdGVtczogY2VudGVyOyBnYXA6IDhweDtcbn1cbi5ib29zdC1yYXRlLWxhYmVsIHsgZm9udC1zaXplOiAwLjg1cmVtOyBjb2xvcjogIzY2NjsgfVxuLnNlbGVjdC1taW5pIHtcbiAgcGFkZGluZzogM3B4IDhweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2ZmZDliMztcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXNpemU6IDAuODJyZW07XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgY29sb3I6ICNjNDUwMDA7XG59XG4uYm9vc3QtZW1wdHkge1xuICBwYWRkaW5nOiAxNnB4OyBjb2xvcjogIzg4ODsgZm9udC1zaXplOiAwLjlyZW07XG4gIGJhY2tncm91bmQ6ICNmYWZhZmE7IGJvcmRlci1yYWRpdXM6IDZweDtcbn1cbi5ib29zdC1lbXB0eSBjb2RlIHtcbiAgYmFja2dyb3VuZDogI2YwZjBmMDsgcGFkZGluZzogMnB4IDZweDsgYm9yZGVyLXJhZGl1czogM3B4O1xuICBmb250LXNpemU6IDAuODVlbTsgY29sb3I6ICNjNDUwMDA7XG59XG4uYm9vc3QtcGxhdGZvcm1zIHtcbiAgZGlzcGxheTogZ3JpZDtcbiAgZ3JpZC10ZW1wbGF0ZS1jb2x1bW5zOiByZXBlYXQoYXV0by1maXQsIG1pbm1heCgzODBweCwgMWZyKSk7XG4gIGdhcDogMTJweDtcbn1cbi5ib29zdC1wY2FyZCB7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmMGUwZDA7XG4gIGJvcmRlci1yYWRpdXM6IDZweDtcbiAgcGFkZGluZzogMTJweCAxNHB4O1xufVxuLnBjYXJkLWhlYWQge1xuICBkaXNwbGF5OiBmbGV4OyBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47IGFsaWduLWl0ZW1zOiBiYXNlbGluZTtcbiAgbWFyZ2luLWJvdHRvbTogMTBweDtcbiAgYm9yZGVyLWJvdHRvbTogMXB4IGRhc2hlZCAjZjBlMGQwO1xuICBwYWRkaW5nLWJvdHRvbTogNnB4O1xufVxuLnBjYXJkLW5hbWUgeyBmb250LXdlaWdodDogNjAwOyBjb2xvcjogIzMzMzsgZm9udC1zaXplOiAwLjk1cmVtOyB9XG4ucGNhcmQtcGVyaW9kIHsgY29sb3I6ICM5OTk7IGZvbnQtc2l6ZTogMC43OHJlbTsgfVxuLnBjYXJkLWdyaWQge1xuICBkaXNwbGF5OiBncmlkO1xuICBncmlkLXRlbXBsYXRlLWNvbHVtbnM6IHJlcGVhdCg0LCAxZnIpO1xuICBnYXA6IDhweDtcbn1cbi5wbWV0cmljIHtcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xuICBwYWRkaW5nOiA2cHggNHB4O1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG59XG4ucG1ldHJpYy1udW0geyBmb250LXNpemU6IDEuMDVyZW07IGZvbnQtd2VpZ2h0OiA3MDA7IGNvbG9yOiAjMmMzZTUwOyBsaW5lLWhlaWdodDogMS4yOyB9XG4ucG1ldHJpYy1sYWJlbCB7IGZvbnQtc2l6ZTogMC43MnJlbTsgY29sb3I6ICM5OTk7IG1hcmdpbi10b3A6IDJweDsgfVxuLnBtZXRyaWMtc3ViIHsgZm9udC1zaXplOiAwLjdyZW07IGNvbG9yOiAjYWFhOyBtYXJnaW4tbGVmdDogMnB4OyB9XG4ucG1ldHJpYy1jb3N0IHsgYmFja2dyb3VuZDogI2ZmZjVlNjsgfVxuLnBtZXRyaWMtY29zdCAucG1ldHJpYy1udW0geyBjb2xvcjogI2M0NTAwMDsgfVxuLnBtZXRyaWMtZm9sbG93IHsgYmFja2dyb3VuZDogI2U2ZjdmZjsgfVxuLnBtZXRyaWMtZm9sbG93IC5wbWV0cmljLW51bSB7IGNvbG9yOiAjMDk2ZGQ5OyB9XG4ucG1ldHJpYy1yb2kgeyBiYWNrZ3JvdW5kOiAjZjZmZmVkOyB9XG4ucG1ldHJpYy1yb2kgLnBtZXRyaWMtbnVtIHsgY29sb3I6ICMzODllMGQ7IGZvbnQtc2l6ZTogMC45NXJlbTsgfVxuXG4uYm9vc3QtdG9wIHtcbiAgbWFyZ2luLXRvcDogMTRweDtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2YwZTBkMDtcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xufVxuLmJvb3N0LXRvcCBzdW1tYXJ5IHtcbiAgcGFkZGluZzogOHB4IDEycHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAwLjg4cmVtO1xuICBjb2xvcjogI2M0NTAwMDtcbiAgZm9udC13ZWlnaHQ6IDUwMDtcbn1cbi5ib29zdC10b3AtdGFibGUge1xuICB3aWR0aDogMTAwJTtcbiAgYm9yZGVyLWNvbGxhcHNlOiBjb2xsYXBzZTtcbiAgZm9udC1zaXplOiAwLjgycmVtO1xufVxuLmJvb3N0LXRvcC10YWJsZSB0aCwgLmJvb3N0LXRvcC10YWJsZSB0ZCB7XG4gIHBhZGRpbmc6IDZweCAxMHB4O1xuICBib3JkZXItdG9wOiAxcHggc29saWQgI2YzZjNmMztcbiAgdGV4dC1hbGlnbjogcmlnaHQ7XG59XG4uYm9vc3QtdG9wLXRhYmxlIHRoIHsgYmFja2dyb3VuZDogI2ZhZmFmYTsgY29sb3I6ICM2NjY7IGZvbnQtd2VpZ2h0OiA1MDA7IH1cbi5ib29zdC10b3AtdGFibGUgLnRoLWxlZnQsIC5ib29zdC10b3AtdGFibGUgLnRkLWxlZnQgeyB0ZXh0LWFsaWduOiBsZWZ0OyB9XG4uYm9vc3QtdG9wLXRhYmxlIC50aXRsZS1jZWxsIHsgdGV4dC1hbGlnbjogbGVmdDsgbWF4LXdpZHRoOiAzODBweDsgb3ZlcmZsb3c6IGhpZGRlbjsgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7IHdoaXRlLXNwYWNlOiBub3dyYXA7IH1cbi5ib29zdC10b3AtdGFibGUgLnRpdGxlLWNlbGwgYSB7IGNvbG9yOiAjMTg5MGZmOyB0ZXh0LWRlY29yYXRpb246IG5vbmU7IH1cbi5ib29zdC10b3AtdGFibGUgLnRpdGxlLWNlbGwgYTpob3ZlciB7IHRleHQtZGVjb3JhdGlvbjogdW5kZXJsaW5lOyB9XG4uYm9vc3QtdG9wLXRhYmxlIC5jZWxsLWZvbGxvdyB7IGNvbG9yOiAjMDk2ZGQ5OyBmb250LXdlaWdodDogNjAwOyB9XG4uYm9vc3QtdG9wLXRhYmxlIC5jZWxsLWNvc3QgeyBjb2xvcjogI2M0NTAwMDsgZm9udC13ZWlnaHQ6IDYwMDsgfVxuLmJvb3N0LXRvcC10YWJsZSAuY29zdC1jb2lucyB7IGNvbG9yOiAjYWFhOyBmb250LXdlaWdodDogNDAwOyBmb250LXNpemU6IDAuOTJlbTsgfVxuLmJvb3N0LXRvcC10YWJsZSAudGQtdGltZSB7IHdoaXRlLXNwYWNlOiBub3dyYXA7IGNvbG9yOiAjNTU1OyBmb250LXNpemU6IDAuNzhyZW07IH1cbi5ib29zdC10b3AtdGFibGUgLnRkLW1ldGEgeyB3aGl0ZS1zcGFjZTogbm93cmFwOyBjb2xvcjogI2FhYTsgZm9udC1zaXplOiAwLjc1cmVtOyB9XG4vKiBhY3RpdmUg5Y2V5Yqg5bem5L6n5qmZ6Imy5o+Q56S65p2hLCDlrrnmmJPmiavliLBcIui/mOWcqOi3kVwiICovXG4uYm9vc3QtdG9wLXRhYmxlIC5vcmRlci1hY3RpdmUgdGQ6Zmlyc3QtY2hpbGQgeyBib3JkZXItbGVmdDogM3B4IHNvbGlkICNmYThjMTY7IH1cbi5ib29zdC10b3AtdGFibGUgLm9yZGVyLWNvbXBsZXRlZCB0ZDpmaXJzdC1jaGlsZCB7IGJvcmRlci1sZWZ0OiAzcHggc29saWQgIzUyYzQxYTsgfVxuLmJvb3N0LXRvcC10YWJsZSAub3JkZXItZmFpbGVkIHRkOmZpcnN0LWNoaWxkIHsgYm9yZGVyLWxlZnQ6IDNweCBzb2xpZCAjY2YxMzIyOyB9XG4uYm9vc3QtdG9wLXRhYmxlIC5vcmRlci1hY3RpdmUgeyBiYWNrZ3JvdW5kOiByZ2JhKDI1MCwgMTQwLCAyMiwgMC4wNCk7IH1cblxuLyogPT09IOaJuemHj+WKoOeDreW8ueeqlyA9PT0gKi9cbi5tb2RhbC1tYXNrIHtcbiAgcG9zaXRpb246IGZpeGVkOyBpbnNldDogMDtcbiAgYmFja2dyb3VuZDogcmdiYSgwLCAwLCAwLCAwLjQ1KTtcbiAgei1pbmRleDogMTAwMDtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XG59XG4ubW9kYWwtY2FyZCB7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgd2lkdGg6IDcyMHB4O1xuICBtYXgtd2lkdGg6IDk1dnc7XG4gIG1heC1oZWlnaHQ6IDkwdmg7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG4gIGJveC1zaGFkb3c6IDAgOHB4IDMycHggcmdiYSgwLCAwLCAwLCAwLjIpO1xufVxuLm1vZGFsLWhlYWQge1xuICBwYWRkaW5nOiAxNHB4IDIwcHg7XG4gIGJvcmRlci1ib3R0b206IDFweCBzb2xpZCAjZjBmMGYwO1xuICBkaXNwbGF5OiBmbGV4O1xuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG59XG4ubW9kYWwtaGVhZCBoMyB7IG1hcmdpbjogMDsgZm9udC1zaXplOiAxLjA1cmVtOyBjb2xvcjogIzMzMzsgfVxuLm1vZGFsLWNsb3NlIHtcbiAgYmFja2dyb3VuZDogbm9uZTsgYm9yZGVyOiBub25lO1xuICBmb250LXNpemU6IDEuNnJlbTtcbiAgbGluZS1oZWlnaHQ6IDE7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgY29sb3I6ICM5OTk7XG4gIHBhZGRpbmc6IDAgNHB4O1xufVxuLm1vZGFsLWNsb3NlOmhvdmVyIHsgY29sb3I6ICMzMzM7IH1cbi5tb2RhbC1ib2R5IHtcbiAgcGFkZGluZzogMTZweCAyMHB4O1xuICBvdmVyZmxvdy15OiBhdXRvO1xuICBmbGV4OiAxO1xufVxuLm1vZGFsLXJvdyB7XG4gIGRpc3BsYXk6IGdyaWQ7XG4gIGdyaWQtdGVtcGxhdGUtY29sdW1uczogMTAwcHggMWZyO1xuICBnYXA6IDEycHg7XG4gIG1hcmdpbi1ib3R0b206IDE0cHg7XG4gIGFsaWduLWl0ZW1zOiBzdGFydDtcbn1cbi5tb2RhbC1yb3cgPiBsYWJlbCB7XG4gIGZvbnQtc2l6ZTogMC44NXJlbTtcbiAgY29sb3I6ICM1NTU7XG4gIHBhZGRpbmctdG9wOiA1cHg7XG4gIHRleHQtYWxpZ246IHJpZ2h0O1xufVxuLm1vZGFsLWhpbnQgeyBjb2xvcjogIzk5OTsgZm9udC1zaXplOiAwLjcycmVtOyB9XG4ucmFkaW8taW5saW5lLCAuY2hlY2staW5saW5lIHtcbiAgZGlzcGxheTogaW5saW5lLWZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogNHB4O1xuICBtYXJnaW4tcmlnaHQ6IDE4cHg7XG4gIGZvbnQtc2l6ZTogMC44NXJlbTtcbiAgY29sb3I6ICM0NDQ7XG4gIGN1cnNvcjogcG9pbnRlcjtcbn1cbi5tb2RhbC1pbnB1dCwgLm1vZGFsLXNlbGVjdCB7XG4gIHBhZGRpbmc6IDVweCAxMHB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDBkN2RlO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGZvbnQtc2l6ZTogMC44OHJlbTtcbiAgd2lkdGg6IDE4MHB4O1xufVxuLm1vZGFsLWlucHV0LXdpZGUgeyB3aWR0aDogMTAwJTsgbWF4LXdpZHRoOiA0ODBweDsgfVxuLm1vZGFsLXVuaXQgeyBmb250LXNpemU6IDAuNzVyZW07IGNvbG9yOiAjODg4OyBtYXJnaW4tbGVmdDogOHB4OyB9XG4ubW9kYWwtd2FybiB7IGNvbG9yOiAjY2YxMzIyOyBtYXJnaW4tbGVmdDogOHB4OyBmb250LXdlaWdodDogNjAwOyBmb250LXNpemU6IDAuNzhyZW07IH1cblxuLm1vZGFsLXZpZGVvcyB7XG4gIG1heC1oZWlnaHQ6IDIwMHB4O1xuICBvdmVyZmxvdy15OiBhdXRvO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZjBmMGYwO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIHBhZGRpbmc6IDZweDtcbiAgYmFja2dyb3VuZDogI2ZhZmFmYTtcbn1cbi5tb2RhbC12aWRlby1saW5lIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA4cHg7XG4gIHBhZGRpbmc6IDNweCA2cHg7XG4gIGZvbnQtc2l6ZTogMC44MnJlbTtcbiAgY29sb3I6ICM0NDQ7XG4gIGJvcmRlci1yYWRpdXM6IDNweDtcbn1cbi5tb2RhbC12aWRlby1saW5lLnZpZGVvLXNraXAgeyBvcGFjaXR5OiAwLjU7IHRleHQtZGVjb3JhdGlvbjogbGluZS10aHJvdWdoOyB9XG4ubW9kYWwtdmlkZW8tc3RhdHVzIHsgd2lkdGg6IDE4cHg7IHRleHQtYWxpZ246IGNlbnRlcjsgfVxuLm9rLW1hcmsgeyBjb2xvcjogIzUyYzQxYTsgZm9udC13ZWlnaHQ6IGJvbGQ7IH1cbi5za2lwLW1hcmsgeyBjb2xvcjogI2NmMTMyMjsgZm9udC13ZWlnaHQ6IGJvbGQ7IGN1cnNvcjogaGVscDsgfVxuLm1vZGFsLXZpZGVvLXRpdGxlIHtcbiAgZmxleDogMTsgb3ZlcmZsb3c6IGhpZGRlbjsgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7IHdoaXRlLXNwYWNlOiBub3dyYXA7XG59XG4ubW9kYWwtdmlkZW8tdnBpZCB7IGNvbG9yOiAjODg4OyBmb250LXNpemU6IDAuNzJyZW07IH1cbi5tb2RhbC1lbXB0eSB7IGNvbG9yOiAjOTk5OyBwYWRkaW5nOiA4cHg7IHRleHQtYWxpZ246IGNlbnRlcjsgfVxuXG4ubW9kYWwtZm9vdGVyIHtcbiAgcGFkZGluZzogMTJweCAyMHB4O1xuICBib3JkZXItdG9wOiAxcHggc29saWQgI2YwZjBmMDtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBmbGV4LWVuZDtcbiAgZ2FwOiAxMHB4O1xufVxuXG4vKiA9PT0g5om56YeP5Lu75Yqh6L+b5bqm5Y2h54mHID09PSAqL1xuLmJhdGNoLWpvYi1jYXJkIHtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2ZhOGMxNjtcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xuICBwYWRkaW5nOiAxNHB4IDE4cHg7XG4gIG1hcmdpbjogMTZweCAwO1xuICBib3gtc2hhZG93OiAwIDJweCA4cHggcmdiYSgyNTAsIDE0MCwgMjIsIDAuMTUpO1xufVxuLmJhdGNoLWpvYi1oZWFkIHtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBtYXJnaW4tYm90dG9tOiA0cHg7XG59XG4uYmF0Y2gtam9iLWhlYWQgaDMgeyBtYXJnaW46IDA7IGZvbnQtc2l6ZTogMXJlbTsgY29sb3I6ICNkNDZiMDg7IH1cbi5iYXRjaC1yZWplY3RlZC1udW0geyBjb2xvcjogI2NmMTMyMjsgZm9udC1zaXplOiAwLjg1ZW07IH1cblxuLnFyLWJ0biB7XG4gIHBhZGRpbmc6IDJweCAxMHB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjMTg5MGZmO1xuICBiYWNrZ3JvdW5kOiAjMTg5MGZmO1xuICBjb2xvcjogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXNpemU6IDAuNzhyZW07XG4gIGN1cnNvcjogcG9pbnRlcjtcbn1cbi5xci1idG46aG92ZXIgeyBiYWNrZ3JvdW5kOiAjMDk2ZGQ5OyBib3JkZXItY29sb3I6ICMwOTZkZDk7IH1cbi5xci1oaW50IHsgY29sb3I6ICM4ODg7IGZvbnQtc2l6ZTogMC43NXJlbTsgbWFyZ2luLWxlZnQ6IDZweDsgfVxuXG4ucXItbW9kYWwtY2FyZCB7IHdpZHRoOiA2NDBweDsgfVxuLnFyLW1vZGFsLWJvZHkgeyBwYWRkaW5nOiAyNHB4IDI4cHg7IHRleHQtYWxpZ246IGNlbnRlcjsgfVxuLnFyLXRpcCB7IG1hcmdpbjogMCAwIDE4cHg7IGNvbG9yOiAjMzMzOyBmb250LXNpemU6IDFyZW07IGZvbnQtd2VpZ2h0OiA1MDA7IH1cbi5xci1wcmV2aWV3LWltZyB7XG4gIG1heC13aWR0aDogNTIwcHg7XG4gIHdpZHRoOiAxMDAlO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZjBmMGYwO1xuICBib3JkZXItcmFkaXVzOiA2cHg7XG59XG4ucXItaGludC1zbWFsbCB7XG4gIG1hcmdpbjogMTZweCBhdXRvIDA7XG4gIG1heC13aWR0aDogNTQwcHg7XG4gIGNvbG9yOiAjODg4O1xuICBmb250LXNpemU6IDAuOHJlbTtcbiAgbGluZS1oZWlnaHQ6IDEuNTU7XG59XG5cbi8qIFFSIOW8ueeql+W6lemDqDog5bem5L6n54q25oCB5paH5qGIICsg5Y+z5L6n5oyJ6ZKu57uEICovXG4ucXItbW9kYWwtZm9vdGVyIHtcbiAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xufVxuLnFyLXN5bmMtc3RhdHVzIHtcbiAgZmxleDogMTtcbiAgdGV4dC1hbGlnbjogbGVmdDtcbiAgZm9udC1zaXplOiAwLjgycmVtO1xuICBjb2xvcjogIzY2NjtcbiAgcGFkZGluZy1yaWdodDogMTJweDtcbn1cbi5xci1zeW5jLXN0YXR1cy5xci1zeW5jLXN5bmNpbmcgeyBjb2xvcjogIzE4OTBmZjsgfVxuLnFyLXN5bmMtc3RhdHVzLnFyLXN5bmMtZG9uZSB7IGNvbG9yOiAjNTJjNDFhOyB9XG4ucXItc3luYy1zdGF0dXMucXItc3luYy10aW1lb3V0IHsgY29sb3I6ICNmYWFkMTQ7IH1cbi5xci1zeW5jLXN0YXR1cy5xci1zeW5jLWVycm9yIHsgY29sb3I6ICNjZjEzMjI7IH1cbi5xci1zeW5jLXN0YXR1cy5xci1zeW5jLXdhaXRpbmdfbG9naW4geyBjb2xvcjogI2Q0NmIwODsgZm9udC13ZWlnaHQ6IDYwMDsgfVxuXG4uYnRuLXByaW1hcnkge1xuICBwYWRkaW5nOiA2cHggMTZweDtcbiAgYm9yZGVyOiAxcHggc29saWQgIzE4OTBmZjtcbiAgYmFja2dyb3VuZDogIzE4OTBmZjtcbiAgY29sb3I6ICNmZmY7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgZm9udC1zaXplOiAwLjg2cmVtO1xuICBjdXJzb3I6IHBvaW50ZXI7XG59XG4uYnRuLXByaW1hcnk6aG92ZXI6bm90KDpkaXNhYmxlZCkgeyBiYWNrZ3JvdW5kOiAjMDk2ZGQ5OyBib3JkZXItY29sb3I6ICMwOTZkZDk7IH1cbi5idG4tcHJpbWFyeTpkaXNhYmxlZCB7IG9wYWNpdHk6IDAuNTU7IGN1cnNvcjogbm90LWFsbG93ZWQ7IH1cbi5idG4tc2Vjb25kYXJ5IHtcbiAgcGFkZGluZzogNnB4IDE0cHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNkMGQ3ZGU7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGNvbG9yOiAjNTU1O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGZvbnQtc2l6ZTogMC44NnJlbTtcbiAgY3Vyc29yOiBwb2ludGVyO1xufVxuLmJ0bi1zZWNvbmRhcnk6aG92ZXI6bm90KDpkaXNhYmxlZCkgeyBib3JkZXItY29sb3I6ICMxODkwZmY7IGNvbG9yOiAjMTg5MGZmOyB9XG4uYnRuLXNlY29uZGFyeTpkaXNhYmxlZCB7IG9wYWNpdHk6IDAuNTU7IGN1cnNvcjogbm90LWFsbG93ZWQ7IH1cbjwvc3R5bGU+XG4iXSwibWFwcGluZ3MiOiJBQWtrQkEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7Ozs7Ozs7O0FBRWxELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUV6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3Qjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFDOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7QUFFM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekI7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRTNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRTFELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2I7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25ELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRSxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEI7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEM7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0QsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckM7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZDs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkUsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEM7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEM7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakI7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQ7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRTlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVsRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNFLENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUM7O0FBRUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkM7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUU7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRTs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hFOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2RDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9FLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUI7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0I7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakcsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7QUFFdkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRXhCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9ELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9FLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVHLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0U7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0Qjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JFOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9FLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQztBQUNGO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFD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