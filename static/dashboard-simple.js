// Simplified Dashboard JavaScript for GPT-DRAA
const API_BASE = 'http://localhost:8000';

// Dashboard Component
function dashboard() {
    return {
        loading: true,
        stats: {},
        recentQueries: [],
        performanceTrends: {},
        lastUpdated: '',

        async init() {
            console.log("Initializing dashboard...");
            await this.loadDashboardData();
            this.initializeCharts();
            this.loading = false;
        },

        async loadDashboardData() {
            try {
                console.log("Loading dashboard data...");
                
                // Load real system stats from API
                const statsResponse = await fetch(`${API_BASE}/api/api/monitoring/stats/`);
                if (statsResponse.ok) {
                    const data = await statsResponse.json();
                    this.stats = data.stats || {};
                    console.log('Dashboard stats loaded:', this.stats);
                } else {
                    console.warn('Could not load stats from API, using fallbacks');
                    this.stats = { 
                        total_queries: 0,
                        last_day: { avg_response_time: 0, avg_relevance: 0, count: 0 }
                    };
                }

                // Load recent queries
                const dashboardResponse = await fetch(`${API_BASE}/api/api/monitoring/dashboard/`);
                if (dashboardResponse.ok) {
                    const dashboardData = await dashboardResponse.json();
                    this.recentQueries = dashboardData.recent_queries || [];
                    console.log('Recent queries loaded:', this.recentQueries.length, 'queries');
                } else {
                    console.warn('Could not load dashboard data from API');
                    this.recentQueries = [];
                }

                // Load performance trends (including real chart data)
                const trendsResponse = await fetch(`${API_BASE}/api/api/monitoring/trends/`);
                if (trendsResponse.ok) {
                    this.performanceTrends = await trendsResponse.json();
                    console.log('Performance trends loaded:', this.performanceTrends);
                } else {
                    console.warn('Could not load trends from API');
                    this.performanceTrends = {};
                }

                this.lastUpdated = new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                this.stats = { total_queries: 0 };
                this.recentQueries = [];
                this.performanceTrends = {};
            }
        },

        initializeCharts() {
            // Simple chart initialization with real data
            try {
                const responseTimeCtx = document.getElementById('responseTimeChart');
                if (responseTimeCtx) {
                    // Use real response time trend data
                    const responseTrends = this.performanceTrends.response_time_trend || [];
                    const responseLabels = responseTrends.map(item => 
                        new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                    );
                    const responseData = responseTrends.map(item => item.avg_response_time * 1000); // Convert to ms
                    
                    // Fallback to sample data if no real data
                    const labels = responseLabels.length > 0 ? responseLabels : ['6 days ago', '5 days ago', '4 days ago', '3 days ago', '2 days ago', 'Yesterday', 'Today'];
                    const data = responseData.length > 0 ? responseData : [30000, 35000, 40000, 42000, 38000, 36000, this.stats.last_day?.avg_response_time || 0];

                    new Chart(responseTimeCtx, {
                        type: 'line',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Response Time (ms)',
                                data: data,
                                borderColor: 'rgb(59, 130, 246)',
                                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                                borderWidth: 2,
                                fill: true
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        callback: function(value) {
                                            return (value / 1000).toFixed(1) + 's';
                                        }
                                    }
                                }
                            }
                        }
                    });
                }

                const queryVolumeCtx = document.getElementById('queryVolumeChart');
                if (queryVolumeCtx) {
                    // Use real query volume trend data
                    const volumeTrends = this.performanceTrends.query_volume_trend || [];
                    const volumeLabels = volumeTrends.map(item => 
                        new Date(item.date).toLocaleDateString('en-US', { weekday: 'short' })
                    );
                    const volumeData = volumeTrends.map(item => item.count);
                    
                    // Fallback to sample data if no real data, but include current total
                    const labels = volumeLabels.length > 0 ? volumeLabels : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Today'];
                    const data = volumeData.length > 0 ? volumeData : [0, 0, 0, 0, 0, 0, this.stats.total_queries || 0];

                    new Chart(queryVolumeCtx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: 'Queries',
                                data: data,
                                backgroundColor: 'rgba(147, 51, 234, 0.7)',
                                borderColor: 'rgb(147, 51, 234)',
                                borderWidth: 1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    ticks: {
                                        stepSize: 1
                                    }
                                }
                            }
                        }
                    });
                }
            } catch (error) {
                console.error('Error initializing charts:', error);
            }
        },

        formatResponseTime(ms) {
            if (!ms) return '0ms';
            if (ms < 1000) return Math.round(ms) + 'ms';
            return (ms / 1000).toFixed(1) + 's';
        },

        formatTime(timestamp) {
            if (!timestamp) return '';
            return new Date(timestamp).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        },

        getSystemHealth() {
            const avgResponseTime = this.stats.last_day?.avg_response_time || 0;
            const avgRelevance = this.stats.last_day?.avg_relevance || 0;
            
            if (avgResponseTime < 5000 && avgRelevance > 0.05) return 'Excellent';
            if (avgResponseTime < 10000 && avgRelevance > 0.03) return 'Good';
            return 'Fair';
        }
    };
}

