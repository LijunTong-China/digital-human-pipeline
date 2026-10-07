import { createHotContext as __vite__createHotContext } from "/@vite/client";import.meta.hot = __vite__createHotContext("/src/views/Videos.vue");import { ref, computed, onMounted, onUnmounted, watch } from "/node_modules/.vite/deps/vue.js?v=99b192bf"
import { useRoute, useRouter } from "/node_modules/.vite/deps/vue-router.js?v=99b192bf"
import { API_BASE_URL } from "/src/utils/apiConfig.js"
import AppHeader from "/src/components/AppHeader.vue"
import AlertModal from "/src/components/AlertModal.vue"


const _sfc_main = {
  __name: 'Videos',
  setup(__props, { expose: __expose }) {
  __expose();

const route = useRoute()
const router = useRouter()
const articles = ref([])
const loading = ref(true)
const filterSelected = ref(false)  // 默认显示待审核（未选中）
const filterRejected = ref(null)
const statusFilter = ref('pending')  // 状态筛选：pending, selected, deleted
const filterPlatform = ref(null)  // 平台筛选：默认全部渠道
const filterTag = ref('AI')  // 标签筛选：默认 AI
const pagination = ref(null)
const currentPage = ref(1)
const sortBy = ref('published_at')  // 默认按时间排序
const statistics = ref(null)
const searchKeyword = ref('')  // 搜索关键词
const jumpPage = ref(null)  // 跳转页码输入

// 发布计划面板 (GET /api/zhihu/video-schedule)
const showSchedule = ref(false)
const scheduleLoading = ref(false)
const scheduleItems = ref([])
const scheduleSummary = ref(null)

// Charles 状态
const charlesStatus = ref(null)
const statusShownAlert = ref(false)
const showStopAlert = ref(false)
const stopAlertMessage = ref('')

// 新建文章相关
const showCreateModal = ref(false)
const newArticle = ref({
  title: '',
  content: '',
  platform: 'manual',
  account_target: 'AI',  // AI / 经济学 / 心理学
  content_type_image: true,  // 是否制作图文
  content_type_video: false,  // 是否制作视频
})

// 是否显示目标账号选项 (选了图文或视频才显示)
const showAccountTarget = computed(() => {
  return newArticle.value.content_type_image || newArticle.value.content_type_video
})

const onContentTypeChange = () => {
  // 允许同时勾图文和视频
}
const creating = ref(false)
const generatingTitle = ref(false)

// 选中设置相关
const showSelectModal = ref(false)
const selectingArticle = ref(null)
const selecting = ref(false)
const selectSettings = ref({
  account_target: 'AI',  // AI / 经济学 / 心理学
  content_type_image: false,
  content_type_video: false,
})

const showSelectAccountTarget = computed(() => {
  return selectSettings.value.content_type_image || selectSettings.value.content_type_video
})

const hasSelectContentType = computed(() => {
  return selectSettings.value.content_type_image || selectSettings.value.content_type_video
})

const onSelectContentTypeChange = () => {
  // 允许同时勾图文和视频
}

// 文章编辑相关
const showContentModal = ref(false)
const viewingArticle = ref(null)
const editingArticle = ref({
  id: '',
  title: '',
  content: '',
  url: ''
})
const loadingArticleContent = ref(false)
const saving = ref(false)
const saveSuccess = ref(false)
const savingAndSelecting = ref(false)
const arrangingType = ref(null)  // 当前正在安排的类型: 'video' | 'image' | null
const recrawling = ref(false)

// 判断是否已安排视频（必须同时满足 is_selected=true 且 content_type 包含 video）
const isArrangedVideo = computed(() => {
  return editingArticle.value.is_selected && (editingArticle.value.content_type === 'video' || editingArticle.value.content_type === 'both')
})

// 判断是否已安排图文（必须同时满足 is_selected=true 且 content_type 包含 image）
const isArrangedImage = computed(() => {
  return editingArticle.value.is_selected && (editingArticle.value.content_type === 'image' || editingArticle.value.content_type === 'both')
})

// 根据当前筛选标签确定目标账号
// 量化交易归属于经济学账号，其他标签直接对应
const getAccountTarget = () => {
  const tagToAccount = {
    'AI': 'AI',
    '量化交易': '经济学',
    '经济学': '经济学',
    '心理学': '心理学'
  }
  return tagToAccount[filterTag.value] || 'AI'
}

// 批量操作相关
const selectedArticleIds = ref(new Set())
const batchDeleting = ref(false)

// AI过滤相关
const aiFiltering = ref(false)
const showAIFilterModal = ref(false)
const aiFilterArticles = ref([])
const aiFilterTotalChecked = ref(0)
const aiFilterDeleting = ref(false)
// 提示词编辑弹窗
const showPromptEditModal = ref(false)
const editingPrompt = ref('')
const savingPrompt = ref(false)
const loadingPrompt = ref(false)

const statusClass = computed(() => {
  if (!charlesStatus.value) return 'status-unknown'
  const s = charlesStatus.value
  if (s.status === 'dead') return 'status-dead'
  if (s.status === 'working') {
    // 连续空轮超过 10 次，或最后采集时间超过 24 小时，视为异常
    if (s.empty_cycles >= 10) return 'status-warning'
    if (s.last_new_article_time) {
      const lastTime = new Date(s.last_new_article_time).getTime()
      const now = Date.now()
      if (now - lastTime > 24 * 60 * 60 * 1000) return 'status-warning'
    }
    return 'status-working'
  }
  return 'status-unknown'
})

const statusText = computed(() => {
  if (!charlesStatus.value) return '未知'
  const s = charlesStatus.value
  if (s.status === 'dead') return '已停止'
  if (s.status === 'working') {
    if (statusClass.value === 'status-warning') return '采集异常'
    return '运行中'
  }
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
          stopAlertMessage.value = `Charles 已停止运行！${errorMsg}\n\n请检查并重新启动 Charles。`
          showStopAlert.value = true
        }
      }
    }
  } catch (error) {
    console.error('获取状态失败:', error)
  }
}

// 获取发布计划 (管道里已选未发完的视频)
const fetchSchedule = async () => {
  scheduleLoading.value = true
  try {
    const response = await fetch(`${API_BASE_URL}/api/zhihu/video-schedule`)
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        scheduleItems.value = result.data?.items || []
        scheduleSummary.value = result.data?.summary || null
      }
    }
  } catch (error) {
    console.error('获取发布计划失败:', error)
  } finally {
    scheduleLoading.value = false
  }
}

// 新鲜度: 事件时间 (published_at, 没有就 created_at) 距今天数
const freshAgeDays = (article) => {
  const t = article.published_at || article.created_at
  if (!t) return null
  const days = Math.floor((Date.now() - new Date(t).getTime()) / 86400000)
  return days < 0 ? 0 : days
}

const freshBadgeClassByDays = (days) => {
  if (days === null) return ''
  if (days <= 3) return 'fresh-hot'     // Fresh 强保底窗口内
  if (days <= 7) return 'fresh-ok'      // 还在候选拉取窗口内
  return 'fresh-stale'
}

const freshBadgeClass = (article) => freshBadgeClassByDays(freshAgeDays(article))

const videoStatusText = (s) => {
  const map = {
    pending: '排队', processing: '制作中', completed: '已完成',
    failed: '失败', published: '已发'
  }
  return map[s] || '排队'
}

// 平台单元格: 有排期时间显示时间, 否则显示状态
const platformCell = (status, scheduledAt) => {
  if (scheduledAt) {
    const d = new Date(scheduledAt)
    const mm = (d.getMonth() + 1).toString().padStart(2, '0')
    const dd = d.getDate().toString().padStart(2, '0')
    const hh = d.getHours().toString().padStart(2, '0')
    return `${mm}-${dd} ${hh}:00`
  }
  const map = {
    approved: '待排期', scheduled: '已排期', published: '已发',
    failed: '失败', abandoned: '放弃', pending: '处理中', processing: '处理中'
  }
  return map[status] || '-'
}

// 获取知乎文章列表
const fetchArticles = async (page = 1) => {
  loading.value = true
  // 切换页面时清空选中状态
  if (page !== currentPage.value) {
    selectedArticleIds.value.clear()
  }
  try {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: '20',
      sort_by: sortBy.value
    })
    
    // 待审核：filterSelected=false, filterRejected=null → is_selected=0, 不传 is_deleted（后端默认排除已删除）
    // 已安排：filterSelected=true, filterRejected=null → is_selected=1, 不传 is_deleted（后端默认排除已删除）
    // 已删除：filterRejected=true → is_deleted=1
    // 注意：当有搜索关键词且没有明确指定状态时，搜索所有状态（不传 is_selected）
    const hasSearchKeyword = searchKeyword.value && searchKeyword.value.trim()
    const hasExplicitStatus = route.query.status
    
    if (filterRejected.value === true) {
      params.append('is_deleted', '1')
    } else if (!hasSearchKeyword || hasExplicitStatus) {
      // 没有搜索关键词，或者有明确指定状态时，按状态筛选
      if (filterSelected.value !== null) {
        params.append('is_selected', filterSelected.value ? '1' : '0')
      }
      // 不传 is_deleted，让后端默认排除已删除的文章
    }
    // 如果有搜索关键词但没有明确指定状态，则搜索所有状态（不传 is_selected）
    
    // 如果有搜索关键词，添加到参数中
    if (searchKeyword.value && searchKeyword.value.trim()) {
      params.append('title', searchKeyword.value.trim())
    }
    
    // 如果有平台筛选，添加到参数中
    if (filterPlatform.value) {
      params.append('platform', filterPlatform.value)
    }
    
    // 如果有标签筛选，添加到参数中
    if (filterTag.value) {
      params.append('tag', filterTag.value)
    }
    
    // 使用统一的 API 端点（与后端服务在同一端口）
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles?${params}`)
    
    if (response.ok) {
      const result = await response.json()
      // 兼容两种响应格式：{code: 0, data: [], pagination: {}} 和 {code: 0, msg: "ok", data: [], pagination: {}}
      if (result.code === 0 || result.code === 200) {
        articles.value = result.data || []
        pagination.value = result.pagination
        currentPage.value = page
      } else {
        console.error('获取文章列表失败:', result.msg || result.message)
        articles.value = []
      }
    } else {
      console.error('API 请求失败:', response.status)
      articles.value = []
    }
  } catch (error) {
    console.error('获取文章列表出错:', error)
    articles.value = []
  } finally {
    loading.value = false
  }
}

// 切换选中状态
const toggleSelect = async (article) => {
  // 如果已选中，直接取消选中
  if (article.is_selected) {
    await updateSelectStatus(article, false)
    return
  }
  
  // 如果未选中，弹出设置弹窗
  selectingArticle.value = article
  // 根据文章当前状态初始化设置
  selectSettings.value = {
    account_target: article.account_target || 'AI',
    content_type_image: article.content_type === 'image' || article.content_type === 'both',
    content_type_video: article.content_type === 'video' || article.content_type === 'both',
  }
  showSelectModal.value = true
}

// 确认选中
const confirmSelect = async () => {
  if (!hasSelectContentType.value || !selectingArticle.value) return
  
  selecting.value = true
  try {
    const article = selectingArticle.value
    
    // 构建 content_type
    let content_type = null
    if (selectSettings.value.content_type_image && selectSettings.value.content_type_video) {
      content_type = 'both'
    } else if (selectSettings.value.content_type_image) {
      content_type = 'image'
    } else if (selectSettings.value.content_type_video) {
      content_type = 'video'
    }
    
    // 调用 API 更新选中状态
    await updateSelectStatus(
      article, 
      true, 
      content_type,
      selectSettings.value.account_target,
    )
    
    // 关闭弹窗
    closeSelectModal()
  } catch (error) {
    console.error('确认选中出错:', error)
    alert('设置失败，请稍后重试')
  } finally {
    selecting.value = false
  }
}

// 更新选中状态的通用函数
const updateSelectStatus = async (article, is_selected, content_type = null, account_target = null) => {
  try {
    const apiUrl = API_BASE_URL
    const body = { is_selected }
    
    if (is_selected) {
      if (content_type) body.content_type = content_type
      if (account_target) body.account_target = account_target
    }
    
    const response = await fetch(`${apiUrl}/api/zhihu/articles/${article.id}/select`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body)
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        // 更新本地状态
        article.is_selected = is_selected
        if (content_type) article.content_type = content_type
        if (account_target) article.account_target = account_target
        
        // 刷新统计信息
        fetchStatistics()
        
        // 如果当前是"待审核"列表且设置为已安排，或者当前是"已安排"列表且取消安排，从列表中移除
        if ((statusFilter.value === 'pending' && is_selected) || 
            (statusFilter.value === 'selected' && !is_selected)) {
          articles.value = articles.value.filter(a => a.id !== article.id)
        }
      } else {
        alert('更新失败: ' + (result.msg || result.message))
      }
    } else {
      alert('更新失败，请稍后重试')
    }
  } catch (error) {
    console.error('更新选中状态出错:', error)
    alert('更新失败，请稍后重试')
  }
}

// 关闭选中设置弹窗
const closeSelectModal = () => {
  showSelectModal.value = false
  selectingArticle.value = null
  selectSettings.value = {
    account_target: 'AI',
    content_type_image: false,
    content_type_video: false,
  }
}

// 标记为删除的
const markRejected = async (article) => {
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles/${article.id}/delete`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        is_deleted: !article.is_deleted
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        // 更新本地状态
        article.is_deleted = !article.is_deleted
        // 如果标记为删除，从列表中移除（除非当前正在查看"删除的"列表）
        if (article.is_deleted && filterRejected.value !== true) {
          articles.value = articles.value.filter(a => a.id !== article.id)
        }
        // 刷新统计信息
        fetchStatistics()
      } else {
        alert('更新失败: ' + (result.msg || result.message))
      }
    } else {
      alert('更新失败，请稍后重试')
    }
  } catch (error) {
    console.error('标记失败:', error)
    alert('更新失败，请稍后重试')
  }
}

// 计算可见的页码列表
const visiblePages = computed(() => {
  if (!pagination.value || pagination.value.total_pages <= 1) {
    return []
  }
  
  const current = pagination.value.page
  const total = pagination.value.total_pages
  const pages = []
  
  // 如果总页数少于等于7页，显示所有页码
  if (total <= 7) {
    for (let i = 1; i <= total; i++) {
      pages.push(i)
    }
  } else {
    // 总页数大于7页，显示当前页附近的页码
    if (current <= 4) {
      // 当前页在前4页，显示前5页 + ... + 最后一页
      for (let i = 1; i <= 5; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(total)
    } else if (current >= total - 3) {
      // 当前页在后4页，显示第一页 + ... + 后5页
      pages.push(1)
      pages.push('...')
      for (let i = total - 4; i <= total; i++) {
        pages.push(i)
      }
    } else {
      // 当前页在中间，显示第一页 + ... + 当前页附近3页 + ... + 最后一页
      pages.push(1)
      pages.push('...')
      for (let i = current - 1; i <= current + 1; i++) {
        pages.push(i)
      }
      pages.push('...')
      pages.push(total)
    }
  }
  
  return pages
})

// 切换页码
const changePage = (page) => {
  if (page >= 1 && (!pagination.value || page <= pagination.value.total_pages)) {
    // 切换页面时清空选中状态
    selectedArticleIds.value.clear()
    // 构建完整的 URL 参数
    const query = { page: page.toString() }
    query.status = statusFilter.value
    if (filterPlatform.value) {
      query.platform = filterPlatform.value
    }
    if (filterTag.value) {
      query.tag = filterTag.value
    }
    if (sortBy.value !== 'published_at') {
      query.sort = sortBy.value
    }
    if (searchKeyword.value && searchKeyword.value.trim()) {
      query.search = searchKeyword.value.trim()
    }
    router.replace({ query })
    fetchArticles(page)
  }
}

// 跳转到指定页
const jumpToPage = () => {
  if (!jumpPage.value || !pagination.value) {
    return
  }
  
  const page = parseInt(jumpPage.value)
  if (page >= 1 && page <= pagination.value.total_pages) {
    changePage(page)
    jumpPage.value = null
  } else {
    alert(`请输入 1-${pagination.value.total_pages} 之间的页码`)
  }
}

// 批量选择相关
const toggleArticleSelection = (articleId) => {
  if (selectedArticleIds.value.has(articleId)) {
    selectedArticleIds.value.delete(articleId)
  } else {
    selectedArticleIds.value.add(articleId)
  }
  // 触发响应式更新
  selectedArticleIds.value = new Set(selectedArticleIds.value)
}

// 全选/取消全选
const toggleSelectAll = () => {
  if (isAllSelected.value) {
    // 取消全选
    selectedArticleIds.value.clear()
  } else {
    // 全选当前页（排除已删除的文章）
    const selectableArticles = articles.value.filter(a => !a.is_deleted)
    selectedArticleIds.value = new Set(selectableArticles.map(a => a.id))
  }
}

// 计算是否全选
const isAllSelected = computed(() => {
  if (articles.value.length === 0) return false
  const selectableArticles = articles.value.filter(a => !a.is_deleted)
  if (selectableArticles.length === 0) return false
  return selectableArticles.every(a => selectedArticleIds.value.has(a.id))
})

// 计算是否部分选中（用于显示 indeterminate 状态）
const isIndeterminate = computed(() => {
  const selectableArticles = articles.value.filter(a => !a.is_deleted)
  if (selectableArticles.length === 0) return false
  const selectedCount = selectableArticles.filter(a => selectedArticleIds.value.has(a.id)).length
  return selectedCount > 0 && selectedCount < selectableArticles.length
})

// 批量删除
const batchDelete = async () => {
  if (selectedArticleIds.value.size === 0) return
  
  batchDeleting.value = true
  const apiUrl = API_BASE_URL
  const ids = Array.from(selectedArticleIds.value)
  
  try {
    // 调用批量删除 API
    const response = await fetch(`${apiUrl}/api/zhihu/articles/batch-delete`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
        article_ids: ids,
            is_deleted: true
          })
        })
        
        if (response.ok) {
          const result = await response.json()
      if (result.code !== 0 && result.code !== 200) {
        console.error('批量删除失败:', result.msg || result.message)
          }
        } else {
      console.error('批量删除失败:', response.status)
    }
  } catch (error) {
    console.error('批量删除出错:', error)
  } finally {
    // 无论成功失败，都清空选中状态并刷新
    selectedArticleIds.value.clear()
    batchDeleting.value = false
    fetchArticles(currentPage.value)
    fetchStatistics()
  }
}

// AI智能过滤 - 打开提示词编辑弹窗
const startAIFilter = async () => {
  if (!filterTag.value) return
  loadingPrompt.value = true
  const apiUrl = API_BASE_URL

  try {
    // 从后端加载当前 tag 的提示词
    const response = await fetch(`${apiUrl}/api/zhihu/articles/ai-filter?tag=${encodeURIComponent(filterTag.value)}`)
    if (response.ok) {
      const result = await response.json()
      editingPrompt.value = result.data?.prompt || ''
    } else {
      editingPrompt.value = ''
    }
  } catch (e) {
    console.error('加载提示词失败:', e)
    editingPrompt.value = ''
  } finally {
    loadingPrompt.value = false
  }

  showPromptEditModal.value = true
}

// 保存提示词到 yaml
const savePrompt = async () => {
  if (!filterTag.value || !editingPrompt.value.trim()) return
  savingPrompt.value = true
  const apiUrl = API_BASE_URL

  try {
    const response = await fetch(`${apiUrl}/api/zhihu/articles/ai-filter`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag: filterTag.value, prompt: editingPrompt.value.trim() })
    })
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        alert('提示词已保存')
      }
    }
  } catch (e) {
    console.error('保存提示词失败:', e)
  } finally {
    savingPrompt.value = false
  }
}

// 执行AI过滤
const runAIFilter = async () => {
  if (!filterTag.value || !editingPrompt.value.trim()) return
  aiFiltering.value = true
  const apiUrl = API_BASE_URL

  try {
    const response = await fetch(`${apiUrl}/api/zhihu/articles/ai-filter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tag: filterTag.value, prompt: editingPrompt.value.trim() })
    })

    if (!response.ok) {
      console.error('AI过滤请求失败:', response.status)
      return
    }

    const result = await response.json()
    if (result.code !== 0 && result.code !== 200) {
      console.error('AI过滤失败:', result.msg || result.message)
      alert('AI过滤失败: ' + (result.msg || result.message || ''))
      return
    }

    const data = result.data || {}
    aiFilterArticles.value = data.articles_to_delete || []
    aiFilterTotalChecked.value = data.total_checked || 0

    // 关闭提示词编辑弹窗
    showPromptEditModal.value = false

    if (aiFilterArticles.value.length === 0) {
      alert('AI分析完成，没有需要删除的文章')
      return
    }

    showAIFilterModal.value = true
  } catch (e) {
    console.error('AI过滤出错:', e)
  } finally {
    aiFiltering.value = false
  }
}

// 确认AI过滤删除
const confirmAIFilterDelete = async () => {
  if (aiFilterArticles.value.length === 0) return
  aiFilterDeleting.value = true
  const apiUrl = API_BASE_URL
  const ids = aiFilterArticles.value.map(a => a.id)

  try {
    const response = await fetch(`${apiUrl}/api/zhihu/articles/batch-delete`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ article_ids: ids, is_deleted: true })
    })

    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        showAIFilterModal.value = false
        aiFilterArticles.value = []
        fetchArticles(currentPage.value)
        fetchStatistics()
      } else {
        console.error('批量删除失败:', result.msg || result.message)
      }
    } else {
      console.error('批量删除失败:', response.status)
    }
  } catch (e) {
    console.error('AI过滤删除出错:', e)
  } finally {
    aiFilterDeleting.value = false
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

// 格式化内容长度
const formatContentLength = (length) => {
  if (!length) return ''
  if (length < 1000) {
    return `${length}字`
  } else {
    return `${(length / 1000).toFixed(1)}k字`
  }
}

// KIMI 评分徽章: 按 RED/YELLOW 前缀 + 分数档位返回 class
// 后端 reason 字段约定: [RED] / [YELLOW] / 无前缀 (绿) — 见 save_kimi_scores()
const getKimiBadgeClass = (article) => {
  const reason = article.kimi_pick_reason || ''
  if (reason.startsWith('[RED]')) return 'kimi-red'
  if (reason.startsWith('[YELLOW]')) return 'kimi-yellow'
  const s = Number(article.kimi_pick_score) || 0
  if (s >= 60) return 'kimi-high'
  if (s >= 30) return 'kimi-mid'
  return 'kimi-low'
}

// hover 看到的完整 tooltip: 理由全文 + 评分时间
const getKimiTooltip = (article) => {
  const parts = []
  if (article.kimi_pick_reason) parts.push(article.kimi_pick_reason)
  if (article.kimi_pick_scored_at) {
    parts.push(`(评分时间: ${article.kimi_pick_scored_at.replace('T', ' ').slice(0, 16)})`)
  }
  return parts.join(' ')
}

// 列表上显示的简短理由 (前 18 字, 去掉 [RED]/[YELLOW] 前缀)
const getKimiReasonShort = (article) => {
  let r = article.kimi_pick_reason || ''
  r = r.replace(/^\[(RED|YELLOW)\]\s*/, '')
  if (r.length > 18) r = r.slice(0, 18) + '…'
  return r
}

// 获取统计信息
const fetchStatistics = async () => {
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/statistics`)
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        statistics.value = result.data
      }
    }
  } catch (error) {
    console.error('获取统计信息出错:', error)
  }
}

// 设置状态筛选
// 监听 statusFilter 变化，同步到 filterSelected/filterRejected
watch(statusFilter, (status) => {
  if (status === 'pending') {
    filterSelected.value = false
    filterRejected.value = null
  } else if (status === 'selected') {
    filterSelected.value = true
    filterRejected.value = null
  } else if (status === 'deleted') {
    filterSelected.value = null
    filterRejected.value = true
  }
})

// 监听筛选条件变化，同时更新 URL
watch([statusFilter, filterPlatform, filterTag, sortBy], () => {
  // 筛选条件变化时清空选中状态
  selectedArticleIds.value.clear()
  
  // 更新 URL 参数
  const query = {}
  query.status = statusFilter.value
  if (filterPlatform.value) {
    query.platform = filterPlatform.value
  }
  if (filterTag.value) {
    query.tag = filterTag.value
  }
  if (sortBy.value !== 'published_at') {
    query.sort = sortBy.value
  }
  if (searchKeyword.value && searchKeyword.value.trim()) {
    query.search = searchKeyword.value.trim()
  }
  router.replace({ query })
  
  fetchArticles(1)
})

// 监听搜索关键词变化（从 SearchBox 组件通过 URL 传入）
watch(() => route.query.search, (newSearch) => {
  const newKeyword = newSearch || ''
  if (searchKeyword.value !== newKeyword) {
    searchKeyword.value = newKeyword
    fetchArticles(1)
  }
})

// 生成标题
const generateTitle = async () => {
  if (!newArticle.value.content || generatingTitle.value) return
  
  generatingTitle.value = true
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles/generate-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: newArticle.value.content
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        newArticle.value.title = result.data?.title || ''
      } else {
        alert('生成标题失败: ' + (result.msg || result.message))
      }
    } else {
      alert('生成标题失败，请稍后重试')
    }
  } catch (error) {
    console.error('生成标题出错:', error)
    alert('生成标题失败，请稍后重试')
  } finally {
    generatingTitle.value = false
  }
}

// 创建文章
const createArticle = async () => {
  if (!newArticle.value.content || creating.value) return
  
  // 至少选择一种制作类型
  if (!newArticle.value.content_type_image && !newArticle.value.content_type_video) {
    alert('请至少选择一种制作类型 (图文 或 视频)')
    return
  }
  
  creating.value = true
  try {
    const apiUrl = API_BASE_URL
    
    let content_type = 'image'
    if (newArticle.value.content_type_image && newArticle.value.content_type_video) {
      content_type = 'both'
    } else if (newArticle.value.content_type_video) {
      content_type = 'video'
    }
    
    const response = await fetch(`${apiUrl}/api/zhihu/articles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: newArticle.value.title || '',
        content: newArticle.value.content,
        platform: 'manual',
        account_target: newArticle.value.account_target || 'AI',
        content_type: content_type,
        is_selected: 1
      })
    })
    
    let ok = false
    let errMsg = ''
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        ok = true
      } else {
        errMsg = result.msg || result.message || '未知错误'
      }
    } else {
      errMsg = `请求失败: ${response.status}`
    }
    
    if (ok) {
      newArticle.value = {
        title: '',
        content: '',
        platform: 'manual',
        account_target: 'AI',
        content_type_image: true,
        content_type_video: false,
      }
      closeCreateModal()
      fetchArticles(currentPage.value)
      fetchStatistics()
    } else {
      alert('创建失败: ' + errMsg)
    }
  } catch (error) {
    console.error('创建文章出错:', error)
    alert('创建失败，请稍后重试')
  } finally {
    creating.value = false
  }
}

// 显示文章内容（编辑模式）
const showArticleContent = async (article) => {
  viewingArticle.value = article
  showContentModal.value = true
  editingArticle.value = {
    id: article.id,
    title: article.title || '',
    content: '',
    url: article.url || '',
    content_type: article.content_type || null,
    is_selected: article.is_selected || false
  }
  loadingArticleContent.value = true
  
  try {
    // 如果文章已经有 content 字段，直接使用
    if (article.content) {
      editingArticle.value.content = article.content
      loadingArticleContent.value = false
      return
    }
    
    // 否则从 API 获取文章详情
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles/${article.id}`)
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        editingArticle.value.content = result.data?.content || ''
        editingArticle.value.title = result.data?.title || article.title || ''
      } else {
        alert('获取内容失败: ' + (result.msg || result.message))
        showContentModal.value = false
      }
    } else {
      alert('获取内容失败，请稍后重试')
      showContentModal.value = false
    }
  } catch (error) {
    console.error('获取文章内容出错:', error)
    alert('获取内容失败，请稍后重试')
    showContentModal.value = false
  } finally {
    loadingArticleContent.value = false
  }
}

// 关闭编辑模态框
const closeEditModal = () => {
  showContentModal.value = false
  editingArticle.value = { id: '', title: '', content: '', url: '' }
}

// 关闭新建模态框
const closeCreateModal = () => {
  showCreateModal.value = false
  newArticle.value = { 
    title: '', 
    content: '', 
    platform: 'manual', 
    account_target: 'AI',
    content_type_image: true,
    content_type_video: false,
  }
}

// 为编辑模式生成标题
const generateTitleForEdit = async () => {
  if (!editingArticle.value.content || generatingTitle.value) return
  
  generatingTitle.value = true
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles/generate-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: editingArticle.value.content
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        editingArticle.value.title = result.data?.title || ''
      } else {
        alert('生成标题失败: ' + (result.msg || result.message))
      }
    } else {
      alert('生成标题失败，请稍后重试')
    }
  } catch (error) {
    console.error('生成标题出错:', error)
    alert('生成标题失败，请稍后重试')
  } finally {
    generatingTitle.value = false
  }
}

// 重新采集文章内容
const recrawlArticle = async () => {
  if (!viewingArticle.value || recrawling.value) return
  
  recrawling.value = true
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles/${viewingArticle.value.id}/recrawl`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        // 更新编辑框中的内容
        editingArticle.value.content = result.data?.content || ''
        editingArticle.value.title = result.data?.title || editingArticle.value.title
        
        // 更新本地列表中的文章
        const articleIndex = articles.value.findIndex(a => a.id === viewingArticle.value.id)
        if (articleIndex !== -1) {
          articles.value[articleIndex].content = result.data?.content || ''
          articles.value[articleIndex].content_length = result.data?.content_length || 0
          if (result.data?.published_at) {
            articles.value[articleIndex].published_at = result.data.published_at
          }
        }
        // 成功时不弹窗，内容已自动更新到编辑框
      } else {
        alert('重新采集失败: ' + (result.msg || result.message))
      }
    } else {
      alert('重新采集失败，请稍后重试')
    }
  } catch (error) {
    console.error('重新采集出错:', error)
    alert('重新采集失败，请稍后重试')
  } finally {
    recrawling.value = false
  }
}

// 保存文章
const saveArticle = async () => {
  if (!editingArticle.value.content || saving.value) return
  
  saving.value = true
  try {
    const apiUrl = API_BASE_URL
    const response = await fetch(`${apiUrl}/api/zhihu/articles/${editingArticle.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: editingArticle.value.title || '',
        content: editingArticle.value.content
      })
    })
    
    if (response.ok) {
      const result = await response.json()
      if (result.code === 0 || result.code === 200) {
        // 更新本地列表中的文章
        const articleIndex = articles.value.findIndex(a => a.id === editingArticle.value.id)
        if (articleIndex !== -1) {
          articles.value[articleIndex].title = editingArticle.value.title
          articles.value[articleIndex].content = editingArticle.value.content
        }
        // 显示保存成功提示，不关闭弹窗
        saveSuccess.value = true
        setTimeout(() => { saveSuccess.value = false }, 2000)
      } else {
        alert('保存失败: ' + (result.msg || result.message))
      }
    } else {
      alert('保存失败，请稍后重试')
    }
  } catch (error) {
    console.error('保存文章出错:', error)
    alert('保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

// 保存并制作（保存文章后设置为选中状态，视频类型，目标账号AI）
const saveAndSelect = async () => {
  if (!editingArticle.value.content || savingAndSelecting.value) return
  
  savingAndSelecting.value = true
  try {
    const apiUrl = API_BASE_URL
    
    // 第一步：保存文章内容
    const saveResponse = await fetch(`${apiUrl}/api/zhihu/articles/${editingArticle.value.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        title: editingArticle.value.title || '',
        content: editingArticle.value.content
      })
    })
    
    if (!saveResponse.ok) {
      alert('保存失败，请稍后重试')
      return
    }
    
    const saveResult = await saveResponse.json()
    if (saveResult.code !== 0 && saveResult.code !== 200) {
      alert('保存失败: ' + (saveResult.msg || saveResult.message))
      return
    }
    
    // 更新本地列表中的文章
    const articleIndex = articles.value.findIndex(a => a.id === editingArticle.value.id)
    if (articleIndex !== -1) {
      articles.value[articleIndex].title = editingArticle.value.title
      articles.value[articleIndex].content = editingArticle.value.content
    }
    
    // 第二步：设置为选中状态（is_selected=true, content_type=video, account_target根据当前标签确定）
    const targetAccount = getAccountTarget()
    const selectResponse = await fetch(`${apiUrl}/api/zhihu/articles/${editingArticle.value.id}/select`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        is_selected: true,
        content_type: 'video',
        account_target: targetAccount
      })
    })
    
    if (selectResponse.ok) {
      const selectResult = await selectResponse.json()
      if (selectResult.code === 0 || selectResult.code === 200) {
        // 更新本地状态
        if (articleIndex !== -1) {
          articles.value[articleIndex].is_selected = true
          articles.value[articleIndex].content_type = 'video'
          articles.value[articleIndex].account_target = targetAccount
        }
        
        // 刷新统计信息
        fetchStatistics()
        
        // 如果当前是"待审核"列表，从列表中移除该文章
        if (statusFilter.value === 'pending') {
          articles.value = articles.value.filter(a => a.id !== editingArticle.value.id)
        }
        
        closeEditModal()
      } else {
        alert('设置制作状态失败: ' + (selectResult.msg || selectResult.message))
      }
    } else {
      alert('设置制作状态失败，请稍后重试')
    }
  } catch (error) {
    console.error('保存并制作出错:', error)
    alert('操作失败，请稍后重试')
  } finally {
    savingAndSelecting.value = false
  }
}

// 安排制作类型 (视频 / 图文)
const arrangeType = async (type) => {
  if (!editingArticle.value.content || arrangingType.value) return
  
  arrangingType.value = type
  try {
    const apiUrl = API_BASE_URL
    
    // 第一步: 保存文章内容
    const saveResponse = await fetch(`${apiUrl}/api/zhihu/articles/${editingArticle.value.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: editingArticle.value.title || '',
        content: editingArticle.value.content
      })
    })
    
    if (!saveResponse.ok) {
      alert('保存失败，请稍后重试')
      return
    }
    
    const articleIndex = articles.value.findIndex(a => a.id === editingArticle.value.id)
    if (articleIndex !== -1) {
      articles.value[articleIndex].title = editingArticle.value.title
      articles.value[articleIndex].content = editingArticle.value.content
    }
    
    // 第二步: 更新 content_type (已经安排了另一种就 both)
    let newContentType = type
    if (type === 'video' && isArrangedImage.value) {
      newContentType = 'both'
    } else if (type === 'image' && isArrangedVideo.value) {
      newContentType = 'both'
    }
    
    const targetAccount = getAccountTarget()
    const selectResponse = await fetch(`${apiUrl}/api/zhihu/articles/${editingArticle.value.id}/select`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        is_selected: true,
        content_type: newContentType,
        account_target: targetAccount
      })
    })
    
    if (selectResponse.ok) {
      const selectResult = await selectResponse.json()
      if (selectResult.code === 0 || selectResult.code === 200) {
        editingArticle.value.content_type = newContentType
        editingArticle.value.is_selected = true
        if (articleIndex !== -1) {
          articles.value[articleIndex].is_selected = true
          articles.value[articleIndex].content_type = newContentType
          articles.value[articleIndex].account_target = targetAccount
        }
        
        fetchStatistics()
        
        if (statusFilter.value === 'pending') {
          articles.value = articles.value.filter(a => a.id !== editingArticle.value.id)
          closeEditModal()
        }
      } else {
        alert('安排失败: ' + (selectResult.msg || selectResult.message))
        return
      }
    } else {
      alert('安排失败，请稍后重试')
      return
    }
  } catch (error) {
    console.error('安排制作出错:', error)
    alert('操作失败，请稍后重试')
  } finally {
    arrangingType.value = null
  }
}

onMounted(() => {
  // 从 URL 初始化筛选条件
  if (route.query.status) {
    statusFilter.value = route.query.status
    // 同步到 filterSelected/filterRejected
    if (route.query.status === 'selected') {
      filterSelected.value = true
      filterRejected.value = null
    } else if (route.query.status === 'deleted') {
      filterSelected.value = null
      filterRejected.value = true
    } else {
      filterSelected.value = false
      filterRejected.value = null
    }
  }
  
  if (route.query.platform) {
    filterPlatform.value = route.query.platform
  }
  
  if (route.query.tag) {
    filterTag.value = route.query.tag
  }
  
  if (route.query.sort) {
    sortBy.value = route.query.sort
  }
  
  // 初始化搜索关键词
  if (route.query.search) {
    searchKeyword.value = route.query.search
  }
  
  // 初始化页码
  const initialPage = parseInt(route.query.page) || 1
  fetchStatistics()
  fetchArticles(initialPage)
  fetchCharlesStatus()
  fetchSchedule()
})

const __returned__ = { route, router, articles, loading, filterSelected, filterRejected, statusFilter, filterPlatform, filterTag, pagination, currentPage, sortBy, statistics, searchKeyword, jumpPage, showSchedule, scheduleLoading, scheduleItems, scheduleSummary, charlesStatus, statusShownAlert, showStopAlert, stopAlertMessage, showCreateModal, newArticle, showAccountTarget, onContentTypeChange, creating, generatingTitle, showSelectModal, selectingArticle, selecting, selectSettings, showSelectAccountTarget, hasSelectContentType, onSelectContentTypeChange, showContentModal, viewingArticle, editingArticle, loadingArticleContent, saving, saveSuccess, savingAndSelecting, arrangingType, recrawling, isArrangedVideo, isArrangedImage, getAccountTarget, selectedArticleIds, batchDeleting, aiFiltering, showAIFilterModal, aiFilterArticles, aiFilterTotalChecked, aiFilterDeleting, showPromptEditModal, editingPrompt, savingPrompt, loadingPrompt, statusClass, statusText, showStatusDetail, fetchCharlesStatus, fetchSchedule, freshAgeDays, freshBadgeClassByDays, freshBadgeClass, videoStatusText, platformCell, fetchArticles, toggleSelect, confirmSelect, updateSelectStatus, closeSelectModal, markRejected, visiblePages, changePage, jumpToPage, toggleArticleSelection, toggleSelectAll, isAllSelected, isIndeterminate, batchDelete, startAIFilter, savePrompt, runAIFilter, confirmAIFilterDelete, formatDate, formatContentLength, getKimiBadgeClass, getKimiTooltip, getKimiReasonShort, fetchStatistics, generateTitle, createArticle, showArticleContent, closeEditModal, closeCreateModal, generateTitleForEdit, recrawlArticle, saveArticle, saveAndSelect, arrangeType, ref, computed, onMounted, onUnmounted, watch, get useRoute() { return useRoute }, get useRouter() { return useRouter }, get API_BASE_URL() { return API_BASE_URL }, AppHeader, AlertModal }
Object.defineProperty(__returned__, '__isScriptSetup', { enumerable: false, value: true })
return __returned__
}

}
import { createVNode as _createVNode, createElementVNode as _createElementVNode, createTextVNode as _createTextVNode, resolveComponent as _resolveComponent, normalizeClass as _normalizeClass, withCtx as _withCtx, openBlock as _openBlock, createElementBlock as _createElementBlock, createCommentVNode as _createCommentVNode, toDisplayString as _toDisplayString, vModelSelect as _vModelSelect, withDirectives as _withDirectives, renderList as _renderList, Fragment as _Fragment, withModifiers as _withModifiers, vModelText as _vModelText, withKeys as _withKeys, createBlock as _createBlock, vModelCheckbox as _vModelCheckbox, vModelRadio as _vModelRadio } from "/node_modules/.vite/deps/vue.js?v=99b192bf"

const _hoisted_1 = { class: "articles-page" }
const _hoisted_2 = { class: "page-header" }
const _hoisted_3 = { class: "header-controls" }
const _hoisted_4 = { class: "header-left" }
const _hoisted_5 = ["title"]
const _hoisted_6 = {
  key: 1,
  class: "status-warning-tip status-dead-tip"
}
const _hoisted_7 = { class: "filter-tabs" }
const _hoisted_8 = {
  key: 0,
  class: "count-badge"
}
const _hoisted_9 = {
  key: 0,
  class: "count-badge"
}
const _hoisted_10 = {
  key: 0,
  class: "count-badge"
}
const _hoisted_11 = {
  key: 0,
  class: "count-badge"
}
const _hoisted_12 = { value: "pending" }
const _hoisted_13 = { value: "selected" }
const _hoisted_14 = { value: "deleted" }
const _hoisted_15 = { class: "header-right" }
const _hoisted_16 = ["disabled"]
const _hoisted_17 = {
  key: 0,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": "2"
}
const _hoisted_18 = {
  key: 1,
  class: "spinning",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": "2"
}
const _hoisted_19 = { class: "schedule-panel" }
const _hoisted_20 = {
  key: 0,
  class: "schedule-summary"
}
const _hoisted_21 = { class: "schedule-toggle" }
const _hoisted_22 = {
  key: 0,
  class: "schedule-body"
}
const _hoisted_23 = {
  key: 0,
  class: "schedule-empty"
}
const _hoisted_24 = {
  key: 1,
  class: "schedule-empty"
}
const _hoisted_25 = {
  key: 2,
  class: "schedule-table"
}
const _hoisted_26 = ["title"]
const _hoisted_27 = { key: 1 }
const _hoisted_28 = {
  key: 0,
  class: "batch-actions-bar"
}
const _hoisted_29 = { class: "batch-actions-left" }
const _hoisted_30 = { class: "batch-checkbox-label" }
const _hoisted_31 = ["checked", "indeterminate"]
const _hoisted_32 = { class: "batch-checkbox-text" }
const _hoisted_33 = {
  key: 0,
  class: "selected-count"
}
const _hoisted_34 = {
  key: 0,
  class: "batch-actions-right"
}
const _hoisted_35 = ["disabled"]
const _hoisted_36 = { class: "articles-list" }
const _hoisted_37 = { class: "article-row" }
const _hoisted_38 = { class: "article-checkbox-label" }
const _hoisted_39 = ["checked", "onChange"]
const _hoisted_40 = ["onClick"]
const _hoisted_41 = { class: "article-title" }
const _hoisted_42 = { class: "article-meta-inline" }
const _hoisted_43 = {
  key: 0,
  class: "article-platform manual-badge"
}
const _hoisted_44 = {
  key: 1,
  class: "article-platform creator-badge",
  title: "对标博主热门视频转写稿注入 (creator_video_inject)"
}
const _hoisted_45 = ["title"]
const _hoisted_46 = ["title"]
const _hoisted_47 = { class: "kimi-reason-mini" }
const _hoisted_48 = {
  key: 5,
  class: "article-keyword"
}
const _hoisted_49 = { class: "meta-item" }
const _hoisted_50 = { class: "meta-item" }
const _hoisted_51 = {
  key: 6,
  class: "meta-item"
}
const _hoisted_52 = { class: "article-date" }
const _hoisted_53 = { class: "article-actions" }
const _hoisted_54 = ["onClick", "title"]
const _hoisted_55 = {
  key: 0,
  viewBox: "0 0 24 24",
  fill: "currentColor"
}
const _hoisted_56 = {
  key: 1,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor"
}
const _hoisted_57 = ["onClick", "title"]
const _hoisted_58 = {
  key: 1,
  class: "loading"
}
const _hoisted_59 = {
  key: 2,
  class: "empty"
}
const _hoisted_60 = {
  key: 3,
  class: "pagination"
}
const _hoisted_61 = ["disabled"]
const _hoisted_62 = { class: "page-numbers" }
const _hoisted_63 = ["onClick"]
const _hoisted_64 = {
  key: 1,
  class: "page-ellipsis"
}
const _hoisted_65 = ["disabled"]
const _hoisted_66 = { class: "page-jump" }
const _hoisted_67 = ["max"]
const _hoisted_68 = { class: "page-info" }
const _hoisted_69 = {
  key: 4,
  class: "modal-overlay"
}
const _hoisted_70 = { class: "modal-content create-article-modal" }
const _hoisted_71 = { class: "modal-header" }
const _hoisted_72 = {
  key: 0,
  class: "article-id-badge"
}
const _hoisted_73 = { class: "modal-header-actions" }
const _hoisted_74 = ["disabled"]
const _hoisted_75 = {
  key: 0,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor"
}
const _hoisted_76 = {
  key: 1,
  class: "spinning",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor"
}
const _hoisted_77 = ["href"]
const _hoisted_78 = { class: "modal-body" }
const _hoisted_79 = {
  key: 0,
  class: "loading-content"
}
const _hoisted_80 = { key: 1 }
const _hoisted_81 = { class: "form-group" }
const _hoisted_82 = { class: "title-input-group" }
const _hoisted_83 = ["disabled"]
const _hoisted_84 = { class: "form-group" }
const _hoisted_85 = { class: "char-count" }
const _hoisted_86 = { class: "form-actions" }
const _hoisted_87 = {
  key: 0,
  class: "save-success-tip"
}
const _hoisted_88 = ["disabled"]
const _hoisted_89 = {
  key: 0,
  class: "arrange-actions"
}
const _hoisted_90 = ["disabled"]
const _hoisted_91 = ["disabled"]
const _hoisted_92 = {
  key: 5,
  class: "modal-overlay"
}
const _hoisted_93 = { class: "modal-content create-article-modal" }
const _hoisted_94 = { class: "modal-body" }
const _hoisted_95 = { class: "form-group" }
const _hoisted_96 = { class: "title-input-group" }
const _hoisted_97 = ["disabled"]
const _hoisted_98 = { class: "form-group" }
const _hoisted_99 = { class: "char-count" }
const _hoisted_100 = { class: "form-group" }
const _hoisted_101 = { class: "checkbox-group" }
const _hoisted_102 = { class: "checkbox-label" }
const _hoisted_103 = { class: "checkbox-label" }
const _hoisted_104 = {
  key: 0,
  class: "form-group"
}
const _hoisted_105 = { class: "radio-group" }
const _hoisted_106 = { class: "radio-label" }
const _hoisted_107 = { class: "radio-label" }
const _hoisted_108 = { class: "radio-label" }
const _hoisted_109 = { class: "form-actions" }
const _hoisted_110 = ["disabled"]
const _hoisted_111 = {
  key: 6,
  class: "modal-overlay"
}
const _hoisted_112 = { class: "modal-content create-article-modal" }
const _hoisted_113 = { class: "modal-body" }
const _hoisted_114 = { class: "form-group" }
const _hoisted_115 = { class: "checkbox-group" }
const _hoisted_116 = { class: "checkbox-label" }
const _hoisted_117 = { class: "checkbox-label" }
const _hoisted_118 = {
  key: 0,
  class: "form-group"
}
const _hoisted_119 = { class: "radio-group" }
const _hoisted_120 = { class: "radio-label" }
const _hoisted_121 = { class: "radio-label" }
const _hoisted_122 = { class: "radio-label" }
const _hoisted_123 = { class: "form-actions" }
const _hoisted_124 = ["disabled"]
const _hoisted_125 = {
  key: 7,
  class: "modal-overlay"
}
const _hoisted_126 = { class: "modal-content prompt-edit-modal" }
const _hoisted_127 = { class: "modal-header" }
const _hoisted_128 = { class: "modal-body" }
const _hoisted_129 = { class: "form-actions prompt-actions" }
const _hoisted_130 = ["disabled"]
const _hoisted_131 = ["disabled"]
const _hoisted_132 = {
  key: 0,
  class: "spinning",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  "stroke-width": "2",
  style: {"width":"14px","height":"14px","margin-right":"4px"}
}
const _hoisted_133 = {
  key: 8,
  class: "modal-overlay"
}
const _hoisted_134 = { class: "modal-content ai-filter-modal" }
const _hoisted_135 = { class: "modal-header" }
const _hoisted_136 = { class: "modal-body" }
const _hoisted_137 = { class: "ai-filter-summary" }
const _hoisted_138 = { class: "ai-filter-list" }
const _hoisted_139 = { class: "ai-filter-index" }
const _hoisted_140 = { class: "ai-filter-title" }
const _hoisted_141 = { class: "ai-filter-id" }
const _hoisted_142 = { class: "form-actions" }
const _hoisted_143 = ["disabled"]

function _sfc_render(_ctx, _cache, $props, $setup, $data, $options) {
  const _component_router_link = _resolveComponent("router-link")

  return (_openBlock(), _createElementBlock(_Fragment, null, [
    _createVNode($setup["AppHeader"]),
    _createVNode($setup["AlertModal"], {
      show: $setup.showStopAlert,
      "onUpdate:show": _cache[0] || (_cache[0] = $event => (($setup.showStopAlert) = $event)),
      title: "Charles 已停止运行",
      message: $setup.stopAlertMessage
    }, null, 8 /* PROPS */, ["show", "message"]),
    _createElementVNode("div", _hoisted_1, [
      _createElementVNode("div", _hoisted_2, [
        _createElementVNode("div", _hoisted_3, [
          _createElementVNode("div", _hoisted_4, [
            _createVNode(_component_router_link, {
              to: "/charles-logs",
              class: _normalizeClass(["log-btn", $setup.statusClass])
            }, {
              default: _withCtx(() => [...(_cache[36] || (_cache[36] = [
                _createElementVNode("span", { class: "status-dot" }, null, -1 /* CACHED */),
                _createTextVNode(" Charles 工作日志 ", -1 /* CACHED */)
              ]))]),
              _: 1 /* STABLE */
            }, 8 /* PROPS */, ["class"]),
            ($setup.statusClass === 'status-warning')
              ? (_openBlock(), _createElementBlock("span", {
                  key: 0,
                  class: "status-warning-tip",
                  title: $setup.charlesStatus?.last_new_article_time ? `最后采到新文章: ${$setup.charlesStatus.last_new_article_time}` : '连续多轮无新文章'
                }, "采集空转 (可能标签已满 / 知乎风控 / cookie 过期)", 8 /* PROPS */, _hoisted_5))
              : ($setup.statusClass === 'status-dead')
                ? (_openBlock(), _createElementBlock("span", _hoisted_6, _toDisplayString($setup.charlesStatus?.error_message || 'Charles 已停止'), 1 /* TEXT */))
                : _createCommentVNode("v-if", true),
            _createElementVNode("div", _hoisted_7, [
              _createElementVNode("button", {
                class: _normalizeClass(["filter-tab", { active: $setup.filterTag === 'AI' }]),
                onClick: _cache[1] || (_cache[1] = $event => ($setup.filterTag = 'AI'))
              }, [
                _cache[37] || (_cache[37] = _createTextVNode(" AI", -1 /* CACHED */)),
                ($setup.statistics?.tag_pending)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_8, _toDisplayString($setup.statistics.tag_pending['AI'] || 0), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true)
              ], 2 /* CLASS */),
              _createElementVNode("button", {
                class: _normalizeClass(["filter-tab", { active: $setup.filterTag === '量化交易' }]),
                onClick: _cache[2] || (_cache[2] = $event => ($setup.filterTag = '量化交易'))
              }, [
                _cache[38] || (_cache[38] = _createTextVNode(" 量化", -1 /* CACHED */)),
                ($setup.statistics?.tag_pending)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_9, _toDisplayString($setup.statistics.tag_pending['量化交易'] || 0), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true)
              ], 2 /* CLASS */),
              _createElementVNode("button", {
                class: _normalizeClass(["filter-tab", { active: $setup.filterTag === '经济学' }]),
                onClick: _cache[3] || (_cache[3] = $event => ($setup.filterTag = '经济学'))
              }, [
                _cache[39] || (_cache[39] = _createTextVNode(" 经济学", -1 /* CACHED */)),
                ($setup.statistics?.tag_pending)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_10, _toDisplayString($setup.statistics.tag_pending['经济学'] || 0), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true)
              ], 2 /* CLASS */),
              _createElementVNode("button", {
                class: _normalizeClass(["filter-tab", { active: $setup.filterTag === '心理学' }]),
                onClick: _cache[4] || (_cache[4] = $event => ($setup.filterTag = '心理学'))
              }, [
                _cache[40] || (_cache[40] = _createTextVNode(" 心理学", -1 /* CACHED */)),
                ($setup.statistics?.tag_pending)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_11, _toDisplayString($setup.statistics.tag_pending['心理学'] || 0), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true)
              ], 2 /* CLASS */)
            ]),
            _withDirectives(_createElementVNode("select", {
              "onUpdate:modelValue": _cache[5] || (_cache[5] = $event => (($setup.statusFilter) = $event)),
              class: "filter-select filter-select-narrow"
            }, [
              _createElementVNode("option", _hoisted_12, "待审核(" + _toDisplayString($setup.statistics?.pending || 0) + ")", 1 /* TEXT */),
              _createElementVNode("option", _hoisted_13, "已安排(" + _toDisplayString($setup.statistics?.selected || 0) + ")", 1 /* TEXT */),
              _createElementVNode("option", _hoisted_14, "已删除(" + _toDisplayString($setup.statistics?.deleted || 0) + ")", 1 /* TEXT */)
            ], 512 /* NEED_PATCH */), [
              [_vModelSelect, $setup.statusFilter]
            ]),
            _withDirectives(_createElementVNode("select", {
              "onUpdate:modelValue": _cache[6] || (_cache[6] = $event => (($setup.filterPlatform) = $event)),
              class: "filter-select filter-select-narrow"
            }, [...(_cache[41] || (_cache[41] = [
              _createElementVNode("option", { value: "zhihu" }, "知乎", -1 /* CACHED */),
              _createElementVNode("option", { value: "creator_video" }, "对标博主", -1 /* CACHED */),
              _createElementVNode("option", { value: "manual" }, "人工", -1 /* CACHED */),
              _createElementVNode("option", { value: null }, "全部渠道", -1 /* CACHED */)
            ]))], 512 /* NEED_PATCH */), [
              [_vModelSelect, $setup.filterPlatform]
            ]),
            _withDirectives(_createElementVNode("select", {
              "onUpdate:modelValue": _cache[7] || (_cache[7] = $event => (($setup.sortBy) = $event)),
              class: "filter-select filter-select-sort"
            }, [...(_cache[42] || (_cache[42] = [
              _createElementVNode("option", { value: "published_at" }, "按时间", -1 /* CACHED */),
              _createElementVNode("option", { value: "agree_count" }, "按赞同", -1 /* CACHED */),
              _createElementVNode("option", { value: "comment_count" }, "按评论", -1 /* CACHED */)
            ]))], 512 /* NEED_PATCH */), [
              [_vModelSelect, $setup.sortBy]
            ])
          ]),
          _createElementVNode("div", _hoisted_15, [
            ($setup.statusFilter === 'pending' && $setup.filterTag)
              ? (_openBlock(), _createElementBlock("button", {
                  key: 0,
                  class: "ai-filter-btn",
                  onClick: $setup.startAIFilter,
                  disabled: $setup.aiFiltering
                }, [
                  (!$setup.aiFiltering)
                    ? (_openBlock(), _createElementBlock("svg", _hoisted_17, [...(_cache[43] || (_cache[43] = [
                        _createElementVNode("polygon", { points: "22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" }, null, -1 /* CACHED */)
                      ]))]))
                    : (_openBlock(), _createElementBlock("svg", _hoisted_18, [...(_cache[44] || (_cache[44] = [
                        _createElementVNode("circle", {
                          cx: "12",
                          cy: "12",
                          r: "10",
                          "stroke-dasharray": "31.4 31.4"
                        }, null, -1 /* CACHED */)
                      ]))])),
                  _createTextVNode(" " + _toDisplayString($setup.aiFiltering ? 'AI分析中...' : '帮我过滤'), 1 /* TEXT */)
                ], 8 /* PROPS */, _hoisted_16))
              : _createCommentVNode("v-if", true),
            _createElementVNode("button", {
              class: "new-article-btn",
              onClick: _cache[8] || (_cache[8] = $event => ($setup.showCreateModal = true))
            }, [...(_cache[45] || (_cache[45] = [
              _createElementVNode("svg", {
                viewBox: "0 0 24 24",
                fill: "none",
                stroke: "currentColor"
              }, [
                _createElementVNode("line", {
                  x1: "12",
                  y1: "5",
                  x2: "12",
                  y2: "19"
                }),
                _createElementVNode("line", {
                  x1: "5",
                  y1: "12",
                  x2: "19",
                  y2: "12"
                })
              ], -1 /* CACHED */),
              _createTextVNode(" 新建文章 ", -1 /* CACHED */)
            ]))])
          ])
        ])
      ]),
      _createCommentVNode(" 发布计划面板: 管道里已选未发完的视频 (制作队列 + 三平台排期) "),
      _createElementVNode("div", _hoisted_19, [
        _createElementVNode("div", {
          class: "schedule-header",
          onClick: _cache[9] || (_cache[9] = $event => ($setup.showSchedule = !$setup.showSchedule))
        }, [
          _cache[46] || (_cache[46] = _createElementVNode("span", { class: "schedule-title" }, "发布计划", -1 /* CACHED */)),
          ($setup.scheduleSummary)
            ? (_openBlock(), _createElementBlock("span", _hoisted_20, " 管道 " + _toDisplayString($setup.scheduleSummary.total) + " 条 · 制作中/排队 " + _toDisplayString($setup.scheduleSummary.making) + " · 已排期 " + _toDisplayString($setup.scheduleSummary.scheduled), 1 /* TEXT */))
            : _createCommentVNode("v-if", true),
          _createElementVNode("span", _hoisted_21, _toDisplayString($setup.showSchedule ? '收起 ▲' : '展开 ▼'), 1 /* TEXT */)
        ]),
        ($setup.showSchedule)
          ? (_openBlock(), _createElementBlock("div", _hoisted_22, [
              ($setup.scheduleLoading)
                ? (_openBlock(), _createElementBlock("div", _hoisted_23, "加载中..."))
                : ($setup.scheduleItems.length === 0)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_24, "管道为空 (水位补给会自动选题)"))
                  : (_openBlock(), _createElementBlock("table", _hoisted_25, [
                      _cache[47] || (_cache[47] = _createElementVNode("thead", null, [
                        _createElementVNode("tr", null, [
                          _createElementVNode("th", { class: "col-title" }, "视频选题"),
                          _createElementVNode("th", null, "来源"),
                          _createElementVNode("th", null, "新鲜度"),
                          _createElementVNode("th", null, "KIMI"),
                          _createElementVNode("th", null, "制作"),
                          _createElementVNode("th", null, "视频号"),
                          _createElementVNode("th", null, "抖音"),
                          _createElementVNode("th", null, "B站")
                        ])
                      ], -1 /* CACHED */)),
                      _createElementVNode("tbody", null, [
                        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.scheduleItems, (item) => {
                          return (_openBlock(), _createElementBlock("tr", {
                            key: item.id
                          }, [
                            _createElementVNode("td", {
                              class: "col-title",
                              title: item.title
                            }, _toDisplayString(item.title), 9 /* TEXT, PROPS */, _hoisted_26),
                            _createElementVNode("td", null, [
                              _createElementVNode("span", {
                                class: _normalizeClass(["schedule-source", { creator: item.platform === 'creator_video' }])
                              }, _toDisplayString(item.platform === 'creator_video' ? '对标博主' : (item.platform === 'manual' ? '人工' : '知乎')), 3 /* TEXT, CLASS */)
                            ]),
                            _createElementVNode("td", null, [
                              (item.event_age_days !== null)
                                ? (_openBlock(), _createElementBlock("span", {
                                    key: 0,
                                    class: _normalizeClass(["fresh-badge", $setup.freshBadgeClassByDays(item.event_age_days)])
                                  }, _toDisplayString(item.event_age_days) + "d ", 3 /* TEXT, CLASS */))
                                : (_openBlock(), _createElementBlock("span", _hoisted_27, "-"))
                            ]),
                            _createElementVNode("td", null, _toDisplayString(item.kimi_pick_score ?? '-'), 1 /* TEXT */),
                            _createElementVNode("td", null, [
                              _createElementVNode("span", {
                                class: _normalizeClass(["schedule-status", 'vs-' + (item.video_status || 'pending')])
                              }, _toDisplayString($setup.videoStatusText(item.video_status)), 3 /* TEXT, CLASS */)
                            ]),
                            _createElementVNode("td", null, _toDisplayString($setup.platformCell(item.channels_status, item.channels_scheduled_at)), 1 /* TEXT */),
                            _createElementVNode("td", null, _toDisplayString($setup.platformCell(item.douyin_status, item.douyin_scheduled_at)), 1 /* TEXT */),
                            _createElementVNode("td", null, _toDisplayString($setup.platformCell(item.bilibili_status, item.bilibili_scheduled_at)), 1 /* TEXT */)
                          ]))
                        }), 128 /* KEYED_FRAGMENT */))
                      ])
                    ]))
            ]))
          : _createCommentVNode("v-if", true)
      ]),
      _createCommentVNode(" 批量操作工具栏 "),
      ($setup.articles.length > 0)
        ? (_openBlock(), _createElementBlock("div", _hoisted_28, [
            _createElementVNode("div", _hoisted_29, [
              _createElementVNode("label", _hoisted_30, [
                _createElementVNode("input", {
                  type: "checkbox",
                  class: "batch-checkbox",
                  checked: $setup.isAllSelected,
                  indeterminate: $setup.isIndeterminate,
                  onChange: $setup.toggleSelectAll
                }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_31),
                _createElementVNode("span", _hoisted_32, [
                  _createTextVNode(_toDisplayString($setup.isAllSelected ? '取消全选' : '全选当前页') + " ", 1 /* TEXT */),
                  ($setup.selectedArticleIds.size > 0)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_33, "（已选 " + _toDisplayString($setup.selectedArticleIds.size) + " 项）", 1 /* TEXT */))
                    : _createCommentVNode("v-if", true)
                ])
              ])
            ]),
            ($setup.selectedArticleIds.size > 0)
              ? (_openBlock(), _createElementBlock("div", _hoisted_34, [
                  _createElementVNode("button", {
                    class: "batch-delete-btn",
                    onClick: $setup.batchDelete,
                    disabled: $setup.batchDeleting
                  }, [
                    _cache[48] || (_cache[48] = _createElementVNode("svg", {
                      viewBox: "0 0 24 24",
                      fill: "none",
                      stroke: "currentColor"
                    }, [
                      _createElementVNode("polyline", { points: "3 6 5 6 21 6" }),
                      _createElementVNode("path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" })
                    ], -1 /* CACHED */)),
                    _createTextVNode(" " + _toDisplayString($setup.batchDeleting ? '删除中...' : `批量删除 (${$setup.selectedArticleIds.size})`), 1 /* TEXT */)
                  ], 8 /* PROPS */, _hoisted_35)
                ]))
              : _createCommentVNode("v-if", true)
          ]))
        : _createCommentVNode("v-if", true),
      _createElementVNode("div", _hoisted_36, [
        (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.articles, (article) => {
          return (_openBlock(), _createElementBlock("div", {
            key: article.id,
            class: _normalizeClass(["article-item", { selected: article.is_selected, deleted: article.is_deleted }])
          }, [
            _createElementVNode("div", _hoisted_37, [
              _createCommentVNode(" 批量选择复选框 "),
              _createElementVNode("label", _hoisted_38, [
                _createElementVNode("input", {
                  type: "checkbox",
                  class: "article-checkbox",
                  checked: $setup.selectedArticleIds.has(article.id),
                  onChange: $event => ($setup.toggleArticleSelection(article.id)),
                  onClick: _cache[10] || (_cache[10] = _withModifiers(() => {}, ["stop"]))
                }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_39)
              ]),
              _createElementVNode("div", {
                class: "article-link clickable-title",
                onClick: $event => ($setup.showArticleContent(article))
              }, [
                _createElementVNode("h3", _hoisted_41, _toDisplayString(article.title), 1 /* TEXT */)
              ], 8 /* PROPS */, _hoisted_40),
              _createElementVNode("div", _hoisted_42, [
                (article.platform === 'manual')
                  ? (_openBlock(), _createElementBlock("span", _hoisted_43, " 人工 "))
                  : _createCommentVNode("v-if", true),
                (article.platform === 'creator_video')
                  ? (_openBlock(), _createElementBlock("span", _hoisted_44, " 对标博主 "))
                  : _createCommentVNode("v-if", true),
                _createCommentVNode(" 新鲜度: 事件时间 (published_at) 距今天数, ≤3d 在选题时走 Fresh 强保底通道 "),
                ($setup.freshAgeDays(article) !== null)
                  ? (_openBlock(), _createElementBlock("span", {
                      key: 2,
                      class: _normalizeClass(["fresh-badge", $setup.freshBadgeClass(article)]),
                      title: `事件时间距今 ${$setup.freshAgeDays(article)} 天 (≤3天走 Fresh 强保底通道)`
                    }, " 鲜 " + _toDisplayString($setup.freshAgeDays(article)) + "d ", 11 /* TEXT, CLASS, PROPS */, _hoisted_45))
                  : _createCommentVNode("v-if", true),
                _createCommentVNode(" 已安排类型标签 "),
                (article.is_selected && article.content_type)
                  ? (_openBlock(), _createElementBlock("span", {
                      key: 3,
                      class: _normalizeClass(["content-type-badge", article.content_type])
                    }, [
                      (article.content_type === 'video')
                        ? (_openBlock(), _createElementBlock(_Fragment, { key: 0 }, [
                            _createTextVNode("视频")
                          ], 64 /* STABLE_FRAGMENT */))
                        : (article.content_type === 'image')
                          ? (_openBlock(), _createElementBlock(_Fragment, { key: 1 }, [
                              _createTextVNode("图文")
                            ], 64 /* STABLE_FRAGMENT */))
                          : (article.content_type === 'both')
                            ? (_openBlock(), _createElementBlock(_Fragment, { key: 2 }, [
                                _createTextVNode("视频+图文")
                              ], 64 /* STABLE_FRAGMENT */))
                            : _createCommentVNode("v-if", true)
                    ], 2 /* CLASS */))
                  : _createCommentVNode("v-if", true),
                _createCommentVNode(" KIMI 视频号选题评分 (仅评过的有, 候选池 80 条之外的不会有) "),
                (article.kimi_pick_score !== null && article.kimi_pick_score !== undefined)
                  ? (_openBlock(), _createElementBlock("span", {
                      key: 4,
                      class: _normalizeClass(["kimi-score-badge", $setup.getKimiBadgeClass(article)]),
                      title: $setup.getKimiTooltip(article)
                    }, [
                      _createTextVNode(" KIMI " + _toDisplayString(article.kimi_pick_score) + " ", 1 /* TEXT */),
                      _createElementVNode("span", _hoisted_47, _toDisplayString($setup.getKimiReasonShort(article)), 1 /* TEXT */)
                    ], 10 /* CLASS, PROPS */, _hoisted_46))
                  : _createCommentVNode("v-if", true),
                (article.search_keyword)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_48, _toDisplayString(article.search_keyword), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true),
                _createElementVNode("span", _hoisted_49, [
                  _cache[49] || (_cache[49] = _createElementVNode("svg", {
                    viewBox: "0 0 24 24",
                    fill: "currentColor"
                  }, [
                    _createElementVNode("path", { d: "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" })
                  ], -1 /* CACHED */)),
                  _createTextVNode(" " + _toDisplayString(article.agree_count || 0), 1 /* TEXT */)
                ]),
                _createElementVNode("span", _hoisted_50, [
                  _cache[50] || (_cache[50] = _createElementVNode("svg", {
                    viewBox: "0 0 24 24",
                    fill: "currentColor"
                  }, [
                    _createElementVNode("path", { d: "M21.99 4c0-1.1-.89-2-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h14l4 4-.01-18zM18 14H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z" })
                  ], -1 /* CACHED */)),
                  _createTextVNode(" " + _toDisplayString(article.comment_count || 0), 1 /* TEXT */)
                ]),
                (article.content_length)
                  ? (_openBlock(), _createElementBlock("span", _hoisted_51, _toDisplayString($setup.formatContentLength(article.content_length)), 1 /* TEXT */))
                  : _createCommentVNode("v-if", true),
                _createElementVNode("span", _hoisted_52, _toDisplayString($setup.formatDate(article.published_at || article.created_at)), 1 /* TEXT */)
              ]),
              _createElementVNode("div", _hoisted_53, [
                _createElementVNode("button", {
                  class: _normalizeClass(["action-btn select-btn", { active: article.is_selected }]),
                  onClick: $event => ($setup.toggleSelect(article)),
                  title: article.is_selected ? '取消选中' : '选中'
                }, [
                  (article.is_selected)
                    ? (_openBlock(), _createElementBlock("svg", _hoisted_55, [...(_cache[51] || (_cache[51] = [
                        _createElementVNode("path", { d: "M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" }, null, -1 /* CACHED */)
                      ]))]))
                    : (_openBlock(), _createElementBlock("svg", _hoisted_56, [...(_cache[52] || (_cache[52] = [
                        _createElementVNode("rect", {
                          x: "3",
                          y: "3",
                          width: "18",
                          height: "18",
                          rx: "2",
                          "stroke-width": "2"
                        }, null, -1 /* CACHED */)
                      ]))]))
                ], 10 /* CLASS, PROPS */, _hoisted_54),
                _createElementVNode("button", {
                  class: "action-btn delete-btn",
                  onClick: $event => ($setup.markRejected(article)),
                  title: article.is_deleted ? '取消标记' : '标记为删除'
                }, [...(_cache[53] || (_cache[53] = [
                  _createElementVNode("svg", {
                    viewBox: "0 0 24 24",
                    fill: "none",
                    stroke: "currentColor"
                  }, [
                    _createElementVNode("polyline", { points: "3 6 5 6 21 6" }),
                    _createElementVNode("path", { d: "M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" })
                  ], -1 /* CACHED */)
                ]))], 8 /* PROPS */, _hoisted_57)
              ])
            ])
          ], 2 /* CLASS */))
        }), 128 /* KEYED_FRAGMENT */))
      ]),
      ($setup.loading)
        ? (_openBlock(), _createElementBlock("div", _hoisted_58, "加载中..."))
        : _createCommentVNode("v-if", true),
      (!$setup.loading && $setup.articles.length === 0)
        ? (_openBlock(), _createElementBlock("div", _hoisted_59, "暂无文章"))
        : _createCommentVNode("v-if", true),
      ($setup.pagination && $setup.pagination.total_pages > 1)
        ? (_openBlock(), _createElementBlock("div", _hoisted_60, [
            _createElementVNode("button", {
              class: "page-btn",
              disabled: $setup.pagination.page === 1,
              onClick: _cache[11] || (_cache[11] = $event => ($setup.changePage($setup.pagination.page - 1)))
            }, " 上一页 ", 8 /* PROPS */, _hoisted_61),
            _createCommentVNode(" 页码按钮 "),
            _createElementVNode("div", _hoisted_62, [
              (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.visiblePages, (pageNum) => {
                return (_openBlock(), _createElementBlock(_Fragment, { key: pageNum }, [
                  (pageNum !== '...')
                    ? (_openBlock(), _createElementBlock("button", {
                        key: 0,
                        class: _normalizeClass(["page-number-btn", { active: pageNum === $setup.pagination.page }]),
                        onClick: $event => ($setup.changePage(pageNum))
                      }, _toDisplayString(pageNum), 11 /* TEXT, CLASS, PROPS */, _hoisted_63))
                    : (_openBlock(), _createElementBlock("span", _hoisted_64, "..."))
                ], 64 /* STABLE_FRAGMENT */))
              }), 128 /* KEYED_FRAGMENT */))
            ]),
            _createElementVNode("button", {
              class: "page-btn",
              disabled: $setup.pagination.page >= $setup.pagination.total_pages,
              onClick: _cache[12] || (_cache[12] = $event => ($setup.changePage($setup.pagination.page + 1)))
            }, " 下一页 ", 8 /* PROPS */, _hoisted_65),
            _createCommentVNode(" 跳转输入框 "),
            _createElementVNode("div", _hoisted_66, [
              _cache[54] || (_cache[54] = _createElementVNode("span", { class: "jump-label" }, "跳转到", -1 /* CACHED */)),
              _withDirectives(_createElementVNode("input", {
                "onUpdate:modelValue": _cache[13] || (_cache[13] = $event => (($setup.jumpPage) = $event)),
                type: "number",
                class: "jump-input",
                min: 1,
                max: $setup.pagination.total_pages,
                onKeyup: _withKeys($setup.jumpToPage, ["enter"])
              }, null, 40 /* PROPS, NEED_HYDRATION */, _hoisted_67), [
                [
                  _vModelText,
                  $setup.jumpPage,
                  void 0,
                  { number: true }
                ]
              ]),
              _cache[55] || (_cache[55] = _createElementVNode("span", { class: "jump-label" }, "页", -1 /* CACHED */)),
              _createElementVNode("button", {
                class: "jump-btn",
                onClick: $setup.jumpToPage
              }, "跳转")
            ]),
            _createElementVNode("span", _hoisted_68, " 共 " + _toDisplayString($setup.pagination.total) + " 条 ", 1 /* TEXT */)
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 文章编辑模态框 "),
      ($setup.showContentModal)
        ? (_openBlock(), _createElementBlock("div", _hoisted_69, [
            _createElementVNode("div", _hoisted_70, [
              _createElementVNode("div", _hoisted_71, [
                _createElementVNode("h2", null, [
                  _cache[56] || (_cache[56] = _createTextVNode("编辑文章 ", -1 /* CACHED */)),
                  ($setup.viewingArticle?.id)
                    ? (_openBlock(), _createElementBlock("span", _hoisted_72, "(ID: " + _toDisplayString($setup.viewingArticle.id) + ")", 1 /* TEXT */))
                    : _createCommentVNode("v-if", true)
                ]),
                _createElementVNode("div", _hoisted_73, [
                  ($setup.viewingArticle?.url && !$setup.viewingArticle?.url.startsWith('manual-') && $setup.viewingArticle?.url.includes('zhihu.com'))
                    ? (_openBlock(), _createElementBlock("button", {
                        key: 0,
                        class: "recrawl-btn",
                        onClick: $setup.recrawlArticle,
                        disabled: $setup.recrawling
                      }, [
                        (!$setup.recrawling)
                          ? (_openBlock(), _createElementBlock("svg", _hoisted_75, [...(_cache[57] || (_cache[57] = [
                              _createElementVNode("path", { d: "M23 4v6h-6" }, null, -1 /* CACHED */),
                              _createElementVNode("path", { d: "M1 20v-6h6" }, null, -1 /* CACHED */),
                              _createElementVNode("path", { d: "M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" }, null, -1 /* CACHED */)
                            ]))]))
                          : (_openBlock(), _createElementBlock("svg", _hoisted_76, [...(_cache[58] || (_cache[58] = [
                              _createElementVNode("circle", {
                                cx: "12",
                                cy: "12",
                                r: "10",
                                "stroke-width": "2",
                                "stroke-dasharray": "31.4 31.4"
                              }, null, -1 /* CACHED */)
                            ]))])),
                        _createTextVNode(" " + _toDisplayString($setup.recrawling ? '采集中...' : '重新采集'), 1 /* TEXT */)
                      ], 8 /* PROPS */, _hoisted_74))
                    : _createCommentVNode("v-if", true),
                  ($setup.viewingArticle?.url && !$setup.viewingArticle?.url.startsWith('manual-'))
                    ? (_openBlock(), _createElementBlock("a", {
                        key: 1,
                        href: $setup.viewingArticle.url,
                        target: "_blank",
                        class: "external-link-btn",
                        onClick: _cache[14] || (_cache[14] = _withModifiers(() => {}, ["stop"]))
                      }, [...(_cache[59] || (_cache[59] = [
                        _createElementVNode("svg", {
                          viewBox: "0 0 24 24",
                          fill: "none",
                          stroke: "currentColor"
                        }, [
                          _createElementVNode("path", { d: "M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" }),
                          _createElementVNode("polyline", { points: "15 3 21 3 21 9" }),
                          _createElementVNode("line", {
                            x1: "10",
                            y1: "14",
                            x2: "21",
                            y2: "3"
                          })
                        ], -1 /* CACHED */),
                        _createTextVNode(" 查看原始链接 ", -1 /* CACHED */)
                      ]))], 8 /* PROPS */, _hoisted_77))
                    : _createCommentVNode("v-if", true),
                  _createElementVNode("button", {
                    class: "modal-close",
                    onClick: $setup.closeEditModal
                  }, [...(_cache[60] || (_cache[60] = [
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
              _createElementVNode("div", _hoisted_78, [
                ($setup.loadingArticleContent)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_79, "加载中..."))
                  : (_openBlock(), _createElementBlock("div", _hoisted_80, [
                      _createElementVNode("div", _hoisted_81, [
                        _cache[61] || (_cache[61] = _createElementVNode("label", { class: "form-label" }, [
                          _createTextVNode("标题 "),
                          _createElementVNode("span", { class: "optional" }, "（可选，可自动生成）")
                        ], -1 /* CACHED */)),
                        _createElementVNode("div", _hoisted_82, [
                          _withDirectives(_createElementVNode("input", {
                            "onUpdate:modelValue": _cache[15] || (_cache[15] = $event => (($setup.editingArticle.title) = $event)),
                            type: "text",
                            class: "form-input",
                            placeholder: "输入标题或点击下方按钮自动生成"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelText, $setup.editingArticle.title]
                          ]),
                          _createElementVNode("button", {
                            class: "generate-title-btn",
                            onClick: $setup.generateTitleForEdit,
                            disabled: !$setup.editingArticle.content || $setup.generatingTitle
                          }, _toDisplayString($setup.generatingTitle ? '生成中...' : 'AI生成标题'), 9 /* TEXT, PROPS */, _hoisted_83)
                        ])
                      ]),
                      _createElementVNode("div", _hoisted_84, [
                        _cache[62] || (_cache[62] = _createElementVNode("label", { class: "form-label" }, [
                          _createTextVNode("文章内容 "),
                          _createElementVNode("span", { class: "required" }, "*")
                        ], -1 /* CACHED */)),
                        _withDirectives(_createElementVNode("textarea", {
                          "onUpdate:modelValue": _cache[16] || (_cache[16] = $event => (($setup.editingArticle.content) = $event)),
                          class: "form-textarea",
                          rows: "15",
                          placeholder: "请输入文章内容..."
                        }, null, 512 /* NEED_PATCH */), [
                          [_vModelText, $setup.editingArticle.content]
                        ]),
                        _createElementVNode("div", _hoisted_85, _toDisplayString($setup.editingArticle.content.length) + " 字", 1 /* TEXT */)
                      ]),
                      _createElementVNode("div", _hoisted_86, [
                        _createElementVNode("button", {
                          class: "btn btn-secondary",
                          onClick: $setup.closeEditModal
                        }, "关闭"),
                        ($setup.saveSuccess)
                          ? (_openBlock(), _createElementBlock("span", _hoisted_87, "已保存"))
                          : _createCommentVNode("v-if", true),
                        _createElementVNode("button", {
                          class: "btn btn-primary",
                          onClick: $setup.saveArticle,
                          disabled: !$setup.editingArticle.content || $setup.saving || $setup.arrangingType
                        }, _toDisplayString($setup.saving ? '保存中...' : '保存'), 9 /* TEXT, PROPS */, _hoisted_88)
                      ]),
                      ($setup.editingArticle.id)
                        ? (_openBlock(), _createElementBlock("div", _hoisted_89, [
                            _cache[64] || (_cache[64] = _createElementVNode("span", { class: "arrange-label" }, "安排制作：", -1 /* CACHED */)),
                            ($setup.isArrangedVideo)
                              ? (_openBlock(), _createBlock(_component_router_link, {
                                  key: 0,
                                  to: `/zoe/${$setup.editingArticle.id}`,
                                  class: "btn btn-arrange arranged"
                                }, {
                                  default: _withCtx(() => [...(_cache[63] || (_cache[63] = [
                                    _createTextVNode(" 已安排视频（点击查看） ", -1 /* CACHED */)
                                  ]))]),
                                  _: 1 /* STABLE */
                                }, 8 /* PROPS */, ["to"]))
                              : (_openBlock(), _createElementBlock("button", {
                                  key: 1,
                                  class: "btn btn-arrange",
                                  onClick: _cache[17] || (_cache[17] = $event => ($setup.arrangeType('video'))),
                                  disabled: !$setup.editingArticle.content || $setup.saving || $setup.arrangingType
                                }, _toDisplayString($setup.arrangingType === 'video' ? '安排中...' : '安排视频'), 9 /* TEXT, PROPS */, _hoisted_90)),
                            _createElementVNode("button", {
                              class: _normalizeClass(["btn btn-arrange", { 'arranged': $setup.isArrangedImage }]),
                              onClick: _cache[18] || (_cache[18] = $event => ($setup.arrangeType('image'))),
                              disabled: $setup.isArrangedImage || !$setup.editingArticle.content || $setup.saving || $setup.arrangingType
                            }, _toDisplayString($setup.arrangingType === 'image' ? '安排中...' : ($setup.isArrangedImage ? '已安排图文' : '安排图文')), 11 /* TEXT, CLASS, PROPS */, _hoisted_91)
                          ]))
                        : _createCommentVNode("v-if", true)
                    ]))
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 新建文章模态框 "),
      ($setup.showCreateModal)
        ? (_openBlock(), _createElementBlock("div", _hoisted_92, [
            _createElementVNode("div", _hoisted_93, [
              _createElementVNode("div", { class: "modal-header" }, [
                _cache[66] || (_cache[66] = _createElementVNode("h2", null, "新建文章", -1 /* CACHED */)),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: $setup.closeCreateModal
                }, [...(_cache[65] || (_cache[65] = [
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
              _createElementVNode("div", _hoisted_94, [
                _createElementVNode("div", _hoisted_95, [
                  _cache[67] || (_cache[67] = _createElementVNode("label", { class: "form-label" }, [
                    _createTextVNode("标题 "),
                    _createElementVNode("span", { class: "optional" }, "（可选，可自动生成）")
                  ], -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_96, [
                    _withDirectives(_createElementVNode("input", {
                      "onUpdate:modelValue": _cache[19] || (_cache[19] = $event => (($setup.newArticle.title) = $event)),
                      type: "text",
                      class: "form-input",
                      placeholder: "输入标题或点击下方按钮自动生成"
                    }, null, 512 /* NEED_PATCH */), [
                      [_vModelText, $setup.newArticle.title]
                    ]),
                    _createElementVNode("button", {
                      class: "generate-title-btn",
                      onClick: $setup.generateTitle,
                      disabled: !$setup.newArticle.content || $setup.generatingTitle
                    }, _toDisplayString($setup.generatingTitle ? '生成中...' : 'AI生成标题'), 9 /* TEXT, PROPS */, _hoisted_97)
                  ])
                ]),
                _createElementVNode("div", _hoisted_98, [
                  _cache[68] || (_cache[68] = _createElementVNode("label", { class: "form-label" }, [
                    _createTextVNode("文章内容 "),
                    _createElementVNode("span", { class: "required" }, "*")
                  ], -1 /* CACHED */)),
                  _withDirectives(_createElementVNode("textarea", {
                    "onUpdate:modelValue": _cache[20] || (_cache[20] = $event => (($setup.newArticle.content) = $event)),
                    class: "form-textarea",
                    rows: "15",
                    placeholder: "请输入文章内容..."
                  }, null, 512 /* NEED_PATCH */), [
                    [_vModelText, $setup.newArticle.content]
                  ]),
                  _createElementVNode("div", _hoisted_99, _toDisplayString($setup.newArticle.content.length) + " 字", 1 /* TEXT */)
                ]),
                _createElementVNode("div", _hoisted_100, [
                  _cache[71] || (_cache[71] = _createElementVNode("label", { class: "form-label" }, "制作类型", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_101, [
                    _createElementVNode("label", _hoisted_102, [
                      _withDirectives(_createElementVNode("input", {
                        type: "checkbox",
                        "onUpdate:modelValue": _cache[21] || (_cache[21] = $event => (($setup.newArticle.content_type_image) = $event)),
                        onChange: $setup.onContentTypeChange
                      }, null, 544 /* NEED_HYDRATION, NEED_PATCH */), [
                        [_vModelCheckbox, $setup.newArticle.content_type_image]
                      ]),
                      _cache[69] || (_cache[69] = _createElementVNode("span", null, "图文", -1 /* CACHED */))
                    ]),
                    _createElementVNode("label", _hoisted_103, [
                      _withDirectives(_createElementVNode("input", {
                        type: "checkbox",
                        "onUpdate:modelValue": _cache[22] || (_cache[22] = $event => (($setup.newArticle.content_type_video) = $event)),
                        onChange: $setup.onContentTypeChange
                      }, null, 544 /* NEED_HYDRATION, NEED_PATCH */), [
                        [_vModelCheckbox, $setup.newArticle.content_type_video]
                      ]),
                      _cache[70] || (_cache[70] = _createElementVNode("span", null, "视频", -1 /* CACHED */))
                    ])
                  ])
                ]),
                ($setup.showAccountTarget)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_104, [
                      _cache[75] || (_cache[75] = _createElementVNode("label", { class: "form-label" }, "目标账号", -1 /* CACHED */)),
                      _createElementVNode("div", _hoisted_105, [
                        _createElementVNode("label", _hoisted_106, [
                          _withDirectives(_createElementVNode("input", {
                            type: "radio",
                            "onUpdate:modelValue": _cache[23] || (_cache[23] = $event => (($setup.newArticle.account_target) = $event)),
                            value: "AI"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelRadio, $setup.newArticle.account_target]
                          ]),
                          _cache[72] || (_cache[72] = _createElementVNode("span", null, "AI", -1 /* CACHED */))
                        ]),
                        _createElementVNode("label", _hoisted_107, [
                          _withDirectives(_createElementVNode("input", {
                            type: "radio",
                            "onUpdate:modelValue": _cache[24] || (_cache[24] = $event => (($setup.newArticle.account_target) = $event)),
                            value: "经济学"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelRadio, $setup.newArticle.account_target]
                          ]),
                          _cache[73] || (_cache[73] = _createElementVNode("span", null, "经济学", -1 /* CACHED */))
                        ]),
                        _createElementVNode("label", _hoisted_108, [
                          _withDirectives(_createElementVNode("input", {
                            type: "radio",
                            "onUpdate:modelValue": _cache[25] || (_cache[25] = $event => (($setup.newArticle.account_target) = $event)),
                            value: "心理学"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelRadio, $setup.newArticle.account_target]
                          ]),
                          _cache[74] || (_cache[74] = _createElementVNode("span", null, "心理学", -1 /* CACHED */))
                        ])
                      ])
                    ]))
                  : _createCommentVNode("v-if", true),
                _createElementVNode("div", _hoisted_109, [
                  _createElementVNode("button", {
                    class: "btn btn-secondary",
                    onClick: $setup.closeCreateModal
                  }, "取消"),
                  _createElementVNode("button", {
                    class: "btn btn-primary",
                    onClick: $setup.createArticle,
                    disabled: !$setup.newArticle.content || $setup.creating
                  }, _toDisplayString($setup.creating ? '创建中...' : '创建文章（默认已安排）'), 9 /* TEXT, PROPS */, _hoisted_110)
                ])
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" 选中设置模态框 "),
      ($setup.showSelectModal)
        ? (_openBlock(), _createElementBlock("div", _hoisted_111, [
            _createElementVNode("div", _hoisted_112, [
              _createElementVNode("div", { class: "modal-header" }, [
                _cache[77] || (_cache[77] = _createElementVNode("h2", null, "设置制作类型和目标账号", -1 /* CACHED */)),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: $setup.closeSelectModal
                }, [...(_cache[76] || (_cache[76] = [
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
              _createElementVNode("div", _hoisted_113, [
                _createElementVNode("div", _hoisted_114, [
                  _cache[80] || (_cache[80] = _createElementVNode("label", { class: "form-label" }, "制作类型", -1 /* CACHED */)),
                  _createElementVNode("div", _hoisted_115, [
                    _createElementVNode("label", _hoisted_116, [
                      _withDirectives(_createElementVNode("input", {
                        type: "checkbox",
                        "onUpdate:modelValue": _cache[26] || (_cache[26] = $event => (($setup.selectSettings.content_type_image) = $event)),
                        onChange: $setup.onSelectContentTypeChange
                      }, null, 544 /* NEED_HYDRATION, NEED_PATCH */), [
                        [_vModelCheckbox, $setup.selectSettings.content_type_image]
                      ]),
                      _cache[78] || (_cache[78] = _createElementVNode("span", null, "图文", -1 /* CACHED */))
                    ]),
                    _createElementVNode("label", _hoisted_117, [
                      _withDirectives(_createElementVNode("input", {
                        type: "checkbox",
                        "onUpdate:modelValue": _cache[27] || (_cache[27] = $event => (($setup.selectSettings.content_type_video) = $event)),
                        onChange: $setup.onSelectContentTypeChange
                      }, null, 544 /* NEED_HYDRATION, NEED_PATCH */), [
                        [_vModelCheckbox, $setup.selectSettings.content_type_video]
                      ]),
                      _cache[79] || (_cache[79] = _createElementVNode("span", null, "视频", -1 /* CACHED */))
                    ])
                  ])
                ]),
                ($setup.showSelectAccountTarget)
                  ? (_openBlock(), _createElementBlock("div", _hoisted_118, [
                      _cache[84] || (_cache[84] = _createElementVNode("label", { class: "form-label" }, "目标账号", -1 /* CACHED */)),
                      _createElementVNode("div", _hoisted_119, [
                        _createElementVNode("label", _hoisted_120, [
                          _withDirectives(_createElementVNode("input", {
                            type: "radio",
                            "onUpdate:modelValue": _cache[28] || (_cache[28] = $event => (($setup.selectSettings.account_target) = $event)),
                            value: "AI"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelRadio, $setup.selectSettings.account_target]
                          ]),
                          _cache[81] || (_cache[81] = _createElementVNode("span", null, "AI", -1 /* CACHED */))
                        ]),
                        _createElementVNode("label", _hoisted_121, [
                          _withDirectives(_createElementVNode("input", {
                            type: "radio",
                            "onUpdate:modelValue": _cache[29] || (_cache[29] = $event => (($setup.selectSettings.account_target) = $event)),
                            value: "经济学"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelRadio, $setup.selectSettings.account_target]
                          ]),
                          _cache[82] || (_cache[82] = _createElementVNode("span", null, "经济学", -1 /* CACHED */))
                        ]),
                        _createElementVNode("label", _hoisted_122, [
                          _withDirectives(_createElementVNode("input", {
                            type: "radio",
                            "onUpdate:modelValue": _cache[30] || (_cache[30] = $event => (($setup.selectSettings.account_target) = $event)),
                            value: "心理学"
                          }, null, 512 /* NEED_PATCH */), [
                            [_vModelRadio, $setup.selectSettings.account_target]
                          ]),
                          _cache[83] || (_cache[83] = _createElementVNode("span", null, "心理学", -1 /* CACHED */))
                        ])
                      ])
                    ]))
                  : _createCommentVNode("v-if", true),
                _createElementVNode("div", _hoisted_123, [
                  _createElementVNode("button", {
                    class: "btn btn-secondary",
                    onClick: $setup.closeSelectModal
                  }, "取消"),
                  _createElementVNode("button", {
                    class: "btn btn-primary",
                    onClick: $setup.confirmSelect,
                    disabled: !$setup.hasSelectContentType || $setup.selecting
                  }, _toDisplayString($setup.selecting ? '设置中...' : '确认选中'), 9 /* TEXT, PROPS */, _hoisted_124)
                ])
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" AI过滤提示词编辑弹窗 "),
      ($setup.showPromptEditModal)
        ? (_openBlock(), _createElementBlock("div", _hoisted_125, [
            _createElementVNode("div", _hoisted_126, [
              _createElementVNode("div", _hoisted_127, [
                _createElementVNode("h2", null, "过滤提示词 - " + _toDisplayString($setup.filterTag), 1 /* TEXT */),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: _cache[31] || (_cache[31] = $event => ($setup.showPromptEditModal = false))
                }, [...(_cache[85] || (_cache[85] = [
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
              _createElementVNode("div", _hoisted_128, [
                _cache[87] || (_cache[87] = _createElementVNode("div", { class: "prompt-edit-hint" }, " 以下提示词用于指导AI判断哪些文章应该被删除。你可以修改后点击保存，或直接开始过滤。 ", -1 /* CACHED */)),
                _withDirectives(_createElementVNode("textarea", {
                  "onUpdate:modelValue": _cache[32] || (_cache[32] = $event => (($setup.editingPrompt) = $event)),
                  class: "prompt-textarea",
                  rows: "16",
                  placeholder: "请输入过滤提示词..."
                }, null, 512 /* NEED_PATCH */), [
                  [_vModelText, $setup.editingPrompt]
                ]),
                _createElementVNode("div", _hoisted_129, [
                  _createElementVNode("button", {
                    class: "btn btn-secondary",
                    onClick: _cache[33] || (_cache[33] = $event => ($setup.showPromptEditModal = false))
                  }, "取消"),
                  _createElementVNode("button", {
                    class: "btn btn-outline-primary",
                    onClick: $setup.savePrompt,
                    disabled: $setup.savingPrompt
                  }, _toDisplayString($setup.savingPrompt ? '保存中...' : '保存提示词'), 9 /* TEXT, PROPS */, _hoisted_130),
                  _createElementVNode("button", {
                    class: "btn btn-primary",
                    onClick: $setup.runAIFilter,
                    disabled: $setup.aiFiltering || !$setup.editingPrompt.trim()
                  }, [
                    ($setup.aiFiltering)
                      ? (_openBlock(), _createElementBlock("svg", _hoisted_132, [...(_cache[86] || (_cache[86] = [
                          _createElementVNode("circle", {
                            cx: "12",
                            cy: "12",
                            r: "10",
                            "stroke-dasharray": "31.4 31.4"
                          }, null, -1 /* CACHED */)
                        ]))]))
                      : _createCommentVNode("v-if", true),
                    _createTextVNode(" " + _toDisplayString($setup.aiFiltering ? 'AI分析中...' : '开始过滤'), 1 /* TEXT */)
                  ], 8 /* PROPS */, _hoisted_131)
                ])
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true),
      _createCommentVNode(" AI过滤确认弹窗 "),
      ($setup.showAIFilterModal)
        ? (_openBlock(), _createElementBlock("div", _hoisted_133, [
            _createElementVNode("div", _hoisted_134, [
              _createElementVNode("div", _hoisted_135, [
                _createElementVNode("h2", null, "AI过滤结果 - " + _toDisplayString($setup.filterTag), 1 /* TEXT */),
                _createElementVNode("button", {
                  class: "modal-close",
                  onClick: _cache[34] || (_cache[34] = $event => ($setup.showAIFilterModal = false))
                }, [...(_cache[88] || (_cache[88] = [
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
              _createElementVNode("div", _hoisted_136, [
                _createElementVNode("div", _hoisted_137, [
                  _createElementVNode("p", null, [
                    _cache[89] || (_cache[89] = _createTextVNode("共检查 ", -1 /* CACHED */)),
                    _createElementVNode("strong", null, _toDisplayString($setup.aiFilterTotalChecked), 1 /* TEXT */),
                    _cache[90] || (_cache[90] = _createTextVNode(" 篇待审核文章，AI建议删除以下 ", -1 /* CACHED */)),
                    _createElementVNode("strong", null, _toDisplayString($setup.aiFilterArticles.length), 1 /* TEXT */),
                    _cache[91] || (_cache[91] = _createTextVNode(" 篇：", -1 /* CACHED */))
                  ])
                ]),
                _createElementVNode("div", _hoisted_138, [
                  (_openBlock(true), _createElementBlock(_Fragment, null, _renderList($setup.aiFilterArticles, (article, index) => {
                    return (_openBlock(), _createElementBlock("div", {
                      key: article.id,
                      class: "ai-filter-item"
                    }, [
                      _createElementVNode("span", _hoisted_139, _toDisplayString(index + 1), 1 /* TEXT */),
                      _createElementVNode("span", _hoisted_140, _toDisplayString(article.title), 1 /* TEXT */),
                      _createElementVNode("span", _hoisted_141, "ID:" + _toDisplayString(article.id), 1 /* TEXT */)
                    ]))
                  }), 128 /* KEYED_FRAGMENT */))
                ]),
                _createElementVNode("div", _hoisted_142, [
                  _createElementVNode("button", {
                    class: "btn btn-secondary",
                    onClick: _cache[35] || (_cache[35] = $event => ($setup.showAIFilterModal = false))
                  }, "取消"),
                  _createElementVNode("button", {
                    class: "btn btn-danger",
                    onClick: $setup.confirmAIFilterDelete,
                    disabled: $setup.aiFilterDeleting
                  }, _toDisplayString($setup.aiFilterDeleting ? '删除中...' : `确认删除 (${$setup.aiFilterArticles.length})`), 9 /* TEXT, PROPS */, _hoisted_143)
                ])
              ])
            ])
          ]))
        : _createCommentVNode("v-if", true)
    ])
  ], 64 /* STABLE_FRAGMENT */))
}

import "/src/views/Videos.vue?t=1781051563784&vue&type=style&index=0&scoped=5b1e9f71&lang.css"

_sfc_main.__hmrId = "5b1e9f71"
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
export default /*#__PURE__*/_export_sfc(_sfc_main, [['render',_sfc_render],['__scopeId',"data-v-5b1e9f71"],['__file',"C:/WucaiMedia/client/src/views/Videos.vue"]])
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJuYW1lcyI6W10sInNvdXJjZXMiOlsiVmlkZW9zLnZ1ZSJdLCJzb3VyY2VzQ29udGVudCI6WyI8dGVtcGxhdGU+XG4gIDxBcHBIZWFkZXIgLz5cbiAgPEFsZXJ0TW9kYWwgXG4gICAgdi1tb2RlbDpzaG93PVwic2hvd1N0b3BBbGVydFwiIFxuICAgIHRpdGxlPVwiQ2hhcmxlcyDlt7LlgZzmraLov5DooYxcIiBcbiAgICA6bWVzc2FnZT1cInN0b3BBbGVydE1lc3NhZ2VcIlxuICAvPlxuICA8ZGl2IGNsYXNzPVwiYXJ0aWNsZXMtcGFnZVwiPlxuICAgIDxkaXYgY2xhc3M9XCJwYWdlLWhlYWRlclwiPlxuICAgICAgPGRpdiBjbGFzcz1cImhlYWRlci1jb250cm9sc1wiPlxuICAgICAgICA8ZGl2IGNsYXNzPVwiaGVhZGVyLWxlZnRcIj5cbiAgICAgICAgICA8cm91dGVyLWxpbmsgdG89XCIvY2hhcmxlcy1sb2dzXCIgY2xhc3M9XCJsb2ctYnRuXCIgOmNsYXNzPVwic3RhdHVzQ2xhc3NcIj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwic3RhdHVzLWRvdFwiPjwvc3Bhbj5cbiAgICAgICAgICAgIENoYXJsZXMg5bel5L2c5pel5b+XXG4gICAgICAgICAgPC9yb3V0ZXItbGluaz5cbiAgICAgICAgICA8c3BhbiB2LWlmPVwic3RhdHVzQ2xhc3MgPT09ICdzdGF0dXMtd2FybmluZydcIiBjbGFzcz1cInN0YXR1cy13YXJuaW5nLXRpcFwiIDp0aXRsZT1cImNoYXJsZXNTdGF0dXM/Lmxhc3RfbmV3X2FydGljbGVfdGltZSA/IGDmnIDlkI7ph4fliLDmlrDmlofnq6A6ICR7Y2hhcmxlc1N0YXR1cy5sYXN0X25ld19hcnRpY2xlX3RpbWV9YCA6ICfov57nu63lpJrova7ml6DmlrDmlofnq6AnXCI+6YeH6ZuG56m66L2sICjlj6/og73moIfnrb7lt7Lmu6EgLyDnn6XkuY7po47mjqcgLyBjb29raWUg6L+H5pyfKTwvc3Bhbj5cbiAgICAgICAgICA8c3BhbiB2LWVsc2UtaWY9XCJzdGF0dXNDbGFzcyA9PT0gJ3N0YXR1cy1kZWFkJ1wiIGNsYXNzPVwic3RhdHVzLXdhcm5pbmctdGlwIHN0YXR1cy1kZWFkLXRpcFwiPnt7IGNoYXJsZXNTdGF0dXM/LmVycm9yX21lc3NhZ2UgfHwgJ0NoYXJsZXMg5bey5YGc5q2iJyB9fTwvc3Bhbj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZmlsdGVyLXRhYnNcIj5cbiAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgIGNsYXNzPVwiZmlsdGVyLXRhYlwiIFxuICAgICAgICAgICAgICA6Y2xhc3M9XCJ7IGFjdGl2ZTogZmlsdGVyVGFnID09PSAnQUknIH1cIlxuICAgICAgICAgICAgICBAY2xpY2s9XCJmaWx0ZXJUYWcgPSAnQUknXCJcbiAgICAgICAgICAgID5cbiAgICAgICAgICAgICAgQUk8c3BhbiB2LWlmPVwic3RhdGlzdGljcz8udGFnX3BlbmRpbmdcIiBjbGFzcz1cImNvdW50LWJhZGdlXCI+e3sgc3RhdGlzdGljcy50YWdfcGVuZGluZ1snQUknXSB8fCAwIH19PC9zcGFuPlxuICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgICA8YnV0dG9uIFxuICAgICAgICAgICAgICBjbGFzcz1cImZpbHRlci10YWJcIiBcbiAgICAgICAgICAgICAgOmNsYXNzPVwieyBhY3RpdmU6IGZpbHRlclRhZyA9PT0gJ+mHj+WMluS6pOaYkycgfVwiXG4gICAgICAgICAgICAgIEBjbGljaz1cImZpbHRlclRhZyA9ICfph4/ljJbkuqTmmJMnXCJcbiAgICAgICAgICAgID5cbiAgICAgICAgICAgICAg6YeP5YyWPHNwYW4gdi1pZj1cInN0YXRpc3RpY3M/LnRhZ19wZW5kaW5nXCIgY2xhc3M9XCJjb3VudC1iYWRnZVwiPnt7IHN0YXRpc3RpY3MudGFnX3BlbmRpbmdbJ+mHj+WMluS6pOaYkyddIHx8IDAgfX08L3NwYW4+XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgIGNsYXNzPVwiZmlsdGVyLXRhYlwiIFxuICAgICAgICAgICAgICA6Y2xhc3M9XCJ7IGFjdGl2ZTogZmlsdGVyVGFnID09PSAn57uP5rWO5a2mJyB9XCJcbiAgICAgICAgICAgICAgQGNsaWNrPVwiZmlsdGVyVGFnID0gJ+e7j+a1juWtpidcIlxuICAgICAgICAgICAgPlxuICAgICAgICAgICAgICDnu4/mtY7lraY8c3BhbiB2LWlmPVwic3RhdGlzdGljcz8udGFnX3BlbmRpbmdcIiBjbGFzcz1cImNvdW50LWJhZGdlXCI+e3sgc3RhdGlzdGljcy50YWdfcGVuZGluZ1sn57uP5rWO5a2mJ10gfHwgMCB9fTwvc3Bhbj5cbiAgICAgICAgICAgIDwvYnV0dG9uPlxuICAgICAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICAgICAgY2xhc3M9XCJmaWx0ZXItdGFiXCIgXG4gICAgICAgICAgICAgIDpjbGFzcz1cInsgYWN0aXZlOiBmaWx0ZXJUYWcgPT09ICflv4PnkIblraYnIH1cIlxuICAgICAgICAgICAgICBAY2xpY2s9XCJmaWx0ZXJUYWcgPSAn5b+D55CG5a2mJ1wiXG4gICAgICAgICAgICA+XG4gICAgICAgICAgICAgIOW/g+eQhuWtpjxzcGFuIHYtaWY9XCJzdGF0aXN0aWNzPy50YWdfcGVuZGluZ1wiIGNsYXNzPVwiY291bnQtYmFkZ2VcIj57eyBzdGF0aXN0aWNzLnRhZ19wZW5kaW5nWyflv4PnkIblraYnXSB8fCAwIH19PC9zcGFuPlxuICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPHNlbGVjdCB2LW1vZGVsPVwic3RhdHVzRmlsdGVyXCIgY2xhc3M9XCJmaWx0ZXItc2VsZWN0IGZpbHRlci1zZWxlY3QtbmFycm93XCI+XG4gICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwicGVuZGluZ1wiPuW+heWuoeaguCh7eyBzdGF0aXN0aWNzPy5wZW5kaW5nIHx8IDAgfX0pPC9vcHRpb24+XG4gICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwic2VsZWN0ZWRcIj7lt7LlronmjpIoe3sgc3RhdGlzdGljcz8uc2VsZWN0ZWQgfHwgMCB9fSk8L29wdGlvbj5cbiAgICAgICAgICAgIDxvcHRpb24gdmFsdWU9XCJkZWxldGVkXCI+5bey5Yig6ZmkKHt7IHN0YXRpc3RpY3M/LmRlbGV0ZWQgfHwgMCB9fSk8L29wdGlvbj5cbiAgICAgICAgICA8L3NlbGVjdD5cbiAgICAgICAgICA8c2VsZWN0IHYtbW9kZWw9XCJmaWx0ZXJQbGF0Zm9ybVwiIGNsYXNzPVwiZmlsdGVyLXNlbGVjdCBmaWx0ZXItc2VsZWN0LW5hcnJvd1wiPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cInpoaWh1XCI+55+l5LmOPC9vcHRpb24+XG4gICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwiY3JlYXRvcl92aWRlb1wiPuWvueagh+WNmuS4uzwvb3B0aW9uPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cIm1hbnVhbFwiPuS6uuW3pTwvb3B0aW9uPlxuICAgICAgICAgICAgPG9wdGlvbiA6dmFsdWU9XCJudWxsXCI+5YWo6YOo5rig6YGTPC9vcHRpb24+XG4gICAgICAgICAgPC9zZWxlY3Q+XG4gICAgICAgICAgPHNlbGVjdCB2LW1vZGVsPVwic29ydEJ5XCIgY2xhc3M9XCJmaWx0ZXItc2VsZWN0IGZpbHRlci1zZWxlY3Qtc29ydFwiPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cInB1Ymxpc2hlZF9hdFwiPuaMieaXtumXtDwvb3B0aW9uPlxuICAgICAgICAgICAgPG9wdGlvbiB2YWx1ZT1cImFncmVlX2NvdW50XCI+5oyJ6LWe5ZCMPC9vcHRpb24+XG4gICAgICAgICAgICA8b3B0aW9uIHZhbHVlPVwiY29tbWVudF9jb3VudFwiPuaMieivhOiuujwvb3B0aW9uPlxuICAgICAgICAgIDwvc2VsZWN0PlxuICAgICAgICA8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cImhlYWRlci1yaWdodFwiPlxuICAgICAgICAgIDxidXR0b25cbiAgICAgICAgICAgIHYtaWY9XCJzdGF0dXNGaWx0ZXIgPT09ICdwZW5kaW5nJyAmJiBmaWx0ZXJUYWdcIlxuICAgICAgICAgICAgY2xhc3M9XCJhaS1maWx0ZXItYnRuXCJcbiAgICAgICAgICAgIEBjbGljaz1cInN0YXJ0QUlGaWx0ZXJcIlxuICAgICAgICAgICAgOmRpc2FibGVkPVwiYWlGaWx0ZXJpbmdcIlxuICAgICAgICAgID5cbiAgICAgICAgICAgIDxzdmcgdi1pZj1cIiFhaUZpbHRlcmluZ1wiIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiIHN0cm9rZS13aWR0aD1cIjJcIj5cbiAgICAgICAgICAgICAgPHBvbHlnb24gcG9pbnRzPVwiMjIgMyAyIDMgMTAgMTIuNDYgMTAgMTkgMTQgMjEgMTQgMTIuNDYgMjIgM1wiLz5cbiAgICAgICAgICAgIDwvc3ZnPlxuICAgICAgICAgICAgPHN2ZyB2LWVsc2UgY2xhc3M9XCJzcGlubmluZ1wiIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiIHN0cm9rZS13aWR0aD1cIjJcIj5cbiAgICAgICAgICAgICAgPGNpcmNsZSBjeD1cIjEyXCIgY3k9XCIxMlwiIHI9XCIxMFwiIHN0cm9rZS1kYXNoYXJyYXk9XCIzMS40IDMxLjRcIi8+XG4gICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICAgIHt7IGFpRmlsdGVyaW5nID8gJ0FJ5YiG5p6Q5LitLi4uJyA6ICfluK7miJHov4fmu6QnIH19XG4gICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cIm5ldy1hcnRpY2xlLWJ0blwiIEBjbGljaz1cInNob3dDcmVhdGVNb2RhbCA9IHRydWVcIj5cbiAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XG4gICAgICAgICAgICAgIDxsaW5lIHgxPVwiMTJcIiB5MT1cIjVcIiB4Mj1cIjEyXCIgeTI9XCIxOVwiLz5cbiAgICAgICAgICAgICAgPGxpbmUgeDE9XCI1XCIgeTE9XCIxMlwiIHgyPVwiMTlcIiB5Mj1cIjEyXCIvPlxuICAgICAgICAgICAgPC9zdmc+XG4gICAgICAgICAgICDmlrDlu7rmlofnq6BcbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g5Y+R5biD6K6h5YiS6Z2i5p2/OiDnrqHpgZPph4zlt7LpgInmnKrlj5HlroznmoTop4bpopEgKOWItuS9nOmYn+WIlyArIOS4ieW5s+WPsOaOkuacnykgLS0+XG4gICAgPGRpdiBjbGFzcz1cInNjaGVkdWxlLXBhbmVsXCI+XG4gICAgICA8ZGl2IGNsYXNzPVwic2NoZWR1bGUtaGVhZGVyXCIgQGNsaWNrPVwic2hvd1NjaGVkdWxlID0gIXNob3dTY2hlZHVsZVwiPlxuICAgICAgICA8c3BhbiBjbGFzcz1cInNjaGVkdWxlLXRpdGxlXCI+5Y+R5biD6K6h5YiSPC9zcGFuPlxuICAgICAgICA8c3BhbiB2LWlmPVwic2NoZWR1bGVTdW1tYXJ5XCIgY2xhc3M9XCJzY2hlZHVsZS1zdW1tYXJ5XCI+XG4gICAgICAgICAg566h6YGTIHt7IHNjaGVkdWxlU3VtbWFyeS50b3RhbCB9fSDmnaEgwrcg5Yi25L2c5LitL+aOkumYnyB7eyBzY2hlZHVsZVN1bW1hcnkubWFraW5nIH19IMK3IOW3suaOkuacnyB7eyBzY2hlZHVsZVN1bW1hcnkuc2NoZWR1bGVkIH19XG4gICAgICAgIDwvc3Bhbj5cbiAgICAgICAgPHNwYW4gY2xhc3M9XCJzY2hlZHVsZS10b2dnbGVcIj57eyBzaG93U2NoZWR1bGUgPyAn5pS26LW3IOKWsicgOiAn5bGV5byAIOKWvCcgfX08L3NwYW4+XG4gICAgICA8L2Rpdj5cbiAgICAgIDxkaXYgdi1pZj1cInNob3dTY2hlZHVsZVwiIGNsYXNzPVwic2NoZWR1bGUtYm9keVwiPlxuICAgICAgICA8ZGl2IHYtaWY9XCJzY2hlZHVsZUxvYWRpbmdcIiBjbGFzcz1cInNjaGVkdWxlLWVtcHR5XCI+5Yqg6L295LitLi4uPC9kaXY+XG4gICAgICAgIDxkaXYgdi1lbHNlLWlmPVwic2NoZWR1bGVJdGVtcy5sZW5ndGggPT09IDBcIiBjbGFzcz1cInNjaGVkdWxlLWVtcHR5XCI+566h6YGT5Li656m6ICjmsLTkvY3ooaXnu5nkvJroh6rliqjpgInpopgpPC9kaXY+XG4gICAgICAgIDx0YWJsZSB2LWVsc2UgY2xhc3M9XCJzY2hlZHVsZS10YWJsZVwiPlxuICAgICAgICAgIDx0aGVhZD5cbiAgICAgICAgICAgIDx0cj5cbiAgICAgICAgICAgICAgPHRoIGNsYXNzPVwiY29sLXRpdGxlXCI+6KeG6aKR6YCJ6aKYPC90aD5cbiAgICAgICAgICAgICAgPHRoPuadpea6kDwvdGg+XG4gICAgICAgICAgICAgIDx0aD7mlrDpspzluqY8L3RoPlxuICAgICAgICAgICAgICA8dGg+S0lNSTwvdGg+XG4gICAgICAgICAgICAgIDx0aD7liLbkvZw8L3RoPlxuICAgICAgICAgICAgICA8dGg+6KeG6aKR5Y+3PC90aD5cbiAgICAgICAgICAgICAgPHRoPuaKlumfszwvdGg+XG4gICAgICAgICAgICAgIDx0aD5C56uZPC90aD5cbiAgICAgICAgICAgIDwvdHI+XG4gICAgICAgICAgPC90aGVhZD5cbiAgICAgICAgICA8dGJvZHk+XG4gICAgICAgICAgICA8dHIgdi1mb3I9XCJpdGVtIGluIHNjaGVkdWxlSXRlbXNcIiA6a2V5PVwiaXRlbS5pZFwiPlxuICAgICAgICAgICAgICA8dGQgY2xhc3M9XCJjb2wtdGl0bGVcIiA6dGl0bGU9XCJpdGVtLnRpdGxlXCI+e3sgaXRlbS50aXRsZSB9fTwvdGQ+XG4gICAgICAgICAgICAgIDx0ZD5cbiAgICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cInNjaGVkdWxlLXNvdXJjZVwiIDpjbGFzcz1cInsgY3JlYXRvcjogaXRlbS5wbGF0Zm9ybSA9PT0gJ2NyZWF0b3JfdmlkZW8nIH1cIj5cbiAgICAgICAgICAgICAgICAgIHt7IGl0ZW0ucGxhdGZvcm0gPT09ICdjcmVhdG9yX3ZpZGVvJyA/ICflr7nmoIfljZrkuLsnIDogKGl0ZW0ucGxhdGZvcm0gPT09ICdtYW51YWwnID8gJ+S6uuW3pScgOiAn55+l5LmOJykgfX1cbiAgICAgICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICAgIDwvdGQ+XG4gICAgICAgICAgICAgIDx0ZD5cbiAgICAgICAgICAgICAgICA8c3BhbiB2LWlmPVwiaXRlbS5ldmVudF9hZ2VfZGF5cyAhPT0gbnVsbFwiIGNsYXNzPVwiZnJlc2gtYmFkZ2VcIiA6Y2xhc3M9XCJmcmVzaEJhZGdlQ2xhc3NCeURheXMoaXRlbS5ldmVudF9hZ2VfZGF5cylcIj5cbiAgICAgICAgICAgICAgICAgIHt7IGl0ZW0uZXZlbnRfYWdlX2RheXMgfX1kXG4gICAgICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgICAgIDxzcGFuIHYtZWxzZT4tPC9zcGFuPlxuICAgICAgICAgICAgICA8L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgaXRlbS5raW1pX3BpY2tfc2NvcmUgPz8gJy0nIH19PC90ZD5cbiAgICAgICAgICAgICAgPHRkPlxuICAgICAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwic2NoZWR1bGUtc3RhdHVzXCIgOmNsYXNzPVwiJ3ZzLScgKyAoaXRlbS52aWRlb19zdGF0dXMgfHwgJ3BlbmRpbmcnKVwiPlxuICAgICAgICAgICAgICAgICAge3sgdmlkZW9TdGF0dXNUZXh0KGl0ZW0udmlkZW9fc3RhdHVzKSB9fVxuICAgICAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgICAgPC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IHBsYXRmb3JtQ2VsbChpdGVtLmNoYW5uZWxzX3N0YXR1cywgaXRlbS5jaGFubmVsc19zY2hlZHVsZWRfYXQpIH19PC90ZD5cbiAgICAgICAgICAgICAgPHRkPnt7IHBsYXRmb3JtQ2VsbChpdGVtLmRvdXlpbl9zdGF0dXMsIGl0ZW0uZG91eWluX3NjaGVkdWxlZF9hdCkgfX08L3RkPlxuICAgICAgICAgICAgICA8dGQ+e3sgcGxhdGZvcm1DZWxsKGl0ZW0uYmlsaWJpbGlfc3RhdHVzLCBpdGVtLmJpbGliaWxpX3NjaGVkdWxlZF9hdCkgfX08L3RkPlxuICAgICAgICAgICAgPC90cj5cbiAgICAgICAgICA8L3Rib2R5PlxuICAgICAgICA8L3RhYmxlPlxuICAgICAgPC9kaXY+XG4gICAgPC9kaXY+XG5cbiAgICA8IS0tIOaJuemHj+aTjeS9nOW3peWFt+agjyAtLT5cbiAgICA8ZGl2IHYtaWY9XCJhcnRpY2xlcy5sZW5ndGggPiAwXCIgY2xhc3M9XCJiYXRjaC1hY3Rpb25zLWJhclwiPlxuICAgICAgPGRpdiBjbGFzcz1cImJhdGNoLWFjdGlvbnMtbGVmdFwiPlxuICAgICAgICA8bGFiZWwgY2xhc3M9XCJiYXRjaC1jaGVja2JveC1sYWJlbFwiPlxuICAgICAgICAgIDxpbnB1dCBcbiAgICAgICAgICAgIHR5cGU9XCJjaGVja2JveFwiIFxuICAgICAgICAgICAgY2xhc3M9XCJiYXRjaC1jaGVja2JveFwiXG4gICAgICAgICAgICA6Y2hlY2tlZD1cImlzQWxsU2VsZWN0ZWRcIlxuICAgICAgICAgICAgOmluZGV0ZXJtaW5hdGU9XCJpc0luZGV0ZXJtaW5hdGVcIlxuICAgICAgICAgICAgQGNoYW5nZT1cInRvZ2dsZVNlbGVjdEFsbFwiXG4gICAgICAgICAgLz5cbiAgICAgICAgICA8c3BhbiBjbGFzcz1cImJhdGNoLWNoZWNrYm94LXRleHRcIj5cbiAgICAgICAgICAgIHt7IGlzQWxsU2VsZWN0ZWQgPyAn5Y+W5raI5YWo6YCJJyA6ICflhajpgInlvZPliY3pobUnIH19XG4gICAgICAgICAgICA8c3BhbiB2LWlmPVwic2VsZWN0ZWRBcnRpY2xlSWRzLnNpemUgPiAwXCIgY2xhc3M9XCJzZWxlY3RlZC1jb3VudFwiPu+8iOW3sumAiSB7eyBzZWxlY3RlZEFydGljbGVJZHMuc2l6ZSB9fSDpobnvvIk8L3NwYW4+XG4gICAgICAgICAgPC9zcGFuPlxuICAgICAgICA8L2xhYmVsPlxuICAgICAgPC9kaXY+XG4gICAgICA8ZGl2IHYtaWY9XCJzZWxlY3RlZEFydGljbGVJZHMuc2l6ZSA+IDBcIiBjbGFzcz1cImJhdGNoLWFjdGlvbnMtcmlnaHRcIj5cbiAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICBjbGFzcz1cImJhdGNoLWRlbGV0ZS1idG5cIiBcbiAgICAgICAgICBAY2xpY2s9XCJiYXRjaERlbGV0ZVwiXG4gICAgICAgICAgOmRpc2FibGVkPVwiYmF0Y2hEZWxldGluZ1wiXG4gICAgICAgID5cbiAgICAgICAgICA8c3ZnIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiPlxuICAgICAgICAgICAgPHBvbHlsaW5lIHBvaW50cz1cIjMgNiA1IDYgMjEgNlwiLz5cbiAgICAgICAgICAgIDxwYXRoIGQ9XCJNMTkgNnYxNGEyIDIgMCAwIDEtMiAySDdhMiAyIDAgMCAxLTItMlY2bTMgMFY0YTIgMiAwIDAgMSAyLTJoNGEyIDIgMCAwIDEgMiAydjJcIi8+XG4gICAgICAgICAgPC9zdmc+XG4gICAgICAgICAge3sgYmF0Y2hEZWxldGluZyA/ICfliKDpmaTkuK0uLi4nIDogYOaJuemHj+WIoOmZpCAoJHtzZWxlY3RlZEFydGljbGVJZHMuc2l6ZX0pYCB9fVxuICAgICAgICA8L2J1dHRvbj5cbiAgICAgIDwvZGl2PlxuICAgIDwvZGl2PlxuXG4gICAgPGRpdiBjbGFzcz1cImFydGljbGVzLWxpc3RcIj5cbiAgICAgIDxkaXYgdi1mb3I9XCJhcnRpY2xlIGluIGFydGljbGVzXCIgOmtleT1cImFydGljbGUuaWRcIiBjbGFzcz1cImFydGljbGUtaXRlbVwiIDpjbGFzcz1cInsgc2VsZWN0ZWQ6IGFydGljbGUuaXNfc2VsZWN0ZWQsIGRlbGV0ZWQ6IGFydGljbGUuaXNfZGVsZXRlZCB9XCI+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJhcnRpY2xlLXJvd1wiPlxuICAgICAgICAgIDwhLS0g5om56YeP6YCJ5oup5aSN6YCJ5qGGIC0tPlxuICAgICAgICAgIDxsYWJlbCBjbGFzcz1cImFydGljbGUtY2hlY2tib3gtbGFiZWxcIj5cbiAgICAgICAgICAgIDxpbnB1dCBcbiAgICAgICAgICAgICAgdHlwZT1cImNoZWNrYm94XCIgXG4gICAgICAgICAgICAgIGNsYXNzPVwiYXJ0aWNsZS1jaGVja2JveFwiXG4gICAgICAgICAgICAgIDpjaGVja2VkPVwic2VsZWN0ZWRBcnRpY2xlSWRzLmhhcyhhcnRpY2xlLmlkKVwiXG4gICAgICAgICAgICAgIEBjaGFuZ2U9XCJ0b2dnbGVBcnRpY2xlU2VsZWN0aW9uKGFydGljbGUuaWQpXCJcbiAgICAgICAgICAgICAgQGNsaWNrLnN0b3BcbiAgICAgICAgICAgIC8+XG4gICAgICAgICAgPC9sYWJlbD5cbiAgICAgICAgICBcbiAgICAgICAgICA8ZGl2IFxuICAgICAgICAgICAgY2xhc3M9XCJhcnRpY2xlLWxpbmsgY2xpY2thYmxlLXRpdGxlXCJcbiAgICAgICAgICAgIEBjbGljaz1cInNob3dBcnRpY2xlQ29udGVudChhcnRpY2xlKVwiXG4gICAgICAgICAgPlxuICAgICAgICAgICAgPGgzIGNsYXNzPVwiYXJ0aWNsZS10aXRsZVwiPnt7IGFydGljbGUudGl0bGUgfX08L2gzPlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIFxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJhcnRpY2xlLW1ldGEtaW5saW5lXCI+XG4gICAgICAgICAgICA8c3BhbiB2LWlmPVwiYXJ0aWNsZS5wbGF0Zm9ybSA9PT0gJ21hbnVhbCdcIiBjbGFzcz1cImFydGljbGUtcGxhdGZvcm0gbWFudWFsLWJhZGdlXCI+XG4gICAgICAgICAgICAgIOS6uuW3pVxuICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgPHNwYW4gdi1pZj1cImFydGljbGUucGxhdGZvcm0gPT09ICdjcmVhdG9yX3ZpZGVvJ1wiIGNsYXNzPVwiYXJ0aWNsZS1wbGF0Zm9ybSBjcmVhdG9yLWJhZGdlXCIgdGl0bGU9XCLlr7nmoIfljZrkuLvng63pl6jop4bpopHovazlhpnnqL/ms6jlhaUgKGNyZWF0b3JfdmlkZW9faW5qZWN0KVwiPlxuICAgICAgICAgICAgICDlr7nmoIfljZrkuLtcbiAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgIDwhLS0g5paw6bKc5bqmOiDkuovku7bml7bpl7QgKHB1Ymxpc2hlZF9hdCkg6Led5LuK5aSp5pWwLCDiiaQzZCDlnKjpgInpopjml7botbAgRnJlc2gg5by65L+d5bqV6YCa6YGTIC0tPlxuICAgICAgICAgICAgPHNwYW5cbiAgICAgICAgICAgICAgdi1pZj1cImZyZXNoQWdlRGF5cyhhcnRpY2xlKSAhPT0gbnVsbFwiXG4gICAgICAgICAgICAgIGNsYXNzPVwiZnJlc2gtYmFkZ2VcIlxuICAgICAgICAgICAgICA6Y2xhc3M9XCJmcmVzaEJhZGdlQ2xhc3MoYXJ0aWNsZSlcIlxuICAgICAgICAgICAgICA6dGl0bGU9XCJg5LqL5Lu25pe26Ze06Led5LuKICR7ZnJlc2hBZ2VEYXlzKGFydGljbGUpfSDlpKkgKOKJpDPlpKnotbAgRnJlc2gg5by65L+d5bqV6YCa6YGTKWBcIlxuICAgICAgICAgICAgPlxuICAgICAgICAgICAgICDpspwge3sgZnJlc2hBZ2VEYXlzKGFydGljbGUpIH19ZFxuICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgPCEtLSDlt7LlronmjpLnsbvlnovmoIfnrb4gLS0+XG4gICAgICAgICAgICA8c3BhbiB2LWlmPVwiYXJ0aWNsZS5pc19zZWxlY3RlZCAmJiBhcnRpY2xlLmNvbnRlbnRfdHlwZVwiIGNsYXNzPVwiY29udGVudC10eXBlLWJhZGdlXCIgOmNsYXNzPVwiYXJ0aWNsZS5jb250ZW50X3R5cGVcIj5cbiAgICAgICAgICAgICAgPHRlbXBsYXRlIHYtaWY9XCJhcnRpY2xlLmNvbnRlbnRfdHlwZSA9PT0gJ3ZpZGVvJ1wiPuinhumikTwvdGVtcGxhdGU+XG4gICAgICAgICAgICAgIDx0ZW1wbGF0ZSB2LWVsc2UtaWY9XCJhcnRpY2xlLmNvbnRlbnRfdHlwZSA9PT0gJ2ltYWdlJ1wiPuWbvuaWhzwvdGVtcGxhdGU+XG4gICAgICAgICAgICAgIDx0ZW1wbGF0ZSB2LWVsc2UtaWY9XCJhcnRpY2xlLmNvbnRlbnRfdHlwZSA9PT0gJ2JvdGgnXCI+6KeG6aKRK+WbvuaWhzwvdGVtcGxhdGU+XG4gICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICA8IS0tIEtJTUkg6KeG6aKR5Y+36YCJ6aKY6K+E5YiGICjku4Xor4Tov4fnmoTmnIksIOWAmemAieaxoCA4MCDmnaHkuYvlpJbnmoTkuI3kvJrmnIkpIC0tPlxuICAgICAgICAgICAgPHNwYW5cbiAgICAgICAgICAgICAgdi1pZj1cImFydGljbGUua2ltaV9waWNrX3Njb3JlICE9PSBudWxsICYmIGFydGljbGUua2ltaV9waWNrX3Njb3JlICE9PSB1bmRlZmluZWRcIlxuICAgICAgICAgICAgICBjbGFzcz1cImtpbWktc2NvcmUtYmFkZ2VcIlxuICAgICAgICAgICAgICA6Y2xhc3M9XCJnZXRLaW1pQmFkZ2VDbGFzcyhhcnRpY2xlKVwiXG4gICAgICAgICAgICAgIDp0aXRsZT1cImdldEtpbWlUb29sdGlwKGFydGljbGUpXCJcbiAgICAgICAgICAgID5cbiAgICAgICAgICAgICAgS0lNSSB7eyBhcnRpY2xlLmtpbWlfcGlja19zY29yZSB9fVxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cImtpbWktcmVhc29uLW1pbmlcIj57eyBnZXRLaW1pUmVhc29uU2hvcnQoYXJ0aWNsZSkgfX08L3NwYW4+XG4gICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICA8c3BhbiB2LWlmPVwiYXJ0aWNsZS5zZWFyY2hfa2V5d29yZFwiIGNsYXNzPVwiYXJ0aWNsZS1rZXl3b3JkXCI+XG4gICAgICAgICAgICAgIHt7IGFydGljbGUuc2VhcmNoX2tleXdvcmQgfX1cbiAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibWV0YS1pdGVtXCI+XG4gICAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJjdXJyZW50Q29sb3JcIj5cbiAgICAgICAgICAgICAgICA8cGF0aCBkPVwiTTEyIDIxLjM1bC0xLjQ1LTEuMzJDNS40IDE1LjM2IDIgMTIuMjggMiA4LjUgMiA1LjQyIDQuNDIgMyA3LjUgM2MxLjc0IDAgMy40MS44MSA0LjUgMi4wOUMxMy4wOSAzLjgxIDE0Ljc2IDMgMTYuNSAzIDE5LjU4IDMgMjIgNS40MiAyMiA4LjVjMCAzLjc4LTMuNCA2Ljg2LTguNTUgMTEuNTRMMTIgMjEuMzV6XCIvPlxuICAgICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICAgICAge3sgYXJ0aWNsZS5hZ3JlZV9jb3VudCB8fCAwIH19XG4gICAgICAgICAgICA8L3NwYW4+XG4gICAgICAgICAgICA8c3BhbiBjbGFzcz1cIm1ldGEtaXRlbVwiPlxuICAgICAgICAgICAgICA8c3ZnIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwiY3VycmVudENvbG9yXCI+XG4gICAgICAgICAgICAgICAgPHBhdGggZD1cIk0yMS45OSA0YzAtMS4xLS44OS0yLTItMkg0Yy0xLjEgMC0yIC45LTIgMnYxMmMwIDEuMS45IDIgMiAyaDE0bDQgNC0uMDEtMTh6TTE4IDE0SDZ2LTJoMTJ2MnptMC0zSDZWOWgxMnYyem0wLTNINlY2aDEydjJ6XCIvPlxuICAgICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICAgICAge3sgYXJ0aWNsZS5jb21tZW50X2NvdW50IHx8IDAgfX1cbiAgICAgICAgICAgIDwvc3Bhbj5cbiAgICAgICAgICAgIDxzcGFuIGNsYXNzPVwibWV0YS1pdGVtXCIgdi1pZj1cImFydGljbGUuY29udGVudF9sZW5ndGhcIj5cbiAgICAgICAgICAgICAge3sgZm9ybWF0Q29udGVudExlbmd0aChhcnRpY2xlLmNvbnRlbnRfbGVuZ3RoKSB9fVxuICAgICAgICAgICAgPC9zcGFuPlxuICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJhcnRpY2xlLWRhdGVcIj57eyBmb3JtYXREYXRlKGFydGljbGUucHVibGlzaGVkX2F0IHx8IGFydGljbGUuY3JlYXRlZF9hdCkgfX08L3NwYW4+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgXG4gICAgICAgICAgPGRpdiBjbGFzcz1cImFydGljbGUtYWN0aW9uc1wiPlxuICAgICAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICAgICAgY2xhc3M9XCJhY3Rpb24tYnRuIHNlbGVjdC1idG5cIlxuICAgICAgICAgICAgICA6Y2xhc3M9XCJ7IGFjdGl2ZTogYXJ0aWNsZS5pc19zZWxlY3RlZCB9XCJcbiAgICAgICAgICAgICAgQGNsaWNrPVwidG9nZ2xlU2VsZWN0KGFydGljbGUpXCJcbiAgICAgICAgICAgICAgOnRpdGxlPVwiYXJ0aWNsZS5pc19zZWxlY3RlZCA/ICflj5bmtojpgInkuK0nIDogJ+mAieS4rSdcIlxuICAgICAgICAgICAgPlxuICAgICAgICAgICAgICA8c3ZnIHYtaWY9XCJhcnRpY2xlLmlzX3NlbGVjdGVkXCIgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJjdXJyZW50Q29sb3JcIj5cbiAgICAgICAgICAgICAgICA8cGF0aCBkPVwiTTkgMTYuMTdMNC44MyAxMmwtMS40MiAxLjQxTDkgMTkgMjEgN2wtMS40MS0xLjQxelwiLz5cbiAgICAgICAgICAgICAgPC9zdmc+XG4gICAgICAgICAgICAgIDxzdmcgdi1lbHNlIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiPlxuICAgICAgICAgICAgICAgIDxyZWN0IHg9XCIzXCIgeT1cIjNcIiB3aWR0aD1cIjE4XCIgaGVpZ2h0PVwiMThcIiByeD1cIjJcIiBzdHJva2Utd2lkdGg9XCIyXCIvPlxuICAgICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICAgIDwvYnV0dG9uPlxuICAgICAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICAgICAgY2xhc3M9XCJhY3Rpb24tYnRuIGRlbGV0ZS1idG5cIlxuICAgICAgICAgICAgICBAY2xpY2s9XCJtYXJrUmVqZWN0ZWQoYXJ0aWNsZSlcIlxuICAgICAgICAgICAgICA6dGl0bGU9XCJhcnRpY2xlLmlzX2RlbGV0ZWQgPyAn5Y+W5raI5qCH6K6wJyA6ICfmoIforrDkuLrliKDpmaQnXCJcbiAgICAgICAgICAgID5cbiAgICAgICAgICAgICAgPHN2ZyB2aWV3Qm94PVwiMCAwIDI0IDI0XCIgZmlsbD1cIm5vbmVcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cbiAgICAgICAgICAgICAgICA8cG9seWxpbmUgcG9pbnRzPVwiMyA2IDUgNiAyMSA2XCIvPlxuICAgICAgICAgICAgICAgIDxwYXRoIGQ9XCJNMTkgNnYxNGEyIDIgMCAwIDEtMiAySDdhMiAyIDAgMCAxLTItMlY2bTMgMFY0YTIgMiAwIDAgMSAyLTJoNGEyIDIgMCAwIDEgMiAydjJcIi8+XG4gICAgICAgICAgICAgIDwvc3ZnPlxuICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgIDwvZGl2PlxuICAgICAgPC9kaXY+XG4gICAgPC9kaXY+XG5cbiAgICA8ZGl2IHYtaWY9XCJsb2FkaW5nXCIgY2xhc3M9XCJsb2FkaW5nXCI+5Yqg6L295LitLi4uPC9kaXY+XG4gICAgPGRpdiB2LWlmPVwiIWxvYWRpbmcgJiYgYXJ0aWNsZXMubGVuZ3RoID09PSAwXCIgY2xhc3M9XCJlbXB0eVwiPuaaguaXoOaWh+eroDwvZGl2PlxuXG4gICAgPGRpdiB2LWlmPVwicGFnaW5hdGlvbiAmJiBwYWdpbmF0aW9uLnRvdGFsX3BhZ2VzID4gMVwiIGNsYXNzPVwicGFnaW5hdGlvblwiPlxuICAgICAgPGJ1dHRvbiBcbiAgICAgICAgY2xhc3M9XCJwYWdlLWJ0blwiIFxuICAgICAgICA6ZGlzYWJsZWQ9XCJwYWdpbmF0aW9uLnBhZ2UgPT09IDFcIlxuICAgICAgICBAY2xpY2s9XCJjaGFuZ2VQYWdlKHBhZ2luYXRpb24ucGFnZSAtIDEpXCJcbiAgICAgID5cbiAgICAgICAg5LiK5LiA6aG1XG4gICAgICA8L2J1dHRvbj5cbiAgICAgIFxuICAgICAgPCEtLSDpobXnoIHmjInpkq4gLS0+XG4gICAgICA8ZGl2IGNsYXNzPVwicGFnZS1udW1iZXJzXCI+XG4gICAgICAgIDx0ZW1wbGF0ZSB2LWZvcj1cInBhZ2VOdW0gaW4gdmlzaWJsZVBhZ2VzXCIgOmtleT1cInBhZ2VOdW1cIj5cbiAgICAgICAgICA8YnV0dG9uXG4gICAgICAgICAgICB2LWlmPVwicGFnZU51bSAhPT0gJy4uLidcIlxuICAgICAgICAgICAgY2xhc3M9XCJwYWdlLW51bWJlci1idG5cIlxuICAgICAgICAgICAgOmNsYXNzPVwieyBhY3RpdmU6IHBhZ2VOdW0gPT09IHBhZ2luYXRpb24ucGFnZSB9XCJcbiAgICAgICAgICAgIEBjbGljaz1cImNoYW5nZVBhZ2UocGFnZU51bSlcIlxuICAgICAgICAgID5cbiAgICAgICAgICAgIHt7IHBhZ2VOdW0gfX1cbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8c3BhbiB2LWVsc2UgY2xhc3M9XCJwYWdlLWVsbGlwc2lzXCI+Li4uPC9zcGFuPlxuICAgICAgICA8L3RlbXBsYXRlPlxuICAgICAgPC9kaXY+XG4gICAgICBcbiAgICAgIDxidXR0b24gXG4gICAgICAgIGNsYXNzPVwicGFnZS1idG5cIiBcbiAgICAgICAgOmRpc2FibGVkPVwicGFnaW5hdGlvbi5wYWdlID49IHBhZ2luYXRpb24udG90YWxfcGFnZXNcIlxuICAgICAgICBAY2xpY2s9XCJjaGFuZ2VQYWdlKHBhZ2luYXRpb24ucGFnZSArIDEpXCJcbiAgICAgID5cbiAgICAgICAg5LiL5LiA6aG1XG4gICAgICA8L2J1dHRvbj5cbiAgICAgIFxuICAgICAgPCEtLSDot7PovazovpPlhaXmoYYgLS0+XG4gICAgICA8ZGl2IGNsYXNzPVwicGFnZS1qdW1wXCI+XG4gICAgICAgIDxzcGFuIGNsYXNzPVwianVtcC1sYWJlbFwiPui3s+i9rOWIsDwvc3Bhbj5cbiAgICAgICAgPGlucHV0XG4gICAgICAgICAgdi1tb2RlbC5udW1iZXI9XCJqdW1wUGFnZVwiXG4gICAgICAgICAgdHlwZT1cIm51bWJlclwiXG4gICAgICAgICAgY2xhc3M9XCJqdW1wLWlucHV0XCJcbiAgICAgICAgICA6bWluPVwiMVwiXG4gICAgICAgICAgOm1heD1cInBhZ2luYXRpb24udG90YWxfcGFnZXNcIlxuICAgICAgICAgIEBrZXl1cC5lbnRlcj1cImp1bXBUb1BhZ2VcIlxuICAgICAgICAvPlxuICAgICAgICA8c3BhbiBjbGFzcz1cImp1bXAtbGFiZWxcIj7pobU8L3NwYW4+XG4gICAgICAgIDxidXR0b24gY2xhc3M9XCJqdW1wLWJ0blwiIEBjbGljaz1cImp1bXBUb1BhZ2VcIj7ot7Povaw8L2J1dHRvbj5cbiAgICAgIDwvZGl2PlxuICAgICAgXG4gICAgICA8c3BhbiBjbGFzcz1cInBhZ2UtaW5mb1wiPlxuICAgICAgICDlhbEge3sgcGFnaW5hdGlvbi50b3RhbCB9fSDmnaFcbiAgICAgIDwvc3Bhbj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g5paH56ug57yW6L6R5qih5oCB5qGGIC0tPlxuICAgIDxkaXYgdi1pZj1cInNob3dDb250ZW50TW9kYWxcIiBjbGFzcz1cIm1vZGFsLW92ZXJsYXlcIj5cbiAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1jb250ZW50IGNyZWF0ZS1hcnRpY2xlLW1vZGFsXCI+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1oZWFkZXJcIj5cbiAgICAgICAgICA8aDI+57yW6L6R5paH56ugIDxzcGFuIGNsYXNzPVwiYXJ0aWNsZS1pZC1iYWRnZVwiIHYtaWY9XCJ2aWV3aW5nQXJ0aWNsZT8uaWRcIj4oSUQ6IHt7IHZpZXdpbmdBcnRpY2xlLmlkIH19KTwvc3Bhbj48L2gyPlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1oZWFkZXItYWN0aW9uc1wiPlxuICAgICAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICAgICAgdi1pZj1cInZpZXdpbmdBcnRpY2xlPy51cmwgJiYgIXZpZXdpbmdBcnRpY2xlPy51cmwuc3RhcnRzV2l0aCgnbWFudWFsLScpICYmIHZpZXdpbmdBcnRpY2xlPy51cmwuaW5jbHVkZXMoJ3poaWh1LmNvbScpXCJcbiAgICAgICAgICAgICAgY2xhc3M9XCJyZWNyYXdsLWJ0blwiXG4gICAgICAgICAgICAgIEBjbGljaz1cInJlY3Jhd2xBcnRpY2xlXCJcbiAgICAgICAgICAgICAgOmRpc2FibGVkPVwicmVjcmF3bGluZ1wiXG4gICAgICAgICAgICA+XG4gICAgICAgICAgICAgIDxzdmcgdi1pZj1cIiFyZWNyYXdsaW5nXCIgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XG4gICAgICAgICAgICAgICAgPHBhdGggZD1cIk0yMyA0djZoLTZcIi8+XG4gICAgICAgICAgICAgICAgPHBhdGggZD1cIk0xIDIwdi02aDZcIi8+XG4gICAgICAgICAgICAgICAgPHBhdGggZD1cIk0zLjUxIDlhOSA5IDAgMCAxIDE0Ljg1LTMuMzZMMjMgMTBNMSAxNGw0LjY0IDQuMzZBOSA5IDAgMCAwIDIwLjQ5IDE1XCIvPlxuICAgICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICAgICAgPHN2ZyB2LWVsc2UgY2xhc3M9XCJzcGlubmluZ1wiIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiPlxuICAgICAgICAgICAgICAgIDxjaXJjbGUgY3g9XCIxMlwiIGN5PVwiMTJcIiByPVwiMTBcIiBzdHJva2Utd2lkdGg9XCIyXCIgc3Ryb2tlLWRhc2hhcnJheT1cIjMxLjQgMzEuNFwiLz5cbiAgICAgICAgICAgICAgPC9zdmc+XG4gICAgICAgICAgICAgIHt7IHJlY3Jhd2xpbmcgPyAn6YeH6ZuG5LitLi4uJyA6ICfph43mlrDph4fpm4YnIH19XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICAgIDxhIFxuICAgICAgICAgICAgICB2LWlmPVwidmlld2luZ0FydGljbGU/LnVybCAmJiAhdmlld2luZ0FydGljbGU/LnVybC5zdGFydHNXaXRoKCdtYW51YWwtJylcIlxuICAgICAgICAgICAgICA6aHJlZj1cInZpZXdpbmdBcnRpY2xlLnVybFwiIFxuICAgICAgICAgICAgICB0YXJnZXQ9XCJfYmxhbmtcIiBcbiAgICAgICAgICAgICAgY2xhc3M9XCJleHRlcm5hbC1saW5rLWJ0blwiXG4gICAgICAgICAgICAgIEBjbGljay5zdG9wXG4gICAgICAgICAgICA+XG4gICAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XG4gICAgICAgICAgICAgICAgPHBhdGggZD1cIk0xOCAxM3Y2YTIgMiAwIDAgMS0yIDJINWEyIDIgMCAwIDEtMi0yVjhhMiAyIDAgMCAxIDItMmg2XCIvPlxuICAgICAgICAgICAgICAgIDxwb2x5bGluZSBwb2ludHM9XCIxNSAzIDIxIDMgMjEgOVwiLz5cbiAgICAgICAgICAgICAgICA8bGluZSB4MT1cIjEwXCIgeTE9XCIxNFwiIHgyPVwiMjFcIiB5Mj1cIjNcIi8+XG4gICAgICAgICAgICAgIDwvc3ZnPlxuICAgICAgICAgICAgICDmn6XnnIvljp/lp4vpk77mjqVcbiAgICAgICAgICAgIDwvYT5cbiAgICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cImNsb3NlRWRpdE1vZGFsXCI+XG4gICAgICAgICAgICA8c3ZnIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiPlxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjE4XCIgeTE9XCI2XCIgeDI9XCI2XCIgeTI9XCIxOFwiLz5cbiAgICAgICAgICAgICAgPGxpbmUgeDE9XCI2XCIgeTE9XCI2XCIgeDI9XCIxOFwiIHkyPVwiMThcIi8+XG4gICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1ib2R5XCI+XG4gICAgICAgICAgPGRpdiB2LWlmPVwibG9hZGluZ0FydGljbGVDb250ZW50XCIgY2xhc3M9XCJsb2FkaW5nLWNvbnRlbnRcIj7liqDovb3kuK0uLi48L2Rpdj5cbiAgICAgICAgICA8ZGl2IHYtZWxzZT5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJmb3JtLWdyb3VwXCI+XG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cImZvcm0tbGFiZWxcIj7moIfpopggPHNwYW4gY2xhc3M9XCJvcHRpb25hbFwiPu+8iOWPr+mAie+8jOWPr+iHquWKqOeUn+aIkO+8iTwvc3Bhbj48L2xhYmVsPlxuICAgICAgICAgICAgICA8ZGl2IGNsYXNzPVwidGl0bGUtaW5wdXQtZ3JvdXBcIj5cbiAgICAgICAgICAgICAgICA8aW5wdXQgXG4gICAgICAgICAgICAgICAgICB2LW1vZGVsPVwiZWRpdGluZ0FydGljbGUudGl0bGVcIiBcbiAgICAgICAgICAgICAgICAgIHR5cGU9XCJ0ZXh0XCIgXG4gICAgICAgICAgICAgICAgICBjbGFzcz1cImZvcm0taW5wdXRcIiBcbiAgICAgICAgICAgICAgICAgIHBsYWNlaG9sZGVyPVwi6L6T5YWl5qCH6aKY5oiW54K55Ye75LiL5pa55oyJ6ZKu6Ieq5Yqo55Sf5oiQXCJcbiAgICAgICAgICAgICAgICAvPlxuICAgICAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgICAgICBjbGFzcz1cImdlbmVyYXRlLXRpdGxlLWJ0blwiIFxuICAgICAgICAgICAgICAgICAgQGNsaWNrPVwiZ2VuZXJhdGVUaXRsZUZvckVkaXRcIlxuICAgICAgICAgICAgICAgICAgOmRpc2FibGVkPVwiIWVkaXRpbmdBcnRpY2xlLmNvbnRlbnQgfHwgZ2VuZXJhdGluZ1RpdGxlXCJcbiAgICAgICAgICAgICAgICA+XG4gICAgICAgICAgICAgICAgICB7eyBnZW5lcmF0aW5nVGl0bGUgPyAn55Sf5oiQ5LitLi4uJyA6ICdBSeeUn+aIkOagh+mimCcgfX1cbiAgICAgICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1ncm91cFwiPlxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJmb3JtLWxhYmVsXCI+5paH56ug5YaF5a65IDxzcGFuIGNsYXNzPVwicmVxdWlyZWRcIj4qPC9zcGFuPjwvbGFiZWw+XG4gICAgICAgICAgICAgIDx0ZXh0YXJlYSBcbiAgICAgICAgICAgICAgICB2LW1vZGVsPVwiZWRpdGluZ0FydGljbGUuY29udGVudFwiIFxuICAgICAgICAgICAgICAgIGNsYXNzPVwiZm9ybS10ZXh0YXJlYVwiIFxuICAgICAgICAgICAgICAgIHJvd3M9XCIxNVwiXG4gICAgICAgICAgICAgICAgcGxhY2Vob2xkZXI9XCLor7fovpPlhaXmlofnq6DlhoXlrrkuLi5cIlxuICAgICAgICAgICAgICA+PC90ZXh0YXJlYT5cbiAgICAgICAgICAgICAgPGRpdiBjbGFzcz1cImNoYXItY291bnRcIj57eyBlZGl0aW5nQXJ0aWNsZS5jb250ZW50Lmxlbmd0aCB9fSDlrZc8L2Rpdj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cImZvcm0tYWN0aW9uc1wiPlxuICAgICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuIGJ0bi1zZWNvbmRhcnlcIiBAY2xpY2s9XCJjbG9zZUVkaXRNb2RhbFwiPuWFs+mXrTwvYnV0dG9uPlxuICAgICAgICAgICAgICA8c3BhbiB2LWlmPVwic2F2ZVN1Y2Nlc3NcIiBjbGFzcz1cInNhdmUtc3VjY2Vzcy10aXBcIj7lt7Lkv53lrZg8L3NwYW4+XG4gICAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgICAgY2xhc3M9XCJidG4gYnRuLXByaW1hcnlcIiBcbiAgICAgICAgICAgICAgICBAY2xpY2s9XCJzYXZlQXJ0aWNsZVwiXG4gICAgICAgICAgICAgICAgOmRpc2FibGVkPVwiIWVkaXRpbmdBcnRpY2xlLmNvbnRlbnQgfHwgc2F2aW5nIHx8IGFycmFuZ2luZ1R5cGVcIlxuICAgICAgICAgICAgICA+XG4gICAgICAgICAgICAgICAge3sgc2F2aW5nID8gJ+S/neWtmOS4rS4uLicgOiAn5L+d5a2YJyB9fVxuICAgICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cImFycmFuZ2UtYWN0aW9uc1wiIHYtaWY9XCJlZGl0aW5nQXJ0aWNsZS5pZFwiPlxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cImFycmFuZ2UtbGFiZWxcIj7lronmjpLliLbkvZzvvJo8L3NwYW4+XG4gICAgICAgICAgICAgIDxyb3V0ZXItbGlua1xuICAgICAgICAgICAgICAgIHYtaWY9XCJpc0FycmFuZ2VkVmlkZW9cIlxuICAgICAgICAgICAgICAgIDp0bz1cImAvem9lLyR7ZWRpdGluZ0FydGljbGUuaWR9YFwiXG4gICAgICAgICAgICAgICAgY2xhc3M9XCJidG4gYnRuLWFycmFuZ2UgYXJyYW5nZWRcIlxuICAgICAgICAgICAgICA+XG4gICAgICAgICAgICAgICAg5bey5a6J5o6S6KeG6aKR77yI54K55Ye75p+l55yL77yJXG4gICAgICAgICAgICAgIDwvcm91dGVyLWxpbms+XG4gICAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgICAgdi1lbHNlXG4gICAgICAgICAgICAgICAgY2xhc3M9XCJidG4gYnRuLWFycmFuZ2VcIlxuICAgICAgICAgICAgICAgIEBjbGljaz1cImFycmFuZ2VUeXBlKCd2aWRlbycpXCJcbiAgICAgICAgICAgICAgICA6ZGlzYWJsZWQ9XCIhZWRpdGluZ0FydGljbGUuY29udGVudCB8fCBzYXZpbmcgfHwgYXJyYW5naW5nVHlwZVwiXG4gICAgICAgICAgICAgID5cbiAgICAgICAgICAgICAgICB7eyBhcnJhbmdpbmdUeXBlID09PSAndmlkZW8nID8gJ+WuieaOkuS4rS4uLicgOiAn5a6J5o6S6KeG6aKRJyB9fVxuICAgICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICAgICAgICBjbGFzcz1cImJ0biBidG4tYXJyYW5nZVwiXG4gICAgICAgICAgICAgICAgOmNsYXNzPVwieyAnYXJyYW5nZWQnOiBpc0FycmFuZ2VkSW1hZ2UgfVwiXG4gICAgICAgICAgICAgICAgQGNsaWNrPVwiYXJyYW5nZVR5cGUoJ2ltYWdlJylcIlxuICAgICAgICAgICAgICAgIDpkaXNhYmxlZD1cImlzQXJyYW5nZWRJbWFnZSB8fCAhZWRpdGluZ0FydGljbGUuY29udGVudCB8fCBzYXZpbmcgfHwgYXJyYW5naW5nVHlwZVwiXG4gICAgICAgICAgICAgID5cbiAgICAgICAgICAgICAgICB7eyBhcnJhbmdpbmdUeXBlID09PSAnaW1hZ2UnID8gJ+WuieaOkuS4rS4uLicgOiAoaXNBcnJhbmdlZEltYWdlID8gJ+W3suWuieaOkuWbvuaWhycgOiAn5a6J5o6S5Zu+5paHJykgfX1cbiAgICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g5paw5bu65paH56ug5qih5oCB5qGGIC0tPlxuICAgIDxkaXYgdi1pZj1cInNob3dDcmVhdGVNb2RhbFwiIGNsYXNzPVwibW9kYWwtb3ZlcmxheVwiPlxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnQgY3JlYXRlLWFydGljbGUtbW9kYWxcIj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWhlYWRlclwiPlxuICAgICAgICAgIDxoMj7mlrDlu7rmlofnq6A8L2gyPlxuICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cImNsb3NlQ3JlYXRlTW9kYWxcIj5cbiAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XG4gICAgICAgICAgICAgIDxsaW5lIHgxPVwiMThcIiB5MT1cIjZcIiB4Mj1cIjZcIiB5Mj1cIjE4XCIvPlxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjZcIiB5MT1cIjZcIiB4Mj1cIjE4XCIgeTI9XCIxOFwiLz5cbiAgICAgICAgICAgIDwvc3ZnPlxuICAgICAgICAgIDwvYnV0dG9uPlxuICAgICAgICA8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWJvZHlcIj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1ncm91cFwiPlxuICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiZm9ybS1sYWJlbFwiPuagh+mimCA8c3BhbiBjbGFzcz1cIm9wdGlvbmFsXCI+77yI5Y+v6YCJ77yM5Y+v6Ieq5Yqo55Sf5oiQ77yJPC9zcGFuPjwvbGFiZWw+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwidGl0bGUtaW5wdXQtZ3JvdXBcIj5cbiAgICAgICAgICAgICAgPGlucHV0IFxuICAgICAgICAgICAgICAgIHYtbW9kZWw9XCJuZXdBcnRpY2xlLnRpdGxlXCIgXG4gICAgICAgICAgICAgICAgdHlwZT1cInRleHRcIiBcbiAgICAgICAgICAgICAgICBjbGFzcz1cImZvcm0taW5wdXRcIiBcbiAgICAgICAgICAgICAgICBwbGFjZWhvbGRlcj1cIui+k+WFpeagh+mimOaIlueCueWHu+S4i+aWueaMiemSruiHquWKqOeUn+aIkFwiXG4gICAgICAgICAgICAgIC8+XG4gICAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgICAgY2xhc3M9XCJnZW5lcmF0ZS10aXRsZS1idG5cIiBcbiAgICAgICAgICAgICAgICBAY2xpY2s9XCJnZW5lcmF0ZVRpdGxlXCJcbiAgICAgICAgICAgICAgICA6ZGlzYWJsZWQ9XCIhbmV3QXJ0aWNsZS5jb250ZW50IHx8IGdlbmVyYXRpbmdUaXRsZVwiXG4gICAgICAgICAgICAgID5cbiAgICAgICAgICAgICAgICB7eyBnZW5lcmF0aW5nVGl0bGUgPyAn55Sf5oiQ5LitLi4uJyA6ICdBSeeUn+aIkOagh+mimCcgfX1cbiAgICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1ncm91cFwiPlxuICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiZm9ybS1sYWJlbFwiPuaWh+eroOWGheWuuSA8c3BhbiBjbGFzcz1cInJlcXVpcmVkXCI+Kjwvc3Bhbj48L2xhYmVsPlxuICAgICAgICAgICAgPHRleHRhcmVhIFxuICAgICAgICAgICAgICB2LW1vZGVsPVwibmV3QXJ0aWNsZS5jb250ZW50XCIgXG4gICAgICAgICAgICAgIGNsYXNzPVwiZm9ybS10ZXh0YXJlYVwiIFxuICAgICAgICAgICAgICByb3dzPVwiMTVcIlxuICAgICAgICAgICAgICBwbGFjZWhvbGRlcj1cIuivt+i+k+WFpeaWh+eroOWGheWuuS4uLlwiXG4gICAgICAgICAgICA+PC90ZXh0YXJlYT5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJjaGFyLWNvdW50XCI+e3sgbmV3QXJ0aWNsZS5jb250ZW50Lmxlbmd0aCB9fSDlrZc8L2Rpdj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1ncm91cFwiPlxuICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiZm9ybS1sYWJlbFwiPuWItuS9nOexu+WeizwvbGFiZWw+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwiY2hlY2tib3gtZ3JvdXBcIj5cbiAgICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiY2hlY2tib3gtbGFiZWxcIj5cbiAgICAgICAgICAgICAgICA8aW5wdXQgdHlwZT1cImNoZWNrYm94XCIgdi1tb2RlbD1cIm5ld0FydGljbGUuY29udGVudF90eXBlX2ltYWdlXCIgQGNoYW5nZT1cIm9uQ29udGVudFR5cGVDaGFuZ2VcIiAvPlxuICAgICAgICAgICAgICAgIDxzcGFuPuWbvuaWhzwvc3Bhbj5cbiAgICAgICAgICAgICAgPC9sYWJlbD5cbiAgICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiY2hlY2tib3gtbGFiZWxcIj5cbiAgICAgICAgICAgICAgICA8aW5wdXQgdHlwZT1cImNoZWNrYm94XCIgdi1tb2RlbD1cIm5ld0FydGljbGUuY29udGVudF90eXBlX3ZpZGVvXCIgQGNoYW5nZT1cIm9uQ29udGVudFR5cGVDaGFuZ2VcIiAvPlxuICAgICAgICAgICAgICAgIDxzcGFuPuinhumikTwvc3Bhbj5cbiAgICAgICAgICAgICAgPC9sYWJlbD5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJmb3JtLWdyb3VwXCIgdi1pZj1cInNob3dBY2NvdW50VGFyZ2V0XCI+XG4gICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJmb3JtLWxhYmVsXCI+55uu5qCH6LSm5Y+3PC9sYWJlbD5cbiAgICAgICAgICAgIDxkaXYgY2xhc3M9XCJyYWRpby1ncm91cFwiPlxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJyYWRpby1sYWJlbFwiPlxuICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwicmFkaW9cIiB2LW1vZGVsPVwibmV3QXJ0aWNsZS5hY2NvdW50X3RhcmdldFwiIHZhbHVlPVwiQUlcIiAvPlxuICAgICAgICAgICAgICAgIDxzcGFuPkFJPC9zcGFuPlxuICAgICAgICAgICAgICA8L2xhYmVsPlxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJyYWRpby1sYWJlbFwiPlxuICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwicmFkaW9cIiB2LW1vZGVsPVwibmV3QXJ0aWNsZS5hY2NvdW50X3RhcmdldFwiIHZhbHVlPVwi57uP5rWO5a2mXCIgLz5cbiAgICAgICAgICAgICAgICA8c3Bhbj7nu4/mtY7lraY8L3NwYW4+XG4gICAgICAgICAgICAgIDwvbGFiZWw+XG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cInJhZGlvLWxhYmVsXCI+XG4gICAgICAgICAgICAgICAgPGlucHV0IHR5cGU9XCJyYWRpb1wiIHYtbW9kZWw9XCJuZXdBcnRpY2xlLmFjY291bnRfdGFyZ2V0XCIgdmFsdWU9XCLlv4PnkIblraZcIiAvPlxuICAgICAgICAgICAgICAgIDxzcGFuPuW/g+eQhuWtpjwvc3Bhbj5cbiAgICAgICAgICAgICAgPC9sYWJlbD5cbiAgICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJmb3JtLWFjdGlvbnNcIj5cbiAgICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJidG4gYnRuLXNlY29uZGFyeVwiIEBjbGljaz1cImNsb3NlQ3JlYXRlTW9kYWxcIj7lj5bmtog8L2J1dHRvbj5cbiAgICAgICAgICAgIDxidXR0b24gXG4gICAgICAgICAgICAgIGNsYXNzPVwiYnRuIGJ0bi1wcmltYXJ5XCIgXG4gICAgICAgICAgICAgIEBjbGljaz1cImNyZWF0ZUFydGljbGVcIlxuICAgICAgICAgICAgICA6ZGlzYWJsZWQ9XCIhbmV3QXJ0aWNsZS5jb250ZW50IHx8IGNyZWF0aW5nXCJcbiAgICAgICAgICAgID5cbiAgICAgICAgICAgICAge3sgY3JlYXRpbmcgPyAn5Yib5bu65LitLi4uJyA6ICfliJvlu7rmlofnq6DvvIjpu5jorqTlt7LlronmjpLvvIknIH19XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0g6YCJ5Lit6K6+572u5qih5oCB5qGGIC0tPlxuICAgIDxkaXYgdi1pZj1cInNob3dTZWxlY3RNb2RhbFwiIGNsYXNzPVwibW9kYWwtb3ZlcmxheVwiPlxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnQgY3JlYXRlLWFydGljbGUtbW9kYWxcIj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWhlYWRlclwiPlxuICAgICAgICAgIDxoMj7orr7nva7liLbkvZznsbvlnovlkoznm67moIfotKblj7c8L2gyPlxuICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cImNsb3NlU2VsZWN0TW9kYWxcIj5cbiAgICAgICAgICAgIDxzdmcgdmlld0JveD1cIjAgMCAyNCAyNFwiIGZpbGw9XCJub25lXCIgc3Ryb2tlPVwiY3VycmVudENvbG9yXCI+XG4gICAgICAgICAgICAgIDxsaW5lIHgxPVwiMThcIiB5MT1cIjZcIiB4Mj1cIjZcIiB5Mj1cIjE4XCIvPlxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjZcIiB5MT1cIjZcIiB4Mj1cIjE4XCIgeTI9XCIxOFwiLz5cbiAgICAgICAgICAgIDwvc3ZnPlxuICAgICAgICAgIDwvYnV0dG9uPlxuICAgICAgICA8L2Rpdj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWJvZHlcIj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1ncm91cFwiPlxuICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiZm9ybS1sYWJlbFwiPuWItuS9nOexu+WeizwvbGFiZWw+XG4gICAgICAgICAgICA8ZGl2IGNsYXNzPVwiY2hlY2tib3gtZ3JvdXBcIj5cbiAgICAgICAgICAgICAgPGxhYmVsIGNsYXNzPVwiY2hlY2tib3gtbGFiZWxcIj5cbiAgICAgICAgICAgICAgICA8aW5wdXQgdHlwZT1cImNoZWNrYm94XCIgdi1tb2RlbD1cInNlbGVjdFNldHRpbmdzLmNvbnRlbnRfdHlwZV9pbWFnZVwiIEBjaGFuZ2U9XCJvblNlbGVjdENvbnRlbnRUeXBlQ2hhbmdlXCIgLz5cbiAgICAgICAgICAgICAgICA8c3Bhbj7lm77mloc8L3NwYW4+XG4gICAgICAgICAgICAgIDwvbGFiZWw+XG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cImNoZWNrYm94LWxhYmVsXCI+XG4gICAgICAgICAgICAgICAgPGlucHV0IHR5cGU9XCJjaGVja2JveFwiIHYtbW9kZWw9XCJzZWxlY3RTZXR0aW5ncy5jb250ZW50X3R5cGVfdmlkZW9cIiBAY2hhbmdlPVwib25TZWxlY3RDb250ZW50VHlwZUNoYW5nZVwiIC8+XG4gICAgICAgICAgICAgICAgPHNwYW4+6KeG6aKRPC9zcGFuPlxuICAgICAgICAgICAgICA8L2xhYmVsPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cImZvcm0tZ3JvdXBcIiB2LWlmPVwic2hvd1NlbGVjdEFjY291bnRUYXJnZXRcIj5cbiAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cImZvcm0tbGFiZWxcIj7nm67moIfotKblj7c8L2xhYmVsPlxuICAgICAgICAgICAgPGRpdiBjbGFzcz1cInJhZGlvLWdyb3VwXCI+XG4gICAgICAgICAgICAgIDxsYWJlbCBjbGFzcz1cInJhZGlvLWxhYmVsXCI+XG4gICAgICAgICAgICAgICAgPGlucHV0IHR5cGU9XCJyYWRpb1wiIHYtbW9kZWw9XCJzZWxlY3RTZXR0aW5ncy5hY2NvdW50X3RhcmdldFwiIHZhbHVlPVwiQUlcIiAvPlxuICAgICAgICAgICAgICAgIDxzcGFuPkFJPC9zcGFuPlxuICAgICAgICAgICAgICA8L2xhYmVsPlxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJyYWRpby1sYWJlbFwiPlxuICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwicmFkaW9cIiB2LW1vZGVsPVwic2VsZWN0U2V0dGluZ3MuYWNjb3VudF90YXJnZXRcIiB2YWx1ZT1cIue7j+a1juWtplwiIC8+XG4gICAgICAgICAgICAgICAgPHNwYW4+57uP5rWO5a2mPC9zcGFuPlxuICAgICAgICAgICAgICA8L2xhYmVsPlxuICAgICAgICAgICAgICA8bGFiZWwgY2xhc3M9XCJyYWRpby1sYWJlbFwiPlxuICAgICAgICAgICAgICAgIDxpbnB1dCB0eXBlPVwicmFkaW9cIiB2LW1vZGVsPVwic2VsZWN0U2V0dGluZ3MuYWNjb3VudF90YXJnZXRcIiB2YWx1ZT1cIuW/g+eQhuWtplwiIC8+XG4gICAgICAgICAgICAgICAgPHNwYW4+5b+D55CG5a2mPC9zcGFuPlxuICAgICAgICAgICAgICA8L2xhYmVsPlxuICAgICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cImZvcm0tYWN0aW9uc1wiPlxuICAgICAgICAgICAgPGJ1dHRvbiBjbGFzcz1cImJ0biBidG4tc2Vjb25kYXJ5XCIgQGNsaWNrPVwiY2xvc2VTZWxlY3RNb2RhbFwiPuWPlua2iDwvYnV0dG9uPlxuICAgICAgICAgICAgPGJ1dHRvbiBcbiAgICAgICAgICAgICAgY2xhc3M9XCJidG4gYnRuLXByaW1hcnlcIiBcbiAgICAgICAgICAgICAgQGNsaWNrPVwiY29uZmlybVNlbGVjdFwiXG4gICAgICAgICAgICAgIDpkaXNhYmxlZD1cIiFoYXNTZWxlY3RDb250ZW50VHlwZSB8fCBzZWxlY3RpbmdcIlxuICAgICAgICAgICAgPlxuICAgICAgICAgICAgICB7eyBzZWxlY3RpbmcgPyAn6K6+572u5LitLi4uJyA6ICfnoa7orqTpgInkuK0nIH19XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0gQUnov4fmu6Tmj5DnpLror43nvJbovpHlvLnnqpcgLS0+XG4gICAgPGRpdiB2LWlmPVwic2hvd1Byb21wdEVkaXRNb2RhbFwiIGNsYXNzPVwibW9kYWwtb3ZlcmxheVwiPlxuICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWNvbnRlbnQgcHJvbXB0LWVkaXQtbW9kYWxcIj5cbiAgICAgICAgPGRpdiBjbGFzcz1cIm1vZGFsLWhlYWRlclwiPlxuICAgICAgICAgIDxoMj7ov4fmu6Tmj5DnpLror40gLSB7eyBmaWx0ZXJUYWcgfX08L2gyPlxuICAgICAgICAgIDxidXR0b24gY2xhc3M9XCJtb2RhbC1jbG9zZVwiIEBjbGljaz1cInNob3dQcm9tcHRFZGl0TW9kYWwgPSBmYWxzZVwiPlxuICAgICAgICAgICAgPHN2ZyB2aWV3Qm94PVwiMCAwIDI0IDI0XCIgZmlsbD1cIm5vbmVcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIj5cbiAgICAgICAgICAgICAgPGxpbmUgeDE9XCIxOFwiIHkxPVwiNlwiIHgyPVwiNlwiIHkyPVwiMThcIi8+XG4gICAgICAgICAgICAgIDxsaW5lIHgxPVwiNlwiIHkxPVwiNlwiIHgyPVwiMThcIiB5Mj1cIjE4XCIvPlxuICAgICAgICAgICAgPC9zdmc+XG4gICAgICAgICAgPC9idXR0b24+XG4gICAgICAgIDwvZGl2PlxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtYm9keVwiPlxuICAgICAgICAgIDxkaXYgY2xhc3M9XCJwcm9tcHQtZWRpdC1oaW50XCI+XG4gICAgICAgICAgICDku6XkuIvmj5DnpLror43nlKjkuo7mjIflr7xBSeWIpOaWreWTquS6m+aWh+eroOW6lOivpeiiq+WIoOmZpOOAguS9oOWPr+S7peS/ruaUueWQjueCueWHu+S/neWtmO+8jOaIluebtOaOpeW8gOWni+i/h+a7pOOAglxuICAgICAgICAgIDwvZGl2PlxuICAgICAgICAgIDx0ZXh0YXJlYVxuICAgICAgICAgICAgdi1tb2RlbD1cImVkaXRpbmdQcm9tcHRcIlxuICAgICAgICAgICAgY2xhc3M9XCJwcm9tcHQtdGV4dGFyZWFcIlxuICAgICAgICAgICAgcm93cz1cIjE2XCJcbiAgICAgICAgICAgIHBsYWNlaG9sZGVyPVwi6K+36L6T5YWl6L+H5ruk5o+Q56S66K+NLi4uXCJcbiAgICAgICAgICA+PC90ZXh0YXJlYT5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1hY3Rpb25zIHByb21wdC1hY3Rpb25zXCI+XG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuIGJ0bi1zZWNvbmRhcnlcIiBAY2xpY2s9XCJzaG93UHJvbXB0RWRpdE1vZGFsID0gZmFsc2VcIj7lj5bmtog8L2J1dHRvbj5cbiAgICAgICAgICAgIDxidXR0b25cbiAgICAgICAgICAgICAgY2xhc3M9XCJidG4gYnRuLW91dGxpbmUtcHJpbWFyeVwiXG4gICAgICAgICAgICAgIEBjbGljaz1cInNhdmVQcm9tcHRcIlxuICAgICAgICAgICAgICA6ZGlzYWJsZWQ9XCJzYXZpbmdQcm9tcHRcIlxuICAgICAgICAgICAgPlxuICAgICAgICAgICAgICB7eyBzYXZpbmdQcm9tcHQgPyAn5L+d5a2Y5LitLi4uJyA6ICfkv53lrZjmj5DnpLror40nIH19XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICAgIDxidXR0b25cbiAgICAgICAgICAgICAgY2xhc3M9XCJidG4gYnRuLXByaW1hcnlcIlxuICAgICAgICAgICAgICBAY2xpY2s9XCJydW5BSUZpbHRlclwiXG4gICAgICAgICAgICAgIDpkaXNhYmxlZD1cImFpRmlsdGVyaW5nIHx8ICFlZGl0aW5nUHJvbXB0LnRyaW0oKVwiXG4gICAgICAgICAgICA+XG4gICAgICAgICAgICAgIDxzdmcgdi1pZj1cImFpRmlsdGVyaW5nXCIgY2xhc3M9XCJzcGlubmluZ1wiIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiIHN0cm9rZS13aWR0aD1cIjJcIiBzdHlsZT1cIndpZHRoOjE0cHg7aGVpZ2h0OjE0cHg7bWFyZ2luLXJpZ2h0OjRweDtcIj5cbiAgICAgICAgICAgICAgICA8Y2lyY2xlIGN4PVwiMTJcIiBjeT1cIjEyXCIgcj1cIjEwXCIgc3Ryb2tlLWRhc2hhcnJheT1cIjMxLjQgMzEuNFwiLz5cbiAgICAgICAgICAgICAgPC9zdmc+XG4gICAgICAgICAgICAgIHt7IGFpRmlsdGVyaW5nID8gJ0FJ5YiG5p6Q5LitLi4uJyA6ICflvIDlp4vov4fmu6QnIH19XG4gICAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgPC9kaXY+XG4gICAgICA8L2Rpdj5cbiAgICA8L2Rpdj5cblxuICAgIDwhLS0gQUnov4fmu6Tnoa7orqTlvLnnqpcgLS0+XG4gICAgPGRpdiB2LWlmPVwic2hvd0FJRmlsdGVyTW9kYWxcIiBjbGFzcz1cIm1vZGFsLW92ZXJsYXlcIj5cbiAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1jb250ZW50IGFpLWZpbHRlci1tb2RhbFwiPlxuICAgICAgICA8ZGl2IGNsYXNzPVwibW9kYWwtaGVhZGVyXCI+XG4gICAgICAgICAgPGgyPkFJ6L+H5ruk57uT5p6cIC0ge3sgZmlsdGVyVGFnIH19PC9oMj5cbiAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwibW9kYWwtY2xvc2VcIiBAY2xpY2s9XCJzaG93QUlGaWx0ZXJNb2RhbCA9IGZhbHNlXCI+XG4gICAgICAgICAgICA8c3ZnIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBmaWxsPVwibm9uZVwiIHN0cm9rZT1cImN1cnJlbnRDb2xvclwiPlxuICAgICAgICAgICAgICA8bGluZSB4MT1cIjE4XCIgeTE9XCI2XCIgeDI9XCI2XCIgeTI9XCIxOFwiLz5cbiAgICAgICAgICAgICAgPGxpbmUgeDE9XCI2XCIgeTE9XCI2XCIgeDI9XCIxOFwiIHkyPVwiMThcIi8+XG4gICAgICAgICAgICA8L3N2Zz5cbiAgICAgICAgICA8L2J1dHRvbj5cbiAgICAgICAgPC9kaXY+XG4gICAgICAgIDxkaXYgY2xhc3M9XCJtb2RhbC1ib2R5XCI+XG4gICAgICAgICAgPGRpdiBjbGFzcz1cImFpLWZpbHRlci1zdW1tYXJ5XCI+XG4gICAgICAgICAgICA8cD7lhbHmo4Dmn6UgPHN0cm9uZz57eyBhaUZpbHRlclRvdGFsQ2hlY2tlZCB9fTwvc3Ryb25nPiDnr4flvoXlrqHmoLjmlofnq6DvvIxBSeW7uuiuruWIoOmZpOS7peS4iyA8c3Ryb25nPnt7IGFpRmlsdGVyQXJ0aWNsZXMubGVuZ3RoIH19PC9zdHJvbmc+IOevh++8mjwvcD5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiYWktZmlsdGVyLWxpc3RcIj5cbiAgICAgICAgICAgIDxkaXZcbiAgICAgICAgICAgICAgdi1mb3I9XCIoYXJ0aWNsZSwgaW5kZXgpIGluIGFpRmlsdGVyQXJ0aWNsZXNcIlxuICAgICAgICAgICAgICA6a2V5PVwiYXJ0aWNsZS5pZFwiXG4gICAgICAgICAgICAgIGNsYXNzPVwiYWktZmlsdGVyLWl0ZW1cIlxuICAgICAgICAgICAgPlxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cImFpLWZpbHRlci1pbmRleFwiPnt7IGluZGV4ICsgMSB9fTwvc3Bhbj5cbiAgICAgICAgICAgICAgPHNwYW4gY2xhc3M9XCJhaS1maWx0ZXItdGl0bGVcIj57eyBhcnRpY2xlLnRpdGxlIH19PC9zcGFuPlxuICAgICAgICAgICAgICA8c3BhbiBjbGFzcz1cImFpLWZpbHRlci1pZFwiPklEOnt7IGFydGljbGUuaWQgfX08L3NwYW4+XG4gICAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8L2Rpdj5cbiAgICAgICAgICA8ZGl2IGNsYXNzPVwiZm9ybS1hY3Rpb25zXCI+XG4gICAgICAgICAgICA8YnV0dG9uIGNsYXNzPVwiYnRuIGJ0bi1zZWNvbmRhcnlcIiBAY2xpY2s9XCJzaG93QUlGaWx0ZXJNb2RhbCA9IGZhbHNlXCI+5Y+W5raIPC9idXR0b24+XG4gICAgICAgICAgICA8YnV0dG9uXG4gICAgICAgICAgICAgIGNsYXNzPVwiYnRuIGJ0bi1kYW5nZXJcIlxuICAgICAgICAgICAgICBAY2xpY2s9XCJjb25maXJtQUlGaWx0ZXJEZWxldGVcIlxuICAgICAgICAgICAgICA6ZGlzYWJsZWQ9XCJhaUZpbHRlckRlbGV0aW5nXCJcbiAgICAgICAgICAgID5cbiAgICAgICAgICAgICAge3sgYWlGaWx0ZXJEZWxldGluZyA/ICfliKDpmaTkuK0uLi4nIDogYOehruiupOWIoOmZpCAoJHthaUZpbHRlckFydGljbGVzLmxlbmd0aH0pYCB9fVxuICAgICAgICAgICAgPC9idXR0b24+XG4gICAgICAgICAgPC9kaXY+XG4gICAgICAgIDwvZGl2PlxuICAgICAgPC9kaXY+XG4gICAgPC9kaXY+XG5cbiAgPC9kaXY+XG48L3RlbXBsYXRlPlxuXG48c2NyaXB0IHNldHVwPlxuaW1wb3J0IHsgcmVmLCBjb21wdXRlZCwgb25Nb3VudGVkLCBvblVubW91bnRlZCwgd2F0Y2ggfSBmcm9tICd2dWUnXG5pbXBvcnQgeyB1c2VSb3V0ZSwgdXNlUm91dGVyIH0gZnJvbSAndnVlLXJvdXRlcidcbmltcG9ydCB7IEFQSV9CQVNFX1VSTCB9IGZyb20gJy4uL3V0aWxzL2FwaUNvbmZpZydcbmltcG9ydCBBcHBIZWFkZXIgZnJvbSAnLi4vY29tcG9uZW50cy9BcHBIZWFkZXIudnVlJ1xuaW1wb3J0IEFsZXJ0TW9kYWwgZnJvbSAnLi4vY29tcG9uZW50cy9BbGVydE1vZGFsLnZ1ZSdcblxuY29uc3Qgcm91dGUgPSB1c2VSb3V0ZSgpXG5jb25zdCByb3V0ZXIgPSB1c2VSb3V0ZXIoKVxuY29uc3QgYXJ0aWNsZXMgPSByZWYoW10pXG5jb25zdCBsb2FkaW5nID0gcmVmKHRydWUpXG5jb25zdCBmaWx0ZXJTZWxlY3RlZCA9IHJlZihmYWxzZSkgIC8vIOm7mOiupOaYvuekuuW+heWuoeaguO+8iOacqumAieS4re+8iVxuY29uc3QgZmlsdGVyUmVqZWN0ZWQgPSByZWYobnVsbClcbmNvbnN0IHN0YXR1c0ZpbHRlciA9IHJlZigncGVuZGluZycpICAvLyDnirbmgIHnrZvpgInvvJpwZW5kaW5nLCBzZWxlY3RlZCwgZGVsZXRlZFxuY29uc3QgZmlsdGVyUGxhdGZvcm0gPSByZWYobnVsbCkgIC8vIOW5s+WPsOetm+mAie+8mum7mOiupOWFqOmDqOa4oOmBk1xuY29uc3QgZmlsdGVyVGFnID0gcmVmKCdBSScpICAvLyDmoIfnrb7nrZvpgInvvJrpu5jorqQgQUlcbmNvbnN0IHBhZ2luYXRpb24gPSByZWYobnVsbClcbmNvbnN0IGN1cnJlbnRQYWdlID0gcmVmKDEpXG5jb25zdCBzb3J0QnkgPSByZWYoJ3B1Ymxpc2hlZF9hdCcpICAvLyDpu5jorqTmjInml7bpl7TmjpLluo9cbmNvbnN0IHN0YXRpc3RpY3MgPSByZWYobnVsbClcbmNvbnN0IHNlYXJjaEtleXdvcmQgPSByZWYoJycpICAvLyDmkJzntKLlhbPplK7or41cbmNvbnN0IGp1bXBQYWdlID0gcmVmKG51bGwpICAvLyDot7PovazpobXnoIHovpPlhaVcblxuLy8g5Y+R5biD6K6h5YiS6Z2i5p2/IChHRVQgL2FwaS96aGlodS92aWRlby1zY2hlZHVsZSlcbmNvbnN0IHNob3dTY2hlZHVsZSA9IHJlZihmYWxzZSlcbmNvbnN0IHNjaGVkdWxlTG9hZGluZyA9IHJlZihmYWxzZSlcbmNvbnN0IHNjaGVkdWxlSXRlbXMgPSByZWYoW10pXG5jb25zdCBzY2hlZHVsZVN1bW1hcnkgPSByZWYobnVsbClcblxuLy8gQ2hhcmxlcyDnirbmgIFcbmNvbnN0IGNoYXJsZXNTdGF0dXMgPSByZWYobnVsbClcbmNvbnN0IHN0YXR1c1Nob3duQWxlcnQgPSByZWYoZmFsc2UpXG5jb25zdCBzaG93U3RvcEFsZXJ0ID0gcmVmKGZhbHNlKVxuY29uc3Qgc3RvcEFsZXJ0TWVzc2FnZSA9IHJlZignJylcblxuLy8g5paw5bu65paH56ug55u45YWzXG5jb25zdCBzaG93Q3JlYXRlTW9kYWwgPSByZWYoZmFsc2UpXG5jb25zdCBuZXdBcnRpY2xlID0gcmVmKHtcbiAgdGl0bGU6ICcnLFxuICBjb250ZW50OiAnJyxcbiAgcGxhdGZvcm06ICdtYW51YWwnLFxuICBhY2NvdW50X3RhcmdldDogJ0FJJywgIC8vIEFJIC8g57uP5rWO5a2mIC8g5b+D55CG5a2mXG4gIGNvbnRlbnRfdHlwZV9pbWFnZTogdHJ1ZSwgIC8vIOaYr+WQpuWItuS9nOWbvuaWh1xuICBjb250ZW50X3R5cGVfdmlkZW86IGZhbHNlLCAgLy8g5piv5ZCm5Yi25L2c6KeG6aKRXG59KVxuXG4vLyDmmK/lkKbmmL7npLrnm67moIfotKblj7fpgInpobkgKOmAieS6huWbvuaWh+aIluinhumikeaJjeaYvuekuilcbmNvbnN0IHNob3dBY2NvdW50VGFyZ2V0ID0gY29tcHV0ZWQoKCkgPT4ge1xuICByZXR1cm4gbmV3QXJ0aWNsZS52YWx1ZS5jb250ZW50X3R5cGVfaW1hZ2UgfHwgbmV3QXJ0aWNsZS52YWx1ZS5jb250ZW50X3R5cGVfdmlkZW9cbn0pXG5cbmNvbnN0IG9uQ29udGVudFR5cGVDaGFuZ2UgPSAoKSA9PiB7XG4gIC8vIOWFgeiuuOWQjOaXtuWLvuWbvuaWh+WSjOinhumikVxufVxuY29uc3QgY3JlYXRpbmcgPSByZWYoZmFsc2UpXG5jb25zdCBnZW5lcmF0aW5nVGl0bGUgPSByZWYoZmFsc2UpXG5cbi8vIOmAieS4reiuvue9ruebuOWFs1xuY29uc3Qgc2hvd1NlbGVjdE1vZGFsID0gcmVmKGZhbHNlKVxuY29uc3Qgc2VsZWN0aW5nQXJ0aWNsZSA9IHJlZihudWxsKVxuY29uc3Qgc2VsZWN0aW5nID0gcmVmKGZhbHNlKVxuY29uc3Qgc2VsZWN0U2V0dGluZ3MgPSByZWYoe1xuICBhY2NvdW50X3RhcmdldDogJ0FJJywgIC8vIEFJIC8g57uP5rWO5a2mIC8g5b+D55CG5a2mXG4gIGNvbnRlbnRfdHlwZV9pbWFnZTogZmFsc2UsXG4gIGNvbnRlbnRfdHlwZV92aWRlbzogZmFsc2UsXG59KVxuXG5jb25zdCBzaG93U2VsZWN0QWNjb3VudFRhcmdldCA9IGNvbXB1dGVkKCgpID0+IHtcbiAgcmV0dXJuIHNlbGVjdFNldHRpbmdzLnZhbHVlLmNvbnRlbnRfdHlwZV9pbWFnZSB8fCBzZWxlY3RTZXR0aW5ncy52YWx1ZS5jb250ZW50X3R5cGVfdmlkZW9cbn0pXG5cbmNvbnN0IGhhc1NlbGVjdENvbnRlbnRUeXBlID0gY29tcHV0ZWQoKCkgPT4ge1xuICByZXR1cm4gc2VsZWN0U2V0dGluZ3MudmFsdWUuY29udGVudF90eXBlX2ltYWdlIHx8IHNlbGVjdFNldHRpbmdzLnZhbHVlLmNvbnRlbnRfdHlwZV92aWRlb1xufSlcblxuY29uc3Qgb25TZWxlY3RDb250ZW50VHlwZUNoYW5nZSA9ICgpID0+IHtcbiAgLy8g5YWB6K645ZCM5pe25Yu+5Zu+5paH5ZKM6KeG6aKRXG59XG5cbi8vIOaWh+eroOe8lui+keebuOWFs1xuY29uc3Qgc2hvd0NvbnRlbnRNb2RhbCA9IHJlZihmYWxzZSlcbmNvbnN0IHZpZXdpbmdBcnRpY2xlID0gcmVmKG51bGwpXG5jb25zdCBlZGl0aW5nQXJ0aWNsZSA9IHJlZih7XG4gIGlkOiAnJyxcbiAgdGl0bGU6ICcnLFxuICBjb250ZW50OiAnJyxcbiAgdXJsOiAnJ1xufSlcbmNvbnN0IGxvYWRpbmdBcnRpY2xlQ29udGVudCA9IHJlZihmYWxzZSlcbmNvbnN0IHNhdmluZyA9IHJlZihmYWxzZSlcbmNvbnN0IHNhdmVTdWNjZXNzID0gcmVmKGZhbHNlKVxuY29uc3Qgc2F2aW5nQW5kU2VsZWN0aW5nID0gcmVmKGZhbHNlKVxuY29uc3QgYXJyYW5naW5nVHlwZSA9IHJlZihudWxsKSAgLy8g5b2T5YmN5q2j5Zyo5a6J5o6S55qE57G75Z6LOiAndmlkZW8nIHwgJ2ltYWdlJyB8IG51bGxcbmNvbnN0IHJlY3Jhd2xpbmcgPSByZWYoZmFsc2UpXG5cbi8vIOWIpOaWreaYr+WQpuW3suWuieaOkuinhumike+8iOW/hemhu+WQjOaXtua7oei2syBpc19zZWxlY3RlZD10cnVlIOS4lCBjb250ZW50X3R5cGUg5YyF5ZCrIHZpZGVv77yJXG5jb25zdCBpc0FycmFuZ2VkVmlkZW8gPSBjb21wdXRlZCgoKSA9PiB7XG4gIHJldHVybiBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5pc19zZWxlY3RlZCAmJiAoZWRpdGluZ0FydGljbGUudmFsdWUuY29udGVudF90eXBlID09PSAndmlkZW8nIHx8IGVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnRfdHlwZSA9PT0gJ2JvdGgnKVxufSlcblxuLy8g5Yik5pat5piv5ZCm5bey5a6J5o6S5Zu+5paH77yI5b+F6aG75ZCM5pe25ruh6LazIGlzX3NlbGVjdGVkPXRydWUg5LiUIGNvbnRlbnRfdHlwZSDljIXlkKsgaW1hZ2XvvIlcbmNvbnN0IGlzQXJyYW5nZWRJbWFnZSA9IGNvbXB1dGVkKCgpID0+IHtcbiAgcmV0dXJuIGVkaXRpbmdBcnRpY2xlLnZhbHVlLmlzX3NlbGVjdGVkICYmIChlZGl0aW5nQXJ0aWNsZS52YWx1ZS5jb250ZW50X3R5cGUgPT09ICdpbWFnZScgfHwgZWRpdGluZ0FydGljbGUudmFsdWUuY29udGVudF90eXBlID09PSAnYm90aCcpXG59KVxuXG4vLyDmoLnmja7lvZPliY3nrZvpgInmoIfnrb7noa7lrprnm67moIfotKblj7dcbi8vIOmHj+WMluS6pOaYk+W9kuWxnuS6jue7j+a1juWtpui0puWPt++8jOWFtuS7luagh+etvuebtOaOpeWvueW6lFxuY29uc3QgZ2V0QWNjb3VudFRhcmdldCA9ICgpID0+IHtcbiAgY29uc3QgdGFnVG9BY2NvdW50ID0ge1xuICAgICdBSSc6ICdBSScsXG4gICAgJ+mHj+WMluS6pOaYkyc6ICfnu4/mtY7lraYnLFxuICAgICfnu4/mtY7lraYnOiAn57uP5rWO5a2mJyxcbiAgICAn5b+D55CG5a2mJzogJ+W/g+eQhuWtpidcbiAgfVxuICByZXR1cm4gdGFnVG9BY2NvdW50W2ZpbHRlclRhZy52YWx1ZV0gfHwgJ0FJJ1xufVxuXG4vLyDmibnph4/mk43kvZznm7jlhbNcbmNvbnN0IHNlbGVjdGVkQXJ0aWNsZUlkcyA9IHJlZihuZXcgU2V0KCkpXG5jb25zdCBiYXRjaERlbGV0aW5nID0gcmVmKGZhbHNlKVxuXG4vLyBBSei/h+a7pOebuOWFs1xuY29uc3QgYWlGaWx0ZXJpbmcgPSByZWYoZmFsc2UpXG5jb25zdCBzaG93QUlGaWx0ZXJNb2RhbCA9IHJlZihmYWxzZSlcbmNvbnN0IGFpRmlsdGVyQXJ0aWNsZXMgPSByZWYoW10pXG5jb25zdCBhaUZpbHRlclRvdGFsQ2hlY2tlZCA9IHJlZigwKVxuY29uc3QgYWlGaWx0ZXJEZWxldGluZyA9IHJlZihmYWxzZSlcbi8vIOaPkOekuuivjee8lui+keW8ueeql1xuY29uc3Qgc2hvd1Byb21wdEVkaXRNb2RhbCA9IHJlZihmYWxzZSlcbmNvbnN0IGVkaXRpbmdQcm9tcHQgPSByZWYoJycpXG5jb25zdCBzYXZpbmdQcm9tcHQgPSByZWYoZmFsc2UpXG5jb25zdCBsb2FkaW5nUHJvbXB0ID0gcmVmKGZhbHNlKVxuXG5jb25zdCBzdGF0dXNDbGFzcyA9IGNvbXB1dGVkKCgpID0+IHtcbiAgaWYgKCFjaGFybGVzU3RhdHVzLnZhbHVlKSByZXR1cm4gJ3N0YXR1cy11bmtub3duJ1xuICBjb25zdCBzID0gY2hhcmxlc1N0YXR1cy52YWx1ZVxuICBpZiAocy5zdGF0dXMgPT09ICdkZWFkJykgcmV0dXJuICdzdGF0dXMtZGVhZCdcbiAgaWYgKHMuc3RhdHVzID09PSAnd29ya2luZycpIHtcbiAgICAvLyDov57nu63nqbrova7otoXov4cgMTAg5qyh77yM5oiW5pyA5ZCO6YeH6ZuG5pe26Ze06LaF6L+HIDI0IOWwj+aXtu+8jOinhuS4uuW8guW4uFxuICAgIGlmIChzLmVtcHR5X2N5Y2xlcyA+PSAxMCkgcmV0dXJuICdzdGF0dXMtd2FybmluZydcbiAgICBpZiAocy5sYXN0X25ld19hcnRpY2xlX3RpbWUpIHtcbiAgICAgIGNvbnN0IGxhc3RUaW1lID0gbmV3IERhdGUocy5sYXN0X25ld19hcnRpY2xlX3RpbWUpLmdldFRpbWUoKVxuICAgICAgY29uc3Qgbm93ID0gRGF0ZS5ub3coKVxuICAgICAgaWYgKG5vdyAtIGxhc3RUaW1lID4gMjQgKiA2MCAqIDYwICogMTAwMCkgcmV0dXJuICdzdGF0dXMtd2FybmluZydcbiAgICB9XG4gICAgcmV0dXJuICdzdGF0dXMtd29ya2luZydcbiAgfVxuICByZXR1cm4gJ3N0YXR1cy11bmtub3duJ1xufSlcblxuY29uc3Qgc3RhdHVzVGV4dCA9IGNvbXB1dGVkKCgpID0+IHtcbiAgaWYgKCFjaGFybGVzU3RhdHVzLnZhbHVlKSByZXR1cm4gJ+acquefpSdcbiAgY29uc3QgcyA9IGNoYXJsZXNTdGF0dXMudmFsdWVcbiAgaWYgKHMuc3RhdHVzID09PSAnZGVhZCcpIHJldHVybiAn5bey5YGc5q2iJ1xuICBpZiAocy5zdGF0dXMgPT09ICd3b3JraW5nJykge1xuICAgIGlmIChzdGF0dXNDbGFzcy52YWx1ZSA9PT0gJ3N0YXR1cy13YXJuaW5nJykgcmV0dXJuICfph4fpm4blvILluLgnXG4gICAgcmV0dXJuICfov5DooYzkuK0nXG4gIH1cbiAgcmV0dXJuICfmnKrnn6UnXG59KVxuXG5jb25zdCBzaG93U3RhdHVzRGV0YWlsID0gKCkgPT4ge1xuICBpZiAoIWNoYXJsZXNTdGF0dXMudmFsdWUpIHtcbiAgICBhbGVydCgn5peg5rOV6I635Y+W54q25oCB5L+h5oGvJylcbiAgICByZXR1cm5cbiAgfVxuICBjb25zdCBzID0gY2hhcmxlc1N0YXR1cy52YWx1ZVxuICBsZXQgbXNnID0gYOeKtuaAgTogJHtzdGF0dXNUZXh0LnZhbHVlfVxcbmBcbiAgaWYgKHMuc3RhcnRfdGltZSkgbXNnICs9IGDlkK/liqjml7bpl7Q6ICR7cy5zdGFydF90aW1lfVxcbmBcbiAgaWYgKHMubGFzdF91cGRhdGVfdGltZSkgbXNnICs9IGDmnIDlkI7lv4Pot7M6ICR7cy5sYXN0X3VwZGF0ZV90aW1lfVxcbmBcbiAgaWYgKHMuZW5kX3RpbWUpIG1zZyArPSBg57uT5p2f5pe26Ze0OiAke3MuZW5kX3RpbWV9XFxuYFxuICBpZiAocy5lcnJvcl9tZXNzYWdlKSBtc2cgKz0gYOmUmeivr+S/oeaBrzogJHtzLmVycm9yX21lc3NhZ2V9XFxuYFxuICBpZiAocy5waWQpIG1zZyArPSBg6L+b56iLSUQ6ICR7cy5waWR9XFxuYFxuICBpZiAocy5tZXNzYWdlKSBtc2cgKz0gYOivtOaYjjogJHtzLm1lc3NhZ2V9XFxuYFxuICBhbGVydChtc2cpXG59XG5cbmNvbnN0IGZldGNoQ2hhcmxlc1N0YXR1cyA9IGFzeW5jICgpID0+IHtcbiAgdHJ5IHtcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L3N0YXR1c2ApXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XG4gICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XG4gICAgICAgIGNoYXJsZXNTdGF0dXMudmFsdWUgPSByZXN1bHQuZGF0YVxuICAgICAgICBpZiAocmVzdWx0LmRhdGEuc3RhdHVzID09PSAnZGVhZCcgJiYgIXN0YXR1c1Nob3duQWxlcnQudmFsdWUpIHtcbiAgICAgICAgICBzdGF0dXNTaG93bkFsZXJ0LnZhbHVlID0gdHJ1ZVxuICAgICAgICAgIGNvbnN0IGVycm9yTXNnID0gcmVzdWx0LmRhdGEuZXJyb3JfbWVzc2FnZSA/IGBcXG7plJnor6/kv6Hmga86ICR7cmVzdWx0LmRhdGEuZXJyb3JfbWVzc2FnZX1gIDogJydcbiAgICAgICAgICBzdG9wQWxlcnRNZXNzYWdlLnZhbHVlID0gYENoYXJsZXMg5bey5YGc5q2i6L+Q6KGM77yBJHtlcnJvck1zZ31cXG5cXG7or7fmo4Dmn6Xlubbph43mlrDlkK/liqggQ2hhcmxlc+OAgmBcbiAgICAgICAgICBzaG93U3RvcEFsZXJ0LnZhbHVlID0gdHJ1ZVxuICAgICAgICB9XG4gICAgICB9XG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPlueKtuaAgeWksei0pTonLCBlcnJvcilcbiAgfVxufVxuXG4vLyDojrflj5blj5HluIPorqHliJIgKOeuoemBk+mHjOW3sumAieacquWPkeWujOeahOinhumikSlcbmNvbnN0IGZldGNoU2NoZWR1bGUgPSBhc3luYyAoKSA9PiB7XG4gIHNjaGVkdWxlTG9hZGluZy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke0FQSV9CQVNFX1VSTH0vYXBpL3poaWh1L3ZpZGVvLXNjaGVkdWxlYClcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxuICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcbiAgICAgICAgc2NoZWR1bGVJdGVtcy52YWx1ZSA9IHJlc3VsdC5kYXRhPy5pdGVtcyB8fCBbXVxuICAgICAgICBzY2hlZHVsZVN1bW1hcnkudmFsdWUgPSByZXN1bHQuZGF0YT8uc3VtbWFyeSB8fCBudWxsXG4gICAgICB9XG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluWPkeW4g+iuoeWIkuWksei0pTonLCBlcnJvcilcbiAgfSBmaW5hbGx5IHtcbiAgICBzY2hlZHVsZUxvYWRpbmcudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOaWsOmynOW6pjog5LqL5Lu25pe26Ze0IChwdWJsaXNoZWRfYXQsIOayoeacieWwsSBjcmVhdGVkX2F0KSDot53ku4rlpKnmlbBcbmNvbnN0IGZyZXNoQWdlRGF5cyA9IChhcnRpY2xlKSA9PiB7XG4gIGNvbnN0IHQgPSBhcnRpY2xlLnB1Ymxpc2hlZF9hdCB8fCBhcnRpY2xlLmNyZWF0ZWRfYXRcbiAgaWYgKCF0KSByZXR1cm4gbnVsbFxuICBjb25zdCBkYXlzID0gTWF0aC5mbG9vcigoRGF0ZS5ub3coKSAtIG5ldyBEYXRlKHQpLmdldFRpbWUoKSkgLyA4NjQwMDAwMClcbiAgcmV0dXJuIGRheXMgPCAwID8gMCA6IGRheXNcbn1cblxuY29uc3QgZnJlc2hCYWRnZUNsYXNzQnlEYXlzID0gKGRheXMpID0+IHtcbiAgaWYgKGRheXMgPT09IG51bGwpIHJldHVybiAnJ1xuICBpZiAoZGF5cyA8PSAzKSByZXR1cm4gJ2ZyZXNoLWhvdCcgICAgIC8vIEZyZXNoIOW8uuS/neW6leeql+WPo+WGhVxuICBpZiAoZGF5cyA8PSA3KSByZXR1cm4gJ2ZyZXNoLW9rJyAgICAgIC8vIOi/mOWcqOWAmemAieaLieWPlueql+WPo+WGhVxuICByZXR1cm4gJ2ZyZXNoLXN0YWxlJ1xufVxuXG5jb25zdCBmcmVzaEJhZGdlQ2xhc3MgPSAoYXJ0aWNsZSkgPT4gZnJlc2hCYWRnZUNsYXNzQnlEYXlzKGZyZXNoQWdlRGF5cyhhcnRpY2xlKSlcblxuY29uc3QgdmlkZW9TdGF0dXNUZXh0ID0gKHMpID0+IHtcbiAgY29uc3QgbWFwID0ge1xuICAgIHBlbmRpbmc6ICfmjpLpmJ8nLCBwcm9jZXNzaW5nOiAn5Yi25L2c5LitJywgY29tcGxldGVkOiAn5bey5a6M5oiQJyxcbiAgICBmYWlsZWQ6ICflpLHotKUnLCBwdWJsaXNoZWQ6ICflt7Llj5EnXG4gIH1cbiAgcmV0dXJuIG1hcFtzXSB8fCAn5o6S6ZifJ1xufVxuXG4vLyDlubPlj7DljZXlhYPmoLw6IOacieaOkuacn+aXtumXtOaYvuekuuaXtumXtCwg5ZCm5YiZ5pi+56S654q25oCBXG5jb25zdCBwbGF0Zm9ybUNlbGwgPSAoc3RhdHVzLCBzY2hlZHVsZWRBdCkgPT4ge1xuICBpZiAoc2NoZWR1bGVkQXQpIHtcbiAgICBjb25zdCBkID0gbmV3IERhdGUoc2NoZWR1bGVkQXQpXG4gICAgY29uc3QgbW0gPSAoZC5nZXRNb250aCgpICsgMSkudG9TdHJpbmcoKS5wYWRTdGFydCgyLCAnMCcpXG4gICAgY29uc3QgZGQgPSBkLmdldERhdGUoKS50b1N0cmluZygpLnBhZFN0YXJ0KDIsICcwJylcbiAgICBjb25zdCBoaCA9IGQuZ2V0SG91cnMoKS50b1N0cmluZygpLnBhZFN0YXJ0KDIsICcwJylcbiAgICByZXR1cm4gYCR7bW19LSR7ZGR9ICR7aGh9OjAwYFxuICB9XG4gIGNvbnN0IG1hcCA9IHtcbiAgICBhcHByb3ZlZDogJ+W+heaOkuacnycsIHNjaGVkdWxlZDogJ+W3suaOkuacnycsIHB1Ymxpc2hlZDogJ+W3suWPkScsXG4gICAgZmFpbGVkOiAn5aSx6LSlJywgYWJhbmRvbmVkOiAn5pS+5byDJywgcGVuZGluZzogJ+WkhOeQhuS4rScsIHByb2Nlc3Npbmc6ICflpITnkIbkuK0nXG4gIH1cbiAgcmV0dXJuIG1hcFtzdGF0dXNdIHx8ICctJ1xufVxuXG4vLyDojrflj5bnn6XkuY7mlofnq6DliJfooahcbmNvbnN0IGZldGNoQXJ0aWNsZXMgPSBhc3luYyAocGFnZSA9IDEpID0+IHtcbiAgbG9hZGluZy52YWx1ZSA9IHRydWVcbiAgLy8g5YiH5o2i6aG16Z2i5pe25riF56m66YCJ5Lit54q25oCBXG4gIGlmIChwYWdlICE9PSBjdXJyZW50UGFnZS52YWx1ZSkge1xuICAgIHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZS5jbGVhcigpXG4gIH1cbiAgdHJ5IHtcbiAgICBjb25zdCBwYXJhbXMgPSBuZXcgVVJMU2VhcmNoUGFyYW1zKHtcbiAgICAgIHBhZ2U6IHBhZ2UudG9TdHJpbmcoKSxcbiAgICAgIHBhZ2Vfc2l6ZTogJzIwJyxcbiAgICAgIHNvcnRfYnk6IHNvcnRCeS52YWx1ZVxuICAgIH0pXG4gICAgXG4gICAgLy8g5b6F5a6h5qC477yaZmlsdGVyU2VsZWN0ZWQ9ZmFsc2UsIGZpbHRlclJlamVjdGVkPW51bGwg4oaSIGlzX3NlbGVjdGVkPTAsIOS4jeS8oCBpc19kZWxldGVk77yI5ZCO56uv6buY6K6k5o6S6Zmk5bey5Yig6Zmk77yJXG4gICAgLy8g5bey5a6J5o6S77yaZmlsdGVyU2VsZWN0ZWQ9dHJ1ZSwgZmlsdGVyUmVqZWN0ZWQ9bnVsbCDihpIgaXNfc2VsZWN0ZWQ9MSwg5LiN5LygIGlzX2RlbGV0ZWTvvIjlkI7nq6/pu5jorqTmjpLpmaTlt7LliKDpmaTvvIlcbiAgICAvLyDlt7LliKDpmaTvvJpmaWx0ZXJSZWplY3RlZD10cnVlIOKGkiBpc19kZWxldGVkPTFcbiAgICAvLyDms6jmhI/vvJrlvZPmnInmkJzntKLlhbPplK7or43kuJTmsqHmnInmmI7noa7mjIflrprnirbmgIHml7bvvIzmkJzntKLmiYDmnInnirbmgIHvvIjkuI3kvKAgaXNfc2VsZWN0ZWTvvIlcbiAgICBjb25zdCBoYXNTZWFyY2hLZXl3b3JkID0gc2VhcmNoS2V5d29yZC52YWx1ZSAmJiBzZWFyY2hLZXl3b3JkLnZhbHVlLnRyaW0oKVxuICAgIGNvbnN0IGhhc0V4cGxpY2l0U3RhdHVzID0gcm91dGUucXVlcnkuc3RhdHVzXG4gICAgXG4gICAgaWYgKGZpbHRlclJlamVjdGVkLnZhbHVlID09PSB0cnVlKSB7XG4gICAgICBwYXJhbXMuYXBwZW5kKCdpc19kZWxldGVkJywgJzEnKVxuICAgIH0gZWxzZSBpZiAoIWhhc1NlYXJjaEtleXdvcmQgfHwgaGFzRXhwbGljaXRTdGF0dXMpIHtcbiAgICAgIC8vIOayoeacieaQnOe0ouWFs+mUruivje+8jOaIluiAheacieaYjuehruaMh+WumueKtuaAgeaXtu+8jOaMieeKtuaAgeetm+mAiVxuICAgICAgaWYgKGZpbHRlclNlbGVjdGVkLnZhbHVlICE9PSBudWxsKSB7XG4gICAgICAgIHBhcmFtcy5hcHBlbmQoJ2lzX3NlbGVjdGVkJywgZmlsdGVyU2VsZWN0ZWQudmFsdWUgPyAnMScgOiAnMCcpXG4gICAgICB9XG4gICAgICAvLyDkuI3kvKAgaXNfZGVsZXRlZO+8jOiuqeWQjuerr+m7mOiupOaOkumZpOW3suWIoOmZpOeahOaWh+eroFxuICAgIH1cbiAgICAvLyDlpoLmnpzmnInmkJzntKLlhbPplK7or43kvYbmsqHmnInmmI7noa7mjIflrprnirbmgIHvvIzliJnmkJzntKLmiYDmnInnirbmgIHvvIjkuI3kvKAgaXNfc2VsZWN0ZWTvvIlcbiAgICBcbiAgICAvLyDlpoLmnpzmnInmkJzntKLlhbPplK7or43vvIzmt7vliqDliLDlj4LmlbDkuK1cbiAgICBpZiAoc2VhcmNoS2V5d29yZC52YWx1ZSAmJiBzZWFyY2hLZXl3b3JkLnZhbHVlLnRyaW0oKSkge1xuICAgICAgcGFyYW1zLmFwcGVuZCgndGl0bGUnLCBzZWFyY2hLZXl3b3JkLnZhbHVlLnRyaW0oKSlcbiAgICB9XG4gICAgXG4gICAgLy8g5aaC5p6c5pyJ5bmz5Y+w562b6YCJ77yM5re75Yqg5Yiw5Y+C5pWw5LitXG4gICAgaWYgKGZpbHRlclBsYXRmb3JtLnZhbHVlKSB7XG4gICAgICBwYXJhbXMuYXBwZW5kKCdwbGF0Zm9ybScsIGZpbHRlclBsYXRmb3JtLnZhbHVlKVxuICAgIH1cbiAgICBcbiAgICAvLyDlpoLmnpzmnInmoIfnrb7nrZvpgInvvIzmt7vliqDliLDlj4LmlbDkuK1cbiAgICBpZiAoZmlsdGVyVGFnLnZhbHVlKSB7XG4gICAgICBwYXJhbXMuYXBwZW5kKCd0YWcnLCBmaWx0ZXJUYWcudmFsdWUpXG4gICAgfVxuICAgIFxuICAgIC8vIOS9v+eUqOe7n+S4gOeahCBBUEkg56uv54K577yI5LiO5ZCO56uv5pyN5Yqh5Zyo5ZCM5LiA56uv5Y+j77yJXG4gICAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcz8ke3BhcmFtc31gKVxuICAgIFxuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICAvLyDlhbzlrrnkuKTnp43lk43lupTmoLzlvI/vvJp7Y29kZTogMCwgZGF0YTogW10sIHBhZ2luYXRpb246IHt9fSDlkowge2NvZGU6IDAsIG1zZzogXCJva1wiLCBkYXRhOiBbXSwgcGFnaW5hdGlvbjoge319XG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBhcnRpY2xlcy52YWx1ZSA9IHJlc3VsdC5kYXRhIHx8IFtdXG4gICAgICAgIHBhZ2luYXRpb24udmFsdWUgPSByZXN1bHQucGFnaW5hdGlvblxuICAgICAgICBjdXJyZW50UGFnZS52YWx1ZSA9IHBhZ2VcbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluaWh+eroOWIl+ihqOWksei0pTonLCByZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKVxuICAgICAgICBhcnRpY2xlcy52YWx1ZSA9IFtdXG4gICAgICB9XG4gICAgfSBlbHNlIHtcbiAgICAgIGNvbnNvbGUuZXJyb3IoJ0FQSSDor7fmsYLlpLHotKU6JywgcmVzcG9uc2Uuc3RhdHVzKVxuICAgICAgYXJ0aWNsZXMudmFsdWUgPSBbXVxuICAgIH1cbiAgfSBjYXRjaCAoZXJyb3IpIHtcbiAgICBjb25zb2xlLmVycm9yKCfojrflj5bmlofnq6DliJfooajlh7rplJk6JywgZXJyb3IpXG4gICAgYXJ0aWNsZXMudmFsdWUgPSBbXVxuICB9IGZpbmFsbHkge1xuICAgIGxvYWRpbmcudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOWIh+aNoumAieS4reeKtuaAgVxuY29uc3QgdG9nZ2xlU2VsZWN0ID0gYXN5bmMgKGFydGljbGUpID0+IHtcbiAgLy8g5aaC5p6c5bey6YCJ5Lit77yM55u05o6l5Y+W5raI6YCJ5LitXG4gIGlmIChhcnRpY2xlLmlzX3NlbGVjdGVkKSB7XG4gICAgYXdhaXQgdXBkYXRlU2VsZWN0U3RhdHVzKGFydGljbGUsIGZhbHNlKVxuICAgIHJldHVyblxuICB9XG4gIFxuICAvLyDlpoLmnpzmnKrpgInkuK3vvIzlvLnlh7rorr7nva7lvLnnqpdcbiAgc2VsZWN0aW5nQXJ0aWNsZS52YWx1ZSA9IGFydGljbGVcbiAgLy8g5qC55o2u5paH56ug5b2T5YmN54q25oCB5Yid5aeL5YyW6K6+572uXG4gIHNlbGVjdFNldHRpbmdzLnZhbHVlID0ge1xuICAgIGFjY291bnRfdGFyZ2V0OiBhcnRpY2xlLmFjY291bnRfdGFyZ2V0IHx8ICdBSScsXG4gICAgY29udGVudF90eXBlX2ltYWdlOiBhcnRpY2xlLmNvbnRlbnRfdHlwZSA9PT0gJ2ltYWdlJyB8fCBhcnRpY2xlLmNvbnRlbnRfdHlwZSA9PT0gJ2JvdGgnLFxuICAgIGNvbnRlbnRfdHlwZV92aWRlbzogYXJ0aWNsZS5jb250ZW50X3R5cGUgPT09ICd2aWRlbycgfHwgYXJ0aWNsZS5jb250ZW50X3R5cGUgPT09ICdib3RoJyxcbiAgfVxuICBzaG93U2VsZWN0TW9kYWwudmFsdWUgPSB0cnVlXG59XG5cbi8vIOehruiupOmAieS4rVxuY29uc3QgY29uZmlybVNlbGVjdCA9IGFzeW5jICgpID0+IHtcbiAgaWYgKCFoYXNTZWxlY3RDb250ZW50VHlwZS52YWx1ZSB8fCAhc2VsZWN0aW5nQXJ0aWNsZS52YWx1ZSkgcmV0dXJuXG4gIFxuICBzZWxlY3RpbmcudmFsdWUgPSB0cnVlXG4gIHRyeSB7XG4gICAgY29uc3QgYXJ0aWNsZSA9IHNlbGVjdGluZ0FydGljbGUudmFsdWVcbiAgICBcbiAgICAvLyDmnoTlu7ogY29udGVudF90eXBlXG4gICAgbGV0IGNvbnRlbnRfdHlwZSA9IG51bGxcbiAgICBpZiAoc2VsZWN0U2V0dGluZ3MudmFsdWUuY29udGVudF90eXBlX2ltYWdlICYmIHNlbGVjdFNldHRpbmdzLnZhbHVlLmNvbnRlbnRfdHlwZV92aWRlbykge1xuICAgICAgY29udGVudF90eXBlID0gJ2JvdGgnXG4gICAgfSBlbHNlIGlmIChzZWxlY3RTZXR0aW5ncy52YWx1ZS5jb250ZW50X3R5cGVfaW1hZ2UpIHtcbiAgICAgIGNvbnRlbnRfdHlwZSA9ICdpbWFnZSdcbiAgICB9IGVsc2UgaWYgKHNlbGVjdFNldHRpbmdzLnZhbHVlLmNvbnRlbnRfdHlwZV92aWRlbykge1xuICAgICAgY29udGVudF90eXBlID0gJ3ZpZGVvJ1xuICAgIH1cbiAgICBcbiAgICAvLyDosIPnlKggQVBJIOabtOaWsOmAieS4reeKtuaAgVxuICAgIGF3YWl0IHVwZGF0ZVNlbGVjdFN0YXR1cyhcbiAgICAgIGFydGljbGUsIFxuICAgICAgdHJ1ZSwgXG4gICAgICBjb250ZW50X3R5cGUsXG4gICAgICBzZWxlY3RTZXR0aW5ncy52YWx1ZS5hY2NvdW50X3RhcmdldCxcbiAgICApXG4gICAgXG4gICAgLy8g5YWz6Zet5by556qXXG4gICAgY2xvc2VTZWxlY3RNb2RhbCgpXG4gIH0gY2F0Y2ggKGVycm9yKSB7XG4gICAgY29uc29sZS5lcnJvcign56Gu6K6k6YCJ5Lit5Ye66ZSZOicsIGVycm9yKVxuICAgIGFsZXJ0KCforr7nva7lpLHotKXvvIzor7fnqI3lkI7ph43or5UnKVxuICB9IGZpbmFsbHkge1xuICAgIHNlbGVjdGluZy52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cblxuLy8g5pu05paw6YCJ5Lit54q25oCB55qE6YCa55So5Ye95pWwXG5jb25zdCB1cGRhdGVTZWxlY3RTdGF0dXMgPSBhc3luYyAoYXJ0aWNsZSwgaXNfc2VsZWN0ZWQsIGNvbnRlbnRfdHlwZSA9IG51bGwsIGFjY291bnRfdGFyZ2V0ID0gbnVsbCkgPT4ge1xuICB0cnkge1xuICAgIGNvbnN0IGFwaVVybCA9IEFQSV9CQVNFX1VSTFxuICAgIGNvbnN0IGJvZHkgPSB7IGlzX3NlbGVjdGVkIH1cbiAgICBcbiAgICBpZiAoaXNfc2VsZWN0ZWQpIHtcbiAgICAgIGlmIChjb250ZW50X3R5cGUpIGJvZHkuY29udGVudF90eXBlID0gY29udGVudF90eXBlXG4gICAgICBpZiAoYWNjb3VudF90YXJnZXQpIGJvZHkuYWNjb3VudF90YXJnZXQgPSBhY2NvdW50X3RhcmdldFxuICAgIH1cbiAgICBcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzLyR7YXJ0aWNsZS5pZH0vc2VsZWN0YCwge1xuICAgICAgbWV0aG9kOiAnUFVUJyxcbiAgICAgIGhlYWRlcnM6IHtcbiAgICAgICAgJ0NvbnRlbnQtVHlwZSc6ICdhcHBsaWNhdGlvbi9qc29uJ1xuICAgICAgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KGJvZHkpXG4gICAgfSlcbiAgICBcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxuICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcbiAgICAgICAgLy8g5pu05paw5pys5Zyw54q25oCBXG4gICAgICAgIGFydGljbGUuaXNfc2VsZWN0ZWQgPSBpc19zZWxlY3RlZFxuICAgICAgICBpZiAoY29udGVudF90eXBlKSBhcnRpY2xlLmNvbnRlbnRfdHlwZSA9IGNvbnRlbnRfdHlwZVxuICAgICAgICBpZiAoYWNjb3VudF90YXJnZXQpIGFydGljbGUuYWNjb3VudF90YXJnZXQgPSBhY2NvdW50X3RhcmdldFxuICAgICAgICBcbiAgICAgICAgLy8g5Yi35paw57uf6K6h5L+h5oGvXG4gICAgICAgIGZldGNoU3RhdGlzdGljcygpXG4gICAgICAgIFxuICAgICAgICAvLyDlpoLmnpzlvZPliY3mmK9cIuW+heWuoeaguFwi5YiX6KGo5LiU6K6+572u5Li65bey5a6J5o6S77yM5oiW6ICF5b2T5YmN5pivXCLlt7LlronmjpJcIuWIl+ihqOS4lOWPlua2iOWuieaOku+8jOS7juWIl+ihqOS4reenu+mZpFxuICAgICAgICBpZiAoKHN0YXR1c0ZpbHRlci52YWx1ZSA9PT0gJ3BlbmRpbmcnICYmIGlzX3NlbGVjdGVkKSB8fCBcbiAgICAgICAgICAgIChzdGF0dXNGaWx0ZXIudmFsdWUgPT09ICdzZWxlY3RlZCcgJiYgIWlzX3NlbGVjdGVkKSkge1xuICAgICAgICAgIGFydGljbGVzLnZhbHVlID0gYXJ0aWNsZXMudmFsdWUuZmlsdGVyKGEgPT4gYS5pZCAhPT0gYXJ0aWNsZS5pZClcbiAgICAgICAgfVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+abtOaWsOWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKSlcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgYWxlcnQoJ+abtOaWsOWksei0pe+8jOivt+eojeWQjumHjeivlScpXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+abtOaWsOmAieS4reeKtuaAgeWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn5pu05paw5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfVxufVxuXG4vLyDlhbPpl63pgInkuK3orr7nva7lvLnnqpdcbmNvbnN0IGNsb3NlU2VsZWN0TW9kYWwgPSAoKSA9PiB7XG4gIHNob3dTZWxlY3RNb2RhbC52YWx1ZSA9IGZhbHNlXG4gIHNlbGVjdGluZ0FydGljbGUudmFsdWUgPSBudWxsXG4gIHNlbGVjdFNldHRpbmdzLnZhbHVlID0ge1xuICAgIGFjY291bnRfdGFyZ2V0OiAnQUknLFxuICAgIGNvbnRlbnRfdHlwZV9pbWFnZTogZmFsc2UsXG4gICAgY29udGVudF90eXBlX3ZpZGVvOiBmYWxzZSxcbiAgfVxufVxuXG4vLyDmoIforrDkuLrliKDpmaTnmoRcbmNvbnN0IG1hcmtSZWplY3RlZCA9IGFzeW5jIChhcnRpY2xlKSA9PiB7XG4gIHRyeSB7XG4gICAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcy8ke2FydGljbGUuaWR9L2RlbGV0ZWAsIHtcbiAgICAgIG1ldGhvZDogJ1BVVCcsXG4gICAgICBoZWFkZXJzOiB7XG4gICAgICAgICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbidcbiAgICAgIH0sXG4gICAgICBib2R5OiBKU09OLnN0cmluZ2lmeSh7XG4gICAgICAgIGlzX2RlbGV0ZWQ6ICFhcnRpY2xlLmlzX2RlbGV0ZWRcbiAgICAgIH0pXG4gICAgfSlcbiAgICBcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxuICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcbiAgICAgICAgLy8g5pu05paw5pys5Zyw54q25oCBXG4gICAgICAgIGFydGljbGUuaXNfZGVsZXRlZCA9ICFhcnRpY2xlLmlzX2RlbGV0ZWRcbiAgICAgICAgLy8g5aaC5p6c5qCH6K6w5Li65Yig6Zmk77yM5LuO5YiX6KGo5Lit56e76Zmk77yI6Zmk6Z2e5b2T5YmN5q2j5Zyo5p+l55yLXCLliKDpmaTnmoRcIuWIl+ihqO+8iVxuICAgICAgICBpZiAoYXJ0aWNsZS5pc19kZWxldGVkICYmIGZpbHRlclJlamVjdGVkLnZhbHVlICE9PSB0cnVlKSB7XG4gICAgICAgICAgYXJ0aWNsZXMudmFsdWUgPSBhcnRpY2xlcy52YWx1ZS5maWx0ZXIoYSA9PiBhLmlkICE9PSBhcnRpY2xlLmlkKVxuICAgICAgICB9XG4gICAgICAgIC8vIOWIt+aWsOe7n+iuoeS/oeaBr1xuICAgICAgICBmZXRjaFN0YXRpc3RpY3MoKVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+abtOaWsOWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKSlcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgYWxlcnQoJ+abtOaWsOWksei0pe+8jOivt+eojeWQjumHjeivlScpXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+agh+iusOWksei0pTonLCBlcnJvcilcbiAgICBhbGVydCgn5pu05paw5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfVxufVxuXG4vLyDorqHnrpflj6/op4HnmoTpobXnoIHliJfooahcbmNvbnN0IHZpc2libGVQYWdlcyA9IGNvbXB1dGVkKCgpID0+IHtcbiAgaWYgKCFwYWdpbmF0aW9uLnZhbHVlIHx8IHBhZ2luYXRpb24udmFsdWUudG90YWxfcGFnZXMgPD0gMSkge1xuICAgIHJldHVybiBbXVxuICB9XG4gIFxuICBjb25zdCBjdXJyZW50ID0gcGFnaW5hdGlvbi52YWx1ZS5wYWdlXG4gIGNvbnN0IHRvdGFsID0gcGFnaW5hdGlvbi52YWx1ZS50b3RhbF9wYWdlc1xuICBjb25zdCBwYWdlcyA9IFtdXG4gIFxuICAvLyDlpoLmnpzmgLvpobXmlbDlsJHkuo7nrYnkuo436aG177yM5pi+56S65omA5pyJ6aG156CBXG4gIGlmICh0b3RhbCA8PSA3KSB7XG4gICAgZm9yIChsZXQgaSA9IDE7IGkgPD0gdG90YWw7IGkrKykge1xuICAgICAgcGFnZXMucHVzaChpKVxuICAgIH1cbiAgfSBlbHNlIHtcbiAgICAvLyDmgLvpobXmlbDlpKfkuo436aG177yM5pi+56S65b2T5YmN6aG16ZmE6L+R55qE6aG156CBXG4gICAgaWYgKGN1cnJlbnQgPD0gNCkge1xuICAgICAgLy8g5b2T5YmN6aG15Zyo5YmNNOmhte+8jOaYvuekuuWJjTXpobUgKyAuLi4gKyDmnIDlkI7kuIDpobVcbiAgICAgIGZvciAobGV0IGkgPSAxOyBpIDw9IDU7IGkrKykge1xuICAgICAgICBwYWdlcy5wdXNoKGkpXG4gICAgICB9XG4gICAgICBwYWdlcy5wdXNoKCcuLi4nKVxuICAgICAgcGFnZXMucHVzaCh0b3RhbClcbiAgICB9IGVsc2UgaWYgKGN1cnJlbnQgPj0gdG90YWwgLSAzKSB7XG4gICAgICAvLyDlvZPliY3pobXlnKjlkI406aG177yM5pi+56S656ys5LiA6aG1ICsgLi4uICsg5ZCONemhtVxuICAgICAgcGFnZXMucHVzaCgxKVxuICAgICAgcGFnZXMucHVzaCgnLi4uJylcbiAgICAgIGZvciAobGV0IGkgPSB0b3RhbCAtIDQ7IGkgPD0gdG90YWw7IGkrKykge1xuICAgICAgICBwYWdlcy5wdXNoKGkpXG4gICAgICB9XG4gICAgfSBlbHNlIHtcbiAgICAgIC8vIOW9k+WJjemhteWcqOS4remXtO+8jOaYvuekuuesrOS4gOmhtSArIC4uLiArIOW9k+WJjemhtemZhOi/kTPpobUgKyAuLi4gKyDmnIDlkI7kuIDpobVcbiAgICAgIHBhZ2VzLnB1c2goMSlcbiAgICAgIHBhZ2VzLnB1c2goJy4uLicpXG4gICAgICBmb3IgKGxldCBpID0gY3VycmVudCAtIDE7IGkgPD0gY3VycmVudCArIDE7IGkrKykge1xuICAgICAgICBwYWdlcy5wdXNoKGkpXG4gICAgICB9XG4gICAgICBwYWdlcy5wdXNoKCcuLi4nKVxuICAgICAgcGFnZXMucHVzaCh0b3RhbClcbiAgICB9XG4gIH1cbiAgXG4gIHJldHVybiBwYWdlc1xufSlcblxuLy8g5YiH5o2i6aG156CBXG5jb25zdCBjaGFuZ2VQYWdlID0gKHBhZ2UpID0+IHtcbiAgaWYgKHBhZ2UgPj0gMSAmJiAoIXBhZ2luYXRpb24udmFsdWUgfHwgcGFnZSA8PSBwYWdpbmF0aW9uLnZhbHVlLnRvdGFsX3BhZ2VzKSkge1xuICAgIC8vIOWIh+aNoumhtemdouaXtua4heepuumAieS4reeKtuaAgVxuICAgIHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZS5jbGVhcigpXG4gICAgLy8g5p6E5bu65a6M5pW055qEIFVSTCDlj4LmlbBcbiAgICBjb25zdCBxdWVyeSA9IHsgcGFnZTogcGFnZS50b1N0cmluZygpIH1cbiAgICBxdWVyeS5zdGF0dXMgPSBzdGF0dXNGaWx0ZXIudmFsdWVcbiAgICBpZiAoZmlsdGVyUGxhdGZvcm0udmFsdWUpIHtcbiAgICAgIHF1ZXJ5LnBsYXRmb3JtID0gZmlsdGVyUGxhdGZvcm0udmFsdWVcbiAgICB9XG4gICAgaWYgKGZpbHRlclRhZy52YWx1ZSkge1xuICAgICAgcXVlcnkudGFnID0gZmlsdGVyVGFnLnZhbHVlXG4gICAgfVxuICAgIGlmIChzb3J0QnkudmFsdWUgIT09ICdwdWJsaXNoZWRfYXQnKSB7XG4gICAgICBxdWVyeS5zb3J0ID0gc29ydEJ5LnZhbHVlXG4gICAgfVxuICAgIGlmIChzZWFyY2hLZXl3b3JkLnZhbHVlICYmIHNlYXJjaEtleXdvcmQudmFsdWUudHJpbSgpKSB7XG4gICAgICBxdWVyeS5zZWFyY2ggPSBzZWFyY2hLZXl3b3JkLnZhbHVlLnRyaW0oKVxuICAgIH1cbiAgICByb3V0ZXIucmVwbGFjZSh7IHF1ZXJ5IH0pXG4gICAgZmV0Y2hBcnRpY2xlcyhwYWdlKVxuICB9XG59XG5cbi8vIOi3s+i9rOWIsOaMh+WumumhtVxuY29uc3QganVtcFRvUGFnZSA9ICgpID0+IHtcbiAgaWYgKCFqdW1wUGFnZS52YWx1ZSB8fCAhcGFnaW5hdGlvbi52YWx1ZSkge1xuICAgIHJldHVyblxuICB9XG4gIFxuICBjb25zdCBwYWdlID0gcGFyc2VJbnQoanVtcFBhZ2UudmFsdWUpXG4gIGlmIChwYWdlID49IDEgJiYgcGFnZSA8PSBwYWdpbmF0aW9uLnZhbHVlLnRvdGFsX3BhZ2VzKSB7XG4gICAgY2hhbmdlUGFnZShwYWdlKVxuICAgIGp1bXBQYWdlLnZhbHVlID0gbnVsbFxuICB9IGVsc2Uge1xuICAgIGFsZXJ0KGDor7fovpPlhaUgMS0ke3BhZ2luYXRpb24udmFsdWUudG90YWxfcGFnZXN9IOS5i+mXtOeahOmhteeggWApXG4gIH1cbn1cblxuLy8g5om56YeP6YCJ5oup55u45YWzXG5jb25zdCB0b2dnbGVBcnRpY2xlU2VsZWN0aW9uID0gKGFydGljbGVJZCkgPT4ge1xuICBpZiAoc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmhhcyhhcnRpY2xlSWQpKSB7XG4gICAgc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmRlbGV0ZShhcnRpY2xlSWQpXG4gIH0gZWxzZSB7XG4gICAgc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmFkZChhcnRpY2xlSWQpXG4gIH1cbiAgLy8g6Kem5Y+R5ZON5bqU5byP5pu05pawXG4gIHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZSA9IG5ldyBTZXQoc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlKVxufVxuXG4vLyDlhajpgIkv5Y+W5raI5YWo6YCJXG5jb25zdCB0b2dnbGVTZWxlY3RBbGwgPSAoKSA9PiB7XG4gIGlmIChpc0FsbFNlbGVjdGVkLnZhbHVlKSB7XG4gICAgLy8g5Y+W5raI5YWo6YCJXG4gICAgc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmNsZWFyKClcbiAgfSBlbHNlIHtcbiAgICAvLyDlhajpgInlvZPliY3pobXvvIjmjpLpmaTlt7LliKDpmaTnmoTmlofnq6DvvIlcbiAgICBjb25zdCBzZWxlY3RhYmxlQXJ0aWNsZXMgPSBhcnRpY2xlcy52YWx1ZS5maWx0ZXIoYSA9PiAhYS5pc19kZWxldGVkKVxuICAgIHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZSA9IG5ldyBTZXQoc2VsZWN0YWJsZUFydGljbGVzLm1hcChhID0+IGEuaWQpKVxuICB9XG59XG5cbi8vIOiuoeeul+aYr+WQpuWFqOmAiVxuY29uc3QgaXNBbGxTZWxlY3RlZCA9IGNvbXB1dGVkKCgpID0+IHtcbiAgaWYgKGFydGljbGVzLnZhbHVlLmxlbmd0aCA9PT0gMCkgcmV0dXJuIGZhbHNlXG4gIGNvbnN0IHNlbGVjdGFibGVBcnRpY2xlcyA9IGFydGljbGVzLnZhbHVlLmZpbHRlcihhID0+ICFhLmlzX2RlbGV0ZWQpXG4gIGlmIChzZWxlY3RhYmxlQXJ0aWNsZXMubGVuZ3RoID09PSAwKSByZXR1cm4gZmFsc2VcbiAgcmV0dXJuIHNlbGVjdGFibGVBcnRpY2xlcy5ldmVyeShhID0+IHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZS5oYXMoYS5pZCkpXG59KVxuXG4vLyDorqHnrpfmmK/lkKbpg6jliIbpgInkuK3vvIjnlKjkuo7mmL7npLogaW5kZXRlcm1pbmF0ZSDnirbmgIHvvIlcbmNvbnN0IGlzSW5kZXRlcm1pbmF0ZSA9IGNvbXB1dGVkKCgpID0+IHtcbiAgY29uc3Qgc2VsZWN0YWJsZUFydGljbGVzID0gYXJ0aWNsZXMudmFsdWUuZmlsdGVyKGEgPT4gIWEuaXNfZGVsZXRlZClcbiAgaWYgKHNlbGVjdGFibGVBcnRpY2xlcy5sZW5ndGggPT09IDApIHJldHVybiBmYWxzZVxuICBjb25zdCBzZWxlY3RlZENvdW50ID0gc2VsZWN0YWJsZUFydGljbGVzLmZpbHRlcihhID0+IHNlbGVjdGVkQXJ0aWNsZUlkcy52YWx1ZS5oYXMoYS5pZCkpLmxlbmd0aFxuICByZXR1cm4gc2VsZWN0ZWRDb3VudCA+IDAgJiYgc2VsZWN0ZWRDb3VudCA8IHNlbGVjdGFibGVBcnRpY2xlcy5sZW5ndGhcbn0pXG5cbi8vIOaJuemHj+WIoOmZpFxuY29uc3QgYmF0Y2hEZWxldGUgPSBhc3luYyAoKSA9PiB7XG4gIGlmIChzZWxlY3RlZEFydGljbGVJZHMudmFsdWUuc2l6ZSA9PT0gMCkgcmV0dXJuXG4gIFxuICBiYXRjaERlbGV0aW5nLnZhbHVlID0gdHJ1ZVxuICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgY29uc3QgaWRzID0gQXJyYXkuZnJvbShzZWxlY3RlZEFydGljbGVJZHMudmFsdWUpXG4gIFxuICB0cnkge1xuICAgIC8vIOiwg+eUqOaJuemHj+WIoOmZpCBBUElcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzL2JhdGNoLWRlbGV0ZWAsIHtcbiAgICAgICAgICBtZXRob2Q6ICdQVVQnLFxuICAgICAgICAgIGhlYWRlcnM6IHtcbiAgICAgICAgICAgICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbidcbiAgICAgICAgICB9LFxuICAgICAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgYXJ0aWNsZV9pZHM6IGlkcyxcbiAgICAgICAgICAgIGlzX2RlbGV0ZWQ6IHRydWVcbiAgICAgICAgICB9KVxuICAgICAgICB9KVxuICAgICAgICBcbiAgICAgICAgaWYgKHJlc3BvbnNlLm9rKSB7XG4gICAgICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgIT09IDAgJiYgcmVzdWx0LmNvZGUgIT09IDIwMCkge1xuICAgICAgICBjb25zb2xlLmVycm9yKCfmibnph4/liKDpmaTlpLHotKU6JywgcmVzdWx0Lm1zZyB8fCByZXN1bHQubWVzc2FnZSlcbiAgICAgICAgICB9XG4gICAgICAgIH0gZWxzZSB7XG4gICAgICBjb25zb2xlLmVycm9yKCfmibnph4/liKDpmaTlpLHotKU6JywgcmVzcG9uc2Uuc3RhdHVzKVxuICAgIH1cbiAgfSBjYXRjaCAoZXJyb3IpIHtcbiAgICBjb25zb2xlLmVycm9yKCfmibnph4/liKDpmaTlh7rplJk6JywgZXJyb3IpXG4gIH0gZmluYWxseSB7XG4gICAgLy8g5peg6K665oiQ5Yqf5aSx6LSl77yM6YO95riF56m66YCJ5Lit54q25oCB5bm25Yi35pawXG4gICAgc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmNsZWFyKClcbiAgICBiYXRjaERlbGV0aW5nLnZhbHVlID0gZmFsc2VcbiAgICBmZXRjaEFydGljbGVzKGN1cnJlbnRQYWdlLnZhbHVlKVxuICAgIGZldGNoU3RhdGlzdGljcygpXG4gIH1cbn1cblxuLy8gQUnmmbrog73ov4fmu6QgLSDmiZPlvIDmj5DnpLror43nvJbovpHlvLnnqpdcbmNvbnN0IHN0YXJ0QUlGaWx0ZXIgPSBhc3luYyAoKSA9PiB7XG4gIGlmICghZmlsdGVyVGFnLnZhbHVlKSByZXR1cm5cbiAgbG9hZGluZ1Byb21wdC52YWx1ZSA9IHRydWVcbiAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXG5cbiAgdHJ5IHtcbiAgICAvLyDku47lkI7nq6/liqDovb3lvZPliY0gdGFnIOeahOaPkOekuuivjVxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goYCR7YXBpVXJsfS9hcGkvemhpaHUvYXJ0aWNsZXMvYWktZmlsdGVyP3RhZz0ke2VuY29kZVVSSUNvbXBvbmVudChmaWx0ZXJUYWcudmFsdWUpfWApXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XG4gICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcbiAgICAgIGVkaXRpbmdQcm9tcHQudmFsdWUgPSByZXN1bHQuZGF0YT8ucHJvbXB0IHx8ICcnXG4gICAgfSBlbHNlIHtcbiAgICAgIGVkaXRpbmdQcm9tcHQudmFsdWUgPSAnJ1xuICAgIH1cbiAgfSBjYXRjaCAoZSkge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+WKoOi9veaPkOekuuivjeWksei0pTonLCBlKVxuICAgIGVkaXRpbmdQcm9tcHQudmFsdWUgPSAnJ1xuICB9IGZpbmFsbHkge1xuICAgIGxvYWRpbmdQcm9tcHQudmFsdWUgPSBmYWxzZVxuICB9XG5cbiAgc2hvd1Byb21wdEVkaXRNb2RhbC52YWx1ZSA9IHRydWVcbn1cblxuLy8g5L+d5a2Y5o+Q56S66K+N5YiwIHlhbWxcbmNvbnN0IHNhdmVQcm9tcHQgPSBhc3luYyAoKSA9PiB7XG4gIGlmICghZmlsdGVyVGFnLnZhbHVlIHx8ICFlZGl0aW5nUHJvbXB0LnZhbHVlLnRyaW0oKSkgcmV0dXJuXG4gIHNhdmluZ1Byb21wdC52YWx1ZSA9IHRydWVcbiAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXG5cbiAgdHJ5IHtcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzL2FpLWZpbHRlcmAsIHtcbiAgICAgIG1ldGhvZDogJ1BVVCcsXG4gICAgICBoZWFkZXJzOiB7ICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHsgdGFnOiBmaWx0ZXJUYWcudmFsdWUsIHByb21wdDogZWRpdGluZ1Byb21wdC52YWx1ZS50cmltKCkgfSlcbiAgICB9KVxuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBhbGVydCgn5o+Q56S66K+N5bey5L+d5a2YJylcbiAgICAgIH1cbiAgICB9XG4gIH0gY2F0Y2ggKGUpIHtcbiAgICBjb25zb2xlLmVycm9yKCfkv53lrZjmj5DnpLror43lpLHotKU6JywgZSlcbiAgfSBmaW5hbGx5IHtcbiAgICBzYXZpbmdQcm9tcHQudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOaJp+ihjEFJ6L+H5rukXG5jb25zdCBydW5BSUZpbHRlciA9IGFzeW5jICgpID0+IHtcbiAgaWYgKCFmaWx0ZXJUYWcudmFsdWUgfHwgIWVkaXRpbmdQcm9tcHQudmFsdWUudHJpbSgpKSByZXR1cm5cbiAgYWlGaWx0ZXJpbmcudmFsdWUgPSB0cnVlXG4gIGNvbnN0IGFwaVVybCA9IEFQSV9CQVNFX1VSTFxuXG4gIHRyeSB7XG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcy9haS1maWx0ZXJgLCB7XG4gICAgICBtZXRob2Q6ICdQT1NUJyxcbiAgICAgIGhlYWRlcnM6IHsgJ0NvbnRlbnQtVHlwZSc6ICdhcHBsaWNhdGlvbi9qc29uJyB9LFxuICAgICAgYm9keTogSlNPTi5zdHJpbmdpZnkoeyB0YWc6IGZpbHRlclRhZy52YWx1ZSwgcHJvbXB0OiBlZGl0aW5nUHJvbXB0LnZhbHVlLnRyaW0oKSB9KVxuICAgIH0pXG5cbiAgICBpZiAoIXJlc3BvbnNlLm9rKSB7XG4gICAgICBjb25zb2xlLmVycm9yKCdBSei/h+a7pOivt+axguWksei0pTonLCByZXNwb25zZS5zdGF0dXMpXG4gICAgICByZXR1cm5cbiAgICB9XG5cbiAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcbiAgICBpZiAocmVzdWx0LmNvZGUgIT09IDAgJiYgcmVzdWx0LmNvZGUgIT09IDIwMCkge1xuICAgICAgY29uc29sZS5lcnJvcignQUnov4fmu6TlpLHotKU6JywgcmVzdWx0Lm1zZyB8fCByZXN1bHQubWVzc2FnZSlcbiAgICAgIGFsZXJ0KCdBSei/h+a7pOWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlIHx8ICcnKSlcbiAgICAgIHJldHVyblxuICAgIH1cblxuICAgIGNvbnN0IGRhdGEgPSByZXN1bHQuZGF0YSB8fCB7fVxuICAgIGFpRmlsdGVyQXJ0aWNsZXMudmFsdWUgPSBkYXRhLmFydGljbGVzX3RvX2RlbGV0ZSB8fCBbXVxuICAgIGFpRmlsdGVyVG90YWxDaGVja2VkLnZhbHVlID0gZGF0YS50b3RhbF9jaGVja2VkIHx8IDBcblxuICAgIC8vIOWFs+mXreaPkOekuuivjee8lui+keW8ueeql1xuICAgIHNob3dQcm9tcHRFZGl0TW9kYWwudmFsdWUgPSBmYWxzZVxuXG4gICAgaWYgKGFpRmlsdGVyQXJ0aWNsZXMudmFsdWUubGVuZ3RoID09PSAwKSB7XG4gICAgICBhbGVydCgnQUnliIbmnpDlrozmiJDvvIzmsqHmnInpnIDopoHliKDpmaTnmoTmlofnq6AnKVxuICAgICAgcmV0dXJuXG4gICAgfVxuXG4gICAgc2hvd0FJRmlsdGVyTW9kYWwudmFsdWUgPSB0cnVlXG4gIH0gY2F0Y2ggKGUpIHtcbiAgICBjb25zb2xlLmVycm9yKCdBSei/h+a7pOWHuumUmTonLCBlKVxuICB9IGZpbmFsbHkge1xuICAgIGFpRmlsdGVyaW5nLnZhbHVlID0gZmFsc2VcbiAgfVxufVxuXG4vLyDnoa7orqRBSei/h+a7pOWIoOmZpFxuY29uc3QgY29uZmlybUFJRmlsdGVyRGVsZXRlID0gYXN5bmMgKCkgPT4ge1xuICBpZiAoYWlGaWx0ZXJBcnRpY2xlcy52YWx1ZS5sZW5ndGggPT09IDApIHJldHVyblxuICBhaUZpbHRlckRlbGV0aW5nLnZhbHVlID0gdHJ1ZVxuICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgY29uc3QgaWRzID0gYWlGaWx0ZXJBcnRpY2xlcy52YWx1ZS5tYXAoYSA9PiBhLmlkKVxuXG4gIHRyeSB7XG4gICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcy9iYXRjaC1kZWxldGVgLCB7XG4gICAgICBtZXRob2Q6ICdQVVQnLFxuICAgICAgaGVhZGVyczogeyAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nIH0sXG4gICAgICBib2R5OiBKU09OLnN0cmluZ2lmeSh7IGFydGljbGVfaWRzOiBpZHMsIGlzX2RlbGV0ZWQ6IHRydWUgfSlcbiAgICB9KVxuXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XG4gICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XG4gICAgICAgIHNob3dBSUZpbHRlck1vZGFsLnZhbHVlID0gZmFsc2VcbiAgICAgICAgYWlGaWx0ZXJBcnRpY2xlcy52YWx1ZSA9IFtdXG4gICAgICAgIGZldGNoQXJ0aWNsZXMoY3VycmVudFBhZ2UudmFsdWUpXG4gICAgICAgIGZldGNoU3RhdGlzdGljcygpXG4gICAgICB9IGVsc2Uge1xuICAgICAgICBjb25zb2xlLmVycm9yKCfmibnph4/liKDpmaTlpLHotKU6JywgcmVzdWx0Lm1zZyB8fCByZXN1bHQubWVzc2FnZSlcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgY29uc29sZS5lcnJvcign5om56YeP5Yig6Zmk5aSx6LSlOicsIHJlc3BvbnNlLnN0YXR1cylcbiAgICB9XG4gIH0gY2F0Y2ggKGUpIHtcbiAgICBjb25zb2xlLmVycm9yKCdBSei/h+a7pOWIoOmZpOWHuumUmTonLCBlKVxuICB9IGZpbmFsbHkge1xuICAgIGFpRmlsdGVyRGVsZXRpbmcudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOagvOW8j+WMluaXpeacn1xuY29uc3QgZm9ybWF0RGF0ZSA9IChkYXRlU3RyKSA9PiB7XG4gIGlmICghZGF0ZVN0cikgcmV0dXJuICcnXG4gIGNvbnN0IGRhdGUgPSBuZXcgRGF0ZShkYXRlU3RyKVxuICBjb25zdCBtb250aCA9IChkYXRlLmdldE1vbnRoKCkgKyAxKS50b1N0cmluZygpLnBhZFN0YXJ0KDIsICcwJylcbiAgY29uc3QgZGF5ID0gZGF0ZS5nZXREYXRlKCkudG9TdHJpbmcoKS5wYWRTdGFydCgyLCAnMCcpXG4gIHJldHVybiBgJHtkYXRlLmdldEZ1bGxZZWFyKCl9LSR7bW9udGh9LSR7ZGF5fWBcbn1cblxuLy8g5qC85byP5YyW5YaF5a656ZW/5bqmXG5jb25zdCBmb3JtYXRDb250ZW50TGVuZ3RoID0gKGxlbmd0aCkgPT4ge1xuICBpZiAoIWxlbmd0aCkgcmV0dXJuICcnXG4gIGlmIChsZW5ndGggPCAxMDAwKSB7XG4gICAgcmV0dXJuIGAke2xlbmd0aH3lrZdgXG4gIH0gZWxzZSB7XG4gICAgcmV0dXJuIGAkeyhsZW5ndGggLyAxMDAwKS50b0ZpeGVkKDEpfWvlrZdgXG4gIH1cbn1cblxuLy8gS0lNSSDor4TliIblvr3nq6A6IOaMiSBSRUQvWUVMTE9XIOWJjee8gCArIOWIhuaVsOaho+S9jei/lOWbniBjbGFzc1xuLy8g5ZCO56uvIHJlYXNvbiDlrZfmrrXnuqblrpo6IFtSRURdIC8gW1lFTExPV10gLyDml6DliY3nvIAgKOe7vykg4oCUIOingSBzYXZlX2tpbWlfc2NvcmVzKClcbmNvbnN0IGdldEtpbWlCYWRnZUNsYXNzID0gKGFydGljbGUpID0+IHtcbiAgY29uc3QgcmVhc29uID0gYXJ0aWNsZS5raW1pX3BpY2tfcmVhc29uIHx8ICcnXG4gIGlmIChyZWFzb24uc3RhcnRzV2l0aCgnW1JFRF0nKSkgcmV0dXJuICdraW1pLXJlZCdcbiAgaWYgKHJlYXNvbi5zdGFydHNXaXRoKCdbWUVMTE9XXScpKSByZXR1cm4gJ2tpbWkteWVsbG93J1xuICBjb25zdCBzID0gTnVtYmVyKGFydGljbGUua2ltaV9waWNrX3Njb3JlKSB8fCAwXG4gIGlmIChzID49IDYwKSByZXR1cm4gJ2tpbWktaGlnaCdcbiAgaWYgKHMgPj0gMzApIHJldHVybiAna2ltaS1taWQnXG4gIHJldHVybiAna2ltaS1sb3cnXG59XG5cbi8vIGhvdmVyIOeci+WIsOeahOWujOaVtCB0b29sdGlwOiDnkIbnlLHlhajmlocgKyDor4TliIbml7bpl7RcbmNvbnN0IGdldEtpbWlUb29sdGlwID0gKGFydGljbGUpID0+IHtcbiAgY29uc3QgcGFydHMgPSBbXVxuICBpZiAoYXJ0aWNsZS5raW1pX3BpY2tfcmVhc29uKSBwYXJ0cy5wdXNoKGFydGljbGUua2ltaV9waWNrX3JlYXNvbilcbiAgaWYgKGFydGljbGUua2ltaV9waWNrX3Njb3JlZF9hdCkge1xuICAgIHBhcnRzLnB1c2goYCjor4TliIbml7bpl7Q6ICR7YXJ0aWNsZS5raW1pX3BpY2tfc2NvcmVkX2F0LnJlcGxhY2UoJ1QnLCAnICcpLnNsaWNlKDAsIDE2KX0pYClcbiAgfVxuICByZXR1cm4gcGFydHMuam9pbignICcpXG59XG5cbi8vIOWIl+ihqOS4iuaYvuekuueahOeugOefreeQhueUsSAo5YmNIDE4IOWtlywg5Y675o6JIFtSRURdL1tZRUxMT1ddIOWJjee8gClcbmNvbnN0IGdldEtpbWlSZWFzb25TaG9ydCA9IChhcnRpY2xlKSA9PiB7XG4gIGxldCByID0gYXJ0aWNsZS5raW1pX3BpY2tfcmVhc29uIHx8ICcnXG4gIHIgPSByLnJlcGxhY2UoL15cXFsoUkVEfFlFTExPVylcXF1cXHMqLywgJycpXG4gIGlmIChyLmxlbmd0aCA+IDE4KSByID0gci5zbGljZSgwLCAxOCkgKyAn4oCmJ1xuICByZXR1cm4gclxufVxuXG4vLyDojrflj5bnu5/orqHkv6Hmga9cbmNvbnN0IGZldGNoU3RhdGlzdGljcyA9IGFzeW5jICgpID0+IHtcbiAgdHJ5IHtcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L3N0YXRpc3RpY3NgKVxuICAgIFxuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBzdGF0aXN0aWNzLnZhbHVlID0gcmVzdWx0LmRhdGFcbiAgICAgIH1cbiAgICB9XG4gIH0gY2F0Y2ggKGVycm9yKSB7XG4gICAgY29uc29sZS5lcnJvcign6I635Y+W57uf6K6h5L+h5oGv5Ye66ZSZOicsIGVycm9yKVxuICB9XG59XG5cbi8vIOiuvue9rueKtuaAgeetm+mAiVxuLy8g55uR5ZCsIHN0YXR1c0ZpbHRlciDlj5jljJbvvIzlkIzmraXliLAgZmlsdGVyU2VsZWN0ZWQvZmlsdGVyUmVqZWN0ZWRcbndhdGNoKHN0YXR1c0ZpbHRlciwgKHN0YXR1cykgPT4ge1xuICBpZiAoc3RhdHVzID09PSAncGVuZGluZycpIHtcbiAgICBmaWx0ZXJTZWxlY3RlZC52YWx1ZSA9IGZhbHNlXG4gICAgZmlsdGVyUmVqZWN0ZWQudmFsdWUgPSBudWxsXG4gIH0gZWxzZSBpZiAoc3RhdHVzID09PSAnc2VsZWN0ZWQnKSB7XG4gICAgZmlsdGVyU2VsZWN0ZWQudmFsdWUgPSB0cnVlXG4gICAgZmlsdGVyUmVqZWN0ZWQudmFsdWUgPSBudWxsXG4gIH0gZWxzZSBpZiAoc3RhdHVzID09PSAnZGVsZXRlZCcpIHtcbiAgICBmaWx0ZXJTZWxlY3RlZC52YWx1ZSA9IG51bGxcbiAgICBmaWx0ZXJSZWplY3RlZC52YWx1ZSA9IHRydWVcbiAgfVxufSlcblxuLy8g55uR5ZCs562b6YCJ5p2h5Lu25Y+Y5YyW77yM5ZCM5pe25pu05pawIFVSTFxud2F0Y2goW3N0YXR1c0ZpbHRlciwgZmlsdGVyUGxhdGZvcm0sIGZpbHRlclRhZywgc29ydEJ5XSwgKCkgPT4ge1xuICAvLyDnrZvpgInmnaHku7blj5jljJbml7bmuIXnqbrpgInkuK3nirbmgIFcbiAgc2VsZWN0ZWRBcnRpY2xlSWRzLnZhbHVlLmNsZWFyKClcbiAgXG4gIC8vIOabtOaWsCBVUkwg5Y+C5pWwXG4gIGNvbnN0IHF1ZXJ5ID0ge31cbiAgcXVlcnkuc3RhdHVzID0gc3RhdHVzRmlsdGVyLnZhbHVlXG4gIGlmIChmaWx0ZXJQbGF0Zm9ybS52YWx1ZSkge1xuICAgIHF1ZXJ5LnBsYXRmb3JtID0gZmlsdGVyUGxhdGZvcm0udmFsdWVcbiAgfVxuICBpZiAoZmlsdGVyVGFnLnZhbHVlKSB7XG4gICAgcXVlcnkudGFnID0gZmlsdGVyVGFnLnZhbHVlXG4gIH1cbiAgaWYgKHNvcnRCeS52YWx1ZSAhPT0gJ3B1Ymxpc2hlZF9hdCcpIHtcbiAgICBxdWVyeS5zb3J0ID0gc29ydEJ5LnZhbHVlXG4gIH1cbiAgaWYgKHNlYXJjaEtleXdvcmQudmFsdWUgJiYgc2VhcmNoS2V5d29yZC52YWx1ZS50cmltKCkpIHtcbiAgICBxdWVyeS5zZWFyY2ggPSBzZWFyY2hLZXl3b3JkLnZhbHVlLnRyaW0oKVxuICB9XG4gIHJvdXRlci5yZXBsYWNlKHsgcXVlcnkgfSlcbiAgXG4gIGZldGNoQXJ0aWNsZXMoMSlcbn0pXG5cbi8vIOebkeWQrOaQnOe0ouWFs+mUruivjeWPmOWMlu+8iOS7jiBTZWFyY2hCb3gg57uE5Lu26YCa6L+HIFVSTCDkvKDlhaXvvIlcbndhdGNoKCgpID0+IHJvdXRlLnF1ZXJ5LnNlYXJjaCwgKG5ld1NlYXJjaCkgPT4ge1xuICBjb25zdCBuZXdLZXl3b3JkID0gbmV3U2VhcmNoIHx8ICcnXG4gIGlmIChzZWFyY2hLZXl3b3JkLnZhbHVlICE9PSBuZXdLZXl3b3JkKSB7XG4gICAgc2VhcmNoS2V5d29yZC52YWx1ZSA9IG5ld0tleXdvcmRcbiAgICBmZXRjaEFydGljbGVzKDEpXG4gIH1cbn0pXG5cbi8vIOeUn+aIkOagh+mimFxuY29uc3QgZ2VuZXJhdGVUaXRsZSA9IGFzeW5jICgpID0+IHtcbiAgaWYgKCFuZXdBcnRpY2xlLnZhbHVlLmNvbnRlbnQgfHwgZ2VuZXJhdGluZ1RpdGxlLnZhbHVlKSByZXR1cm5cbiAgXG4gIGdlbmVyYXRpbmdUaXRsZS52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzL2dlbmVyYXRlLXRpdGxlYCwge1xuICAgICAgbWV0aG9kOiAnUE9TVCcsXG4gICAgICBoZWFkZXJzOiB7XG4gICAgICAgICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbidcbiAgICAgIH0sXG4gICAgICBib2R5OiBKU09OLnN0cmluZ2lmeSh7XG4gICAgICAgIGNvbnRlbnQ6IG5ld0FydGljbGUudmFsdWUuY29udGVudFxuICAgICAgfSlcbiAgICB9KVxuICAgIFxuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBuZXdBcnRpY2xlLnZhbHVlLnRpdGxlID0gcmVzdWx0LmRhdGE/LnRpdGxlIHx8ICcnXG4gICAgICB9IGVsc2Uge1xuICAgICAgICBhbGVydCgn55Sf5oiQ5qCH6aKY5aSx6LSlOiAnICsgKHJlc3VsdC5tc2cgfHwgcmVzdWx0Lm1lc3NhZ2UpKVxuICAgICAgfVxuICAgIH0gZWxzZSB7XG4gICAgICBhbGVydCgn55Sf5oiQ5qCH6aKY5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgICB9XG4gIH0gY2F0Y2ggKGVycm9yKSB7XG4gICAgY29uc29sZS5lcnJvcign55Sf5oiQ5qCH6aKY5Ye66ZSZOicsIGVycm9yKVxuICAgIGFsZXJ0KCfnlJ/miJDmoIfpopjlpLHotKXvvIzor7fnqI3lkI7ph43or5UnKVxuICB9IGZpbmFsbHkge1xuICAgIGdlbmVyYXRpbmdUaXRsZS52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cblxuLy8g5Yib5bu65paH56ugXG5jb25zdCBjcmVhdGVBcnRpY2xlID0gYXN5bmMgKCkgPT4ge1xuICBpZiAoIW5ld0FydGljbGUudmFsdWUuY29udGVudCB8fCBjcmVhdGluZy52YWx1ZSkgcmV0dXJuXG4gIFxuICAvLyDoh7PlsJHpgInmi6nkuIDnp43liLbkvZznsbvlnotcbiAgaWYgKCFuZXdBcnRpY2xlLnZhbHVlLmNvbnRlbnRfdHlwZV9pbWFnZSAmJiAhbmV3QXJ0aWNsZS52YWx1ZS5jb250ZW50X3R5cGVfdmlkZW8pIHtcbiAgICBhbGVydCgn6K+36Iez5bCR6YCJ5oup5LiA56eN5Yi25L2c57G75Z6LICjlm77mlocg5oiWIOinhumikSknKVxuICAgIHJldHVyblxuICB9XG4gIFxuICBjcmVhdGluZy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBcbiAgICBsZXQgY29udGVudF90eXBlID0gJ2ltYWdlJ1xuICAgIGlmIChuZXdBcnRpY2xlLnZhbHVlLmNvbnRlbnRfdHlwZV9pbWFnZSAmJiBuZXdBcnRpY2xlLnZhbHVlLmNvbnRlbnRfdHlwZV92aWRlbykge1xuICAgICAgY29udGVudF90eXBlID0gJ2JvdGgnXG4gICAgfSBlbHNlIGlmIChuZXdBcnRpY2xlLnZhbHVlLmNvbnRlbnRfdHlwZV92aWRlbykge1xuICAgICAgY29udGVudF90eXBlID0gJ3ZpZGVvJ1xuICAgIH1cbiAgICBcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzYCwge1xuICAgICAgbWV0aG9kOiAnUE9TVCcsXG4gICAgICBoZWFkZXJzOiB7ICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgdGl0bGU6IG5ld0FydGljbGUudmFsdWUudGl0bGUgfHwgJycsXG4gICAgICAgIGNvbnRlbnQ6IG5ld0FydGljbGUudmFsdWUuY29udGVudCxcbiAgICAgICAgcGxhdGZvcm06ICdtYW51YWwnLFxuICAgICAgICBhY2NvdW50X3RhcmdldDogbmV3QXJ0aWNsZS52YWx1ZS5hY2NvdW50X3RhcmdldCB8fCAnQUknLFxuICAgICAgICBjb250ZW50X3R5cGU6IGNvbnRlbnRfdHlwZSxcbiAgICAgICAgaXNfc2VsZWN0ZWQ6IDFcbiAgICAgIH0pXG4gICAgfSlcbiAgICBcbiAgICBsZXQgb2sgPSBmYWxzZVxuICAgIGxldCBlcnJNc2cgPSAnJ1xuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBvayA9IHRydWVcbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIGVyck1zZyA9IHJlc3VsdC5tc2cgfHwgcmVzdWx0Lm1lc3NhZ2UgfHwgJ+acquefpemUmeivrydcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgZXJyTXNnID0gYOivt+axguWksei0pTogJHtyZXNwb25zZS5zdGF0dXN9YFxuICAgIH1cbiAgICBcbiAgICBpZiAob2spIHtcbiAgICAgIG5ld0FydGljbGUudmFsdWUgPSB7XG4gICAgICAgIHRpdGxlOiAnJyxcbiAgICAgICAgY29udGVudDogJycsXG4gICAgICAgIHBsYXRmb3JtOiAnbWFudWFsJyxcbiAgICAgICAgYWNjb3VudF90YXJnZXQ6ICdBSScsXG4gICAgICAgIGNvbnRlbnRfdHlwZV9pbWFnZTogdHJ1ZSxcbiAgICAgICAgY29udGVudF90eXBlX3ZpZGVvOiBmYWxzZSxcbiAgICAgIH1cbiAgICAgIGNsb3NlQ3JlYXRlTW9kYWwoKVxuICAgICAgZmV0Y2hBcnRpY2xlcyhjdXJyZW50UGFnZS52YWx1ZSlcbiAgICAgIGZldGNoU3RhdGlzdGljcygpXG4gICAgfSBlbHNlIHtcbiAgICAgIGFsZXJ0KCfliJvlu7rlpLHotKU6ICcgKyBlcnJNc2cpXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+WIm+W7uuaWh+eroOWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn5Yib5bu65aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfSBmaW5hbGx5IHtcbiAgICBjcmVhdGluZy52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cblxuLy8g5pi+56S65paH56ug5YaF5a6577yI57yW6L6R5qih5byP77yJXG5jb25zdCBzaG93QXJ0aWNsZUNvbnRlbnQgPSBhc3luYyAoYXJ0aWNsZSkgPT4ge1xuICB2aWV3aW5nQXJ0aWNsZS52YWx1ZSA9IGFydGljbGVcbiAgc2hvd0NvbnRlbnRNb2RhbC52YWx1ZSA9IHRydWVcbiAgZWRpdGluZ0FydGljbGUudmFsdWUgPSB7XG4gICAgaWQ6IGFydGljbGUuaWQsXG4gICAgdGl0bGU6IGFydGljbGUudGl0bGUgfHwgJycsXG4gICAgY29udGVudDogJycsXG4gICAgdXJsOiBhcnRpY2xlLnVybCB8fCAnJyxcbiAgICBjb250ZW50X3R5cGU6IGFydGljbGUuY29udGVudF90eXBlIHx8IG51bGwsXG4gICAgaXNfc2VsZWN0ZWQ6IGFydGljbGUuaXNfc2VsZWN0ZWQgfHwgZmFsc2VcbiAgfVxuICBsb2FkaW5nQXJ0aWNsZUNvbnRlbnQudmFsdWUgPSB0cnVlXG4gIFxuICB0cnkge1xuICAgIC8vIOWmguaenOaWh+eroOW3sue7j+aciSBjb250ZW50IOWtl+aute+8jOebtOaOpeS9v+eUqFxuICAgIGlmIChhcnRpY2xlLmNvbnRlbnQpIHtcbiAgICAgIGVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnQgPSBhcnRpY2xlLmNvbnRlbnRcbiAgICAgIGxvYWRpbmdBcnRpY2xlQ29udGVudC52YWx1ZSA9IGZhbHNlXG4gICAgICByZXR1cm5cbiAgICB9XG4gICAgXG4gICAgLy8g5ZCm5YiZ5LuOIEFQSSDojrflj5bmlofnq6Dor6bmg4VcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzLyR7YXJ0aWNsZS5pZH1gKVxuICAgIFxuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5jb250ZW50ID0gcmVzdWx0LmRhdGE/LmNvbnRlbnQgfHwgJydcbiAgICAgICAgZWRpdGluZ0FydGljbGUudmFsdWUudGl0bGUgPSByZXN1bHQuZGF0YT8udGl0bGUgfHwgYXJ0aWNsZS50aXRsZSB8fCAnJ1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+iOt+WPluWGheWuueWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKSlcbiAgICAgICAgc2hvd0NvbnRlbnRNb2RhbC52YWx1ZSA9IGZhbHNlXG4gICAgICB9XG4gICAgfSBlbHNlIHtcbiAgICAgIGFsZXJ0KCfojrflj5blhoXlrrnlpLHotKXvvIzor7fnqI3lkI7ph43or5UnKVxuICAgICAgc2hvd0NvbnRlbnRNb2RhbC52YWx1ZSA9IGZhbHNlXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+iOt+WPluaWh+eroOWGheWuueWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn6I635Y+W5YaF5a655aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgICBzaG93Q29udGVudE1vZGFsLnZhbHVlID0gZmFsc2VcbiAgfSBmaW5hbGx5IHtcbiAgICBsb2FkaW5nQXJ0aWNsZUNvbnRlbnQudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOWFs+mXree8lui+keaooeaAgeahhlxuY29uc3QgY2xvc2VFZGl0TW9kYWwgPSAoKSA9PiB7XG4gIHNob3dDb250ZW50TW9kYWwudmFsdWUgPSBmYWxzZVxuICBlZGl0aW5nQXJ0aWNsZS52YWx1ZSA9IHsgaWQ6ICcnLCB0aXRsZTogJycsIGNvbnRlbnQ6ICcnLCB1cmw6ICcnIH1cbn1cblxuLy8g5YWz6Zet5paw5bu65qih5oCB5qGGXG5jb25zdCBjbG9zZUNyZWF0ZU1vZGFsID0gKCkgPT4ge1xuICBzaG93Q3JlYXRlTW9kYWwudmFsdWUgPSBmYWxzZVxuICBuZXdBcnRpY2xlLnZhbHVlID0geyBcbiAgICB0aXRsZTogJycsIFxuICAgIGNvbnRlbnQ6ICcnLCBcbiAgICBwbGF0Zm9ybTogJ21hbnVhbCcsIFxuICAgIGFjY291bnRfdGFyZ2V0OiAnQUknLFxuICAgIGNvbnRlbnRfdHlwZV9pbWFnZTogdHJ1ZSxcbiAgICBjb250ZW50X3R5cGVfdmlkZW86IGZhbHNlLFxuICB9XG59XG5cbi8vIOS4uue8lui+keaooeW8j+eUn+aIkOagh+mimFxuY29uc3QgZ2VuZXJhdGVUaXRsZUZvckVkaXQgPSBhc3luYyAoKSA9PiB7XG4gIGlmICghZWRpdGluZ0FydGljbGUudmFsdWUuY29udGVudCB8fCBnZW5lcmF0aW5nVGl0bGUudmFsdWUpIHJldHVyblxuICBcbiAgZ2VuZXJhdGluZ1RpdGxlLnZhbHVlID0gdHJ1ZVxuICB0cnkge1xuICAgIGNvbnN0IGFwaVVybCA9IEFQSV9CQVNFX1VSTFxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goYCR7YXBpVXJsfS9hcGkvemhpaHUvYXJ0aWNsZXMvZ2VuZXJhdGUtdGl0bGVgLCB7XG4gICAgICBtZXRob2Q6ICdQT1NUJyxcbiAgICAgIGhlYWRlcnM6IHtcbiAgICAgICAgJ0NvbnRlbnQtVHlwZSc6ICdhcHBsaWNhdGlvbi9qc29uJ1xuICAgICAgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgY29udGVudDogZWRpdGluZ0FydGljbGUudmFsdWUuY29udGVudFxuICAgICAgfSlcbiAgICB9KVxuICAgIFxuICAgIGlmIChyZXNwb25zZS5vaykge1xuICAgICAgY29uc3QgcmVzdWx0ID0gYXdhaXQgcmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAocmVzdWx0LmNvZGUgPT09IDAgfHwgcmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICBlZGl0aW5nQXJ0aWNsZS52YWx1ZS50aXRsZSA9IHJlc3VsdC5kYXRhPy50aXRsZSB8fCAnJ1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+eUn+aIkOagh+mimOWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKSlcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgYWxlcnQoJ+eUn+aIkOagh+mimOWksei0pe+8jOivt+eojeWQjumHjeivlScpXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+eUn+aIkOagh+mimOWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn55Sf5oiQ5qCH6aKY5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfSBmaW5hbGx5IHtcbiAgICBnZW5lcmF0aW5nVGl0bGUudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOmHjeaWsOmHh+mbhuaWh+eroOWGheWuuVxuY29uc3QgcmVjcmF3bEFydGljbGUgPSBhc3luYyAoKSA9PiB7XG4gIGlmICghdmlld2luZ0FydGljbGUudmFsdWUgfHwgcmVjcmF3bGluZy52YWx1ZSkgcmV0dXJuXG4gIFxuICByZWNyYXdsaW5nLnZhbHVlID0gdHJ1ZVxuICB0cnkge1xuICAgIGNvbnN0IGFwaVVybCA9IEFQSV9CQVNFX1VSTFxuICAgIGNvbnN0IHJlc3BvbnNlID0gYXdhaXQgZmV0Y2goYCR7YXBpVXJsfS9hcGkvemhpaHUvYXJ0aWNsZXMvJHt2aWV3aW5nQXJ0aWNsZS52YWx1ZS5pZH0vcmVjcmF3bGAsIHtcbiAgICAgIG1ldGhvZDogJ1BPU1QnLFxuICAgICAgaGVhZGVyczoge1xuICAgICAgICAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nXG4gICAgICB9XG4gICAgfSlcbiAgICBcbiAgICBpZiAocmVzcG9uc2Uub2spIHtcbiAgICAgIGNvbnN0IHJlc3VsdCA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKVxuICAgICAgaWYgKHJlc3VsdC5jb2RlID09PSAwIHx8IHJlc3VsdC5jb2RlID09PSAyMDApIHtcbiAgICAgICAgLy8g5pu05paw57yW6L6R5qGG5Lit55qE5YaF5a65XG4gICAgICAgIGVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnQgPSByZXN1bHQuZGF0YT8uY29udGVudCB8fCAnJ1xuICAgICAgICBlZGl0aW5nQXJ0aWNsZS52YWx1ZS50aXRsZSA9IHJlc3VsdC5kYXRhPy50aXRsZSB8fCBlZGl0aW5nQXJ0aWNsZS52YWx1ZS50aXRsZVxuICAgICAgICBcbiAgICAgICAgLy8g5pu05paw5pys5Zyw5YiX6KGo5Lit55qE5paH56ugXG4gICAgICAgIGNvbnN0IGFydGljbGVJbmRleCA9IGFydGljbGVzLnZhbHVlLmZpbmRJbmRleChhID0+IGEuaWQgPT09IHZpZXdpbmdBcnRpY2xlLnZhbHVlLmlkKVxuICAgICAgICBpZiAoYXJ0aWNsZUluZGV4ICE9PSAtMSkge1xuICAgICAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0uY29udGVudCA9IHJlc3VsdC5kYXRhPy5jb250ZW50IHx8ICcnXG4gICAgICAgICAgYXJ0aWNsZXMudmFsdWVbYXJ0aWNsZUluZGV4XS5jb250ZW50X2xlbmd0aCA9IHJlc3VsdC5kYXRhPy5jb250ZW50X2xlbmd0aCB8fCAwXG4gICAgICAgICAgaWYgKHJlc3VsdC5kYXRhPy5wdWJsaXNoZWRfYXQpIHtcbiAgICAgICAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0ucHVibGlzaGVkX2F0ID0gcmVzdWx0LmRhdGEucHVibGlzaGVkX2F0XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICAgIC8vIOaIkOWKn+aXtuS4jeW8ueeql++8jOWGheWuueW3suiHquWKqOabtOaWsOWIsOe8lui+keahhlxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+mHjeaWsOmHh+mbhuWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKSlcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgYWxlcnQoJ+mHjeaWsOmHh+mbhuWksei0pe+8jOivt+eojeWQjumHjeivlScpXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+mHjeaWsOmHh+mbhuWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn6YeN5paw6YeH6ZuG5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfSBmaW5hbGx5IHtcbiAgICByZWNyYXdsaW5nLnZhbHVlID0gZmFsc2VcbiAgfVxufVxuXG4vLyDkv53lrZjmlofnq6BcbmNvbnN0IHNhdmVBcnRpY2xlID0gYXN5bmMgKCkgPT4ge1xuICBpZiAoIWVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnQgfHwgc2F2aW5nLnZhbHVlKSByZXR1cm5cbiAgXG4gIHNhdmluZy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzLyR7ZWRpdGluZ0FydGljbGUudmFsdWUuaWR9YCwge1xuICAgICAgbWV0aG9kOiAnUFVUJyxcbiAgICAgIGhlYWRlcnM6IHtcbiAgICAgICAgJ0NvbnRlbnQtVHlwZSc6ICdhcHBsaWNhdGlvbi9qc29uJ1xuICAgICAgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgdGl0bGU6IGVkaXRpbmdBcnRpY2xlLnZhbHVlLnRpdGxlIHx8ICcnLFxuICAgICAgICBjb250ZW50OiBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5jb250ZW50XG4gICAgICB9KVxuICAgIH0pXG4gICAgXG4gICAgaWYgKHJlc3BvbnNlLm9rKSB7XG4gICAgICBjb25zdCByZXN1bHQgPSBhd2FpdCByZXNwb25zZS5qc29uKClcbiAgICAgIGlmIChyZXN1bHQuY29kZSA9PT0gMCB8fCByZXN1bHQuY29kZSA9PT0gMjAwKSB7XG4gICAgICAgIC8vIOabtOaWsOacrOWcsOWIl+ihqOS4reeahOaWh+eroFxuICAgICAgICBjb25zdCBhcnRpY2xlSW5kZXggPSBhcnRpY2xlcy52YWx1ZS5maW5kSW5kZXgoYSA9PiBhLmlkID09PSBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5pZClcbiAgICAgICAgaWYgKGFydGljbGVJbmRleCAhPT0gLTEpIHtcbiAgICAgICAgICBhcnRpY2xlcy52YWx1ZVthcnRpY2xlSW5kZXhdLnRpdGxlID0gZWRpdGluZ0FydGljbGUudmFsdWUudGl0bGVcbiAgICAgICAgICBhcnRpY2xlcy52YWx1ZVthcnRpY2xlSW5kZXhdLmNvbnRlbnQgPSBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5jb250ZW50XG4gICAgICAgIH1cbiAgICAgICAgLy8g5pi+56S65L+d5a2Y5oiQ5Yqf5o+Q56S677yM5LiN5YWz6Zet5by556qXXG4gICAgICAgIHNhdmVTdWNjZXNzLnZhbHVlID0gdHJ1ZVxuICAgICAgICBzZXRUaW1lb3V0KCgpID0+IHsgc2F2ZVN1Y2Nlc3MudmFsdWUgPSBmYWxzZSB9LCAyMDAwKVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+S/neWtmOWksei0pTogJyArIChyZXN1bHQubXNnIHx8IHJlc3VsdC5tZXNzYWdlKSlcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgYWxlcnQoJ+S/neWtmOWksei0pe+8jOivt+eojeWQjumHjeivlScpXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+S/neWtmOaWh+eroOWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn5L+d5a2Y5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfSBmaW5hbGx5IHtcbiAgICBzYXZpbmcudmFsdWUgPSBmYWxzZVxuICB9XG59XG5cbi8vIOS/neWtmOW5tuWItuS9nO+8iOS/neWtmOaWh+eroOWQjuiuvue9ruS4uumAieS4reeKtuaAge+8jOinhumikeexu+Wei++8jOebruagh+i0puWPt0FJ77yJXG5jb25zdCBzYXZlQW5kU2VsZWN0ID0gYXN5bmMgKCkgPT4ge1xuICBpZiAoIWVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnQgfHwgc2F2aW5nQW5kU2VsZWN0aW5nLnZhbHVlKSByZXR1cm5cbiAgXG4gIHNhdmluZ0FuZFNlbGVjdGluZy52YWx1ZSA9IHRydWVcbiAgdHJ5IHtcbiAgICBjb25zdCBhcGlVcmwgPSBBUElfQkFTRV9VUkxcbiAgICBcbiAgICAvLyDnrKzkuIDmraXvvJrkv53lrZjmlofnq6DlhoXlrrlcbiAgICBjb25zdCBzYXZlUmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcy8ke2VkaXRpbmdBcnRpY2xlLnZhbHVlLmlkfWAsIHtcbiAgICAgIG1ldGhvZDogJ1BVVCcsXG4gICAgICBoZWFkZXJzOiB7XG4gICAgICAgICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbidcbiAgICAgIH0sXG4gICAgICBib2R5OiBKU09OLnN0cmluZ2lmeSh7XG4gICAgICAgIHRpdGxlOiBlZGl0aW5nQXJ0aWNsZS52YWx1ZS50aXRsZSB8fCAnJyxcbiAgICAgICAgY29udGVudDogZWRpdGluZ0FydGljbGUudmFsdWUuY29udGVudFxuICAgICAgfSlcbiAgICB9KVxuICAgIFxuICAgIGlmICghc2F2ZVJlc3BvbnNlLm9rKSB7XG4gICAgICBhbGVydCgn5L+d5a2Y5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgICAgIHJldHVyblxuICAgIH1cbiAgICBcbiAgICBjb25zdCBzYXZlUmVzdWx0ID0gYXdhaXQgc2F2ZVJlc3BvbnNlLmpzb24oKVxuICAgIGlmIChzYXZlUmVzdWx0LmNvZGUgIT09IDAgJiYgc2F2ZVJlc3VsdC5jb2RlICE9PSAyMDApIHtcbiAgICAgIGFsZXJ0KCfkv53lrZjlpLHotKU6ICcgKyAoc2F2ZVJlc3VsdC5tc2cgfHwgc2F2ZVJlc3VsdC5tZXNzYWdlKSlcbiAgICAgIHJldHVyblxuICAgIH1cbiAgICBcbiAgICAvLyDmm7TmlrDmnKzlnLDliJfooajkuK3nmoTmlofnq6BcbiAgICBjb25zdCBhcnRpY2xlSW5kZXggPSBhcnRpY2xlcy52YWx1ZS5maW5kSW5kZXgoYSA9PiBhLmlkID09PSBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5pZClcbiAgICBpZiAoYXJ0aWNsZUluZGV4ICE9PSAtMSkge1xuICAgICAgYXJ0aWNsZXMudmFsdWVbYXJ0aWNsZUluZGV4XS50aXRsZSA9IGVkaXRpbmdBcnRpY2xlLnZhbHVlLnRpdGxlXG4gICAgICBhcnRpY2xlcy52YWx1ZVthcnRpY2xlSW5kZXhdLmNvbnRlbnQgPSBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5jb250ZW50XG4gICAgfVxuICAgIFxuICAgIC8vIOesrOS6jOatpe+8muiuvue9ruS4uumAieS4reeKtuaAge+8iGlzX3NlbGVjdGVkPXRydWUsIGNvbnRlbnRfdHlwZT12aWRlbywgYWNjb3VudF90YXJnZXTmoLnmja7lvZPliY3moIfnrb7noa7lrprvvIlcbiAgICBjb25zdCB0YXJnZXRBY2NvdW50ID0gZ2V0QWNjb3VudFRhcmdldCgpXG4gICAgY29uc3Qgc2VsZWN0UmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcy8ke2VkaXRpbmdBcnRpY2xlLnZhbHVlLmlkfS9zZWxlY3RgLCB7XG4gICAgICBtZXRob2Q6ICdQVVQnLFxuICAgICAgaGVhZGVyczoge1xuICAgICAgICAnQ29udGVudC1UeXBlJzogJ2FwcGxpY2F0aW9uL2pzb24nXG4gICAgICB9LFxuICAgICAgYm9keTogSlNPTi5zdHJpbmdpZnkoe1xuICAgICAgICBpc19zZWxlY3RlZDogdHJ1ZSxcbiAgICAgICAgY29udGVudF90eXBlOiAndmlkZW8nLFxuICAgICAgICBhY2NvdW50X3RhcmdldDogdGFyZ2V0QWNjb3VudFxuICAgICAgfSlcbiAgICB9KVxuICAgIFxuICAgIGlmIChzZWxlY3RSZXNwb25zZS5vaykge1xuICAgICAgY29uc3Qgc2VsZWN0UmVzdWx0ID0gYXdhaXQgc2VsZWN0UmVzcG9uc2UuanNvbigpXG4gICAgICBpZiAoc2VsZWN0UmVzdWx0LmNvZGUgPT09IDAgfHwgc2VsZWN0UmVzdWx0LmNvZGUgPT09IDIwMCkge1xuICAgICAgICAvLyDmm7TmlrDmnKzlnLDnirbmgIFcbiAgICAgICAgaWYgKGFydGljbGVJbmRleCAhPT0gLTEpIHtcbiAgICAgICAgICBhcnRpY2xlcy52YWx1ZVthcnRpY2xlSW5kZXhdLmlzX3NlbGVjdGVkID0gdHJ1ZVxuICAgICAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0uY29udGVudF90eXBlID0gJ3ZpZGVvJ1xuICAgICAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0uYWNjb3VudF90YXJnZXQgPSB0YXJnZXRBY2NvdW50XG4gICAgICAgIH1cbiAgICAgICAgXG4gICAgICAgIC8vIOWIt+aWsOe7n+iuoeS/oeaBr1xuICAgICAgICBmZXRjaFN0YXRpc3RpY3MoKVxuICAgICAgICBcbiAgICAgICAgLy8g5aaC5p6c5b2T5YmN5pivXCLlvoXlrqHmoLhcIuWIl+ihqO+8jOS7juWIl+ihqOS4reenu+mZpOivpeaWh+eroFxuICAgICAgICBpZiAoc3RhdHVzRmlsdGVyLnZhbHVlID09PSAncGVuZGluZycpIHtcbiAgICAgICAgICBhcnRpY2xlcy52YWx1ZSA9IGFydGljbGVzLnZhbHVlLmZpbHRlcihhID0+IGEuaWQgIT09IGVkaXRpbmdBcnRpY2xlLnZhbHVlLmlkKVxuICAgICAgICB9XG4gICAgICAgIFxuICAgICAgICBjbG9zZUVkaXRNb2RhbCgpXG4gICAgICB9IGVsc2Uge1xuICAgICAgICBhbGVydCgn6K6+572u5Yi25L2c54q25oCB5aSx6LSlOiAnICsgKHNlbGVjdFJlc3VsdC5tc2cgfHwgc2VsZWN0UmVzdWx0Lm1lc3NhZ2UpKVxuICAgICAgfVxuICAgIH0gZWxzZSB7XG4gICAgICBhbGVydCgn6K6+572u5Yi25L2c54q25oCB5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgICB9XG4gIH0gY2F0Y2ggKGVycm9yKSB7XG4gICAgY29uc29sZS5lcnJvcign5L+d5a2Y5bm25Yi25L2c5Ye66ZSZOicsIGVycm9yKVxuICAgIGFsZXJ0KCfmk43kvZzlpLHotKXvvIzor7fnqI3lkI7ph43or5UnKVxuICB9IGZpbmFsbHkge1xuICAgIHNhdmluZ0FuZFNlbGVjdGluZy52YWx1ZSA9IGZhbHNlXG4gIH1cbn1cblxuLy8g5a6J5o6S5Yi25L2c57G75Z6LICjop4bpopEgLyDlm77mlocpXG5jb25zdCBhcnJhbmdlVHlwZSA9IGFzeW5jICh0eXBlKSA9PiB7XG4gIGlmICghZWRpdGluZ0FydGljbGUudmFsdWUuY29udGVudCB8fCBhcnJhbmdpbmdUeXBlLnZhbHVlKSByZXR1cm5cbiAgXG4gIGFycmFuZ2luZ1R5cGUudmFsdWUgPSB0eXBlXG4gIHRyeSB7XG4gICAgY29uc3QgYXBpVXJsID0gQVBJX0JBU0VfVVJMXG4gICAgXG4gICAgLy8g56ys5LiA5q2lOiDkv53lrZjmlofnq6DlhoXlrrlcbiAgICBjb25zdCBzYXZlUmVzcG9uc2UgPSBhd2FpdCBmZXRjaChgJHthcGlVcmx9L2FwaS96aGlodS9hcnRpY2xlcy8ke2VkaXRpbmdBcnRpY2xlLnZhbHVlLmlkfWAsIHtcbiAgICAgIG1ldGhvZDogJ1BVVCcsXG4gICAgICBoZWFkZXJzOiB7ICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgdGl0bGU6IGVkaXRpbmdBcnRpY2xlLnZhbHVlLnRpdGxlIHx8ICcnLFxuICAgICAgICBjb250ZW50OiBlZGl0aW5nQXJ0aWNsZS52YWx1ZS5jb250ZW50XG4gICAgICB9KVxuICAgIH0pXG4gICAgXG4gICAgaWYgKCFzYXZlUmVzcG9uc2Uub2spIHtcbiAgICAgIGFsZXJ0KCfkv53lrZjlpLHotKXvvIzor7fnqI3lkI7ph43or5UnKVxuICAgICAgcmV0dXJuXG4gICAgfVxuICAgIFxuICAgIGNvbnN0IGFydGljbGVJbmRleCA9IGFydGljbGVzLnZhbHVlLmZpbmRJbmRleChhID0+IGEuaWQgPT09IGVkaXRpbmdBcnRpY2xlLnZhbHVlLmlkKVxuICAgIGlmIChhcnRpY2xlSW5kZXggIT09IC0xKSB7XG4gICAgICBhcnRpY2xlcy52YWx1ZVthcnRpY2xlSW5kZXhdLnRpdGxlID0gZWRpdGluZ0FydGljbGUudmFsdWUudGl0bGVcbiAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0uY29udGVudCA9IGVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnRcbiAgICB9XG4gICAgXG4gICAgLy8g56ys5LqM5q2lOiDmm7TmlrAgY29udGVudF90eXBlICjlt7Lnu4/lronmjpLkuoblj6bkuIDnp43lsLEgYm90aClcbiAgICBsZXQgbmV3Q29udGVudFR5cGUgPSB0eXBlXG4gICAgaWYgKHR5cGUgPT09ICd2aWRlbycgJiYgaXNBcnJhbmdlZEltYWdlLnZhbHVlKSB7XG4gICAgICBuZXdDb250ZW50VHlwZSA9ICdib3RoJ1xuICAgIH0gZWxzZSBpZiAodHlwZSA9PT0gJ2ltYWdlJyAmJiBpc0FycmFuZ2VkVmlkZW8udmFsdWUpIHtcbiAgICAgIG5ld0NvbnRlbnRUeXBlID0gJ2JvdGgnXG4gICAgfVxuICAgIFxuICAgIGNvbnN0IHRhcmdldEFjY291bnQgPSBnZXRBY2NvdW50VGFyZ2V0KClcbiAgICBjb25zdCBzZWxlY3RSZXNwb25zZSA9IGF3YWl0IGZldGNoKGAke2FwaVVybH0vYXBpL3poaWh1L2FydGljbGVzLyR7ZWRpdGluZ0FydGljbGUudmFsdWUuaWR9L3NlbGVjdGAsIHtcbiAgICAgIG1ldGhvZDogJ1BVVCcsXG4gICAgICBoZWFkZXJzOiB7ICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicgfSxcbiAgICAgIGJvZHk6IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgaXNfc2VsZWN0ZWQ6IHRydWUsXG4gICAgICAgIGNvbnRlbnRfdHlwZTogbmV3Q29udGVudFR5cGUsXG4gICAgICAgIGFjY291bnRfdGFyZ2V0OiB0YXJnZXRBY2NvdW50XG4gICAgICB9KVxuICAgIH0pXG4gICAgXG4gICAgaWYgKHNlbGVjdFJlc3BvbnNlLm9rKSB7XG4gICAgICBjb25zdCBzZWxlY3RSZXN1bHQgPSBhd2FpdCBzZWxlY3RSZXNwb25zZS5qc29uKClcbiAgICAgIGlmIChzZWxlY3RSZXN1bHQuY29kZSA9PT0gMCB8fCBzZWxlY3RSZXN1bHQuY29kZSA9PT0gMjAwKSB7XG4gICAgICAgIGVkaXRpbmdBcnRpY2xlLnZhbHVlLmNvbnRlbnRfdHlwZSA9IG5ld0NvbnRlbnRUeXBlXG4gICAgICAgIGVkaXRpbmdBcnRpY2xlLnZhbHVlLmlzX3NlbGVjdGVkID0gdHJ1ZVxuICAgICAgICBpZiAoYXJ0aWNsZUluZGV4ICE9PSAtMSkge1xuICAgICAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0uaXNfc2VsZWN0ZWQgPSB0cnVlXG4gICAgICAgICAgYXJ0aWNsZXMudmFsdWVbYXJ0aWNsZUluZGV4XS5jb250ZW50X3R5cGUgPSBuZXdDb250ZW50VHlwZVxuICAgICAgICAgIGFydGljbGVzLnZhbHVlW2FydGljbGVJbmRleF0uYWNjb3VudF90YXJnZXQgPSB0YXJnZXRBY2NvdW50XG4gICAgICAgIH1cbiAgICAgICAgXG4gICAgICAgIGZldGNoU3RhdGlzdGljcygpXG4gICAgICAgIFxuICAgICAgICBpZiAoc3RhdHVzRmlsdGVyLnZhbHVlID09PSAncGVuZGluZycpIHtcbiAgICAgICAgICBhcnRpY2xlcy52YWx1ZSA9IGFydGljbGVzLnZhbHVlLmZpbHRlcihhID0+IGEuaWQgIT09IGVkaXRpbmdBcnRpY2xlLnZhbHVlLmlkKVxuICAgICAgICAgIGNsb3NlRWRpdE1vZGFsKClcbiAgICAgICAgfVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgYWxlcnQoJ+WuieaOkuWksei0pTogJyArIChzZWxlY3RSZXN1bHQubXNnIHx8IHNlbGVjdFJlc3VsdC5tZXNzYWdlKSlcbiAgICAgICAgcmV0dXJuXG4gICAgICB9XG4gICAgfSBlbHNlIHtcbiAgICAgIGFsZXJ0KCflronmjpLlpLHotKXvvIzor7fnqI3lkI7ph43or5UnKVxuICAgICAgcmV0dXJuXG4gICAgfVxuICB9IGNhdGNoIChlcnJvcikge1xuICAgIGNvbnNvbGUuZXJyb3IoJ+WuieaOkuWItuS9nOWHuumUmTonLCBlcnJvcilcbiAgICBhbGVydCgn5pON5L2c5aSx6LSl77yM6K+356iN5ZCO6YeN6K+VJylcbiAgfSBmaW5hbGx5IHtcbiAgICBhcnJhbmdpbmdUeXBlLnZhbHVlID0gbnVsbFxuICB9XG59XG5cbm9uTW91bnRlZCgoKSA9PiB7XG4gIC8vIOS7jiBVUkwg5Yid5aeL5YyW562b6YCJ5p2h5Lu2XG4gIGlmIChyb3V0ZS5xdWVyeS5zdGF0dXMpIHtcbiAgICBzdGF0dXNGaWx0ZXIudmFsdWUgPSByb3V0ZS5xdWVyeS5zdGF0dXNcbiAgICAvLyDlkIzmraXliLAgZmlsdGVyU2VsZWN0ZWQvZmlsdGVyUmVqZWN0ZWRcbiAgICBpZiAocm91dGUucXVlcnkuc3RhdHVzID09PSAnc2VsZWN0ZWQnKSB7XG4gICAgICBmaWx0ZXJTZWxlY3RlZC52YWx1ZSA9IHRydWVcbiAgICAgIGZpbHRlclJlamVjdGVkLnZhbHVlID0gbnVsbFxuICAgIH0gZWxzZSBpZiAocm91dGUucXVlcnkuc3RhdHVzID09PSAnZGVsZXRlZCcpIHtcbiAgICAgIGZpbHRlclNlbGVjdGVkLnZhbHVlID0gbnVsbFxuICAgICAgZmlsdGVyUmVqZWN0ZWQudmFsdWUgPSB0cnVlXG4gICAgfSBlbHNlIHtcbiAgICAgIGZpbHRlclNlbGVjdGVkLnZhbHVlID0gZmFsc2VcbiAgICAgIGZpbHRlclJlamVjdGVkLnZhbHVlID0gbnVsbFxuICAgIH1cbiAgfVxuICBcbiAgaWYgKHJvdXRlLnF1ZXJ5LnBsYXRmb3JtKSB7XG4gICAgZmlsdGVyUGxhdGZvcm0udmFsdWUgPSByb3V0ZS5xdWVyeS5wbGF0Zm9ybVxuICB9XG4gIFxuICBpZiAocm91dGUucXVlcnkudGFnKSB7XG4gICAgZmlsdGVyVGFnLnZhbHVlID0gcm91dGUucXVlcnkudGFnXG4gIH1cbiAgXG4gIGlmIChyb3V0ZS5xdWVyeS5zb3J0KSB7XG4gICAgc29ydEJ5LnZhbHVlID0gcm91dGUucXVlcnkuc29ydFxuICB9XG4gIFxuICAvLyDliJ3lp4vljJbmkJzntKLlhbPplK7or41cbiAgaWYgKHJvdXRlLnF1ZXJ5LnNlYXJjaCkge1xuICAgIHNlYXJjaEtleXdvcmQudmFsdWUgPSByb3V0ZS5xdWVyeS5zZWFyY2hcbiAgfVxuICBcbiAgLy8g5Yid5aeL5YyW6aG156CBXG4gIGNvbnN0IGluaXRpYWxQYWdlID0gcGFyc2VJbnQocm91dGUucXVlcnkucGFnZSkgfHwgMVxuICBmZXRjaFN0YXRpc3RpY3MoKVxuICBmZXRjaEFydGljbGVzKGluaXRpYWxQYWdlKVxuICBmZXRjaENoYXJsZXNTdGF0dXMoKVxuICBmZXRjaFNjaGVkdWxlKClcbn0pXG48L3NjcmlwdD5cblxuPHN0eWxlIHNjb3BlZD5cbi5hcnRpY2xlcy1wYWdlIHtcbiAgbWF4LXdpZHRoOiAxMzAwcHg7XG4gIG1hcmdpbjogMCBhdXRvO1xuICBwYWRkaW5nOiAyNHB4IDQwcHg7XG59XG5cbi5wYWdlLWhlYWRlciB7XG4gIG1hcmdpbi1ib3R0b206IDI0cHg7XG59XG5cbi5oZWFkZXItY29udHJvbHMge1xuICBkaXNwbGF5OiBmbGV4O1xuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGZsZXgtd3JhcDogd3JhcDtcbiAgZ2FwOiAxNnB4O1xufVxuXG4uaGVhZGVyLWxlZnQge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDE2cHg7XG4gIGZsZXgtd3JhcDogd3JhcDtcbn1cblxuLmhlYWRlci1yaWdodCB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogMTZweDtcbiAgZmxleC13cmFwOiB3cmFwO1xufVxuXG4uZmlsdGVyLXRhYnMge1xuICBkaXNwbGF5OiBmbGV4O1xuICBnYXA6IDhweDtcbn1cblxuLmZpbHRlci1zZWxlY3QtZ3JvdXAge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDhweDtcbn1cblxuLmZpbHRlci1sYWJlbCB7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICM2NjY7XG59XG5cbi5maWx0ZXItc2VsZWN0IHtcbiAgcGFkZGluZzogOHB4IDEycHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBjb2xvcjogIzY2NjtcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XG4gIG1pbi13aWR0aDogMTAwcHg7XG59XG5cbi5maWx0ZXItc2VsZWN0LW5hcnJvdyB7XG4gIG1pbi13aWR0aDogODBweDtcbiAgcGFkZGluZzogOHB4IDEwcHg7XG59XG5cbi5maWx0ZXItc2VsZWN0LXNvcnQge1xuICBtaW4td2lkdGg6IDcwcHg7XG4gIHBhZGRpbmc6IDhweCA4cHg7XG59XG5cbi5maWx0ZXItc2VsZWN0OmhvdmVyIHtcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xufVxuXG4uZmlsdGVyLXNlbGVjdDpmb2N1cyB7XG4gIG91dGxpbmU6IG5vbmU7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgYm94LXNoYWRvdzogMCAwIDAgMnB4IHJnYmEoMjQsIDE0NCwgMjU1LCAwLjEpO1xufVxuXG4uc29ydC1jb250cm9scyB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogOHB4O1xufVxuXG4uc29ydC1sYWJlbCB7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICM2NjY7XG59XG5cbi5zb3J0LXNlbGVjdCB7XG4gIHBhZGRpbmc6IDhweCAxMnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICM2NjY7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xuICBtaW4td2lkdGg6IDEyMHB4O1xufVxuXG4uc29ydC1zZWxlY3Q6aG92ZXIge1xuICBib3JkZXItY29sb3I6ICMxODkwZmY7XG59XG5cbi5zb3J0LXNlbGVjdDpmb2N1cyB7XG4gIG91dGxpbmU6IG5vbmU7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgYm94LXNoYWRvdzogMCAwIDAgMnB4IHJnYmEoMjQsIDE0NCwgMjU1LCAwLjEpO1xufVxuXG4uZmlsdGVyLXRhYiB7XG4gIHBhZGRpbmc6IDhweCAxNnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICM2NjY7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xufVxuXG4uZmlsdGVyLXRhYjpob3ZlciB7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgY29sb3I6ICMxODkwZmY7XG59XG5cbi5maWx0ZXItdGFiLmFjdGl2ZSB7XG4gIGJhY2tncm91bmQ6ICMxODkwZmY7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgY29sb3I6IHdoaXRlO1xufVxuXG4uY291bnQtYmFkZ2Uge1xuICBtYXJnaW4tbGVmdDogNnB4O1xuICBwYWRkaW5nOiAycHggNnB4O1xuICBiYWNrZ3JvdW5kOiByZ2JhKDI1NSwgMjU1LCAyNTUsIDAuMik7XG4gIGJvcmRlci1yYWRpdXM6IDEwcHg7XG4gIGZvbnQtc2l6ZTogMTJweDtcbiAgZm9udC13ZWlnaHQ6IDYwMDtcbn1cblxuLmZpbHRlci10YWIuYWN0aXZlIC5jb3VudC1iYWRnZSB7XG4gIGJhY2tncm91bmQ6IHJnYmEoMjU1LCAyNTUsIDI1NSwgMC4zKTtcbn1cblxuLmFydGljbGVzLWxpc3Qge1xuICBkaXNwbGF5OiBmbGV4O1xuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICBnYXA6IDEycHg7XG59XG5cbi5hcnRpY2xlLWl0ZW0ge1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xuICBwYWRkaW5nOiAxMnB4IDIwcHg7XG4gIGJveC1zaGFkb3c6IDAgMXB4IDRweCByZ2JhKDAsIDAsIDAsIDAuMDgpO1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbiAgYm9yZGVyOiAycHggc29saWQgdHJhbnNwYXJlbnQ7XG59XG5cbi5hcnRpY2xlLWl0ZW06aG92ZXIge1xuICBib3gtc2hhZG93OiAwIDJweCA4cHggcmdiYSgwLCAwLCAwLCAwLjEyKTtcbn1cblxuLmFydGljbGUtaXRlbS5zZWxlY3RlZCB7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgYmFja2dyb3VuZDogI2YwZjdmZjtcbn1cblxuLmFydGljbGUtaXRlbS5kZWxldGVkIHtcbiAgb3BhY2l0eTogMC42O1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xufVxuXG4uYXJ0aWNsZS1yb3cge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDEycHg7XG59XG5cbi5hcnRpY2xlLWNoZWNrYm94LWxhYmVsIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmbGV4LXNocmluazogMDtcbn1cblxuLmFydGljbGUtY2hlY2tib3gge1xuICB3aWR0aDogMThweDtcbiAgaGVpZ2h0OiAxOHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGFjY2VudC1jb2xvcjogIzE4OTBmZjtcbn1cblxuLyog5om56YeP5pON5L2c5bel5YW35qCPICovXG4uYmF0Y2gtYWN0aW9ucy1iYXIge1xuICBkaXNwbGF5OiBmbGV4O1xuICBqdXN0aWZ5LWNvbnRlbnQ6IHNwYWNlLWJldHdlZW47XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIHBhZGRpbmc6IDEycHggMjBweDtcbiAgYmFja2dyb3VuZDogd2hpdGU7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgbWFyZ2luLWJvdHRvbTogMTJweDtcbiAgYm94LXNoYWRvdzogMCAxcHggNHB4IHJnYmEoMCwgMCwgMCwgMC4wOCk7XG59XG5cbi5iYXRjaC1hY3Rpb25zLWxlZnQge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xufVxuXG4uYmF0Y2gtY2hlY2tib3gtbGFiZWwge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDhweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDE0cHg7XG4gIGNvbG9yOiAjNjY2O1xufVxuXG4uYmF0Y2gtY2hlY2tib3gge1xuICB3aWR0aDogMThweDtcbiAgaGVpZ2h0OiAxOHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGFjY2VudC1jb2xvcjogIzE4OTBmZjtcbn1cblxuLmJhdGNoLWNoZWNrYm94LXRleHQge1xuICB1c2VyLXNlbGVjdDogbm9uZTtcbn1cblxuLnNlbGVjdGVkLWNvdW50IHtcbiAgY29sb3I6ICMxODkwZmY7XG4gIGZvbnQtd2VpZ2h0OiA1MDA7XG59XG5cbi5iYXRjaC1hY3Rpb25zLXJpZ2h0IHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiAxMnB4O1xufVxuXG4uYmF0Y2gtZGVsZXRlLWJ0biB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogNnB4O1xuICBwYWRkaW5nOiA4cHggMTZweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2ZmNGQ0ZjtcbiAgYmFja2dyb3VuZDogI2ZmNGQ0ZjtcbiAgY29sb3I6IHdoaXRlO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAxNHB4O1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbn1cblxuLmJhdGNoLWRlbGV0ZS1idG46aG92ZXI6bm90KDpkaXNhYmxlZCkge1xuICBiYWNrZ3JvdW5kOiAjZmY3ODc1O1xuICBib3JkZXItY29sb3I6ICNmZjc4NzU7XG59XG5cbi5iYXRjaC1kZWxldGUtYnRuOmRpc2FibGVkIHtcbiAgb3BhY2l0eTogMC42O1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xufVxuXG4uYmF0Y2gtZGVsZXRlLWJ0biBzdmcge1xuICB3aWR0aDogMTZweDtcbiAgaGVpZ2h0OiAxNnB4O1xuICBzdHJva2Utd2lkdGg6IDI7XG59XG5cbi5hcnRpY2xlLWxpbmsge1xuICBmbGV4OiAxO1xuICB0ZXh0LWRlY29yYXRpb246IG5vbmU7XG4gIGNvbG9yOiBpbmhlcml0O1xufVxuXG4uYXJ0aWNsZS1saW5rIHtcbiAgZmxleDogMTtcbiAgbWluLXdpZHRoOiAwO1xuICB0ZXh0LWRlY29yYXRpb246IG5vbmU7XG4gIGNvbG9yOiBpbmhlcml0O1xufVxuXG4uY2xpY2thYmxlLXRpdGxlIHtcbiAgY3Vyc29yOiBwb2ludGVyO1xufVxuXG4uY2xpY2thYmxlLXRpdGxlOmhvdmVyIC5hcnRpY2xlLXRpdGxlIHtcbiAgY29sb3I6ICMxODkwZmY7XG59XG5cbi5hcnRpY2xlLXRpdGxlIHtcbiAgZm9udC1zaXplOiAxNnB4O1xuICBmb250LXdlaWdodDogNTAwO1xuICBjb2xvcjogIzFhMWExYTtcbiAgbWFyZ2luOiAwO1xuICBsaW5lLWhlaWdodDogMS41O1xuICBkaXNwbGF5OiAtd2Via2l0LWJveDtcbiAgLXdlYmtpdC1saW5lLWNsYW1wOiAxO1xuICAtd2Via2l0LWJveC1vcmllbnQ6IHZlcnRpY2FsO1xuICBvdmVyZmxvdzogaGlkZGVuO1xufVxuXG4uYXJ0aWNsZS1saW5rOmhvdmVyIC5hcnRpY2xlLXRpdGxlIHtcbiAgY29sb3I6ICMxODkwZmY7XG59XG5cbi5hcnRpY2xlLW1ldGEtaW5saW5lIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiAxNnB4O1xuICBmbGV4LXNocmluazogMDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbn1cblxuLmFydGljbGUtYWN0aW9ucyB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogOHB4O1xuICBmbGV4LXNocmluazogMDtcbn1cblxuLmFjdGlvbi1idG4ge1xuICB3aWR0aDogMzJweDtcbiAgaGVpZ2h0OiAzMnB4O1xuICBib3JkZXI6IDJweCBzb2xpZCAjZTBlMGUwO1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbiAgcGFkZGluZzogMDtcbn1cblxuLmFjdGlvbi1idG46aG92ZXIge1xuICBib3JkZXItY29sb3I6ICMxODkwZmY7XG4gIGJhY2tncm91bmQ6ICNmMGY3ZmY7XG59XG5cbi5zZWxlY3QtYnRuLmFjdGl2ZSB7XG4gIGJhY2tncm91bmQ6ICMxODkwZmY7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgY29sb3I6IHdoaXRlO1xufVxuXG4uZGVsZXRlLWJ0bjpob3ZlciB7XG4gIGJvcmRlci1jb2xvcjogI2ZmNGQ0ZjtcbiAgYmFja2dyb3VuZDogI2ZmZjFmMDtcbiAgY29sb3I6ICNmZjRkNGY7XG59XG5cbi5hY3Rpb24tYnRuIHN2ZyB7XG4gIHdpZHRoOiAxNnB4O1xuICBoZWlnaHQ6IDE2cHg7XG59XG5cbi5tZXRhLWl0ZW0ge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDRweDtcbiAgZm9udC1zaXplOiAxM3B4O1xuICBjb2xvcjogIzY2Njtcbn1cblxuLm1ldGEtaXRlbSBzdmcge1xuICB3aWR0aDogMTRweDtcbiAgaGVpZ2h0OiAxNHB4O1xuICBjb2xvcjogIzk5OTtcbn1cblxuLmFydGljbGUtZGF0ZSB7XG4gIGZvbnQtc2l6ZTogMTJweDtcbiAgY29sb3I6ICM5OTk7XG59XG5cbi5hcnRpY2xlLWtleXdvcmQge1xuICBmb250LXNpemU6IDEycHg7XG4gIGNvbG9yOiAjMTg5MGZmO1xuICBiYWNrZ3JvdW5kOiAjZTZmN2ZmO1xuICBwYWRkaW5nOiAycHggOHB4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG59XG5cbi5hcnRpY2xlLXBsYXRmb3JtIHtcbiAgZm9udC1zaXplOiAxMnB4O1xuICBwYWRkaW5nOiAycHggOHB4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGZvbnQtd2VpZ2h0OiA1MDA7XG59XG5cbi5tYW51YWwtYmFkZ2Uge1xuICBjb2xvcjogIzUyYzQxYTtcbiAgYmFja2dyb3VuZDogI2Y2ZmZlZDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2I3ZWI4Zjtcbn1cblxuLmNyZWF0b3ItYmFkZ2Uge1xuICBjb2xvcjogIzcyMmVkMTtcbiAgYmFja2dyb3VuZDogI2Y5ZjBmZjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2QzYWRmNztcbn1cblxuLyog5paw6bKc5bqm5b6956ugOiDiiaQzZCDnuqIgKEZyZXNoIOW8uuS/neW6leeql+WPoykgLyDiiaQ3ZCDmqZkgLyDlhbbkvZnngbAgKi9cbi5mcmVzaC1iYWRnZSB7XG4gIGZvbnQtc2l6ZTogMTFweDtcbiAgcGFkZGluZzogMnB4IDZweDtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXdlaWdodDogNjAwO1xuICBjdXJzb3I6IGhlbHA7XG4gIHdoaXRlLXNwYWNlOiBub3dyYXA7XG59XG4uZnJlc2gtYmFkZ2UuZnJlc2gtaG90IHtcbiAgY29sb3I6ICNmNTIyMmQ7XG4gIGJhY2tncm91bmQ6ICNmZmYxZjA7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmEzOWU7XG59XG4uZnJlc2gtYmFkZ2UuZnJlc2gtb2sge1xuICBjb2xvcjogI2ZhOGMxNjtcbiAgYmFja2dyb3VuZDogI2ZmZjdlNjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2ZmZDU5MTtcbn1cbi5mcmVzaC1iYWRnZS5mcmVzaC1zdGFsZSB7XG4gIGNvbG9yOiAjOGM4YzhjO1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDlkOWQ5O1xufVxuXG4vKiDlj5HluIPorqHliJLpnaLmnb8gKi9cbi5zY2hlZHVsZS1wYW5lbCB7XG4gIG1hcmdpbi1ib3R0b206IDE2cHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlOGU4ZTg7XG4gIGJvcmRlci1yYWRpdXM6IDhweDtcbiAgYmFja2dyb3VuZDogI2ZmZjtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbn1cbi5zY2hlZHVsZS1oZWFkZXIge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDEycHg7XG4gIHBhZGRpbmc6IDEwcHggMTZweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICB1c2VyLXNlbGVjdDogbm9uZTtcbiAgYmFja2dyb3VuZDogI2ZhZmFmYTtcbn1cbi5zY2hlZHVsZS1oZWFkZXI6aG92ZXIge1xuICBiYWNrZ3JvdW5kOiAjZjBmNWZmO1xufVxuLnNjaGVkdWxlLXRpdGxlIHtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBmb250LXdlaWdodDogNjAwO1xuICBjb2xvcjogIzFmMWYxZjtcbn1cbi5zY2hlZHVsZS1zdW1tYXJ5IHtcbiAgZm9udC1zaXplOiAxMnB4O1xuICBjb2xvcjogIzhjOGM4Yztcbn1cbi5zY2hlZHVsZS10b2dnbGUge1xuICBtYXJnaW4tbGVmdDogYXV0bztcbiAgZm9udC1zaXplOiAxMnB4O1xuICBjb2xvcjogIzE2NzdmZjtcbn1cbi5zY2hlZHVsZS1ib2R5IHtcbiAgYm9yZGVyLXRvcDogMXB4IHNvbGlkICNlOGU4ZTg7XG4gIG1heC1oZWlnaHQ6IDQyMHB4O1xuICBvdmVyZmxvdy15OiBhdXRvO1xufVxuLnNjaGVkdWxlLWVtcHR5IHtcbiAgcGFkZGluZzogMjBweDtcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xuICBjb2xvcjogIzhjOGM4YztcbiAgZm9udC1zaXplOiAxM3B4O1xufVxuLnNjaGVkdWxlLXRhYmxlIHtcbiAgd2lkdGg6IDEwMCU7XG4gIGJvcmRlci1jb2xsYXBzZTogY29sbGFwc2U7XG4gIGZvbnQtc2l6ZTogMTJweDtcbn1cbi5zY2hlZHVsZS10YWJsZSB0aCxcbi5zY2hlZHVsZS10YWJsZSB0ZCB7XG4gIHBhZGRpbmc6IDZweCAxMHB4O1xuICB0ZXh0LWFsaWduOiBsZWZ0O1xuICBib3JkZXItYm90dG9tOiAxcHggc29saWQgI2YwZjBmMDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbn1cbi5zY2hlZHVsZS10YWJsZSB0aCB7XG4gIHBvc2l0aW9uOiBzdGlja3k7XG4gIHRvcDogMDtcbiAgYmFja2dyb3VuZDogI2ZhZmFmYTtcbiAgZm9udC13ZWlnaHQ6IDYwMDtcbiAgY29sb3I6ICM1OTU5NTk7XG4gIHotaW5kZXg6IDE7XG59XG4uc2NoZWR1bGUtdGFibGUgLmNvbC10aXRsZSB7XG4gIG1heC13aWR0aDogMzYwcHg7XG4gIG92ZXJmbG93OiBoaWRkZW47XG4gIHRleHQtb3ZlcmZsb3c6IGVsbGlwc2lzO1xufVxuLnNjaGVkdWxlLXNvdXJjZSB7XG4gIGZvbnQtc2l6ZTogMTFweDtcbiAgcGFkZGluZzogMXB4IDZweDtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjb2xvcjogIzE2NzdmZjtcbiAgYmFja2dyb3VuZDogI2U2ZjRmZjtcbiAgYm9yZGVyOiAxcHggc29saWQgIzkxY2FmZjtcbn1cbi5zY2hlZHVsZS1zb3VyY2UuY3JlYXRvciB7XG4gIGNvbG9yOiAjNzIyZWQxO1xuICBiYWNrZ3JvdW5kOiAjZjlmMGZmO1xuICBib3JkZXItY29sb3I6ICNkM2FkZjc7XG59XG4uc2NoZWR1bGUtc3RhdHVzIHtcbiAgZm9udC1zaXplOiAxMXB4O1xuICBwYWRkaW5nOiAxcHggNnB4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGNvbG9yOiAjNTk1OTU5O1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDlkOWQ5O1xufVxuLnNjaGVkdWxlLXN0YXR1cy52cy1wcm9jZXNzaW5nIHtcbiAgY29sb3I6ICMxNjc3ZmY7XG4gIGJhY2tncm91bmQ6ICNlNmY0ZmY7XG4gIGJvcmRlci1jb2xvcjogIzkxY2FmZjtcbn1cbi5zY2hlZHVsZS1zdGF0dXMudnMtY29tcGxldGVkIHtcbiAgY29sb3I6ICM1MmM0MWE7XG4gIGJhY2tncm91bmQ6ICNmNmZmZWQ7XG4gIGJvcmRlci1jb2xvcjogI2I3ZWI4Zjtcbn1cbi5zY2hlZHVsZS1zdGF0dXMudnMtZmFpbGVkIHtcbiAgY29sb3I6ICNmNTIyMmQ7XG4gIGJhY2tncm91bmQ6ICNmZmYxZjA7XG4gIGJvcmRlci1jb2xvcjogI2ZmYTM5ZTtcbn1cblxuLmNvbnRlbnQtdHlwZS1iYWRnZSB7XG4gIGZvbnQtc2l6ZTogMTFweDtcbiAgcGFkZGluZzogMnB4IDZweDtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXdlaWdodDogNTAwO1xufVxuXG4uY29udGVudC10eXBlLWJhZGdlLnZpZGVvIHtcbiAgY29sb3I6ICMxODkwZmY7XG4gIGJhY2tncm91bmQ6ICNlNmY3ZmY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICM5MWQ1ZmY7XG59XG5cbi5jb250ZW50LXR5cGUtYmFkZ2UuaW1hZ2Uge1xuICBjb2xvcjogIzcyMmVkMTtcbiAgYmFja2dyb3VuZDogI2Y5ZjBmZjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2QzYWRmNztcbn1cblxuLmNvbnRlbnQtdHlwZS1iYWRnZS5ib3RoIHtcbiAgY29sb3I6ICNmYThjMTY7XG4gIGJhY2tncm91bmQ6ICNmZmY3ZTY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmQ1OTE7XG59XG5cbi8qIEtJTUkg6KeG6aKR5Y+36YCJ6aKY6K+E5YiG5b6956ugICjliIbmlbAgKyDnroDnn63nkIbnlLEpLCBob3ZlciDnnIvlrozmlbQgcmVhc29uICovXG4ua2ltaS1zY29yZS1iYWRnZSB7XG4gIGRpc3BsYXk6IGlubGluZS1mbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDZweDtcbiAgZm9udC1zaXplOiAxMXB4O1xuICBwYWRkaW5nOiAycHggNnB4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGZvbnQtd2VpZ2h0OiA1MDA7XG4gIGN1cnNvcjogaGVscDtcbiAgbWF4LXdpZHRoOiAyODBweDtcbn1cbi5raW1pLXNjb3JlLWJhZGdlIC5raW1pLXJlYXNvbi1taW5pIHtcbiAgZm9udC13ZWlnaHQ6IDQwMDtcbiAgb3BhY2l0eTogMC44NTtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7XG59XG4ua2ltaS1zY29yZS1iYWRnZS5raW1pLWhpZ2gge1xuICBjb2xvcjogIzM4OWUwZDtcbiAgYmFja2dyb3VuZDogI2Y2ZmZlZDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2I3ZWI4Zjtcbn1cbi5raW1pLXNjb3JlLWJhZGdlLmtpbWktbWlkIHtcbiAgY29sb3I6ICNkNDZiMDg7XG4gIGJhY2tncm91bmQ6ICNmZmY3ZTY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmQ1OTE7XG59XG4ua2ltaS1zY29yZS1iYWRnZS5raW1pLWxvdyB7XG4gIGNvbG9yOiAjNTk1OTU5O1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDlkOWQ5O1xufVxuLmtpbWktc2NvcmUtYmFkZ2Uua2ltaS15ZWxsb3cge1xuICBjb2xvcjogI2FkNjgwMDtcbiAgYmFja2dyb3VuZDogI2ZmZmJlNjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2ZmZTU4Zjtcbn1cbi5raW1pLXNjb3JlLWJhZGdlLmtpbWktcmVkIHtcbiAgY29sb3I6ICNjZjEzMjI7XG4gIGJhY2tncm91bmQ6ICNmZmYxZjA7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNmZmEzOWU7XG59XG5cbi5sb2FkaW5nLFxuLmVtcHR5IHtcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xuICBwYWRkaW5nOiA2MHB4IDIwcHg7XG4gIGNvbG9yOiAjODg4O1xuICBmb250LXNpemU6IDFyZW07XG59XG5cbi5wYWdpbmF0aW9uIHtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogMTZweDtcbiAgbWFyZ2luLXRvcDogMzJweDtcbiAgcGFkZGluZzogMjBweCAwO1xufVxuXG4ucGFnZS1idG4ge1xuICBwYWRkaW5nOiA4cHggMTZweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2UwZTBlMDtcbiAgYmFja2dyb3VuZDogd2hpdGU7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDE0cHg7XG4gIGNvbG9yOiAjNjY2O1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbn1cblxuLnBhZ2UtYnRuOmhvdmVyOm5vdCg6ZGlzYWJsZWQpIHtcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xuICBjb2xvcjogIzE4OTBmZjtcbn1cblxuLnBhZ2UtYnRuOmRpc2FibGVkIHtcbiAgb3BhY2l0eTogMC41O1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xufVxuXG4ucGFnZS1pbmZvIHtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBjb2xvcjogIzY2Njtcbn1cblxuLnBhZ2UtbnVtYmVycyB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGdhcDogNHB4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xufVxuXG4ucGFnZS1udW1iZXItYnRuIHtcbiAgbWluLXdpZHRoOiAzNnB4O1xuICBoZWlnaHQ6IDM2cHg7XG4gIHBhZGRpbmc6IDAgOHB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZTBlMGUwO1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICM2NjY7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBqdXN0aWZ5LWNvbnRlbnQ6IGNlbnRlcjtcbn1cblxuLnBhZ2UtbnVtYmVyLWJ0bjpob3Zlcjpub3QoOmRpc2FibGVkKSB7XG4gIGJvcmRlci1jb2xvcjogIzE4OTBmZjtcbiAgY29sb3I6ICMxODkwZmY7XG59XG5cbi5wYWdlLW51bWJlci1idG4uYWN0aXZlIHtcbiAgYmFja2dyb3VuZDogIzE4OTBmZjtcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xuICBjb2xvcjogd2hpdGU7XG59XG5cbi5wYWdlLW51bWJlci1idG46ZGlzYWJsZWQge1xuICBvcGFjaXR5OiAwLjU7XG4gIGN1cnNvcjogbm90LWFsbG93ZWQ7XG59XG5cbi5wYWdlLWVsbGlwc2lzIHtcbiAgcGFkZGluZzogMCA0cHg7XG4gIGNvbG9yOiAjOTk5O1xuICBmb250LXNpemU6IDE0cHg7XG4gIHVzZXItc2VsZWN0OiBub25lO1xufVxuXG4ucGFnZS1qdW1wIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA4cHg7XG4gIG1hcmdpbi1sZWZ0OiAxNnB4O1xufVxuXG4uanVtcC1sYWJlbCB7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICM2NjY7XG59XG5cbi5qdW1wLWlucHV0IHtcbiAgd2lkdGg6IDYwcHg7XG4gIHBhZGRpbmc6IDZweCA4cHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgdGV4dC1hbGlnbjogY2VudGVyO1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbn1cblxuLmp1bXAtaW5wdXQ6Zm9jdXMge1xuICBvdXRsaW5lOiBub25lO1xuICBib3JkZXItY29sb3I6ICMxODkwZmY7XG4gIGJveC1zaGFkb3c6IDAgMCAwIDJweCByZ2JhKDI0LCAxNDQsIDI1NSwgMC4xKTtcbn1cblxuLmp1bXAtYnRuIHtcbiAgcGFkZGluZzogNnB4IDEycHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICMxODkwZmY7XG4gIGJhY2tncm91bmQ6ICMxODkwZmY7XG4gIGNvbG9yOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XG59XG5cbi5qdW1wLWJ0bjpob3ZlciB7XG4gIGJhY2tncm91bmQ6ICM0MGE5ZmY7XG4gIGJvcmRlci1jb2xvcjogIzQwYTlmZjtcbn1cblxuLmxvZy1idG4ge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDhweDtcbiAgcGFkZGluZzogOHB4IDE2cHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBjb2xvcjogIzY2NjtcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XG4gIHRleHQtZGVjb3JhdGlvbjogbm9uZTtcbn1cblxuLmxvZy1idG46aG92ZXIge1xuICBib3JkZXItY29sb3I6ICMxODkwZmY7XG4gIGNvbG9yOiAjMTg5MGZmO1xuICBiYWNrZ3JvdW5kOiAjZjBmN2ZmO1xufVxuXG4ubG9nLWJ0biAuc3RhdHVzLWRvdCB7XG4gIHdpZHRoOiA4cHg7XG4gIGhlaWdodDogOHB4O1xuICBib3JkZXItcmFkaXVzOiA1MCU7XG4gIGJhY2tncm91bmQ6ICM5OTk7XG59XG5cbi5sb2ctYnRuLnN0YXR1cy13b3JraW5nIHtcbiAgYm9yZGVyLWNvbG9yOiAjYjdlYjhmO1xuICBiYWNrZ3JvdW5kOiAjZjZmZmVkO1xuICBjb2xvcjogIzUyYzQxYTtcbn1cblxuLmxvZy1idG4uc3RhdHVzLXdvcmtpbmc6aG92ZXIge1xuICBib3JkZXItY29sb3I6ICM1MmM0MWE7XG4gIGJhY2tncm91bmQ6ICNkOWY3YmU7XG59XG5cbi5sb2ctYnRuLnN0YXR1cy13b3JraW5nIC5zdGF0dXMtZG90IHtcbiAgYmFja2dyb3VuZDogIzUyYzQxYTtcbiAgYW5pbWF0aW9uOiBwdWxzZSAycyBpbmZpbml0ZTtcbn1cblxuLmxvZy1idG4uc3RhdHVzLWRlYWQge1xuICBib3JkZXItY29sb3I6ICNmZmNjYzc7XG4gIGJhY2tncm91bmQ6ICNmZmYyZjA7XG4gIGNvbG9yOiAjZmY0ZDRmO1xufVxuXG4ubG9nLWJ0bi5zdGF0dXMtZGVhZDpob3ZlciB7XG4gIGJvcmRlci1jb2xvcjogI2ZmNGQ0ZjtcbiAgYmFja2dyb3VuZDogI2ZmY2NjNztcbn1cblxuLmxvZy1idG4uc3RhdHVzLWRlYWQgLnN0YXR1cy1kb3Qge1xuICBiYWNrZ3JvdW5kOiAjZmY0ZDRmO1xufVxuXG4ubG9nLWJ0bi5zdGF0dXMtd2FybmluZyB7XG4gIGJvcmRlci1jb2xvcjogI2ZmZTU4ZjtcbiAgYmFja2dyb3VuZDogI2ZmZmJlNjtcbiAgY29sb3I6ICNkNDg4MDY7XG59XG5cbi5sb2ctYnRuLnN0YXR1cy13YXJuaW5nOmhvdmVyIHtcbiAgYm9yZGVyLWNvbG9yOiAjZmFhZDE0O1xuICBiYWNrZ3JvdW5kOiAjZmZmMWI4O1xufVxuXG4ubG9nLWJ0bi5zdGF0dXMtd2FybmluZyAuc3RhdHVzLWRvdCB7XG4gIGJhY2tncm91bmQ6ICNmYWFkMTQ7XG4gIGFuaW1hdGlvbjogcHVsc2UgMXMgaW5maW5pdGU7XG59XG5cbi5zdGF0dXMtd2FybmluZy10aXAge1xuICBmb250LXNpemU6IDEycHg7XG4gIGNvbG9yOiAjZDQ4ODA2O1xuICBiYWNrZ3JvdW5kOiAjZmZmYmU2O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZmZlNThmO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIHBhZGRpbmc6IDRweCAxMHB4O1xufVxuXG4uc3RhdHVzLXdhcm5pbmctdGlwLnN0YXR1cy1kZWFkLXRpcCB7XG4gIGNvbG9yOiAjZmY0ZDRmO1xuICBiYWNrZ3JvdW5kOiAjZmZmMmYwO1xuICBib3JkZXItY29sb3I6ICNmZmNjYzc7XG59XG5cbkBrZXlmcmFtZXMgcHVsc2Uge1xuICAwJSwgMTAwJSB7IG9wYWNpdHk6IDE7IH1cbiAgNTAlIHsgb3BhY2l0eTogMC41OyB9XG59XG5cbi8qIOaWsOW7uuaWh+eroOaMiemSriAqL1xuLyogQUnov4fmu6TmjInpkq4gKi9cbi5haS1maWx0ZXItYnRuIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA2cHg7XG4gIHBhZGRpbmc6IDhweCAxNnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjNzIyZWQxO1xuICBiYWNrZ3JvdW5kOiAjNzIyZWQxO1xuICBjb2xvcjogd2hpdGU7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDE0cHg7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xufVxuXG4uYWktZmlsdGVyLWJ0bjpob3ZlciB7XG4gIGJhY2tncm91bmQ6ICM5MjU0ZGU7XG4gIGJvcmRlci1jb2xvcjogIzkyNTRkZTtcbn1cblxuLmFpLWZpbHRlci1idG46ZGlzYWJsZWQge1xuICBiYWNrZ3JvdW5kOiAjZDNhZGY3O1xuICBib3JkZXItY29sb3I6ICNkM2FkZjc7XG4gIGN1cnNvcjogbm90LWFsbG93ZWQ7XG59XG5cbi5haS1maWx0ZXItYnRuIHN2ZyB7XG4gIHdpZHRoOiAxNnB4O1xuICBoZWlnaHQ6IDE2cHg7XG59XG5cbi8qIOaPkOekuuivjee8lui+keW8ueeqlyAqL1xuLnByb21wdC1lZGl0LW1vZGFsIHtcbiAgbWF4LXdpZHRoOiA3MDBweDtcbiAgbWF4LWhlaWdodDogODB2aDtcbn1cblxuLnByb21wdC1lZGl0LWhpbnQge1xuICBmb250LXNpemU6IDEzcHg7XG4gIGNvbG9yOiAjNjY2O1xuICBtYXJnaW4tYm90dG9tOiAxMnB4O1xuICBsaW5lLWhlaWdodDogMS41O1xufVxuXG4ucHJvbXB0LXRleHRhcmVhIHtcbiAgd2lkdGg6IDEwMCU7XG4gIG1pbi1oZWlnaHQ6IDMwMHB4O1xuICBwYWRkaW5nOiAxMnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjZDlkOWQ5O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGZvbnQtc2l6ZTogMTNweDtcbiAgbGluZS1oZWlnaHQ6IDEuNjtcbiAgcmVzaXplOiB2ZXJ0aWNhbDtcbiAgZm9udC1mYW1pbHk6IC1hcHBsZS1zeXN0ZW0sIEJsaW5rTWFjU3lzdGVtRm9udCwgJ1NlZ29lIFVJJywgUm9ib3RvLCBzYW5zLXNlcmlmO1xuICBjb2xvcjogIzMzMztcbiAgYm94LXNpemluZzogYm9yZGVyLWJveDtcbn1cblxuLnByb21wdC10ZXh0YXJlYTpmb2N1cyB7XG4gIGJvcmRlci1jb2xvcjogIzcyMmVkMTtcbiAgb3V0bGluZTogbm9uZTtcbiAgYm94LXNoYWRvdzogMCAwIDAgMnB4IHJnYmEoMTE0LCA0NiwgMjA5LCAwLjEpO1xufVxuXG4ucHJvbXB0LWFjdGlvbnMge1xuICBtYXJnaW4tdG9wOiAxNnB4O1xufVxuXG4uYnRuLW91dGxpbmUtcHJpbWFyeSB7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xuICBib3JkZXI6IDFweCBzb2xpZCAjNzIyZWQxO1xuICBjb2xvcjogIzcyMmVkMTtcbiAgcGFkZGluZzogOHB4IDE2cHg7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDE0cHg7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xufVxuXG4uYnRuLW91dGxpbmUtcHJpbWFyeTpob3ZlciB7XG4gIGJhY2tncm91bmQ6ICNmOWYwZmY7XG59XG5cbi5idG4tb3V0bGluZS1wcmltYXJ5OmRpc2FibGVkIHtcbiAgYm9yZGVyLWNvbG9yOiAjZDNhZGY3O1xuICBjb2xvcjogI2QzYWRmNztcbiAgY3Vyc29yOiBub3QtYWxsb3dlZDtcbn1cblxuLyogQUnov4fmu6TlvLnnqpcgKi9cbi5haS1maWx0ZXItbW9kYWwge1xuICBtYXgtd2lkdGg6IDcwMHB4O1xuICBtYXgtaGVpZ2h0OiA4MHZoO1xufVxuXG4uYWktZmlsdGVyLW1vZGFsIC5tb2RhbC1ib2R5IHtcbiAgZGlzcGxheTogZmxleDtcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcbiAgbWF4LWhlaWdodDogY2FsYyg4MHZoIC0gODBweCk7XG59XG5cbi5haS1maWx0ZXItc3VtbWFyeSB7XG4gIG1hcmdpbi1ib3R0b206IDE2cHg7XG4gIHBhZGRpbmc6IDEycHggMTZweDtcbiAgYmFja2dyb3VuZDogI2ZmZjdlNjtcbiAgYm9yZGVyOiAxcHggc29saWQgI2ZmZDU5MTtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBmb250LXNpemU6IDE0cHg7XG4gIGNvbG9yOiAjZDQ2YjA4O1xuICBmbGV4LXNocmluazogMDtcbn1cblxuLmFpLWZpbHRlci1zdW1tYXJ5IHN0cm9uZyB7XG4gIGNvbG9yOiAjYWQ0ZTAwO1xufVxuXG4uYWktZmlsdGVyLWxpc3Qge1xuICBmbGV4OiAxO1xuICBvdmVyZmxvdy15OiBhdXRvO1xuICBtYXgtaGVpZ2h0OiA0MDBweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2YwZjBmMDtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBtYXJnaW4tYm90dG9tOiAyMHB4O1xufVxuXG4uYWktZmlsdGVyLWl0ZW0ge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDEwcHg7XG4gIHBhZGRpbmc6IDEwcHggMTRweDtcbiAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkICNmNWY1ZjU7XG4gIGZvbnQtc2l6ZTogMTRweDtcbn1cblxuLmFpLWZpbHRlci1pdGVtOmxhc3QtY2hpbGQge1xuICBib3JkZXItYm90dG9tOiBub25lO1xufVxuXG4uYWktZmlsdGVyLWl0ZW06aG92ZXIge1xuICBiYWNrZ3JvdW5kOiAjZmFmYWZhO1xufVxuXG4uYWktZmlsdGVyLWluZGV4IHtcbiAgZmxleC1zaHJpbms6IDA7XG4gIHdpZHRoOiAyOHB4O1xuICBoZWlnaHQ6IDI4cHg7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xuICBiYWNrZ3JvdW5kOiAjZmZmMWYwO1xuICBjb2xvcjogI2NmMTMyMjtcbiAgYm9yZGVyLXJhZGl1czogNTAlO1xuICBmb250LXNpemU6IDEycHg7XG4gIGZvbnQtd2VpZ2h0OiA2MDA7XG59XG5cbi5haS1maWx0ZXItdGl0bGUge1xuICBmbGV4OiAxO1xuICBvdmVyZmxvdzogaGlkZGVuO1xuICB0ZXh0LW92ZXJmbG93OiBlbGxpcHNpcztcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgY29sb3I6ICMzMzM7XG59XG5cbi5haS1maWx0ZXItaWQge1xuICBmbGV4LXNocmluazogMDtcbiAgZm9udC1zaXplOiAxMnB4O1xuICBjb2xvcjogIzk5OTtcbn1cblxuLmJ0bi1kYW5nZXIge1xuICBiYWNrZ3JvdW5kOiAjZmY0ZDRmO1xuICBib3JkZXItY29sb3I6ICNmZjRkNGY7XG4gIGNvbG9yOiB3aGl0ZTtcbn1cblxuLmJ0bi1kYW5nZXI6aG92ZXIge1xuICBiYWNrZ3JvdW5kOiAjZmY3ODc1O1xuICBib3JkZXItY29sb3I6ICNmZjc4NzU7XG59XG5cbi5idG4tZGFuZ2VyOmRpc2FibGVkIHtcbiAgYmFja2dyb3VuZDogI2ZmY2NjNztcbiAgYm9yZGVyLWNvbG9yOiAjZmZjY2M3O1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xufVxuXG4ubmV3LWFydGljbGUtYnRuIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiA2cHg7XG4gIHBhZGRpbmc6IDhweCAxNnB4O1xuICBib3JkZXI6IDFweCBzb2xpZCAjMTg5MGZmO1xuICBiYWNrZ3JvdW5kOiAjMTg5MGZmO1xuICBjb2xvcjogd2hpdGU7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgY3Vyc29yOiBwb2ludGVyO1xuICBmb250LXNpemU6IDE0cHg7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xufVxuXG4ubmV3LWFydGljbGUtYnRuOmhvdmVyIHtcbiAgYmFja2dyb3VuZDogIzQwYTlmZjtcbiAgYm9yZGVyLWNvbG9yOiAjNDBhOWZmO1xufVxuXG4ubmV3LWFydGljbGUtYnRuIHN2ZyB7XG4gIHdpZHRoOiAxNnB4O1xuICBoZWlnaHQ6IDE2cHg7XG4gIHN0cm9rZS13aWR0aDogMjtcbn1cblxuLyog5paw5bu65paH56ug5qih5oCB5qGGICovXG4uY3JlYXRlLWFydGljbGUtbW9kYWwge1xuICBtYXgtd2lkdGg6IDgwMHB4O1xufVxuXG4uZm9ybS1ncm91cCB7XG4gIG1hcmdpbi1ib3R0b206IDIwcHg7XG59XG5cbi5mb3JtLWxhYmVsIHtcbiAgZGlzcGxheTogYmxvY2s7XG4gIG1hcmdpbi1ib3R0b206IDhweDtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBmb250LXdlaWdodDogNTAwO1xuICBjb2xvcjogIzMzMztcbn1cblxuLmZvcm0tbGFiZWwgLnJlcXVpcmVkIHtcbiAgY29sb3I6ICNmZjRkNGY7XG59XG5cbi5mb3JtLWxhYmVsIC5vcHRpb25hbCB7XG4gIGNvbG9yOiAjOTk5O1xuICBmb250LXdlaWdodDogbm9ybWFsO1xuICBmb250LXNpemU6IDEycHg7XG59XG5cbi5mb3JtLWlucHV0LFxuLmZvcm0tdGV4dGFyZWEsXG4uZm9ybS1zZWxlY3Qge1xuICB3aWR0aDogMTAwJTtcbiAgcGFkZGluZzogOHB4IDEycHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBjb2xvcjogIzMzMztcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XG4gIGZvbnQtZmFtaWx5OiBpbmhlcml0O1xufVxuXG4uZm9ybS1pbnB1dDpmb2N1cyxcbi5mb3JtLXRleHRhcmVhOmZvY3VzLFxuLmZvcm0tc2VsZWN0OmZvY3VzIHtcbiAgb3V0bGluZTogbm9uZTtcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xuICBib3gtc2hhZG93OiAwIDAgMCAycHggcmdiYSgyNCwgMTQ0LCAyNTUsIDAuMSk7XG59XG5cbi5mb3JtLXRleHRhcmVhIHtcbiAgcmVzaXplOiB2ZXJ0aWNhbDtcbiAgbWluLWhlaWdodDogMzAwcHg7XG59XG5cbi50aXRsZS1pbnB1dC1ncm91cCB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGdhcDogOHB4O1xufVxuXG4udGl0bGUtaW5wdXQtZ3JvdXAgLmZvcm0taW5wdXQge1xuICBmbGV4OiAxO1xufVxuXG4uZ2VuZXJhdGUtdGl0bGUtYnRuIHtcbiAgcGFkZGluZzogOHB4IDE2cHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICMxODkwZmY7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xuICBjb2xvcjogIzE4OTBmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgdHJhbnNpdGlvbjogYWxsIDAuMnM7XG4gIHdoaXRlLXNwYWNlOiBub3dyYXA7XG59XG5cbi5nZW5lcmF0ZS10aXRsZS1idG46aG92ZXI6bm90KDpkaXNhYmxlZCkge1xuICBiYWNrZ3JvdW5kOiAjZjBmN2ZmO1xufVxuXG4uZ2VuZXJhdGUtdGl0bGUtYnRuOmRpc2FibGVkIHtcbiAgb3BhY2l0eTogMC41O1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xufVxuXG4uY2hhci1jb3VudCB7XG4gIG1hcmdpbi10b3A6IDRweDtcbiAgZm9udC1zaXplOiAxMnB4O1xuICBjb2xvcjogIzk5OTtcbiAgdGV4dC1hbGlnbjogcmlnaHQ7XG59XG5cbi5mb3JtLWFjdGlvbnMge1xuICBkaXNwbGF5OiBmbGV4O1xuICBqdXN0aWZ5LWNvbnRlbnQ6IGZsZXgtZW5kO1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDEycHg7XG4gIG1hcmdpbi10b3A6IDI0cHg7XG59XG5cbi5zYXZlLXN1Y2Nlc3MtdGlwIHtcbiAgY29sb3I6ICM1MmM0MWE7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgZm9udC13ZWlnaHQ6IDUwMDtcbiAgYW5pbWF0aW9uOiBmYWRlSW5PdXQgMnMgZWFzZS1pbi1vdXQ7XG59XG5cbkBrZXlmcmFtZXMgZmFkZUluT3V0IHtcbiAgMCUgeyBvcGFjaXR5OiAwOyB9XG4gIDE1JSB7IG9wYWNpdHk6IDE7IH1cbiAgODUlIHsgb3BhY2l0eTogMTsgfVxuICAxMDAlIHsgb3BhY2l0eTogMDsgfVxufVxuXG4uYXJyYW5nZS1hY3Rpb25zIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiAxMHB4O1xuICBtYXJnaW4tdG9wOiAxNnB4O1xuICBwYWRkaW5nLXRvcDogMTZweDtcbiAgYm9yZGVyLXRvcDogMXB4IHNvbGlkICNmMGYwZjA7XG59XG5cbi5hcnJhbmdlLWxhYmVsIHtcbiAgZm9udC1zaXplOiAxM3B4O1xuICBjb2xvcjogIzY2NjtcbiAgbWFyZ2luLXJpZ2h0OiA0cHg7XG59XG5cbi5idG4tYXJyYW5nZSB7XG4gIHBhZGRpbmc6IDZweCAxNHB4O1xuICBmb250LXNpemU6IDEzcHg7XG4gIGJvcmRlci1yYWRpdXM6IDRweDtcbiAgYm9yZGVyOiAxcHggc29saWQgI2Q5ZDlkOTtcbiAgYmFja2dyb3VuZDogd2hpdGU7XG4gIGNvbG9yOiAjMzMzO1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xufVxuXG4uYnRuLWFycmFuZ2U6aG92ZXI6bm90KDpkaXNhYmxlZCkge1xuICBib3JkZXItY29sb3I6ICMxODkwZmY7XG4gIGNvbG9yOiAjMTg5MGZmO1xufVxuXG4uYnRuLWFycmFuZ2U6ZGlzYWJsZWQge1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xuICBvcGFjaXR5OiAwLjY7XG59XG5cbi5idG4tYXJyYW5nZS5hcnJhbmdlZCB7XG4gIGJhY2tncm91bmQ6ICNmNmZmZWQ7XG4gIGJvcmRlci1jb2xvcjogI2I3ZWI4ZjtcbiAgY29sb3I6ICM1MmM0MWE7XG59XG5cbi5idG4tYXJyYW5nZS5hcnJhbmdlZDpob3ZlciB7XG4gIGJhY2tncm91bmQ6ICNkOWY3YmU7XG4gIGJvcmRlci1jb2xvcjogIzUyYzQxYTtcbiAgY29sb3I6ICMzODllMGQ7XG59XG5cbi5idG4tYXJyYW5nZSB7XG4gIHRleHQtZGVjb3JhdGlvbjogbm9uZTtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xufVxuXG4uYnRuIHtcbiAgcGFkZGluZzogMTBweCAyMHB4O1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAxNHB4O1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbiAgYm9yZGVyOiBub25lO1xufVxuXG4uYnRuLXByaW1hcnkge1xuICBiYWNrZ3JvdW5kOiAjMTg5MGZmO1xuICBjb2xvcjogd2hpdGU7XG59XG5cbi5idG4tcHJpbWFyeTpob3Zlcjpub3QoOmRpc2FibGVkKSB7XG4gIGJhY2tncm91bmQ6ICM0MGE5ZmY7XG59XG5cbi5idG4tcHJpbWFyeTpkaXNhYmxlZCB7XG4gIG9wYWNpdHk6IDAuNTtcbiAgY3Vyc29yOiBub3QtYWxsb3dlZDtcbn1cblxuLmJ0bi1zZWNvbmRhcnkge1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgY29sb3I6ICM2NjY7XG4gIGJvcmRlcjogMXB4IHNvbGlkICNlMGUwZTA7XG59XG5cbi5idG4tc2Vjb25kYXJ5OmhvdmVyIHtcbiAgYm9yZGVyLWNvbG9yOiAjMTg5MGZmO1xuICBjb2xvcjogIzE4OTBmZjtcbn1cblxuLmJ0bi1zdWNjZXNzIHtcbiAgYmFja2dyb3VuZDogIzUyYzQxYTtcbiAgY29sb3I6IHdoaXRlO1xufVxuXG4uYnRuLXN1Y2Nlc3M6aG92ZXI6bm90KDpkaXNhYmxlZCkge1xuICBiYWNrZ3JvdW5kOiAjNzNkMTNkO1xufVxuXG4uYnRuLXN1Y2Nlc3M6ZGlzYWJsZWQge1xuICBvcGFjaXR5OiAwLjU7XG4gIGN1cnNvcjogbm90LWFsbG93ZWQ7XG59XG5cbi8qIOaooeaAgeahhuagt+W8jyAqL1xuLm1vZGFsLW92ZXJsYXkge1xuICBwb3NpdGlvbjogZml4ZWQ7XG4gIHRvcDogMDtcbiAgbGVmdDogMDtcbiAgcmlnaHQ6IDA7XG4gIGJvdHRvbTogMDtcbiAgYmFja2dyb3VuZDogcmdiYSgwLCAwLCAwLCAwLjUpO1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBqdXN0aWZ5LWNvbnRlbnQ6IGNlbnRlcjtcbiAgei1pbmRleDogMTAwMDtcbiAgcGFkZGluZzogMjBweDtcbn1cblxuLm1vZGFsLWNvbnRlbnQge1xuICBiYWNrZ3JvdW5kOiB3aGl0ZTtcbiAgYm9yZGVyLXJhZGl1czogOHB4O1xuICBtYXgtd2lkdGg6IDYwMHB4O1xuICB3aWR0aDogMTAwJTtcbiAgbWF4LWhlaWdodDogOTB2aDtcbiAgZGlzcGxheTogZmxleDtcbiAgZmxleC1kaXJlY3Rpb246IGNvbHVtbjtcbiAgYm94LXNoYWRvdzogMCA0cHggMjBweCByZ2JhKDAsIDAsIDAsIDAuMTUpO1xufVxuXG4ubW9kYWwtaGVhZGVyIHtcbiAgZGlzcGxheTogZmxleDtcbiAganVzdGlmeS1jb250ZW50OiBzcGFjZS1iZXR3ZWVuO1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBwYWRkaW5nOiAyMHB4IDI0cHg7XG4gIGJvcmRlci1ib3R0b206IDFweCBzb2xpZCAjZTBlMGUwO1xufVxuXG4ubW9kYWwtaGVhZGVyLWFjdGlvbnMge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDEycHg7XG59XG5cbi5yZWNyYXdsLWJ0biB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogNnB4O1xuICBwYWRkaW5nOiA2cHggMTJweDtcbiAgYm9yZGVyOiAxcHggc29saWQgIzUyYzQxYTtcbiAgYmFja2dyb3VuZDogd2hpdGU7XG4gIGNvbG9yOiAjNTJjNDFhO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgZm9udC1zaXplOiAxNHB4O1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbn1cblxuLnJlY3Jhd2wtYnRuOmhvdmVyOm5vdCg6ZGlzYWJsZWQpIHtcbiAgYmFja2dyb3VuZDogI2Y2ZmZlZDtcbiAgYm9yZGVyLWNvbG9yOiAjNzNkMTNkO1xuICBjb2xvcjogIzczZDEzZDtcbn1cblxuLnJlY3Jhd2wtYnRuOmRpc2FibGVkIHtcbiAgb3BhY2l0eTogMC42O1xuICBjdXJzb3I6IG5vdC1hbGxvd2VkO1xufVxuXG4ucmVjcmF3bC1idG4gc3ZnIHtcbiAgd2lkdGg6IDE2cHg7XG4gIGhlaWdodDogMTZweDtcbiAgc3Ryb2tlLXdpZHRoOiAyO1xufVxuXG4ucmVjcmF3bC1idG4gc3ZnLnNwaW5uaW5nLFxuLmFpLWZpbHRlci1idG4gc3ZnLnNwaW5uaW5nIHtcbiAgYW5pbWF0aW9uOiBzcGluIDFzIGxpbmVhciBpbmZpbml0ZTtcbn1cblxuQGtleWZyYW1lcyBzcGluIHtcbiAgZnJvbSB7IHRyYW5zZm9ybTogcm90YXRlKDBkZWcpOyB9XG4gIHRvIHsgdHJhbnNmb3JtOiByb3RhdGUoMzYwZGVnKTsgfVxufVxuXG4uZXh0ZXJuYWwtbGluay1idG4ge1xuICBkaXNwbGF5OiBmbGV4O1xuICBhbGlnbi1pdGVtczogY2VudGVyO1xuICBnYXA6IDZweDtcbiAgcGFkZGluZzogNnB4IDEycHg7XG4gIGJvcmRlcjogMXB4IHNvbGlkICMxODkwZmY7XG4gIGJhY2tncm91bmQ6IHdoaXRlO1xuICBjb2xvcjogIzE4OTBmZjtcbiAgYm9yZGVyLXJhZGl1czogNHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgdGV4dC1kZWNvcmF0aW9uOiBub25lO1xuICB0cmFuc2l0aW9uOiBhbGwgMC4ycztcbn1cblxuLmV4dGVybmFsLWxpbmstYnRuOmhvdmVyIHtcbiAgYmFja2dyb3VuZDogI2YwZjdmZjtcbiAgYm9yZGVyLWNvbG9yOiAjNDBhOWZmO1xuICBjb2xvcjogIzQwYTlmZjtcbn1cblxuLmV4dGVybmFsLWxpbmstYnRuIHN2ZyB7XG4gIHdpZHRoOiAxNnB4O1xuICBoZWlnaHQ6IDE2cHg7XG4gIHN0cm9rZS13aWR0aDogMjtcbn1cblxuLm1vZGFsLWhlYWRlciBoMiB7XG4gIGZvbnQtc2l6ZTogMjBweDtcbiAgZm9udC13ZWlnaHQ6IDYwMDtcbiAgY29sb3I6ICMxYTFhMWE7XG4gIG1hcmdpbjogMDtcbn1cblxuLmFydGljbGUtaWQtYmFkZ2Uge1xuICBmb250LXNpemU6IDEycHg7XG4gIGZvbnQtd2VpZ2h0OiBub3JtYWw7XG4gIGNvbG9yOiAjOTk5O1xufVxuXG4ubW9kYWwtY2xvc2Uge1xuICB3aWR0aDogMzJweDtcbiAgaGVpZ2h0OiAzMnB4O1xuICBib3JkZXI6IG5vbmU7XG4gIGJhY2tncm91bmQ6IHRyYW5zcGFyZW50O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGp1c3RpZnktY29udGVudDogY2VudGVyO1xuICBib3JkZXItcmFkaXVzOiA0cHg7XG4gIHRyYW5zaXRpb246IGFsbCAwLjJzO1xuICBwYWRkaW5nOiAwO1xufVxuXG4ubW9kYWwtY2xvc2U6aG92ZXIge1xuICBiYWNrZ3JvdW5kOiAjZjVmNWY1O1xufVxuXG4ubW9kYWwtY2xvc2Ugc3ZnIHtcbiAgd2lkdGg6IDIwcHg7XG4gIGhlaWdodDogMjBweDtcbiAgc3Ryb2tlLXdpZHRoOiAyO1xuICBjb2xvcjogIzY2Njtcbn1cblxuLm1vZGFsLWJvZHkge1xuICBmbGV4OiAxO1xuICBvdmVyZmxvdy15OiBhdXRvO1xuICBwYWRkaW5nOiAyNHB4O1xuICBtaW4taGVpZ2h0OiAwO1xufVxuXG4vKiDmlofnq6DlhoXlrrnmn6XnnIvmqKHmgIHmoYYgKi9cbi5hcnRpY2xlLWNvbnRlbnQtbW9kYWwge1xuICBtYXgtd2lkdGg6IDkwMHB4O1xufVxuXG4uYXJ0aWNsZS1jb250ZW50LXRleHQge1xuICBmb250LXNpemU6IDE0cHg7XG4gIGxpbmUtaGVpZ2h0OiAxLjg7XG4gIGNvbG9yOiAjMzMzO1xuICB3aGl0ZS1zcGFjZTogcHJlLXdyYXA7XG4gIHdvcmQtd3JhcDogYnJlYWstd29yZDtcbn1cblxuLmFydGljbGUtY29udGVudC10ZXh0IHByZSB7XG4gIG1hcmdpbjogMDtcbiAgZm9udC1mYW1pbHk6IGluaGVyaXQ7XG4gIHdoaXRlLXNwYWNlOiBwcmUtd3JhcDtcbiAgd29yZC13cmFwOiBicmVhay13b3JkO1xufVxuXG4ubG9hZGluZy1jb250ZW50LFxuLmVtcHR5LWNvbnRlbnQge1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIHBhZGRpbmc6IDQwcHggMjBweDtcbiAgY29sb3I6ICM5OTk7XG4gIGZvbnQtc2l6ZTogMTRweDtcbn1cblxuLyog5Y2V6YCJ5ZKM5aSN6YCJ5qGG57uE5qC35byPICovXG4ucmFkaW8tZ3JvdXAsXG4uY2hlY2tib3gtZ3JvdXAge1xuICBkaXNwbGF5OiBmbGV4O1xuICBnYXA6IDI0cHg7XG59XG5cbi5yYWRpby1sYWJlbCxcbi5jaGVja2JveC1sYWJlbCB7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIGdhcDogOHB4O1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIGZvbnQtc2l6ZTogMTRweDtcbiAgY29sb3I6ICMzMzM7XG59XG5cbi5yYWRpby1sYWJlbCBpbnB1dCxcbi5jaGVja2JveC1sYWJlbCBpbnB1dCB7XG4gIHdpZHRoOiAxNnB4O1xuICBoZWlnaHQ6IDE2cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgYWNjZW50LWNvbG9yOiAjMTg5MGZmO1xufVxuXG4ucmFkaW8tbGFiZWwgc3Bhbixcbi5jaGVja2JveC1sYWJlbCBzcGFuIHtcbiAgdXNlci1zZWxlY3Q6IG5vbmU7XG59XG5cbjwvc3R5bGU+XG4iXSwibWFwcGluZ3MiOiJBQTRxQkEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7Ozs7Ozs7QUFFcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRXBDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRWhDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRS9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDOztBQUVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEYsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkO0FBQ0EsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUYsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUYsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRTVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0ksQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNJLENBQUM7O0FBRUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3Qzs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRS9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7QUFFL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RFLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUM7O0FBRUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0UsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0I7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckI7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVoRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkUsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9DLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkQsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RSxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDO0FBQ0YsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzRixDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0I7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkUsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3RCxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUM7QUFDRixDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQztBQUNGLENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQztBQUNGLENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkQsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdEOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNWLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RSxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekUsQ0FBQzs7QUFFRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0RSxDQUFDOztBQUVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hELENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRTVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEgsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDOztBQUVGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUU1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUU1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVMLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7QUFFSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7QUFFSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUV2RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDOztBQUVKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7O0FBRWxELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQzs7QUFFTCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9DOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0MsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25FLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEI7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RGLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2Qjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1Q7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakUsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BDLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQztBQUNGLENBQUM7O0FBRUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEMsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDO0FBQ0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQztBQUNGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUM7O0FBRUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUM7QUFDRixDQUFDOztBQUVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvRCxDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQztBQUNGOztBQUVBLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNkLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1QsQ0FBQyxDQUFDO0FBQ0YsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUM7QUFDRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdFLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0UsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QyxDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNULENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkU7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkUsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNyQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNWLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0RCxDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzRixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0UsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNWLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDZixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1RSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDYixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEUsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25CLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2YsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDL0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzdCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RSxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQy9FLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNmLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDN0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3BFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNSLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM5QyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEYsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZFLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM1QixDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0osQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25DLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkMsQ0FBQyxDQUFDO0FBQ0Y7O0FBRUEsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pFLENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNOLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlCLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hHLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3JELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzNCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzFCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNYLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3ZGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDcEUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEUsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDO0FBQ0gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25ELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDNUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMxRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDSixDQUFDLENBQUMsQ0FBQztBQUNILENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0MsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekcsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNuQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDM0IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ0wsQ0FBQyxDQUFDLENBQUM7QUFDSCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDckQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN6RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzlDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2pDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN4RCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ25FLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwRSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDUixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1AsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNQLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ3RGLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDekIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1IsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbkUsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNiLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ04sQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ1gsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2xCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDbEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN0QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNaLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUM3QixDQUFDLENBQUM7QUFDRjs7QUFFQSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDdkMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDakQsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQ2hDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNoQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNqQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDaEMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNKLENBQUMsQ0FBQztBQUNGLENBQUM7QUFDRCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDO0FBQzVCLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDOUMsQ0FBQyxDQUFDO0FBQ0YsQ0FBQztBQUNELENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUN2QixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNwQyxDQUFDLENBQUM7QUFDRixDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDeEIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUNsQyxDQUFDLENBQUM7QUFDRixDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDWixDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDMUIsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQztBQUMzQyxDQUFDLENBQUM7QUFDRixDQUFDO0FBQ0QsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7QUFDVCxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUMsQ0FB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