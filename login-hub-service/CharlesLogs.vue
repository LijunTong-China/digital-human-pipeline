import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/views/CharlesLogs.vue");import { ref, computed, onMounted, onUnmounted, watch } from "/node_modules/.vite/deps/vue.js?v=93b042e3"
import { useRouter } from "/node_modules/.vite/deps/vue-router.js?v=93b042e3"
import { API_BASE_URL } from "/src/utils/apiConfig.js"
import AppHeader from "/src/components/AppHeader.vue"


const _sfc_main = {
  __name: 'CharlesLogs',
  setup(__props, { expose: __expose }) {
  __expose();

const router = useRouter()
const logs = ref([])
const logLoading = ref(false)
const autoRefresh = ref(false)
const logContent = ref(null)
const logContentPreview = ref(null)
const logContentFull = ref(null)
const logInfo = ref(null)
let refreshTimer = null

// 日期相关
const todayDate = ref(new Date().toISOString().split('T')[0])  // YYYY-MM-DD格式
const selectedDate = ref(todayDate.value)  // 默认选择今天

// 工作汇报
const dailyReport = ref(null)
const reportLoading = ref(false)

// 工作定义
const workDefinition = ref(null)
const workDefinitionLoading = ref(false)

// 模态框状态
const showDefinitionModal = ref(false)
const showLogsModal = ref(false)

// Charles 状态
const charlesStatus = ref(null)
const statusShownAlert = ref(false)

const statusClass = computed(() => {
  if (!charlesStatus.value) return 'status-unknown'
  const status = charlesStatus.value.status
  if (status === 'working') return 'status-working'
  if (status === 'dead') return 'status-dead'
  return 'status-unknown'
})

const statusText = computed(() => {
  if (!charlesStatus.value) return '未知'
  const status = charlesStatus.value.status
  if (status === 'working') return '运行中'
  if (status === 'dead') return '已停止'
  return '未知'
})

const showStatusDetail = () => {
  if (!charlesStatus.value) {
    alert('无法获取状态信息')
    return
  }
  const s = charlesStatus.value
  let msg = `状态: ${statusText.value}\n`
  if (s.start_time) msg += `启动时间: ${s.start_time}\n`
  if (s.last_update_time) msg += `最后心跳: ${s.last_update_time}\n`
  if (s.end_time) msg += `结束时间: ${s.end_time}\n`
  if (s.error_message) msg += `错误信息: ${s.error_message}\n`
  if (s.pid) msg += `进程ID: ${s.pid}\n`
  if (s.message) msg += `说明: ${s.message}\n`
  alert(msg)
}

const fetchCharlesStatus = async () => {
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/status`)
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        charlesStatus.value = result.data
        if (result.data.status === 'dead' && !statusShownAlert.value) {
          statusShownAlert.value = true
          const errorMsg = result.data.error_message ? `\n错误信息: ${result.data.error_message}` : ''
          alert(`Charles 已停止运行！${errorMsg}\n\n请检查并重新启动 Charles。`)
        }
      }
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

const logText = computed(() => {
  return logs.value.join('\n')
})

// 预览模式的日志文本（只显示最后200行）
const logTextPreview = computed(() => {
  if (logs.value.length <= 200) {
    return logs.value.join('\n')
  }
  return logs.value.slice(-200).join('\n')
})

// 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
const formatDateForApi = (dateStr) => {
  if (!dateStr) return null
  return dateStr.replace(/-/g, '')
}

// 格式化显示日期
const formatDisplayDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  return `${year}年${month}月${day}日`
}

// 获取日志
const fetchLogs = async (showLoading = true) => {
  // 只有在需要显示loading时才设置loading状态，避免不必要的闪动
  if (showLoading) {
    logLoading.value = true
  }
  try {
    const apiUrl = API_BASE_URL
    const dateParam = formatDateForApi(selectedDate.value)
    const url = `${apiUrl}/api/zhihu/logs?lines=1000&tail=true${dateParam ? `&date=${dateParam}` : ''}`
    const response = await fetch(url)
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        // 直接更新数据，避免先清空再设置导致的闪动
        const newLogs = result.data.logs || []
        const newLogInfo = {
          total_lines: result.data.total_lines || 0,
          returned_lines: result.data.returned_lines || 0,
          file_exists: result.data.file_exists !== false,
          log_path: result.data.log_path || '',
          date: result.data.date || formatDateForApi(selectedDate.value),
          available_dates: result.data.available_dates || []
        }
        
        // 批量更新，减少重新渲染次数
        logs.value = newLogs
        logInfo.value = newLogInfo
        
        // 滚动到底部（预览区域）
        if (logContentPreview.value) {
          setTimeout(() => {
            logContentPreview.value.scrollTop = logContentPreview.value.scrollHeight
          }, 100)
        }
      } else {
        console.error('获取日志失败:', result.msg || result.message)
        logs.value = []
        logInfo.value = {
          total_lines: 0,
          returned_lines: 0,
          file_exists: false,
          log_path: '',
          date: formatDateForApi(selectedDate.value),
          available_dates: result.data?.available_dates || []
        }
      }
    } else {
      console.error('API 请求失败:', response.status)
      logs.value = []
    }
  } catch (error) {
    console.error('获取日志出错:', error)
    logs.value = []
  } finally {
    if (showLoading) {
      logLoading.value = false
    }
  }
}

// 日期变化处理（只刷新日志）
const onDateChange = () => {
  // 停止自动刷新（切换日期时）
  autoRefresh.value = false
  fetchLogs()
}

// 刷新日志数据
const refreshLogs = () => {
  fetchLogs()
}

// 打开工作定义模态框时滚动到底部
watch(showDefinitionModal, (show) => {
  if (show && workDefinition.value) {
    setTimeout(() => {
      const modalBody = document.querySelector('.definition-content-full')
      if (modalBody) {
        modalBody.scrollTop = 0
      }
    }, 100)
  }
})

// 打开日志模态框时滚动到底部
watch(showLogsModal, (show) => {
  if (show && logContentFull.value) {
    setTimeout(() => {
      logContentFull.value.scrollTop = logContentFull.value.scrollHeight
    }, 100)
  }
})

// 获取工作汇报
const fetchDailyReport = async () => {
  reportLoading.value = true
  try {
    const apiUrl = API_BASE_URL
    const dateParam = formatDateForApi(selectedDate.value)
    const response = await fetch(`${apiUrl}/api/zhihu/daily-report?date=${dateParam}`)
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        dailyReport.value = result.data
      } else {
        console.error('获取工作汇报失败:', result.msg || result.message)
        dailyReport.value = null
      }
    } else {
      console.error('API 请求失败:', response.status)
      dailyReport.value = null
    }
  } catch (error) {
    console.error('获取工作汇报出错:', error)
    dailyReport.value = null
  } finally {
    reportLoading.value = false
  }
}

// 获取工作定义
const fetchWorkDefinition = async () => {
  workDefinitionLoading.value = true
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/work-definition`)
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        workDefinition.value = result.data?.content || ''
      } else {
        console.error('获取工作定义失败:', result.msg || result.message)
        workDefinition.value = null
      }
    } else {
      console.error('API 请求失败:', response.status)
      workDefinition.value = null
    }
  } catch (error) {
    console.error('获取工作定义出错:', error)
    workDefinition.value = null
  } finally {
    workDefinitionLoading.value = false
  }
}

// 格式化工作定义内容（将文本转换为HTML）
const formatWorkDefinition = (text) => {
  if (!text) return ''
  
  // 将文本按行分割
  const lines = text.split('\n')
  let html = ''
  let inList = false
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    
    if (!line) {
      if (inList) {
        html += '</ol>'
        inList = false
      }
      html += '<br>'
      continue
    }
    
    // 检查是否是标题
    if (line.includes('工作定义') || line.includes('工作流程') || line.includes('人工操作')) {
      if (inList) {
        html += '</ol>'
        inList = false
      }
      html += `<h4>${line}</h4>`
    }
    // 检查是否是列表项（以数字开头）
    else if (/^\d+\./.test(line)) {
      if (!inList) {
        html += '<ol>'
        inList = true
      }
      // 提取数字和内容
      const match = line.match(/^(\d+)\.\s*(.+)/)
      if (match) {
        const content = match[2]
        // 检查是否有冒号分隔的标题和描述
        if (content.includes('：')) {
          const [title, desc] = content.split('：', 2)
          html += `<li><strong>${title}</strong>：${desc}</li>`
        } else {
          html += `<li>${content}</li>`
        }
      }
    }
    // 检查是否是列表项（以-开头）
    else if (line.startsWith('-')) {
      if (!inList) {
        html += '<ul>'
        inList = true
      }
      html += `<li>${line.substring(1).trim()}</li>`
    }
    // 普通文本
    else {
      if (inList) {
        html += '</ol>'
        inList = false
      }
      html += `<p>${line}</p>`
    }
  }
  
  if (inList) {
    html += '</ol>'
  }
  
  return html
}

// 监听自动刷新（静默刷新，不显示loading）
watch(autoRefresh, (auto) => {
  if (auto) {
    fetchLogs(false) // 自动刷新时不显示loading，避免闪动
    refreshTimer = setInterval(() => {
      fetchLogs(false) // 静默刷新
    }, 5000)
  } else {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }
})

onMounted(() => {
  fetchLogs()
  fetchDailyReport()
  fetchWorkDefinition()
  fetchCharlesStatus()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

const __returned__ = { router, logs, logLoading, autoRefresh, logContent, logContentPreview, logContentFull, logInfo, get refreshTimer() { return refreshTimer }, set refreshTimer(v) { refreshTimer = v }, todayDate, selectedDate, dailyReport, reportLoading, workDefinition, workDefinitionLoading, showDefinitionModal, showLogsModal, charlesStatus, statusShownAlert, statusClass, statusText, showStatusDetail, fetchCharlesStatus, logText, logTextPreview, formatDateForApi, formatDisplayDate, fetchLogs, onDateChange, refreshLogs, fetchDailyReport, fetchWorkDefinition, formatWorkDefinition, ref, computed, onMounted, onUnmounted, watch, get useRouter() { return useRouter }, get API_BASE_URL() { return API_BASE_URL }, AppHeader }
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true })
return __returned__
}

}
import { createVNode as _createVNode, toDisplayString as _toDisplayString, openBlock as _openBlock, createElementBlock as _createElementBlock, createCommentVNode as _createCommentVNode, createTextVNode as _createTextVNode, createElementVNode as _createElementVNode, normalizeClass as _normalizeClass, renderList as _renderList, Fragment as _Fragment, vModelText as _vModelText, withDirectives as _withDirectives, vModelCheckbox as _vModelCheckbox, withModifiers as _withModifiers } from "/node_modules/.vite/deps/vue.js?v=93b042e3"

const _hoisted_1 = { class: "logs-page" }
const _hoisted_2 = { class: "logs-header" }
const _hoisted_3 = { class: "title-with-status" }
const _hoisted_4 = { class: "logs-title" }
const _hoisted_5 = {
  key: 0,
  class: "title-date"
}
const _hoisted_6 = { class: "status-text" }
const _hoisted_7 = { class: "report-section-full" }
const _hoisted_8 = {
  key: 0,
  class: "report-loading"
}
const _hoisted_9 = {
  key: 1,
  class: "report-dashboard"
}
const _hoisted_10 = { class: "dashboard-group" }
const _hoisted_11 = { class: "stat-row" }
const _hoisted_12 = { class: "stat-card stat-primary" }
const _hoisted_13 = { class: "stat-value" }
const _hoisted_14 = { class: "stat-card stat-primary" }
const _hoisted_15 = { class: "stat-value" }
const _hoisted_16 = { class: "stat-card stat-primary" }
const _hoisted_17 = { class: "stat-value" }
const _hoisted_18 = { class: "dashboard-group" }
const _hoisted_19 = { class: "stat-row" }
const _hoisted_20 = { class: "stat-card stat-secondary" }
const _hoisted_21 = { class: "stat-value" }
const _hoisted_22 = { class: "stat-card stat-secondary" }
const _hoisted_23 = { class: "stat-value" }
const _hoisted_24 = { class: "stat-card stat-secondary" }
const _hoisted_25 = { class: "stat-value" }
const _hoisted_26 = {
  key: 0,
  class: "dashboard-group"
}
const _hoisted_27 = { class: "source-tags" }
const _hoisted_28 = { class: "tag-name" }
const _hoisted_29 = { class: "tag-count" }
const _hoisted_30 = {
  key: 2,
  class: "report-empty"
}
const _hoisted_31 = { class: "bottom-layout" }
const _hoisted_32 = { class: "preview-panel definition-preview" }
const _hoisted_33 = { class: "preview-header" }
const _hoisted_34 = { class: "preview-content" }
const _hoisted_35 = {
  key: 0,
  class: "definition-loading"
}
const _hoisted_36 = ["innerHTML"]
const _hoisted_37 = {
  key: 2,
  class: "definition-error"
}
const _hoisted_38 = { class: "preview-panel logs-preview" }
const _hoisted_39 = { class: "preview-header" }
const _hoisted_40 = { class: "logs-header-controls" }
const _hoisted_41 = { class: "date-selector" }
const _hoisted_42 = ["max"]
const _hoisted_43 = { class: "auto-refresh-label" }
const _hoisted_44 = { class: "preview-content" }
const _hoisted_45 = {
  key: 0,
  class: "logs-info-compact"
}
const _hoisted_46 = {
  key: 0,
  class: "error-text"
}
const _hoisted_47 = {
  class: "log-content-preview",
  ref: "logContentPreview"
}
const _hoisted_48 = {
  key: 0,
  class: "log-loading"
}
const _hoisted_49 = {
  key: 1,
  class: "log-empty"
}
const _hoisted_50 = { class: "modal-header" }
const _hoisted_51 = { class: "modal-body" }
const _hoisted_52 = {
  key: 0,
  class: "definition-loading"
}
const _hoisted_53 = ["innerHTML"]
const _hoisted_54 = {
  key: 2,
  class: "definition-error"
}
const _hoisted_55 = { class: "modal-header" }
const _hoisted_56 = { class: "modal-header-right" }
const _hoisted_57 = {
  key: 0,
  class: "logs-info-modal"
}
const _hoisted_58 = { class: "modal-body" }
const _hoisted_59 = {
  class: "log-content-full",
  ref: "logContentFull"
}
const _hoisted_60 = {
  key: 0,
  class: "log-loading"
}
const _hoisted_61 = {
  key: 1,
  class: "log-empty"
}
const _hoisted_62 = {
  key: 2,
  class: "log-text-full"
}