// Chat Interface Component
function chatInterface() {
    return {
        chatMessages: [],
        currentMessage: '',
        isSending: false,
        isTyping: false,

        init() {
            console.log('Chat interface initialized');
        },

        async sendMessage() {
            if (!this.currentMessage.trim() || this.isSending) return;

            const userMessage = {
                type: 'user',
                content: this.currentMessage.trim(),
                timestamp: new Date()
            };

            this.chatMessages.push(userMessage);
            const prompt = this.currentMessage.trim();
            this.currentMessage = '';
            this.isSending = true;
            this.isTyping = true;

            try {
                const response = await fetch(`${API_BASE}/api/ask/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: prompt,
                        language: 'en'
                    })
                });

                this.isTyping = false;

                if (response.ok) {
                    const data = await response.json();
                    const aiMessage = {
                        type: 'ai',
                        content: data.response,
                        timestamp: new Date(),
                        contextCount: data.context_used ? data.context_used.length : 0
                    };
                    this.chatMessages.push(aiMessage);
                } else {
                    const errorMessage = {
                        type: 'ai',
                        content: 'Sorry, I encountered an error while processing your question. Please try again.',
                        timestamp: new Date(),
                        contextCount: 0
                    };
                    this.chatMessages.push(errorMessage);
                }
            } catch (error) {
                console.error('Error sending message:', error);
                this.isTyping = false;
                const errorMessage = {
                    type: 'ai',
                    content: 'Sorry, I could not connect to the AI service. Please check your connection and try again.',
                    timestamp: new Date(),
                    contextCount: 0
                };
                this.chatMessages.push(errorMessage);
            } finally {
                this.isSending = false;
            }
        },

        formatTime(timestamp) {
            return new Date(timestamp).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        }
    };
}

// Document Manager Component  
function documentManager() {
    return {
        selectedFiles: [],
        isDragging: false,
        isUploading: false,
        uploadProgress: 0,
        uploadStatus: '',
        uploadSuccess: false,
        documents: [],
        embeddedCount: 0,

        async init() {
            await this.loadDocuments();
        },

        handleDrop(event) {
            this.isDragging = false;
            const files = Array.from(event.dataTransfer.files);
            this.addFiles(files);
        },

        handleFileSelect(event) {
            const files = Array.from(event.target.files);
            this.addFiles(files);
        },

        addFiles(files) {
            const validFiles = files.filter(file => {
                const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
                const maxSize = 10 * 1024 * 1024; // 10MB
                return validTypes.includes(file.type) && file.size <= maxSize;
            });

            this.selectedFiles = [...this.selectedFiles, ...validFiles];
        },

        removeFile(index) {
            this.selectedFiles.splice(index, 1);
        },

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },

        async uploadFiles() {
            if (this.selectedFiles.length === 0) return;

            this.isUploading = true;
            this.uploadProgress = 0;
            this.uploadStatus = '';

            try {
                for (let i = 0; i < this.selectedFiles.length; i++) {
                    const file = this.selectedFiles[i];
                    const formData = new FormData();
                    formData.append('document', file);

                    const response = await fetch(`${API_BASE}/api/embed/`, {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        this.uploadProgress = ((i + 1) / this.selectedFiles.length) * 100;
                        
                        if (i === this.selectedFiles.length - 1) {
                            this.uploadStatus = `Successfully uploaded and embedded ${this.selectedFiles.length} document(s)`;
                            this.uploadSuccess = true;
                            this.selectedFiles = [];
                            await this.loadDocuments();
                        }
                    } else {
                        throw new Error(`Failed to upload ${file.name}`);
                    }
                }
            } catch (error) {
                console.error('Upload error:', error);
                this.uploadStatus = `Upload failed: ${error.message}`;
                this.uploadSuccess = false;
            } finally {
                this.isUploading = false;
                setTimeout(() => {
                    this.uploadStatus = '';
                }, 5000);
            }
        },

        async loadDocuments() {
            try {
                this.documents = [
                    {
                        id: 1,
                        name: 'Advancing-Digital-Inclusion-for-Persons-with-Disabilities-in-Africa.pdf',
                        uploaded_at: new Date().toISOString(),
                        embedded: true
                    },
                    {
                        id: 2,
                        name: 'ssrn-5151540.docx',
                        uploaded_at: new Date().toISOString(),
                        embedded: true
                    }
                ];
                
                this.embeddedCount = this.documents.filter(doc => doc.embedded).length;
            } catch (error) {
                console.error('Error loading documents:', error);
            }
        },

        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString();
        },

        async deleteDocument(docId) {
            if (confirm('Are you sure you want to delete this document?')) {
                this.documents = this.documents.filter(doc => doc.id !== docId);
                this.embeddedCount = this.documents.filter(doc => doc.embedded).length;
            }
        }
    };
}

// Settings Manager Component
function settingsManager() {
    return {
        init() {
            console.log('Settings manager initialized');
        }
    };
}

// Initialize Alpine.js components
document.addEventListener('alpine:init', () => {
    console.log('Alpine.js initialized');
});
