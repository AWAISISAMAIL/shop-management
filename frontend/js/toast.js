// ========================================
// GOHAR TRADERS - Toast Notification System
// ========================================

(function() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            display: flex;
            flex-direction: column;
            gap: 12px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    window.showToast = function(message, type = 'info') {
        const icons = {
            success: 'fa-check-circle',
            error: 'fa-times-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };
        const colors = {
            success: '#10B981',
            error: '#EF4444',
            warning: '#F59E0B',
            info: '#7C3AED'
        };

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.style.cssText = `
            background: #1F2937;
            border: 1px solid ${colors[type]};
            border-radius: 16px;
            padding: 14px 20px;
            min-width: 300px;
            max-width: 450px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: white;
            font-family: 'Segoe UI', sans-serif;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            backdrop-filter: blur(12px);
            pointer-events: auto;
            transform: translateX(120%);
            transition: transform 0.3s ease;
            opacity: 0.95;
        `;

        toast.innerHTML = `
            <i class="fas ${icons[type]}" style="color: ${colors[type]}; font-size: 22px;"></i>
            <span style="flex:1; font-size: 14px;">${message}</span>
        `;

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.transform = 'translateX(0)';
        }, 10);

        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => {
                if (toast.parentNode) {
                    container.removeChild(toast);
                }
            }, 300);
        }, 4000);
    };

    window.showConfirm = function(message, onConfirm, onCancel) {
        const overlay = document.createElement('div');
        overlay.className = 'confirm-overlay';
        overlay.style.cssText = `
            position: fixed;
            inset: 0;
            background: rgba(0,0,0,0.7);
            z-index: 10000;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: 'Segoe UI', sans-serif;
        `;

        const modal = document.createElement('div');
        modal.style.cssText = `
            background: #111827;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            color: white;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        `;

        modal.innerHTML = `
            <p style="font-size: 16px; margin-bottom: 24px;">${message}</p>
            <div style="display: flex; gap: 12px; justify-content: flex-end;">
                <button class="confirm-cancel-btn" style="
                    background: transparent;
                    border: 1px solid #7C3AED;
                    color: #7C3AED;
                    padding: 10px 20px;
                    border-radius: 12px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.2s;
                ">Cancel</button>
                <button class="confirm-ok-btn" style="
                    background: linear-gradient(135deg, #7C3AED, #A855F7);
                    border: none;
                    color: white;
                    padding: 10px 20px;
                    border-radius: 12px;
                    cursor: pointer;
                    font-weight: 600;
                    transition: all 0.2s;
                ">Confirm</button>
            </div>
        `;

        overlay.appendChild(modal);
        document.body.appendChild(overlay);

        const cancelBtn = modal.querySelector('.confirm-cancel-btn');
        const okBtn = modal.querySelector('.confirm-ok-btn');

        cancelBtn.onclick = () => {
            document.body.removeChild(overlay);
            if (onCancel) onCancel();
        };
        okBtn.onclick = () => {
            document.body.removeChild(overlay);
            onConfirm();
        };

        overlay.onclick = (e) => {
            if (e.target === overlay) {
                document.body.removeChild(overlay);
                if (onCancel) onCancel();
            }
        };
    };
})();