import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/views/ZoeLogs.vue");import { ref, computed, onMounted, onUnmounted, watch } from "/node_modules/.vite/deps/vue.js?v=93b042e3"
import { useRouter } from "/node_modules/.vite/deps/vue-router.js?v=93b042e3"
import { API_BASE_URL } from "/src/utils/apiConfig.js"
import AppHeader from "/src/components/AppHeader.vue"


const _sfc_main = {
  __name: 'ZoeLogs',
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

// 统计数据
const statistics = ref(null)
const statisticsLoading = ref(false)
const dailyCompletedData = ref([]) // 每日完成数量数据

// 工作定义
const workDefinition = ref(null)
const workDefinitionLoading = ref(false)

// 模态框状态
const showDefinitionModal = ref(false)
const showLogsModal = ref(false)

// Zoe 视频 service 状态徽标 (复用 /api/zhihu/system-status, 跟 /system-status 页同一份数据源)
// 之所以不走老的 /api/video/status: status_video.txt 已升级成分层心跳 (顶层 phase + main + workers),
// 老接口只裸透传文件内容、不算 health, 前端按 status 字段判会永远拿 unknown 灰色.
const zoeStatus = ref(null)        // = systemStatus.services[zoe_video].heartbeat
const statusShownAlert = ref(false)

// health → 徽标三态. healthy/starting 算运行中; dead/stale/worker_stale 都算异常(红, 都需要人介入);
// stopped/unknown 灰. 保持跟 SystemStatus.vue 的 healthText 同语义.
const statusClass = computed(() => {
  if (!zoeStatus.value) return 'status-unknown'
  const h = zoeStatus.value.health
  if (h === 'healthy' || h === 'starting') return 'status-working'
  if (h === 'dead' || h === 'stale' || h === 'worker_stale') return 'status-dead'
  return 'status-unknown'
})

const statusText = computed(() => {
  if (!zoeStatus.value) return '未知'
  const h = zoeStatus.value.health
  if (h === 'healthy') return '运行中'
  if (h === 'starting') return '启动中'
  if (h === 'dead') return '已停止(异常)'
  if (h === 'stale') return '心跳掉线'
  if (h === 'worker_stale') return '子线程卡死'
  if (h === 'stopped') return '已停止'
  return '未知'
})

const showStatusDetail = () => {
  if (!zoeStatus.value) {
    alert('无法获取状态信息')
    return
  }
  const s = zoeStatus.value
  let msg = `状态: ${statusText.value}\n`
  if (s.start_time) msg += `启动时间: ${s.start_time}\n`
  if (s.last_update_time) msg += `最后心跳: ${s.last_update_time}\n`
  if (s.heartbeat_age_seconds != null) msg += `心跳距今: ${Math.round(s.heartbeat_age_seconds)}秒\n`
  if (s.pid) msg += `进程ID: ${s.pid}\n`
  if (s.error_message) msg += `错误信息: ${s.error_message}\n`
  if (s.message) msg += `说明: ${s.message}\n`
  // worker 卡死时把卡死的 worker 名字也带出来
  if (s.worker_issues && s.worker_issues.length) {
    const names = s.worker_issues.map((w) => w.name).join(', ')
    msg += `卡死子线程: ${names}\n`
  }
  alert(msg)
}

const fetchZoeStatus = async () => {
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/system-status`)
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        const services = (result.data && result.data.services) || []
        const videoSvc = services.find((s) => s.key === 'zoe_video')
        const heartbeat = videoSvc ? videoSvc.heartbeat : null
        zoeStatus.value = heartbeat
        // 只对真正异常 (dead) 才弹一次. stale/worker_stale 是软告警, 不打断用户.
        if (heartbeat && heartbeat.health === 'dead' && !statusShownAlert.value) {
          statusShownAlert.value = true
          const errorMsg = heartbeat.error_message ? `\n错误信息: ${heartbeat.error_message}` : ''
          alert(`Zoe 视频 service 已停止运行！${errorMsg}\n\n请检查并重新启动 zoe_video_service.py。`)
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
    const url = `${apiUrl}/api/video/logs?lines=1000&tail=true${dateParam ? `&date=${dateParam}` : ''}`
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

// 获取统计数据
const fetchStatistics = async () => {
  statisticsLoading.value = true
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/videos/statistics`)
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        statistics.value = result.data
        // 获取每日完成数量数据
        fetchDailyCompletedData()
      }
    }
  } catch (error) {
    console.error('获取统计信息出错:', error)
  } finally {
    statisticsLoading.value = false
  }
}

// 获取每日完成数量数据（最近30天）
const fetchDailyCompletedData = async () => {
  try {
    const apiUrl = API_BASE_URL
    const endDate = new Date()
    const startDate = new Date()
    startDate.setDate(startDate.getDate() - 29) // 最近30天
    
    // 生成日期范围
    const dates = []
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
      const dateStr = d.toISOString().split('T')[0]
      dates.push(dateStr)
    }
    
    // 初始化所有日期为0
    const dateCountMap = {}
    dates.forEach(date => {
      dateCountMap[date] = 0
    })
    
    // 一次性获取所有已完成的视频（分页获取）
    let page = 1
    let hasMore = true
    
    while (hasMore) {
      try {
        const response = await fetch(`${apiUrl}/api/zhihu/videos?page=${page}&page_size=100&video_status=completed&sort_by=video_completed_at`)
        if (response.ok) {
          const result = await response.json()
          if (result.code === 0 || result.code === 200) {
            const videos = result.data?.videos || []
            
            // 统计每天的完成数量
            videos.forEach(video => {
              if (video.video_completed_at) {
                const completedDate = new Date(video.video_completed_at).toISOString().split('T')[0]
                if (dateCountMap.hasOwnProperty(completedDate)) {
                  dateCountMap[completedDate]++
                }
              }
            })
            
            // 检查是否还有更多数据
            const pagination = result.data?.pagination
            if (pagination && page < pagination.total_pages) {
              page++
            } else {
              hasMore = false
            }
          } else {
            hasMore = false
          }
        } else {
          hasMore = false
        }
      } catch (error) {
        console.error(`获取第${page}页数据失败:`, error)
        hasMore = false
      }
    }
    
    // 转换为数组格式
    dailyCompletedData.value = dates.map(date => ({
      date: date,
      count: dateCountMap[date] || 0
    }))
  } catch (error) {
    console.error('获取每日完成数量数据出错:', error)
    dailyCompletedData.value = []
  }
}

// 计算今天完成的视频数量
const todayCompletedCount = computed(() => {
  if (!statistics.value) return 0
  // 从每日数据中获取今天的数据
  const today = new Date().toISOString().split('T')[0]
  const todayData = dailyCompletedData.value.find(item => item.date === today)
  return todayData ? todayData.count : 0
})

// 计算累计完成的视频数量
const totalCompletedCount = computed(() => {
  if (!statistics.value) return 0
  return statistics.value.completed || 0
})

// 计算柱状图的最大值（用于计算高度百分比）
const maxBarValue = computed(() => {
  if (dailyCompletedData.value.length === 0) return 1
  return Math.max(...dailyCompletedData.value.map(item => item.count), 1)
})

// 获取柱状图的高度百分比
const getBarHeight = (value) => {
  if (maxBarValue.value === 0) return 0
  return (value / maxBarValue.value) * 100
}

// 格式化图表日期（显示为 MM-DD）
const formatChartDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  return `${month}-${day}`
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
    const response = await fetch(`${apiUrl}/api/video/daily-report?date=${dateParam}`)
    
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
    const response = await fetch(`${apiUrl}/api/video/work-definition`)
    
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
  fetchZoeStatus()
  fetchStatistics()
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})

const __returned__ = { router, logs, logLoading, autoRefresh, logContent, logContentPreview, logContentFull, logInfo, get refreshTimer() { return refreshTimer }, set refreshTimer(v) { refreshTimer = v }, todayDate, selectedDate, dailyReport, reportLoading, statistics, statisticsLoading, dailyCompletedData, workDefinition, workDefinitionLoading, showDefinitionModal, showLogsModal, zoeStatus, statusShownAlert, statusClass, statusText, showStatusDetail, fetchZoeStatus, logText, logTextPreview, formatDateForApi, formatDisplayDate, fetchLogs, onDateChange, refreshLogs, fetchStatistics, fetchDailyCompletedData, todayCompletedCount, totalCompletedCount, maxBarValue, getBarHeight, formatChartDate, fetchDailyReport, fetchWorkDefinition, formatWorkDefinition, ref, computed, onMounted, onUnmounted, watch, get useRouter() { return useRouter }, get API_BASE_URL() { return API_BASE_URL }, AppHeader }
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true })
return __returned__
}

}
import { createVNode as _createVNode, toDisplayString as _toDisplayString, openBlock as _openBlock, createElementBlock as _createElementBlock, createCommentVNode as _createCommentVNode, createTextVNode as _createTextVNode, createElementVNode as _createElementVNode, normalizeClass as _normalizeClass, renderList as _renderList, Fragment as _Fragment, normalizeStyle as _normalizeStyle, vModelText as _vModelText, withDirectives as _withDirectives, vModelCheckbox as _vModelCheckbox, withModifiers as _withModifiers } from "/node_modules/.vite/deps/vue.js?v=93b042e3"

