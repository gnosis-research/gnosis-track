// Initialize Lucide icons
lucide.createIcons();

class LogViewer {
    constructor() {
        this.isStreaming = false;
        this.streamingInterval = null;
        this.seenLogFiles = new Set();
        this.allLogs = [];
        this.filteredLogs = [];
        this.stats = { total: 0, error: 0, warning: 0, info: 0 };
        this.config = this.loadConfig();
        this.lastLogTimestamp = null;
        this.apiBaseUrl = this.config.useLocalServer ? `http://localhost:${window.location.port}/api` : '/api';
        this.isFullscreen = false;
        
        this.initializeElements();
        this.bindEvents();
        this.checkServerHealth();
        this.loadValidators();
    }
    
    initializeElements() {
        this.elements = {
            validatorSelect: document.getElementById('validator-select'),
            runSelect: document.getElementById('run-select'),
            levelFilter: document.getElementById('level-filter'),
            searchInput: document.getElementById('search-input'),
            startBtn: document.getElementById('start-streaming'),
            stopBtn: document.getElementById('stop-streaming'),
            clearBtn: document.getElementById('clear-logs'),
            autoScroll: document.getElementById('auto-scroll'),
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),
            logsContent: document.getElementById('logs-content'),
            logsContainer: document.getElementById('logs-container'),
            logsMainContainer: document.getElementById('logs-main-container'),
            fullscreenBtn: document.getElementById('fullscreen-btn'),
            fullscreenIcon: document.getElementById('fullscreen-icon'),
            downloadBtn: document.getElementById('download-btn'),
            downloadMenu: document.getElementById('download-menu'),
            downloadTxt: document.getElementById('download-txt'),
            downloadJson: document.getElementById('download-json'),
            downloadCsv: document.getElementById('download-csv'),
            downloadFiltered: document.getElementById('download-filtered'),
            downloadTimestamps: document.getElementById('download-timestamps'),
            totalLogs: document.getElementById('total-logs'),
            errorCount: document.getElementById('error-count'),
            warningCount: document.getElementById('warning-count'),
            infoCount: document.getElementById('info-count'),
            lastUpdate: document.getElementById('last-update'),
            settingsBtn: document.getElementById('settings-btn'),
            configModal: document.getElementById('config-modal'),
            minioEndpoint: document.getElementById('minio-endpoint'),
            minioAccessKey: document.getElementById('minio-access-key'),
            minioSecretKey: document.getElementById('minio-secret-key'),
            minioBucket: document.getElementById('minio-bucket'),
            saveConfig: document.getElementById('save-config'),
            cancelConfig: document.getElementById('cancel-config')
        };
    }
    
    bindEvents() {
        this.elements.validatorSelect.addEventListener('change', () => this.loadRuns());
        this.elements.startBtn.addEventListener('click', () => this.startStreaming());
        this.elements.stopBtn.addEventListener('click', () => this.stopStreaming());
        this.elements.clearBtn.addEventListener('click', () => this.clearLogs());
        this.elements.levelFilter.addEventListener('change', () => this.filterLogs());
        this.elements.searchInput.addEventListener('input', () => this.filterLogs());
        this.elements.settingsBtn.addEventListener('click', () => this.showConfigModal());
        this.elements.saveConfig.addEventListener('click', () => this.saveConfiguration());
        this.elements.cancelConfig.addEventListener('click', () => this.hideConfigModal());
        this.elements.fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        this.elements.downloadBtn.addEventListener('click', () => this.toggleDownloadMenu());
        this.elements.downloadTxt.addEventListener('click', () => this.downloadLogs('txt'));
        this.elements.downloadJson.addEventListener('click', () => this.downloadLogs('json'));
        this.elements.downloadCsv.addEventListener('click', () => this.downloadLogs('csv'));
        
        // Close modal and dropdown on outside click
        this.elements.configModal.addEventListener('click', (e) => {
            if (e.target === this.elements.configModal) {
                this.hideConfigModal();
            }
        });
        
        // Close download menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.elements.downloadBtn.contains(e.target) && !this.elements.downloadMenu.contains(e.target)) {
                this.elements.downloadMenu.classList.add('hidden');
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Don't trigger shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' && e.key !== 'Escape') {
                return;
            }
            
            if (e.key === 'Escape') {
                if (this.isFullscreen) {
                    this.toggleFullscreen();
                } else {
                    this.hideConfigModal();
                    this.elements.downloadMenu.classList.add('hidden');
                }
            } else if (e.ctrlKey && e.key === 'k') {
                e.preventDefault();
                this.elements.searchInput.focus();
                this.elements.searchInput.select();
            } else if (e.ctrlKey && e.key === 'l') {
                e.preventDefault();
                this.clearLogs();
            } else if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            } else if (e.ctrlKey && e.key === 'd') {
                e.preventDefault();
                this.toggleDownloadMenu();
            } else if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                if (this.isStreaming) {
                    this.stopStreaming();
                } else {
                    this.startStreaming();
                }
            } else if (e.ctrlKey && e.key === ',') {
                e.preventDefault();
                this.showConfigModal();
            } else if (e.key === 'a' && !e.ctrlKey) {
                e.preventDefault();
                this.elements.autoScroll.checked = !this.elements.autoScroll.checked;
                this.showAlert(`Auto-scroll ${this.elements.autoScroll.checked ? 'enabled' : 'disabled'}`, 'info');
            } else if (e.key === '/' && !e.ctrlKey) {
                e.preventDefault();
                this.elements.searchInput.focus();
                this.elements.searchInput.select();
            }
        });
    }
    
    loadConfig() {
        const defaultConfig = {
            endpoint: '146.190.168.187:9000',
            accessKey: 'miner_test_hot',
            secretKey: 'key_key_offline_secret2',
            bucket: 'validator-logs',
            useLocalServer: true
        };
        
        try {
            const saved = localStorage.getItem('minio-config');
            return saved ? { ...defaultConfig, ...JSON.parse(saved) } : defaultConfig;
        } catch {
            return defaultConfig;
        }
    }
    
    saveConfig() {
        try {
            localStorage.setItem('minio-config', JSON.stringify(this.config));
        } catch (error) {
            console.error('Failed to save config:', error);
        }
    }
    
    showConfigModal() {
        this.elements.minioEndpoint.value = this.config.endpoint;
        this.elements.minioAccessKey.value = this.config.accessKey;
        this.elements.minioSecretKey.value = this.config.secretKey;
        this.elements.minioBucket.value = this.config.bucket;
        this.elements.configModal.classList.remove('hidden');
        this.elements.configModal.classList.add('flex');
    }
    
    hideConfigModal() {
        this.elements.configModal.classList.add('hidden');
        this.elements.configModal.classList.remove('flex');
    }
    
    saveConfiguration() {
        this.config = {
            endpoint: this.elements.minioEndpoint.value,
            accessKey: this.elements.minioAccessKey.value,
            secretKey: this.elements.minioSecretKey.value,
            bucket: this.elements.minioBucket.value,
            useLocalServer: this.config.useLocalServer
        };
        
        this.saveConfig();
        this.hideConfigModal();
        
        // Reload validators with new config
        this.loadValidators();
    }
    
    toggleFullscreen() {
        this.isFullscreen = !this.isFullscreen;
        
        if (this.isFullscreen) {
            // Enter fullscreen mode
            this.elements.logsMainContainer.classList.add('fullscreen-mode');
            this.elements.logsContainer.classList.add('logs-container-fullscreen');
            this.elements.fullscreenIcon.setAttribute('data-lucide', 'minimize');
            this.elements.fullscreenBtn.title = 'Exit Fullscreen';
            
            // Hide page content except logs
            document.body.style.overflow = 'hidden';
            
        } else {
            // Exit fullscreen mode
            this.elements.logsMainContainer.classList.remove('fullscreen-mode');
            this.elements.logsContainer.classList.remove('logs-container-fullscreen');
            this.elements.fullscreenIcon.setAttribute('data-lucide', 'maximize');
            this.elements.fullscreenBtn.title = 'Toggle Fullscreen';
            
            // Restore page content
            document.body.style.overflow = '';
        }
        
        // Reinitialize Lucide icons to update the icon
        lucide.createIcons();
        
        // Auto-scroll to bottom if enabled and we have content
        if (this.elements.autoScroll.checked) {
            setTimeout(() => {
                this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
            }, 100);
        }
    }
    
    toggleDownloadMenu() {
        this.elements.downloadMenu.classList.toggle('hidden');
    }
    
    downloadLogs(format) {
        // Hide the download menu
        this.elements.downloadMenu.classList.add('hidden');
        
        // Determine which logs to export
        const useFiltered = this.elements.downloadFiltered.checked;
        const includeTimestamps = this.elements.downloadTimestamps.checked;
        const logsToExport = useFiltered ? this.filteredLogs : this.allLogs;
        
        if (logsToExport.length === 0) {
            this.showAlert('No logs to export', 'warning');
            return;
        }
        
        // Generate filename
        const validatorUid = this.elements.validatorSelect.value || 'unknown';
        const runId = this.elements.runSelect.value || 'latest';
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `validator-${validatorUid}-${runId}-${timestamp}.${format}`;
        
        let content = '';
        let mimeType = '';
        
        try {
            switch (format) {
                case 'txt':
                    content = this.generateTextExport(logsToExport, includeTimestamps);
                    mimeType = 'text/plain';
                    break;
                case 'json':
                    content = this.generateJsonExport(logsToExport, includeTimestamps);
                    mimeType = 'application/json';
                    break;
                case 'csv':
                    content = this.generateCsvExport(logsToExport, includeTimestamps);
                    mimeType = 'text/csv';
                    break;
                default:
                    throw new Error('Unsupported format');
            }
            
            // Create and download file
            this.downloadFile(content, filename, mimeType);
            this.showAlert(`Downloaded ${logsToExport.length} logs as ${format.toUpperCase()}`, 'success');
            
        } catch (error) {
            console.error('Export failed:', error);
            this.showAlert('Export failed. Please try again.', 'error');
        }
    }
    
    generateTextExport(logs, includeTimestamps) {
        const lines = [];
        
        // Add header
        lines.push('# Validator Logs Export');
        lines.push(`# Generated: ${new Date().toISOString()}`);
        lines.push(`# Total logs: ${logs.length}`);
        lines.push(`# Validator: ${this.elements.validatorSelect.value || 'unknown'}`);
        lines.push(`# Run: ${this.elements.runSelect.value || 'latest'}`);
        lines.push('');
        
        // Add logs
        logs.forEach(log => {
            let line = '';
            if (includeTimestamps) {
                const timestamp = new Date(log.timestamp).toLocaleString();
                line += `[${timestamp}] `;
            }
            line += `${log.level.padEnd(8)} | ${log.message}`;
            lines.push(line);
        });
        
        return lines.join('\n');
    }
    
    generateJsonExport(logs, includeTimestamps) {
        const exportData = {
            meta: {
                exported_at: new Date().toISOString(),
                validator_uid: this.elements.validatorSelect.value || 'unknown',
                run_id: this.elements.runSelect.value || 'latest',
                total_logs: logs.length,
                include_timestamps: includeTimestamps
            },
            logs: logs.map(log => {
                const exportLog = {
                    level: log.level,
                    message: log.message
                };
                
                if (includeTimestamps) {
                    exportLog.timestamp = log.timestamp;
                }
                
                return exportLog;
            })
        };
        
        return JSON.stringify(exportData, null, 2);
    }
    
    generateCsvExport(logs, includeTimestamps) {
        const lines = [];
        
        // CSV header
        const headers = ['Level', 'Message'];
        if (includeTimestamps) {
            headers.unshift('Timestamp');
        }
        lines.push(headers.map(h => `"${h}"`).join(','));
        
        // CSV data
        logs.forEach(log => {
            const row = [
                `"${log.level}"`,
                `"${log.message.replace(/"/g, '""')}"`  // Escape quotes
            ];
            
            if (includeTimestamps) {
                const timestamp = new Date(log.timestamp).toLocaleString();
                row.unshift(`"${timestamp}"`);
            }
            
            lines.push(row.join(','));
        });
        
        return lines.join('\n');
    }
    
    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Clean up the URL object
        setTimeout(() => URL.revokeObjectURL(url), 100);
    }
    
    async makeApiRequest(endpoint) {
        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            throw error;
        }
    }
    
    async checkServerHealth() {
        try {
            const health = await this.makeApiRequest('/health');
            if (health.minio_connected) {
                this.updateStatus('Server Ready', 'green');
            } else {
                this.updateStatus('Server Connected, MinIO Unavailable', 'yellow');
            }
        } catch (error) {
            this.updateStatus('Server Unavailable', 'red');
            console.error('Health check failed:', error);
        }
    }
    
    async loadValidators() {
        try {
            this.updateStatus('Loading validators...', 'yellow');
            const data = await this.makeApiRequest('/validators');
            
            this.elements.validatorSelect.innerHTML = '<option value="">Select Validator</option>';
            
            // Handle both array response and object with validators property
            const validators = Array.isArray(data) ? data : data.validators || [];
            
            if (validators.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No validators found';
                this.elements.validatorSelect.appendChild(option);
            } else {
                validators.forEach(uid => {
                    const option = document.createElement('option');
                    option.value = uid;
                    option.textContent = `Validator ${uid}`;
                    this.elements.validatorSelect.appendChild(option);
                });
            }
            
            this.updateStatus('Ready', 'green');
        } catch (error) {
            console.error('Failed to load validators:', error);
            this.updateStatus('Error loading validators', 'red');
            this.showAlert('Failed to load validators. Check server connection.', 'error');
        }
    }
    
    async loadRuns() {
        const validatorUid = this.elements.validatorSelect.value;
        if (!validatorUid) return;
        
        try {
            const data = await this.makeApiRequest(`/validators/${validatorUid}/runs`);
            
            this.elements.runSelect.innerHTML = '<option value="">Latest Run</option>';
            
            // Handle both array response and object with runs property
            const runs = Array.isArray(data) ? data : data.runs || [];
            
            if (runs.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No runs found';
                this.elements.runSelect.appendChild(option);
            } else {
                runs.forEach(run => {
                    const option = document.createElement('option');
                    option.value = run;
                    option.textContent = run;
                    this.elements.runSelect.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Failed to load runs:', error);
            this.showAlert('Failed to load runs for this validator', 'error');
        }
    }
    
    startStreaming() {
        const validatorUid = this.elements.validatorSelect.value;
        if (!validatorUid) {
            this.showAlert('Please select a validator first', 'warning');
            return;
        }
        
        this.isStreaming = true;
        this.elements.startBtn.disabled = true;
        this.elements.stopBtn.disabled = false;
        this.updateStatus('Streaming...', 'green');
        
        // Reset last timestamp for fresh start
        this.lastLogTimestamp = null;
        
        // Load config first
        this.loadValidatorConfig();
        
        // Start polling for new logs
        this.streamingInterval = setInterval(() => {
            this.fetchLogs();
        }, 2000);
        
        // Fetch initial logs
        this.fetchLogs();
    }
    
    stopStreaming() {
        this.isStreaming = false;
        this.elements.startBtn.disabled = false;
        this.elements.stopBtn.disabled = true;
        this.updateStatus('Stopped', 'yellow');
        
        if (this.streamingInterval) {
            clearInterval(this.streamingInterval);
            this.streamingInterval = null;
        }
    }
    
    async loadValidatorConfig() {
        try {
            const validatorUid = this.elements.validatorSelect.value;
            const runId = this.elements.runSelect.value;
            
            // Use the config endpoint with proper parameters
            let configEndpoint;
            if (!runId) {
                configEndpoint = `/validators/${validatorUid}/config`;
            } else {
                configEndpoint = `/validators/${validatorUid}/config?run_id=${runId}`;
            }
            
            const config = await this.makeApiRequest(configEndpoint);
            
            if (config && config.run_info) {
                this.showValidatorInfo(config.run_info);
            }
        } catch (error) {
            console.error('Failed to load validator config:', error);
        }
    }
    
    showValidatorInfo(runInfo) {
        const infoHtml = `
            <div class="bg-slate-800/50 rounded-lg p-4 mb-4">
                <h3 class="text-lg font-semibold mb-2 flex items-center">
                    <i data-lucide="info" class="w-5 h-5 mr-2 text-blue-400"></i>
                    Validator Information
                </h3>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                    <div>
                        <span class="text-slate-400">UID:</span>
                        <span class="ml-2 font-medium">${runInfo.uid}</span>
                    </div>
                    <div>
                        <span class="text-slate-400">Version:</span>
                        <span class="ml-2 font-medium">${runInfo.version}</span>
                    </div>
                    <div>
                        <span class="text-slate-400">Started:</span>
                        <span class="ml-2 font-medium">${new Date(runInfo.started_at).toLocaleString()}</span>
                    </div>
                    <div class="col-span-2 md:col-span-3">
                        <span class="text-slate-400">Hotkey:</span>
                        <span class="ml-2 font-mono text-xs">${runInfo.hotkey.substring(0, 20)}...</span>
                    </div>
                    <div class="col-span-2 md:col-span-3">
                        <span class="text-slate-400">Scrapers:</span>
                        <span class="ml-2">${runInfo.scrapers.join(', ')}</span>
                    </div>
                </div>
            </div>
        `;
        
        this.elements.logsContent.insertAdjacentHTML('afterbegin', infoHtml);
        lucide.createIcons();
    }
    
    async fetchLogs() {
        if (!this.isStreaming) return;
        
        try {
            const validatorUid = this.elements.validatorSelect.value;
            const runId = this.elements.runSelect.value;
            
            // Build query parameters
            let queryParams = '?limit=100';
            if (this.lastLogTimestamp) {
                queryParams += `&since=${encodeURIComponent(this.lastLogTimestamp)}`;
            }
            
            // Choose endpoint based on whether specific run is selected
            let logData;
            if (!runId) {
                // Use latest endpoint for latest run
                logData = await this.makeApiRequest(`/validators/${validatorUid}/latest${queryParams}`);
            } else {
                // Use specific run endpoint
                logData = await this.makeApiRequest(`/validators/${validatorUid}/logs?run_id=${runId}&limit=100`);
            }
            
            if (logData && logData.logs && logData.logs.length > 0) {
                let newLogsAdded = false;
                
                logData.logs.forEach(log => {
                    const logId = `${log.timestamp}-${log.message}`;
                    if (!this.seenLogFiles.has(logId)) {
                        this.seenLogFiles.add(logId);
                        this.allLogs.push({ ...log, id: logId });
                        this.updateStats(log);
                        newLogsAdded = true;
                        
                        // Update last timestamp
                        if (!this.lastLogTimestamp || log.timestamp > this.lastLogTimestamp) {
                            this.lastLogTimestamp = log.timestamp;
                        }
                    }
                });
                
                if (newLogsAdded) {
                    this.filterLogs();
                    this.elements.lastUpdate.textContent = new Date().toLocaleTimeString();
                }
            }
            
            this.updateStatus('Connected', 'green');
            
        } catch (error) {
            console.error('Failed to fetch logs:', error);
            this.updateStatus('Connection Error', 'red');
        }
    }
    
    updateStats(log) {
        this.stats.total++;
        if (log.level === 'ERROR') this.stats.error++;
        else if (log.level === 'WARNING') this.stats.warning++;
        else if (log.level === 'INFO') this.stats.info++;
        
        this.elements.totalLogs.textContent = this.stats.total.toLocaleString();
        this.elements.errorCount.textContent = this.stats.error.toLocaleString();
        this.elements.warningCount.textContent = this.stats.warning.toLocaleString();
        this.elements.infoCount.textContent = this.stats.info.toLocaleString();
    }
    
    filterLogs() {
        const levelFilter = this.elements.levelFilter.value;
        const searchTerm = this.elements.searchInput.value.toLowerCase();
        
        this.filteredLogs = this.allLogs.filter(log => {
            const levelMatch = !levelFilter || log.level === levelFilter;
            const searchMatch = !searchTerm || 
                log.message.toLowerCase().includes(searchTerm) ||
                log.level.toLowerCase().includes(searchTerm);
            return levelMatch && searchMatch;
        });
        
        this.renderLogs();
    }
    
    renderLogs() {
        const logsToShow = this.filteredLogs.slice(-200); // Show last 200 logs for performance
        
        if (logsToShow.length === 0 && this.allLogs.length === 0) {
            this.elements.logsContent.innerHTML = `
                <div class="text-center text-slate-400 py-8">
                    <i data-lucide="server" class="w-12 h-12 mx-auto mb-3 opacity-50"></i>
                    <p>Select a validator and start streaming to view logs</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        if (logsToShow.length === 0) {
            this.elements.logsContent.innerHTML = `
                <div class="text-center text-slate-400 py-8">
                    <i data-lucide="filter" class="w-12 h-12 mx-auto mb-3 opacity-50"></i>
                    <p>No logs match your filters</p>
                    <p class="text-sm mt-2">Try adjusting your search terms or log level filter</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        const logsHtml = logsToShow.map(log => this.renderLogEntry(log)).join('');
        this.elements.logsContent.innerHTML = logsHtml;
        
        // Auto-scroll to bottom if enabled
        if (this.elements.autoScroll.checked) {
            this.elements.logsContainer.scrollTop = this.elements.logsContainer.scrollHeight;
        }
        
        lucide.createIcons();
    }
    
    renderLogEntry(log) {
        const timestamp = new Date(log.timestamp).toLocaleString();
        const levelColors = {
            ERROR: 'text-red-400',
            WARNING: 'text-yellow-400',
            INFO: 'text-green-400',
            DEBUG: 'text-blue-400',
            TRACE: 'text-purple-400',
            SUCCESS: 'text-emerald-400'
        };
        
        const levelIcons = {
            ERROR: 'alert-circle',
            WARNING: 'alert-triangle',
            INFO: 'info',
            DEBUG: 'bug',
            TRACE: 'search',
            SUCCESS: 'check-circle'
        };
        
        return `
            <div class="log-entry level-${log.level} p-3 rounded-lg mb-1 log-font text-sm hover:bg-slate-800/30 transition-colors">
                <div class="flex items-start space-x-3">
                    <div class="flex-shrink-0">
                        <i data-lucide="${levelIcons[log.level] || 'circle'}" class="w-4 h-4 ${levelColors[log.level] || 'text-gray-400'} mt-0.5"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-3 mb-1">
                            <span class="text-slate-400 text-xs">${timestamp}</span>
                            <span class="px-2 py-0.5 text-xs rounded font-medium ${levelColors[log.level] || 'text-gray-400'} bg-slate-800">
                                ${log.level}
                            </span>
                        </div>
                        <div class="text-white break-words">
                            ${this.highlightSearchTerms(this.escapeHtml(log.message))}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    highlightSearchTerms(text) {
        const searchTerm = this.elements.searchInput.value.trim();
        if (!searchTerm) return text;
        
        const regex = new RegExp(`(${this.escapeRegex(searchTerm)})`, 'gi');
        return text.replace(regex, '<mark class="bg-yellow-400 text-black px-1 rounded">$1</mark>');
    }
    
    escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }
    
    clearLogs() {
        this.allLogs = [];
        this.filteredLogs = [];
        this.seenLogFiles.clear();
        this.stats = { total: 0, error: 0, warning: 0, info: 0 };
        this.lastLogTimestamp = null;
        
        this.elements.totalLogs.textContent = '0';
        this.elements.errorCount.textContent = '0';
        this.elements.warningCount.textContent = '0';
        this.elements.infoCount.textContent = '0';
        this.elements.lastUpdate.textContent = 'Never';
        
        this.renderLogs();
    }
    
    updateStatus(status, color) {
        this.elements.statusText.textContent = status;
        this.elements.statusIndicator.className = `w-3 h-3 bg-${color}-500 rounded-full ${color === 'red' || color === 'yellow' ? 'animate-pulse' : ''}`;
    }
    
    showAlert(message, type = 'info') {
        const alertColors = {
            info: 'bg-blue-600',
            success: 'bg-green-600',
            warning: 'bg-yellow-600',
            error: 'bg-red-600'
        };
        
        const alert = document.createElement('div');
        alert.className = `fixed top-4 right-4 ${alertColors[type]} text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-pulse`;
        alert.textContent = message;
        
        document.body.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the log viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LogViewer();
});

// Add some helpful keyboard shortcuts info
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === '?') {
        e.preventDefault();
        const shortcuts = `
🔥 KEYBOARD SHORTCUTS 🔥

📋 BASIC CONTROLS:
• Ctrl + K    → Focus search box
• Ctrl + L    → Clear all logs  
• /           → Quick search (alternative)
• A           → Toggle auto-scroll
• Escape      → Exit fullscreen/close menus

🎬 STREAMING:
• Ctrl + S    → Start/Stop streaming
• F11         → Toggle fullscreen mode

📥 EXPORT & SETTINGS:
• Ctrl + D    → Open download menu
• Ctrl + ,    → Open settings/config

❓ HELP:
• Ctrl + ?    → Show this help

💡 TIP: Most shortcuts work anywhere in the app!
        `;
        alert(shortcuts);
    }
});