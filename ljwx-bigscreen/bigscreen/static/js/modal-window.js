/**
 * 统一模态窗口组件
 * 用于personal.html和bigscreen_main.html的弹窗功能
 * @Author bruno.gao
 * @CreateTime 2025-09-08
 */

class ModalWindow {
    constructor(options = {}) {
        this.options = {
            width: options.width || '90%',
            height: options.height || '90%',
            title: options.title || '',
            showHeader: options.showHeader !== false, // 默认显示头部
            showFilters: options.showFilters === true, // 默认不显示过滤器
            closeOnBackdrop: options.closeOnBackdrop !== false, // 默认允许点击背景关闭
            customStyles: options.customStyles || {},
            onClose: options.onClose || null,
            onLoad: options.onLoad || null
        };
        
        this.modalContainer = null;
        this.iframe = null;
        this.isOpen = false;
    }

    /**
     * 创建并显示模态窗口
     * @param {string} url - iframe的URL
     * @param {Object} data - 传递给iframe的数据
     * @param {string} dataType - 数据类型标识
     */
    open(url, data = null, dataType = null) {
        if (this.isOpen) {
            console.warn('⚠️ 模态窗口已经打开');
            return;
        }

        this.createModal(url);
        this.addStyles();
        this.addEventListeners();
        this.show();
        
        // 处理数据传递
        if (data && dataType) {
            this.handleDataTransfer(data, dataType);
        }
        
        this.isOpen = true;
        console.log('✅ 模态窗口已创建并显示');
    }

    /**
     * 创建模态窗口HTML结构
     * @param {string} url 
     */
    createModal(url) {
        this.modalContainer = document.createElement('div');
        this.modalContainer.className = 'unified-modal-container';
        
        const headerHTML = this.options.showHeader ? this.createHeaderHTML() : '';
        
        this.modalContainer.innerHTML = `
            <div class="unified-modal-content">
                <button class="unified-modal-close" title="关闭">✖</button>
                ${headerHTML}
                <iframe src="${url}" class="unified-modal-iframe"></iframe>
            </div>
        `;
        
        document.body.appendChild(this.modalContainer);
        this.iframe = this.modalContainer.querySelector('.unified-modal-iframe');
    }

    /**
     * 创建头部HTML（包含标题和过滤器）
     */
    createHeaderHTML() {
        if (!this.options.showFilters && !this.options.title) {
            return '';
        }

        let headerContent = '';
        
        if (this.options.title) {
            headerContent += `<h3 class="unified-modal-title">${this.options.title}</h3>`;
        }
        
        if (this.options.showFilters) {
            headerContent += `
                <div class="unified-modal-filters">
                    <div class="unified-select-group">
                        <select id="unifiedModalDeptSelect" class="unified-modal-select">
                            <option value="">选择部门</option>
                        </select>
                        <select id="unifiedModalUserSelect" class="unified-modal-select">
                            <option value="">选择用户</option>
                        </select>
                    </div>
                </div>
            `;
        }
        
        return `<div class="unified-modal-header">${headerContent}</div>`;
    }

    /**
     * 添加统一样式
     */
    addStyles() {
        if (document.getElementById('unifiedModalStyles')) {
            return; // 样式已存在
        }

        const style = document.createElement('style');
        style.id = 'unifiedModalStyles';
        style.textContent = `
            .unified-modal-container {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s ease;
            }
            
            .unified-modal-container.show {
                opacity: 1;
            }
            
            .unified-modal-content {
                width: ${this.options.width};
                height: ${this.options.height};
                background: rgba(0,21,41,0.95);
                border-radius: 8px;
                position: relative;
                border: 1px solid rgba(0, 228, 255, 0.3);
                box-shadow: 0 0 20px rgba(0, 228, 255, 0.2);
                display: flex;
                flex-direction: column;
                transform: scale(0.9);
                transition: transform 0.3s ease;
            }
            
            .unified-modal-container.show .unified-modal-content {
                transform: scale(1);
            }
            
            .unified-modal-close {
                position: absolute;
                top: 10px;
                right: 15px;
                background: #ff4757;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                cursor: pointer;
                z-index: 10001;
                font-size: 14px;
                font-weight: bold;
                transition: all 0.2s ease;
            }
            
            .unified-modal-close:hover {
                background: #ff3742;
                transform: scale(1.05);
            }
            
            .unified-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                border-bottom: 1px solid rgba(0, 228, 255, 0.3);
                background: rgba(0, 21, 41, 0.9);
                border-radius: 8px 8px 0 0;
                min-height: 50px;
            }
            
            .unified-modal-title {
                color: #00e4ff;
                font-size: 18px;
                font-weight: bold;
                margin: 0;
                text-shadow: 0 0 10px rgba(0, 228, 255, 0.5);
            }
            
            .unified-modal-filters {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .unified-select-group {
                display: flex;
                gap: 10px;
            }
            
            .unified-modal-select {
                background: rgba(0, 21, 41, 0.8);
                border: 1px solid rgba(0, 228, 255, 0.3);
                border-radius: 4px;
                color: #fff;
                padding: 6px 12px;
                font-size: 12px;
                min-width: 100px;
                transition: all 0.2s ease;
            }
            
            .unified-modal-select:hover {
                border-color: rgba(0, 228, 255, 0.6);
                box-shadow: 0 0 5px rgba(0, 228, 255, 0.3);
            }
            
            .unified-modal-select:focus {
                outline: none;
                border-color: #00e4ff;
                box-shadow: 0 0 10px rgba(0, 228, 255, 0.5);
            }
            
            .unified-modal-select option {
                background: rgba(0,21,41,0.95);
                color: #fff;
            }
            
            .unified-modal-iframe {
                flex: 1;
                width: 100%;
                border: none;
                border-radius: 0 0 8px 8px;
                background: transparent;
            }
            
            /* 响应式设计 */
            @media (max-width: 768px) {
                .unified-modal-content {
                    width: 95%;
                    height: 95%;
                    margin: 10px;
                }
                
                .unified-modal-header {
                    flex-direction: column;
                    gap: 10px;
                    padding: 10px;
                }
                
                .unified-modal-title {
                    font-size: 16px;
                }
                
                .unified-select-group {
                    flex-direction: column;
                    gap: 5px;
                    width: 100%;
                }
                
                .unified-modal-select {
                    width: 100%;
                }
            }
            
            /* 自定义样式支持 */
            ${this.options.customStyles}
        `;
        
        document.head.appendChild(style);
    }

