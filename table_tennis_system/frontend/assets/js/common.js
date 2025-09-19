// 全局配置
const CONFIG = {
    API_BASE_URL: 'http://localhost:5001/api',
    TOKEN_KEY: 'authToken',
    USER_KEY: 'currentUser'
};

// 全局变量
let currentUser = null;
let authToken = null;

// 页面加载时执行
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
});

// 初始化页面
function initializePage() {
    checkAuthStatus();
    setupAxiosInterceptors();
    setupGlobalEventListeners();
}

// 检查登录状态
function checkAuthStatus() {
    const token = localStorage.getItem(CONFIG.TOKEN_KEY);
    const user = localStorage.getItem(CONFIG.USER_KEY);

    if (token && user) {
        authToken = token;
        currentUser = JSON.parse(user);

        // 设置axios默认请求头
        axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;

        // 检查用户权限
        if (!checkPagePermission()) {
            redirectToLogin();
            return;
        }

        // 更新用户信息显示
        updateUserInfo();
    } else {
        // 如果不是登录页面，重定向到登录页
        if (!window.location.pathname.includes('index.html') && !window.location.pathname.endsWith('/')) {
            redirectToLogin();
        }
    }
}

// 检查页面权限
function checkPagePermission() {
    if (!currentUser) return false;

    const path = window.location.pathname;
    const userType = currentUser.user_type;

    // 根据用户类型检查页面访问权限
    if (path.includes('/student/') && userType !== 'student') {
        return false;
    }
    if (path.includes('/coach/') && userType !== 'coach') {
        return false;
    }
    if (path.includes('/admin/') && !['campus_admin', 'super_admin'].includes(userType)) {
        return false;
    }

    return true;
}

// 设置Axios拦截器
function setupAxiosInterceptors() {
    // 请求拦截器
    axios.interceptors.request.use(
        config => {
            // 显示加载状态
            showLoading();
            return config;
        },
        error => {
            hideLoading();
            return Promise.reject(error);
        }
    );

    // 响应拦截器
    axios.interceptors.response.use(
        response => {
            hideLoading();
            return response;
        },
        error => {
            hideLoading();

            // 处理401错误（未授权）
            if (error.response && error.response.status === 401) {
                logout(false);
                showToast('登录已过期，请重新登录', 'error');
                return Promise.reject(error);
            }

            // 处理网络错误
            if (error.code === 'NETWORK_ERROR') {
                showToast('网络连接失败，请检查网络设置', 'error');
                return Promise.reject(error);
            }

            return Promise.reject(error);
        }
    );
}

// 设置全局事件监听器
function setupGlobalEventListeners() {
    // 监听退出登录
    document.addEventListener('click', function(e) {
        if (e.target.matches('[data-action="logout"]')) {
            e.preventDefault();
            confirmLogout();
        }
    });

    // 监听快捷键
    document.addEventListener('keydown', function(e) {
        // Ctrl+L 快速登出
        if (e.ctrlKey && e.key === 'l') {
            e.preventDefault();
            confirmLogout();
        }
    });
}

// 更新用户信息显示
function updateUserInfo() {
    if (!currentUser) return;

    // 更新用户名显示
    const userNameElements = document.querySelectorAll('[data-user="name"]');
    userNameElements.forEach(el => {
        el.textContent = currentUser.real_name || currentUser.username;
    });

    // 更新用户头像
    const userAvatarElements = document.querySelectorAll('[data-user="avatar"]');
    userAvatarElements.forEach(el => {
        const initials = (currentUser.real_name || currentUser.username).charAt(0).toUpperCase();
        el.textContent = initials;
        el.setAttribute('title', currentUser.real_name || currentUser.username);
    });

    // 更新用户类型显示
    const userTypeElements = document.querySelectorAll('[data-user="type"]');
    userTypeElements.forEach(el => {
        el.textContent = getUserTypeText(currentUser.user_type);
    });
}

// 获取用户类型文本
function getUserTypeText(userType) {
    const types = {
        'student': '学员',
        'coach': '教练',
        'campus_admin': '校区管理员',
        'super_admin': '超级管理员'
    };
    return types[userType] || userType;
}

// 登录函数
async function login(username, password) {
    try {
        const response = await axios.post(`${CONFIG.API_BASE_URL}/auth/login`, {
            username,
            password
        });

        if (response.data.success) {
            authToken = response.data.data.access_token;
            currentUser = response.data.data.user;

            // 保存到本地存储
            localStorage.setItem(CONFIG.TOKEN_KEY, authToken);
            localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(currentUser));

            // 设置默认请求头
            axios.defaults.headers.common['Authorization'] = `Bearer ${authToken}`;

            return { success: true, user: currentUser };
        } else {
            return { success: false, message: response.data.message };
        }
    } catch (error) {
        return {
            success: false,
            message: error.response?.data?.message || '登录失败，请检查网络连接'
        };
    }
}

