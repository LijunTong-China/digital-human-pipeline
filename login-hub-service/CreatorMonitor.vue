import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/views/CreatorMonitor.vue");import { ref, reactive, onMounted } from "/node_modules/.vite/deps/vue.js?v=99b192bf"
import AppHeader from "/src/components/AppHeader.vue"
import { API_BASE_URL } from "/src/utils/apiConfig.js"


const _sfc_main = {
  __name: 'CreatorMonitor',
  setup(__props, { expose: __expose }) {
  __expose();

const subscriptions = ref([])
const loadingSubs = ref(false)
const currentSubId = ref(null)

const videos = ref([])
const videoTotal = ref(0)
const loadingVideos = ref(false)
const page = ref(1)
const pageSize = ref(20)
const filterTranscriptStatus = ref('')

const syncingAll = ref(false)
const syncingId = ref(null)
const transcribingId = ref(null)
const batchTranscribing = ref(false)

const showAddModal = ref(false)
const adding = ref(false)
const addError = ref('')
const addForm = reactive({ nickname: '', note: '', do_initial_sync: true })

const transcriptModal = reactive({ open: false, text: '', desc: '' })

// ============ 工具 ============
function formatNumber(n) {
  if (n == null) return '0'
  if (n >= 100000000) return (n / 100000000).toFixed(1) + '亿'
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  return String(n)
}

function formatTime(t) {
  if (!t) return '-'
  const d = new Date(t)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day} ${hh}:${mm}`
}

function formatDuration(sec) {
  if (!sec) return ''
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function truncate(s, n) {
  if (!s) return ''
  return s.length > n ? s.slice(0, n) + '...' : s
}

function transcriptStatusLabel(s) {
  return ({
    pending: '未生成',
    processing: '生成中',
    done: '已完成',
    failed: '失败',
    skipped: '已跳过',
  })[s] || s
}

// ============ 网络 ============
async function api(path, options = {}) {
  const url = `${API_BASE_URL}${path}`
  const opts = { headers: { 'Content-Type': 'application/json' }, ...options }
  const resp = await fetch(url, opts)
  const json = await resp.json()
  if (json.code !== 200 && json.code !== 0) {
    throw new Error(json.msg || `HTTP ${resp.status}`)
  }
  return json.data
}

// ============ 加载 ============
async function loadSubs() {
  loadingSubs.value = true
  try {
    subscriptions.value = await api('/api/videos/creators') || []
    if (!currentSubId.value && subscriptions.value.length > 0) {
      const firstActive = subscriptions.value.find(s => s.is_active) || subscriptions.value[0]
      selectSub(firstActive)
    }
  } catch (e) {
    alert('加载博主列表失败: ' + e.message)
  } finally {
    loadingSubs.value = false
  }
}

function selectSub(sub) {
  currentSubId.value = sub.id
  page.value = 1
  loadVideos(1)
}

async function loadVideos(p) {
  if (!currentSubId.value) return
  page.value = p
  loadingVideos.value = true
  try {
    const params = new URLSearchParams({
      subscription_id: String(currentSubId.value),
      page: String(p),
      page_size: String(pageSize.value),
    })
    if (filterTranscriptStatus.value) params.append('transcript_status', filterTranscriptStatus.value)
    const data = await api(`/api/videos/creator_videos?${params}`)
    videos.value = data.items || []
    videoTotal.value = data.total || 0
  } catch (e) {
    alert('加载视频失败: ' + e.message)
  } finally {
    loadingVideos.value = false
  }
}

// ============ 操作 ============
async function syncOne(sub) {
  syncingId.value = sub.id
  try {
    await api(`/api/videos/creators/${sub.id}/sync`, {
      method: 'POST',
      body: JSON.stringify({ max_pages: 3 }),
    })
    await loadSubs()
    if (currentSubId.value === sub.id) await loadVideos(1)
  } catch (e) {
    alert('同步失败: ' + e.message)
  } finally {
    syncingId.value = null
  }
}

async function syncAll() {
  if (!confirm('同步全部启用的博主？每个博主之间会间隔 8 秒')) return
  syncingAll.value = true
  try {
    await api('/api/videos/creators/sync_all', {
      method: 'POST',
      body: JSON.stringify({ max_pages: 3 }),
    })
    await loadSubs()
    if (currentSubId.value) await loadVideos(1)
  } catch (e) {
    alert('同步失败: ' + e.message)
  } finally {
    syncingAll.value = false
  }
}

async function toggleActive(sub) {
  try {
    await api(`/api/videos/creators/${sub.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ is_active: !sub.is_active }),
    })
    await loadSubs()
  } catch (e) {
    alert('操作失败: ' + e.message)
  }
}

async function submitAdd() {
  adding.value = true
  addError.value = ''
  try {
    await api('/api/videos/creators', {
      method: 'POST',
      body: JSON.stringify({
        nickname: addForm.nickname.trim(),
        note: addForm.note.trim() || null,
        do_initial_sync: addForm.do_initial_sync,
      }),
    })
    closeAddModal()
    await loadSubs()
  } catch (e) {
    addError.value = e.message
  } finally {
    adding.value = false
  }
}

function closeAddModal() {
  showAddModal.value = false
  addError.value = ''
  addForm.nickname = ''
  addForm.note = ''
  addForm.do_initial_sync = true
}

async function transcribeOne(v) {
  transcribingId.value = v.id
  try {
    await api(`/api/videos/creator_videos/${v.id}/transcribe`, { method: 'POST' })
    await loadVideos(page.value)
  } catch (e) {
    alert('生成失败: ' + e.message)
    await loadVideos(page.value)
  } finally {
    transcribingId.value = null
  }
}

async function batchTranscribe() {
  batchTranscribing.value = true
  try {
    await api('/api/videos/creator_videos/transcribe_batch', {
      method: 'POST',
      body: JSON.stringify({ limit: 5 }),
    })
    await loadVideos(page.value)
  } catch (e) {
    alert('批量生成失败: ' + e.message)
  } finally {
    batchTranscribing.value = false
  }
}

async function viewTranscript(v) {
  try {
    const data = await api(`/api/videos/creator_videos/${v.id}`)
    transcriptModal.text = data.transcript_text || '(本地文件读取失败)'
    transcriptModal.desc = (v.desc || '').slice(0, 60)
    transcriptModal.open = true
  } catch (e) {
    alert('加载文字稿失败: ' + e.message)
  }
}

function copyTranscript() {
  navigator.clipboard.writeText(transcriptModal.text || '').then(
    () => alert('已复制到剪贴板'),
    () => alert('复制失败')
  )
}

onMounted(loadSubs)

const __returned__ = { subscriptions, loadingSubs, currentSubId, videos, videoTotal, loadingVideos, page, pageSize, filterTranscriptStatus, syncingAll, syncingId, transcribingId, batchTranscribing, showAddModal, adding, addError, addForm, transcriptModal, formatNumber, formatTime, formatDuration, truncate, transcriptStatusLabel, api, loadSubs, selectSub, loadVideos, syncOne, syncAll, toggleActive, submitAdd, closeAddModal, transcribeOne, batchTranscribe, viewTranscript, copyTranscript, ref, reactive, onMounted, AppHeader, get API_BASE_URL() { return API_BASE_URL } }
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true })
return __returned__
}

}
import { createVNode as _createVNode, createElementVNode as _createElementVNode, toDisplayString as _toDisplayString, createCommentVNode as _createCommentVNode, openBlock as _openBlock, createElementBlock as _createElementBlock, renderList as _renderList, Fragment as _Fragment, createTextVNode as _createTextVNode, withModifiers as _withModifiers, normalizeClass as _normalizeClass, vModelSelect as _vModelSelect, withDirectives as _withDirectives, vModelText as _vModelText, withKeys as _withKeys, vModelCheckbox as _vModelCheckbox, createStaticVNode as _createStaticVNode } from "/node_modules/.vite/deps/vue.js?v=99b192bf"

const _hoisted_1 = { class: "creator-monitor" }
const _hoisted_2 = { class: "page-header" }
const _hoisted_3 = { class: "header-right" }
const _hoisted_4 = ["disabled"]
const _hoisted_5 = { class: "main-layout" }
const _hoisted_6 = { class: "creators-pane" }
const _hoisted_7 = { class: "pane-title" }
const _hoisted_8 = {
  key: 0,
  class: "empty"
}
const _hoisted_9 = {
  key: 1,
  class: "empty"
}
const _hoisted_10 = ["onClick"]
const _hoisted_11 = ["src"]
const _hoisted_12 = {
  key: 1,
  class: "avatar avatar-placeholder"
}
const _hoisted_13 = { class: "creator-info" }
const _hoisted_14 = { class: "creator-name" }
const _hoisted_15 = {
  key: 0,
  class: "tag-disabled"
}
const _hoisted_16 = { class: "creator-meta" }
const _hoisted_17 = {
  key: 0,
  class: "creator-meta"
}
const _hoisted_18 = {
  key: 0,
  class: "tag-failed"
}
const _hoisted_19 = {
  key: 1,
  class: "creator-note"
}
const _hoisted_20 = ["disabled", "onClick"]
const _hoisted_21 = ["onClick", "title"]
const _hoisted_22 = { class: "videos-pane" }
const _hoisted_23 = {
  key: 0,
  class: "empty-main"
}
const _hoisted_24 = { class: "videos-toolbar" }
const _hoisted_25 = { class: "toolbar-left" }
const _hoisted_26 = { class: "muted" }
const _hoisted_27 = { class: "toolbar-right" }
const _hoisted_28 = ["disabled"]
const _hoisted_29 = {
  key: 0,
  class: "empty-main"
}
const _hoisted_30 = {
  key: 1,
  class: "empty-main"
}
const _hoisted_31 = { class: "video-grid" }
const _hoisted_32 = ["href"]
const _hoisted_33 = ["src"]
const _hoisted_34 = {
  key: 1,
  class: "video-cover video-cover-placeholder"
}
const _hoisted_35 = { class: "duration-badge" }
const _hoisted_36 = { class: "video-body" }
const _hoisted_37 = ["title"]
const _hoisted_38 = { class: "video-meta" }
const _hoisted_39 = {
  key: 0,
  class: "dot"
}
const _hoisted_40 = { key: 1 }
const _hoisted_41 = ["href"]
const _hoisted_42 = { class: "video-stats" }
const _hoisted_43 = { title: "点赞" }
const _hoisted_44 = { title: "评论" }
const _hoisted_45 = { title: "收藏" }
const _hoisted_46 = { title: "分享" }
const _hoisted_47 = { class: "video-transcript" }
const _hoisted_48 = ["onClick"]
const _hoisted_49 = ["disabled", "onClick"]
const _hoisted_50 = ["title"]
const _hoisted_51 = {
  key: 2,
  class: "pagination"
}
const _hoisted_52 = ["disabled"]
const _hoisted_53 = ["disabled"]
const _hoisted_54 = { class: "modal" }
const _hoisted_55 = { class: "modal-body" }
const _hoisted_56 = { class: "modal-footer" }
const _hoisted_57 = ["disabled"]
const _hoisted_58 = ["disabled"]
const _hoisted_59 = {
  key: 0,
  class: "modal-error"
}
const _hoisted_60 = { class: "modal modal-wide" }
const _hoisted_61 = { class: "modal-title" }
const _hoisted_62 = { class: "muted" }
const _hoisted_63 = { class: "modal-body" }
const _hoisted_64 = { class: "transcript-text" }
const _hoisted_65 = { class: "modal-footer" }

