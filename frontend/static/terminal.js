/**
 * Web Terminal JavaScript
 * Handles WebSocket communication, user interactions, and UI updates
 */

class WebTerminal {
    constructor() {
        this.socket = null;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.currentSessionId = this.generateSessionId();
        this.currentUserId = 'anonymous';
        this.isConnected = false;
        this.commandSuggestions = [];
        
        // Initialize the terminal
        this.init();
    }
    
    init() {
        this.setupSocketConnection();
        this.setupEventListeners();
        this.setupKeyboardShortcuts();
        this.loadCommandHistory();
        this.focusInput();
    }
    
    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    setupSocketConnection() {
        // Initialize Socket.IO connection
        this.socket = io();
        
        // Connection event handlers
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.updateConnectionStatus('Connected', 'connected');
            this.showNotification('Connected to web terminal', 'success');
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.updateConnectionStatus('Disconnected', 'disconnected');
            this.showNotification('Disconnected from server', 'error');
        });
        
        this.socket.on('connect_error', () => {
            this.isConnected = false;
            this.updateConnectionStatus('Connection Error', 'disconnected');
            this.showNotification('Failed to connect to server', 'error');
        });
        
        // Command response handler
        this.socket.on('response', (data) => {
            this.handleServerResponse(data);
            this.hideLoading();
        });
        
        // Initial connection attempt
        this.updateConnectionStatus('Connecting...', 'connecting');
    }
    
    setupEventListeners() {
        const commandInput = document.getElementById('command-input');
        const sendButton = document.getElementById('send-button');
        const terminalOutput = document.getElementById('terminal-output');
        
        // Command input handlers
        commandInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        commandInput.addEventListener('input', (e) => this.handleInput(e));
        sendButton.addEventListener('click', () => this.executeCommand());
        
        // Control panel buttons
        document.getElementById('history-toggle').addEventListener('click', () => this.toggleHistory());
        document.getElementById('system-info-toggle').addEventListener('click', () => this.toggleSystemInfo());
        document.getElementById('help-toggle').addEventListener('click', () => this.toggleHelp());
        document.getElementById('clear-terminal').addEventListener('click', () => this.clearTerminal());
        
        // Sidebar controls
        document.getElementById('close-history').addEventListener('click', () => this.toggleHistory());
        document.getElementById('close-system-info').addEventListener('click', () => this.toggleSystemInfo());
        document.getElementById('close-shortcuts').addEventListener('click', () => this.toggleHelp());
        document.getElementById('clear-history').addEventListener('click', () => this.clearHistory());
        document.getElementById('refresh-system-info').addEventListener('click', () => this.refreshSystemInfo());
        
        // Context menu
        terminalOutput.addEventListener('contextmenu', (e) => this.showContextMenu(e));
        document.addEventListener('click', () => this.hideContextMenu());
        
        // Window focus handler
        window.addEventListener('focus', () => this.focusInput());
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+L - Clear terminal
            if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                this.clearTerminal();
            }
            
            // Ctrl+H - Toggle history
            if (e.ctrlKey && e.key === 'h') {
                e.preventDefault();
                this.toggleHistory();
            }
            
            // Ctrl+I - Toggle system info
            if (e.ctrlKey && e.key === 'i') {
                e.preventDefault();
                this.toggleSystemInfo();
            }
            
            // Ctrl+? - Toggle help
            if (e.ctrlKey && e.key === '?') {
                e.preventDefault();
                this.toggleHelp();
            }
            
            // Escape - Close all panels
            if (e.key === 'Escape') {
                this.closeAllPanels();
            }
        });
    }
    
    handleKeyDown(e) {
        const input = e.target;
        
        switch (e.key) {
            case 'Enter':
                e.preventDefault();
                this.executeCommand();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.navigateHistory(-1);
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                this.navigateHistory(1);
                break;
                
            case 'Tab':
                e.preventDefault();
                this.showSuggestions();
                break;
        }
    }
    
    handleInput(e) {
        const input = e.target.value;
        
        // Hide suggestions if input is empty
        if (!input.trim()) {
            this.hideSuggestions();
        }
        
        // Reset history navigation
        this.historyIndex = -1;
    }
    
    executeCommand() {
        const commandInput = document.getElementById('command-input');
        const command = commandInput.value.trim();
        
        if (!command) return;
        
        if (!this.isConnected) {
            this.showNotification('Not connected to server', 'error');
            return;
        }
        
        // Add command to output
        this.addCommandToOutput(command);
        
        // Add to history
        this.addToHistory(command);
        
        // Clear input
        commandInput.value = '';
        this.historyIndex = -1;
        
        // Hide suggestions
        this.hideSuggestions();
        
        // Show loading
        this.showLoading();
        
        // Send command to server
        this.socket.emit('command', {
            command: command,
            session_id: this.currentSessionId,
            user_id: this.currentUserId,
            timestamp: new Date().toISOString()
        });
    }
    
    handleServerResponse(data) {
        switch (data.type) {
            case 'command_result':
                this.handleCommandResult(data);
                break;
                
            case 'ai_interpretation':
                this.addAIInterpretation(data.message);
                break;
                
            case 'system_info':
                this.updateSystemInfo(data.data);
                break;
                
            case 'command_history':
                this.updateCommandHistory(data.data);
                break;
                
            case 'error':
                this.addErrorToOutput(data.message);
                break;
                
            case 'system':
                this.addSystemMessage(data.message);
                break;
                
            default:
                console.log('Unknown response type:', data.type);
        }
    }
    
    handleCommandResult(data) {
        if (data.success) {
            if (data.output) {
                this.addSuccessOutput(data.output);
            }
        } else {
            this.addErrorToOutput(data.error || 'Command failed');
        }
    }
    
    addCommandToOutput(command) {
        const terminalOutput = document.getElementById('terminal-output');
        const commandLine = document.createElement('div');
        commandLine.className = 'terminal-line command-line';
        
        commandLine.innerHTML = `
            <div class="terminal-content">
                <span class="prompt-user">${this.currentUserId}</span>
                <span class="prompt-separator">@</span>
                <span class="prompt-host">web-terminal</span>
                <span class="prompt-separator">:</span>
                <span class="prompt-path">~</span>
                <span class="prompt-symbol">$</span>
                <span class="command-text">${this.escapeHtml(command)}</span>
            </div>
        `;
        
        terminalOutput.appendChild(commandLine);
        this.scrollToBottom();
    }
    
    addSuccessOutput(output) {
        if (!output) return;
        
        const terminalOutput = document.getElementById('terminal-output');
        const outputLine = document.createElement('div');
        outputLine.className = 'terminal-line success-output';
        
        outputLine.innerHTML = `
            <div class="terminal-content">
                <pre>${this.escapeHtml(output)}</pre>
            </div>
        `;
        
        terminalOutput.appendChild(outputLine);
        this.scrollToBottom();
    }
    
    addErrorToOutput(error) {
        const terminalOutput = document.getElementById('terminal-output');
        const errorLine = document.createElement('div');
        errorLine.className = 'terminal-line error-output';
        
        errorLine.innerHTML = `
            <div class="terminal-content">
                <pre>Error: ${this.escapeHtml(error)}</pre>
            </div>
        `;
        
        terminalOutput.appendChild(errorLine);
        this.scrollToBottom();
    }
    
    addAIInterpretation(message) {
        const terminalOutput = document.getElementById('terminal-output');
        const aiLine = document.createElement('div');
        aiLine.className = 'terminal-line ai-interpretation';
        
        aiLine.innerHTML = `
            <div class="terminal-content">
                <pre>🤖 ${this.escapeHtml(message)}</pre>
            </div>
        `;
        
        terminalOutput.appendChild(aiLine);
        this.scrollToBottom();
    }
    
    addSystemMessage(message) {
        const terminalOutput = document.getElementById('terminal-output');
        const systemLine = document.createElement('div');
        systemLine.className = 'terminal-line system-output';
        
        systemLine.innerHTML = `
            <div class="terminal-content">
                <pre>ℹ️ ${this.escapeHtml(message)}</pre>
            </div>
        `;
        
        terminalOutput.appendChild(systemLine);
        this.scrollToBottom();
    }
    
    scrollToBottom() {
        const terminalOutput = document.getElementById('terminal-output');
        terminalOutput.scrollTop = terminalOutput.scrollHeight;
    }
    
    addToHistory(command) {
        // Avoid duplicate consecutive commands
        if (this.commandHistory.length === 0 || this.commandHistory[this.commandHistory.length - 1] !== command) {
            this.commandHistory.push(command);
            
            // Limit history size
            if (this.commandHistory.length > 100) {
                this.commandHistory.shift();
            }
            
            // Save to localStorage
            this.saveCommandHistory();
        }
    }
    
    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return;
        
        const commandInput = document.getElementById('command-input');
        
        if (direction === -1) { // Up arrow
            if (this.historyIndex === -1) {
                this.historyIndex = this.commandHistory.length - 1;
            } else if (this.historyIndex > 0) {
                this.historyIndex--;
            }
        } else if (direction === 1) { // Down arrow
            if (this.historyIndex === -1) return;
            
            if (this.historyIndex < this.commandHistory.length - 1) {
                this.historyIndex++;
            } else {
                this.historyIndex = -1;
                commandInput.value = '';
                return;
            }
        }
        
        if (this.historyIndex >= 0 && this.historyIndex < this.commandHistory.length) {
            commandInput.value = this.commandHistory[this.historyIndex];
        }
    }
    
    saveCommandHistory() {
        try {
            localStorage.setItem('web-terminal-history', JSON.stringify(this.commandHistory));
        } catch (e) {
            console.warn('Failed to save command history:', e);
        }
    }
    
    loadCommandHistory() {
        try {
            const saved = localStorage.getItem('web-terminal-history');
            if (saved) {
                this.commandHistory = JSON.parse(saved);
            }
        } catch (e) {
            console.warn('Failed to load command history:', e);
            this.commandHistory = [];
        }
    }
    
    clearHistory() {
        this.commandHistory = [];
        this.historyIndex = -1;
        this.saveCommandHistory();
        this.updateHistoryDisplay();
        this.showNotification('Command history cleared', 'info');
    }
    
    toggleHistory() {
        const sidebar = document.getElementById('history-sidebar');
        sidebar.classList.toggle('show');
        
        if (sidebar.classList.contains('show')) {
            this.updateHistoryDisplay();
        }
    }
    
    toggleSystemInfo() {
        const panel = document.getElementById('system-info-panel');
        panel.classList.toggle('show');
        
        if (panel.classList.contains('show')) {
            this.requestSystemInfo();
        }
    }
    
    toggleHelp() {
        const help = document.getElementById('shortcuts-help');
        help.classList.toggle('hidden');
    }
    
    closeAllPanels() {
        document.getElementById('history-sidebar').classList.remove('show');
        document.getElementById('system-info-panel').classList.remove('show');
        document.getElementById('shortcuts-help').classList.add('hidden');
        this.hideSuggestions();
        this.hideContextMenu();
    }
    
    clearTerminal() {
        const terminalOutput = document.getElementById('terminal-output');
        terminalOutput.innerHTML = `
            <div class="terminal-line welcome-message">
                <div class="terminal-content">
                    <pre>Terminal cleared - Welcome back!
Type 'help' for available commands or use natural language.
---------------------------------------------------</pre>
                </div>
            </div>
        `;
        this.focusInput();
    }
    
    updateHistoryDisplay() {
        const historyList = document.getElementById('history-list');
        historyList.innerHTML = '';
        
        if (this.commandHistory.length === 0) {
            historyList.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No command history</div>';
            return;
        }
        
        // Show recent commands first
        const recentHistory = this.commandHistory.slice(-20).reverse();
        
        recentHistory.forEach((command, index) => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            historyItem.innerHTML = `
                <div class="history-command">${this.escapeHtml(command)}</div>
                <div class="history-time">${new Date().toLocaleTimeString()}</div>
            `;
            
            historyItem.addEventListener('click', () => {
                document.getElementById('command-input').value = command;
                this.toggleHistory();
                this.focusInput();
            });
            
            historyList.appendChild(historyItem);
        });
    }
    
    requestSystemInfo() {
        if (this.isConnected) {
            this.socket.emit('get_system_info');
        } else {
            this.showNotification('Not connected to server', 'error');
        }
    }
    
    refreshSystemInfo() {
        this.requestSystemInfo();
        this.showNotification('System information refreshed', 'info');
    }
    
    updateSystemInfo(data) {
        const content = document.getElementById('system-info-content');
        
        if (data.error) {
            content.innerHTML = `<div class="error-output">Error: ${this.escapeHtml(data.error)}</div>`;
            return;
        }
        
        let html = '';
        
        // CPU Information
        if (data.cpu) {
            const cpuUsage = data.cpu.usage_percent || 0;
            html += this.createMetricHTML('CPU Usage', `${cpuUsage.toFixed(1)}%`, cpuUsage);
            html += this.createMetricHTML('CPU Cores', `${data.cpu.count_logical} logical, ${data.cpu.count_physical} physical`);
        }
        
        // Memory Information
        if (data.memory && data.memory.virtual) {
            const memUsage = data.memory.virtual.percent || 0;
            html += this.createMetricHTML('Memory Usage', `${memUsage.toFixed(1)}%`, memUsage);
            html += this.createMetricHTML('Memory', `${data.memory.virtual.used_gb}GB / ${data.memory.virtual.total_gb}GB`);
        }
        
        // Disk Information
        if (data.disk && data.disk.partitions && data.disk.partitions.length > 0) {
            const mainPartition = data.disk.partitions[0];
            html += this.createMetricHTML('Disk Usage', `${mainPartition.percent.toFixed(1)}%`, mainPartition.percent);
            html += this.createMetricHTML('Disk Space', `${mainPartition.used_gb}GB / ${mainPartition.total_gb}GB`);
        }
        
        // Process Information
        if (data.processes) {
            html += this.createMetricHTML('Active Processes', data.processes.total_count.toString());
        }
        
        // Uptime
        if (data.uptime) {
            html += this.createMetricHTML('System Uptime', data.uptime.uptime_formatted);
        }
        
        content.innerHTML = html;
    }
    
    createMetricHTML(label, value, percentage = null) {
        let barHTML = '';
        if (percentage !== null) {
            const fillClass = percentage > 80 ? 'danger' : percentage > 60 ? 'warning' : '';
            barHTML = `
                <div class="metric-bar">
                    <div class="metric-fill ${fillClass}" style="width: ${percentage}%"></div>
                </div>
            `;
        }
        
        return `
            <div class="system-metric">
                <div class="metric-label">${this.escapeHtml(label)}</div>
                <div class="metric-value">${this.escapeHtml(value)}</div>
                ${barHTML}
            </div>
        `;
    }
    
    showSuggestions() {
        const input = document.getElementById('command-input').value.trim();
        if (!input) return;
        
        // Simple command suggestions
        const suggestions = [
            { command: 'ls', description: 'List directory contents' },
            { command: 'pwd', description: 'Print working directory' },
            { command: 'cd', description: 'Change directory' },
            { command: 'mkdir', description: 'Create directory' },
            { command: 'cat', description: 'Display file contents' },
            { command: 'echo', description: 'Display text' },
            { command: 'system', description: 'Show system information' },
            { command: 'help', description: 'Show available commands' },
            { command: 'clear', description: 'Clear terminal screen' },
            { command: 'history', description: 'Show command history' }
        ];
        
        const filtered = suggestions.filter(s => 
            s.command.toLowerCase().includes(input.toLowerCase()) ||
            s.description.toLowerCase().includes(input.toLowerCase())
        );
        
        if (filtered.length > 0) {
            this.showSuggestionsPanel(filtered.slice(0, 5));
        } else {
            this.hideSuggestions();
        }
    }
    
    showSuggestionsPanel(suggestions) {
        const panel = document.getElementById('suggestions-panel');
        const list = document.getElementById('suggestions-list');
        
        list.innerHTML = '';
        
        suggestions.forEach(suggestion => {
            const item = document.createElement('div');
            item.className = 'suggestion-item';
            item.innerHTML = `
                <div class="suggestion-command">${this.escapeHtml(suggestion.command)}</div>
                <div class="suggestion-description">${this.escapeHtml(suggestion.description)}</div>
            `;
            
            item.addEventListener('click', () => {
                document.getElementById('command-input').value = suggestion.command;
                this.hideSuggestions();
                this.focusInput();
            });
            
            list.appendChild(item);
        });
        
        panel.classList.remove('hidden');
    }
    
    hideSuggestions() {
        document.getElementById('suggestions-panel').classList.add('hidden');
    }
    
    showContextMenu(e) {
        e.preventDefault();
        const menu = document.getElementById('context-menu');
        
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        menu.classList.remove('hidden');
    }
    
    hideContextMenu() {
        document.getElementById('context-menu').classList.add('hidden');
    }
    
    updateConnectionStatus(text, status) {
        const statusElement = document.getElementById('status-text');
        const indicatorElement = document.getElementById('connection-status');
        
        statusElement.textContent = text;
        
        indicatorElement.className = 'status-indicator';
        if (status) {
            indicatorElement.classList.add(status);
        }
    }
    
    showLoading() {
        document.getElementById('loading-indicator').classList.remove('hidden');
    }
    
    hideLoading() {
        document.getElementById('loading-indicator').classList.add('hidden');
    }
    
    showNotification(message, type = 'info') {
        const container = document.getElementById('notification-container');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }
    
    focusInput() {
        setTimeout(() => {
            const input = document.getElementById('command-input');
            if (input && !input.disabled) {
                input.focus();
            }
        }, 100);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the terminal when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.terminal = new WebTerminal();
});

// Service Worker registration for offline functionality (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}