function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createVNode($setup["AppHeader"]),
    _createElementVNode("div", _hoisted_1, [
      _createElementVNode("div", _hoisted_2, [
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("h1", _hoisted_4, [
            _cache[10] || (_cache[10] = _createTextVNode("Charles工作汇报", -1 /* CACHED */)),
            ($setup.dailyReport)
              ? (_openBlock(), _createElementBlock("span", _hoisted_5, "（" + _toDisplayString($setup.formatDisplayDate($setup.selectedDate)) + "）", 1 /* TEXT */))
              : _createCommentVNode("v-if", true)
          ]),
          _createElementVNode("div", {
            class: _normalizeClass(["status-badge", $setup.statusClass]),
            onClick: $setup.showStatusDetail
          }, [
            _cache[11] || (_cache[11] = _createElementVNode("span", { class: "status-dot" }, null, -1 /* CACHED */)),
            _createElementVNode("span", _hoisted_6, _toDisplayString($setup.statusText), 1 /* TEXT */)
          ], 2 /* CLASS */)
        ])
      ]),
      _createCommentVNode(" 工作汇报区域 "),
      _createElementVNode("div", _hoisted_7, [
        ($setup.reportLoading)
          ? (_openBlock(), _createElementBlock("div", _hoisted_8, "加载中..."))
          : ($setup.dailyReport)
            ? (_openBlock(), _createElementBlock("div", _hoisted_9, [
                _createCommentVNode(" 当日数据 "),
                _createElementVNode("div", _hoisted_10, [
                  _cache[15] || (_cache[15] = _createElementVNode("div", { class: "group-title" }, "当日工作", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_11, [
                    _createElementVNode("div", _hoisted_12, [
                      _createElementVNode("div", _hoisted_13, _toDisplayString($setup.dailyReport.summary.new_articles), 1 /* TEXT */),
                      _cache[12] || (_cache[12] = _createElementVNode("div", { class: "stat-label" }, "新增文章", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_14, [
                      _createElementVNode("div", _hoisted_15, _toDisplayString($setup.dailyReport.summary.fetched_content), 1 /* TEXT */),
                      _cache[13] || (_cache[13] = _createElementVNode("div", { class: "stat-label" }, "采集内容", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_16, [
                      _createElementVNode("div", _hoisted_17, _toDisplayString($setup.dailyReport.summary.selected), 1 /* TEXT */),
                      _cache[14] || (_cache[14] = _createElementVNode("div", { class: "stat-label" }, "标记选中", -1 /* CACHED */))
                    ])
                  ])
                ]),
                _createCommentVNode(" 累计数据 "),
                _createElementVNode("div", _hoisted_18, [
                  _cache[19] || (_cache[19] = _createElementVNode("div", { class: "group-title" }, "累计数据", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_19, [
                    _createElementVNode("div", _hoisted_20, [
                      _createElementVNode("div", _hoisted_21, _toDisplayString($setup.dailyReport.cumulative.total_articles), 1 /* TEXT */),
                      _cache[16] || (_cache[16] = _createElementVNode("div", { class: "stat-label" }, "总文章", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_22, [
                      _createElementVNode("div", _hoisted_23, _toDisplayString($setup.dailyReport.cumulative.total_with_content), 1 /* TEXT */),
                      _cache[17] || (_cache[17] = _createElementVNode("div", { class: "stat-label" }, "已采集", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_24, [
                      _createElementVNode("div", _hoisted_25, _toDisplayString($setup.dailyReport.cumulative.total_selected), 1 /* TEXT */),
                      _cache[18] || (_cache[18] = _createElementVNode("div", { class: "stat-label" }, "已选中", -1 /* CACHED */))
                    ])
                  ])
                ]),
                _createCommentVNode(" 采集来源（累计符合条件的） "),
                ($setup.dailyReport.source_stats && $setup.dailyReport.source_stats.length > 0)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_26, [
                      _cache[20] || (_cache[20] = _createElementVNode("div", { class: "group-title" }, "采集来源（符合条件）", -1 /* CACHED */)),
                      _createElementVNode("div", _hoisted_27, [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.dailyReport.source_stats, (item) => {
                          return (_openBlock(), _createElementBlock("div", {
                            key: item.source,
                            class: "source-tag"
                          }, [
                            _createElementVNode("span", _hoisted_28, _toDisplayString(item.source), 1 /* TEXT */),
                            _createElementVNode("span", _hoisted_29, _toDisplayString(item.count), 1 /* TEXT */)
                          ]))
                        }), 128 /* KEYED_FRAGMENT */))
                      ])
                    ]))
                  : _createCommentVNode("v-if", true)
              ]))
            : (_openBlock(), _createElementBlock("div", _hoisted_30, "暂无工作汇报数据"))
      ]),
      _createCommentVNode(" 底部两栏布局 "),
      _createElementVNode("div", _hoisted_31, [
        _createCommentVNode(" 左侧：工作定义（预览） "),
        _createElementVNode("div", _hoisted_32, [
          _createElementVNode("div", _hoisted_33, [
            _cache[22] || (_cache[22] = _createElementVNode("h3", null, "Charles 工作定义", -1 /* CACHED */)),
            _createElementVNode("button", {
              class: "expand-btn",
              onClick: _cache[0] || (_cache[0] = $event => ($setup.showDefinitionModal = true)),
              title: "查看全部"
            }, [...(_cache[21] || (_cache[21] = [
              _createElementVNode("svg", {
                viewBox: "0 0 24 24",
                fill: "none",
                stroke: "currentColor"
              }, [
                _createElementVNode("path", { d: "M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" })
              ], -1 /* CACHED */)
            ]))])
          ]),
          _createElementVNode("div", _hoisted_34, [
            ($setup.workDefinitionLoading)
              ? (_openBlock(), _createElementBlock("div", _hoisted_35, "加载中..."))
              : ($setup.workDefinition)
                ? (_openBlock(), _createElementBlock("div", {
                    key: 1,
                    class: "definition-content-preview",
                    innerHTML: $setup.formatWorkDefinition($setup.workDefinition)
                  }, null, 8 /* PROPS */, _hoisted_36))
                : (_openBlock(), _createElementBlock("div", _hoisted_37, "无法加载工作定义"))
          ])
        ]),
        _createCommentVNode(" 右侧：工作日志（预览） "),
        _createElementVNode("div", _hoisted_38, [
          _createElementVNode("div", _hoisted_39, [
            _cache[26] || (_cache[26] = _createElementVNode("h3", null, "工作日志", -1 /* CACHED */)),
            _createElementVNode("div", _hoisted_40, [
              _createElementVNode("div", _hoisted_41, [
                _cache[23] || (_cache[23] = _createElementVNode("label", { class: "date-label" }, "选择日期：", -1 /* CACHED */)),
                _withDirectives(_createElementVNode("input", {
                  type: "date",
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => (($setup.selectedDate) = $event)),
                  onChange: $setup.onDateChange,
                  class: "date-input",
                  max: $setup.todayDate
                }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_42), [
                  [_vModelText, $setup.selectedDate]
                ])
              ]),
              _createElementVNode("label", _hoisted_43, [
                _withDirectives(_createElementVNode("input", {
                  type: "checkbox",
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => (($setup.autoRefresh) = $event))
                }, null, 512 /* NEED_PATCH */), [
                  [_vModelCheckbox, $setup.autoRefresh]
                ]),
                _cache[24] || (_cache[24] = _createTextVNode(" 自动刷新（5秒） ", -1 /* CACHED */))
              ]),
              _createElementVNode("button", {
                class: "refresh-btn",
                onClick: $setup.refreshLogs
              }, "刷新"),
              _createElementVNode("button", {
                class: "expand-btn",
                onClick: _cache[3] || (_cache[3] = $event => ($setup.showLogsModal = true)),
                title: "查看全部"
              }, [...(_cache[25] || (_cache[25] = [
                _createElementVNode("svg", {
                  viewBox: "0 0 24 24",
                  fill: "none",
                  stroke: "currentColor"
                }, [
                  _createElementVNode("path", { d: "M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" })
                ], -1 /* CACHED */)
              ]))])
            ])
          ]),
          _createElementVNode("div", _hoisted_44, [
            ($setup.logInfo)
              ? (_openBlock(), _createElementBlock("div", _hoisted_45, [
                  _createElementVNode("span", null, "日期: " + _toDisplayString($setup.formatDisplayDate($setup.selectedDate)), 1 /* TEXT */),
                  _createElementVNode("span", null, "总行数: " + _toDisplayString($setup.logInfo.total_lines), 1 /* TEXT */),
                  (!$setup.logInfo.file_exists)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_46, "日志文件不存在"))
                    : _createCommentVNode("v-if", true)
                ]))
              : _createCommentVNode("v-if", true),
            _createElementVNode("div", _hoisted_47, [
              ($setup.logLoading && $setup.logs.length === 0)
                ? (_openBlock(), _createElementBlock("div", _hoisted_48, "加载中..."))
                : ($setup.logs.length === 0)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_49, "暂无日志"))
                  : (_openBlock(), _createElementBlock("pre", {
                      key: 2,
                      class: _normalizeClass(["log-text-preview", { 'updating': $setup.logLoading }])
                    }, _toDisplayString($setup.logTextPreview), 3 /* TEXT, CLASS */))
            ], 512 /* NEED_PATCH */)
          ])
        ])
      ]),
      _createCommentVNode(" 工作定义全屏模态框 "),
      ($setup.showDefinitionModal)
        ? (_openBlock(), _createElementBlock("div", {
            key: 0,
            class: "modal-overlay",
            onClick: _cache[6] || (_cache[6] = $event => ($setup.showDefinitionModal = false))
          }, [
            _createElementVNode("div", {
              class: "modal-content",
              onClick: _cache[5] || (_cache[5] = _withModifiers(() => {}, ["stop"]))
            }, [
              _createElementVNode("div", _hoisted_50, [
                _cache[28] || (_cache[28] = _createElementVNode("h2", null, "Charles 工作定义", -1 /* CACHED */)),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: _cache[4] || (_cache[4] = $event => ($setup.showDefinitionModal = false))
                }, [...(_cache[27] || (_cache[27] = [
                  _createElementVNode("svg", {
                    viewBox: "0 0 24 24",
                    fill: "none",
                    stroke: "currentColor"
                  }, [
                    _createElementVNode("line", {
                      x1: "18",
                      y1: "6",
                      x2: "6",
                      y2: "18"
                    }),
                    _createElementVNode("line", {
                      x1: "6",
                      y1: "6",
                      x2: "18",
                      y2: "18"
                    })
                  ], -1 /* CACHED */)
                ]))])
              ]),
              _createElementVNode("div", _hoisted_51, [
                ($setup.workDefinitionLoading)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_52, "加载中..."))
                  : ($setup.workDefinition)
                    ? (_openBlock(), _createElementBlock("div", {
                        key: 1,
                        class: "definition-content-full",
                        innerHTML: $setup.formatWorkDefinition($setup.workDefinition)
                      }, null, 8 /* PROPS */, _hoisted_53))
                    : (_openBlock(), _createElementBlock("div", _hoisted_54, "无法加载工作定义"))
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 工作日志全屏模态框 "),
      ($setup.showLogsModal)
        ? (_openBlock(), _createElementBlock("div", {
            key: 1,
            class: "modal-overlay",
            onClick: _cache[9] || (_cache[9] = $event => ($setup.showLogsModal = false))
          }, [
            _createElementVNode("div", {
              class: "modal-content modal-content-large",
              onClick: _cache[8] || (_cache[8] = _withModifiers(() => {}, ["stop"]))
            }, [
              _createElementVNode("div", _hoisted_55, [
                _cache[30] || (_cache[30] = _createElementVNode("h2", null, "工作日志", -1 /* CACHED */)),
                _createElementVNode("div", _hoisted_56, [
                  ($setup.logInfo)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_57, [
                        _createElementVNode("span", null, "日期: " + _toDisplayString($setup.formatDisplayDate($setup.selectedDate)), 1 /* TEXT */),
                        _createElementVNode("span", null, "总行数: " + _toDisplayString($setup.logInfo.total_lines), 1 /* TEXT */),
                        _createElementVNode("span", null, "显示行数: " + _toDisplayString($setup.logInfo.returned_lines), 1 /* TEXT */)
                      ]))
                    : _createCommentVNode("v-if", true),
                  _createElementVNode("button", {
                    class: "modal-close",
                    onClick: _cache[7] || (_cache[7] = $event => ($setup.showLogsModal = false))
                  }, [...(_cache[29] || (_cache[29] = [
                    _createElementVNode("svg", {
                      viewBox: "0 0 24 24",
                      fill: "none",
                      stroke: "currentColor"
                    }, [
                      _createElementVNode("line", {
                        x1: "18",
                        y1: "6",
                        x2: "6",
                        y2: "18"
                      }),
                      _createElementVNode("line", {
                        x1: "6",
                        y1: "6",
                        x2: "18",
                        y2: "18"
                      })
                    ], -1 /* CACHED */)
                  ]))])
                ])
              ]),
              _createElementVNode("div", _hoisted_58, [
                _createElementVNode("div", _hoisted_59, [
                  ($setup.logLoading)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_60, "加载中..."))
                    : ($setup.logs.length === 0)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_61, "暂无日志"))
                      : (_openBlock(), _createElementBlock("pre", _hoisted_62, _toDisplayString($setup.logText), 1 /* TEXT */))
                ], 512 /* NEED_PATCH */)
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true)
    ])
  ], 64 /* STABLE_FRAGMENT */))
}

import "/src/views/CharlesLogs.vue?vue&type=style&index=0&scoped=b99ecf82&lang.css"