    /**
     * 添加事件监听器
     */
    addEventListeners() {
        // 关闭按钮事件
        const closeBtn = this.modalContainer.querySelector('.unified-modal-close');
        closeBtn.addEventListener('click', () => this.close());
        
        // 点击背景关闭（可选）
        if (this.options.closeOnBackdrop) {
            this.modalContainer.addEventListener('click', (e) => {
                if (e.target === this.modalContainer) {
                    this.close();
                }
            });
        }
        
        // ESC键关闭
        this.escKeyHandler = (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        };
        document.addEventListener('keydown', this.escKeyHandler);
        
        // iframe加载完成事件
        if (this.iframe && this.options.onLoad) {
            this.iframe.onload = this.options.onLoad;
        }
    }

    /**
     * 显示模态窗口（带动画）
     */
    show() {
        // 强制重绘以确保过渡动画生效
        this.modalContainer.offsetHeight;
        this.modalContainer.classList.add('show');
    }

    /**
     * 处理数据传递到iframe
     * @param {Object} data 
     * @param {string} dataType 
     */
    handleDataTransfer(data, dataType) {
        if (!this.iframe) return;

        this.iframe.onload = () => {
            console.log('📤 iframe加载完成，准备传递数据:', { dataType, hasData: !!data });
            
            setTimeout(() => {
                try {
                    this.iframe.contentWindow.postMessage({
                        type: dataType,
                        data: data
                    }, '*');
                    console.log('✅ 数据传递完成');
                } catch (e) {
                    console.error('❌ 无法传递数据到iframe:', e);
                }
            }, 100);
        };
    }

    /**
     * 关闭模态窗口
     */
    close() {
        if (!this.isOpen) return;

        // 执行关闭回调
        if (this.options.onClose) {
            this.options.onClose();
        }

        // 添加关闭动画
        this.modalContainer.classList.remove('show');
        
        // 动画结束后移除DOM元素
        setTimeout(() => {
            if (this.modalContainer && this.modalContainer.parentNode) {
                document.body.removeChild(this.modalContainer);
            }
            
            // 清理事件监听器
            if (this.escKeyHandler) {
                document.removeEventListener('keydown', this.escKeyHandler);
            }
            
            this.isOpen = false;
            console.log('✅ 模态窗口已关闭');
        }, 300);
    }

    /**
     * 更新iframe的URL
     * @param {string} newUrl 
     */
    updateUrl(newUrl) {
        if (this.iframe) {
            this.iframe.src = newUrl;
        }
    }

    /**
     * 获取当前iframe的window对象
     */
    getIframeWindow() {
        return this.iframe ? this.iframe.contentWindow : null;
    }
}

// 全局静态方法，用于快速创建模态窗口
ModalWindow.create = function(url, options = {}) {
    const modal = new ModalWindow(options);
    modal.open(url, options.data, options.dataType);
    return modal;
};

// 兼容原有的createModalWindow函数
function createModalWindow(url, title, width, height, data, dataType) {
    // 兼容不同的参数传递方式
    let options = {};
    
    if (typeof title === 'object') {
        // 如果第二个参数是对象，则使用新的方式
        options = title;
    } else {
        // 使用传统方式
        options = {
            title: title,
            width: width || '90%',
            height: height || '90%',
            data: data,
            dataType: dataType
        };
    }
    
    return ModalWindow.create(url, options);
}

// 导出到全局作用域
if (typeof window !== 'undefined') {
    window.ModalWindow = ModalWindow;
    window.createModalWindow = createModalWindow;
}

console.log('✅ 统一模态窗口组件已加载');