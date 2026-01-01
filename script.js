// ==================== 光晕光标逻辑 ====================
        const glowCursor = document.getElementById('glowCursor');
        let mouseX = 0, mouseY = 0;
        let cursorX = 0, cursorY = 0;
        
        // 鼠标移动时更新光标位置
        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
            
            // 更新光晕位置
            glowCursor.style.left = `${mouseX}px`;
            glowCursor.style.top = `${mouseY}px`;
            
            // 悬停效果：在可点击元素上增强光晕
            const hoveredElement = document.elementFromPoint(mouseX, mouseY);
            if (hoveredElement && (
                hoveredElement.tagName === 'A' || 
                hoveredElement.tagName === 'BUTTON' ||
                hoveredElement.classList.contains('nav-icon')
            )) {
                glowCursor.style.width = '100px';
                glowCursor.style.height = '100px';
                glowCursor.style.opacity = '0.9';
            } else {
                glowCursor.style.width = '80px';
                glowCursor.style.height = '80px';
                glowCursor.style.opacity = '1';
            }
        });
        
        // 鼠标离开窗口时淡出光晕
        document.addEventListener('mouseleave', () => {
            glowCursor.style.opacity = '0';
        });
        
        document.addEventListener('mouseenter', () => {
            glowCursor.style.opacity = '1';
        });
        
        // ==================== 导航栏交互 ====================
        const navLinks = document.getElementById('navLinks');
        const navHighlight = document.getElementById('navHighlight');
        const links = navLinks.querySelectorAll('a');
        
        // 初始化导航高光位置
        updateNavHighlight(navLinks.querySelector('.active'));
        
        // 为每个链接添加交互
        links.forEach(link => {
            link.addEventListener('mouseenter', () => {
                updateNavHighlight(link);
            });
            
            link.addEventListener('mouseleave', () => {
                updateNavHighlight(navLinks.querySelector('.active'));
            });
            
            link.addEventListener('click', (e) => {
                links.forEach(a => a.classList.remove('active'));
                link.classList.add('active');
                updateNavHighlight(link);
                
                // 点击时创建涟漪效果
                createRippleEffect(e);
            });
        });
        
        // 更新导航高光位置
        function updateNavHighlight(target) {
            if (!target) return;
            
            const rect = target.getBoundingClientRect();
            const parentRect = navLinks.getBoundingClientRect();
            
            navHighlight.style.left = `${rect.left - parentRect.left}px`;
            navHighlight.style.width = `${rect.width}px`;
        }
        
        // 创建涟漪效果
        function createRippleEffect(e) {
            const ripple = document.createElement('div');
            ripple.style.position = 'fixed';
            ripple.style.left = `${e.clientX}px`;
            ripple.style.top = `${e.clientY}px`;
            ripple.style.width = '10px';
            ripple.style.height = '10px';
            ripple.style.background = 'radial-gradient(circle, rgba(59,130,246,0.3) 0%, transparent 70%)';
            ripple.style.borderRadius = '50%';
            ripple.style.pointerEvents = 'none';
            ripple.style.zIndex = '9998';
            ripple.style.transform = 'translate(-50%, -50%)';
            
            document.body.appendChild(ripple);
            
            // 涟漪动画
            ripple.animate([
                { opacity: 0.8, transform: 'translate(-50%, -50%) scale(1)' },
                { opacity: 0, transform: 'translate(-50%, -50%) scale(15)' }
            ], {
                duration: 800,
                easing: 'ease-out'
            });
            
            setTimeout(() => {
                if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
            }, 800);
        }
        
        // ==================== 移动端适配 ====================
        function checkMobile() {
            if (window.innerWidth <= 768) {
                glowCursor.style.display = 'none';
            } else {
                glowCursor.style.display = 'block';
            }
        }
        
        // 初始检查和窗口大小变化监听
        checkMobile();
        window.addEventListener('resize', checkMobile);