_sfc_main.__hmrId = "b99ecf82"
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
export default /*#__PURE__*/_export_sfc(_sfc_main, [['render',_sfc_render],['__scopeId',"data-v-b99ecf82"],['__file',"C:/WucaiMedia/client/src/views/CharlesLogs.vue"]])
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6W10sInNvdXJjZXMiOlsiQ2hhcmxlc0xvZ3MudnVlIl0sInNvdXJjZXNDb250ZW50IjpbIjx0ZW1wbGF0ZT5cclxuICA8QXBwSGVhZGVyIC8+XHJcbiAgPGRpdiBjbGFzcz1cImxvZ3MtcGFnZVwiPlxyXG4gICAgPGRpdiBjbGFzcz1cImxvZ3MtaGVhZGVyXCI+XHJcbiAgICAgIDxkaXYgY2xhc3M9XCJ0aXRsZS13aXRoLXN0YXR1c1wiPlxyXG4gICAgICAgIDxoMSBjbGFzcz1cImxvZ3MtdGl0bGVcIj5DaGFybGVz5bel5L2c5rGH5oqlPHNwYW4gdi1pZj1cImRhaWx5UmVwb3J0XCIgY2xhc3M9XCJ0aXRsZS1kYXRlXCI+77yIe3sgZm9ybWF0RGlzcGxheURhdGUoc2VsZWN0ZWREYXRlKSB9fe+8iTwvc3Bhbj48L2gxPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0dXMtYmFkZ2VcIiA6Y2xhc3M9XCJzdGF0dXNDbGFzc1wiIEBjbGljaz1cInNob3dTdGF0dXNEZXRhaWxcIj5cclxuICAgICAgICAgIDxzcGFuIGNsYXNzPVwic3RhdHVzLWRvdFwiPjwvc3Bhbj5cclxuICAgICAgICAgIDxzcGFuIGNsYXNzPVwic3RhdHVzLXRleHRcIj57eyBzdGF0dXNUZXh0IH19PC9zcGFuPlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICA8L2Rpdj5cclxuICAgIDwvZGl2PlxyXG5cclxuICAgIDwhLS0g5bel5L2c5rGH5oql5Yy65Z+fIC0tPlxyXG4gICAgPGRpdiBjbGFzcz1cInJlcG9ydC1zZWN0aW9uLWZ1bGxcIj5cclxuICAgICAgPGRpdiB2LWlmPVwicmVwb3J0TG9hZGluZ1wiIGNsYXNzPVwicmVwb3J0LWxvYWRpbmdcIj7liqDovb3kuK0uLi48L2Rpdj5cclxuICAgICAgPGRpdiB2LWVsc2UtaWY9XCJkYWlseVJlcG9ydFwiIGNsYXNzPVwicmVwb3J0LWRhc2hib2FyZFwiPlxyXG4gICAgICAgIDwhLS0g5b2T5pel5pWw5o2uIC0tPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJkYXNoYm9hcmQtZ3JvdXBcIj5cclxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJncm91cC10aXRsZVwiPuW9k+aXpeW3peS9nDwvZGl2PlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtcm93XCI+XHJcbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWNhcmQgc3RhdC1wcmltYXJ5XCI+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtdmFsdWVcIj57eyBkYWlseVJlcG9ydC5zdW1tYXJ5Lm5ld19hcnRpY2xlcyB9fTwvZGl2PlxyXG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWxhYmVsXCI+5paw5aKe5paH56ugPC9kaXY+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkIHN0YXQtcHJpbWFyeVwiPlxyXG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LXZhbHVlXCI+e3sgZGFpbHlSZXBvcnQuc3VtbWFyeS5mZXRjaGVkX2NvbnRlbnQgfX08L2Rpdj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1sYWJlbFwiPumHh+mbhuWGheWuuTwvZGl2PlxyXG4gICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtY2FyZCBzdGF0LXByaW1hcnlcIj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC12YWx1ZVwiPnt7IGRhaWx5UmVwb3J0LnN1bW1hcnkuc2VsZWN0ZWQgfX08L2Rpdj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1sYWJlbFwiPuagh+iusOmAieS4rTwvZGl2PlxyXG4gICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG5cclxuICAgICAgICA8IS0tIOe0r+iuoeaVsOaNriAtLT5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwiZGFzaGJvYXJkLWdyb3VwXCI+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZ3JvdXAtdGl0bGVcIj7ntK/orqHmlbDmja48L2Rpdj5cclxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LXJvd1wiPlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkIHN0YXQtc2Vjb25kYXJ5XCI+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtdmFsdWVcIj57eyBkYWlseVJlcG9ydC5jdW11bGF0aXZlLnRvdGFsX2FydGljbGVzIH19PC9kaXY+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtbGFiZWxcIj7mgLvmlofnq6A8L2Rpdj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWNhcmQgc3RhdC1zZWNvbmRhcnlcIj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC12YWx1ZVwiPnt7IGRhaWx5UmVwb3J0LmN1bXVsYXRpdmUudG90YWxfd2l0aF9jb250ZW50IH19PC9kaXY+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtbGFiZWxcIj7lt7Lph4fpm4Y8L2Rpdj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWNhcmQgc3RhdC1zZWNvbmRhcnlcIj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC12YWx1ZVwiPnt7IGRhaWx5UmVwb3J0LmN1bXVsYXRpdmUudG90YWxfc2VsZWN0ZWQgfX08L2Rpdj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1sYWJlbFwiPuW3sumAieS4rTwvZGl2PlxyXG4gICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG5cclxuICAgICAgICA8IS0tIOmHh+mbhuadpea6kO+8iOe0r+iuoeespuWQiOadoeS7tueahO+8iSAtLT5cclxuICAgICAgICA8ZGl2IHYtaWY9XCJkYWlseVJlcG9ydC5zb3VyY2Vfc3RhdHMgJiYgZGFpbHlSZXBvcnQuc291cmNlX3N0YXRzLmxlbmd0aCA+IDBcIiBjbGFzcz1cImRhc2hib2FyZC1ncm91cFwiPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cImdyb3VwLXRpdGxlXCI+6YeH6ZuG5p2l5rqQ77yI56ym5ZCI5p2h5Lu277yJPC9kaXY+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwic291cmNlLXRhZ3NcIj5cclxuICAgICAgICAgICAgPGRpdiB2LWZvcj1cIml0ZW0gaW4gZGFpbHlSZXBvcnQuc291cmNlX3N0YXRzXCIgOmtleT1cIml0ZW0uc291cmNlXCIgY2xhc3M9XCJzb3VyY2UtdGFnXCI+XHJcbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJ0YWctbmFtZVwiPnt7IGl0ZW0uc291cmNlIH19PC9zcGFuPlxyXG4gICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwidGFnLWNvdW50XCI+e3sgaXRlbS5jb3VudCB9fTwvc3Bhbj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgPC9kaXY+XHJcbiAgICAgIDxkaXYgdi1lbHNlIGNsYXNzPVwicmVwb3J0LWVtcHR5XCI+5pqC5peg5bel5L2c5rGH5oql5pWw5o2uPC9kaXY+XHJcbiAgICA8L2Rpdj5cclxuICAgIFxyXG4gICAgPCEtLSDlupXpg6jkuKTmoI/luIPlsYAgLS0+XHJcbiAgICA8ZGl2IGNsYXNzPVwiYm90dG9tLWxheW91dFwiPlxyXG4gICAgICA8IS0tIOW3puS+p++8muW3peS9nOWumuS5ie+8iOmihOiniO+8iSAtLT5cclxuICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctcGFuZWwgZGVmaW5pdGlvbi1wcmV2aWV3XCI+XHJcbiAgICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctaGVhZGVyXCI+XHJcbiAgICAgICAgICA8aDM+Q2hhcmxlcyDlt6XkvZzlrprkuYk8L2gzPlxyXG4gICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImV4cGFuZC1idG5cIiBAY2xpY2s9XCJzaG93RGVmaW5pdGlvbk1vZGFsID0gdHJ1ZVwiIHRpdGxlPVwi5p+l55yL5YWo6YOoXCI+XHJcbiAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XHJcbiAgICAgICAgICAgICAgPHBhdGggZD1cIk04IDNINWEyIDIgMCAwIDAtMiAydjNtMTggMFY1YTIgMiAwIDAgMC0yLTJoLTNtMCAxOGgzYTIgMiAwIDAgMCAyLTJ2LTNNMyAxNnYzYTIgMiAwIDAgMCAyIDJoM1wiLz5cclxuICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICA8L2J1dHRvbj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwicHJldmlldy1jb250ZW50XCI+XHJcbiAgICAgICAgICA8ZGl2IHYtaWY9XCJ3b3JrRGVmaW5pdGlvbkxvYWRpbmdcIiBjbGFzcz1cImRlZmluaXRpb24tbG9hZGluZ1wiPuWKoOi9veS4rS4uLjwvZGl2PlxyXG4gICAgICAgICAgPGRpdiBcclxuICAgICAgICAgICAgdi1lbHNlLWlmPVwid29ya0RlZmluaXRpb25cIiBcclxuICAgICAgICAgICAgY2xhc3M9XCJkZWZpbml0aW9uLWNvbnRlbnQtcHJldmlld1wiIFxyXG4gICAgICAgICAgICB2LWh0bWw9XCJmb3JtYXRXb3JrRGVmaW5pdGlvbih3b3JrRGVmaW5pdGlvbilcIlxyXG4gICAgICAgICAgPjwvZGl2PlxyXG4gICAgICAgICAgPGRpdiB2LWVsc2UgY2xhc3M9XCJkZWZpbml0aW9uLWVycm9yXCI+5peg5rOV5Yqg6L295bel5L2c5a6a5LmJPC9kaXY+XHJcbiAgICAgICAgPC9kaXY+XHJcbiAgICAgIDwvZGl2PlxyXG4gICAgICBcclxuICAgICAgPCEtLSDlj7PkvqfvvJrlt6XkvZzml6Xlv5fvvIjpooTop4jvvIkgLS0+XHJcbiAgICAgIDxkaXYgY2xhc3M9XCJwcmV2aWV3LXBhbmVsIGxvZ3MtcHJldmlld1wiPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJwcmV2aWV3LWhlYWRlclwiPlxyXG4gICAgICAgICAgPGgzPuW3peS9nOaXpeW/lzwvaDM+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwibG9ncy1oZWFkZXItY29udHJvbHNcIj5cclxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cImRhdGUtc2VsZWN0b3JcIj5cclxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJkYXRlLWxhYmVsXCI+6YCJ5oup5pel5pyf77yaPC9sYWJlbD5cclxuICAgICAgICAgICAgICA8aW5wdXRcclxuICAgICAgICAgICAgICAgIHR5cGU9XCJkYXRlXCJcclxuICAgICAgICAgICAgICAgIHYtbW9kZWw9XCJzZWxlY3RlZERhdGVcIlxyXG4gICAgICAgICAgICAgICAgQGNoYW5nZT1cIm9uRGF0ZUNoYW5nZVwiXHJcbiAgICAgICAgICAgICAgICBjbGFzcz1cImRhdGUtaW5wdXRcIlxyXG4gICAgICAgICAgICAgICAgOm1heD1cInRvZGF5RGF0ZVwiXHJcbiAgICAgICAgICAgICAgLz5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cImF1dG8tcmVmcmVzaC1sYWJlbFwiPlxyXG4gICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwiY2hlY2tib3hcIiB2LW1vZGVsPVwiYXV0b1JlZnJlc2hcIiAvPlxyXG4gICAgICAgICAgICAgIOiHquWKqOWIt+aWsO+8iDXnp5LvvIlcclxuICAgICAgICAgICAgPC9sYWJlbD5cclxuICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cInJlZnJlc2gtYnRuXCIgQGNsaWNrPVwicmVmcmVzaExvZ3NcIj7liLfmlrA8L2J1dHRvbj5cclxuICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImV4cGFuZC1idG5cIiBAY2xpY2s9XCJzaG93TG9nc01vZGFsID0gdHJ1ZVwiIHRpdGxlPVwi5p+l55yL5YWo6YOoXCI+XHJcbiAgICAgICAgICAgICAgPHN2ZyB2aWV3Qm94PVwiMCAwIDI0IDI0XCIgZmlsbD1cIm5vbmVcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cclxuICAgICAgICAgICAgICAgIDxwYXRoIGQ9XCJNOCAzSDVhMiAyIDAgMCAwLTIgMnYzbTE4IDBWNWEyIDIgMCAwIDAtMi0yaC0zbTAgMThoM2EyIDIgMCAwIDAgMi0ydi0zTTMgMTZ2M2EyIDIgMCAwIDAgMiAyaDNcIi8+XHJcbiAgICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICAgIDwvYnV0dG9uPlxyXG4gICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctY29udGVudFwiPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cImxvZ3MtaW5mby1jb21wYWN0XCIgdi1pZj1cImxvZ0luZm9cIj5cclxuICAgICAgICAgICAgPHNwYW4+5pel5pyfOiB7eyBmb3JtYXREaXNwbGF5RGF0ZShzZWxlY3RlZERhdGUpIH19PC9zcGFuPlxyXG4gICAgICAgICAgICA8c3Bhbj7mgLvooYzmlbA6IHt7IGxvZ0luZm8udG90YWxfbGluZXMgfX08L3NwYW4+XHJcbiAgICAgICAgICAgIDxzcGFuIHYtaWY9XCIhbG9nSW5mby5maWxlX2V4aXN0c1wiIGNsYXNzPVwiZXJyb3ItdGV4dFwiPuaXpeW/l+aWh+S7tuS4jeWtmOWcqDwvc3Bhbj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cImxvZy1jb250ZW50LXByZXZpZXdcIiByZWY9XCJsb2dDb250ZW50UHJldmlld1wiPlxyXG4gICAgICAgICAgICA8ZGl2IHYtaWY9XCJsb2dMb2FkaW5nICYmIGxvZ3MubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJsb2ctbG9hZGluZ1wiPuWKoOi9veS4rS4uLjwvZGl2PlxyXG4gICAgICAgICAgICA8ZGl2IHYtZWxzZS1pZj1cImxvZ3MubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJsb2ctZW1wdHlcIj7mmoLml6Dml6Xlv5c8L2Rpdj5cclxuICAgICAgICAgICAgPHByZSB2LWVsc2UgY2xhc3M9XCJsb2ctdGV4dC1wcmV2aWV3XCIgOmNsYXNzPVwieyAndXBkYXRpbmcnOiBsb2dMb2FkaW5nIH1cIj57eyBsb2dUZXh0UHJldmlldyB9fTwvcHJlPlxyXG4gICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgPC9kaXY+XHJcbiAgICAgIDwvZGl2PlxyXG4gICAgPC9kaXY+XHJcbiAgICBcclxuICAgIDwhLS0g5bel5L2c5a6a5LmJ5YWo5bGP5qih5oCB5qGGIC0tPlxyXG4gICAgPGRpdiB2LWlmPVwic2hvd0RlZmluaXRpb25Nb2RhbFwiIGNsYXNzPVwibW9kYWwtb3ZlcmxheVwiIEBjbGljaz1cInNob3dEZWZpbml0aW9uTW9kYWwgPSBmYWxzZVwiPlxyXG4gICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtY29udGVudFwiIEBjbGljay5zdG9wPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1oZWFkZXJcIj5cclxuICAgICAgICAgIDxoMj5DaGFybGVzIOW3peS9nOWumuS5iTwvaDI+XHJcbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwibW9kYWwtY2xvc2VcIiBAY2xpY2s9XCJzaG93RGVmaW5pdGlvbk1vZGFsID0gZmFsc2VcIj5cclxuICAgICAgICAgICAgPHN2ZyB2aWV3Qm94PVwiMCAwIDI0IDI0XCIgZmlsbD1cIm5vbmVcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cclxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjE4XCIgeTE9XCI2XCIgeDI9XCI2XCIgeTI9XCIxOFwiLz5cclxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjZcIiB5MT1cIjZcIiB4Mj1cIjE4XCIgeTI9XCIxOFwiLz5cclxuICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICA8L2J1dHRvbj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtYm9keVwiPlxyXG4gICAgICAgICAgPGRpdiB2LWlmPVwid29ya0RlZmluaXRpb25Mb2FkaW5nXCIgY2xhc3M9XCJkZWZpbml0aW9uLWxvYWRpbmdcIj7liqDovb3kuK0uLi48L2Rpdj5cclxuICAgICAgICAgIDxkaXYgXHJcbiAgICAgICAgICAgIHYtZWxzZS1pZj1cIndvcmtEZWZpbml0aW9uXCIgXHJcbiAgICAgICAgICAgIGNsYXNzPVwiZGVmaW5pdGlvbi1jb250ZW50LWZ1bGxcIiBcclxuICAgICAgICAgICAgdi1odG1sPVwiZm9ybWF0V29ya0RlZmluaXRpb24od29ya0RlZmluaXRpb24pXCJcclxuICAgICAgICAgID48L2Rpdj5cclxuICAgICAgICAgIDxkaXYgdi1lbHNlIGNsYXNzPVwiZGVmaW5pdGlvbi1lcnJvclwiPuaXoOazleWKoOi9veW3peS9nOWumuS5iTwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICA8L2Rpdj5cclxuICAgIDwvZGl2PlxyXG4gICAgXHJcbiAgICA8IS0tIOW3peS9nOaXpeW/l+WFqOWxj+aooeaAgeahhiAtLT5cclxuICAgIDxkaXYgdi1pZj1cInNob3dMb2dzTW9kYWxcIiBjbGFzcz1cIm1vZGFsLW92ZXJsYXlcIiBAY2xpY2s9XCJzaG93TG9nc01vZGFsID0gZmFsc2VcIj5cclxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnQgbW9kYWwtY29udGVudC1sYXJnZVwiIEBjbGljay5zdG9wPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1oZWFkZXJcIj5cclxuICAgICAgICAgIDxoMj7lt6XkvZzml6Xlv5c8L2gyPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWhlYWRlci1yaWdodFwiPlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwibG9ncy1pbmZvLW1vZGFsXCIgdi1pZj1cImxvZ0luZm9cIj5cclxuICAgICAgICAgICAgICA8c3Bhbj7ml6XmnJ86IHt7IGZvcm1hdERpc3BsYXlEYXRlKHNlbGVjdGVkRGF0ZSkgfX08L3NwYW4+XHJcbiAgICAgICAgICAgICAgPHNwYW4+5oC76KGM5pWwOiB7eyBsb2dJbmZvLnRvdGFsX2xpbmVzIH19PC9zcGFuPlxyXG4gICAgICAgICAgICAgIDxzcGFuPuaYvuekuuihjOaVsDoge3sgbG9nSW5mby5yZXR1cm5lZF9saW5lcyB9fTwvc3Bhbj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cInNob3dMb2dzTW9kYWwgPSBmYWxzZVwiPlxyXG4gICAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XHJcbiAgICAgICAgICAgICAgICA8bGluZSB4MT1cIjE4XCIgeTE9XCI2XCIgeDI9XCI2XCIgeTI9XCIxOFwiLz5cclxuICAgICAgICAgICAgICAgIDxsaW5lIHgxPVwiNlwiIHkxPVwiNlwiIHgyPVwiMThcIiB5Mj1cIjE4XCIvPlxyXG4gICAgICAgICAgICAgIDwvc3ZnPlxyXG4gICAgICAgICAgICA8L2J1dHRvbj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1ib2R5XCI+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwibG9nLWNvbnRlbnQtZnVsbFwiIHJlZj1cImxvZ0NvbnRlbnRGdWxsXCI+XHJcbiAgICAgICAgICAgIDxkaXYgdi1pZj1cImxvZ0xvYWRpbmdcIiBjbGFzcz1cImxvZy1sb2FkaW5nXCI+5Yqg6L295LitLi4uPC9kaXY+XHJcbiAgICAgICAgICAgIDxkaXYgdi1lbHNlLWlmPVwibG9ncy5sZW5ndGggPT09IDBcIiBjbGFzcz1cImxvZy1lbXB0eVwiPuaaguaXoOaXpeW/lzwvZGl2PlxyXG4gICAgICAgICAgICA8cHJlIHYtZWxzZSBjbGFzcz1cImxvZy10ZXh0LWZ1bGxcIj57eyBsb2dUZXh0IH19PC9wcmU+XHJcbiAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgPC9kaXY+XHJcbiAgICA8L2Rpdj5cclxuICA8L2Rpdj5cclxuPC90ZW1wbGF0ZT5cclxuXHJcbjxzY3JpcHQgc2V0dXA+XHJcbmltcG9ydCB7IHJlZiwgY29tcHV0ZWQsIG9uTW91bnRlZCwgb25Vbm1vdW50ZWQsIHdhdGNoIH0gZnJvbSAndnVlJ1xyXG5pbXBvcnQgeyB1c2VSb3V0ZXIgfSBmcm9tICd2dWUtcm91dGVyJ1xyXG5pbXBvcnQgeyBBUElfQkFTRV9VUkwgfSBmcm9tICcuLi91dGlscy9hcGlDb25maWcnXHJcbmltcG9ydCBBcHBIZWFkZXIgZnJvbSAnLi4vY29tcG9uZW50cy9BcHBIZWFkZXIudnVlJ1xyXG5cclxuY29uc3Qgcm91dGVyID0gdXNlUm91dGVyKClcclxuY29uc3QgbG9ncyA9IHJlZihbXSlcclxuY29uc3QgbG9nTG9hZGluZyA9IHJlZihmYWxzZSlcclxuY29uc3QgYXV0b1JlZnJlc2ggPSByZWYoZmFsc2UpXHJcbmNvbnN0IGxvZ0NvbnRlbnQgPSByZWYobnVsbClcclxuY29uc3QgbG9nQ29udGVudFByZXZpZXcgPSByZWYobnVsbClcclxuY29uc3QgbG9nQ29udGVudEZ1bGwgPSByZWYobnVsbClcclxuY29uc3QgbG9nSW5mbyA9IHJlZihudWxsKVxyXG5sZXQgcmVmcmVzaFRpbWVyID0gbnVsbFxyXG5cclxuLy8g5pel5pyf55u45YWzXHJcbmNvbnN0IHRvZGF5RGF0ZSA9IHJlZihuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCkuc3BsaXQoJ1QnKVswXSkgIC8vIFlZWVktTU0tRETmoLzlvI9cclxuY29uc3Qgc2VsZWN0ZWREYXRlID0gcmVmKHRvZGF5RGF0ZS52YWx1ZSkgIC8vIOm7mOiupOmAieaLqeS7iuWkqVxyXG5cclxuLy8g5bel5L2c5rGH5oqlXHJcbmNvbnN0IGRhaWx5UmVwb3J0ID0gcmVmKG51bGwpXHJcbmNvbnN0IHJlcG9ydExvYWRpbmcgPSByZWYoZmFsc2UpXHJcblxyXG4vLyDlt6XkvZzlrprkuYlcclxuY29uc3Qgd29ya0RlZmluaXRpb24gPSByZWYobnVsbClcclxuY29uc3Qgd29ya0RlZmluaXRpb25Mb2FkaW5nID0gcmVmKGZhbHNlKVxyXG5cclxuLy8g5qih5oCB5qGG54q25oCBXHJcbmNvbnN0IHNob3dEZWZpbml0aW9uTW9kYWwgPSByZWYoZmFsc2UpXHJcbmNvbnN0IHNob3dMb2dzTW9kYWwgPSByZWYoZmFsc2UpXHJcblxyXG4vLyBDaGFybGVzIOeKtuaAgVxyXG5jb25zdCBjaGFybGVzU3RhdHVzID0gcmVmKG51bGwpXHJcbmNvbnN0IHN0YXR1c1Nob3duQWxlcnQgPSByZWYoZmFsc2UpXHJcblxyXG5jb25zdCBzdGF0dXNDbGFzcyA9IGNvbXB1dGVkKCgpID0+IHtcclxuICBpZiAoIWNoYXJsZXNTdGF0dXMudmFsdWUpIHJldHVybiAnc3RhdHVzLXVua25vd24nXHJcbiAgY29uc3Qgc3RhdHVzID0gY2hhcmxlc1N0YXR1cy52YWx1ZS5zdGF0dXNcclxuICBpZiAoc3RhdHVzID09PSAnd29ya2luZycpIHJldHVybiAnc3RhdHVzLXdvcmtpbmcnXHJcbiAgaWYgKHN0YXR1cyA9PT0gJ2RlYWQnKSByZXR1cm4gJ3N0YXR1cy1kZWFkJ1xyXG4gIHJldHVybiAnc3RhdHVzLXVua25vd24nXHJcbn0pXHJcblxyXG5jb25zdCBzdGF0dXNUZXh0ID0gY29tcHV0ZWQoKCkgPT4ge1xyXG4gIGlmICghY2hhcmxlc1N0YXR1cy52YWx1ZSkgcmV0dXJuICfmnKrnn6UnXHJcbiAgY29uc3Qgc3RhdHVzID0gY2hhcmxlc1N0YXR1cy52YWx1ZS5zdGF0dXNcclxuICBpZiAoc3RhdHVzID09PSAnd29ya2luZycpIHJldHVybiAn6L+Q6KGM5LitJ1xyXG4gIGlmIChzdGF0dXMgPT09ICdkZWFkJykgcmV0dXJuICflt7LlgZzmraInXHJcbiAgcmV0dXJuICfmnKrnn6UnXHJcbn0pXHJcblxyXG5jb25zdCBzaG93U3RhdHVzRGV0YWlsID0gKCkgPT4ge1xyXG4gIGlmICghY2hhcmxlc1N0YXR1cy52YWx1ZSkge1xyXG4gICAgYWxlcnQoJ+aXoOazleiOt+WPlueKtuaAgeS/oeaBrycpXHJcbiAgICByZXR1cm5cclxuICB9XHJcbiAgY29uc3QgcyA9IGNoYXJsZXNTdGF0dXMudmFsdWVcclxuICBsZXQgbXNnID0gYOeKtuaAgTogJHtzdGF0dXNUZXh0LnZhbHVlfVxcbmBcclxuICBpZiAocy5zdGFydF90aW1lKSBtc2cgKz0gYOWQr+WKqOaXtumXtDogJHtzLnN0YXJ0X3RpbWV9XFxuYFxyXG4gIGlmIChzLmxhc3RfdXBkYXRlX3RpbWUpIG1zZyArPSBg5pyA5ZCO5b+D6LezOiAke3MubGFzdF91cGRhdGVfdGltZX1cXG5gXHJcbiAgaWYgKHMuZW5kX3RpbWUpIG1zZyArPSBg57uT5p2f5pe26Ze0OiAke3MuZW5kX3RpbWV9XFxuYFxyXG4gIGlmIChzLmVycm9yX21lc3NhZ2UpIG1zZyArPSBg6ZSZ6K+v5L+h5oGvOiAke3MuZXJyb3JfbWVzc2FnZX1cXG5gXHJcbiAgaWYgKHMucGlkKSBtc2cgKz0gYOi/m+eoi0lEOiAke3MucGlkfVxcbmBcclxuICBpZiAocy5tZXNzYWdlKSBtc2cgKz0gYOivtOaYjjogJHtzLm1lc3NhZ2V9XFxuYFxyXG4gIGFsZXJ0KG1zZylcclxufVxyXG5cclxuY29uc3QgZmV0Y2hDaGFybGVzU3RhdHVzID0gYXN5bmMgKCkgPT4ge1xyXG4gIHRyeSB7XHJcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcclxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goYCR7YXBpVXJsfS9hcGkvemhpaHUvc3RhdHVzYClcclxuICAgIGlmIChyZXNwb25zZS5vaykge1xyXG4gICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcclxuICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcclxuICAgICAgICBjaGFybGVzU3RhdHVzLnZhbHVlID0gcmVzdWx0LmRhdGFcclxuICAgICAgICBpZiAocmVzdWx0LmRhdGEuc3RhdHVzID09PSAnZGVhZCcgJiYgIXN0YXR1c1Nob3duQWxlcnQudmFsdWUpIHtcclxuICAgICAgICAgIHN0YXR1c1Nob3duQWxlcnQudmFsdWUgPSB0cnVlXHJcbiAgICAgICAgICBjb25zdCBlcnJvck1zZyA9IHJlc3VsdC5kYXRhLmVycm9yX21lc3NhZ2UgPyBgXFxu6ZSZ6K+v5L+h5oGvOiAke3Jlc3VsdC5kYXRhLmVycm9yX21lc3NhZ2V9YCA6ICcnXHJcbiAgICAgICAgICBhbGVydChgQ2hhcmxlcyDlt7LlgZzmraLov5DooYzvvIEke2Vycm9yTXNnfVxcblxcbuivt+ajgOafpeW5tumHjeaWsOWQr+WKqCBDaGFybGVz44CCYClcclxuICAgICAgICB9XHJcbiAgICAgIH1cclxuICAgIH1cclxuICB9IGNhdGNoIChlcnJvcikge1xyXG4gICAgY29uc29sZS5lcnJvcign6I635Y+W54q25oCB5aSx6LSlOicsIGVycm9yKVxyXG4gIH1cclxufVxyXG5cclxuY29uc3QgbG9nVGV4dCA9IGNvbXB1dGVkKCgpID0+IHtcclxuICByZXR1cm4gbG9ncy52YWx1ZS5qb2luKCdcXG4nKVxyXG59KVxyXG5cclxuLy8g6aKE6KeI5qih5byP55qE5pel5b+X5paH5pys77yI5Y+q5pi+56S65pyA5ZCOMjAw6KGM77yJXHJcbmNvbnN0IGxvZ1RleHRQcmV2aWV3ID0gY29tcHV0ZWQoKCkgPT4ge1xyXG4gIGlmIChsb2dzLnZhbHVlLmxlbmd0aCA8PSAyMDApIHtcclxuICAgIHJldHVybiBsb2dzLnZhbHVlLmpvaW4oJ1xcbicpXHJcbiAgfVxyXG4gIHJldHVybiBsb2dzLnZhbHVlLnNsaWNlKC0yMDApLmpvaW4oJ1xcbicpXHJcbn0pXHJcblxyXG4vLyDlsIbml6XmnJ/moLzlvI/ku44gWVlZWS1NTS1ERCDovazmjaLkuLogWVlZWU1NRERcclxuY29uc3QgZm9ybWF0RGF0ZUZvckFwaSA9IChkYXRlU3RyKSA9PiB7XHJcbiAgaWYgKCFkYXRlU3RyKSByZXR1cm4gbnVsbFxyXG4gIHJldHVybiBkYXRlU3RyLnJlcGxhY2UoLy0vZywgJycpXHJcbn1cclxuXHJcbi8vIOagvOW8j+WMluaYvuekuuaXpeacn1xyXG5jb25zdCBmb3JtYXREaXNwbGF5RGF0ZSA9IChkYXRlU3RyKSA9PiB7XHJcbiAgaWYgKCFkYXRlU3RyKSByZXR1cm4gJydcclxuICBjb25zdCBkYXRlID0gbmV3IERhdGUoZGF0ZVN0cilcclxuICBjb25zdCB5ZWFyID0gZGF0ZS5nZXRGdWxsWWVhcigpXHJcbiAgY29uc3QgbW9udGggPSAoZGF0ZS5nZXRNb250aCgpICsgMSkudG9TdHJpbmcoKS5wYWRTdGFydCgyLCAnMCcpXHJcbiAgY29uc3QgZGF5ID0gZGF0ZS5nZXREYXRlKCkudG9TdHJpbmcoKS5wYWRTdGFydCgyLCAnMCcpXHJcbiAgcmV0dXJuIGAke3llYXJ95bm0JHttb250aH3mnIgke2RheX3ml6VgXHJcbn1cclxuXHJcbi8vIOiOt+WPluaXpeW/l1xyXG5jb25zdCBmZXRjaExvZ3MgPSBhc3luYyAoc2hvd0xvYWRpbmcgPSB0cnVlKSA9PiB7XHJcbiAgLy8g5Y+q5pyJ5Zyo6ZyA6KaB5pi+56S6bG9hZGluZ+aXtuaJjeiuvue9rmxvYWRpbmfnirbmgIHvvIzpgb/lhY3kuI3lv4XopoHnmoTpl6rliqhcclxuICBpZiAoc2hvd0xvYWRpbmcpIHtcclxuICAgIGxvZ0xvYWRpbmcudmFsdWUgPSB0cnVlXHJcbiAgfVxyXG4gIHRyeSB7XHJcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcclxuICAgIGNvbnN0IGRhdGVQYXJhbSA9IGZvcm1hdERhdGVGb3JBcGkoc2VsZWN0ZWREYXRlLnZhbHVlKVxyXG4gICAgY29uc3QgdXJsID0gYCR7YXBpVXJsfS9hcGkvemhpaHUvbG9ncz9saW5lcz0xMDAwJnRhaWw9dHJ1ZSR7ZGF0ZVBhcmFtID8gYCZkYXRlPSR7ZGF0ZVBhcmFtfWAgOiAnJ31gXHJcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKHVybClcclxuICAgIFxyXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XHJcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxyXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xyXG4gICAgICAgIC8vIOebtOaOpeabtOaWsOaVsOaNru+8jOmBv+WFjeWFiOa4heepuuWGjeiuvue9ruWvvOiHtOeahOmXquWKqFxyXG4gICAgICAgIGNvbnN0IG5ld0xvZ3MgPSByZXN1bHQuZGF0YS5sb2dzIHx8IFtdXHJcbiAgICAgICAgY29uc3QgbmV3TG9nSW5mbyA9IHtcclxuICAgICAgICAgIHRvdGFsX2xpbmVzOiByZXN1bHQuZGF0YS50b3RhbF9saW5lcyB8fCAwLFxyXG4gICAgICAgICAgcmV0dXJuZWRfbGluZXM6IHJlc3VsdC5kYXRhLnJldHVybmVkX2xpbmVzIHx8IDAsXHJcbiAgICAgICAgICBmaWxlX2V4aXN0czogcmVzdWx0LmRhdGEuZmlsZV9leGlzdHMgIT09IGZhbHNlLFxyXG4gICAgICAgICAgbG9nX3BhdGg6IHJlc3VsdC5kYXRhLmxvZ19wYXRoIHx8ICcnLFxyXG4gICAgICAgICAgZGF0ZTogcmVzdWx0LmRhdGEuZGF0ZSB8fCBmb3JtYXREYXRlRm9yQXBpKHNlbGVjdGVkRGF0ZS52YWx1ZSksXHJcbiAgICAgICAgICBhdmFpbGFibGVfZGF0ZXM6IHJlc3VsdC5kYXRhLmF2YWlsYWJsZV9kYXRlcyB8fCBbXVxyXG4gICAgICAgIH1cclxuICAgICAgICBcclxuICAgICAgICAvLyDmibnph4/mm7TmlrDvvIzlh4/lsJHph43mlrDmuLLmn5PmrKHmlbBcclxuICAgICAgICBsb2dzLnZhbHVlID0gbmV3TG9nc1xyXG4gICAgICAgIGxvZ0luZm8udmFsdWUgPSBuZXdMb2dJbmZvXHJcbiAgICAgICAgXHJcbiAgICAgICAgLy8g5rua5Yqo5Yiw5bqV6YOo77yI6aKE6KeI5Yy65Z+f77yJXHJcbiAgICAgICAgaWYgKGxvZ0NvbnRlbnRQcmV2aWV3LnZhbHVlKSB7XHJcbiAgICAgICAgICBzZXRUaW1lb3V0KCgpID0+IHtcclxuICAgICAgICAgICAgbG9nQ29udGVudFByZXZpZXcudmFsdWUuc2Nyb2xsVG9wID0gbG9nQ29udGVudFByZXZpZXcudmFsdWUuc2Nyb2xsSGVpZ2h0XHJcbiAgICAgICAgICB9LCAxMDApXHJcbiAgICAgICAgfVxyXG4gICAgICB9IGVsc2Uge1xyXG4gICAgICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluaXpeW/l+Wksei0pTonLCByZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKVxyXG4gICAgICAgIGxvZ3MudmFsdWUgPSBbXVxyXG4gICAgICAgIGxvZ0luZm8udmFsdWUgPSB7XHJcbiAgICAgICAgICB0b3RhbF9saW5lczogMCxcclxuICAgICAgICAgIHJldHVybmVkX2xpbmVzOiAwLFxyXG4gICAgICAgICAgZmlsZV9leGlzdHM6IGZhbHNlLFxyXG4gICAgICAgICAgbG9nX3BhdGg6ICcnLFxyXG4gICAgICAgICAgZGF0ZTogZm9ybWF0RGF0ZUZvckFwaShzZWxlY3RlZERhdGUudmFsdWUpLFxyXG4gICAgICAgICAgYXZhaWxhYmxlX2RhdGVzOiByZXN1bHQuZGF0YT8uYXZhaWxhYmxlX2RhdGVzIHx8IFtdXHJcbiAgICAgICAgfVxyXG4gICAgICB9XHJcbiAgICB9IGVsc2Uge1xyXG4gICAgICBjb25zb2xlLmVycm9yKCdBUEkg6K+35rGC5aSx6LSlOicsIHJlc3BvbnNlLnN0YXR1cylcclxuICAgICAgbG9ncy52YWx1ZSA9IFtdXHJcbiAgICB9XHJcbiAgfSBjYXRjaCAoZXJyb3IpIHtcclxuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluaXpeW/l+WHuumUmTonLCBlcnJvcilcclxuICAgIGxvZ3MudmFsdWUgPSBbXVxyXG4gIH0gZmluYWxseSB7XHJcbiAgICBpZiAoc2hvd0xvYWRpbmcpIHtcclxuICAgICAgbG9nTG9hZGluZy52YWx1ZSA9IGZhbHNlXHJcbiAgICB9XHJcbiAgfVxyXG59XHJcblxyXG4vLyDml6XmnJ/lj5jljJblpITnkIbvvIjlj6rliLfmlrDml6Xlv5fvvIlcclxuY29uc3Qgb25EYXRlQ2hhbmdlID0gKCkgPT4ge1xyXG4gIC8vIOWBnOatouiHquWKqOWIt+aWsO+8iOWIh+aNouaXpeacn+aXtu+8iVxyXG4gIGF1dG9SZWZyZXNoLnZhbHVlID0gZmFsc2VcclxuICBmZXRjaExvZ3MoKVxyXG59XHJcblxyXG4vLyDliLfmlrDml6Xlv5fmlbDmja5cclxuY29uc3QgcmVmcmVzaExvZ3MgPSAoKSA9PiB7XHJcbiAgZmV0Y2hMb2dzKClcclxufVxyXG5cclxuLy8g5omT5byA5bel5L2c5a6a5LmJ5qih5oCB5qGG5pe25rua5Yqo5Yiw5bqV6YOoXHJcbndhdGNoKHNob3dEZWZpbml0aW9uTW9kYWwsIChzaG93KSA9PiB7XHJcbiAgaWYgKHNob3cgJiYgd29ya0RlZmluaXRpb24udmFsdWUpIHtcclxuICAgIHNldFRpbWVvdXQoKCkgPT4ge1xyXG4gICAgICBjb25zdCBtb2RhbEJvZHkgPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKCcuZGVmaW5pdGlvbi1jb250ZW50LWZ1bGwnKVxyXG4gICAgICBpZiAobW9kYWxCb2R5KSB7XHJcbiAgICAgICAgbW9kYWxCb2R5LnNjcm9sbFRvcCA9IDBcclxuICAgICAgfVxyXG4gICAgfSwgMTAwKVxyXG4gIH1cclxufSlcclxuXHJcbi8vIOaJk+W8gOaXpeW/l+aooeaAgeahhuaXtua7muWKqOWIsOW6lemDqFxyXG53YXRjaChzaG93TG9nc01vZGFsLCAoc2hvdykgPT4ge1xyXG4gIGlmIChzaG93ICYmIGxvZ0NvbnRlbnRGdWxsLnZhbHVlKSB7XHJcbiAgICBzZXRUaW1lb3V0KCgpID0+IHtcclxuICAgICAgbG9nQ29udGVudEZ1bGwudmFsdWUuc2Nyb2xsVG9wID0gbG9nQ29udGVudEZ1bGwudmFsdWUuc2Nyb2xsSGVpZ2h0XHJcbiAgICB9LCAxMDApXHJcbiAgfVxyXG59KVxyXG5cclxuLy8g6I635Y+W5bel5L2c5rGH5oqlXHJcbmNvbnN0IGZldGNoRGFpbHlSZXBvcnQgPSBhc3luYyAoKSA9PiB7XHJcbiAgcmVwb3J0TG9hZGluZy52YWx1ZSA9IHRydWVcclxuICB0cnkge1xyXG4gICAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXHJcbiAgICBjb25zdCBkYXRlUGFyYW0gPSBmb3JtYXREYXRlRm9yQXBpKHNlbGVjdGVkRGF0ZS52YWx1ZSlcclxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goYCR7YXBpVXJsfS9hcGkvemhpaHUvZGFpbHktcmVwb3J0P2RhdGU9JHtkYXRlUGFyYW19YClcclxuICAgIFxyXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XHJcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxyXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xyXG4gICAgICAgIGRhaWx5UmVwb3J0LnZhbHVlID0gcmVzdWx0LmRhdGFcclxuICAgICAgfSBlbHNlIHtcclxuICAgICAgICBjb25zb2xlLmVycm9yKCfojrflj5blt6XkvZzmsYfmiqXlpLHotKU6JywgcmVzdWx0Lm1zZyB8fCByZXN1bHQubWVzc2FnZSlcclxuICAgICAgICBkYWlseVJlcG9ydC52YWx1ZSA9IG51bGxcclxuICAgICAgfVxyXG4gICAgfSBlbHNlIHtcclxuICAgICAgY29uc29sZS5lcnJvcignQVBJIOivt+axguWksei0pTonLCByZXNwb25zZS5zdGF0dXMpXHJcbiAgICAgIGRhaWx5UmVwb3J0LnZhbHVlID0gbnVsbFxyXG4gICAgfVxyXG4gIH0gY2F0Y2ggKGVycm9yKSB7XHJcbiAgICBjb25zb2xlLmVycm9yKCfojrflj5blt6XkvZzmsYfmiqXlh7rplJk6JywgZXJyb3IpXHJcbiAgICBkYWlseVJlcG9ydC52YWx1ZSA9IG51bGxcclxuICB9IGZpbmFsbHkge1xyXG4gICAgcmVwb3J0TG9hZGluZy52YWx1ZSA9IGZhbHNlXHJcbiAgfVxyXG59XHJcblxyXG4vLyDojrflj5blt6XkvZzlrprkuYlcclxuY29uc3QgZmV0Y2hXb3JrRGVmaW5pdGlvbiA9IGFzeW5jICgpID0+IHtcclxuICB3b3JrRGVmaW5pdGlvbkxvYWRpbmcudmFsdWUgPSB0cnVlXHJcbiAgdHJ5IHtcclxuICAgIGNvbnN0IGFwaVVybCA9IEFQSV9CQVNFX1VSTFxyXG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS93b3JrLWRlZmluaXRpb25gKVxyXG4gICAgXHJcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcclxuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXHJcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XHJcbiAgICAgICAgd29ya0RlZmluaXRpb24udmFsdWUgPSByZXN1bHQuZGF0YT8uY29udGVudCB8fCAnJ1xyXG4gICAgICB9IGVsc2Uge1xyXG4gICAgICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluW3peS9nOWumuS5ieWksei0pTonLCByZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKVxyXG4gICAgICAgIHdvcmtEZWZpbml0aW9uLnZhbHVlID0gbnVsbFxyXG4gICAgICB9XHJcbiAgICB9IGVsc2Uge1xyXG4gICAgICBjb25zb2xlLmVycm9yKCdBUEkg6K+35rGC5aSx6LSlOicsIHJlc3BvbnNlLnN0YXR1cylcclxuICAgICAgd29ya0RlZmluaXRpb24udmFsdWUgPSBudWxsXHJcbiAgICB9XHJcbiAgfSBjYXRjaCAoZXJyb3IpIHtcclxuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluW3peS9nOWumuS5ieWHuumUmTonLCBlcnJvcilcclxuICAgIHdvcmtEZWZpbml0aW9uLnZhbHVlID0gbnVsbFxyXG4gIH0gZmluYWxseSB7XHJcbiAgICB3b3JrRGVmaW5pdGlvbkxvYWRpbmcudmFsdWUgPSBmYWxzZVxyXG4gIH1cclxufVxyXG5cclxuLy8g5qC85byP5YyW5bel5L2c5a6a5LmJ5YaF5a6577yI5bCG5paH5pys6L2s5o2i5Li6SFRNTO+8iVxyXG5jb25zdCBmb3JtYXRXb3JrRGVmaW5pdGlvbiA9ICh0ZXh0KSA9PiB7XHJcbiAgaWYgKCF0ZXh0KSByZXR1cm4gJydcclxuICBcclxuICAvLyDlsIbmlofmnKzmjInooYzliIblibJcclxuICBjb25zdCBsaW5lcyA9IHRleHQuc3BsaXQoJ1xcbicpXHJcbiAgbGV0IGh0bWwgPSAnJ1xyXG4gIGxldCBpbkxpc3QgPSBmYWxzZVxyXG4gIFxyXG4gIGZvciAobGV0IGkgPSAwOyBpIDwgbGluZXMubGVuZ3RoOyBpKyspIHtcclxuICAgIGNvbnN0IGxpbmUgPSBsaW5lc1tpXS50cmltKClcclxuICAgIFxyXG4gICAgaWYgKCFsaW5lKSB7XHJcbiAgICAgIGlmIChpbkxpc3QpIHtcclxuICAgICAgICBodG1sICs9ICc8L29sPidcclxuICAgICAgICBpbkxpc3QgPSBmYWxzZVxyXG4gICAgICB9XHJcbiAgICAgIGh0bWwgKz0gJzxicj4nXHJcbiAgICAgIGNvbnRpbnVlXHJcbiAgICB9XHJcbiAgICBcclxuICAgIC8vIOajgOafpeaYr+WQpuaYr+agh+mimFxyXG4gICAgaWYgKGxpbmUuaW5jbHVkZXMoJ+W3peS9nOWumuS5iScpIHx8IGxpbmUuaW5jbHVkZXMoJ+W3peS9nOa1geeoiycpIHx8IGxpbmUuaW5jbHVkZXMoJ+S6uuW3peaTjeS9nCcpKSB7XHJcbiAgICAgIGlmIChpbkxpc3QpIHtcclxuICAgICAgICBodG1sICs9ICc8L29sPidcclxuICAgICAgICBpbkxpc3QgPSBmYWxzZVxyXG4gICAgICB9XHJcbiAgICAgIGh0bWwgKz0gYDxoND4ke2xpbmV9PC9oND5gXHJcbiAgICB9XHJcbiAgICAvLyDmo4Dmn6XmmK/lkKbmmK/liJfooajpobnvvIjku6XmlbDlrZflvIDlpLTvvIlcclxuICAgIGVsc2UgaWYgKC9eXFxkK1xcLi8udGVzdChsaW5lKSkge1xyXG4gICAgICBpZiAoIWluTGlzdCkge1xyXG4gICAgICAgIGh0bWwgKz0gJzxvbD4nXHJcbiAgICAgICAgaW5MaXN0ID0gdHJ1ZVxyXG4gICAgICB9XHJcbiAgICAgIC8vIOaPkOWPluaVsOWtl+WSjOWGheWuuVxyXG4gICAgICBjb25zdCBtYXRjaCA9IGxpbmUubWF0Y2goL14oXFxkKylcXC5cXHMqKC4rKS8pXHJcbiAgICAgIGlmIChtYXRjaCkge1xyXG4gICAgICAgIGNvbnN0IGNvbnRlbnQgPSBtYXRjaFsyXVxyXG4gICAgICAgIC8vIOajgOafpeaYr+WQpuacieWGkuWPt+WIhumalOeahOagh+mimOWSjOaPj+i/sFxyXG4gICAgICAgIGlmIChjb250ZW50LmluY2x1ZGVzKCfvvJonKSkge1xyXG4gICAgICAgICAgY29uc3QgW3RpdGxlLCBkZXNjXSA9IGNvbnRlbnQuc3BsaXQoJ++8micsIDIpXHJcbiAgICAgICAgICBodG1sICs9IGA8bGk+PHN0cm9uZz4ke3RpdGxlfTwvc3Ryb25nPu+8miR7ZGVzY308L2xpPmBcclxuICAgICAgICB9IGVsc2Uge1xyXG4gICAgICAgICAgaHRtbCArPSBgPGxpPiR7Y29udGVudH08L2xpPmBcclxuICAgICAgICB9XHJcbiAgICAgIH1cclxuICAgIH1cclxuICAgIC8vIOajgOafpeaYr+WQpuaYr+WIl+ihqOmhue+8iOS7pS3lvIDlpLTvvIlcclxuICAgIGVsc2UgaWYgKGxpbmUuc3RhcnRzV2l0aCgnLScpKSB7XHJcbiAgICAgIGlmICghaW5MaXN0KSB7XHJcbiAgICAgICAgaHRtbCArPSAnPHVsPidcclxuICAgICAgICBpbkxpc3QgPSB0cnVlXHJcbiAgICAgIH1cclxuICAgICAgaHRtbCArPSBgPGxpPiR7bGluZS5zdWJzdHJpbmcoMSkudHJpbSgpfTwvbGk+YFxyXG4gICAgfVxyXG4gICAgLy8g5pmu6YCa5paH5pysXHJcbiAgICBlbHNlIHtcclxuICAgICAgaWYgKGluTGlzdCkge1xyXG4gICAgICAgIGh0bWwgKz0gJzwvb2w+J1xyXG4gICAgICAgIGluTGlzdCA9IGZhbHNlXHJcbiAgICAgIH1cclxuICAgICAgaHRtbCArPSBgPHA+JHtsaW5lfTwvcD5gXHJcbiAgICB9XHJcbiAgfVxyXG4gIFxyXG4gIGlmIChpbkxpc3QpIHtcclxuICAgIGh0bWwgKz0gJzwvb2w+J1xyXG4gIH1cclxuICBcclxuICByZXR1cm4gaHRtbFxyXG59XHJcblxyXG4vLyDnm5HlkKzoh6rliqjliLfmlrDvvIjpnZnpu5jliLfmlrDvvIzkuI3mmL7npLpsb2FkaW5n77yJXHJcbndhdGNoKGF1dG9SZWZyZXNoLCAoYXV0bykgPT4ge1xyXG4gIGlmIChhdXRvKSB7XHJcbiAgICBmZXRjaExvZ3MoZmFsc2UpIC8vIOiHquWKqOWIt+aWsOaXtuS4jeaYvuekumxvYWRpbmfvvIzpgb/lhY3pl6rliqhcclxuICAgIHJlZnJlc2hUaW1lciA9IHNldEludGVydmFsKCgpID0+IHtcclxuICAgICAgZmV0Y2hMb2dzKGZhbHNlKSAvLyDpnZnpu5jliLfmlrBcclxuICAgIH0sIDUwMDApXHJcbiAgfSBlbHNlIHtcclxuICAgIGlmIChyZWZyZXNoVGltZXIpIHtcclxuICAgICAgY2xlYXJJbnRlcnZhbChyZWZyZXNoVGltZXIpXHJcbiAgICAgIHJlZnJlc2hUaW1lciA9IG51bGxcclxuICAgIH1cclxuICB9XHJcbn0pXHJcblxyXG5vbk1vdW50ZWQoKCkgPT4ge1xyXG4gIGZldGNoTG9ncygpXHJcbiAgZmV0Y2hEYWlseVJlcG9ydCgpXHJcbiAgZmV0Y2hXb3JrRGVmaW5pdGlvbigpXHJcbiAgZmV0Y2hDaGFybGVzU3RhdHVzKClcclxufSlcclxuXHJcbm9uVW5tb3VudGVkKCgpID0+IHtcclxuICBpZiAocmVmcmVzaFRpbWVyKSB7XHJcbiAgICBjbGVhckludGVydmFsKHJlZnJlc2hUaW1lcilcclxuICAgIHJlZnJlc2hUaW1lciA9IG51bGxcclxuICB9XHJcbn0pXHJcbjwvc2NyaXB0PlxyXG5cclxuPHN0eWxlIHNjb3BlZD5cclxuLmxvZ3MtcGFnZSB7XHJcbiAgbWF4LXdpZHRoOiAxNjAwcHg7XHJcbiAgbWFyZ2luOiAwIGF1dG87XHJcbiAgcGFkZGluZzogMTZweCAzMnB4O1xyXG4gIG1pbi1oZWlnaHQ6IGNhbGMoMTAwdmggLSA2MHB4KTtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbn1cclxuXHJcbi5sb2dzLWhlYWRlciB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBtYXJnaW4tYm90dG9tOiAxNnB4O1xyXG4gIGZsZXgtd3JhcDogd3JhcDtcclxuICBnYXA6IDEycHg7XHJcbn1cclxuXHJcbi5sb2dzLXRpdGxlIHtcclxuICBmb250LXNpemU6IDIwcHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzFhMWExYTtcclxuICBtYXJnaW46IDA7XHJcbn1cclxuXHJcbi50aXRsZS13aXRoLXN0YXR1cyB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGdhcDogMTJweDtcclxufVxyXG5cclxuLnN0YXR1cy1iYWRnZSB7XHJcbiAgZGlzcGxheTogaW5saW5lLWZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDZweDtcclxuICBwYWRkaW5nOiA0cHggMTBweDtcclxuICBib3JkZXItcmFkaXVzOiAxMnB4O1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XHJcbn1cclxuXHJcbi5zdGF0dXMtYmFkZ2U6aG92ZXIge1xyXG4gIG9wYWNpdHk6IDAuODtcclxufVxyXG5cclxuLnN0YXR1cy1kb3Qge1xyXG4gIHdpZHRoOiA4cHg7XHJcbiAgaGVpZ2h0OiA4cHg7XHJcbiAgYm9yZGVyLXJhZGl1czogNTAlO1xyXG59XHJcblxyXG4uc3RhdHVzLXdvcmtpbmcge1xyXG4gIGJhY2tncm91bmQ6ICNmNmZmZWQ7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2I3ZWI4ZjtcclxuICBjb2xvcjogIzUyYzQxYTtcclxufVxyXG5cclxuLnN0YXR1cy13b3JraW5nIC5zdGF0dXMtZG90IHtcclxuICBiYWNrZ3JvdW5kOiAjNTJjNDFhO1xyXG4gIGFuaW1hdGlvbjogcHVsc2UgMnMgaW5maW5pdGU7XHJcbn1cclxuXHJcbi5zdGF0dXMtZGVhZCB7XHJcbiAgYmFja2dyb3VuZDogI2ZmZjJmMDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZmZjY2M3O1xyXG4gIGNvbG9yOiAjZmY0ZDRmO1xyXG59XHJcblxyXG4uc3RhdHVzLWRlYWQgLnN0YXR1cy1kb3Qge1xyXG4gIGJhY2tncm91bmQ6ICNmZjRkNGY7XHJcbn1cclxuXHJcbi5zdGF0dXMtdW5rbm93biB7XHJcbiAgYmFja2dyb3VuZDogI2ZhZmFmYTtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZDlkOWQ5O1xyXG4gIGNvbG9yOiAjOTk5O1xyXG59XHJcblxyXG4uc3RhdHVzLXVua25vd24gLnN0YXR1cy1kb3Qge1xyXG4gIGJhY2tncm91bmQ6ICM5OTk7XHJcbn1cclxuXHJcbkBrZXlmcmFtZXMgcHVsc2Uge1xyXG4gIDAlLCAxMDAlIHsgb3BhY2l0eTogMTsgfVxyXG4gIDUwJSB7IG9wYWNpdHk6IDAuNTsgfVxyXG59XHJcblxyXG4udGl0bGUtZGF0ZSB7XHJcbiAgZm9udC1zaXplOiAxNnB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA0MDA7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgbWFyZ2luLWxlZnQ6IDhweDtcclxufVxyXG5cclxuLmxvZ3MtY29udHJvbHMge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDEwcHg7XHJcbn1cclxuXHJcbi5hdXRvLXJlZnJlc2gtbGFiZWwge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDRweDtcclxuICBmb250LXNpemU6IDEzcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG59XHJcblxyXG4uYXV0by1yZWZyZXNoLWxhYmVsIGlucHV0W3R5cGU9XCJjaGVja2JveFwiXSB7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG59XHJcblxyXG4uZGF0ZS1zZWxlY3RvciB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGdhcDogNnB4O1xyXG59XHJcblxyXG4uZGF0ZS1sYWJlbCB7XHJcbiAgZm9udC1zaXplOiAxM3B4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG59XHJcblxyXG4uZGF0ZS1pbnB1dCB7XHJcbiAgcGFkZGluZzogNXB4IDEwcHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxuICBib3JkZXItcmFkaXVzOiA0cHg7XHJcbiAgZm9udC1zaXplOiAxM3B4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG4gIGN1cnNvcjogcG9pbnRlcjtcclxuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcclxufVxyXG5cclxuLmRhdGUtaW5wdXQ6aG92ZXIge1xyXG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcclxufVxyXG5cclxuLmRhdGUtaW5wdXQ6Zm9jdXMge1xyXG4gIG91dGxpbmU6IG5vbmU7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG4gIGJveC1zaGFkb3c6IDAgMCAwIDJweCByZ2JhKDI0LCAxNDQsIDI1NSwgMC4xKTtcclxufVxyXG5cclxuLnJlZnJlc2gtYnRuLFxyXG4uYmFjay1idG4ge1xyXG4gIHBhZGRpbmc6IDZweCAxMnB4O1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYmFja2dyb3VuZDogd2hpdGU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGN1cnNvcjogcG9pbnRlcjtcclxuICBmb250LXNpemU6IDEzcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XHJcbn1cclxuXHJcbi5yZWZyZXNoLWJ0bjpob3ZlcixcclxuLmJhY2stYnRuOmhvdmVyIHtcclxuICBib3JkZXItY29sb3I6ICMxODkwZmY7XHJcbiAgY29sb3I6ICMxODkwZmY7XHJcbn1cclxuXHJcblxyXG4uZXJyb3ItdGV4dCB7XHJcbiAgY29sb3I6ICNmZjRkNGY7XHJcbn1cclxuXHJcbi5wYXRoLWhpbnQge1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBjb2xvcjogIzk5OTtcclxuICBtYXJnaW4tbGVmdDogOHB4O1xyXG59XHJcblxyXG4uYXZhaWxhYmxlLWRhdGVzLWhpbnQge1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBjb2xvcjogIzk5OTtcclxuICBtYXJnaW4tbGVmdDogOHB4O1xyXG59XHJcblxyXG4vKiDlt6XkvZzmsYfmiqXljLrln58gKi9cclxuLnJlcG9ydC1zZWN0aW9uLWZ1bGwge1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlci1yYWRpdXM6IDhweDtcclxuICBwYWRkaW5nOiAxNnB4IDIwcHg7XHJcbiAgbWFyZ2luLWJvdHRvbTogMTZweDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xyXG59XHJcblxyXG4vKiDku6rooajnm5jluIPlsYAgKi9cclxuLnJlcG9ydC1kYXNoYm9hcmQge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZ2FwOiAzMnB4O1xyXG4gIGFsaWduLWl0ZW1zOiBmbGV4LXN0YXJ0O1xyXG59XHJcblxyXG4uZGFzaGJvYXJkLWdyb3VwIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbiAgZ2FwOiA4cHg7XHJcbn1cclxuXHJcbi5ncm91cC10aXRsZSB7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA1MDA7XHJcbiAgY29sb3I6ICM5OTk7XHJcbiAgdGV4dC10cmFuc2Zvcm06IHVwcGVyY2FzZTtcclxuICBsZXR0ZXItc3BhY2luZzogMC41cHg7XHJcbn1cclxuXHJcbi5zdGF0LXJvdyB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBnYXA6IDEycHg7XHJcbn1cclxuXHJcbi5zdGF0LWNhcmQge1xyXG4gIHBhZGRpbmc6IDEycHggMTZweDtcclxuICBib3JkZXItcmFkaXVzOiA2cHg7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIG1pbi13aWR0aDogODBweDtcclxufVxyXG5cclxuLnN0YXQtY2FyZC5zdGF0LXByaW1hcnkge1xyXG4gIGJhY2tncm91bmQ6IGxpbmVhci1ncmFkaWVudCgxMzVkZWcsICNlNmY0ZmYgMCUsICNmMGY3ZmYgMTAwJSk7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgIzkxY2FmZjtcclxufVxyXG5cclxuLnN0YXQtY2FyZC5zdGF0LXNlY29uZGFyeSB7XHJcbiAgYmFja2dyb3VuZDogI2Y2ZmZlZDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjYjdlYjhmO1xyXG59XHJcblxyXG4uc3RhdC1jYXJkLnN0YXQtaGlnaGxpZ2h0IHtcclxuICBiYWNrZ3JvdW5kOiBsaW5lYXItZ3JhZGllbnQoMTM1ZGVnLCAjZmZmN2U2IDAlLCAjZmZmYmU2IDEwMCUpO1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmQ1OTE7XHJcbn1cclxuXHJcbi5zdGF0LXZhbHVlIHtcclxuICBmb250LXNpemU6IDI0cHg7XHJcbiAgZm9udC13ZWlnaHQ6IDcwMDtcclxuICBsaW5lLWhlaWdodDogMTtcclxuICBtYXJnaW4tYm90dG9tOiA0cHg7XHJcbn1cclxuXHJcbi5zdGF0LXByaW1hcnkgLnN0YXQtdmFsdWUge1xyXG4gIGNvbG9yOiAjMTg5MGZmO1xyXG59XHJcblxyXG4uc3RhdC1zZWNvbmRhcnkgLnN0YXQtdmFsdWUge1xyXG4gIGNvbG9yOiAjNTJjNDFhO1xyXG59XHJcblxyXG4uc3RhdC1oaWdobGlnaHQgLnN0YXQtdmFsdWUge1xyXG4gIGNvbG9yOiAjZmE4YzE2O1xyXG59XHJcblxyXG4uc3RhdC1sYWJlbCB7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG59XHJcblxyXG4vKiDmnaXmupDmoIfnrb4gKi9cclxuLnNvdXJjZS10YWdzIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtd3JhcDogd3JhcDtcclxuICBnYXA6IDhweDtcclxufVxyXG5cclxuLnNvdXJjZS10YWcge1xyXG4gIGRpc3BsYXk6IGlubGluZS1mbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgZ2FwOiA2cHg7XHJcbiAgcGFkZGluZzogNnB4IDEycHg7XHJcbiAgYmFja2dyb3VuZDogI2ZhZmFmYTtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xyXG4gIGJvcmRlci1yYWRpdXM6IDE2cHg7XHJcbiAgZm9udC1zaXplOiAxM3B4O1xyXG59XHJcblxyXG4udGFnLW5hbWUge1xyXG4gIGNvbG9yOiAjNjY2O1xyXG59XHJcblxyXG4udGFnLWNvdW50IHtcclxuICBmb250LXdlaWdodDogNjAwO1xyXG4gIGNvbG9yOiAjMTg5MGZmO1xyXG4gIGJhY2tncm91bmQ6ICNlNmY0ZmY7XHJcbiAgcGFkZGluZzogMnB4IDhweDtcclxuICBib3JkZXItcmFkaXVzOiAxMHB4O1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxufVxyXG5cclxuLyog5bqV6YOo5Lik5qCP5biD5bGAICovXHJcbi5ib3R0b20tbGF5b3V0IHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGdhcDogMTZweDtcclxuICBmbGV4OiAxO1xyXG4gIG1pbi1oZWlnaHQ6IDA7XHJcbn1cclxuXHJcbi8qIOmihOiniOmdouadv+mAmueUqOagt+W8jyAqL1xyXG4ucHJldmlldy1wYW5lbCB7XHJcbiAgZmxleDogMTtcclxuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcclxuICBib3JkZXItcmFkaXVzOiA4cHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbiAgbWluLXdpZHRoOiAwO1xyXG4gIG92ZXJmbG93OiBoaWRkZW47XHJcbn1cclxuXHJcbi5kZWZpbml0aW9uLXByZXZpZXcge1xyXG4gIGZsZXg6IDAgMCA0NSU7XHJcbn1cclxuXHJcbi5sb2dzLXByZXZpZXcge1xyXG4gIGZsZXg6IDAgMCA1NSU7XHJcbn1cclxuXHJcbi5wcmV2aWV3LWhlYWRlciB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBwYWRkaW5nOiAxMnB4IDE2cHg7XHJcbiAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYmFja2dyb3VuZDogI2Y4ZjlmYTtcclxuICBmbGV4LXdyYXA6IHdyYXA7XHJcbiAgZ2FwOiA4cHg7XHJcbn1cclxuXHJcbi5wcmV2aWV3LWhlYWRlciBoMyB7XHJcbiAgZm9udC1zaXplOiAxNHB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA2MDA7XHJcbiAgY29sb3I6ICMxYTFhMWE7XHJcbiAgbWFyZ2luOiAwO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDEwcHg7XHJcbiAgZmxleC13cmFwOiB3cmFwO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLmRhdGUtc2VsZWN0b3Ige1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDZweDtcclxufVxyXG5cclxuLmxvZ3MtaGVhZGVyLWNvbnRyb2xzIC5kYXRlLWxhYmVsIHtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcclxufVxyXG5cclxuLmxvZ3MtaGVhZGVyLWNvbnRyb2xzIC5kYXRlLWlucHV0IHtcclxuICBwYWRkaW5nOiA0cHggOHB4O1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBjb2xvcjogIzY2NjtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XHJcbn1cclxuXHJcbi5sb2dzLWhlYWRlci1jb250cm9scyAuZGF0ZS1pbnB1dDpob3ZlciB7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLmRhdGUtaW5wdXQ6Zm9jdXMge1xyXG4gIG91dGxpbmU6IG5vbmU7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG4gIGJveC1zaGFkb3c6IDAgMCAwIDJweCByZ2JhKDI0LCAxNDQsIDI1NSwgMC4xKTtcclxufVxyXG5cclxuLmxvZ3MtaGVhZGVyLWNvbnRyb2xzIC5hdXRvLXJlZnJlc2gtbGFiZWwge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDRweDtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG4gIHdoaXRlLXNwYWNlOiBub3dyYXA7XHJcbn1cclxuXHJcbi5sb2dzLWhlYWRlci1jb250cm9scyAuYXV0by1yZWZyZXNoLWxhYmVsIGlucHV0W3R5cGU9XCJjaGVja2JveFwiXSB7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLnJlZnJlc2gtYnRuIHtcclxuICBwYWRkaW5nOiA0cHggMTJweDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlci1yYWRpdXM6IDRweDtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLnJlZnJlc2gtYnRuOmhvdmVyIHtcclxuICBib3JkZXItY29sb3I6ICMxODkwZmY7XHJcbiAgY29sb3I6ICMxODkwZmY7XHJcbn1cclxuXHJcbi5leHBhbmQtYnRuIHtcclxuICB3aWR0aDogMjhweDtcclxuICBoZWlnaHQ6IDI4cHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcclxuICBib3JkZXItcmFkaXVzOiA0cHg7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IGNlbnRlcjtcclxuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcclxuICBwYWRkaW5nOiAwO1xyXG59XHJcblxyXG4uZXhwYW5kLWJ0bjpob3ZlciB7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG4gIGJhY2tncm91bmQ6ICNmMGY3ZmY7XHJcbiAgY29sb3I6ICMxODkwZmY7XHJcbn1cclxuXHJcbi5leHBhbmQtYnRuIHN2ZyB7XHJcbiAgd2lkdGg6IDE2cHg7XHJcbiAgaGVpZ2h0OiAxNnB4O1xyXG4gIHN0cm9rZS13aWR0aDogMjtcclxufVxyXG5cclxuLnByZXZpZXctY29udGVudCB7XHJcbiAgZmxleDogMTtcclxuICBvdmVyZmxvdy15OiBhdXRvO1xyXG4gIHBhZGRpbmc6IDEycHggMTZweDtcclxuICBtaW4taGVpZ2h0OiAwO1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcge1xyXG4gIGxpbmUtaGVpZ2h0OiAxLjY7XHJcbiAgbWF4LWhlaWdodDogNDAwcHg7XHJcbiAgb3ZlcmZsb3cteTogYXV0bztcclxufVxyXG5cclxuLmxvZ3MtaW5mby1jb21wYWN0IHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGdhcDogMTZweDtcclxuICBwYWRkaW5nOiA2cHggMDtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgY29sb3I6ICM4ODg7XHJcbiAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkICNmMGYwZjA7XHJcbiAgbWFyZ2luLWJvdHRvbTogOHB4O1xyXG59XHJcblxyXG4ubG9nLWNvbnRlbnQtcHJldmlldyB7XHJcbiAgbWF4LWhlaWdodDogNDAwcHg7XHJcbiAgb3ZlcmZsb3cteTogYXV0bztcclxuICBwYWRkaW5nOiAxMHB4O1xyXG4gIGJhY2tncm91bmQ6ICMxZTFlMWU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGZvbnQtZmFtaWx5OiAnQ29uc29sYXMnLCAnTW9uYWNvJywgJ0NvdXJpZXIgTmV3JywgbW9ub3NwYWNlO1xyXG4gIGZvbnQtc2l6ZTogMTFweDtcclxuICBsaW5lLWhlaWdodDogMS40O1xyXG59XHJcblxyXG4ubG9nLXRleHQtcHJldmlldyB7XHJcbiAgbWFyZ2luOiAwO1xyXG4gIHdoaXRlLXNwYWNlOiBwcmUtd3JhcDtcclxuICB3b3JkLXdyYXA6IGJyZWFrLXdvcmQ7XHJcbiAgY29sb3I6ICNkNGQ0ZDQ7XHJcbiAgdHJhbnNpdGlvbjogb3BhY2l0eSAwLjJzO1xyXG59XHJcblxyXG4ubG9nLXRleHQtcHJldmlldy51cGRhdGluZyB7XHJcbiAgb3BhY2l0eTogMC43O1xyXG59XHJcblxyXG4ucmVwb3J0LWxvYWRpbmcsXHJcbi5yZXBvcnQtZW1wdHkge1xyXG4gIHRleHQtYWxpZ246IGNlbnRlcjtcclxuICBwYWRkaW5nOiA2MHB4IDIwcHg7XHJcbiAgY29sb3I6ICM4ODg7XHJcbiAgZm9udC1zaXplOiAxcmVtO1xyXG59XHJcblxyXG5cclxuLnJlcG9ydC1oZWFkZXIge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgbWFyZ2luLWJvdHRvbTogMDtcclxuICBwYWRkaW5nLWJvdHRvbTogMTZweDtcclxuICBib3JkZXItYm90dG9tOiAycHggc29saWQgI2UwZTBlMDtcclxufVxyXG5cclxuLnJlcG9ydC1oZWFkZXIgaDIge1xyXG4gIGZvbnQtc2l6ZTogMjRweDtcclxuICBmb250LXdlaWdodDogNjAwO1xyXG4gIGNvbG9yOiAjMWExYTFhO1xyXG4gIG1hcmdpbjogMDtcclxufVxyXG5cclxuLnJlcG9ydC1kYXRlIHtcclxuICBmb250LXNpemU6IDE2cHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgZm9udC13ZWlnaHQ6IDUwMDtcclxufVxyXG5cclxuLyog5bel5L2c5a6a5LmJ5qC35byP77yI6aKE6KeI5ZKM5YWo5bGP5YWx55So77yJICovXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtcHJldmlldyxcclxuLmRlZmluaXRpb24tY29udGVudC1mdWxsIHtcclxuICBsaW5lLWhlaWdodDogMS42O1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcgaDQsXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCBoNCB7XHJcbiAgZm9udC1zaXplOiAxNnB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA2MDA7XHJcbiAgY29sb3I6ICMxYTFhMWE7XHJcbiAgbWFyZ2luOiAxNnB4IDAgOHB4IDA7XHJcbn1cclxuXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtcHJldmlldyBoNDpmaXJzdC1jaGlsZCxcclxuLmRlZmluaXRpb24tY29udGVudC1mdWxsIGg0OmZpcnN0LWNoaWxkIHtcclxuICBtYXJnaW4tdG9wOiAwO1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcgb2wsXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtcHJldmlldyB1bCxcclxuLmRlZmluaXRpb24tY29udGVudC1mdWxsIG9sLFxyXG4uZGVmaW5pdGlvbi1jb250ZW50LWZ1bGwgdWwge1xyXG4gIG1hcmdpbjogOHB4IDA7XHJcbiAgcGFkZGluZy1sZWZ0OiAyNHB4O1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcgbGksXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCBsaSB7XHJcbiAgbWFyZ2luLWJvdHRvbTogOHB4O1xyXG4gIGxpbmUtaGVpZ2h0OiAxLjY7XHJcbiAgY29sb3I6ICM1NTU7XHJcbn1cclxuXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtcHJldmlldyBwLFxyXG4uZGVmaW5pdGlvbi1jb250ZW50LWZ1bGwgcCB7XHJcbiAgbWFyZ2luOiA4cHggMDtcclxuICBsaW5lLWhlaWdodDogMS42O1xyXG4gIGNvbG9yOiAjNTU1O1xyXG59XHJcblxyXG5cclxuLmRlZmluaXRpb24tbG9hZGluZyxcclxuLmRlZmluaXRpb24tZXJyb3Ige1xyXG4gIHBhZGRpbmc6IDIwcHg7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIGNvbG9yOiAjOTk5O1xyXG4gIGZvbnQtc2l6ZTogMTRweDtcclxufVxyXG5cclxuLmRlZmluaXRpb24tZXJyb3Ige1xyXG4gIGNvbG9yOiAjZmY0ZDRmO1xyXG59XHJcblxyXG4ucmVwb3J0LXN1bW1hcnkge1xyXG4gIG1hcmdpbi1ib3R0b206IDA7XHJcbiAgcGFkZGluZzogMDtcclxuICBiYWNrZ3JvdW5kOiB0cmFuc3BhcmVudDtcclxuICBib3JkZXI6IG5vbmU7XHJcbn1cclxuXHJcbi5yZXBvcnQtc3VtbWFyeSBoMyxcclxuLnJlcG9ydC1zZWN0aW9uIGgzIHtcclxuICBmb250LXNpemU6IDE2cHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzFhMWExYTtcclxuICBtYXJnaW46IDAgMCAxMnB4IDA7XHJcbn1cclxuXHJcbi5zdW1tYXJ5LWdyaWQge1xyXG4gIGRpc3BsYXk6IGdyaWQ7XHJcbiAgZ3JpZC10ZW1wbGF0ZS1jb2x1bW5zOiByZXBlYXQoMywgMWZyKTtcclxuICBnYXA6IDEycHg7XHJcbn1cclxuXHJcbi5zdW1tYXJ5LWNhcmQge1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xyXG4gIHBhZGRpbmc6IDE2cHg7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xyXG59XHJcblxyXG4uc3VtbWFyeS1jYXJkOmhvdmVyIHtcclxuICBib3gtc2hhZG93OiAwIDJweCA4cHggcmdiYSgwLCAwLCAwLCAwLjEpO1xyXG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcclxufVxyXG5cclxuLnN1bW1hcnktbGFiZWwge1xyXG4gIGZvbnQtc2l6ZTogMTRweDtcclxuICBjb2xvcjogIzY2NjtcclxuICBtYXJnaW4tYm90dG9tOiA4cHg7XHJcbn1cclxuXHJcbi5zdW1tYXJ5LXZhbHVlIHtcclxuICBmb250LXNpemU6IDMycHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzE4OTBmZjtcclxuICBtYXJnaW4tYm90dG9tOiA0cHg7XHJcbn1cclxuXHJcbi5zdW1tYXJ5LWRlc2Mge1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBjb2xvcjogIzk5OTtcclxufVxyXG5cclxuLnJlcG9ydC1zZWN0aW9uIHtcclxuICBtYXJnaW4tYm90dG9tOiAwO1xyXG4gIHBhZGRpbmc6IDE2cHg7XHJcbiAgYmFja2dyb3VuZDogI2Y4ZjlmYTtcclxuICBib3JkZXItcmFkaXVzOiA2cHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxufVxyXG5cclxuLnNvdXJjZS1saXN0IHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbiAgZ2FwOiA4cHg7XHJcbn1cclxuXHJcbi5zb3VyY2UtaXRlbSB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBwYWRkaW5nOiAxMHB4IDEycHg7XHJcbiAgYmFja2dyb3VuZDogd2hpdGU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbn1cclxuXHJcbi5zb3VyY2UtbmFtZSB7XHJcbiAgZm9udC1zaXplOiAxNHB4O1xyXG4gIGNvbG9yOiAjMzMzO1xyXG59XHJcblxyXG4uc291cmNlLWNvdW50IHtcclxuICBmb250LXNpemU6IDE0cHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzE4OTBmZjtcclxufVxyXG5cclxuLmFpLXN0YXRzIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGdhcDogMTJweDtcclxuICBmbGV4LXdyYXA6IHdyYXA7XHJcbn1cclxuXHJcbi5haS1zdGF0LWl0ZW0ge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcclxuICBwYWRkaW5nOiAxMnB4IDE2cHg7XHJcbiAgYmFja2dyb3VuZDogd2hpdGU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbn1cclxuXHJcbi5haS1sYWJlbCB7XHJcbiAgZm9udC1zaXplOiAxM3B4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG4gIG1hcmdpbi1ib3R0b206IDhweDtcclxufVxyXG5cclxuLmFpLXZhbHVlIHtcclxuICBmb250LXNpemU6IDI0cHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzE4OTBmZjtcclxufVxyXG5cclxuLmN1bXVsYXRpdmUtZ3JpZCB7XHJcbiAgZGlzcGxheTogZ3JpZDtcclxuICBncmlkLXRlbXBsYXRlLWNvbHVtbnM6IHJlcGVhdCgyLCAxZnIpO1xyXG4gIGdhcDogMTJweDtcclxufVxyXG5cclxuLmN1bXVsYXRpdmUtaXRlbSB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xyXG4gIHBhZGRpbmc6IDEycHg7XHJcbiAgYmFja2dyb3VuZDogd2hpdGU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbn1cclxuXHJcbi5jdW11bGF0aXZlLWxhYmVsIHtcclxuICBmb250LXNpemU6IDEzcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgbWFyZ2luLWJvdHRvbTogOHB4O1xyXG59XHJcblxyXG4uY3VtdWxhdGl2ZS12YWx1ZSB7XHJcbiAgZm9udC1zaXplOiAyNHB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA2MDA7XHJcbiAgY29sb3I6ICM1MmM0MWE7XHJcbn1cclxuXHJcbi5sb2dzLWluZm8ge1xyXG4gIG1hcmdpbi1ib3R0b206IDEycHg7XHJcbiAgcGFkZGluZzogMTJweCAxNnB4O1xyXG4gIGJhY2tncm91bmQ6ICNmNWY1ZjU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGZvbnQtc2l6ZTogMTNweDtcclxuICBjb2xvcjogIzY2NjtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtd3JhcDogd3JhcDtcclxuICBnYXA6IDEycHg7XHJcbn1cclxuXHJcbi5sb2ctbG9hZGluZyxcclxuLmxvZy1lbXB0eSB7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIHBhZGRpbmc6IDQwcHggMjBweDtcclxuICBjb2xvcjogIzg4ODtcclxufVxyXG5cclxuLmxvZy10ZXh0IHtcclxuICBtYXJnaW46IDA7XHJcbiAgd2hpdGUtc3BhY2U6IHByZS13cmFwO1xyXG4gIHdvcmQtd3JhcDogYnJlYWstd29yZDtcclxuICBjb2xvcjogIzMzMztcclxufVxyXG5cclxuLyog5qih5oCB5qGG5qC35byPICovXHJcbi5tb2RhbC1vdmVybGF5IHtcclxuICBwb3NpdGlvbjogZml4ZWQ7XHJcbiAgdG9wOiAwO1xyXG4gIGxlZnQ6IDA7XHJcbiAgcmlnaHQ6IDA7XHJcbiAgYm90dG9tOiAwO1xyXG4gIGJhY2tncm91bmQ6IHJnYmEoMCwgMCwgMCwgMC41KTtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XHJcbiAgei1pbmRleDogMTAwMDtcclxuICBwYWRkaW5nOiAyMHB4O1xyXG59XHJcblxyXG4ubW9kYWwtY29udGVudCB7XHJcbiAgYmFja2dyb3VuZDogd2hpdGU7XHJcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xyXG4gIG1heC13aWR0aDogOTAwcHg7XHJcbiAgd2lkdGg6IDEwMCU7XHJcbiAgbWF4LWhlaWdodDogOTB2aDtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbiAgYm94LXNoYWRvdzogMCA0cHggMjBweCByZ2JhKDAsIDAsIDAsIDAuMTUpO1xyXG59XHJcblxyXG4ubW9kYWwtY29udGVudC1sYXJnZSB7XHJcbiAgbWF4LXdpZHRoOiAxMjAwcHg7XHJcbn1cclxuXHJcbi5tb2RhbC1oZWFkZXIge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgcGFkZGluZzogMjBweCAyNHB4O1xyXG4gIGJvcmRlci1ib3R0b206IDFweCBzb2xpZCAjZTBlMGUwO1xyXG59XHJcblxyXG4ubW9kYWwtaGVhZGVyIGgyIHtcclxuICBmb250LXNpemU6IDIwcHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzFhMWExYTtcclxuICBtYXJnaW46IDA7XHJcbn1cclxuXHJcbi5tb2RhbC1oZWFkZXItcmlnaHQge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDE2cHg7XHJcbn1cclxuXHJcbi5sb2dzLWluZm8tbW9kYWwge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZ2FwOiAxMnB4O1xyXG4gIGZvbnQtc2l6ZTogMTNweDtcclxuICBjb2xvcjogIzY2NjtcclxufVxyXG5cclxuLm1vZGFsLWNsb3NlIHtcclxuICB3aWR0aDogMzJweDtcclxuICBoZWlnaHQ6IDMycHg7XHJcbiAgYm9yZGVyOiBub25lO1xyXG4gIGJhY2tncm91bmQ6IHRyYW5zcGFyZW50O1xyXG4gIGN1cnNvcjogcG9pbnRlcjtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xyXG4gIHBhZGRpbmc6IDA7XHJcbn1cclxuXHJcbi5tb2RhbC1jbG9zZTpob3ZlciB7XHJcbiAgYmFja2dyb3VuZDogI2Y1ZjVmNTtcclxufVxyXG5cclxuLm1vZGFsLWNsb3NlIHN2ZyB7XHJcbiAgd2lkdGg6IDIwcHg7XHJcbiAgaGVpZ2h0OiAyMHB4O1xyXG4gIHN0cm9rZS13aWR0aDogMjtcclxuICBjb2xvcjogIzY2NjtcclxufVxyXG5cclxuLm1vZGFsLWJvZHkge1xyXG4gIGZsZXg6IDE7XHJcbiAgb3ZlcmZsb3cteTogYXV0bztcclxuICBwYWRkaW5nOiAyNHB4O1xyXG4gIG1pbi1oZWlnaHQ6IDA7XHJcbn1cclxuXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCB7XHJcbiAgbGluZS1oZWlnaHQ6IDEuNjtcclxufVxyXG5cclxuLmxvZy1jb250ZW50LWZ1bGwge1xyXG4gIHBhZGRpbmc6IDEycHg7XHJcbiAgYmFja2dyb3VuZDogIzFlMWUxZTtcclxuICBib3JkZXItcmFkaXVzOiA0cHg7XHJcbiAgZm9udC1mYW1pbHk6ICdDb25zb2xhcycsICdNb25hY28nLCAnQ291cmllciBOZXcnLCBtb25vc3BhY2U7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGxpbmUtaGVpZ2h0OiAxLjQ7XHJcbiAgbWF4LWhlaWdodDogY2FsYyg5MHZoIC0gMTIwcHgpO1xyXG4gIG92ZXJmbG93LXk6IGF1dG87XHJcbn1cclxuXHJcbi5sb2ctdGV4dC1mdWxsIHtcclxuICBtYXJnaW46IDA7XHJcbiAgd2hpdGUtc3BhY2U6IHByZS13cmFwO1xyXG4gIHdvcmQtd3JhcDogYnJlYWstd29yZDtcclxuICBjb2xvcjogI2Q0ZDRkNDtcclxufVxyXG48L3N0eWxlPlxyXG5cclxuIl0sIm1hcHBpbmdzIjoiQUE4TEEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQ7Ozs7OztBQUxjO0FBTWQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQ7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQztBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QztBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEM7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkM7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25ELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQztBQUNGO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1YsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUM7QUFDRDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUM7QUFDRDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUM7QUFDRjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEYsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkUsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNWLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUM7QUFDRDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQztBQUNGO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENB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