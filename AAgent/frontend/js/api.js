/**
 * API调用封装
 * 统一处理与后端的通信
 */

const API_BASE_URL = '/api';

/**
 * 通用GET请求
 */
async function apiGet(endpoint) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API GET Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * 通用POST请求
 */
async function apiPost(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP Error: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`API POST Error [${endpoint}]:`, error);
        throw error;
    }
}

/**
 * 获取讨论列表
 * @param {string} status - 可选的状态筛选
 */
async function getDiscussions(status = '') {
    const query = status ? `?status=${status}` : '';
    return await apiGet(`/discussions${query}`);
}

/**
 * 获取单个讨论详情
 * @param {number} id - 讨论ID
 */
async function getDiscussion(id) {
    return await apiGet(`/discussions/${id}`);
}

/**
 * 创建新讨论
 * @param {Object} data - 讨论数据
 * @param {string} data.title - 讨论标题
 * @param {string} data.description - 讨论描述
 * @param {Array} data.participants - 参与专家数组
 */
async function createDiscussion(data) {
    return await apiPost('/discussions', data);
}

/**
 * 启动讨论
 * @param {number} id - 讨论ID
 */
async function startDiscussion(id) {
    return await apiPost(`/discussions/${id}/start`, {});
}

/**
 * 获取专家模板列表
 */
async function getExpertTemplates() {
    return await apiGet('/expert-templates');
}

/**
 * 连接SSE事件流
 * @param {number} discussionId - 讨论ID
 * @param {Object} handlers - 事件处理器对象
 * @param {Function} handlers.onMessage - 消息事件处理器
 * @param {Function} handlers.onConsensus - 共识事件处理器
 * @param {Function} handlers.onComplete - 完成事件处理器
 * @param {Function} handlers.onError - 错误事件处理器
 */
function connectSSE(discussionId, handlers) {
    const eventSource = new EventSource(`${API_BASE_URL}/discussions/${discussionId}/events`);
    
    eventSource.addEventListener('message', (event) => {
        try {
            const data = JSON.parse(event.data);
            handlers.onMessage?.(data);
        } catch (error) {
            console.error('SSE Message Parse Error:', error);
        }
    });
    
    eventSource.addEventListener('consensus', (event) => {
        try {
            const data = JSON.parse(event.data);
            handlers.onConsensus?.(data);
        } catch (error) {
            console.error('SSE Consensus Parse Error:', error);
        }
    });
    
    eventSource.addEventListener('complete', (event) => {
        try {
            const data = JSON.parse(event.data);
            handlers.onComplete?.(data);
            eventSource.close();
        } catch (error) {
            console.error('SSE Complete Parse Error:', error);
        }
    });

    eventSource.addEventListener('status', (event) => {
        try {
            const data = JSON.parse(event.data);
            handlers.onStatus?.(data);
        } catch (error) {
            console.error('SSE Status Parse Error:', error);
        }
    });
    
    eventSource.onerror = (error) => {
        console.error('SSE Connection Error:', error);
        handlers.onError?.(error);
        eventSource.close();
    };
    
    return eventSource;
}

/**
 * 格式化日期时间
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    // 小于1分钟
    if (diff < 60000) {
        return '刚刚';
    }
    
    // 小于1小时
    if (diff < 3600000) {
        const minutes = Math.floor(diff / 60000);
        return `${minutes}分钟前`;
    }
    
    // 小于24小时
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}小时前`;
    }
    
    // 大于24小时，显示具体日期
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * 获取状态显示文本和样式
 */
function getStatusDisplay(status) {
    const statusMap = {
        pending: { text: '待启动', class: 'bg-yellow-600' },
        running: { text: '进行中', class: 'bg-blue-600 animate-pulse' },
        completed: { text: '已完成', class: 'bg-green-600' },
        failed: { text: '失败', class: 'bg-red-600' }
    };
    
    return statusMap[status] || { text: '未知', class: 'bg-gray-600' };
}