const _hoisted_1 = { class: "logs-page" }
const _hoisted_2 = { class: "logs-header" }
const _hoisted_3 = { class: "title-with-status" }
const _hoisted_4 = { class: "logs-title" }
const _hoisted_5 = {
  key: 0,
  class: "title-date"
}
const _hoisted_6 = { class: "status-text" }
const _hoisted_7 = {
  key: 0,
  class: "chart-title-header"
}
const _hoisted_8 = { class: "report-section-full" }
const _hoisted_9 = {
  key: 0,
  class: "report-loading"
}
const _hoisted_10 = {
  key: 1,
  class: "report-dashboard"
}
const _hoisted_11 = { class: "dashboard-group" }
const _hoisted_12 = { class: "stat-row" }
const _hoisted_13 = { class: "stat-card stat-primary" }
const _hoisted_14 = { class: "stat-value" }
const _hoisted_15 = { class: "stat-card stat-primary" }
const _hoisted_16 = { class: "stat-value" }
const _hoisted_17 = { class: "stat-card stat-primary" }
const _hoisted_18 = { class: "stat-value" }
const _hoisted_19 = { class: "dashboard-group" }
const _hoisted_20 = { class: "stat-row" }
const _hoisted_21 = { class: "stat-card stat-secondary" }
const _hoisted_22 = { class: "stat-value" }
const _hoisted_23 = { class: "stat-card stat-secondary" }
const _hoisted_24 = { class: "stat-value" }
const _hoisted_25 = { class: "stat-card stat-secondary" }
const _hoisted_26 = { class: "stat-value" }
const _hoisted_27 = {
  key: 2,
  class: "stats-dashboard"
}
const _hoisted_28 = { class: "stats-cards" }
const _hoisted_29 = { class: "stat-card-large" }
const _hoisted_30 = { class: "stat-card-content" }
const _hoisted_31 = { class: "stat-card-value" }
const _hoisted_32 = { class: "stat-card-large" }
const _hoisted_33 = { class: "stat-card-content" }
const _hoisted_34 = { class: "stat-card-value" }
const _hoisted_35 = { class: "chart-container" }
const _hoisted_36 = { class: "bar-chart" }
const _hoisted_37 = {
  key: 0,
  class: "chart-empty"
}
const _hoisted_38 = {
  key: 1,
  class: "chart-bars"
}
const _hoisted_39 = { class: "bar-wrapper" }
const _hoisted_40 = ["title"]
const _hoisted_41 = { class: "bar-label" }
const _hoisted_42 = { class: "bar-value" }
const _hoisted_43 = { class: "bottom-layout" }
const _hoisted_44 = { class: "preview-panel definition-preview" }
const _hoisted_45 = { class: "preview-header" }
const _hoisted_46 = { class: "preview-content" }
const _hoisted_47 = {
  key: 0,
  class: "definition-loading"
}
const _hoisted_48 = ["innerHTML"]
const _hoisted_49 = {
  key: 2,
  class: "definition-error"
}
const _hoisted_50 = { class: "preview-panel logs-preview" }
const _hoisted_51 = { class: "preview-header" }
const _hoisted_52 = { class: "logs-header-controls" }
const _hoisted_53 = { class: "date-selector" }
const _hoisted_54 = ["max"]
const _hoisted_55 = { class: "auto-refresh-label" }
const _hoisted_56 = { class: "preview-content" }
const _hoisted_57 = {
  key: 0,
  class: "logs-info-compact"
}
const _hoisted_58 = {
  key: 0,
  class: "error-text"
}
const _hoisted_59 = {
  class: "log-content-preview",
  ref: "logContentPreview"
}
const _hoisted_60 = {
  key: 0,
  class: "log-loading"
}
const _hoisted_61 = {
  key: 1,
  class: "log-empty"
}
const _hoisted_62 = { class: "modal-header" }
const _hoisted_63 = { class: "modal-body" }
const _hoisted_64 = {
  key: 0,
  class: "definition-loading"
}
const _hoisted_65 = ["innerHTML"]
const _hoisted_66 = {
  key: 2,
  class: "definition-error"
}
const _hoisted_67 = { class: "modal-header" }
const _hoisted_68 = { class: "modal-header-right" }
const _hoisted_69 = {
  key: 0,
  class: "logs-info-modal"
}
const _hoisted_70 = { class: "modal-body" }
const _hoisted_71 = {
  class: "log-content-full",
  ref: "logContentFull"
}
const _hoisted_72 = {
  key: 0,
  class: "log-loading"
}
const _hoisted_73 = {
  key: 1,
  class: "log-empty"
}
const _hoisted_74 = {
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
            _cache[10] || (_cache[10] = _createTextVNode("Zoe工作汇报", -1 /* CACHED */)),
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
        ]),
        (!$setup.dailyReport)
          ? (_openBlock(), _createElementBlock("div", _hoisted_7, [...(_cache[12] || (_cache[12] = [
              _createElementVNode("h2", { class: "chart-title-text" }, "每天制作完成的视频数量", -1 /* CACHED */)
            ]))]))
          : _createCommentVNode("v-if", true)
      ]),
      _createCommentVNode(" 工作汇报区域 "),
      _createElementVNode("div", _hoisted_8, [
        ($setup.reportLoading || $setup.statisticsLoading)
          ? (_openBlock(), _createElementBlock("div", _hoisted_9, "加载中..."))
          : ($setup.dailyReport)
            ? (_openBlock(), _createElementBlock("div", _hoisted_10, [
                _createCommentVNode(" 当日数据 "),
                _createElementVNode("div", _hoisted_11, [
                  _cache[16] || (_cache[16] = _createElementVNode("div", { class: "group-title" }, "当日工作", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_12, [
                    _createElementVNode("div", _hoisted_13, [
                      _createElementVNode("div", _hoisted_14, _toDisplayString($setup.dailyReport.summary.new_videos || 0), 1 /* TEXT */),
                      _cache[13] || (_cache[13] = _createElementVNode("div", { class: "stat-label" }, "新增视频", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_15, [
                      _createElementVNode("div", _hoisted_16, _toDisplayString($setup.dailyReport.summary.completed_videos || 0), 1 /* TEXT */),
                      _cache[14] || (_cache[14] = _createElementVNode("div", { class: "stat-label" }, "完成视频", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_17, [
                      _createElementVNode("div", _hoisted_18, _toDisplayString($setup.dailyReport.summary.failed_videos || 0), 1 /* TEXT */),
                      _cache[15] || (_cache[15] = _createElementVNode("div", { class: "stat-label" }, "失败视频", -1 /* CACHED */))
                    ])
                  ])
                ]),
                _createCommentVNode(" 累计数据 "),
                _createElementVNode("div", _hoisted_19, [
                  _cache[20] || (_cache[20] = _createElementVNode("div", { class: "group-title" }, "累计数据", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_20, [
                    _createElementVNode("div", _hoisted_21, [
                      _createElementVNode("div", _hoisted_22, _toDisplayString($setup.dailyReport.cumulative.total_videos || 0), 1 /* TEXT */),
                      _cache[17] || (_cache[17] = _createElementVNode("div", { class: "stat-label" }, "总视频", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_23, [
                      _createElementVNode("div", _hoisted_24, _toDisplayString($setup.dailyReport.cumulative.total_completed || 0), 1 /* TEXT */),
                      _cache[18] || (_cache[18] = _createElementVNode("div", { class: "stat-label" }, "已完成", -1 /* CACHED */))
                    ]),
                    _createElementVNode("div", _hoisted_25, [
                      _createElementVNode("div", _hoisted_26, _toDisplayString($setup.dailyReport.cumulative.total_published || 0), 1 /* TEXT */),
                      _cache[19] || (_cache[19] = _createElementVNode("div", { class: "stat-label" }, "已发布", -1 /* CACHED */))
                    ])
                  ])
                ])
              ]))
            : (_openBlock(), _createElementBlock("div", _hoisted_27, [
                _createCommentVNode(" 左侧：指标卡 "),
                _createElementVNode("div", _hoisted_28, [
                  _createElementVNode("div", _hoisted_29, [
                    _cache[22] || (_cache[22] = _createElementVNode("div", { class: "stat-card-icon" }, [
                      _createElementVNode("svg", {
                        viewBox: "0 0 24 24",
                        fill: "none",
                        stroke: "currentColor"
                      }, [
                        _createElementVNode("path", {
                          "stroke-linecap": "round",
                          "stroke-linejoin": "round",
                          "stroke-width": "2",
                          d: "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                        })
                      ])
                    ], -1 /* CACHED */)),
                    _createElementVNode("div", _hoisted_30, [
                      _createElementVNode("span", _hoisted_31, _toDisplayString($setup.todayCompletedCount), 1 /* TEXT */),
                      _cache[21] || (_cache[21] = _createElementVNode("span", { class: "stat-card-label" }, "今天完成的视频数量", -1 /* CACHED */))
                    ])
                  ]),
                  _createElementVNode("div", _hoisted_32, [
                    _cache[24] || (_cache[24] = _createElementVNode("div", { class: "stat-card-icon" }, [
                      _createElementVNode("svg", {
                        viewBox: "0 0 24 24",
                        fill: "none",
                        stroke: "currentColor"
                      }, [
                        _createElementVNode("path", {
                          "stroke-linecap": "round",
                          "stroke-linejoin": "round",
                          "stroke-width": "2",
                          d: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                        })
                      ])
                    ], -1 /* CACHED */)),
                    _createElementVNode("div", _hoisted_33, [
                      _createElementVNode("span", _hoisted_34, _toDisplayString($setup.totalCompletedCount), 1 /* TEXT */),
                      _cache[23] || (_cache[23] = _createElementVNode("span", { class: "stat-card-label" }, "累计完成的视频数量", -1 /* CACHED */))
                    ])
                  ])
                ]),
                _createCommentVNode(" 右侧：柱状图 "),
                _createElementVNode("div", _hoisted_35, [
                  _createElementVNode("div", _hoisted_36, [
                    ($setup.dailyCompletedData.length === 0)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_37, "暂无数据"))
                      : (_openBlock(), _createElementBlock("div", _hoisted_38, [
                          (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.dailyCompletedData, (item, index) => {
                            return (_openBlock(), _createElementBlock("div", {
                              key: index,
                              class: "chart-bar-item"
                            }, [
                              _createElementVNode("div", _hoisted_39, [
                                _createElementVNode("div", {
                                  class: "bar",
                                  style: _normalizeStyle({ height: `${$setup.getBarHeight(item.count)}%` }),
                                  title: `${item.date}: ${item.count}个`
                                }, null, 12 /* STYLE, PROPS */, _hoisted_40)
                              ]),
                              _createElementVNode("div", _hoisted_41, _toDisplayString($setup.formatChartDate(item.date)), 1 /* TEXT */),
                              _createElementVNode("div", _hoisted_42, _toDisplayString(item.count), 1 /* TEXT */)
                            ]))
                          }), 128 /* KEYED_FRAGMENT */))
                        ]))
                  ])
                ])
              ]))
      ]),
      _createCommentVNode(" 底部两栏布局 "),
      _createElementVNode("div", _hoisted_43, [
        _createCommentVNode(" 左侧：工作定义（预览） "),
        _createElementVNode("div", _hoisted_44, [
          _createElementVNode("div", _hoisted_45, [
            _cache[26] || (_cache[26] = _createElementVNode("h3", null, "Zoe 工作定义", -1 /* CACHED */)),
            _createElementVNode("button", {
              class: "expand-btn",
              onClick: _cache[0] || (_cache[0] = $event => ($setup.showDefinitionModal = true)),
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
          ]),
          _createElementVNode("div", _hoisted_46, [
            ($setup.workDefinitionLoading)
              ? (_openBlock(), _createElementBlock("div", _hoisted_47, "加载中..."))
              : ($setup.workDefinition)
                ? (_openBlock(), _createElementBlock("div", {
                    key: 1,
                    class: "definition-content-preview",
                    innerHTML: $setup.formatWorkDefinition($setup.workDefinition)
                  }, null, 8 /* PROPS */, _hoisted_48))
                : (_openBlock(), _createElementBlock("div", _hoisted_49, "无法加载工作定义"))
          ])
        ]),
        _createCommentVNode(" 右侧：工作日志（预览） "),
        _createElementVNode("div", _hoisted_50, [
          _createElementVNode("div", _hoisted_51, [
            _cache[30] || (_cache[30] = _createElementVNode("h3", null, "工作日志", -1 /* CACHED */)),
            _createElementVNode("div", _hoisted_52, [
              _createElementVNode("div", _hoisted_53, [
                _cache[27] || (_cache[27] = _createElementVNode("label", { class: "date-label" }, "选择日期：", -1 /* CACHED */)),
                _withDirectives(_createElementVNode("input", {
                  type: "date",
                  "onUpdate:modelValue": _cache[1] || (_cache[1] = $event => (($setup.selectedDate) = $event)),
                  onChange: $setup.onDateChange,
                  class: "date-input",
                  max: $setup.todayDate
                }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_54), [
                  [_vModelText, $setup.selectedDate]
                ])
              ]),
              _createElementVNode("label", _hoisted_55, [
                _withDirectives(_createElementVNode("input", {
                  type: "checkbox",
                  "onUpdate:modelValue": _cache[2] || (_cache[2] = $event => (($setup.autoRefresh) = $event))
                }, null, 512 /* NEED_PATCH */), [
                  [_vModelCheckbox, $setup.autoRefresh]
                ]),
                _cache[28] || (_cache[28] = _createTextVNode(" 自动刷新（5秒） ", -1 /* CACHED */))
              ]),
              _createElementVNode("button", {
                class: "refresh-btn",
                onClick: $setup.refreshLogs
              }, "刷新"),
              _createElementVNode("button", {
                class: "expand-btn",
                onClick: _cache[3] || (_cache[3] = $event => ($setup.showLogsModal = true)),
                title: "查看全部"
              }, [...(_cache[29] || (_cache[29] = [
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
          _createElementVNode("div", _hoisted_56, [
            ($setup.logInfo)
              ? (_openBlock(), _createElementBlock("div", _hoisted_57, [
                  _createElementVNode("span", null, "日期: " + _toDisplayString($setup.formatDisplayDate($setup.selectedDate)), 1 /* TEXT */),
                  _createElementVNode("span", null, "总行数: " + _toDisplayString($setup.logInfo.total_lines), 1 /* TEXT */),
                  (!$setup.logInfo.file_exists)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_58, "日志文件不存在"))
                    : _createCommentVNode("v-if", true)
                ]))
              : _createCommentVNode("v-if", true),
            _createElementVNode("div", _hoisted_59, [
              ($setup.logLoading && $setup.logs.length === 0)
                ? (_openBlock(), _createElementBlock("div", _hoisted_60, "加载中..."))
                : ($setup.logs.length === 0)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_61, "暂无日志"))
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
              _createElementVNode("div", _hoisted_62, [
                _cache[32] || (_cache[32] = _createElementVNode("h2", null, "Zoe 工作定义", -1 /* CACHED */)),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: _cache[4] || (_cache[4] = $event => ($setup.showDefinitionModal = false))
                }, [...(_cache[31] || (_cache[31] = [
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
              _createElementVNode("div", _hoisted_63, [
                ($setup.workDefinitionLoading)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_64, "加载中..."))
                  : ($setup.workDefinition)
                    ? (_openBlock(), _createElementBlock("div", {
                        key: 1,
                        class: "definition-content-full",
                        innerHTML: $setup.formatWorkDefinition($setup.workDefinition)
                      }, null, 8 /* PROPS */, _hoisted_65))
                    : (_openBlock(), _createElementBlock("div", _hoisted_66, "无法加载工作定义"))
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
              _createElementVNode("div", _hoisted_67, [
                _cache[34] || (_cache[34] = _createElementVNode("h2", null, "工作日志", -1 /* CACHED */)),
                _createElementVNode("div", _hoisted_68, [
                  ($setup.logInfo)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_69, [
                        _createElementVNode("span", null, "日期: " + _toDisplayString($setup.formatDisplayDate($setup.selectedDate)), 1 /* TEXT */),
                        _createElementVNode("span", null, "总行数: " + _toDisplayString($setup.logInfo.total_lines), 1 /* TEXT */),
                        _createElementVNode("span", null, "显示行数: " + _toDisplayString($setup.logInfo.returned_lines), 1 /* TEXT */)
                      ]))
                    : _createCommentVNode("v-if", true),
                  _createElementVNode("button", {
                    class: "modal-close",
                    onClick: _cache[7] || (_cache[7] = $event => ($setup.showLogsModal = false))
                  }, [...(_cache[33] || (_cache[33] = [
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
              _createElementVNode("div", _hoisted_70, [
                _createElementVNode("div", _hoisted_71, [
                  ($setup.logLoading)
                    ? (_openBlock(), _createElementBlock("div", _hoisted_72, "加载中..."))
                    : ($setup.logs.length === 0)
                      ? (_openBlock(), _createElementBlock("div", _hoisted_73, "暂无日志"))
                      : (_openBlock(), _createElementBlock("pre", _hoisted_74, _toDisplayString($setup.logText), 1 /* TEXT */))
                ], 512 /* NEED_PATCH */)
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true)
    ])
  ], 64 /* STABLE_FRAGMENT */))
}

import "/src/views/ZoeLogs.vue?vue&type=style&index=0&scoped=e81de20d&lang.css"

_sfc_main.__hmrId = "e81de20d"
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
export default /*#__PURE__*/_export_sfc(_sfc_main, [['render',_sfc_render],['__scopeId',"data-v-e81de20d"],['__file',"C:/WucaiMedia/client/src/views/ZoeLogs.vue"]])
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6W10sInNvdXJjZXMiOlsiWm9lTG9ncy52dWUiXSwic291cmNlc0NvbnRlbnQiOlsiPHRlbXBsYXRlPlxyXG4gIDxBcHBIZWFkZXIgLz5cclxuICA8ZGl2IGNsYXNzPVwibG9ncy1wYWdlXCI+XHJcbiAgICA8ZGl2IGNsYXNzPVwibG9ncy1oZWFkZXJcIj5cclxuICAgICAgPGRpdiBjbGFzcz1cInRpdGxlLXdpdGgtc3RhdHVzXCI+XHJcbiAgICAgICAgPGgxIGNsYXNzPVwibG9ncy10aXRsZVwiPlpvZeW3peS9nOaxh+aKpTxzcGFuIHYtaWY9XCJkYWlseVJlcG9ydFwiIGNsYXNzPVwidGl0bGUtZGF0ZVwiPu+8iHt7IGZvcm1hdERpc3BsYXlEYXRlKHNlbGVjdGVkRGF0ZSkgfX3vvIk8L3NwYW4+PC9oMT5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdHVzLWJhZGdlXCIgOmNsYXNzPVwic3RhdHVzQ2xhc3NcIiBAY2xpY2s9XCJzaG93U3RhdHVzRGV0YWlsXCI+XHJcbiAgICAgICAgICA8c3BhbiBjbGFzcz1cInN0YXR1cy1kb3RcIj48L3NwYW4+XHJcbiAgICAgICAgICA8c3BhbiBjbGFzcz1cInN0YXR1cy10ZXh0XCI+e3sgc3RhdHVzVGV4dCB9fTwvc3Bhbj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgPC9kaXY+XHJcbiAgICAgIDxkaXYgdi1pZj1cIiFkYWlseVJlcG9ydFwiIGNsYXNzPVwiY2hhcnQtdGl0bGUtaGVhZGVyXCI+XHJcbiAgICAgICAgPGgyIGNsYXNzPVwiY2hhcnQtdGl0bGUtdGV4dFwiPuavj+WkqeWItuS9nOWujOaIkOeahOinhumikeaVsOmHjzwvaDI+XHJcbiAgICAgIDwvZGl2PlxyXG4gICAgPC9kaXY+XHJcblxyXG4gICAgPCEtLSDlt6XkvZzmsYfmiqXljLrln58gLS0+XHJcbiAgICA8ZGl2IGNsYXNzPVwicmVwb3J0LXNlY3Rpb24tZnVsbFwiPlxyXG4gICAgICA8ZGl2IHYtaWY9XCJyZXBvcnRMb2FkaW5nIHx8IHN0YXRpc3RpY3NMb2FkaW5nXCIgY2xhc3M9XCJyZXBvcnQtbG9hZGluZ1wiPuWKoOi9veS4rS4uLjwvZGl2PlxyXG4gICAgICA8ZGl2IHYtZWxzZS1pZj1cImRhaWx5UmVwb3J0XCIgY2xhc3M9XCJyZXBvcnQtZGFzaGJvYXJkXCI+XHJcbiAgICAgICAgPCEtLSDlvZPml6XmlbDmja4gLS0+XHJcbiAgICAgICAgPGRpdiBjbGFzcz1cImRhc2hib2FyZC1ncm91cFwiPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cImdyb3VwLXRpdGxlXCI+5b2T5pel5bel5L2cPC9kaXY+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1yb3dcIj5cclxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtY2FyZCBzdGF0LXByaW1hcnlcIj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC12YWx1ZVwiPnt7IGRhaWx5UmVwb3J0LnN1bW1hcnkubmV3X3ZpZGVvcyB8fCAwIH19PC9kaXY+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtbGFiZWxcIj7mlrDlop7op4bpopE8L2Rpdj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWNhcmQgc3RhdC1wcmltYXJ5XCI+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtdmFsdWVcIj57eyBkYWlseVJlcG9ydC5zdW1tYXJ5LmNvbXBsZXRlZF92aWRlb3MgfHwgMCB9fTwvZGl2PlxyXG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWxhYmVsXCI+5a6M5oiQ6KeG6aKRPC9kaXY+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkIHN0YXQtcHJpbWFyeVwiPlxyXG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LXZhbHVlXCI+e3sgZGFpbHlSZXBvcnQuc3VtbWFyeS5mYWlsZWRfdmlkZW9zIHx8IDAgfX08L2Rpdj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1sYWJlbFwiPuWksei0peinhumikTwvZGl2PlxyXG4gICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG5cclxuICAgICAgICA8IS0tIOe0r+iuoeaVsOaNriAtLT5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwiZGFzaGJvYXJkLWdyb3VwXCI+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZ3JvdXAtdGl0bGVcIj7ntK/orqHmlbDmja48L2Rpdj5cclxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LXJvd1wiPlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkIHN0YXQtc2Vjb25kYXJ5XCI+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtdmFsdWVcIj57eyBkYWlseVJlcG9ydC5jdW11bGF0aXZlLnRvdGFsX3ZpZGVvcyB8fCAwIH19PC9kaXY+XHJcbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtbGFiZWxcIj7mgLvop4bpopE8L2Rpdj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWNhcmQgc3RhdC1zZWNvbmRhcnlcIj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC12YWx1ZVwiPnt7IGRhaWx5UmVwb3J0LmN1bXVsYXRpdmUudG90YWxfY29tcGxldGVkIHx8IDAgfX08L2Rpdj5cclxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1sYWJlbFwiPuW3suWujOaIkDwvZGl2PlxyXG4gICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtY2FyZCBzdGF0LXNlY29uZGFyeVwiPlxyXG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LXZhbHVlXCI+e3sgZGFpbHlSZXBvcnQuY3VtdWxhdGl2ZS50b3RhbF9wdWJsaXNoZWQgfHwgMCB9fTwvZGl2PlxyXG4gICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWxhYmVsXCI+5bey5Y+R5biDPC9kaXY+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgPC9kaXY+XHJcbiAgICAgIDwvZGl2PlxyXG4gICAgICA8ZGl2IHYtZWxzZSBjbGFzcz1cInN0YXRzLWRhc2hib2FyZFwiPlxyXG4gICAgICAgIDwhLS0g5bem5L6n77ya5oyH5qCH5Y2hIC0tPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0cy1jYXJkc1wiPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cInN0YXQtY2FyZC1sYXJnZVwiPlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkLWljb25cIj5cclxuICAgICAgICAgICAgICA8c3ZnIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiPlxyXG4gICAgICAgICAgICAgICAgPHBhdGggc3Ryb2tlLWxpbmVjYXA9XCJyb3VuZFwiIHN0cm9rZS1saW5lam9pbj1cInJvdW5kXCIgc3Ryb2tlLXdpZHRoPVwiMlwiIGQ9XCJNOSAxMmwyIDIgNC00bTYgMmE5IDkgMCAxMS0xOCAwIDkgOSAwIDAxMTggMHpcIi8+XHJcbiAgICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkLWNvbnRlbnRcIj5cclxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cInN0YXQtY2FyZC12YWx1ZVwiPnt7IHRvZGF5Q29tcGxldGVkQ291bnQgfX08L3NwYW4+XHJcbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJzdGF0LWNhcmQtbGFiZWxcIj7ku4rlpKnlrozmiJDnmoTop4bpopHmlbDph488L3NwYW4+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkLWxhcmdlXCI+XHJcbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJzdGF0LWNhcmQtaWNvblwiPlxyXG4gICAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XHJcbiAgICAgICAgICAgICAgICA8cGF0aCBzdHJva2UtbGluZWNhcD1cInJvdW5kXCIgc3Ryb2tlLWxpbmVqb2luPVwicm91bmRcIiBzdHJva2Utd2lkdGg9XCIyXCIgZD1cIk05IDE5di02YTIgMiAwIDAwLTItMkg1YTIgMiAwIDAwLTIgMnY2YTIgMiAwIDAwMiAyaDJhMiAyIDAgMDAyLTJ6bTAgMFY5YTIgMiAwIDAxMi0yaDJhMiAyIDAgMDEyIDJ2MTBtLTYgMGEyIDIgMCAwMDIgMmgyYTIgMiAwIDAwMi0ybTAgMFY1YTIgMiAwIDAxMi0yaDJhMiAyIDAgMDEyIDJ2MTRhMiAyIDAgMDEtMiAyaC0yYTIgMiAwIDAxLTItMnpcIi8+XHJcbiAgICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwic3RhdC1jYXJkLWNvbnRlbnRcIj5cclxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cInN0YXQtY2FyZC12YWx1ZVwiPnt7IHRvdGFsQ29tcGxldGVkQ291bnQgfX08L3NwYW4+XHJcbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJzdGF0LWNhcmQtbGFiZWxcIj7ntK/orqHlrozmiJDnmoTop4bpopHmlbDph488L3NwYW4+XHJcbiAgICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgPCEtLSDlj7PkvqfvvJrmn7Hnirblm74gLS0+XHJcbiAgICAgICAgPGRpdiBjbGFzcz1cImNoYXJ0LWNvbnRhaW5lclwiPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cImJhci1jaGFydFwiPlxyXG4gICAgICAgICAgICA8ZGl2IHYtaWY9XCJkYWlseUNvbXBsZXRlZERhdGEubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJjaGFydC1lbXB0eVwiPuaaguaXoOaVsOaNrjwvZGl2PlxyXG4gICAgICAgICAgICA8ZGl2IHYtZWxzZSBjbGFzcz1cImNoYXJ0LWJhcnNcIj5cclxuICAgICAgICAgICAgICA8ZGl2IHYtZm9yPVwiKGl0ZW0sIGluZGV4KSBpbiBkYWlseUNvbXBsZXRlZERhdGFcIiA6a2V5PVwiaW5kZXhcIiBjbGFzcz1cImNoYXJ0LWJhci1pdGVtXCI+XHJcbiAgICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwiYmFyLXdyYXBwZXJcIj5cclxuICAgICAgICAgICAgICAgICAgPGRpdiBcclxuICAgICAgICAgICAgICAgICAgICBjbGFzcz1cImJhclwiIFxyXG4gICAgICAgICAgICAgICAgICAgIDpzdHlsZT1cInsgaGVpZ2h0OiBgJHtnZXRCYXJIZWlnaHQoaXRlbS5jb3VudCl9JWAgfVwiXHJcbiAgICAgICAgICAgICAgICAgICAgOnRpdGxlPVwiYCR7aXRlbS5kYXRlfTogJHtpdGVtLmNvdW50feS4qmBcIlxyXG4gICAgICAgICAgICAgICAgICA+PC9kaXY+XHJcbiAgICAgICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJiYXItbGFiZWxcIj57eyBmb3JtYXRDaGFydERhdGUoaXRlbS5kYXRlKSB9fTwvZGl2PlxyXG4gICAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cImJhci12YWx1ZVwiPnt7IGl0ZW0uY291bnQgfX08L2Rpdj5cclxuICAgICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgPC9kaXY+XHJcbiAgICA8L2Rpdj5cclxuICAgIFxyXG4gICAgPCEtLSDlupXpg6jkuKTmoI/luIPlsYAgLS0+XHJcbiAgICA8ZGl2IGNsYXNzPVwiYm90dG9tLWxheW91dFwiPlxyXG4gICAgICA8IS0tIOW3puS+p++8muW3peS9nOWumuS5ie+8iOmihOiniO+8iSAtLT5cclxuICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctcGFuZWwgZGVmaW5pdGlvbi1wcmV2aWV3XCI+XHJcbiAgICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctaGVhZGVyXCI+XHJcbiAgICAgICAgICA8aDM+Wm9lIOW3peS9nOWumuS5iTwvaDM+XHJcbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiZXhwYW5kLWJ0blwiIEBjbGljaz1cInNob3dEZWZpbml0aW9uTW9kYWwgPSB0cnVlXCIgdGl0bGU9XCLmn6XnnIvlhajpg6hcIj5cclxuICAgICAgICAgICAgPHN2ZyB2aWV3Qm94PVwiMCAwIDI0IDI0XCIgZmlsbD1cIm5vbmVcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cclxuICAgICAgICAgICAgICA8cGF0aCBkPVwiTTggM0g1YTIgMiAwIDAgMC0yIDJ2M20xOCAwVjVhMiAyIDAgMCAwLTItMmgtM20wIDE4aDNhMiAyIDAgMCAwIDItMnYtM00zIDE2djNhMiAyIDAgMCAwIDIgMmgzXCIvPlxyXG4gICAgICAgICAgICA8L3N2Zz5cclxuICAgICAgICAgIDwvYnV0dG9uPlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJwcmV2aWV3LWNvbnRlbnRcIj5cclxuICAgICAgICAgIDxkaXYgdi1pZj1cIndvcmtEZWZpbml0aW9uTG9hZGluZ1wiIGNsYXNzPVwiZGVmaW5pdGlvbi1sb2FkaW5nXCI+5Yqg6L295LitLi4uPC9kaXY+XHJcbiAgICAgICAgICA8ZGl2IFxyXG4gICAgICAgICAgICB2LWVsc2UtaWY9XCJ3b3JrRGVmaW5pdGlvblwiIFxyXG4gICAgICAgICAgICBjbGFzcz1cImRlZmluaXRpb24tY29udGVudC1wcmV2aWV3XCIgXHJcbiAgICAgICAgICAgIHYtaHRtbD1cImZvcm1hdFdvcmtEZWZpbml0aW9uKHdvcmtEZWZpbml0aW9uKVwiXHJcbiAgICAgICAgICA+PC9kaXY+XHJcbiAgICAgICAgICA8ZGl2IHYtZWxzZSBjbGFzcz1cImRlZmluaXRpb24tZXJyb3JcIj7ml6Dms5XliqDovb3lt6XkvZzlrprkuYk8L2Rpdj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgPC9kaXY+XHJcbiAgICAgIFxyXG4gICAgICA8IS0tIOWPs+S+p++8muW3peS9nOaXpeW/l++8iOmihOiniO+8iSAtLT5cclxuICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctcGFuZWwgbG9ncy1wcmV2aWV3XCI+XHJcbiAgICAgICAgPGRpdiBjbGFzcz1cInByZXZpZXctaGVhZGVyXCI+XHJcbiAgICAgICAgICA8aDM+5bel5L2c5pel5b+XPC9oMz5cclxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJsb2dzLWhlYWRlci1jb250cm9sc1wiPlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwiZGF0ZS1zZWxlY3RvclwiPlxyXG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cImRhdGUtbGFiZWxcIj7pgInmi6nml6XmnJ/vvJo8L2xhYmVsPlxyXG4gICAgICAgICAgICAgIDxpbnB1dFxyXG4gICAgICAgICAgICAgICAgdHlwZT1cImRhdGVcIlxyXG4gICAgICAgICAgICAgICAgdi1tb2RlbD1cInNlbGVjdGVkRGF0ZVwiXHJcbiAgICAgICAgICAgICAgICBAY2hhbmdlPVwib25EYXRlQ2hhbmdlXCJcclxuICAgICAgICAgICAgICAgIGNsYXNzPVwiZGF0ZS1pbnB1dFwiXHJcbiAgICAgICAgICAgICAgICA6bWF4PVwidG9kYXlEYXRlXCJcclxuICAgICAgICAgICAgICAvPlxyXG4gICAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiYXV0by1yZWZyZXNoLWxhYmVsXCI+XHJcbiAgICAgICAgICAgICAgPGlucHV0IHR5cGU9XCJjaGVja2JveFwiIHYtbW9kZWw9XCJhdXRvUmVmcmVzaFwiIC8+XHJcbiAgICAgICAgICAgICAg6Ieq5Yqo5Yi35paw77yINeenku+8iVxyXG4gICAgICAgICAgICA8L2xhYmVsPlxyXG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwicmVmcmVzaC1idG5cIiBAY2xpY2s9XCJyZWZyZXNoTG9nc1wiPuWIt+aWsDwvYnV0dG9uPlxyXG4gICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImV4cGFuZC1idG5cIiBAY2xpY2s9XCJzaG93TG9nc01vZGFsID0gdHJ1ZVwiIHRpdGxlPVwi5p+l55yL5YWo6YOoXCI+XHJcbiAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XHJcbiAgICAgICAgICAgICAgPHBhdGggZD1cIk04IDNINWEyIDIgMCAwIDAtMiAydjNtMTggMFY1YTIgMiAwIDAgMC0yLTJoLTNtMCAxOGgzYTIgMiAwIDAgMCAyLTJ2LTNNMyAxNnYzYTIgMiAwIDAgMCAyIDJoM1wiLz5cclxuICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICA8L2J1dHRvbj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJwcmV2aWV3LWNvbnRlbnRcIj5cclxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJsb2dzLWluZm8tY29tcGFjdFwiIHYtaWY9XCJsb2dJbmZvXCI+XHJcbiAgICAgICAgICAgIDxzcGFuPuaXpeacnzoge3sgZm9ybWF0RGlzcGxheURhdGUoc2VsZWN0ZWREYXRlKSB9fTwvc3Bhbj5cclxuICAgICAgICAgICAgPHNwYW4+5oC76KGM5pWwOiB7eyBsb2dJbmZvLnRvdGFsX2xpbmVzIH19PC9zcGFuPlxyXG4gICAgICAgICAgICA8c3BhbiB2LWlmPVwiIWxvZ0luZm8uZmlsZV9leGlzdHNcIiBjbGFzcz1cImVycm9yLXRleHRcIj7ml6Xlv5fmlofku7bkuI3lrZjlnKg8L3NwYW4+XHJcbiAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJsb2ctY29udGVudC1wcmV2aWV3XCIgcmVmPVwibG9nQ29udGVudFByZXZpZXdcIj5cclxuICAgICAgICAgICAgPGRpdiB2LWlmPVwibG9nTG9hZGluZyAmJiBsb2dzLmxlbmd0aCA9PT0gMFwiIGNsYXNzPVwibG9nLWxvYWRpbmdcIj7liqDovb3kuK0uLi48L2Rpdj5cclxuICAgICAgICAgICAgPGRpdiB2LWVsc2UtaWY9XCJsb2dzLmxlbmd0aCA9PT0gMFwiIGNsYXNzPVwibG9nLWVtcHR5XCI+5pqC5peg5pel5b+XPC9kaXY+XHJcbiAgICAgICAgICAgIDxwcmUgdi1lbHNlIGNsYXNzPVwibG9nLXRleHQtcHJldmlld1wiIDpjbGFzcz1cInsgJ3VwZGF0aW5nJzogbG9nTG9hZGluZyB9XCI+e3sgbG9nVGV4dFByZXZpZXcgfX08L3ByZT5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICA8L2Rpdj5cclxuICAgIDwvZGl2PlxyXG4gICAgXHJcbiAgICA8IS0tIOW3peS9nOWumuS5ieWFqOWxj+aooeaAgeahhiAtLT5cclxuICAgIDxkaXYgdi1pZj1cInNob3dEZWZpbml0aW9uTW9kYWxcIiBjbGFzcz1cIm1vZGFsLW92ZXJsYXlcIiBAY2xpY2s9XCJzaG93RGVmaW5pdGlvbk1vZGFsID0gZmFsc2VcIj5cclxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnRcIiBAY2xpY2suc3RvcD5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtaGVhZGVyXCI+XHJcbiAgICAgICAgICA8aDI+Wm9lIOW3peS9nOWumuS5iTwvaDI+XHJcbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwibW9kYWwtY2xvc2VcIiBAY2xpY2s9XCJzaG93RGVmaW5pdGlvbk1vZGFsID0gZmFsc2VcIj5cclxuICAgICAgICAgICAgPHN2ZyB2aWV3Qm94PVwiMCAwIDI0IDI0XCIgZmlsbD1cIm5vbmVcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cclxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjE4XCIgeTE9XCI2XCIgeDI9XCI2XCIgeTI9XCIxOFwiLz5cclxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjZcIiB5MT1cIjZcIiB4Mj1cIjE4XCIgeTI9XCIxOFwiLz5cclxuICAgICAgICAgICAgPC9zdmc+XHJcbiAgICAgICAgICA8L2J1dHRvbj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtYm9keVwiPlxyXG4gICAgICAgICAgPGRpdiB2LWlmPVwid29ya0RlZmluaXRpb25Mb2FkaW5nXCIgY2xhc3M9XCJkZWZpbml0aW9uLWxvYWRpbmdcIj7liqDovb3kuK0uLi48L2Rpdj5cclxuICAgICAgICAgIDxkaXYgXHJcbiAgICAgICAgICAgIHYtZWxzZS1pZj1cIndvcmtEZWZpbml0aW9uXCIgXHJcbiAgICAgICAgICAgIGNsYXNzPVwiZGVmaW5pdGlvbi1jb250ZW50LWZ1bGxcIiBcclxuICAgICAgICAgICAgdi1odG1sPVwiZm9ybWF0V29ya0RlZmluaXRpb24od29ya0RlZmluaXRpb24pXCJcclxuICAgICAgICAgID48L2Rpdj5cclxuICAgICAgICAgIDxkaXYgdi1lbHNlIGNsYXNzPVwiZGVmaW5pdGlvbi1lcnJvclwiPuaXoOazleWKoOi9veW3peS9nOWumuS5iTwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICA8L2Rpdj5cclxuICAgIDwvZGl2PlxyXG4gICAgXHJcbiAgICA8IS0tIOW3peS9nOaXpeW/l+WFqOWxj+aooeaAgeahhiAtLT5cclxuICAgIDxkaXYgdi1pZj1cInNob3dMb2dzTW9kYWxcIiBjbGFzcz1cIm1vZGFsLW92ZXJsYXlcIiBAY2xpY2s9XCJzaG93TG9nc01vZGFsID0gZmFsc2VcIj5cclxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnQgbW9kYWwtY29udGVudC1sYXJnZVwiIEBjbGljay5zdG9wPlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1oZWFkZXJcIj5cclxuICAgICAgICAgIDxoMj7lt6XkvZzml6Xlv5c8L2gyPlxyXG4gICAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWhlYWRlci1yaWdodFwiPlxyXG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwibG9ncy1pbmZvLW1vZGFsXCIgdi1pZj1cImxvZ0luZm9cIj5cclxuICAgICAgICAgICAgICA8c3Bhbj7ml6XmnJ86IHt7IGZvcm1hdERpc3BsYXlEYXRlKHNlbGVjdGVkRGF0ZSkgfX08L3NwYW4+XHJcbiAgICAgICAgICAgICAgPHNwYW4+5oC76KGM5pWwOiB7eyBsb2dJbmZvLnRvdGFsX2xpbmVzIH19PC9zcGFuPlxyXG4gICAgICAgICAgICAgIDxzcGFuPuaYvuekuuihjOaVsDoge3sgbG9nSW5mby5yZXR1cm5lZF9saW5lcyB9fTwvc3Bhbj5cclxuICAgICAgICAgICAgPC9kaXY+XHJcbiAgICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cInNob3dMb2dzTW9kYWwgPSBmYWxzZVwiPlxyXG4gICAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XHJcbiAgICAgICAgICAgICAgICA8bGluZSB4MT1cIjE4XCIgeTE9XCI2XCIgeDI9XCI2XCIgeTI9XCIxOFwiLz5cclxuICAgICAgICAgICAgICAgIDxsaW5lIHgxPVwiNlwiIHkxPVwiNlwiIHgyPVwiMThcIiB5Mj1cIjE4XCIvPlxyXG4gICAgICAgICAgICAgIDwvc3ZnPlxyXG4gICAgICAgICAgICA8L2J1dHRvbj5cclxuICAgICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDwvZGl2PlxyXG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1ib2R5XCI+XHJcbiAgICAgICAgICA8ZGl2IGNsYXNzPVwibG9nLWNvbnRlbnQtZnVsbFwiIHJlZj1cImxvZ0NvbnRlbnRGdWxsXCI+XHJcbiAgICAgICAgICAgIDxkaXYgdi1pZj1cImxvZ0xvYWRpbmdcIiBjbGFzcz1cImxvZy1sb2FkaW5nXCI+5Yqg6L295LitLi4uPC9kaXY+XHJcbiAgICAgICAgICAgIDxkaXYgdi1lbHNlLWlmPVwibG9ncy5sZW5ndGggPT09IDBcIiBjbGFzcz1cImxvZy1lbXB0eVwiPuaaguaXoOaXpeW/lzwvZGl2PlxyXG4gICAgICAgICAgICA8cHJlIHYtZWxzZSBjbGFzcz1cImxvZy10ZXh0LWZ1bGxcIj57eyBsb2dUZXh0IH19PC9wcmU+XHJcbiAgICAgICAgICA8L2Rpdj5cclxuICAgICAgICA8L2Rpdj5cclxuICAgICAgPC9kaXY+XHJcbiAgICA8L2Rpdj5cclxuICA8L2Rpdj5cclxuPC90ZW1wbGF0ZT5cclxuXHJcbjxzY3JpcHQgc2V0dXA+XHJcbmltcG9ydCB7IHJlZiwgY29tcHV0ZWQsIG9uTW91bnRlZCwgb25Vbm1vdW50ZWQsIHdhdGNoIH0gZnJvbSAndnVlJ1xyXG5pbXBvcnQgeyB1c2VSb3V0ZXIgfSBmcm9tICd2dWUtcm91dGVyJ1xyXG5pbXBvcnQgeyBBUElfQkFTRV9VUkwgfSBmcm9tICcuLi91dGlscy9hcGlDb25maWcnXHJcbmltcG9ydCBBcHBIZWFkZXIgZnJvbSAnLi4vY29tcG9uZW50cy9BcHBIZWFkZXIudnVlJ1xyXG5cclxuY29uc3Qgcm91dGVyID0gdXNlUm91dGVyKClcclxuY29uc3QgbG9ncyA9IHJlZihbXSlcclxuY29uc3QgbG9nTG9hZGluZyA9IHJlZihmYWxzZSlcclxuY29uc3QgYXV0b1JlZnJlc2ggPSByZWYoZmFsc2UpXHJcbmNvbnN0IGxvZ0NvbnRlbnQgPSByZWYobnVsbClcclxuY29uc3QgbG9nQ29udGVudFByZXZpZXcgPSByZWYobnVsbClcclxuY29uc3QgbG9nQ29udGVudEZ1bGwgPSByZWYobnVsbClcclxuY29uc3QgbG9nSW5mbyA9IHJlZihudWxsKVxyXG5sZXQgcmVmcmVzaFRpbWVyID0gbnVsbFxyXG5cclxuLy8g5pel5pyf55u45YWzXHJcbmNvbnN0IHRvZGF5RGF0ZSA9IHJlZihuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCkuc3BsaXQoJ1QnKVswXSkgIC8vIFlZWVktTU0tRETmoLzlvI9cclxuY29uc3Qgc2VsZWN0ZWREYXRlID0gcmVmKHRvZGF5RGF0ZS52YWx1ZSkgIC8vIOm7mOiupOmAieaLqeS7iuWkqVxyXG5cclxuLy8g5bel5L2c5rGH5oqlXHJcbmNvbnN0IGRhaWx5UmVwb3J0ID0gcmVmKG51bGwpXHJcbmNvbnN0IHJlcG9ydExvYWRpbmcgPSByZWYoZmFsc2UpXHJcblxyXG4vLyDnu5/orqHmlbDmja5cclxuY29uc3Qgc3RhdGlzdGljcyA9IHJlZihudWxsKVxyXG5jb25zdCBzdGF0aXN0aWNzTG9hZGluZyA9IHJlZihmYWxzZSlcclxuY29uc3QgZGFpbHlDb21wbGV0ZWREYXRhID0gcmVmKFtdKSAvLyDmr4/ml6XlrozmiJDmlbDph4/mlbDmja5cclxuXHJcbi8vIOW3peS9nOWumuS5iVxyXG5jb25zdCB3b3JrRGVmaW5pdGlvbiA9IHJlZihudWxsKVxyXG5jb25zdCB3b3JrRGVmaW5pdGlvbkxvYWRpbmcgPSByZWYoZmFsc2UpXHJcblxyXG4vLyDmqKHmgIHmoYbnirbmgIFcclxuY29uc3Qgc2hvd0RlZmluaXRpb25Nb2RhbCA9IHJlZihmYWxzZSlcclxuY29uc3Qgc2hvd0xvZ3NNb2RhbCA9IHJlZihmYWxzZSlcclxuXHJcbi8vIFpvZSDop4bpopEgc2VydmljZSDnirbmgIHlvr3moIcgKOWkjeeUqCAvYXBpL3poaWh1L3N5c3RlbS1zdGF0dXMsIOi3nyAvc3lzdGVtLXN0YXR1cyDpobXlkIzkuIDku73mlbDmja7mupApXHJcbi8vIOS5i+aJgOS7peS4jei1sOiAgeeahCAvYXBpL3ZpZGVvL3N0YXR1czogc3RhdHVzX3ZpZGVvLnR4dCDlt7LljYfnuqfmiJDliIblsYLlv4Pot7MgKOmhtuWxgiBwaGFzZSArIG1haW4gKyB3b3JrZXJzKSxcclxuLy8g6ICB5o6l5Y+j5Y+q6KO46YCP5Lyg5paH5Lu25YaF5a6544CB5LiN566XIGhlYWx0aCwg5YmN56uv5oyJIHN0YXR1cyDlrZfmrrXliKTkvJrmsLjov5zmi78gdW5rbm93biDngbDoibIuXHJcbmNvbnN0IHpvZVN0YXR1cyA9IHJlZihudWxsKSAgICAgICAgLy8gPSBzeXN0ZW1TdGF0dXMuc2VydmljZXNbem9lX3ZpZGVvXS5oZWFydGJlYXRcclxuY29uc3Qgc3RhdHVzU2hvd25BbGVydCA9IHJlZihmYWxzZSlcclxuXHJcbi8vIGhlYWx0aCDihpIg5b695qCH5LiJ5oCBLiBoZWFsdGh5L3N0YXJ0aW5nIOeul+i/kOihjOS4rTsgZGVhZC9zdGFsZS93b3JrZXJfc3RhbGUg6YO9566X5byC5bi4KOe6oiwg6YO96ZyA6KaB5Lq65LuL5YWlKTtcclxuLy8gc3RvcHBlZC91bmtub3duIOeBsC4g5L+d5oyB6LefIFN5c3RlbVN0YXR1cy52dWUg55qEIGhlYWx0aFRleHQg5ZCM6K+t5LmJLlxyXG5jb25zdCBzdGF0dXNDbGFzcyA9IGNvbXB1dGVkKCgpID0+IHtcclxuICBpZiAoIXpvZVN0YXR1cy52YWx1ZSkgcmV0dXJuICdzdGF0dXMtdW5rbm93bidcclxuICBjb25zdCBoID0gem9lU3RhdHVzLnZhbHVlLmhlYWx0aFxyXG4gIGlmIChoID09PSAnaGVhbHRoeScgfHwgaCA9PT0gJ3N0YXJ0aW5nJykgcmV0dXJuICdzdGF0dXMtd29ya2luZydcclxuICBpZiAoaCA9PT0gJ2RlYWQnIHx8IGggPT09ICdzdGFsZScgfHwgaCA9PT0gJ3dvcmtlcl9zdGFsZScpIHJldHVybiAnc3RhdHVzLWRlYWQnXHJcbiAgcmV0dXJuICdzdGF0dXMtdW5rbm93bidcclxufSlcclxuXHJcbmNvbnN0IHN0YXR1c1RleHQgPSBjb21wdXRlZCgoKSA9PiB7XHJcbiAgaWYgKCF6b2VTdGF0dXMudmFsdWUpIHJldHVybiAn5pyq55+lJ1xyXG4gIGNvbnN0IGggPSB6b2VTdGF0dXMudmFsdWUuaGVhbHRoXHJcbiAgaWYgKGggPT09ICdoZWFsdGh5JykgcmV0dXJuICfov5DooYzkuK0nXHJcbiAgaWYgKGggPT09ICdzdGFydGluZycpIHJldHVybiAn5ZCv5Yqo5LitJ1xyXG4gIGlmIChoID09PSAnZGVhZCcpIHJldHVybiAn5bey5YGc5q2iKOW8guW4uCknXHJcbiAgaWYgKGggPT09ICdzdGFsZScpIHJldHVybiAn5b+D6Lez5o6J57q/J1xyXG4gIGlmIChoID09PSAnd29ya2VyX3N0YWxlJykgcmV0dXJuICflrZDnur/nqIvljaHmrbsnXHJcbiAgaWYgKGggPT09ICdzdG9wcGVkJykgcmV0dXJuICflt7LlgZzmraInXHJcbiAgcmV0dXJuICfmnKrnn6UnXHJcbn0pXHJcblxyXG5jb25zdCBzaG93U3RhdHVzRGV0YWlsID0gKCkgPT4ge1xyXG4gIGlmICghem9lU3RhdHVzLnZhbHVlKSB7XHJcbiAgICBhbGVydCgn5peg5rOV6I635Y+W54q25oCB5L+h5oGvJylcclxuICAgIHJldHVyblxyXG4gIH1cclxuICBjb25zdCBzID0gem9lU3RhdHVzLnZhbHVlXHJcbiAgbGV0IG1zZyA9IGDnirbmgIE6ICR7c3RhdHVzVGV4dC52YWx1ZX1cXG5gXHJcbiAgaWYgKHMuc3RhcnRfdGltZSkgbXNnICs9IGDlkK/liqjml7bpl7Q6ICR7cy5zdGFydF90aW1lfVxcbmBcclxuICBpZiAocy5sYXN0X3VwZGF0ZV90aW1lKSBtc2cgKz0gYOacgOWQjuW/g+i3szogJHtzLmxhc3RfdXBkYXRlX3RpbWV9XFxuYFxyXG4gIGlmIChzLmhlYXJ0YmVhdF9hZ2Vfc2Vjb25kcyAhPSBudWxsKSBtc2cgKz0gYOW/g+i3s+i3neS7ijogJHtNYXRoLnJvdW5kKHMuaGVhcnRiZWF0X2FnZV9zZWNvbmRzKX3np5JcXG5gXHJcbiAgaWYgKHMucGlkKSBtc2cgKz0gYOi/m+eoi0lEOiAke3MucGlkfVxcbmBcclxuICBpZiAocy5lcnJvcl9tZXNzYWdlKSBtc2cgKz0gYOmUmeivr+S/oeaBrzogJHtzLmVycm9yX21lc3NhZ2V9XFxuYFxyXG4gIGlmIChzLm1lc3NhZ2UpIG1zZyArPSBg6K+05piOOiAke3MubWVzc2FnZX1cXG5gXHJcbiAgLy8gd29ya2VyIOWNoeatu+aXtuaKiuWNoeatu+eahCB3b3JrZXIg5ZCN5a2X5Lmf5bim5Ye65p2lXHJcbiAgaWYgKHMud29ya2VyX2lzc3VlcyAmJiBzLndvcmtlcl9pc3N1ZXMubGVuZ3RoKSB7XHJcbiAgICBjb25zdCBuYW1lcyA9IHMud29ya2VyX2lzc3Vlcy5tYXAoKHcpID0+IHcubmFtZSkuam9pbignLCAnKVxyXG4gICAgbXNnICs9IGDljaHmrbvlrZDnur/nqIs6ICR7bmFtZXN9XFxuYFxyXG4gIH1cclxuICBhbGVydChtc2cpXHJcbn1cclxuXHJcbmNvbnN0IGZldGNoWm9lU3RhdHVzID0gYXN5bmMgKCkgPT4ge1xyXG4gIHRyeSB7XHJcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcclxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goYCR7YXBpVXJsfS9hcGkvemhpaHUvc3lzdGVtLXN0YXR1c2ApXHJcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcclxuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXHJcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XHJcbiAgICAgICAgY29uc3Qgc2VydmljZXMgPSAocmVzdWx0LmRhdGEgJiYgcmVzdWx0LmRhdGEuc2VydmljZXMpIHx8IFtdXHJcbiAgICAgICAgY29uc3QgdmlkZW9TdmMgPSBzZXJ2aWNlcy5maW5kKChzKSA9PiBzLmtleSA9PT0gJ3pvZV92aWRlbycpXHJcbiAgICAgICAgY29uc3QgaGVhcnRiZWF0ID0gdmlkZW9TdmMgPyB2aWRlb1N2Yy5oZWFydGJlYXQgOiBudWxsXHJcbiAgICAgICAgem9lU3RhdHVzLnZhbHVlID0gaGVhcnRiZWF0XHJcbiAgICAgICAgLy8g5Y+q5a+555yf5q2j5byC5bi4IChkZWFkKSDmiY3lvLnkuIDmrKEuIHN0YWxlL3dvcmtlcl9zdGFsZSDmmK/ova/lkYroraYsIOS4jeaJk+aWreeUqOaIty5cclxuICAgICAgICBpZiAoaGVhcnRiZWF0ICYmIGhlYXJ0YmVhdC5oZWFsdGggPT09ICdkZWFkJyAmJiAhc3RhdHVzU2hvd25BbGVydC52YWx1ZSkge1xyXG4gICAgICAgICAgc3RhdHVzU2hvd25BbGVydC52YWx1ZSA9IHRydWVcclxuICAgICAgICAgIGNvbnN0IGVycm9yTXNnID0gaGVhcnRiZWF0LmVycm9yX21lc3NhZ2UgPyBgXFxu6ZSZ6K+v5L+h5oGvOiAke2hlYXJ0YmVhdC5lcnJvcl9tZXNzYWdlfWAgOiAnJ1xyXG4gICAgICAgICAgYWxlcnQoYFpvZSDop4bpopEgc2VydmljZSDlt7LlgZzmraLov5DooYzvvIEke2Vycm9yTXNnfVxcblxcbuivt+ajgOafpeW5tumHjeaWsOWQr+WKqCB6b2VfdmlkZW9fc2VydmljZS5weeOAgmApXHJcbiAgICAgICAgfVxyXG4gICAgICB9XHJcbiAgICB9XHJcbiAgfSBjYXRjaCAoZXJyb3IpIHtcclxuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPlueKtuaAgeWksei0pTonLCBlcnJvcilcclxuICB9XHJcbn1cclxuXHJcbmNvbnN0IGxvZ1RleHQgPSBjb21wdXRlZCgoKSA9PiB7XHJcbiAgcmV0dXJuIGxvZ3MudmFsdWUuam9pbignXFxuJylcclxufSlcclxuXHJcbi8vIOmihOiniOaooeW8j+eahOaXpeW/l+aWh+acrO+8iOWPquaYvuekuuacgOWQjjIwMOihjO+8iVxyXG5jb25zdCBsb2dUZXh0UHJldmlldyA9IGNvbXB1dGVkKCgpID0+IHtcclxuICBpZiAobG9ncy52YWx1ZS5sZW5ndGggPD0gMjAwKSB7XHJcbiAgICByZXR1cm4gbG9ncy52YWx1ZS5qb2luKCdcXG4nKVxyXG4gIH1cclxuICByZXR1cm4gbG9ncy52YWx1ZS5zbGljZSgtMjAwKS5qb2luKCdcXG4nKVxyXG59KVxyXG5cclxuLy8g5bCG5pel5pyf5qC85byP5LuOIFlZWVktTU0tREQg6L2s5o2i5Li6IFlZWVlNTUREXHJcbmNvbnN0IGZvcm1hdERhdGVGb3JBcGkgPSAoZGF0ZVN0cikgPT4ge1xyXG4gIGlmICghZGF0ZVN0cikgcmV0dXJuIG51bGxcclxuICByZXR1cm4gZGF0ZVN0ci5yZXBsYWNlKC8tL2csICcnKVxyXG59XHJcblxyXG4vLyDmoLzlvI/ljJbmmL7npLrml6XmnJ9cclxuY29uc3QgZm9ybWF0RGlzcGxheURhdGUgPSAoZGF0ZVN0cikgPT4ge1xyXG4gIGlmICghZGF0ZVN0cikgcmV0dXJuICcnXHJcbiAgY29uc3QgZGF0ZSA9IG5ldyBEYXRlKGRhdGVTdHIpXHJcbiAgY29uc3QgeWVhciA9IGRhdGUuZ2V0RnVsbFllYXIoKVxyXG4gIGNvbnN0IG1vbnRoID0gKGRhdGUuZ2V0TW9udGgoKSArIDEpLnRvU3RyaW5nKCkucGFkU3RhcnQoMiwgJzAnKVxyXG4gIGNvbnN0IGRheSA9IGRhdGUuZ2V0RGF0ZSgpLnRvU3RyaW5nKCkucGFkU3RhcnQoMiwgJzAnKVxyXG4gIHJldHVybiBgJHt5ZWFyfeW5tCR7bW9udGh95pyIJHtkYXl95pelYFxyXG59XHJcblxyXG4vLyDojrflj5bml6Xlv5dcclxuY29uc3QgZmV0Y2hMb2dzID0gYXN5bmMgKHNob3dMb2FkaW5nID0gdHJ1ZSkgPT4ge1xyXG4gIC8vIOWPquacieWcqOmcgOimgeaYvuekumxvYWRpbmfml7bmiY3orr7nva5sb2FkaW5n54q25oCB77yM6YG/5YWN5LiN5b+F6KaB55qE6Zeq5YqoXHJcbiAgaWYgKHNob3dMb2FkaW5nKSB7XHJcbiAgbG9nTG9hZGluZy52YWx1ZSA9IHRydWVcclxuICB9XHJcbiAgdHJ5IHtcclxuICAgIGNvbnN0IGFwaVVybCA9IEFQSV9CQVNFX1VSTFxyXG4gICAgY29uc3QgZGF0ZVBhcmFtID0gZm9ybWF0RGF0ZUZvckFwaShzZWxlY3RlZERhdGUudmFsdWUpXHJcbiAgICBjb25zdCB1cmwgPSBgJHthcGlVcmx9L2FwaS92aWRlby9sb2dzP2xpbmVzPTEwMDAmdGFpbD10cnVlJHtkYXRlUGFyYW0gPyBgJmRhdGU9JHtkYXRlUGFyYW19YCA6ICcnfWBcclxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2godXJsKVxyXG4gICAgXHJcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcclxuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXHJcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XHJcbiAgICAgICAgLy8g55u05o6l5pu05paw5pWw5o2u77yM6YG/5YWN5YWI5riF56m65YaN6K6+572u5a+86Ie055qE6Zeq5YqoXHJcbiAgICAgICAgY29uc3QgbmV3TG9ncyA9IHJlc3VsdC5kYXRhLmxvZ3MgfHwgW11cclxuICAgICAgICBjb25zdCBuZXdMb2dJbmZvID0ge1xyXG4gICAgICAgICAgdG90YWxfbGluZXM6IHJlc3VsdC5kYXRhLnRvdGFsX2xpbmVzIHx8IDAsXHJcbiAgICAgICAgICByZXR1cm5lZF9saW5lczogcmVzdWx0LmRhdGEucmV0dXJuZWRfbGluZXMgfHwgMCxcclxuICAgICAgICAgIGZpbGVfZXhpc3RzOiByZXN1bHQuZGF0YS5maWxlX2V4aXN0cyAhPT0gZmFsc2UsXHJcbiAgICAgICAgICBsb2dfcGF0aDogcmVzdWx0LmRhdGEubG9nX3BhdGggfHwgJycsXHJcbiAgICAgICAgICBkYXRlOiByZXN1bHQuZGF0YS5kYXRlIHx8IGZvcm1hdERhdGVGb3JBcGkoc2VsZWN0ZWREYXRlLnZhbHVlKSxcclxuICAgICAgICAgIGF2YWlsYWJsZV9kYXRlczogcmVzdWx0LmRhdGEuYXZhaWxhYmxlX2RhdGVzIHx8IFtdXHJcbiAgICAgICAgfVxyXG4gICAgICAgIFxyXG4gICAgICAgIC8vIOaJuemHj+abtOaWsO+8jOWHj+WwkemHjeaWsOa4suafk+asoeaVsFxyXG4gICAgICAgIGxvZ3MudmFsdWUgPSBuZXdMb2dzXHJcbiAgICAgICAgbG9nSW5mby52YWx1ZSA9IG5ld0xvZ0luZm9cclxuICAgICAgICBcclxuICAgICAgICAvLyDmu5rliqjliLDlupXpg6jvvIjpooTop4jljLrln5/vvIlcclxuICAgICAgICBpZiAobG9nQ29udGVudFByZXZpZXcudmFsdWUpIHtcclxuICAgICAgICAgIHNldFRpbWVvdXQoKCkgPT4ge1xyXG4gICAgICAgICAgICBsb2dDb250ZW50UHJldmlldy52YWx1ZS5zY3JvbGxUb3AgPSBsb2dDb250ZW50UHJldmlldy52YWx1ZS5zY3JvbGxIZWlnaHRcclxuICAgICAgICAgIH0sIDEwMClcclxuICAgICAgICB9XHJcbiAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgY29uc29sZS5lcnJvcign6I635Y+W5pel5b+X5aSx6LSlOicsIHJlc3VsdC5tc2cgfHwgcmVzdWx0Lm1lc3NhZ2UpXHJcbiAgICAgICAgbG9ncy52YWx1ZSA9IFtdXHJcbiAgICAgICAgbG9nSW5mby52YWx1ZSA9IHtcclxuICAgICAgICAgIHRvdGFsX2xpbmVzOiAwLFxyXG4gICAgICAgICAgcmV0dXJuZWRfbGluZXM6IDAsXHJcbiAgICAgICAgICBmaWxlX2V4aXN0czogZmFsc2UsXHJcbiAgICAgICAgICBsb2dfcGF0aDogJycsXHJcbiAgICAgICAgICBkYXRlOiBmb3JtYXREYXRlRm9yQXBpKHNlbGVjdGVkRGF0ZS52YWx1ZSksXHJcbiAgICAgICAgICBhdmFpbGFibGVfZGF0ZXM6IHJlc3VsdC5kYXRhPy5hdmFpbGFibGVfZGF0ZXMgfHwgW11cclxuICAgICAgICB9XHJcbiAgICAgIH1cclxuICAgIH0gZWxzZSB7XHJcbiAgICAgIGNvbnNvbGUuZXJyb3IoJ0FQSSDor7fmsYLlpLHotKU6JywgcmVzcG9uc2Uuc3RhdHVzKVxyXG4gICAgICBsb2dzLnZhbHVlID0gW11cclxuICAgIH1cclxuICB9IGNhdGNoIChlcnJvcikge1xyXG4gICAgY29uc29sZS5lcnJvcign6I635Y+W5pel5b+X5Ye66ZSZOicsIGVycm9yKVxyXG4gICAgbG9ncy52YWx1ZSA9IFtdXHJcbiAgfSBmaW5hbGx5IHtcclxuICAgIGlmIChzaG93TG9hZGluZykge1xyXG4gICAgbG9nTG9hZGluZy52YWx1ZSA9IGZhbHNlXHJcbiAgICB9XHJcbiAgfVxyXG59XHJcblxyXG4vLyDml6XmnJ/lj5jljJblpITnkIbvvIjlj6rliLfmlrDml6Xlv5fvvIlcclxuY29uc3Qgb25EYXRlQ2hhbmdlID0gKCkgPT4ge1xyXG4gIC8vIOWBnOatouiHquWKqOWIt+aWsO+8iOWIh+aNouaXpeacn+aXtu+8iVxyXG4gIGF1dG9SZWZyZXNoLnZhbHVlID0gZmFsc2VcclxuICBmZXRjaExvZ3MoKVxyXG59XHJcblxyXG4vLyDliLfmlrDml6Xlv5fmlbDmja5cclxuY29uc3QgcmVmcmVzaExvZ3MgPSAoKSA9PiB7XHJcbiAgZmV0Y2hMb2dzKClcclxufVxyXG5cclxuLy8g6I635Y+W57uf6K6h5pWw5o2uXHJcbmNvbnN0IGZldGNoU3RhdGlzdGljcyA9IGFzeW5jICgpID0+IHtcclxuICBzdGF0aXN0aWNzTG9hZGluZy52YWx1ZSA9IHRydWVcclxuICB0cnkge1xyXG4gICAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXHJcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L3ZpZGVvcy9zdGF0aXN0aWNzYClcclxuICAgIFxyXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XHJcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxyXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xyXG4gICAgICAgIHN0YXRpc3RpY3MudmFsdWUgPSByZXN1bHQuZGF0YVxyXG4gICAgICAgIC8vIOiOt+WPluavj+aXpeWujOaIkOaVsOmHj+aVsOaNrlxyXG4gICAgICAgIGZldGNoRGFpbHlDb21wbGV0ZWREYXRhKClcclxuICAgICAgfVxyXG4gICAgfVxyXG4gIH0gY2F0Y2ggKGVycm9yKSB7XHJcbiAgICBjb25zb2xlLmVycm9yKCfojrflj5bnu5/orqHkv6Hmga/lh7rplJk6JywgZXJyb3IpXHJcbiAgfSBmaW5hbGx5IHtcclxuICAgIHN0YXRpc3RpY3NMb2FkaW5nLnZhbHVlID0gZmFsc2VcclxuICB9XHJcbn1cclxuXHJcbi8vIOiOt+WPluavj+aXpeWujOaIkOaVsOmHj+aVsOaNru+8iOacgOi/kTMw5aSp77yJXHJcbmNvbnN0IGZldGNoRGFpbHlDb21wbGV0ZWREYXRhID0gYXN5bmMgKCkgPT4ge1xyXG4gIHRyeSB7XHJcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcclxuICAgIGNvbnN0IGVuZERhdGUgPSBuZXcgRGF0ZSgpXHJcbiAgICBjb25zdCBzdGFydERhdGUgPSBuZXcgRGF0ZSgpXHJcbiAgICBzdGFydERhdGUuc2V0RGF0ZShzdGFydERhdGUuZ2V0RGF0ZSgpIC0gMjkpIC8vIOacgOi/kTMw5aSpXHJcbiAgICBcclxuICAgIC8vIOeUn+aIkOaXpeacn+iMg+WbtFxyXG4gICAgY29uc3QgZGF0ZXMgPSBbXVxyXG4gICAgZm9yIChsZXQgZCA9IG5ldyBEYXRlKHN0YXJ0RGF0ZSk7IGQgPD0gZW5kRGF0ZTsgZC5zZXREYXRlKGQuZ2V0RGF0ZSgpICsgMSkpIHtcclxuICAgICAgY29uc3QgZGF0ZVN0ciA9IGQudG9JU09TdHJpbmcoKS5zcGxpdCgnVCcpWzBdXHJcbiAgICAgIGRhdGVzLnB1c2goZGF0ZVN0cilcclxuICAgIH1cclxuICAgIFxyXG4gICAgLy8g5Yid5aeL5YyW5omA5pyJ5pel5pyf5Li6MFxyXG4gICAgY29uc3QgZGF0ZUNvdW50TWFwID0ge31cclxuICAgIGRhdGVzLmZvckVhY2goZGF0ZSA9PiB7XHJcbiAgICAgIGRhdGVDb3VudE1hcFtkYXRlXSA9IDBcclxuICAgIH0pXHJcbiAgICBcclxuICAgIC8vIOS4gOasoeaAp+iOt+WPluaJgOacieW3suWujOaIkOeahOinhumike+8iOWIhumhteiOt+WPlu+8iVxyXG4gICAgbGV0IHBhZ2UgPSAxXHJcbiAgICBsZXQgaGFzTW9yZSA9IHRydWVcclxuICAgIFxyXG4gICAgd2hpbGUgKGhhc01vcmUpIHtcclxuICAgICAgdHJ5IHtcclxuICAgICAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L3ZpZGVvcz9wYWdlPSR7cGFnZX0mcGFnZV9zaXplPTEwMCZ2aWRlb19zdGF0dXM9Y29tcGxldGVkJnNvcnRfYnk9dmlkZW9fY29tcGxldGVkX2F0YClcclxuICAgICAgICBpZiAocmVzcG9uc2Uub2spIHtcclxuICAgICAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxyXG4gICAgICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcclxuICAgICAgICAgICAgY29uc3QgdmlkZW9zID0gcmVzdWx0LmRhdGE/LnZpZGVvcyB8fCBbXVxyXG4gICAgICAgICAgICBcclxuICAgICAgICAgICAgLy8g57uf6K6h5q+P5aSp55qE5a6M5oiQ5pWw6YePXHJcbiAgICAgICAgICAgIHZpZGVvcy5mb3JFYWNoKHZpZGVvID0+IHtcclxuICAgICAgICAgICAgICBpZiAodmlkZW8udmlkZW9fY29tcGxldGVkX2F0KSB7XHJcbiAgICAgICAgICAgICAgICBjb25zdCBjb21wbGV0ZWREYXRlID0gbmV3IERhdGUodmlkZW8udmlkZW9fY29tcGxldGVkX2F0KS50b0lTT1N0cmluZygpLnNwbGl0KCdUJylbMF1cclxuICAgICAgICAgICAgICAgIGlmIChkYXRlQ291bnRNYXAuaGFzT3duUHJvcGVydHkoY29tcGxldGVkRGF0ZSkpIHtcclxuICAgICAgICAgICAgICAgICAgZGF0ZUNvdW50TWFwW2NvbXBsZXRlZERhdGVdKytcclxuICAgICAgICAgICAgICAgIH1cclxuICAgICAgICAgICAgICB9XHJcbiAgICAgICAgICAgIH0pXHJcbiAgICAgICAgICAgIFxyXG4gICAgICAgICAgICAvLyDmo4Dmn6XmmK/lkKbov5jmnInmm7TlpJrmlbDmja5cclxuICAgICAgICAgICAgY29uc3QgcGFnaW5hdGlvbiA9IHJlc3VsdC5kYXRhPy5wYWdpbmF0aW9uXHJcbiAgICAgICAgICAgIGlmIChwYWdpbmF0aW9uICYmIHBhZ2UgPCBwYWdpbmF0aW9uLnRvdGFsX3BhZ2VzKSB7XHJcbiAgICAgICAgICAgICAgcGFnZSsrXHJcbiAgICAgICAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgICAgICAgaGFzTW9yZSA9IGZhbHNlXHJcbiAgICAgICAgICAgIH1cclxuICAgICAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgICAgIGhhc01vcmUgPSBmYWxzZVxyXG4gICAgICAgICAgfVxyXG4gICAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgICBoYXNNb3JlID0gZmFsc2VcclxuICAgICAgICB9XHJcbiAgICAgIH0gY2F0Y2ggKGVycm9yKSB7XHJcbiAgICAgICAgY29uc29sZS5lcnJvcihg6I635Y+W56ysJHtwYWdlfemhteaVsOaNruWksei0pTpgLCBlcnJvcilcclxuICAgICAgICBoYXNNb3JlID0gZmFsc2VcclxuICAgICAgfVxyXG4gICAgfVxyXG4gICAgXHJcbiAgICAvLyDovazmjaLkuLrmlbDnu4TmoLzlvI9cclxuICAgIGRhaWx5Q29tcGxldGVkRGF0YS52YWx1ZSA9IGRhdGVzLm1hcChkYXRlID0+ICh7XHJcbiAgICAgIGRhdGU6IGRhdGUsXHJcbiAgICAgIGNvdW50OiBkYXRlQ291bnRNYXBbZGF0ZV0gfHwgMFxyXG4gICAgfSkpXHJcbiAgfSBjYXRjaCAoZXJyb3IpIHtcclxuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluavj+aXpeWujOaIkOaVsOmHj+aVsOaNruWHuumUmTonLCBlcnJvcilcclxuICAgIGRhaWx5Q29tcGxldGVkRGF0YS52YWx1ZSA9IFtdXHJcbiAgfVxyXG59XHJcblxyXG4vLyDorqHnrpfku4rlpKnlrozmiJDnmoTop4bpopHmlbDph49cclxuY29uc3QgdG9kYXlDb21wbGV0ZWRDb3VudCA9IGNvbXB1dGVkKCgpID0+IHtcclxuICBpZiAoIXN0YXRpc3RpY3MudmFsdWUpIHJldHVybiAwXHJcbiAgLy8g5LuO5q+P5pel5pWw5o2u5Lit6I635Y+W5LuK5aSp55qE5pWw5o2uXHJcbiAgY29uc3QgdG9kYXkgPSBuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCkuc3BsaXQoJ1QnKVswXVxyXG4gIGNvbnN0IHRvZGF5RGF0YSA9IGRhaWx5Q29tcGxldGVkRGF0YS52YWx1ZS5maW5kKGl0ZW0gPT4gaXRlbS5kYXRlID09PSB0b2RheSlcclxuICByZXR1cm4gdG9kYXlEYXRhID8gdG9kYXlEYXRhLmNvdW50IDogMFxyXG59KVxyXG5cclxuLy8g6K6h566X57Sv6K6h5a6M5oiQ55qE6KeG6aKR5pWw6YePXHJcbmNvbnN0IHRvdGFsQ29tcGxldGVkQ291bnQgPSBjb21wdXRlZCgoKSA9PiB7XHJcbiAgaWYgKCFzdGF0aXN0aWNzLnZhbHVlKSByZXR1cm4gMFxyXG4gIHJldHVybiBzdGF0aXN0aWNzLnZhbHVlLmNvbXBsZXRlZCB8fCAwXHJcbn0pXHJcblxyXG4vLyDorqHnrpfmn7Hnirblm77nmoTmnIDlpKflgLzvvIjnlKjkuo7orqHnrpfpq5jluqbnmb7liIbmr5TvvIlcclxuY29uc3QgbWF4QmFyVmFsdWUgPSBjb21wdXRlZCgoKSA9PiB7XHJcbiAgaWYgKGRhaWx5Q29tcGxldGVkRGF0YS52YWx1ZS5sZW5ndGggPT09IDApIHJldHVybiAxXHJcbiAgcmV0dXJuIE1hdGgubWF4KC4uLmRhaWx5Q29tcGxldGVkRGF0YS52YWx1ZS5tYXAoaXRlbSA9PiBpdGVtLmNvdW50KSwgMSlcclxufSlcclxuXHJcbi8vIOiOt+WPluafseeKtuWbvueahOmrmOW6pueZvuWIhuavlFxyXG5jb25zdCBnZXRCYXJIZWlnaHQgPSAodmFsdWUpID0+IHtcclxuICBpZiAobWF4QmFyVmFsdWUudmFsdWUgPT09IDApIHJldHVybiAwXHJcbiAgcmV0dXJuICh2YWx1ZSAvIG1heEJhclZhbHVlLnZhbHVlKSAqIDEwMFxyXG59XHJcblxyXG4vLyDmoLzlvI/ljJblm77ooajml6XmnJ/vvIjmmL7npLrkuLogTU0tRETvvIlcclxuY29uc3QgZm9ybWF0Q2hhcnREYXRlID0gKGRhdGVTdHIpID0+IHtcclxuICBpZiAoIWRhdGVTdHIpIHJldHVybiAnJ1xyXG4gIGNvbnN0IGRhdGUgPSBuZXcgRGF0ZShkYXRlU3RyKVxyXG4gIGNvbnN0IG1vbnRoID0gKGRhdGUuZ2V0TW9udGgoKSArIDEpLnRvU3RyaW5nKCkucGFkU3RhcnQoMiwgJzAnKVxyXG4gIGNvbnN0IGRheSA9IGRhdGUuZ2V0RGF0ZSgpLnRvU3RyaW5nKCkucGFkU3RhcnQoMiwgJzAnKVxyXG4gIHJldHVybiBgJHttb250aH0tJHtkYXl9YFxyXG59XHJcblxyXG4vLyDmiZPlvIDlt6XkvZzlrprkuYnmqKHmgIHmoYbml7bmu5rliqjliLDlupXpg6hcclxud2F0Y2goc2hvd0RlZmluaXRpb25Nb2RhbCwgKHNob3cpID0+IHtcclxuICBpZiAoc2hvdyAmJiB3b3JrRGVmaW5pdGlvbi52YWx1ZSkge1xyXG4gICAgc2V0VGltZW91dCgoKSA9PiB7XHJcbiAgICAgIGNvbnN0IG1vZGFsQm9keSA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoJy5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCcpXHJcbiAgICAgIGlmIChtb2RhbEJvZHkpIHtcclxuICAgICAgICBtb2RhbEJvZHkuc2Nyb2xsVG9wID0gMFxyXG4gICAgICB9XHJcbiAgICB9LCAxMDApXHJcbiAgfVxyXG59KVxyXG5cclxuLy8g5omT5byA5pel5b+X5qih5oCB5qGG5pe25rua5Yqo5Yiw5bqV6YOoXHJcbndhdGNoKHNob3dMb2dzTW9kYWwsIChzaG93KSA9PiB7XHJcbiAgaWYgKHNob3cgJiYgbG9nQ29udGVudEZ1bGwudmFsdWUpIHtcclxuICAgIHNldFRpbWVvdXQoKCkgPT4ge1xyXG4gICAgICBsb2dDb250ZW50RnVsbC52YWx1ZS5zY3JvbGxUb3AgPSBsb2dDb250ZW50RnVsbC52YWx1ZS5zY3JvbGxIZWlnaHRcclxuICAgIH0sIDEwMClcclxuICB9XHJcbn0pXHJcblxyXG4vLyDojrflj5blt6XkvZzmsYfmiqVcclxuY29uc3QgZmV0Y2hEYWlseVJlcG9ydCA9IGFzeW5jICgpID0+IHtcclxuICByZXBvcnRMb2FkaW5nLnZhbHVlID0gdHJ1ZVxyXG4gIHRyeSB7XHJcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcclxuICAgIGNvbnN0IGRhdGVQYXJhbSA9IGZvcm1hdERhdGVGb3JBcGkoc2VsZWN0ZWREYXRlLnZhbHVlKVxyXG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS92aWRlby9kYWlseS1yZXBvcnQ/ZGF0ZT0ke2RhdGVQYXJhbX1gKVxyXG4gICAgXHJcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcclxuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXHJcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XHJcbiAgICAgICAgZGFpbHlSZXBvcnQudmFsdWUgPSByZXN1bHQuZGF0YVxyXG4gICAgICB9IGVsc2Uge1xyXG4gICAgICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluW3peS9nOaxh+aKpeWksei0pTonLCByZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKVxyXG4gICAgICAgIGRhaWx5UmVwb3J0LnZhbHVlID0gbnVsbFxyXG4gICAgICB9XHJcbiAgICB9IGVsc2Uge1xyXG4gICAgICBjb25zb2xlLmVycm9yKCdBUEkg6K+35rGC5aSx6LSlOicsIHJlc3BvbnNlLnN0YXR1cylcclxuICAgICAgZGFpbHlSZXBvcnQudmFsdWUgPSBudWxsXHJcbiAgICB9XHJcbiAgfSBjYXRjaCAoZXJyb3IpIHtcclxuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluW3peS9nOaxh+aKpeWHuumUmTonLCBlcnJvcilcclxuICAgIGRhaWx5UmVwb3J0LnZhbHVlID0gbnVsbFxyXG4gIH0gZmluYWxseSB7XHJcbiAgICByZXBvcnRMb2FkaW5nLnZhbHVlID0gZmFsc2VcclxuICB9XHJcbn1cclxuXHJcbi8vIOiOt+WPluW3peS9nOWumuS5iVxyXG5jb25zdCBmZXRjaFdvcmtEZWZpbml0aW9uID0gYXN5bmMgKCkgPT4ge1xyXG4gIHdvcmtEZWZpbml0aW9uTG9hZGluZy52YWx1ZSA9IHRydWVcclxuICB0cnkge1xyXG4gICAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXHJcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3ZpZGVvL3dvcmstZGVmaW5pdGlvbmApXHJcbiAgICBcclxuICAgIGlmIChyZXNwb25zZS5vaykge1xyXG4gICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcclxuICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcclxuICAgICAgICB3b3JrRGVmaW5pdGlvbi52YWx1ZSA9IHJlc3VsdC5kYXRhPy5jb250ZW50IHx8ICcnXHJcbiAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgY29uc29sZS5lcnJvcign6I635Y+W5bel5L2c5a6a5LmJ5aSx6LSlOicsIHJlc3VsdC5tc2cgfHwgcmVzdWx0Lm1lc3NhZ2UpXHJcbiAgICAgICAgd29ya0RlZmluaXRpb24udmFsdWUgPSBudWxsXHJcbiAgICAgIH1cclxuICAgIH0gZWxzZSB7XHJcbiAgICAgIGNvbnNvbGUuZXJyb3IoJ0FQSSDor7fmsYLlpLHotKU6JywgcmVzcG9uc2Uuc3RhdHVzKVxyXG4gICAgICB3b3JrRGVmaW5pdGlvbi52YWx1ZSA9IG51bGxcclxuICAgIH1cclxuICB9IGNhdGNoIChlcnJvcikge1xyXG4gICAgY29uc29sZS5lcnJvcign6I635Y+W5bel5L2c5a6a5LmJ5Ye66ZSZOicsIGVycm9yKVxyXG4gICAgd29ya0RlZmluaXRpb24udmFsdWUgPSBudWxsXHJcbiAgfSBmaW5hbGx5IHtcclxuICAgIHdvcmtEZWZpbml0aW9uTG9hZGluZy52YWx1ZSA9IGZhbHNlXHJcbiAgfVxyXG59XHJcblxyXG4vLyDmoLzlvI/ljJblt6XkvZzlrprkuYnlhoXlrrnvvIjlsIbmlofmnKzovazmjaLkuLpIVE1M77yJXHJcbmNvbnN0IGZvcm1hdFdvcmtEZWZpbml0aW9uID0gKHRleHQpID0+IHtcclxuICBpZiAoIXRleHQpIHJldHVybiAnJ1xyXG4gIFxyXG4gIC8vIOWwhuaWh+acrOaMieihjOWIhuWJslxyXG4gIGNvbnN0IGxpbmVzID0gdGV4dC5zcGxpdCgnXFxuJylcclxuICBsZXQgaHRtbCA9ICcnXHJcbiAgbGV0IGluTGlzdCA9IGZhbHNlXHJcbiAgXHJcbiAgZm9yIChsZXQgaSA9IDA7IGkgPCBsaW5lcy5sZW5ndGg7IGkrKykge1xyXG4gICAgY29uc3QgbGluZSA9IGxpbmVzW2ldLnRyaW0oKVxyXG4gICAgXHJcbiAgICBpZiAoIWxpbmUpIHtcclxuICAgICAgaWYgKGluTGlzdCkge1xyXG4gICAgICAgIGh0bWwgKz0gJzwvb2w+J1xyXG4gICAgICAgIGluTGlzdCA9IGZhbHNlXHJcbiAgICAgIH1cclxuICAgICAgaHRtbCArPSAnPGJyPidcclxuICAgICAgY29udGludWVcclxuICAgIH1cclxuICAgIFxyXG4gICAgLy8g5qOA5p+l5piv5ZCm5piv5qCH6aKYXHJcbiAgICBpZiAobGluZS5pbmNsdWRlcygn5bel5L2c5a6a5LmJJykgfHwgbGluZS5pbmNsdWRlcygn5bel5L2c5rWB56iLJykgfHwgbGluZS5pbmNsdWRlcygn5Lq65bel5pON5L2cJykpIHtcclxuICAgICAgaWYgKGluTGlzdCkge1xyXG4gICAgICAgIGh0bWwgKz0gJzwvb2w+J1xyXG4gICAgICAgIGluTGlzdCA9IGZhbHNlXHJcbiAgICAgIH1cclxuICAgICAgaHRtbCArPSBgPGg0PiR7bGluZX08L2g0PmBcclxuICAgIH1cclxuICAgIC8vIOajgOafpeaYr+WQpuaYr+WIl+ihqOmhue+8iOS7peaVsOWtl+W8gOWktO+8iVxyXG4gICAgZWxzZSBpZiAoL15cXGQrXFwuLy50ZXN0KGxpbmUpKSB7XHJcbiAgICAgIGlmICghaW5MaXN0KSB7XHJcbiAgICAgICAgaHRtbCArPSAnPG9sPidcclxuICAgICAgICBpbkxpc3QgPSB0cnVlXHJcbiAgICAgIH1cclxuICAgICAgLy8g5o+Q5Y+W5pWw5a2X5ZKM5YaF5a65XHJcbiAgICAgIGNvbnN0IG1hdGNoID0gbGluZS5tYXRjaCgvXihcXGQrKVxcLlxccyooLispLylcclxuICAgICAgaWYgKG1hdGNoKSB7XHJcbiAgICAgICAgY29uc3QgY29udGVudCA9IG1hdGNoWzJdXHJcbiAgICAgICAgLy8g5qOA5p+l5piv5ZCm5pyJ5YaS5Y+35YiG6ZqU55qE5qCH6aKY5ZKM5o+P6L+wXHJcbiAgICAgICAgaWYgKGNvbnRlbnQuaW5jbHVkZXMoJ++8micpKSB7XHJcbiAgICAgICAgICBjb25zdCBbdGl0bGUsIGRlc2NdID0gY29udGVudC5zcGxpdCgn77yaJywgMilcclxuICAgICAgICAgIGh0bWwgKz0gYDxsaT48c3Ryb25nPiR7dGl0bGV9PC9zdHJvbmc+77yaJHtkZXNjfTwvbGk+YFxyXG4gICAgICAgIH0gZWxzZSB7XHJcbiAgICAgICAgICBodG1sICs9IGA8bGk+JHtjb250ZW50fTwvbGk+YFxyXG4gICAgICAgIH1cclxuICAgICAgfVxyXG4gICAgfVxyXG4gICAgLy8g5qOA5p+l5piv5ZCm5piv5YiX6KGo6aG577yI5LulLeW8gOWktO+8iVxyXG4gICAgZWxzZSBpZiAobGluZS5zdGFydHNXaXRoKCctJykpIHtcclxuICAgICAgaWYgKCFpbkxpc3QpIHtcclxuICAgICAgICBodG1sICs9ICc8dWw+J1xyXG4gICAgICAgIGluTGlzdCA9IHRydWVcclxuICAgICAgfVxyXG4gICAgICBodG1sICs9IGA8bGk+JHtsaW5lLnN1YnN0cmluZygxKS50cmltKCl9PC9saT5gXHJcbiAgICB9XHJcbiAgICAvLyDmma7pgJrmlofmnKxcclxuICAgIGVsc2Uge1xyXG4gICAgICBpZiAoaW5MaXN0KSB7XHJcbiAgICAgICAgaHRtbCArPSAnPC9vbD4nXHJcbiAgICAgICAgaW5MaXN0ID0gZmFsc2VcclxuICAgICAgfVxyXG4gICAgICBodG1sICs9IGA8cD4ke2xpbmV9PC9wPmBcclxuICAgIH1cclxuICB9XHJcbiAgXHJcbiAgaWYgKGluTGlzdCkge1xyXG4gICAgaHRtbCArPSAnPC9vbD4nXHJcbiAgfVxyXG4gIFxyXG4gIHJldHVybiBodG1sXHJcbn1cclxuXHJcbi8vIOebkeWQrOiHquWKqOWIt+aWsO+8iOmdmem7mOWIt+aWsO+8jOS4jeaYvuekumxvYWRpbmfvvIlcclxud2F0Y2goYXV0b1JlZnJlc2gsIChhdXRvKSA9PiB7XHJcbiAgaWYgKGF1dG8pIHtcclxuICAgIGZldGNoTG9ncyhmYWxzZSkgLy8g6Ieq5Yqo5Yi35paw5pe25LiN5pi+56S6bG9hZGluZ++8jOmBv+WFjemXquWKqFxyXG4gICAgcmVmcmVzaFRpbWVyID0gc2V0SW50ZXJ2YWwoKCkgPT4ge1xyXG4gICAgICBmZXRjaExvZ3MoZmFsc2UpIC8vIOmdmem7mOWIt+aWsFxyXG4gICAgfSwgNTAwMClcclxuICB9IGVsc2Uge1xyXG4gICAgaWYgKHJlZnJlc2hUaW1lcikge1xyXG4gICAgICBjbGVhckludGVydmFsKHJlZnJlc2hUaW1lcilcclxuICAgICAgcmVmcmVzaFRpbWVyID0gbnVsbFxyXG4gICAgfVxyXG4gIH1cclxufSlcclxuXHJcbm9uTW91bnRlZCgoKSA9PiB7XHJcbiAgZmV0Y2hMb2dzKClcclxuICBmZXRjaERhaWx5UmVwb3J0KClcclxuICBmZXRjaFdvcmtEZWZpbml0aW9uKClcclxuICBmZXRjaFpvZVN0YXR1cygpXHJcbiAgZmV0Y2hTdGF0aXN0aWNzKClcclxufSlcclxuXHJcbm9uVW5tb3VudGVkKCgpID0+IHtcclxuICBpZiAocmVmcmVzaFRpbWVyKSB7XHJcbiAgICBjbGVhckludGVydmFsKHJlZnJlc2hUaW1lcilcclxuICAgIHJlZnJlc2hUaW1lciA9IG51bGxcclxuICB9XHJcbn0pXHJcbjwvc2NyaXB0PlxyXG5cclxuPHN0eWxlIHNjb3BlZD5cclxuLmxvZ3MtcGFnZSB7XHJcbiAgbWF4LXdpZHRoOiAxNjAwcHg7XHJcbiAgbWFyZ2luOiAwIGF1dG87XHJcbiAgcGFkZGluZzogMTZweCAzMnB4O1xyXG4gIG1pbi1oZWlnaHQ6IGNhbGMoMTAwdmggLSA2MHB4KTtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbn1cclxuXHJcbi5sb2dzLWhlYWRlciB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBtYXJnaW4tYm90dG9tOiAxMnB4O1xyXG4gIGZsZXgtd3JhcDogd3JhcDtcclxuICBnYXA6IDEycHg7XHJcbn1cclxuXHJcbi5sb2dzLXRpdGxlIHtcclxuICBmb250LXNpemU6IDIwcHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzFhMWExYTtcclxuICBtYXJnaW46IDA7XHJcbiAgbWFyZ2luLWxlZnQ6IDEwcHg7XHJcbn1cclxuXHJcbi5jaGFydC10aXRsZS1oZWFkZXIge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxufVxyXG5cclxuLmNoYXJ0LXRpdGxlLXRleHQge1xyXG4gIGZvbnQtc2l6ZTogMjBweDtcclxuICBmb250LXdlaWdodDogNjAwO1xyXG4gIGNvbG9yOiAjMWExYTFhO1xyXG4gIG1hcmdpbjogMDtcclxufVxyXG5cclxuLnRpdGxlLXdpdGgtc3RhdHVzIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgZ2FwOiAxMnB4O1xyXG59XHJcblxyXG4uc3RhdHVzLWJhZGdlIHtcclxuICBkaXNwbGF5OiBpbmxpbmUtZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGdhcDogNnB4O1xyXG4gIHBhZGRpbmc6IDRweCAxMHB4O1xyXG4gIGJvcmRlci1yYWRpdXM6IDEycHg7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGN1cnNvcjogcG9pbnRlcjtcclxuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcclxufVxyXG5cclxuLnN0YXR1cy1iYWRnZTpob3ZlciB7XHJcbiAgb3BhY2l0eTogMC44O1xyXG59XHJcblxyXG4uc3RhdHVzLWRvdCB7XHJcbiAgd2lkdGg6IDhweDtcclxuICBoZWlnaHQ6IDhweDtcclxuICBib3JkZXItcmFkaXVzOiA1MCU7XHJcbn1cclxuXHJcbi5zdGF0dXMtd29ya2luZyB7XHJcbiAgYmFja2dyb3VuZDogI2Y2ZmZlZDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjYjdlYjhmO1xyXG4gIGNvbG9yOiAjNTJjNDFhO1xyXG59XHJcblxyXG4uc3RhdHVzLXdvcmtpbmcgLnN0YXR1cy1kb3Qge1xyXG4gIGJhY2tncm91bmQ6ICM1MmM0MWE7XHJcbiAgYW5pbWF0aW9uOiBwdWxzZSAycyBpbmZpbml0ZTtcclxufVxyXG5cclxuLnN0YXR1cy1kZWFkIHtcclxuICBiYWNrZ3JvdW5kOiAjZmZmMmYwO1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmNjYzc7XHJcbiAgY29sb3I6ICNmZjRkNGY7XHJcbn1cclxuXHJcbi5zdGF0dXMtZGVhZCAuc3RhdHVzLWRvdCB7XHJcbiAgYmFja2dyb3VuZDogI2ZmNGQ0ZjtcclxufVxyXG5cclxuLnN0YXR1cy11bmtub3duIHtcclxuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNkOWQ5ZDk7XHJcbiAgY29sb3I6ICM5OTk7XHJcbn1cclxuXHJcbi5zdGF0dXMtdW5rbm93biAuc3RhdHVzLWRvdCB7XHJcbiAgYmFja2dyb3VuZDogIzk5OTtcclxufVxyXG5cclxuQGtleWZyYW1lcyBwdWxzZSB7XHJcbiAgMCUsIDEwMCUgeyBvcGFjaXR5OiAxOyB9XHJcbiAgNTAlIHsgb3BhY2l0eTogMC41OyB9XHJcbn1cclxuXHJcbi50aXRsZS1kYXRlIHtcclxuICBmb250LXNpemU6IDE2cHg7XHJcbiAgZm9udC13ZWlnaHQ6IDQwMDtcclxuICBjb2xvcjogIzY2NjtcclxuICBtYXJnaW4tbGVmdDogOHB4O1xyXG59XHJcblxyXG4ubG9ncy1jb250cm9scyB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGdhcDogMTBweDtcclxufVxyXG5cclxuLmF1dG8tcmVmcmVzaC1sYWJlbCB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGdhcDogNHB4O1xyXG4gIGZvbnQtc2l6ZTogMTNweDtcclxuICBjb2xvcjogIzY2NjtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbn1cclxuXHJcbi5hdXRvLXJlZnJlc2gtbGFiZWwgaW5wdXRbdHlwZT1cImNoZWNrYm94XCJdIHtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbn1cclxuXHJcbi5kYXRlLXNlbGVjdG9yIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgZ2FwOiA2cHg7XHJcbn1cclxuXHJcbi5kYXRlLWxhYmVsIHtcclxuICBmb250LXNpemU6IDEzcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbn1cclxuXHJcbi5kYXRlLWlucHV0IHtcclxuICBwYWRkaW5nOiA1cHggMTBweDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xyXG4gIGJvcmRlci1yYWRpdXM6IDRweDtcclxuICBmb250LXNpemU6IDEzcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xyXG59XHJcblxyXG4uZGF0ZS1pbnB1dDpob3ZlciB7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG59XHJcblxyXG4uZGF0ZS1pbnB1dDpmb2N1cyB7XHJcbiAgb3V0bGluZTogbm9uZTtcclxuICBib3JkZXItY29sb3I6ICMxODkwZmY7XHJcbiAgYm94LXNoYWRvdzogMCAwIDAgMnB4IHJnYmEoMjQsIDE0NCwgMjU1LCAwLjEpO1xyXG59XHJcblxyXG4ucmVmcmVzaC1idG4sXHJcbi5iYWNrLWJ0biB7XHJcbiAgcGFkZGluZzogNnB4IDEycHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcclxuICBib3JkZXItcmFkaXVzOiA0cHg7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG4gIGZvbnQtc2l6ZTogMTNweDtcclxuICBjb2xvcjogIzY2NjtcclxuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcclxufVxyXG5cclxuLnJlZnJlc2gtYnRuOmhvdmVyLFxyXG4uYmFjay1idG46aG92ZXIge1xyXG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcclxuICBjb2xvcjogIzE4OTBmZjtcclxufVxyXG5cclxuLmVycm9yLXRleHQge1xyXG4gIGNvbG9yOiAjZmY0ZDRmO1xyXG59XHJcblxyXG4vKiDlt6XkvZzmsYfmiqXljLrln58gKi9cclxuLnJlcG9ydC1zZWN0aW9uLWZ1bGwge1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlci1yYWRpdXM6IDhweDtcclxuICBwYWRkaW5nOiAxMnB4IDIwcHg7XHJcbiAgbWFyZ2luLWJvdHRvbTogOHB4O1xyXG59XHJcblxyXG4vKiDku6rooajnm5jluIPlsYAgKi9cclxuLnJlcG9ydC1kYXNoYm9hcmQge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZ2FwOiAzMnB4O1xyXG4gIGFsaWduLWl0ZW1zOiBmbGV4LXN0YXJ0O1xyXG59XHJcblxyXG4uZGFzaGJvYXJkLWdyb3VwIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbiAgZ2FwOiA4cHg7XHJcbn1cclxuXHJcbi5ncm91cC10aXRsZSB7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA1MDA7XHJcbiAgY29sb3I6ICM5OTk7XHJcbiAgdGV4dC10cmFuc2Zvcm06IHVwcGVyY2FzZTtcclxuICBsZXR0ZXItc3BhY2luZzogMC41cHg7XHJcbn1cclxuXHJcbi5zdGF0LXJvdyB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBnYXA6IDEycHg7XHJcbn1cclxuXHJcbi5zdGF0LWNhcmQge1xyXG4gIHBhZGRpbmc6IDEycHggMTZweDtcclxuICBib3JkZXItcmFkaXVzOiA2cHg7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIG1pbi13aWR0aDogODBweDtcclxufVxyXG5cclxuLnN0YXQtY2FyZC5zdGF0LXByaW1hcnkge1xyXG4gIGJhY2tncm91bmQ6IGxpbmVhci1ncmFkaWVudCgxMzVkZWcsICNlNmY0ZmYgMCUsICNmMGY3ZmYgMTAwJSk7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgIzkxY2FmZjtcclxufVxyXG5cclxuLnN0YXQtY2FyZC5zdGF0LXNlY29uZGFyeSB7XHJcbiAgYmFja2dyb3VuZDogI2Y2ZmZlZDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjYjdlYjhmO1xyXG59XHJcblxyXG4uc3RhdC1jYXJkLnN0YXQtaGlnaGxpZ2h0IHtcclxuICBiYWNrZ3JvdW5kOiBsaW5lYXItZ3JhZGllbnQoMTM1ZGVnLCAjZmZmN2U2IDAlLCAjZmZmYmU2IDEwMCUpO1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmQ1OTE7XHJcbn1cclxuXHJcbi5zdGF0LXZhbHVlIHtcclxuICBmb250LXNpemU6IDI0cHg7XHJcbiAgZm9udC13ZWlnaHQ6IDcwMDtcclxuICBsaW5lLWhlaWdodDogMTtcclxuICBtYXJnaW4tYm90dG9tOiA0cHg7XHJcbn1cclxuXHJcbi5zdGF0LXByaW1hcnkgLnN0YXQtdmFsdWUge1xyXG4gIGNvbG9yOiAjMTg5MGZmO1xyXG59XHJcblxyXG4uc3RhdC1zZWNvbmRhcnkgLnN0YXQtdmFsdWUge1xyXG4gIGNvbG9yOiAjNTJjNDFhO1xyXG59XHJcblxyXG4uc3RhdC1oaWdobGlnaHQgLnN0YXQtdmFsdWUge1xyXG4gIGNvbG9yOiAjZmE4YzE2O1xyXG59XHJcblxyXG4uc3RhdC1sYWJlbCB7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG59XHJcblxyXG4vKiDmnaXmupDmoIfnrb4gKi9cclxuLnNvdXJjZS10YWdzIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtd3JhcDogd3JhcDtcclxuICBnYXA6IDhweDtcclxufVxyXG5cclxuLnNvdXJjZS10YWcge1xyXG4gIGRpc3BsYXk6IGlubGluZS1mbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgZ2FwOiA2cHg7XHJcbiAgcGFkZGluZzogNnB4IDEycHg7XHJcbiAgYmFja2dyb3VuZDogI2ZhZmFmYTtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xyXG4gIGJvcmRlci1yYWRpdXM6IDE2cHg7XHJcbiAgZm9udC1zaXplOiAxM3B4O1xyXG59XHJcblxyXG4udGFnLW5hbWUge1xyXG4gIGNvbG9yOiAjNjY2O1xyXG59XHJcblxyXG4udGFnLWNvdW50IHtcclxuICBmb250LXdlaWdodDogNjAwO1xyXG4gIGNvbG9yOiAjMTg5MGZmO1xyXG4gIGJhY2tncm91bmQ6ICNlNmY0ZmY7XHJcbiAgcGFkZGluZzogMnB4IDhweDtcclxuICBib3JkZXItcmFkaXVzOiAxMHB4O1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxufVxyXG5cclxuLyog5bqV6YOo5Lik5qCP5biD5bGAICovXHJcbi5ib3R0b20tbGF5b3V0IHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGdhcDogMTZweDtcclxuICBmbGV4OiAxO1xyXG4gIG1pbi1oZWlnaHQ6IDA7XHJcbn1cclxuXHJcbi8qIOmihOiniOmdouadv+mAmueUqOagt+W8jyAqL1xyXG4ucHJldmlldy1wYW5lbCB7XHJcbiAgZmxleDogMTtcclxuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcclxuICBib3JkZXItcmFkaXVzOiA4cHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGZsZXgtZGlyZWN0aW9uOiBjb2x1bW47XHJcbiAgbWluLXdpZHRoOiAwO1xyXG4gIG92ZXJmbG93OiBoaWRkZW47XHJcbn1cclxuXHJcbi5kZWZpbml0aW9uLXByZXZpZXcge1xyXG4gIGZsZXg6IDAgMCA0NSU7XHJcbn1cclxuXHJcbi5sb2dzLXByZXZpZXcge1xyXG4gIGZsZXg6IDAgMCA1NSU7XHJcbn1cclxuXHJcbi5wcmV2aWV3LWhlYWRlciB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBwYWRkaW5nOiAxMnB4IDE2cHg7XHJcbiAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYmFja2dyb3VuZDogI2Y4ZjlmYTtcclxuICBmbGV4LXdyYXA6IHdyYXA7XHJcbiAgZ2FwOiA4cHg7XHJcbn1cclxuXHJcbi5wcmV2aWV3LWhlYWRlciBoMyB7XHJcbiAgZm9udC1zaXplOiAxNHB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA2MDA7XHJcbiAgY29sb3I6ICMxYTFhMWE7XHJcbiAgbWFyZ2luOiAwO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDEwcHg7XHJcbiAgZmxleC13cmFwOiB3cmFwO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLmRhdGUtc2VsZWN0b3Ige1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDZweDtcclxufVxyXG5cclxuLmxvZ3MtaGVhZGVyLWNvbnRyb2xzIC5kYXRlLWxhYmVsIHtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcclxufVxyXG5cclxuLmxvZ3MtaGVhZGVyLWNvbnRyb2xzIC5kYXRlLWlucHV0IHtcclxuICBwYWRkaW5nOiA0cHggOHB4O1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBjb2xvcjogIzY2NjtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XHJcbn1cclxuXHJcbi5sb2dzLWhlYWRlci1jb250cm9scyAuZGF0ZS1pbnB1dDpob3ZlciB7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLmRhdGUtaW5wdXQ6Zm9jdXMge1xyXG4gIG91dGxpbmU6IG5vbmU7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG4gIGJveC1zaGFkb3c6IDAgMCAwIDJweCByZ2JhKDI0LCAxNDQsIDI1NSwgMC4xKTtcclxufVxyXG5cclxuLmxvZ3MtaGVhZGVyLWNvbnRyb2xzIC5hdXRvLXJlZnJlc2gtbGFiZWwge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBnYXA6IDRweDtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG4gIHdoaXRlLXNwYWNlOiBub3dyYXA7XHJcbn1cclxuXHJcbi5sb2dzLWhlYWRlci1jb250cm9scyAuYXV0by1yZWZyZXNoLWxhYmVsIGlucHV0W3R5cGU9XCJjaGVja2JveFwiXSB7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLnJlZnJlc2gtYnRuIHtcclxuICBwYWRkaW5nOiA0cHggMTJweDtcclxuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlci1yYWRpdXM6IDRweDtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbiAgZm9udC1zaXplOiAxMnB4O1xyXG4gIGNvbG9yOiAjNjY2O1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xyXG59XHJcblxyXG4ubG9ncy1oZWFkZXItY29udHJvbHMgLnJlZnJlc2gtYnRuOmhvdmVyIHtcclxuICBib3JkZXItY29sb3I6ICMxODkwZmY7XHJcbiAgY29sb3I6ICMxODkwZmY7XHJcbn1cclxuXHJcbi5leHBhbmQtYnRuIHtcclxuICB3aWR0aDogMjhweDtcclxuICBoZWlnaHQ6IDI4cHg7XHJcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcclxuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcclxuICBib3JkZXItcmFkaXVzOiA0cHg7XHJcbiAgY3Vyc29yOiBwb2ludGVyO1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IGNlbnRlcjtcclxuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcclxuICBwYWRkaW5nOiAwO1xyXG59XHJcblxyXG4uZXhwYW5kLWJ0bjpob3ZlciB7XHJcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xyXG4gIGJhY2tncm91bmQ6ICNmMGY3ZmY7XHJcbiAgY29sb3I6ICMxODkwZmY7XHJcbn1cclxuXHJcbi5leHBhbmQtYnRuIHN2ZyB7XHJcbiAgd2lkdGg6IDE2cHg7XHJcbiAgaGVpZ2h0OiAxNnB4O1xyXG4gIHN0cm9rZS13aWR0aDogMjtcclxufVxyXG5cclxuLnByZXZpZXctY29udGVudCB7XHJcbiAgZmxleDogMTtcclxuICBvdmVyZmxvdy15OiBhdXRvO1xyXG4gIHBhZGRpbmc6IDEycHggMTZweDtcclxuICBtaW4taGVpZ2h0OiAwO1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcge1xyXG4gIGxpbmUtaGVpZ2h0OiAxLjY7XHJcbiAgbWF4LWhlaWdodDogNDAwcHg7XHJcbiAgb3ZlcmZsb3cteTogYXV0bztcclxufVxyXG5cclxuLmxvZ3MtaW5mby1jb21wYWN0IHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGdhcDogMTZweDtcclxuICBwYWRkaW5nOiA2cHggMDtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgY29sb3I6ICM4ODg7XHJcbiAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkICNmMGYwZjA7XHJcbiAgbWFyZ2luLWJvdHRvbTogOHB4O1xyXG59XHJcblxyXG4ubG9nLWNvbnRlbnQtcHJldmlldyB7XHJcbiAgbWF4LWhlaWdodDogNDAwcHg7XHJcbiAgb3ZlcmZsb3cteTogYXV0bztcclxuICBwYWRkaW5nOiAxMHB4O1xyXG4gIGJhY2tncm91bmQ6ICMxZTFlMWU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGZvbnQtZmFtaWx5OiAnQ29uc29sYXMnLCAnTW9uYWNvJywgJ0NvdXJpZXIgTmV3JywgbW9ub3NwYWNlO1xyXG4gIGZvbnQtc2l6ZTogMTFweDtcclxuICBsaW5lLWhlaWdodDogMS40O1xyXG59XHJcblxyXG4ubG9nLXRleHQtcHJldmlldyB7XHJcbiAgbWFyZ2luOiAwO1xyXG4gIHdoaXRlLXNwYWNlOiBwcmUtd3JhcDtcclxuICB3b3JkLXdyYXA6IGJyZWFrLXdvcmQ7XHJcbiAgY29sb3I6ICNkNGQ0ZDQ7XHJcbiAgdHJhbnNpdGlvbjogb3BhY2l0eSAwLjJzO1xyXG59XHJcblxyXG4ubG9nLXRleHQtcHJldmlldy51cGRhdGluZyB7XHJcbiAgb3BhY2l0eTogMC43O1xyXG59XHJcblxyXG4ucmVwb3J0LWxvYWRpbmcsXHJcbi5yZXBvcnQtZW1wdHkge1xyXG4gIHRleHQtYWxpZ246IGNlbnRlcjtcclxuICBwYWRkaW5nOiA2MHB4IDIwcHg7XHJcbiAgY29sb3I6ICM4ODg7XHJcbiAgZm9udC1zaXplOiAxcmVtO1xyXG59XHJcblxyXG4vKiDnu5/orqHmlbDmja7ku6rooajnm5ggKi9cclxuLnN0YXRzLWRhc2hib2FyZCB7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBnYXA6IDI0cHg7XHJcbiAgYWxpZ24taXRlbXM6IHN0cmV0Y2g7XHJcbn1cclxuXHJcbi5zdGF0cy1jYXJkcyB7XHJcbiAgZmxleDogMCAwIDMwMHB4O1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcclxuICBnYXA6IDE2cHg7XHJcbn1cclxuXHJcbi5zdGF0LWNhcmQtbGFyZ2Uge1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XHJcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xyXG4gIHBhZGRpbmc6IDEycHggMTZweDtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgZ2FwOiAxMnB4O1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xyXG59XHJcblxyXG4uc3RhdC1jYXJkLWxhcmdlOmhvdmVyIHtcclxuICBib3gtc2hhZG93OiAwIDJweCA4cHggcmdiYSgwLCAwLCAwLCAwLjEpO1xyXG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcclxufVxyXG5cclxuLnN0YXQtY2FyZC1pY29uIHtcclxuICB3aWR0aDogNDBweDtcclxuICBoZWlnaHQ6IDQwcHg7XHJcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xyXG4gIGJhY2tncm91bmQ6IGxpbmVhci1ncmFkaWVudCgxMzVkZWcsICNlNmY0ZmYgMCUsICNmMGY3ZmYgMTAwJSk7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xyXG4gIGZsZXgtc2hyaW5rOiAwO1xyXG59XHJcblxyXG4uc3RhdC1jYXJkLWljb24gc3ZnIHtcclxuICB3aWR0aDogMjBweDtcclxuICBoZWlnaHQ6IDIwcHg7XHJcbiAgY29sb3I6ICMxODkwZmY7XHJcbn1cclxuXHJcbi5zdGF0LWNhcmQtY29udGVudCB7XHJcbiAgZmxleDogMTtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBiYXNlbGluZTtcclxuICBnYXA6IDhweDtcclxuICBmbGV4LXdyYXA6IHdyYXA7XHJcbn1cclxuXHJcbi5zdGF0LWNhcmQtdmFsdWUge1xyXG4gIGZvbnQtc2l6ZTogMjhweDtcclxuICBmb250LXdlaWdodDogNzAwO1xyXG4gIGNvbG9yOiAjMWExYTFhO1xyXG4gIGxpbmUtaGVpZ2h0OiAxO1xyXG59XHJcblxyXG4uc3RhdC1jYXJkLWxhYmVsIHtcclxuICBmb250LXNpemU6IDE0cHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgbGluZS1oZWlnaHQ6IDEuNDtcclxufVxyXG5cclxuLmNoYXJ0LWNvbnRhaW5lciB7XHJcbiAgZmxleDogMTtcclxuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcclxuICBib3JkZXItcmFkaXVzOiA4cHg7XHJcbiAgcGFkZGluZzogMTJweCAyMHB4O1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcclxufVxyXG5cclxuLmJhci1jaGFydCB7XHJcbiAgaGVpZ2h0OiAxNjBweDtcclxufVxyXG5cclxuLmNoYXJ0LWVtcHR5IHtcclxuICB0ZXh0LWFsaWduOiBjZW50ZXI7XHJcbiAgcGFkZGluZzogNjBweCAyMHB4O1xyXG4gIGNvbG9yOiAjOTk5O1xyXG4gIGZvbnQtc2l6ZTogMTRweDtcclxufVxyXG5cclxuLmNoYXJ0LWJhcnMge1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgYWxpZ24taXRlbXM6IGZsZXgtZW5kO1xyXG4gIGp1c3RpZnktY29udGVudDogc3BhY2UtYmV0d2VlbjtcclxuICBnYXA6IDRweDtcclxuICBoZWlnaHQ6IDE2MHB4O1xyXG4gIHBhZGRpbmc6IDAgMTBweDtcclxufVxyXG5cclxuLmNoYXJ0LWJhci1pdGVtIHtcclxuICBmbGV4OiAxO1xyXG4gIGRpc3BsYXk6IGZsZXg7XHJcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGhlaWdodDogMTAwJTtcclxuICBtYXgtd2lkdGg6IDQwcHg7XHJcbn1cclxuXHJcbi5iYXItd3JhcHBlciB7XHJcbiAgZmxleDogMTtcclxuICB3aWR0aDogMTAwJTtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBmbGV4LWVuZDtcclxuICBqdXN0aWZ5LWNvbnRlbnQ6IGNlbnRlcjtcclxuICBtYXJnaW4tYm90dG9tOiA4cHg7XHJcbn1cclxuXHJcbi5iYXIge1xyXG4gIHdpZHRoOiAxMDAlO1xyXG4gIGJhY2tncm91bmQ6IGxpbmVhci1ncmFkaWVudCgxODBkZWcsICMxODkwZmYgMCUsICM0MGE5ZmYgMTAwJSk7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4IDRweCAwIDA7XHJcbiAgbWluLWhlaWdodDogNHB4O1xyXG4gIHRyYW5zaXRpb246IGFsbCAwLjNzO1xyXG4gIGN1cnNvcjogcG9pbnRlcjtcclxufVxyXG5cclxuLmJhcjpob3ZlciB7XHJcbiAgb3BhY2l0eTogMC44O1xyXG4gIHRyYW5zZm9ybTogc2NhbGVZKDEuMDUpO1xyXG59XHJcblxyXG4uYmFyLWxhYmVsIHtcclxuICBmb250LXNpemU6IDExcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIG1hcmdpbi1ib3R0b206IDRweDtcclxuICB3aGl0ZS1zcGFjZTogbm93cmFwO1xyXG4gIG92ZXJmbG93OiBoaWRkZW47XHJcbiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7XHJcbiAgd2lkdGg6IDEwMCU7XHJcbiAgbWF4LXdpZHRoOiA1MHB4O1xyXG59XHJcblxyXG4uYmFyLXZhbHVlIHtcclxuICBmb250LXNpemU6IDEycHg7XHJcbiAgZm9udC13ZWlnaHQ6IDYwMDtcclxuICBjb2xvcjogIzE4OTBmZjtcclxuICB0ZXh0LWFsaWduOiBjZW50ZXI7XHJcbn1cclxuXHJcbi8qIOW3peS9nOWumuS5ieagt+W8j++8iOmihOiniOWSjOWFqOWxj+WFseeUqO+8iSAqL1xyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcsXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCB7XHJcbiAgbGluZS1oZWlnaHQ6IDEuNjtcclxufVxyXG5cclxuLmRlZmluaXRpb24tY29udGVudC1wcmV2aWV3IGg0LFxyXG4uZGVmaW5pdGlvbi1jb250ZW50LWZ1bGwgaDQge1xyXG4gIGZvbnQtc2l6ZTogMTZweDtcclxuICBmb250LXdlaWdodDogNjAwO1xyXG4gIGNvbG9yOiAjMWExYTFhO1xyXG4gIG1hcmdpbjogMTZweCAwIDhweCAwO1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcgaDQ6Zmlyc3QtY2hpbGQsXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCBoNDpmaXJzdC1jaGlsZCB7XHJcbiAgbWFyZ2luLXRvcDogMDtcclxufVxyXG5cclxuLmRlZmluaXRpb24tY29udGVudC1wcmV2aWV3IG9sLFxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcgdWwsXHJcbi5kZWZpbml0aW9uLWNvbnRlbnQtZnVsbCBvbCxcclxuLmRlZmluaXRpb24tY29udGVudC1mdWxsIHVsIHtcclxuICBtYXJnaW46IDhweCAwO1xyXG4gIHBhZGRpbmctbGVmdDogMjRweDtcclxufVxyXG5cclxuLmRlZmluaXRpb24tY29udGVudC1wcmV2aWV3IGxpLFxyXG4uZGVmaW5pdGlvbi1jb250ZW50LWZ1bGwgbGkge1xyXG4gIG1hcmdpbi1ib3R0b206IDhweDtcclxuICBsaW5lLWhlaWdodDogMS42O1xyXG4gIGNvbG9yOiAjNTU1O1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LXByZXZpZXcgcCxcclxuLmRlZmluaXRpb24tY29udGVudC1mdWxsIHAge1xyXG4gIG1hcmdpbjogOHB4IDA7XHJcbiAgbGluZS1oZWlnaHQ6IDEuNjtcclxuICBjb2xvcjogIzU1NTtcclxufVxyXG5cclxuLmRlZmluaXRpb24tbG9hZGluZyxcclxuLmRlZmluaXRpb24tZXJyb3Ige1xyXG4gIHBhZGRpbmc6IDIwcHg7XHJcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xyXG4gIGNvbG9yOiAjOTk5O1xyXG4gIGZvbnQtc2l6ZTogMTRweDtcclxufVxyXG5cclxuLmRlZmluaXRpb24tZXJyb3Ige1xyXG4gIGNvbG9yOiAjZmY0ZDRmO1xyXG59XHJcblxyXG4ubG9nLWxvYWRpbmcsXHJcbi5sb2ctZW1wdHkge1xyXG4gIHRleHQtYWxpZ246IGNlbnRlcjtcclxuICBwYWRkaW5nOiA0MHB4IDIwcHg7XHJcbiAgY29sb3I6ICM4ODg7XHJcbn1cclxuXHJcbi5sb2ctdGV4dCB7XHJcbiAgbWFyZ2luOiAwO1xyXG4gIHdoaXRlLXNwYWNlOiBwcmUtd3JhcDtcclxuICB3b3JkLXdyYXA6IGJyZWFrLXdvcmQ7XHJcbiAgY29sb3I6ICMzMzM7XHJcbn1cclxuXHJcbi8qIOaooeaAgeahhuagt+W8jyAqL1xyXG4ubW9kYWwtb3ZlcmxheSB7XHJcbiAgcG9zaXRpb246IGZpeGVkO1xyXG4gIHRvcDogMDtcclxuICBsZWZ0OiAwO1xyXG4gIHJpZ2h0OiAwO1xyXG4gIGJvdHRvbTogMDtcclxuICBiYWNrZ3JvdW5kOiByZ2JhKDAsIDAsIDAsIDAuNSk7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xyXG4gIHotaW5kZXg6IDEwMDA7XHJcbiAgcGFkZGluZzogMjBweDtcclxufVxyXG5cclxuLm1vZGFsLWNvbnRlbnQge1xyXG4gIGJhY2tncm91bmQ6IHdoaXRlO1xyXG4gIGJvcmRlci1yYWRpdXM6IDhweDtcclxuICBtYXgtd2lkdGg6IDkwMHB4O1xyXG4gIHdpZHRoOiAxMDAlO1xyXG4gIG1heC1oZWlnaHQ6IDkwdmg7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xyXG4gIGJveC1zaGFkb3c6IDAgNHB4IDIwcHggcmdiYSgwLCAwLCAwLCAwLjE1KTtcclxufVxyXG5cclxuLm1vZGFsLWNvbnRlbnQtbGFyZ2Uge1xyXG4gIG1heC13aWR0aDogMTIwMHB4O1xyXG59XHJcblxyXG4ubW9kYWwtaGVhZGVyIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGp1c3RpZnktY29udGVudDogc3BhY2UtYmV0d2VlbjtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIHBhZGRpbmc6IDIwcHggMjRweDtcclxuICBib3JkZXItYm90dG9tOiAxcHggc29saWQgI2UwZTBlMDtcclxufVxyXG5cclxuLm1vZGFsLWhlYWRlciBoMiB7XHJcbiAgZm9udC1zaXplOiAyMHB4O1xyXG4gIGZvbnQtd2VpZ2h0OiA2MDA7XHJcbiAgY29sb3I6ICMxYTFhMWE7XHJcbiAgbWFyZ2luOiAwO1xyXG59XHJcblxyXG4ubW9kYWwtaGVhZGVyLXJpZ2h0IHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XHJcbiAgZ2FwOiAxNnB4O1xyXG59XHJcblxyXG4ubG9ncy1pbmZvLW1vZGFsIHtcclxuICBkaXNwbGF5OiBmbGV4O1xyXG4gIGdhcDogMTJweDtcclxuICBmb250LXNpemU6IDEzcHg7XHJcbiAgY29sb3I6ICM2NjY7XHJcbn1cclxuXHJcbi5tb2RhbC1jbG9zZSB7XHJcbiAgd2lkdGg6IDMycHg7XHJcbiAgaGVpZ2h0OiAzMnB4O1xyXG4gIGJvcmRlcjogbm9uZTtcclxuICBiYWNrZ3JvdW5kOiB0cmFuc3BhcmVudDtcclxuICBjdXJzb3I6IHBvaW50ZXI7XHJcbiAgZGlzcGxheTogZmxleDtcclxuICBhbGlnbi1pdGVtczogY2VudGVyO1xyXG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xyXG4gIGJvcmRlci1yYWRpdXM6IDRweDtcclxuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcclxuICBwYWRkaW5nOiAwO1xyXG59XHJcblxyXG4ubW9kYWwtY2xvc2U6aG92ZXIge1xyXG4gIGJhY2tncm91bmQ6ICNmNWY1ZjU7XHJcbn1cclxuXHJcbi5tb2RhbC1jbG9zZSBzdmcge1xyXG4gIHdpZHRoOiAyMHB4O1xyXG4gIGhlaWdodDogMjBweDtcclxuICBzdHJva2Utd2lkdGg6IDI7XHJcbiAgY29sb3I6ICM2NjY7XHJcbn1cclxuXHJcbi5tb2RhbC1ib2R5IHtcclxuICBmbGV4OiAxO1xyXG4gIG92ZXJmbG93LXk6IGF1dG87XHJcbiAgcGFkZGluZzogMjRweDtcclxuICBtaW4taGVpZ2h0OiAwO1xyXG59XHJcblxyXG4uZGVmaW5pdGlvbi1jb250ZW50LWZ1bGwge1xyXG4gIGxpbmUtaGVpZ2h0OiAxLjY7XHJcbn1cclxuXHJcbi5sb2ctY29udGVudC1mdWxsIHtcclxuICBwYWRkaW5nOiAxMnB4O1xyXG4gIGJhY2tncm91bmQ6ICMxZTFlMWU7XHJcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xyXG4gIGZvbnQtZmFtaWx5OiAnQ29uc29sYXMnLCAnTW9uYWNvJywgJ0NvdXJpZXIgTmV3JywgbW9ub3NwYWNlO1xyXG4gIGZvbnQtc2l6ZTogMTJweDtcclxuICBsaW5lLWhlaWdodDogMS40O1xyXG4gIG1heC1oZWlnaHQ6IGNhbGMoOTB2aCAtIDEyMHB4KTtcclxuICBvdmVyZmxvdy15OiBhdXRvO1xyXG59XHJcblxyXG4ubG9nLXRleHQtZnVsbCB7XHJcbiAgbWFyZ2luOiAwO1xyXG4gIHdoaXRlLXNwYWNlOiBwcmUtd3JhcDtcclxuICB3b3JkLXdyYXA6IGJyZWFrLXdvcmQ7XHJcbiAgY29sb3I6ICNkNGQ0ZDQ7XHJcbn1cclxuPC9zdHlsZT5cclxuXHJcbiJdLCJtYXBwaW5ncyI6IkFBbU9BLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25EOzs7Ozs7QUFMYztBQU1kLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEM7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQztBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQztBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUM7QUFDRjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQztBQUNILENBQUM7QUFDRDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUM7QUFDRjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUM7QUFDRjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNWLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekUsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9JLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQztBQUNILENBQUM7QUFDRDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQztBQUNGO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekUsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQztBQUNGO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDO0FBQ0Y7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RGLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQztBQUNEO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZFLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQztBQUNILENBQUM7QUFDRDtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDO0FBQ0Q7QUFDQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUM7QUFDRjtBQUNBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQztBQUNGO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FB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