function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createVNode($setup["AppHeader"]),
    _createElementVNode("div", _hoisted_1, [
      _createElementVNode("div", _hoisted_2, [
        _cache[11] || (_cache[11] = _createElementVNode("div", { class: "header-left" }, [
          _createElementVNode("h2", { class: "page-title" }, "对标博主监控"),
          _createElementVNode("span", { class: "sub-title" }, "采集指定博主的抖音视频，自动生成文字稿用于改写参考")
        ], -1 /* CACHED */)),
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("button", {
            class: "btn primary",
            onClick: _cache[0] || (_cache[0] = $event => ($setup.showAddModal = true))
          }, "+ 添加博主"),
          _createElementVNode("button", {
            class: "btn",
            disabled: $setup.syncingAll,
            onClick: $setup.syncAll
          }, _toDisplayString($setup.syncingAll ? '同步中...' : '同步全部'), 9 /* TEXT, PROPS */, _hoisted_4)
        ])
      ]),
      _createElementVNode("div", _hoisted_5, [
        _createCommentVNode(" 左栏：博主列表 "),
        _createElementVNode("aside", _hoisted_6, [
          _createElementVNode("div", _hoisted_7, "订阅博主 (" + _toDisplayString($setup.subscriptions.length) + ")", 1 /* TEXT */),
          ($setup.loadingSubs)
            ? (_openBlock(), _createElementBlock("div", _hoisted_8, "加载中..."))
            : ($setup.subscriptions.length === 0)
              ? (_openBlock(), _createElementBlock("div", _hoisted_9, "还没有订阅，点上方\"+ 添加博主\""))
              : _createCommentVNode("v-if", true),
          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.subscriptions, (sub) => {
            return (_openBlock(), _createElementBlock("div", {
              key: sub.id,
              class: _normalizeClass(["creator-item", { active: $setup.currentSubId === sub.id, inactive: !sub.is_active }]),
              onClick: $event => ($setup.selectSub(sub))
            }, [
              (sub.avatar_url)
                ? (_openBlock(), _createElementBlock("img", {
                    key: 0,
                    src: sub.avatar_url,
                    class: "avatar"
                  }, null, 8 /* PROPS */, _hoisted_11))
                : (_openBlock(), _createElementBlock("div", _hoisted_12, _toDisplayString((sub.nickname || '?').slice(0, 1)), 1 /* TEXT */)),
              _createElementVNode("div", _hoisted_13, [
                _createElementVNode("div", _hoisted_14, [
                  _createTextVNode(_toDisplayString(sub.nickname || '(未拉到昵称)') + " ", 1 /* TEXT */),
                  (!sub.is_active)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_15, "已停用"))
                    : _createCommentVNode("v-if", true)
                ]),
                _createElementVNode("div", _hoisted_16, " 已采集 " + _toDisplayString(sub.video_count || 0) + " 条 ", 1 /* TEXT */),
                (sub.last_sync_at)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_17, [
                      _createTextVNode(" 上次同步: " + _toDisplayString($setup.formatTime(sub.last_sync_at)) + " ", 1 /* TEXT */),
                      (sub.last_sync_status === 'failed')
                        ? (_openBlock(), _createElementBlock("span", _hoisted_18, "失败"))
                        : _createCommentVNode("v-if", true)
                    ]))
                  : _createCommentVNode("v-if", true),
                (sub.note)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_19, _toDisplayString(sub.note), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true)
              ]),
              _createElementVNode("div", {
                class: "creator-actions",
                onClick: _cache[1] || (_cache[1] = _withModifiers(() => {}, ["stop"]))
              }, [
                _createElementVNode("button", {
                  class: "icon-btn",
                  disabled: $setup.syncingId === sub.id,
                  onClick: $event => ($setup.syncOne(sub)),
                  title: "同步"
                }, _toDisplayString($setup.syncingId === sub.id ? '...' : '↻'), 9 /* TEXT, PROPS */, _hoisted_20),
                _createElementVNode("button", {
                  class: "icon-btn",
                  onClick: $event => ($setup.toggleActive(sub)),
                  title: sub.is_active ? '停用' : '启用'
                }, _toDisplayString(sub.is_active ? '⏸' : '▶'), 9 /* TEXT, PROPS */, _hoisted_21)
              ])
            ], 10 /* CLASS, PROPS */, _hoisted_10))
          }), 128 /* KEYED_FRAGMENT */))
        ]),
        _createCommentVNode(" 右栏：视频列表 "),
        _createElementVNode("section", _hoisted_22, [
          (!$setup.currentSubId)
            ? (_openBlock(), _createElementBlock("div", _hoisted_23, "从左侧选一个博主查看其视频"))
            : (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                _createElementVNode("div", _hoisted_24, [
                  _createElementVNode("div", _hoisted_25, [
                    _cache[13] || (_cache[13] = _createElementVNode("span", { class: "filter-label" }, "筛选:", -1 /* CACHED */)),
                    _withDirectives(_createElementVNode("select", {
                      "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => (($setup.filterTranscriptStatus) = $event)),
                      onChange: _cache[3] || (_cache[3] = $event => ($setup.loadVideos(1)))
                    }, [...(_cache[12] || (_cache[12] = [
                      _createStaticVNode("<option value=\"\" data-v-1d05471c>全部状态</option><option value=\"pending\" data-v-1d05471c>待生成文字稿</option><option value=\"processing\" data-v-1d05471c>生成中</option><option value=\"done\" data-v-1d05471c>已完成</option><option value=\"failed\" data-v-1d05471c>失败</option><option value=\"skipped\" data-v-1d05471c>已跳过</option>", 6)
                    ]))], 544 /* NEED_HYDRATION, NEED_PATCH */), [
                      [_vModelSelect, $setup.filterTranscriptStatus]
                    ]),
                    _createElementVNode("span", _hoisted_26, "共 " + _toDisplayString($setup.videoTotal) + " 条", 1 /* TEXT */)
                  ]),
                  _createElementVNode("div", _hoisted_27, [
                    _createElementVNode("button", {
                      class: "btn",
                      disabled: $setup.batchTranscribing,
                      onClick: $setup.batchTranscribe
                    }, _toDisplayString($setup.batchTranscribing ? '生成中...' : '批量生成文字稿(5条)'), 9 /* TEXT, PROPS */, _hoisted_28)
                  ])
                ]),
                ($setup.loadingVideos)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_29, "加载中..."))
                  : ($setup.videos.length === 0)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_30, "暂无视频"))
                    : _createCommentVNode("v-if", true),
                _createElementVNode("div", _hoisted_31, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.videos, (v) => {
                    return (_openBlock(), _createElementBlock("div", {
                      key: v.id,
                      class: "video-card"
                    }, [
                      _createElementVNode("a", {
                        href: v.share_url,
                        target: "_blank",
                        class: "video-cover-link",
                        title: "在抖音打开原视频"
                      }, [
                        (v.cover_url)
                          ? (_openBlock(), _createElementBlock("img", {
                              key: 0,
                              src: v.cover_url,
                              class: "video-cover"
                            }, null, 8 /* PROPS */, _hoisted_33))
                          : (_openBlock(), _createElementBlock("div", _hoisted_34, "无封面")),
                        _createElementVNode("span", _hoisted_35, _toDisplayString($setup.formatDuration(v.duration_sec)), 1 /* TEXT */)
                      ], 8 /* PROPS */, _hoisted_32),
                      _createElementVNode("div", _hoisted_36, [
                        _createElementVNode("div", {
                          class: "video-desc",
                          title: v.desc
                        }, _toDisplayString(v.desc || '(无文案)'), 9 /* TEXT, PROPS */, _hoisted_37),
                        _createElementVNode("div", _hoisted_38, [
                          _createElementVNode("span", null, _toDisplayString($setup.formatTime(v.published_at)), 1 /* TEXT */),
                          (v.duration_sec)
                            ? (_openBlock(), _createElementBlock("span", _hoisted_39, "·"))
                            : _createCommentVNode("v-if", true),
                          (v.duration_sec)
                            ? (_openBlock(), _createElementBlock("span", _hoisted_40, "时长 " + _toDisplayString($setup.formatDuration(v.duration_sec)), 1 /* TEXT */))
                            : _createCommentVNode("v-if", true),
                          _cache[14] || (_cache[14] = _createElementVNode("span", { class: "dot" }, "·", -1 /* CACHED */)),
                          _createElementVNode("a", {
                            href: v.share_url,
                            target: "_blank",
                            class: "open-link"
                          }, "看原视频 ↗", 8 /* PROPS */, _hoisted_41)
                        ]),
                        _createElementVNode("div", _hoisted_42, [
                          _createElementVNode("span", _hoisted_43, "♥ " + _toDisplayString($setup.formatNumber(v.digg_count)), 1 /* TEXT */),
                          _createElementVNode("span", _hoisted_44, "💬 " + _toDisplayString($setup.formatNumber(v.comment_count)), 1 /* TEXT */),
                          _createElementVNode("span", _hoisted_45, "⭐ " + _toDisplayString($setup.formatNumber(v.collect_count)), 1 /* TEXT */),
                          _createElementVNode("span", _hoisted_46, "↗ " + _toDisplayString($setup.formatNumber(v.share_count)), 1 /* TEXT */)
                        ]),
                        _createElementVNode("div", _hoisted_47, [
                          _createElementVNode("span", {
                            class: _normalizeClass(["transcript-status", `status-${v.transcript_status}`])
                          }, _toDisplayString($setup.transcriptStatusLabel(v.transcript_status)), 3 /* TEXT, CLASS */),
                          (v.transcript_status === 'done')
                            ? (_openBlock(), _createElementBlock("button", {
                                key: 0,
                                class: "link-btn",
                                onClick: $event => ($setup.viewTranscript(v))
                              }, " 查看文字稿 (" + _toDisplayString(v.transcript_chars) + " 字) ", 9 /* TEXT, PROPS */, _hoisted_48))
                            : (_openBlock(), _createElementBlock("button", {
                                key: 1,
                                class: "link-btn",
                                disabled: $setup.transcribingId === v.id || v.transcript_status === 'processing',
                                onClick: $event => ($setup.transcribeOne(v))
                              }, _toDisplayString($setup.transcribingId === v.id ? '生成中...' : '生成文字稿'), 9 /* TEXT, PROPS */, _hoisted_49)),
                          (v.transcript_error)
                            ? (_openBlock(), _createElementBlock("span", {
                                key: 2,
                                class: "error-msg",
                                title: v.transcript_error
                              }, " 错误: " + _toDisplayString($setup.truncate(v.transcript_error, 40)), 9 /* TEXT, PROPS */, _hoisted_50))
                            : _createCommentVNode("v-if", true)
                        ])
                      ])
                    ]))
                  }), 128 /* KEYED_FRAGMENT */))
                ]),
                ($setup.videoTotal > $setup.pageSize)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_51, [
                      _createElementVNode("button", {
                        class: "btn",
                        disabled: $setup.page <= 1,
                        onClick: _cache[4] || (_cache[4] = $event => ($setup.loadVideos($setup.page - 1)))
                      }, "上一页", 8 /* PROPS */, _hoisted_52),
                      _createElementVNode("span", null, "第 " + _toDisplayString($setup.page) + " / " + _toDisplayString(Math.ceil($setup.videoTotal / $setup.pageSize)) + " 页", 1 /* TEXT */),
                      _createElementVNode("button", {
                        class: "btn",
                        disabled: $setup.page * $setup.pageSize >= $setup.videoTotal,
                        onClick: _cache[5] || (_cache[5] = $event => ($setup.loadVideos($setup.page + 1)))
                      }, "下一页", 8 /* PROPS */, _hoisted_53)
                    ]))
                  : _createCommentVNode("v-if", true)
              ], 64 /* STABLE_FRAGMENT */))
        ])
      ]),
      _createCommentVNode(" 添加博主弹窗 "),
      ($setup.showAddModal)
        ? (_openBlock(), _createElementBlock("div", {
            key: 0,
            class: "modal-mask",
            onClick: _withModifiers($setup.closeAddModal, ["self"])
          }, [
            _createElementVNode("div", _hoisted_54, [
              _cache[19] || (_cache[19] = _createElementVNode("div", { class: "modal-title" }, "添加博主", -1 /* CACHED */)),
              _createElementVNode("div", _hoisted_55, [
                _cache[16] || (_cache[16] = _createElementVNode("label", null, "博主昵称（必填）", -1 /* CACHED */)),
                _withDirectives(_createElementVNode("input", {
                  "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => (($setup.addForm.nickname) = $event)),
                  placeholder: "比如：阿畅聊AI",
                  class: "input",
                  onKeyup: _withKeys($setup.submitAdd, ["enter"])
                }, null, 544 /* NEED_HYDRATION, NEED_PATCH */), [
                  [_vModelText, $setup.addForm.nickname]
                ]),
                _cache[17] || (_cache[17] = _createElementVNode("div", { class: "modal-hint" }, "自动在抖音搜索该昵称，取最匹配的博主并采集其视频", -1 /* CACHED */)),
                _cache[18] || (_cache[18] = _createElementVNode("label", null, "备注（可选）", -1 /* CACHED */)),
                _withDirectives(_createElementVNode("input", {
                  "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => (($setup.addForm.note) = $event)),
                  placeholder: "比如：经济学对标号",
                  class: "input"
                }, null, 512 /* NEED_PATCH */), [
                  [_vModelText, $setup.addForm.note]
                ]),
                _createElementVNode("label", null, [
                  _withDirectives(_createElementVNode("input", {
                    type: "checkbox",
                    "onUpdate:modelValue": _cache[8] || (_cache[8] = $event => (($setup.addForm.do_initial_sync) = $event))
                  }, null, 512 /* NEED_PATCH */), [
                    [_vModelCheckbox, $setup.addForm.do_initial_sync]
                  ]),
                  _cache[15] || (_cache[15] = _createTextVNode(" 添加后立即拉取最近视频（建议勾上） ", -1 /* CACHED */))
                ])
              ]),
              _createElementVNode("div", _hoisted_56, [
                _createElementVNode("button", {
                  class: "btn",
                  onClick: $setup.closeAddModal,
                  disabled: $setup.adding
                }, "取消", 8 /* PROPS */, _hoisted_57),
                _createElementVNode("button", {
                  class: "btn primary",
                  disabled: $setup.adding || !$setup.addForm.nickname,
                  onClick: $setup.submitAdd
                }, _toDisplayString($setup.adding ? '搜索并添加中...' : '确认添加'), 9 /* TEXT, PROPS */, _hoisted_58)
              ]),
              ($setup.addError)
                ? (_openBlock(), _createElementBlock("div", _hoisted_59, _toDisplayString($setup.addError), 1 /* TEXT */))
                : _createCommentVNode("v-if", true)
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 文字稿查看弹窗 "),
      ($setup.transcriptModal.open)
        ? (_openBlock(), _createElementBlock("div", {
            key: 1,
            class: "modal-mask",
            onClick: _cache[10] || (_cache[10] = _withModifiers($event => ($setup.transcriptModal.open = false), ["self"]))
          }, [
            _createElementVNode("div", _hoisted_60, [
              _createElementVNode("div", _hoisted_61, [
                _cache[20] || (_cache[20] = _createTextVNode(" 文字稿 ", -1 /* CACHED */)),
                _createElementVNode("span", _hoisted_62, "— " + _toDisplayString($setup.transcriptModal.desc), 1 /* TEXT */)
              ]),
              _createElementVNode("div", _hoisted_63, [
                _createElementVNode("pre", _hoisted_64, _toDisplayString($setup.transcriptModal.text || '(空)'), 1 /* TEXT */)
              ]),
              _createElementVNode("div", _hoisted_65, [
                _createElementVNode("button", {
                  class: "btn",
                  onClick: $setup.copyTranscript
                }, "复制全文"),
                _createElementVNode("button", {
                  class: "btn primary",
                  onClick: _cache[9] || (_cache[9] = $event => ($setup.transcriptModal.open = false))
                }, "关闭")
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true)
    ])
  ], 64 /* STABLE_FRAGMENT */))
}

import "/src/views/CreatorMonitor.vue?vue&type=style&index=0&scoped=1d05471c&lang.css"

_sfc_main.__hmrId = "1d05471c"
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
export default /*#__PURE__*/_export_sfc(_sfc_main, [['render',_sfc_render],['__scopeId',"data-v-1d05471c"],['__file',"C:/WucaiMedia/client/src/views/CreatorMonitor.vue"]])
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6W10sInNvdXJjZXMiOlsiQ3JlYXRvck1vbml0b3IudnVlIl0sInNvdXJjZXNDb250ZW50IjpbIjx0ZW1wbGF0ZT5cbiAgPEFwcEhlYWRlciAvPlxuICA8ZGl2IGNsYXNzPVwiY3JlYXRvci1tb25pdG9yXCI+XG4gICAgPGRpdiBjbGFzcz1cInBhZ2UtaGVhZGVyXCI+XG4gICAgICA8ZGl2IGNsYXNzPVwiaGVhZGVyLWxlZnRcIj5cbiAgICAgICAgPGgyIGNsYXNzPVwicGFnZS10aXRsZVwiPuWvueagh+WNmuS4u+ebkeaOpzwvaDI+XG4gICAgICAgIDxzcGFuIGNsYXNzPVwic3ViLXRpdGxlXCI+6YeH6ZuG5oyH5a6a5Y2a5Li755qE5oqW6Z+z6KeG6aKR77yM6Ieq5Yqo55Sf5oiQ5paH5a2X56i/55So5LqO5pS55YaZ5Y+C6ICDPC9zcGFuPlxuICAgICAgPC9kaXY+XG4gICAgICA8ZGl2IGNsYXNzPVwiaGVhZGVyLXJpZ2h0XCI+XG4gICAgICAgIDxidXR0b24gY2xhc3M9XCJidG4gcHJpbWFyeVwiIEBjbGljaz1cInNob3dBZGRNb2RhbCA9IHRydWVcIj4rIOa3u+WKoOWNmuS4uzwvYnV0dG9uPlxuICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuXCIgOmRpc2FibGVkPVwic3luY2luZ0FsbFwiIEBjbGljaz1cInN5bmNBbGxcIj5cbiAgICAgICAgICB7eyBzeW5jaW5nQWxsID8gJ+WQjOatpeS4rS4uLicgOiAn5ZCM5q2l5YWo6YOoJyB9fVxuICAgICAgICA8L2J1dHRvbj5cbiAgICAgIDwvZGl2PlxuICAgIDwvZGl2PlxuXG4gICAgPGRpdiBjbGFzcz1cIm1haW4tbGF5b3V0XCI+XG4gICAgICA8IS0tIOW3puagj++8muWNmuS4u+WIl+ihqCAtLT5cbiAgICAgIDxhc2lkZSBjbGFzcz1cImNyZWF0b3JzLXBhbmVcIj5cbiAgICAgICAgPGRpdiBjbGFzcz1cInBhbmUtdGl0bGVcIj7orqLpmIXljZrkuLsgKHt7IHN1YnNjcmlwdGlvbnMubGVuZ3RoIH19KTwvZGl2PlxuICAgICAgICA8ZGl2IHYtaWY9XCJsb2FkaW5nU3Vic1wiIGNsYXNzPVwiZW1wdHlcIj7liqDovb3kuK0uLi48L2Rpdj5cbiAgICAgICAgPGRpdiB2LWVsc2UtaWY9XCJzdWJzY3JpcHRpb25zLmxlbmd0aCA9PT0gMFwiIGNsYXNzPVwiZW1wdHlcIj7ov5jmsqHmnInorqLpmIXvvIzngrnkuIrmlrlcIisg5re75Yqg5Y2a5Li7XCI8L2Rpdj5cbiAgICAgICAgPGRpdlxuICAgICAgICAgIHYtZm9yPVwic3ViIGluIHN1YnNjcmlwdGlvbnNcIlxuICAgICAgICAgIDprZXk9XCJzdWIuaWRcIlxuICAgICAgICAgIGNsYXNzPVwiY3JlYXRvci1pdGVtXCJcbiAgICAgICAgICA6Y2xhc3M9XCJ7IGFjdGl2ZTogY3VycmVudFN1YklkID09PSBzdWIuaWQsIGluYWN0aXZlOiAhc3ViLmlzX2FjdGl2ZSB9XCJcbiAgICAgICAgICBAY2xpY2s9XCJzZWxlY3RTdWIoc3ViKVwiXG4gICAgICAgID5cbiAgICAgICAgICA8aW1nIHYtaWY9XCJzdWIuYXZhdGFyX3VybFwiIDpzcmM9XCJzdWIuYXZhdGFyX3VybFwiIGNsYXNzPVwiYXZhdGFyXCIgLz5cbiAgICAgICAgICA8ZGl2IHYtZWxzZSBjbGFzcz1cImF2YXRhciBhdmF0YXItcGxhY2Vob2xkZXJcIj57eyAoc3ViLm5pY2tuYW1lIHx8ICc/Jykuc2xpY2UoMCwgMSkgfX08L2Rpdj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiY3JlYXRvci1pbmZvXCI+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwiY3JlYXRvci1uYW1lXCI+XG4gICAgICAgICAgICAgIHt7IHN1Yi5uaWNrbmFtZSB8fCAnKOacquaLieWIsOaYteensCknIH19XG4gICAgICAgICAgICAgIDxzcGFuIHYtaWY9XCIhc3ViLmlzX2FjdGl2ZVwiIGNsYXNzPVwidGFnLWRpc2FibGVkXCI+5bey5YGc55SoPC9zcGFuPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwiY3JlYXRvci1tZXRhXCI+XG4gICAgICAgICAgICAgIOW3sumHh+mbhiB7eyBzdWIudmlkZW9fY291bnQgfHwgMCB9fSDmnaFcbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiB2LWlmPVwic3ViLmxhc3Rfc3luY19hdFwiIGNsYXNzPVwiY3JlYXRvci1tZXRhXCI+XG4gICAgICAgICAgICAgIOS4iuasoeWQjOatpToge3sgZm9ybWF0VGltZShzdWIubGFzdF9zeW5jX2F0KSB9fVxuICAgICAgICAgICAgICA8c3BhbiB2LWlmPVwic3ViLmxhc3Rfc3luY19zdGF0dXMgPT09ICdmYWlsZWQnXCIgY2xhc3M9XCJ0YWctZmFpbGVkXCI+5aSx6LSlPC9zcGFuPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IHYtaWY9XCJzdWIubm90ZVwiIGNsYXNzPVwiY3JlYXRvci1ub3RlXCI+e3sgc3ViLm5vdGUgfX08L2Rpdj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiY3JlYXRvci1hY3Rpb25zXCIgQGNsaWNrLnN0b3A+XG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiaWNvbi1idG5cIiA6ZGlzYWJsZWQ9XCJzeW5jaW5nSWQgPT09IHN1Yi5pZFwiIEBjbGljaz1cInN5bmNPbmUoc3ViKVwiIHRpdGxlPVwi5ZCM5q2lXCI+XG4gICAgICAgICAgICAgIHt7IHN5bmNpbmdJZCA9PT0gc3ViLmlkID8gJy4uLicgOiAn4oa7JyB9fVxuICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiaWNvbi1idG5cIiBAY2xpY2s9XCJ0b2dnbGVBY3RpdmUoc3ViKVwiIDp0aXRsZT1cInN1Yi5pc19hY3RpdmUgPyAn5YGc55SoJyA6ICflkK/nlKgnXCI+XG4gICAgICAgICAgICAgIHt7IHN1Yi5pc19hY3RpdmUgPyAn4o+4JyA6ICfilrYnIH19XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2FzaWRlPlxuXG4gICAgICA8IS0tIOWPs+agj++8muinhumikeWIl+ihqCAtLT5cbiAgICAgIDxzZWN0aW9uIGNsYXNzPVwidmlkZW9zLXBhbmVcIj5cbiAgICAgICAgPGRpdiB2LWlmPVwiIWN1cnJlbnRTdWJJZFwiIGNsYXNzPVwiZW1wdHktbWFpblwiPuS7juW3puS+p+mAieS4gOS4quWNmuS4u+afpeeci+WFtuinhumikTwvZGl2PlxuXG4gICAgICAgIDx0ZW1wbGF0ZSB2LWVsc2U+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cInZpZGVvcy10b29sYmFyXCI+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwidG9vbGJhci1sZWZ0XCI+XG4gICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwiZmlsdGVyLWxhYmVsXCI+562b6YCJOjwvc3Bhbj5cbiAgICAgICAgICAgICAgPHNlbGVjdCB2LW1vZGVsPVwiZmlsdGVyVHJhbnNjcmlwdFN0YXR1c1wiIEBjaGFuZ2U9XCJsb2FkVmlkZW9zKDEpXCI+XG4gICAgICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cIlwiPuWFqOmDqOeKtuaAgTwvb3B0aW9uPlxuICAgICAgICAgICAgICAgIDxvcHRpb24gdmFsdWU9XCJwZW5kaW5nXCI+5b6F55Sf5oiQ5paH5a2X56i/PC9vcHRpb24+XG4gICAgICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cInByb2Nlc3NpbmdcIj7nlJ/miJDkuK08L29wdGlvbj5cbiAgICAgICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwiZG9uZVwiPuW3suWujOaIkDwvb3B0aW9uPlxuICAgICAgICAgICAgICAgIDxvcHRpb24gdmFsdWU9XCJmYWlsZWRcIj7lpLHotKU8L29wdGlvbj5cbiAgICAgICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwic2tpcHBlZFwiPuW3sui3s+i/hzwvb3B0aW9uPlxuICAgICAgICAgICAgICA8L3NlbGVjdD5cbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJtdXRlZFwiPuWFsSB7eyB2aWRlb1RvdGFsIH19IOadoTwvc3Bhbj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInRvb2xiYXItcmlnaHRcIj5cbiAgICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImJ0blwiIDpkaXNhYmxlZD1cImJhdGNoVHJhbnNjcmliaW5nXCIgQGNsaWNrPVwiYmF0Y2hUcmFuc2NyaWJlXCI+XG4gICAgICAgICAgICAgICAge3sgYmF0Y2hUcmFuc2NyaWJpbmcgPyAn55Sf5oiQ5LitLi4uJyA6ICfmibnph4/nlJ/miJDmloflrZfnqL8oNeadoSknIH19XG4gICAgICAgICAgICAgIDwvYnV0dG9uPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPC9kaXY+XG5cbiAgICAgICAgICA8ZGl2IHYtaWY9XCJsb2FkaW5nVmlkZW9zXCIgY2xhc3M9XCJlbXB0eS1tYWluXCI+5Yqg6L295LitLi4uPC9kaXY+XG4gICAgICAgICAgPGRpdiB2LWVsc2UtaWY9XCJ2aWRlb3MubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJlbXB0eS1tYWluXCI+5pqC5peg6KeG6aKRPC9kaXY+XG5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwidmlkZW8tZ3JpZFwiPlxuICAgICAgICAgICAgPGRpdiB2LWZvcj1cInYgaW4gdmlkZW9zXCIgOmtleT1cInYuaWRcIiBjbGFzcz1cInZpZGVvLWNhcmRcIj5cbiAgICAgICAgICAgICAgPGEgOmhyZWY9XCJ2LnNoYXJlX3VybFwiIHRhcmdldD1cIl9ibGFua1wiIGNsYXNzPVwidmlkZW8tY292ZXItbGlua1wiIHRpdGxlPVwi5Zyo5oqW6Z+z5omT5byA5Y6f6KeG6aKRXCI+XG4gICAgICAgICAgICAgICAgPGltZyB2LWlmPVwidi5jb3Zlcl91cmxcIiA6c3JjPVwidi5jb3Zlcl91cmxcIiBjbGFzcz1cInZpZGVvLWNvdmVyXCIgLz5cbiAgICAgICAgICAgICAgICA8ZGl2IHYtZWxzZSBjbGFzcz1cInZpZGVvLWNvdmVyIHZpZGVvLWNvdmVyLXBsYWNlaG9sZGVyXCI+5peg5bCB6Z2iPC9kaXY+XG4gICAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJkdXJhdGlvbi1iYWRnZVwiPnt7IGZvcm1hdER1cmF0aW9uKHYuZHVyYXRpb25fc2VjKSB9fTwvc3Bhbj5cbiAgICAgICAgICAgICAgPC9hPlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwidmlkZW8tYm9keVwiPlxuICAgICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJ2aWRlby1kZXNjXCIgOnRpdGxlPVwidi5kZXNjXCI+e3sgdi5kZXNjIHx8ICco5peg5paH5qGIKScgfX08L2Rpdj5cbiAgICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwidmlkZW8tbWV0YVwiPlxuICAgICAgICAgICAgICAgICAgPHNwYW4+e3sgZm9ybWF0VGltZSh2LnB1Ymxpc2hlZF9hdCkgfX08L3NwYW4+XG4gICAgICAgICAgICAgICAgICA8c3BhbiB2LWlmPVwidi5kdXJhdGlvbl9zZWNcIiBjbGFzcz1cImRvdFwiPsK3PC9zcGFuPlxuICAgICAgICAgICAgICAgICAgPHNwYW4gdi1pZj1cInYuZHVyYXRpb25fc2VjXCI+5pe26ZW/IHt7IGZvcm1hdER1cmF0aW9uKHYuZHVyYXRpb25fc2VjKSB9fTwvc3Bhbj5cbiAgICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwiZG90XCI+wrc8L3NwYW4+XG4gICAgICAgICAgICAgICAgICA8YSA6aHJlZj1cInYuc2hhcmVfdXJsXCIgdGFyZ2V0PVwiX2JsYW5rXCIgY2xhc3M9XCJvcGVuLWxpbmtcIj7nnIvljp/op4bpopEg4oaXPC9hPlxuICAgICAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJ2aWRlby1zdGF0c1wiPlxuICAgICAgICAgICAgICAgICAgPHNwYW4gdGl0bGU9XCLngrnotZ5cIj7imaUge3sgZm9ybWF0TnVtYmVyKHYuZGlnZ19jb3VudCkgfX08L3NwYW4+XG4gICAgICAgICAgICAgICAgICA8c3BhbiB0aXRsZT1cIuivhOiuulwiPvCfkqwge3sgZm9ybWF0TnVtYmVyKHYuY29tbWVudF9jb3VudCkgfX08L3NwYW4+XG4gICAgICAgICAgICAgICAgICA8c3BhbiB0aXRsZT1cIuaUtuiXj1wiPuKtkCB7eyBmb3JtYXROdW1iZXIodi5jb2xsZWN0X2NvdW50KSB9fTwvc3Bhbj5cbiAgICAgICAgICAgICAgICAgIDxzcGFuIHRpdGxlPVwi5YiG5LqrXCI+4oaXIHt7IGZvcm1hdE51bWJlcih2LnNoYXJlX2NvdW50KSB9fTwvc3Bhbj5cbiAgICAgICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwidmlkZW8tdHJhbnNjcmlwdFwiPlxuICAgICAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJ0cmFuc2NyaXB0LXN0YXR1c1wiIDpjbGFzcz1cImBzdGF0dXMtJHt2LnRyYW5zY3JpcHRfc3RhdHVzfWBcIj5cbiAgICAgICAgICAgICAgICAgICAge3sgdHJhbnNjcmlwdFN0YXR1c0xhYmVsKHYudHJhbnNjcmlwdF9zdGF0dXMpIH19XG4gICAgICAgICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICAgICAgICA8YnV0dG9uIHYtaWY9XCJ2LnRyYW5zY3JpcHRfc3RhdHVzID09PSAnZG9uZSdcIiBjbGFzcz1cImxpbmstYnRuXCIgQGNsaWNrPVwidmlld1RyYW5zY3JpcHQodilcIj5cbiAgICAgICAgICAgICAgICAgICAg5p+l55yL5paH5a2X56i/ICh7eyB2LnRyYW5zY3JpcHRfY2hhcnMgfX0g5a2XKVxuICAgICAgICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgICAgICAgICA8YnV0dG9uXG4gICAgICAgICAgICAgICAgICAgIHYtZWxzZVxuICAgICAgICAgICAgICAgICAgICBjbGFzcz1cImxpbmstYnRuXCJcbiAgICAgICAgICAgICAgICAgICAgOmRpc2FibGVkPVwidHJhbnNjcmliaW5nSWQgPT09IHYuaWQgfHwgdi50cmFuc2NyaXB0X3N0YXR1cyA9PT0gJ3Byb2Nlc3NpbmcnXCJcbiAgICAgICAgICAgICAgICAgICAgQGNsaWNrPVwidHJhbnNjcmliZU9uZSh2KVwiXG4gICAgICAgICAgICAgICAgICA+XG4gICAgICAgICAgICAgICAgICAgIHt7IHRyYW5zY3JpYmluZ0lkID09PSB2LmlkID8gJ+eUn+aIkOS4rS4uLicgOiAn55Sf5oiQ5paH5a2X56i/JyB9fVxuICAgICAgICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgICAgICAgICA8c3BhbiB2LWlmPVwidi50cmFuc2NyaXB0X2Vycm9yXCIgY2xhc3M9XCJlcnJvci1tc2dcIiA6dGl0bGU9XCJ2LnRyYW5zY3JpcHRfZXJyb3JcIj5cbiAgICAgICAgICAgICAgICAgICAg6ZSZ6K+vOiB7eyB0cnVuY2F0ZSh2LnRyYW5zY3JpcHRfZXJyb3IsIDQwKSB9fVxuICAgICAgICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvZGl2PlxuXG4gICAgICAgICAgPGRpdiBjbGFzcz1cInBhZ2luYXRpb25cIiB2LWlmPVwidmlkZW9Ub3RhbCA+IHBhZ2VTaXplXCI+XG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuXCIgOmRpc2FibGVkPVwicGFnZSA8PSAxXCIgQGNsaWNrPVwibG9hZFZpZGVvcyhwYWdlIC0gMSlcIj7kuIrkuIDpobU8L2J1dHRvbj5cbiAgICAgICAgICAgIDxzcGFuPuesrCB7eyBwYWdlIH19IC8ge3sgTWF0aC5jZWlsKHZpZGVvVG90YWwgLyBwYWdlU2l6ZSkgfX0g6aG1PC9zcGFuPlxuICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImJ0blwiIDpkaXNhYmxlZD1cInBhZ2UgKiBwYWdlU2l6ZSA+PSB2aWRlb1RvdGFsXCIgQGNsaWNrPVwibG9hZFZpZGVvcyhwYWdlICsgMSlcIj7kuIvkuIDpobU8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC90ZW1wbGF0ZT5cbiAgICAgIDwvc2VjdGlvbj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g5re75Yqg5Y2a5Li75by556qXIC0tPlxuICAgIDxkaXYgdi1pZj1cInNob3dBZGRNb2RhbFwiIGNsYXNzPVwibW9kYWwtbWFza1wiIEBjbGljay5zZWxmPVwiY2xvc2VBZGRNb2RhbFwiPlxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsXCI+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC10aXRsZVwiPua3u+WKoOWNmuS4uzwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtYm9keVwiPlxuICAgICAgICAgIDxsYWJlbD7ljZrkuLvmmLXnp7DvvIjlv4XloavvvIk8L2xhYmVsPlxuICAgICAgICAgIDxpbnB1dFxuICAgICAgICAgICAgdi1tb2RlbD1cImFkZEZvcm0ubmlja25hbWVcIlxuICAgICAgICAgICAgcGxhY2Vob2xkZXI9XCLmr5TlpoLvvJrpmL/nlYXogYpBSVwiXG4gICAgICAgICAgICBjbGFzcz1cImlucHV0XCJcbiAgICAgICAgICAgIEBrZXl1cC5lbnRlcj1cInN1Ym1pdEFkZFwiXG4gICAgICAgICAgLz5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtaGludFwiPuiHquWKqOWcqOaKlumfs+aQnOe0ouivpeaYteensO+8jOWPluacgOWMuemFjeeahOWNmuS4u+W5tumHh+mbhuWFtuinhumikTwvZGl2PlxuICAgICAgICAgIDxsYWJlbD7lpIfms6jvvIjlj6/pgInvvIk8L2xhYmVsPlxuICAgICAgICAgIDxpbnB1dCB2LW1vZGVsPVwiYWRkRm9ybS5ub3RlXCIgcGxhY2Vob2xkZXI9XCLmr5TlpoLvvJrnu4/mtY7lrablr7nmoIflj7dcIiBjbGFzcz1cImlucHV0XCIgLz5cbiAgICAgICAgICA8bGFiZWw+XG4gICAgICAgICAgICA8aW5wdXQgdHlwZT1cImNoZWNrYm94XCIgdi1tb2RlbD1cImFkZEZvcm0uZG9faW5pdGlhbF9zeW5jXCIgLz5cbiAgICAgICAgICAgIOa3u+WKoOWQjueri+WNs+aLieWPluacgOi/keinhumike+8iOW7uuiuruWLvuS4iu+8iVxuICAgICAgICAgIDwvbGFiZWw+XG4gICAgICAgIDwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtZm9vdGVyXCI+XG4gICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImJ0blwiIEBjbGljaz1cImNsb3NlQWRkTW9kYWxcIiA6ZGlzYWJsZWQ9XCJhZGRpbmdcIj7lj5bmtog8L2J1dHRvbj5cbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuIHByaW1hcnlcIiA6ZGlzYWJsZWQ9XCJhZGRpbmcgfHwgIWFkZEZvcm0ubmlja25hbWVcIiBAY2xpY2s9XCJzdWJtaXRBZGRcIj5cbiAgICAgICAgICAgIHt7IGFkZGluZyA/ICfmkJzntKLlubbmt7vliqDkuK0uLi4nIDogJ+ehruiupOa3u+WKoCcgfX1cbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgdi1pZj1cImFkZEVycm9yXCIgY2xhc3M9XCJtb2RhbC1lcnJvclwiPnt7IGFkZEVycm9yIH19PC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g5paH5a2X56i/5p+l55yL5by556qXIC0tPlxuICAgIDxkaXYgdi1pZj1cInRyYW5zY3JpcHRNb2RhbC5vcGVuXCIgY2xhc3M9XCJtb2RhbC1tYXNrXCIgQGNsaWNrLnNlbGY9XCJ0cmFuc2NyaXB0TW9kYWwub3BlbiA9IGZhbHNlXCI+XG4gICAgICA8ZGl2IGNsYXNzPVwibW9kYWwgbW9kYWwtd2lkZVwiPlxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtdGl0bGVcIj5cbiAgICAgICAgICDmloflrZfnqL9cbiAgICAgICAgICA8c3BhbiBjbGFzcz1cIm11dGVkXCI+4oCUIHt7IHRyYW5zY3JpcHRNb2RhbC5kZXNjIH19PC9zcGFuPlxuICAgICAgICA8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWJvZHlcIj5cbiAgICAgICAgICA8cHJlIGNsYXNzPVwidHJhbnNjcmlwdC10ZXh0XCI+e3sgdHJhbnNjcmlwdE1vZGFsLnRleHQgfHwgJyjnqbopJyB9fTwvcHJlPlxuICAgICAgICA8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWZvb3RlclwiPlxuICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJidG5cIiBAY2xpY2s9XCJjb3B5VHJhbnNjcmlwdFwiPuWkjeWItuWFqOaWhzwvYnV0dG9uPlxuICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJidG4gcHJpbWFyeVwiIEBjbGljaz1cInRyYW5zY3JpcHRNb2RhbC5vcGVuID0gZmFsc2VcIj7lhbPpl608L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cbiAgPC9kaXY+XG48L3RlbXBsYXRlPlxuXG48c2NyaXB0IHNldHVwPlxuaW1wb3J0IHsgcmVmLCByZWFjdGl2ZSwgb25Nb3VudGVkIH0gZnJvbSAndnVlJ1xuaW1wb3J0IEFwcEhlYWRlciBmcm9tICcuLi9jb21wb25lbnRzL0FwcEhlYWRlci52dWUnXG5pbXBvcnQgeyBBUElfQkFTRV9VUkwgfSBmcm9tICcuLi91dGlscy9hcGlDb25maWcnXG5cbmNvbnN0IHN1YnNjcmlwdGlvbnMgPSByZWYoW10pXG5jb25zdCBsb2FkaW5nU3VicyA9IHJlZihmYWxzZSlcbmNvbnN0IGN1cnJlbnRTdWJJZCA9IHJlZihudWxsKVxuXG5jb25zdCB2aWRlb3MgPSByZWYoW10pXG5jb25zdCB2aWRlb1RvdGFsID0gcmVmKDApXG5jb25zdCBsb2FkaW5nVmlkZW9zID0gcmVmKGZhbHNlKVxuY29uc3QgcGFnZSA9IHJlZigxKVxuY29uc3QgcGFnZVNpemUgPSByZWYoMjApXG5jb25zdCBmaWx0ZXJUcmFuc2NyaXB0U3RhdHVzID0gcmVmKCcnKVxuXG5jb25zdCBzeW5jaW5nQWxsID0gcmVmKGZhbHNlKVxuY29uc3Qgc3luY2luZ0lkID0gcmVmKG51bGwpXG5jb25zdCB0cmFuc2NyaWJpbmdJZCA9IHJlZihudWxsKVxuY29uc3QgYmF0Y2hUcmFuc2NyaWJpbmcgPSByZWYoZmFsc2UpXG5cbmNvbnN0IHNob3dBZGRNb2RhbCA9IHJlZihmYWxzZSlcbmNvbnN0IGFkZGluZyA9IHJlZihmYWxzZSlcbmNvbnN0IGFkZEVycm9yID0gcmVmKCcnKVxuY29uc3QgYWRkRm9ybSA9IHJlYWN0aXZlKHsgbmlja25hbWU6ICcnLCBub3RlOiAnJywgZG9faW5pdGlhbF9zeW5jOiB0cnVlIH0pXG5cbmNvbnN0IHRyYW5zY3JpcHRNb2RhbCA9IHJlYWN0aXZlKHsgb3BlbjogZmFsc2UsIHRleHQ6ICcnLCBkZXNjOiAnJyB9KVxuXG4vLyA9PT09PT09PT09PT0g5bel5YW3ID09PT09PT09PT09PVxuZnVuY3Rpb24gZm9ybWF0TnVtYmVyKG4pIHtcbiAgaWYgKG4gPT0gbnVsbCkgcmV0dXJuICcwJ1xuICBpZiAobiA+PSAxMDAwMDAwMDApIHJldHVybiAobiAvIDEwMDAwMDAwMCkudG9GaXhlZCgxKSArICfkur8nXG4gIGlmIChuID49IDEwMDAwKSByZXR1cm4gKG4gLyAxMDAwMCkudG9GaXhlZCgxKSArICd3J1xuICByZXR1cm4gU3RyaW5nKG4pXG59XG5cbmZ1bmN0aW9uIGZvcm1hdFRpbWUodCkge1xuICBpZiAoIXQpIHJldHVybiAnLSdcbiAgY29uc3QgZCA9IG5ldyBEYXRlKHQpXG4gIGNvbnN0IHkgPSBkLmdldEZ1bGxZZWFyKClcbiAgY29uc3QgbSA9IFN0cmluZyhkLmdldE1vbnRoKCkgKyAxKS5wYWRTdGFydCgyLCAnMCcpXG4gIGNvbnN0IGRheSA9IFN0cmluZyhkLmdldERhdGUoKSkucGFkU3RhcnQoMiwgJzAnKVxuICBjb25zdCBoaCA9IFN0cmluZyhkLmdldEhvdXJzKCkpLnBhZFN0YXJ0KDIsICcwJylcbiAgY29uc3QgbW0gPSBTdHJpbmcoZC5nZXRNaW51dGVzKCkpLnBhZFN0YXJ0KDIsICcwJylcbiAgcmV0dXJuIGAke3l9LSR7bX0tJHtkYXl9ICR7aGh9OiR7bW19YFxufVxuXG5mdW5jdGlvbiBmb3JtYXREdXJhdGlvbihzZWMpIHtcbiAgaWYgKCFzZWMpIHJldHVybiAnJ1xuICBjb25zdCBtID0gTWF0aC5mbG9vcihzZWMgLyA2MClcbiAgY29uc3QgcyA9IHNlYyAlIDYwXG4gIHJldHVybiBgJHttfToke1N0cmluZyhzKS5wYWRTdGFydCgyLCAnMCcpfWBcbn1cblxuZnVuY3Rpb24gdHJ1bmNhdGUocywgbikge1xuICBpZiAoIXMpIHJldHVybiAnJ1xuICByZXR1cm4gcy5sZW5ndGggPiBuID8gcy5zbGljZSgwLCBuKSArICcuLi4nIDogc1xufVxuXG5mdW5jdGlvbiB0cmFuc2NyaXB0U3RhdHVzTGFiZWwocykge1xuICByZXR1cm4gKHtcbiAgICBwZW5kaW5nOiAn5pyq55Sf5oiQJyxcbiAgICBwcm9jZXNzaW5nOiAn55Sf5oiQ5LitJyxcbiAgICBkb25lOiAn5bey5a6M5oiQJyxcbiAgICBmYWlsZWQ6ICflpLHotKUnLFxuICAgIHNraXBwZWQ6ICflt7Lot7Pov4cnLFxuICB9KVtzXSB8fCBzXG59XG5cbi8vID09PT09PT09PT09PSDnvZHnu5wgPT09PT09PT09PT09XG5hc3luYyBmdW5jdGlvbiBhcGkocGF0aCwgb3B0aW9ucyA9IHt9KSB7XG4gIGNvbnN0IHVybCA9IGAke0FQSV9CQVNFX1VSTH0ke3BhdGh9YFxuICBjb25zdCBvcHRzID0geyBoZWFkZXJzOiB7ICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicgfSwgLi4ub3B0aW9ucyB9XG4gIGNvbnN0IHJlc3AgPSBhd2FpdCBmZXRjaCh1cmwsIG9wdHMpXG4gIGNvbnN0IGpzb24gPSBhd2FpdCByZXNwLmpzb24oKVxuICBpZiAoanNvbi5jb2RlICE9PSAyMDAgJiYganNvbi5jb2RlICE9PSAwKSB7XG4gICAgdGhyb3cgbmV3IEVycm9yKGpzb24ubXNnIHx8IGBIVFRQICR7cmVzcC5zdGF0dXN9YClcbiAgfVxuICByZXR1cm4ganNvbi5kYXRhXG59XG5cbi8vID09PT09PT09PT09PSDliqDovb0gPT09PT09PT09PT09XG5hc3luYyBmdW5jdGlvbiBsb2FkU3VicygpIHtcbiAgbG9hZGluZ1N1YnMudmFsdWUgPSB0cnVlXG4gIHRyeSB7XG4gICAgc3Vic2NyaXB0aW9ucy52YWx1ZSA9IGF3YWl0IGFwaSgnL2FwaS92aWRlb3MvY3JlYXRvcnMnKSB8fCBbXVxuICAgIGlmICghY3VycmVudFN1YklkLnZhbHVlICYmIHN1YnNjcmlwdGlvbnMudmFsdWUubGVuZ3RoID4gMCkge1xuICAgICAgY29uc3QgZmlyc3RBY3RpdmUgPSBzdWJzY3JpcHRpb25zLnZhbHVlLmZpbmQocyA9PiBzLmlzX2FjdGl2ZSkgfHwgc3Vic2NyaXB0aW9ucy52YWx1ZVswXVxuICAgICAgc2VsZWN0U3ViKGZpcnN0QWN0aXZlKVxuICAgIH1cbiAgfSBjYXRjaCAoZSkge1xuICAgIGFsZXJ0KCfliqDovb3ljZrkuLvliJfooajlpLHotKU6ICcgKyBlLm1lc3NhZ2UpXG4gIH0gZmluYWxseSB7XG4gICAgbG9hZGluZ1N1YnMudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbmZ1bmN0aW9uIHNlbGVjdFN1YihzdWIpIHtcbiAgY3VycmVudFN1YklkLnZhbHVlID0gc3ViLmlkXG4gIHBhZ2UudmFsdWUgPSAxXG4gIGxvYWRWaWRlb3MoMSlcbn1cblxuYXN5bmMgZnVuY3Rpb24gbG9hZFZpZGVvcyhwKSB7XG4gIGlmICghY3VycmVudFN1YklkLnZhbHVlKSByZXR1cm5cbiAgcGFnZS52YWx1ZSA9IHBcbiAgbG9hZGluZ1ZpZGVvcy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCBwYXJhbXMgPSBuZXcgVVJMU2VhcmNoUGFyYW1zKHtcbiAgICAgIHN1YnNjcmlwdGlvbl9pZDogU3RyaW5nKGN1cnJlbnRTdWJJZC52YWx1ZSksXG4gICAgICBwYWdlOiBTdHJpbmcocCksXG4gICAgICBwYWdlX3NpemU6IFN0cmluZyhwYWdlU2l6ZS52YWx1ZSksXG4gICAgfSlcbiAgICBpZiAoZmlsdGVyVHJhbnNjcmlwdFN0YXR1cy52YWx1ZSkgcGFyYW1zLmFwcGVuZCgndHJhbnNjcmlwdF9zdGF0dXMnLCBmaWx0ZXJUcmFuc2NyaXB0U3RhdHVzLnZhbHVlKVxuICAgIGNvbnN0IGRhdGEgPSBhd2FpdCBhcGkoYC9hcGkvdmlkZW9zL2NyZWF0b3JfdmlkZW9zPyR7cGFyYW1zfWApXG4gICAgdmlkZW9zLnZhbHVlID0gZGF0YS5pdGVtcyB8fCBbXVxuICAgIHZpZGVvVG90YWwudmFsdWUgPSBkYXRhLnRvdGFsIHx8IDBcbiAgfSBjYXRjaCAoZSkge1xuICAgIGFsZXJ0KCfliqDovb3op4bpopHlpLHotKU6ICcgKyBlLm1lc3NhZ2UpXG4gIH0gZmluYWxseSB7XG4gICAgbG9hZGluZ1ZpZGVvcy52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cblxuLy8gPT09PT09PT09PT09IOaTjeS9nCA9PT09PT09PT09PT1cbmFzeW5jIGZ1bmN0aW9uIHN5bmNPbmUoc3ViKSB7XG4gIHN5bmNpbmdJZC52YWx1ZSA9IHN1Yi5pZFxuICB0cnkge1xuICAgIGF3YWl0IGFwaShgL2FwaS92aWRlb3MvY3JlYXRvcnMvJHtzdWIuaWR9L3N5bmNgLCB7XG4gICAgICBtZXRob2Q6ICdQT1NUJyxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHsgbWF4X3BhZ2VzOiAzIH0pLFxuICAgIH0pXG4gICAgYXdhaXQgbG9hZFN1YnMoKVxuICAgIGlmIChjdXJyZW50U3ViSWQudmFsdWUgPT09IHN1Yi5pZCkgYXdhaXQgbG9hZFZpZGVvcygxKVxuICB9IGNhdGNoIChlKSB7XG4gICAgYWxlcnQoJ+WQjOatpeWksei0pTogJyArIGUubWVzc2FnZSlcbiAgfSBmaW5hbGx5IHtcbiAgICBzeW5jaW5nSWQudmFsdWUgPSBudWxsXG4gIH1cbn1cblxuYXN5bmMgZnVuY3Rpb24gc3luY0FsbCgpIHtcbiAgaWYgKCFjb25maXJtKCflkIzmraXlhajpg6jlkK/nlKjnmoTljZrkuLvvvJ/mr4/kuKrljZrkuLvkuYvpl7TkvJrpl7TpmpQgOCDnp5InKSkgcmV0dXJuXG4gIHN5bmNpbmdBbGwudmFsdWUgPSB0cnVlXG4gIHRyeSB7XG4gICAgYXdhaXQgYXBpKCcvYXBpL3ZpZGVvcy9jcmVhdG9ycy9zeW5jX2FsbCcsIHtcbiAgICAgIG1ldGhvZDogJ1BPU1QnLFxuICAgICAgYm9keTogSlNPTi5zdHJpbmdpZnkoeyBtYXhfcGFnZXM6IDMgfSksXG4gICAgfSlcbiAgICBhd2FpdCBsb2FkU3VicygpXG4gICAgaWYgKGN1cnJlbnRTdWJJZC52YWx1ZSkgYXdhaXQgbG9hZFZpZGVvcygxKVxuICB9IGNhdGNoIChlKSB7XG4gICAgYWxlcnQoJ+WQjOatpeWksei0pTogJyArIGUubWVzc2FnZSlcbiAgfSBmaW5hbGx5IHtcbiAgICBzeW5jaW5nQWxsLnZhbHVlID0gZmFsc2VcbiAgfVxufVxuXG5hc3luYyBmdW5jdGlvbiB0b2dnbGVBY3RpdmUoc3ViKSB7XG4gIHRyeSB7XG4gICAgYXdhaXQgYXBpKGAvYXBpL3ZpZGVvcy9jcmVhdG9ycy8ke3N1Yi5pZH1gLCB7XG4gICAgICBtZXRob2Q6ICdQQVRDSCcsXG4gICAgICBib2R5OiBKU09OLnN0cmluZ2lmeSh7IGlzX2FjdGl2ZTogIXN1Yi5pc19hY3RpdmUgfSksXG4gICAgfSlcbiAgICBhd2FpdCBsb2FkU3VicygpXG4gIH0gY2F0Y2ggKGUpIHtcbiAgICBhbGVydCgn5pON5L2c5aSx6LSlOiAnICsgZS5tZXNzYWdlKVxuICB9XG59XG5cbmFzeW5jIGZ1bmN0aW9uIHN1Ym1pdEFkZCgpIHtcbiAgYWRkaW5nLnZhbHVlID0gdHJ1ZVxuICBhZGRFcnJvci52YWx1ZSA9ICcnXG4gIHRyeSB7XG4gICAgYXdhaXQgYXBpKCcvYXBpL3ZpZGVvcy9jcmVhdG9ycycsIHtcbiAgICAgIG1ldGhvZDogJ1BPU1QnLFxuICAgICAgYm9keTogSlNPTi5zdHJpbmdpZnkoe1xuICAgICAgICBuaWNrbmFtZTogYWRkRm9ybS5uaWNrbmFtZS50cmltKCksXG4gICAgICAgIG5vdGU6IGFkZEZvcm0ubm90ZS50cmltKCkgfHwgbnVsbCxcbiAgICAgICAgZG9faW5pdGlhbF9zeW5jOiBhZGRGb3JtLmRvX2luaXRpYWxfc3luYyxcbiAgICAgIH0pLFxuICAgIH0pXG4gICAgY2xvc2VBZGRNb2RhbCgpXG4gICAgYXdhaXQgbG9hZFN1YnMoKVxuICB9IGNhdGNoIChlKSB7XG4gICAgYWRkRXJyb3IudmFsdWUgPSBlLm1lc3NhZ2VcbiAgfSBmaW5hbGx5IHtcbiAgICBhZGRpbmcudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbmZ1bmN0aW9uIGNsb3NlQWRkTW9kYWwoKSB7XG4gIHNob3dBZGRNb2RhbC52YWx1ZSA9IGZhbHNlXG4gIGFkZEVycm9yLnZhbHVlID0gJydcbiAgYWRkRm9ybS5uaWNrbmFtZSA9ICcnXG4gIGFkZEZvcm0ubm90ZSA9ICcnXG4gIGFkZEZvcm0uZG9faW5pdGlhbF9zeW5jID0gdHJ1ZVxufVxuXG5hc3luYyBmdW5jdGlvbiB0cmFuc2NyaWJlT25lKHYpIHtcbiAgdHJhbnNjcmliaW5nSWQudmFsdWUgPSB2LmlkXG4gIHRyeSB7XG4gICAgYXdhaXQgYXBpKGAvYXBpL3ZpZGVvcy9jcmVhdG9yX3ZpZGVvcy8ke3YuaWR9L3RyYW5zY3JpYmVgLCB7IG1ldGhvZDogJ1BPU1QnIH0pXG4gICAgYXdhaXQgbG9hZFZpZGVvcyhwYWdlLnZhbHVlKVxuICB9IGNhdGNoIChlKSB7XG4gICAgYWxlcnQoJ+eUn+aIkOWksei0pTogJyArIGUubWVzc2FnZSlcbiAgICBhd2FpdCBsb2FkVmlkZW9zKHBhZ2UudmFsdWUpXG4gIH0gZmluYWxseSB7XG4gICAgdHJhbnNjcmliaW5nSWQudmFsdWUgPSBudWxsXG4gIH1cbn1cblxuYXN5bmMgZnVuY3Rpb24gYmF0Y2hUcmFuc2NyaWJlKCkge1xuICBiYXRjaFRyYW5zY3JpYmluZy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBhd2FpdCBhcGkoJy9hcGkvdmlkZW9zL2NyZWF0b3JfdmlkZW9zL3RyYW5zY3JpYmVfYmF0Y2gnLCB7XG4gICAgICBtZXRob2Q6ICdQT1NUJyxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHsgbGltaXQ6IDUgfSksXG4gICAgfSlcbiAgICBhd2FpdCBsb2FkVmlkZW9zKHBhZ2UudmFsdWUpXG4gIH0gY2F0Y2ggKGUpIHtcbiAgICBhbGVydCgn5om56YeP55Sf5oiQ5aSx6LSlOiAnICsgZS5tZXNzYWdlKVxuICB9IGZpbmFsbHkge1xuICAgIGJhdGNoVHJhbnNjcmliaW5nLnZhbHVlID0gZmFsc2VcbiAgfVxufVxuXG5hc3luYyBmdW5jdGlvbiB2aWV3VHJhbnNjcmlwdCh2KSB7XG4gIHRyeSB7XG4gICAgY29uc3QgZGF0YSA9IGF3YWl0IGFwaShgL2FwaS92aWRlb3MvY3JlYXRvcl92aWRlb3MvJHt2LmlkfWApXG4gICAgdHJhbnNjcmlwdE1vZGFsLnRleHQgPSBkYXRhLnRyYW5zY3JpcHRfdGV4dCB8fCAnKOacrOWcsOaWh+S7tuivu+WPluWksei0pSknXG4gICAgdHJhbnNjcmlwdE1vZGFsLmRlc2MgPSAodi5kZXNjIHx8ICcnKS5zbGljZSgwLCA2MClcbiAgICB0cmFuc2NyaXB0TW9kYWwub3BlbiA9IHRydWVcbiAgfSBjYXRjaCAoZSkge1xuICAgIGFsZXJ0KCfliqDovb3mloflrZfnqL/lpLHotKU6ICcgKyBlLm1lc3NhZ2UpXG4gIH1cbn1cblxuZnVuY3Rpb24gY29weVRyYW5zY3JpcHQoKSB7XG4gIG5hdmlnYXRvci5jbGlwYm9hcmQud3JpdGVUZXh0KHRyYW5zY3JpcHRNb2RhbC50ZXh0IHx8ICcnKS50aGVuKFxuICAgICgpID0+IGFsZXJ0KCflt7LlpI3liLbliLDliarotLTmnb8nKSxcbiAgICAoKSA9PiBhbGVydCgn5aSN5Yi25aSx6LSlJylcbiAgKVxufVxuXG5vbk1vdW50ZWQobG9hZFN1YnMpXG48L3NjcmlwdD5cblxuPHN0eWxlIHNjb3BlZD5cbi5jcmVhdG9yLW1vbml0b3Ige1xuICBwYWRkaW5nOiAxNnB4IDI0cHg7XG4gIGJhY2tncm91bmQ6ICNmNWY2ZmE7XG4gIG1pbi1oZWlnaHQ6IGNhbGMoMTAwdmggLSA2MHB4KTtcbn1cbi5wYWdlLWhlYWRlciB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGp1c3RpZnktY29udGVudDogc3BhY2UtYmV0d2VlbjtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgbWFyZ2luLWJvdHRvbTogMTZweDtcbn1cbi5wYWdlLXRpdGxlIHtcbiAgbWFyZ2luOiAwO1xuICBmb250LXNpemU6IDIwcHg7XG4gIGZvbnQtd2VpZ2h0OiA2MDA7XG59XG4uc3ViLXRpdGxlIHtcbiAgbWFyZ2luLWxlZnQ6IDEycHg7XG4gIGZvbnQtc2l6ZTogMTNweDtcbiAgY29sb3I6ICM4ODg7XG59XG4uaGVhZGVyLXJpZ2h0IHtcbiAgZGlzcGxheTogZmxleDtcbiAgZ2FwOiA4cHg7XG59XG4uYnRuIHtcbiAgcGFkZGluZzogNnB4IDE0cHg7XG4gIGZvbnQtc2l6ZTogMTNweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2Q5ZDlkOTtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xufVxuLmJ0bjpob3Zlcjpub3QoOmRpc2FibGVkKSB7XG4gIGJvcmRlci1jb2xvcjogIzViOGNmZjtcbiAgY29sb3I6ICM1YjhjZmY7XG59XG4uYnRuOmRpc2FibGVkIHtcbiAgb3BhY2l0eTogMC41O1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xufVxuLmJ0bi5wcmltYXJ5IHtcbiAgYmFja2dyb3VuZDogIzViOGNmZjtcbiAgY29sb3I6ICNmZmY7XG4gIGJvcmRlci1jb2xvcjogIzViOGNmZjtcbn1cbi5idG4ucHJpbWFyeTpob3Zlcjpub3QoOmRpc2FibGVkKSB7XG4gIGJhY2tncm91bmQ6ICMzZjcyZjA7XG4gIGNvbG9yOiAjZmZmO1xufVxuXG4ubWFpbi1sYXlvdXQge1xuICBkaXNwbGF5OiBncmlkO1xuICBncmlkLXRlbXBsYXRlLWNvbHVtbnM6IDMyMHB4IDFmcjtcbiAgZ2FwOiAxNnB4O1xufVxuXG4vKiDlt6bmoI8gKi9cbi5jcmVhdG9ycy1wYW5lIHtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xuICBwYWRkaW5nOiAxMnB4O1xuICBoZWlnaHQ6IGNhbGMoMTAwdmggLSAxNjBweCk7XG4gIG92ZXJmbG93LXk6IGF1dG87XG59XG4ucGFuZS10aXRsZSB7XG4gIGZvbnQtc2l6ZTogMTNweDtcbiAgY29sb3I6ICM2NjY7XG4gIG1hcmdpbi1ib3R0b206IDhweDtcbiAgcGFkZGluZzogMCA0cHg7XG59XG4uY3JlYXRvci1pdGVtIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGZsZXgtc3RhcnQ7XG4gIGdhcDogMTBweDtcbiAgcGFkZGluZzogMTBweDtcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIG1hcmdpbi1ib3R0b206IDRweDtcbiAgYm9yZGVyOiAxcHggc29saWQgdHJhbnNwYXJlbnQ7XG59XG4uY3JlYXRvci1pdGVtOmhvdmVyIHtcbiAgYmFja2dyb3VuZDogI2YwZjRmZjtcbn1cbi5jcmVhdG9yLWl0ZW0uYWN0aXZlIHtcbiAgYmFja2dyb3VuZDogI2U4ZjBmZjtcbiAgYm9yZGVyLWNvbG9yOiAjNWI4Y2ZmO1xufVxuLmNyZWF0b3ItaXRlbS5pbmFjdGl2ZSB7XG4gIG9wYWNpdHk6IDAuNTU7XG59XG4uYXZhdGFyIHtcbiAgd2lkdGg6IDQwcHg7XG4gIGhlaWdodDogNDBweDtcbiAgYm9yZGVyLXJhZGl1czogNTAlO1xuICBmbGV4LXNocmluazogMDtcbiAgb2JqZWN0LWZpdDogY292ZXI7XG59XG4uYXZhdGFyLXBsYWNlaG9sZGVyIHtcbiAgYmFja2dyb3VuZDogI2Q5ZTFmZjtcbiAgY29sb3I6ICM1YjhjZmY7XG4gIGZvbnQtd2VpZ2h0OiA2MDA7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xuICBmb250LXNpemU6IDE2cHg7XG59XG4uY3JlYXRvci1pbmZvIHtcbiAgZmxleDogMTtcbiAgbWluLXdpZHRoOiAwO1xufVxuLmNyZWF0b3ItbmFtZSB7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgZm9udC13ZWlnaHQ6IDUwMDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7XG59XG4uY3JlYXRvci1tZXRhIHtcbiAgZm9udC1zaXplOiAxMnB4O1xuICBjb2xvcjogIzg4ODtcbiAgbWFyZ2luLXRvcDogMnB4O1xufVxuLmNyZWF0b3Itbm90ZSB7XG4gIGZvbnQtc2l6ZTogMTJweDtcbiAgY29sb3I6ICM1YjhjZmY7XG4gIG1hcmdpbi10b3A6IDJweDtcbiAgZm9udC1zdHlsZTogaXRhbGljO1xufVxuLmNyZWF0b3ItYWN0aW9ucyB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG4gIGdhcDogNHB4O1xufVxuLmljb24tYnRuIHtcbiAgd2lkdGg6IDI0cHg7XG4gIGhlaWdodDogMjRweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2RkZDtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTJweDtcbn1cbi5pY29uLWJ0bjpob3Zlcjpub3QoOmRpc2FibGVkKSB7XG4gIGJvcmRlci1jb2xvcjogIzViOGNmZjtcbiAgY29sb3I6ICM1YjhjZmY7XG59XG4udGFnLWRpc2FibGVkIHtcbiAgZm9udC1zaXplOiAxMHB4O1xuICBiYWNrZ3JvdW5kOiAjZjBmMGYwO1xuICBjb2xvcjogIzg4ODtcbiAgcGFkZGluZzogMXB4IDZweDtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBtYXJnaW4tbGVmdDogNHB4O1xufVxuLnRhZy1mYWlsZWQge1xuICBmb250LXNpemU6IDEwcHg7XG4gIGNvbG9yOiAjZDk1MzRmO1xuICBtYXJnaW4tbGVmdDogNHB4O1xufVxuXG4vKiDlj7PmoI8gKi9cbi52aWRlb3MtcGFuZSB7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgcGFkZGluZzogMTZweDtcbiAgbWluLWhlaWdodDogY2FsYygxMDB2aCAtIDE2MHB4KTtcbn1cbi5lbXB0eSB7XG4gIHBhZGRpbmc6IDI0cHggMTJweDtcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xuICBjb2xvcjogIzk5OTtcbiAgZm9udC1zaXplOiAxM3B4O1xufVxuLmVtcHR5LW1haW4ge1xuICBwYWRkaW5nOiA4MHB4IDEycHg7XG4gIHRleHQtYWxpZ246IGNlbnRlcjtcbiAgY29sb3I6ICM5OTk7XG59XG4udmlkZW9zLXRvb2xiYXIge1xuICBkaXNwbGF5OiBmbGV4O1xuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIG1hcmdpbi1ib3R0b206IDEycHg7XG4gIGZsZXgtd3JhcDogd3JhcDtcbiAgZ2FwOiA4cHg7XG59XG4udG9vbGJhci1sZWZ0IHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA4cHg7XG59XG4uZmlsdGVyLWxhYmVsIHtcbiAgZm9udC1zaXplOiAxM3B4O1xuICBjb2xvcjogIzY2Njtcbn1cbi5tdXRlZCB7XG4gIGNvbG9yOiAjOTk5O1xuICBmb250LXNpemU6IDEycHg7XG59XG5zZWxlY3Qge1xuICBwYWRkaW5nOiA0cHggOHB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDlkOWQ5O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG59XG5cbi52aWRlby1ncmlkIHtcbiAgZGlzcGxheTogZ3JpZDtcbiAgZ3JpZC10ZW1wbGF0ZS1jb2x1bW5zOiByZXBlYXQoYXV0by1maWxsLCBtaW5tYXgoMzIwcHgsIDFmcikpO1xuICBnYXA6IDEycHg7XG59XG4udmlkZW8tY2FyZCB7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlZWU7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgZGlzcGxheTogZmxleDtcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcbn1cbi52aWRlby1jb3Zlci1saW5rIHtcbiAgcG9zaXRpb246IHJlbGF0aXZlO1xuICBkaXNwbGF5OiBibG9jaztcbiAgd2lkdGg6IDEwMCU7XG4gIHBhZGRpbmctdG9wOiA1Ni4yNSU7XG4gIGJhY2tncm91bmQ6ICMwMDA7XG59XG4udmlkZW8tY292ZXIge1xuICBwb3NpdGlvbjogYWJzb2x1dGU7XG4gIGluc2V0OiAwO1xuICB3aWR0aDogMTAwJTtcbiAgaGVpZ2h0OiAxMDAlO1xuICBvYmplY3QtZml0OiBjb3Zlcjtcbn1cbi52aWRlby1jb3Zlci1wbGFjZWhvbGRlciB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xuICBjb2xvcjogIzg4ODtcbiAgYmFja2dyb3VuZDogI2Y1ZjVmNTtcbn1cbi5kdXJhdGlvbi1iYWRnZSB7XG4gIHBvc2l0aW9uOiBhYnNvbHV0ZTtcbiAgcmlnaHQ6IDZweDtcbiAgYm90dG9tOiA2cHg7XG4gIGJhY2tncm91bmQ6IHJnYmEoMCwgMCwgMCwgMC42KTtcbiAgY29sb3I6ICNmZmY7XG4gIHBhZGRpbmc6IDFweCA2cHg7XG4gIGJvcmRlci1yYWRpdXM6IDNweDtcbiAgZm9udC1zaXplOiAxMXB4O1xufVxuLnZpZGVvLWJvZHkge1xuICBwYWRkaW5nOiAxMHB4IDEycHg7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XG4gIGdhcDogNnB4O1xufVxuLnZpZGVvLWRlc2Mge1xuICBmb250LXNpemU6IDEzcHg7XG4gIGxpbmUtaGVpZ2h0OiAxLjQ7XG4gIGNvbG9yOiAjMzMzO1xuICBkaXNwbGF5OiAtd2Via2l0LWJveDtcbiAgLXdlYmtpdC1saW5lLWNsYW1wOiAyO1xuICAtd2Via2l0LWJveC1vcmllbnQ6IHZlcnRpY2FsO1xuICBvdmVyZmxvdzogaGlkZGVuO1xufVxuLnZpZGVvLW1ldGEge1xuICBmb250LXNpemU6IDExcHg7XG4gIGNvbG9yOiAjODg4O1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDRweDtcbiAgZmxleC13cmFwOiB3cmFwO1xufVxuLnZpZGVvLW1ldGEgLmRvdCB7XG4gIGNvbG9yOiAjY2NjO1xufVxuLm9wZW4tbGluayB7XG4gIGNvbG9yOiAjNWI4Y2ZmO1xuICB0ZXh0LWRlY29yYXRpb246IG5vbmU7XG59XG4ub3Blbi1saW5rOmhvdmVyIHtcbiAgdGV4dC1kZWNvcmF0aW9uOiB1bmRlcmxpbmU7XG59XG4udmlkZW8tc3RhdHMge1xuICBkaXNwbGF5OiBmbGV4O1xuICBnYXA6IDEwcHg7XG4gIGZvbnQtc2l6ZTogMTJweDtcbiAgY29sb3I6ICM2NjY7XG4gIGZsZXgtd3JhcDogd3JhcDtcbn1cbi52aWRlby10cmFuc2NyaXB0IHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA4cHg7XG4gIHBhZGRpbmctdG9wOiA2cHg7XG4gIGJvcmRlci10b3A6IDFweCBkYXNoZWQgI2VlZTtcbiAgZmxleC13cmFwOiB3cmFwO1xuICBmb250LXNpemU6IDEycHg7XG59XG4udHJhbnNjcmlwdC1zdGF0dXMge1xuICBwYWRkaW5nOiAxcHggNnB4O1xuICBib3JkZXItcmFkaXVzOiAzcHg7XG4gIGZvbnQtc2l6ZTogMTFweDtcbn1cbi5zdGF0dXMtcGVuZGluZyB7IGJhY2tncm91bmQ6ICNmMGYwZjA7IGNvbG9yOiAjNjY2OyB9XG4uc3RhdHVzLXByb2Nlc3NpbmcgeyBiYWNrZ3JvdW5kOiAjZmZmM2NkOyBjb2xvcjogIzg1NjQwNDsgfVxuLnN0YXR1cy1kb25lIHsgYmFja2dyb3VuZDogI2Q0ZWRkYTsgY29sb3I6ICMxNTU3MjQ7IH1cbi5zdGF0dXMtZmFpbGVkIHsgYmFja2dyb3VuZDogI2Y4ZDdkYTsgY29sb3I6ICM3MjFjMjQ7IH1cbi5zdGF0dXMtc2tpcHBlZCB7IGJhY2tncm91bmQ6ICNlMmUzZTU7IGNvbG9yOiAjNTU1OyB9XG4ubGluay1idG4ge1xuICBiYWNrZ3JvdW5kOiBub25lO1xuICBib3JkZXI6IG5vbmU7XG4gIGNvbG9yOiAjNWI4Y2ZmO1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTJweDtcbiAgcGFkZGluZzogMDtcbn1cbi5saW5rLWJ0bjpkaXNhYmxlZCB7XG4gIG9wYWNpdHk6IDAuNTtcbiAgY3Vyc29yOiBub3QtYWxsb3dlZDtcbn1cbi5lcnJvci1tc2cge1xuICBjb2xvcjogI2Q5NTM0ZjtcbiAgZm9udC1zaXplOiAxMXB4O1xufVxuXG4ucGFnaW5hdGlvbiB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDEycHg7XG4gIG1hcmdpbi10b3A6IDE2cHg7XG59XG5cbi8qIE1vZGFsICovXG4ubW9kYWwtbWFzayB7XG4gIHBvc2l0aW9uOiBmaXhlZDtcbiAgaW5zZXQ6IDA7XG4gIGJhY2tncm91bmQ6IHJnYmEoMCwgMCwgMCwgMC40KTtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XG4gIHotaW5kZXg6IDk5OTtcbn1cbi5tb2RhbCB7XG4gIGJhY2tncm91bmQ6ICNmZmY7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgd2lkdGg6IDQ4MHB4O1xuICBtYXgtd2lkdGg6IDkwdnc7XG4gIHBhZGRpbmc6IDIwcHg7XG4gIGJveC1zaGFkb3c6IDAgOHB4IDI0cHggcmdiYSgwLCAwLCAwLCAwLjE1KTtcbn1cbi5tb2RhbC13aWRlIHtcbiAgd2lkdGg6IDcyMHB4O1xuICBtYXgtaGVpZ2h0OiA4MHZoO1xuICBkaXNwbGF5OiBmbGV4O1xuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xufVxuLm1vZGFsLXRpdGxlIHtcbiAgZm9udC1zaXplOiAxNnB4O1xuICBmb250LXdlaWdodDogNjAwO1xuICBtYXJnaW4tYm90dG9tOiAxNnB4O1xufVxuLm1vZGFsLWJvZHkge1xuICBkaXNwbGF5OiBmbGV4O1xuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICBnYXA6IDhweDtcbiAgbWFyZ2luLWJvdHRvbTogMTZweDtcbiAgb3ZlcmZsb3cteTogYXV0bztcbn1cbi5tb2RhbC1ib2R5IGxhYmVsIHtcbiAgZm9udC1zaXplOiAxM3B4O1xuICBjb2xvcjogIzY2NjtcbiAgbWFyZ2luLXRvcDogNnB4O1xufVxuLm1vZGFsLWhpbnQge1xuICBmb250LXNpemU6IDEycHg7XG4gIGNvbG9yOiAjOTk5O1xuICBtYXJnaW4tdG9wOiAycHg7XG59XG4uaW5wdXQge1xuICBwYWRkaW5nOiA2cHggMTBweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2Q5ZDlkOTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXNpemU6IDEzcHg7XG59XG4uaW5wdXQ6Zm9jdXMge1xuICBvdXRsaW5lOiBub25lO1xuICBib3JkZXItY29sb3I6ICM1YjhjZmY7XG59XG4ubW9kYWwtZm9vdGVyIHtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBmbGV4LWVuZDtcbiAgZ2FwOiA4cHg7XG59XG4ubW9kYWwtZXJyb3Ige1xuICBtYXJnaW4tdG9wOiA4cHg7XG4gIGNvbG9yOiAjZDk1MzRmO1xuICBmb250LXNpemU6IDEycHg7XG59XG4udHJhbnNjcmlwdC10ZXh0IHtcbiAgZm9udC1mYW1pbHk6IGluaGVyaXQ7XG4gIHdoaXRlLXNwYWNlOiBwcmUtd3JhcDtcbiAgd29yZC1icmVhazogYnJlYWstd29yZDtcbiAgZm9udC1zaXplOiAxM3B4O1xuICBsaW5lLWhlaWdodDogMS43O1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xuICBwYWRkaW5nOiAxMnB4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIG1heC1oZWlnaHQ6IDYwdmg7XG4gIG92ZXJmbG93LXk6IGF1dG87XG59XG48L3N0eWxlPlxuIl0sIm1hcHBpbmdzIjoiQUE0TEEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOzs7Ozs7OztBQUVoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRTdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRXJDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUUxRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRXBFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25ELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0Qzs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUM7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQ7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakI7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9ELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2Q7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9COztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxD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