// 登出函数
function logout(showConfirm = true) {
    if (showConfirm) {
        confirmLogout();
        return;
    }

    // 清除本地存储
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.USER_KEY);

    // 清除全局变量
    currentUser = null;
    authToken = null;

    // 清除axios默认请求头
    delete axios.defaults.headers.common['Authorization'];

    // 重定向到登录页
    redirectToLogin();
}

// 确认登出
function confirmLogout() {
    if (confirm('确定要退出登录吗？')) {
        logout(false);
    }
}

// 重定向到登录页
function redirectToLogin() {
    window.location.href = '/';
}

// 重定向到对应的仪表板
function redirectToDashboard(userType = null) {
    const type = userType || (currentUser ? currentUser.user_type : null);
    if (!type) return;

    const urls = {
        'student': '/frontend/pages/student/dashboard.html',
        'coach': '/frontend/pages/coach/dashboard.html',
        'campus_admin': '/frontend/pages/admin/dashboard.html',
        'super_admin': '/frontend/pages/admin/dashboard.html'
    };

    const url = urls[type];
    if (url) {
        window.location.href = url;
    }
}

// API请求封装
const API = {
    // GET请求
    async get(url, params = {}) {
        try {
            const response = await axios.get(`${CONFIG.API_BASE_URL}${url}`, { params });
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                message: error.response?.data?.message || '请求失败',
                error
            };
        }
    },

    // POST请求
    async post(url, data = {}) {
        try {
            const response = await axios.post(`${CONFIG.API_BASE_URL}${url}`, data);
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                message: error.response?.data?.message || '请求失败',
                error
            };
        }
    },

    // PUT请求
    async put(url, data = {}) {
        try {
            const response = await axios.put(`${CONFIG.API_BASE_URL}${url}`, data);
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                message: error.response?.data?.message || '请求失败',
                error
            };
        }
    },

    // DELETE请求
    async delete(url) {
        try {
            const response = await axios.delete(`${CONFIG.API_BASE_URL}${url}`);
            return { success: true, data: response.data };
        } catch (error) {
            return {
                success: false,
                message: error.response?.data?.message || '请求失败',
                error
            };
        }
    }
};

// Toast提示函数
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = getOrCreateToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${getBootstrapColorClass(type)} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast, { delay: duration });
    bsToast.show();

    // 自动清理
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, duration + 500);
}

// 获取Bootstrap颜色类
function getBootstrapColorClass(type) {
    const colorMap = {
        'success': 'success',
        'error': 'danger',
        'warning': 'warning',
        'info': 'info'
    };
    return colorMap[type] || 'primary';
}

// 获取Toast图标
function getToastIcon(type) {
    const iconMap = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return iconMap[type] || 'info-circle';
}

// 获取或创建Toast容器
function getOrCreateToastContainer() {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    return container;
}

// 显示加载状态
function showLoading() {
    // 可以实现全局加载指示器
    const existingLoader = document.querySelector('.global-loader');
    if (!existingLoader) {
        const loader = document.createElement('div');
        loader.className = 'global-loader position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        loader.style.background = 'rgba(0, 0, 0, 0.5)';
        loader.style.zIndex = '9999';
        loader.innerHTML = '<div class="loading"></div>';
        document.body.appendChild(loader);
    }
}

// 隐藏加载状态
function hideLoading() {
    const loader = document.querySelector('.global-loader');
    if (loader) {
        loader.remove();
    }
}

// 格式化日期
function formatDate(dateString, format = 'YYYY-MM-DD') {
    if (!dateString) return '';

    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return format
        .replace('YYYY', year)
        .replace('MM', month)
        .replace('DD', day)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
}

// 格式化时间为相对时间
function formatRelativeTime(dateString) {
    if (!dateString) return '';

    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) {
        return '刚刚';
    } else if (diffInSeconds < 3600) {
        return `${Math.floor(diffInSeconds / 60)}分钟前`;
    } else if (diffInSeconds < 86400) {
        return `${Math.floor(diffInSeconds / 3600)}小时前`;
    } else if (diffInSeconds < 2592000) {
        return `${Math.floor(diffInSeconds / 86400)}天前`;
    } else {
        return formatDate(dateString);
    }
}

// 格式化货币
function formatCurrency(amount, currency = '¥') {
    if (typeof amount !== 'number') return currency + '0.00';
    return currency + amount.toFixed(2);
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 页面切换动画
function pageTransition(targetUrl) {
    document.body.style.opacity = '0.8';
    document.body.style.transform = 'scale(0.98)';
    document.body.style.transition = 'all 0.3s ease';

    setTimeout(() => {
        window.location.href = targetUrl;
    }, 300);
}

// 获取当前用户信息
function getCurrentUser() {
    return currentUser;
}

// 导出全局对象
window.TableTennisSystem = {
    CONFIG,
    API,
    login,
    logout,
    redirectToDashboard,
    showToast,
    formatDate,
    formatRelativeTime,
    formatCurrency,
    debounce,
    throttle,
    pageTransition
};