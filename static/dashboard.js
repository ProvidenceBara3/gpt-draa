// Dashboard JavaScript for GPT-DRAA Monitoring
const API_BASE = 'http://localhost:8000/api';

// Main App Controller for page navigation
function appController() {
    return {
        currentPage: 'dashboard',
        
        init() {
            // Initialize the app
            console.log('GPT-DRAA Dashboard initialized');
        },
        
        refreshData() {
            // Refresh current page data
            if (this.currentPage === 'dashboard') {
                // Trigger dashboard refresh
                location.reload();
            }
        }
    };
}

// Alpine.js data and methods
function dashboard() {
    return {
        loading: true,
        stats: {},
        recentQueries: [],
        lowPerformanceQueries: [],
        lastUpdated: '',
        charts: {},
        embeddingStats: {
            totalChunks: 0,
            avgChunkSize: 0,
            lastUpdated: 'Never',
            totalDocuments: 0
        },
        performanceTrends: {},

        async initDashboard() {
            console.log("Initializing dashboard...");
            try {
                // Load all data in parallel
                await Promise.all([
                    this.loadDashboardData(),
                    this.loadEmbeddingStats(),
                    this.loadPerformanceTrends()
                ]);
                
                this.initializeCharts();
                console.log("Dashboard initialized successfully");
            } catch (error) {
                console.error("Failed to initialize dashboard:", error);
                // Still initialize charts with mock data as fallback
                this.initializeCharts();
            }
        },

        async loadDashboardData() {
            try {
                this.loading = true;
                
                // Load real system stats from API
                const statsResponse = await fetch(`${API_BASE}/api/api/monitoring/stats/`);
                if (statsResponse.ok) {
                    const data = await statsResponse.json();
                    this.stats = data.stats || {};
                    console.log('Dashboard stats loaded:', this.stats);
                } else {
                    console.warn('Could not load stats from API, using fallbacks');
                    this.stats = { total_queries: 0 };
                }

                // Load real dashboard data from API
                const dashboardResponse = await fetch(`${API_BASE}/api/api/monitoring/dashboard/`);
                if (dashboardResponse.ok) {
                    const dashboardData = await dashboardResponse.json();
                    this.recentQueries = dashboardData.recent_queries || [];
                    this.lowPerformanceQueries = this.recentQueries.filter(q => 
                        (q.avg_relevance || 0) < 0.03
                    );
                    console.log('Recent queries loaded:', this.recentQueries.length, 'queries');
                } else {
                    console.warn('Could not load dashboard data from API, using mock data');
                    // Fallback to mock data only if API fails
                    this.recentQueries = [
                        {
                            id: 1,
                            query_text: "What is digital inclusion in Africa?",
                            language: "en",
                            response_time_ms: 45000,
                            avg_relevance: 0.087,
                            timestamp: new Date().toISOString()
                        },
                        {
                            id: 2,
                            query_text: "How to improve accessibility for persons with disabilities?",
                            language: "en", 
                            response_time_ms: 52000,
                            avg_relevance: 0.092,
                            timestamp: new Date(Date.now() - 300000).toISOString()
                        },
                        {
                            id: 3,
                            query_text: "What are assistive technologies?",
                            language: "en",
                            response_time_ms: 38000,
                            avg_relevance: 0.075,
                            timestamp: new Date(Date.now() - 600000).toISOString()
                        },
                        {
                            id: 4,
                            query_text: "Digital divide challenges in rural areas",
                            language: "en",
                            response_time_ms: 67000,
                            avg_relevance: 0.021,
                            timestamp: new Date(Date.now() - 900000).toISOString()
                        }
                    ];
                    this.lowPerformanceQueries = this.recentQueries.filter(q => 
                        (q.avg_relevance || 0) < 0.03
                    );
                    console.log('Using mock recent queries:', this.recentQueries.length, 'queries');
                }

                this.lastUpdated = new Date().toLocaleTimeString();
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
                // Use mock data as final fallback
                this.stats = { total_queries: 0 };
                this.recentQueries = [];
            } finally {
                this.loading = false;
            }
        },

        async loadEmbeddingStats() {
            try {
                console.log("Loading embedding statistics...");
                // Load real embedding stats from API
                const response = await fetch(`${API_BASE}/api/api/monitoring/embeddings/`);
                if (response.ok) {
                    this.embeddingStats = await response.json();
                    console.log('Embedding stats loaded:', this.embeddingStats);
                } else {
                    console.warn('Could not load embedding stats from API, using defaults');
                    // Fallback to mock data
                    this.embeddingStats = {
                        totalDocuments: 2,
                        totalChunks: 42,
                        avgChunkSize: 512,
                        lastUpdated: new Date().toLocaleDateString()
                    };
                }
            } catch (error) {
                console.error('Error loading embedding stats:', error);
                // Use defaults as fallback
                this.embeddingStats = {
                    totalDocuments: 2,
                    totalChunks: 42,
                    avgChunkSize: 512,
                    lastUpdated: new Date().toLocaleDateString()
                };
            }
        },

        async loadPerformanceTrends() {
            try {
                console.log("Loading performance trends...");
                const response = await fetch(`${API_BASE}/api/api/monitoring/trends/`);
                if (response.ok) {
                    this.performanceTrends = await response.json();
                    console.log("Performance trends loaded:", this.performanceTrends);
                } else {
                    console.warn("Failed to load performance trends from API");
                    this.performanceTrends = {};
                }
            } catch (error) {
                console.error("Error loading performance trends:", error);
                this.performanceTrends = {};
            }
        },

        async refreshData() {
            const refreshBtn = document.getElementById('refreshBtn');
            if (refreshBtn) {
                const originalContent = refreshBtn.innerHTML;
                refreshBtn.innerHTML = '<i class="fas fa-sync-alt animate-spin mr-2"></i>Refreshing...';
                refreshBtn.disabled = true;
            }
            
            await Promise.all([
                this.loadDashboardData(),
                this.loadEmbeddingStats(),
                this.loadPerformanceTrends()
            ]);
            this.updateCharts();
            
            if (refreshBtn) {
                setTimeout(() => {
                    refreshBtn.innerHTML = originalContent;
                    refreshBtn.disabled = false;
                }, 1000);
            }
        },

        startAutoRefresh() {
            // Auto-refresh every 30 seconds
            setInterval(async () => {
                await Promise.all([
                    this.loadDashboardData(),
                    this.loadEmbeddingStats(),
                    this.loadPerformanceTrends()
                ]);
                this.updateCharts();
            }, 30000);
        },

        initializeCharts() {
            // Response Time Trend Chart
            const responseTimeCtx = document.getElementById('responseTimeChart').getContext('2d');
            this.charts.responseTime = new Chart(responseTimeCtx, {
                type: 'line',
                data: {
                    labels: this.generateTimeLabels(),
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: this.generateResponseTimeData(),
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return value + 'ms';
                                }
                            }
                        }
                    }
                }
            });

            // Relevance Score Distribution Chart
            const relevanceCtx = document.getElementById('relevanceChart').getContext('2d');
            this.charts.relevance = new Chart(relevanceCtx, {
                type: 'doughnut',
                data: {
                    labels: ['High (>0.05)', 'Medium (0.03-0.05)', 'Low (<0.03)'],
                    datasets: [{
                        data: this.generateRelevanceDistribution(),
                        backgroundColor: [
                            'rgb(34, 197, 94)',
                            'rgb(251, 191, 36)',
                            'rgb(239, 68, 68)'
                        ],
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });

            // Query Volume Trend Chart
            const queryVolumeCtx = document.getElementById('queryVolumeChart').getContext('2d');
            this.charts.queryVolume = new Chart(queryVolumeCtx, {
                type: 'bar',
                data: {
                    labels: this.generateDateLabels(),
                    datasets: [{
                        label: 'Queries',
                        data: this.generateQueryVolumeData(),
                        backgroundColor: 'rgba(147, 51, 234, 0.7)',
                        borderColor: 'rgb(147, 51, 234)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
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
        },

        updateCharts() {
            // Update chart data with new information
            if (this.charts.responseTime) {
                this.charts.responseTime.data.datasets[0].data = this.generateResponseTimeData();
                this.charts.responseTime.update();
            }

            if (this.charts.relevance) {
                this.charts.relevance.data.datasets[0].data = this.generateRelevanceDistribution();
                this.charts.relevance.update();
            }

            if (this.charts.queryVolume) {
                this.charts.queryVolume.data.datasets[0].data = this.generateQueryVolumeData();
                this.charts.queryVolume.update();
            }
        },

        generateTimeLabels() {
            const labels = [];
            for (let i = 23; i >= 0; i--) {
                const time = new Date();
                time.setHours(time.getHours() - i);
                labels.push(time.getHours() + ':00');
            }
            return labels;
        },

        generateResponseTimeData() {
            // If we have real trend data, use it
            if (this.performanceTrends && this.performanceTrends.response_time_trend) {
                return this.performanceTrends.response_time_trend.map(item => item.avg_response_time * 1000);
            }
            // Otherwise generate sample data - in real implementation, this would come from API
            return Array.from({ length: 24 }, () => 
                Math.floor(Math.random() * 50000) + 30000 // 30-80 seconds
            );
        },

        generateRelevanceDistribution() {
            // If we have real trend data, use it
            if (this.performanceTrends && this.performanceTrends.relevance_distribution) {
                return this.performanceTrends.relevance_distribution;
            }
            
            // Calculate distribution from recent queries
            if (!this.recentQueries.length) return [70, 20, 10]; // Default values
            
            const high = this.recentQueries.filter(q => (q.avg_relevance || 0) > 0.05).length;
            const medium = this.recentQueries.filter(q => {
                const rel = q.avg_relevance || 0;
                return rel >= 0.03 && rel <= 0.05;
            }).length;
            const low = this.recentQueries.filter(q => (q.avg_relevance || 0) < 0.03).length;
            
            return [high, medium, low];
        },

        generateDateLabels() {
            const labels = [];
            for (let i = 6; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
            }
            return labels;
        },

        generateQueryVolumeData() {
            // If we have real trend data, use it
            if (this.performanceTrends && this.performanceTrends.query_volume_trend) {
                return this.performanceTrends.query_volume_trend.map(item => item.count);
            }
            // Generate sample weekly data as fallback
            return [12, 8, 15, 22, 18, 25, this.stats.total_queries || 7];
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

        getLanguageName(code) {
            const languages = {
                'en': 'English',
                'fr': 'French',
                'sw': 'Swahili',
                'am': 'Amharic'
            };
            return languages[code] || code.toUpperCase();
        },

        getLanguageColor(code) {
            const colors = {
                'en': 'bg-blue-500',
                'fr': 'bg-red-500',
                'sw': 'bg-green-500',
                'am': 'bg-yellow-500'
            };
            return colors[code] || 'bg-gray-500';
        },

        getSystemHealth() {
            const avgResponseTime = this.stats.last_day?.avg_response_time || 0;
            const avgRelevance = this.stats.last_day?.avg_relevance || 0;
            
            if (avgResponseTime < 5000 && avgRelevance > 0.05) return 'Excellent';
            if (avgResponseTime < 10000 && avgRelevance > 0.03) return 'Good';
            if (avgResponseTime < 20000 && avgRelevance > 0.02) return 'Fair';
            return 'Poor';
        },

        getPerformanceGrade() {
            const avgResponseTime = this.stats.last_day?.avg_response_time || 0;
            const avgRelevance = this.stats.last_day?.avg_relevance || 0;
            
            let score = 0;
            
            // Response time score (40% weight)
            if (avgResponseTime < 5000) score += 40;
            else if (avgResponseTime < 10000) score += 25;
            else score += 10;
            
            // Relevance score (40% weight)
            if (avgRelevance > 0.05) score += 40;
            else if (avgRelevance > 0.03) score += 25;
            else score += 10;
            
            // Availability score (20% weight)
            score += 20; // Assume 100% availability for now
            
            if (score >= 90) return 'A';
            if (score >= 80) return 'B';
            if (score >= 70) return 'C';
            if (score >= 60) return 'D';
            return 'F';
        }
    }
}

// File Upload Component
function fileUpload() {
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
                    formData.append('file', file);

                    const response = await fetch(`${API_BASE}/api/embed/`, {
                        method: 'POST',
                        body: formData
                    });

                    if (response.ok) {
                        const result = await response.json();
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
                
                // Clear status after 5 seconds
                setTimeout(() => {
                    this.uploadStatus = '';
                }, 5000);
            }
        },

        async loadDocuments() {
            try {
                // For now, we'll simulate document list
                // In a real implementation, you'd have an API endpoint to list documents
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

        async deleteDocument(docId) {
            if (confirm('Are you sure you want to delete this document?')) {
                try {
                    // In a real implementation, you'd call a delete API
                    this.documents = this.documents.filter(doc => doc.id !== docId);
                    this.embeddedCount = this.documents.filter(doc => doc.embedded).length;
                } catch (error) {
                    console.error('Error deleting document:', error);
                }
            }
        },

        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString();
        }
    };
}

// Quick Ask Component
function quickAsk() {
    return {
        question: '',
        response: '',
        isAsking: false,
        contextCount: 0,

        async askQuestion() {
            if (!this.question.trim() || this.isAsking) return;

            this.isAsking = true;
            this.response = '';
            this.contextCount = 0;

            try {
                const response = await fetch(`${API_BASE}/api/ask/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: this.question,
                        language: 'en'
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    this.response = data.response;
                    this.contextCount = data.context_used ? data.context_used.length : 0;
                } else {
                    this.response = 'Sorry, I encountered an error while processing your question.';
                }
            } catch (error) {
                console.error('Error asking question:', error);
                this.response = 'Sorry, I could not connect to the AI service.';
            } finally {
                this.isAsking = false;
            }
        }
    };
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add refresh button functionality - check if element exists first
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            const dashboardData = window.Alpine ? Alpine.store('dashboard') : null;
            if (dashboardData && dashboardData.refreshData) {
                dashboardData.refreshData();
            }
        });
    }

    // Add smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
});

// Add Alpine.js global refresh function
document.addEventListener('alpine:init', () => {
    Alpine.store('dashboard', {
        async refreshData() {
            // This will be called from the refresh button
            location.reload();
        }
    });
});

// CSS for better animations and transitions
const style = document.createElement('style');
style.textContent = `
    [x-cloak] { display: none !important; }
    
    .animate-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: .5;
        }
    }
    
    .animate-spin {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }
    
    .transition-colors {
        transition-property: background-color, border-color, color, fill, stroke;
        transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
        transition-duration: 150ms;
    }
`;
document.head.appendChild(style);

// Chat Interface Component
function chatInterface() {
    return {
        chatMessages: [],
        currentMessage: '',
        isTyping: false,
        isSending: false,

        async sendMessage() {
            if (!this.currentMessage.trim() || this.isSending) return;

            const userMessage = {
                type: 'user',
                content: this.currentMessage.trim(),
                timestamp: new Date(),
                status: 'sent'
            };

            this.chatMessages.push(userMessage);
            const prompt = this.currentMessage.trim();
            this.currentMessage = '';
            this.isSending = true;
            this.isTyping = true;

            // Scroll to bottom
            this.$nextTick(() => {
                const chatArea = document.querySelector('.overflow-y-auto');
                if (chatArea) {
                    chatArea.scrollTop = chatArea.scrollHeight;
                }
            });

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
                        contextCount: data.context_used ? data.context_used.length : 0,
                        status: 'sent',
                        rating: null,
                        queryId: data.query_id, // Store query ID for feedback tracking
                        regenerationCount: 0,
                        suggestions: this.generateFollowUpSuggestions(data.response, prompt)
                    };
                    this.chatMessages.push(aiMessage);
                } else {
                    const errorMessage = {
                        type: 'ai',
                        content: 'Sorry, I encountered an error while processing your question. Please try again.',
                        timestamp: new Date(),
                        contextCount: 0,
                        status: 'error',
                        suggestions: []
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
                    contextCount: 0,
                    status: 'error',
                    suggestions: []
                };
                this.chatMessages.push(errorMessage);
            } finally {
                this.isSending = false;
                // Scroll to bottom after response
                this.$nextTick(() => {
                    const chatArea = document.querySelector('.overflow-y-auto');
                    if (chatArea) {
                        chatArea.scrollTop = chatArea.scrollHeight;
                    }
                });
            }
        },

        // Copy message to clipboard
        async copyMessage(content, message) {
            console.log('Copy button clicked!', content, message); // Debug log
            try {
                await navigator.clipboard.writeText(content);
                this.showNotification('Message copied to clipboard!', 'success');
                
                // Record the copy action
                if (message.queryId) {
                    await this.recordUserAction(message.queryId, 'copy', {
                        content_length: content.length,
                        action_timestamp: new Date().toISOString()
                    });
                }
            } catch (err) {
                console.error('Failed to copy message:', err);
                this.showNotification('Failed to copy message', 'error');
            }
        },

        // Regenerate AI response
        async regenerateResponse(messageIndex) {
            const message = this.chatMessages[messageIndex];
            if (message.type !== 'ai') return;

            // Find the user message that triggered this response
            let userPrompt = '';
            for (let i = messageIndex - 1; i >= 0; i--) {
                if (this.chatMessages[i].type === 'user') {
                    userPrompt = this.chatMessages[i].content;
                    break;
                }
            }

            if (!userPrompt) return;

            // Record regeneration action
            if (message.queryId) {
                await this.recordUserAction(message.queryId, 'regenerate', {
                    original_response_length: message.content.length,
                    regeneration_number: (message.regenerationCount || 0) + 1
                });
            }

            // Mark as regenerating
            message.status = 'sending';
            message.regenerationCount = (message.regenerationCount || 0) + 1;
            this.isTyping = true;

            try {
                const response = await fetch(`${API_BASE}/api/ask/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: userPrompt,
                        language: 'en'
                    })
                });

                this.isTyping = false;

                if (response.ok) {
                    const data = await response.json();
                    message.content = data.response;
                    message.timestamp = new Date();
                    message.status = 'sent';
                    message.rating = null; // Reset rating
                    message.queryId = data.query_id; // Update with new query ID
                    message.suggestions = this.generateFollowUpSuggestions(data.response, userPrompt);
                    
                    this.showNotification('Response regenerated successfully!', 'success');
                } else {
                    message.status = 'error';
                    this.showNotification('Failed to regenerate response', 'error');
                }
            } catch (error) {
                console.error('Error regenerating response:', error);
                message.status = 'error';
                this.isTyping = false;
                this.showNotification('Failed to regenerate response', 'error');
            }
        },

        // Rate message with backend recording
        async rateMessage(message, rating) {
            console.log('Rate button clicked!', message, rating); // Debug log
            const previousRating = message.rating;
            message.rating = message.rating === rating ? null : rating;
            
            // Record rating in backend
            if (message.queryId) {
                try {
                    const response = await fetch(`${API_BASE}/api/monitoring/rate/`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            query_id: message.queryId,
                            user_rating: rating,
                            feedback_type: 'rating'
                        })
                    });

                    if (response.ok) {
                        const data = await response.json();
                        console.log('Rating saved:', data);
                        
                        const feedbackText = rating === 'up' 
                            ? 'Thank you for the positive feedback!' 
                            : 'Thank you for the feedback. We\'ll work to improve our responses.';
                        this.showNotification(feedbackText, 'success');
                    } else {
                        // Revert rating if backend save failed
                        message.rating = previousRating;
                        console.error('Rating request failed:', response.status, response.statusText);
                        const responseText = await response.text();
                        console.error('Response body:', responseText);
                        this.showNotification('Failed to save rating', 'error');
                    }
                } catch (error) {
                    console.error('Error saving rating:', error);
                    message.rating = previousRating;
                    this.showNotification('Failed to save rating', 'error');
                }
            } else {
                console.warn('No query ID available for rating');
                const feedbackText = rating === 'up' 
                    ? 'Thank you for the positive feedback!' 
                    : 'Thank you for the feedback. We\'ll work to improve our responses.';
                this.showNotification(feedbackText, 'info');
            }
        },

        // Record user actions for analytics
        async recordUserAction(queryId, actionType, details = {}) {
            try {
                await fetch(`${API_BASE}/api/monitoring/rate/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query_id: queryId,
                        feedback_type: actionType,
                        action_details: details
                    })
                });
            } catch (error) {
                console.error('Failed to record user action:', error);
            }
        },

        // Ask follow-up question
        async askFollowUp(suggestion, originalMessage) {
            // Record follow-up action
            if (originalMessage && originalMessage.queryId) {
                await this.recordUserAction(originalMessage.queryId, 'follow_up', {
                    suggestion_text: suggestion,
                    suggestion_position: originalMessage.suggestions.indexOf(suggestion)
                });
            }
            
            this.currentMessage = suggestion;
            this.sendMessage();
        },

        // Generate follow-up suggestions based on the response
        generateFollowUpSuggestions(response, originalPrompt) {
            const suggestions = [];
            
            // Digital rights related suggestions
            if (response.toLowerCase().includes('digital rights') || originalPrompt.toLowerCase().includes('digital rights')) {
                suggestions.push('What are the main challenges?');
                suggestions.push('How can this be improved?');
                suggestions.push('What are the legal frameworks?');
            }
            
            // Africa-specific suggestions
            if (response.toLowerCase().includes('africa') || originalPrompt.toLowerCase().includes('africa')) {
                suggestions.push('Which African countries lead in this?');
                suggestions.push('What are the regional differences?');
                suggestions.push('What role do governments play?');
            }
            
            // Accessibility suggestions
            if (response.toLowerCase().includes('accessibility') || response.toLowerCase().includes('disabilities')) {
                suggestions.push('What assistive technologies help?');
                suggestions.push('How can barriers be removed?');
                suggestions.push('What are best practices?');
            }
            
            // Generic follow-ups
            if (suggestions.length < 2) {
                suggestions.push('Can you provide examples?');
                suggestions.push('What are the next steps?');
                suggestions.push('How does this impact communities?');
            }
            
            return suggestions.slice(0, 3); // Limit to 3 suggestions
        },

        // Enhanced time formatting with relative time
        formatEnhancedTime(date) {
            const now = new Date();
            const messageTime = new Date(date);
            const diffMs = now - messageTime;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            
            if (diffMins < 1) return 'Just now';
            if (diffMins < 60) return `${diffMins}m ago`;
            if (diffHours < 24) return `${diffHours}h ago`;
            
            return messageTime.toLocaleString([], { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit' 
            });
        },

        // Show notification (you can enhance this with a toast library)
        showNotification(message, type) {
            // Simple console notification for now - you could enhance with toast UI
            console.log(`${type.toUpperCase()}: ${message}`);
            
            // Create a simple toast notification
            const toast = document.createElement('div');
            toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-lg text-white text-sm font-medium transition-all duration-300 ${
                type === 'success' ? 'bg-green-500' : 
                type === 'error' ? 'bg-red-500' : 
                'bg-blue-500'
            }`;
            toast.textContent = message;
            
            document.body.appendChild(toast);
            
            // Remove after 3 seconds
            setTimeout(() => {
                toast.remove();
            }, 3000);
        },

        formatTime(date) {
            return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }
    };
}

// Document Manager Component
function documentManager() {
    return {
        selectedFiles: [],
        documents: [],
        isDragging: false,
        isUploading: false,
        uploadProgress: 0,
        uploadStatus: '',
        uploadSuccess: false,
        embeddedCount: 0,
        totalChunks: 0,
        documentStats: {},
        showLanguageSelector: false,
        showMetadataForm: false,
        selectedLanguage: 'en',
        documentMetadata: {
            title: '',
            author: '',
            source: '',
            publication_date: '',
            category: 'other',
            description: '',
            tags: '',
            document_type: 'other',
            geographic_scope: '',
            target_audience: ''
        },
        editingDocument: null,
        showEditModal: false,

        init() {
            this.loadDocuments();
            this.loadDocumentStats();
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
                
                if (!validTypes.includes(file.type)) {
                    alert(`File ${file.name} is not a supported type. Please use PDF, DOCX, or TXT files.`);
                    return false;
                }
                
                if (file.size > maxSize) {
                    alert(`File ${file.name} is too large. Maximum size is 10MB.`);
                    return false;
                }
                
                return true;
            });

            this.selectedFiles = [...this.selectedFiles, ...validFiles];
            
            // Show language selector and metadata form if files are selected
            if (this.selectedFiles.length > 0) {
                this.showLanguageSelector = true;
                this.showMetadataForm = true;
            }
        },

        removeFile(index) {
            this.selectedFiles.splice(index, 1);
            if (this.selectedFiles.length === 0) {
                this.showLanguageSelector = false;
                this.showMetadataForm = false;
                this.resetMetadataForm();
            }
        },

        resetMetadataForm() {
            this.documentMetadata = {
                title: '',
                author: '',
                source: '',
                publication_date: '',
                category: 'other',
                description: '',
                tags: '',
                document_type: 'other',
                geographic_scope: '',
                target_audience: ''
            };
        },

        async uploadFiles() {
            if (this.selectedFiles.length === 0 || this.isUploading) return;

            this.isUploading = true;
            this.uploadProgress = 0;
            this.uploadStatus = '';
            this.uploadSuccess = false;

            try {
                for (let i = 0; i < this.selectedFiles.length; i++) {
                    const file = this.selectedFiles[i];
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('language', this.selectedLanguage);
                    
                    // Add metadata
                    Object.keys(this.documentMetadata).forEach(key => {
                        if (this.documentMetadata[key]) {
                            formData.append(key, this.documentMetadata[key]);
                        }
                    });

                    const response = await fetch(`${API_BASE}/api/embed/`, {
                        method: 'POST',
                        body: formData
                    });

                    this.uploadProgress = Math.round(((i + 1) / this.selectedFiles.length) * 100);

                    if (!response.ok) {
                        const errorData = await response.json();
                        throw new Error(errorData.error || `Failed to upload ${file.name}`);
                    }

                    const result = await response.json();
                    console.log(`Upload result for ${file.name}:`, result);
                }

                this.uploadSuccess = true;
                this.uploadStatus = `Successfully uploaded ${this.selectedFiles.length} document(s) and created embeddings.`;
                this.selectedFiles = [];
                this.showLanguageSelector = false;
                this.showMetadataForm = false;
                this.resetMetadataForm();
                await this.loadDocuments();
                await this.loadDocumentStats();

            } catch (error) {
                console.error('Upload error:', error);
                this.uploadSuccess = false;
                this.uploadStatus = `Upload failed: ${error.message}`;
            } finally {
                this.isUploading = false;
                
                // Clear status after 5 seconds
                setTimeout(() => {
                    this.uploadStatus = '';
                }, 5000);
            }
        },

        async loadDocuments() {
            try {
                const response = await fetch(`${API_BASE}/api/documents/`);
                if (response.ok) {
                    const data = await response.json();
                    this.documents = data.documents || [];
                    this.embeddedCount = data.embedded_count || 0;
                    
                    // Initialize showDetails property for each document
                    this.documents.forEach(doc => {
                        doc.showDetails = false;
                    });
                    
                    console.log('Documents loaded:', this.documents.length);
                } else {
                    console.error('Failed to load documents');
                    // Fallback to demo data
                    this.documents = [
                        {
                            id: 1,
                            title: 'Advancing Digital Inclusion for Persons with Disabilities in Africa',
                            file_name: 'Advancing-Digital-Inclusion-for-Persons-with-Disabilities-in-Africa.pdf',
                            uploaded_at: '2025-01-15T10:30:00Z',
                            embedded_chunks: 35,
                            is_embedded: true,
                            language: 'en',
                            file_size: 2048576,
                            author: 'Digital Rights Foundation',
                            source: 'African Union',
                            category: 'accessibility',
                            category_display: 'Accessibility',
                            showDetails: false
                        }
                    ];
                    this.embeddedCount = this.documents.filter(doc => doc.is_embedded).length;
                }
            } catch (error) {
                console.error('Error loading documents:', error);
                this.documents = [];
            }
        },

        editDocument(doc) {
            this.editingDocument = { ...doc };
            this.showEditModal = true;
        },

        async saveDocumentEdit() {
            if (!this.editingDocument) return;

            try {
                const response = await fetch(`${API_BASE}/api/documents/${this.editingDocument.id}/update/`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(this.editingDocument)
                });

                if (response.ok) {
                    await this.loadDocuments();
                    this.showEditModal = false;
                    this.editingDocument = null;
                    
                    this.uploadStatus = 'Document updated successfully';
                    this.uploadSuccess = true;
                    setTimeout(() => {
                        this.uploadStatus = '';
                    }, 3000);
                } else {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to update document');
                }
            } catch (error) {
                console.error('Error updating document:', error);
                this.uploadStatus = `Failed to update document: ${error.message}`;
                this.uploadSuccess = false;
                setTimeout(() => {
                    this.uploadStatus = '';
                }, 5000);
            }
        },

        cancelEdit() {
            this.showEditModal = false;
            this.editingDocument = null;
        },

        getCategoryOptions() {
            return [
                { value: 'internet_freedom', label: 'Internet Freedom' },
                { value: 'accessibility', label: 'Accessibility' },
                { value: 'gender_violence', label: 'Technology Facilitated Gender-Based Violence' },
                { value: 'digital_inclusion', label: 'Digital Inclusion' },
                { value: 'policy_governance', label: 'Policy & Governance' },
                { value: 'cybersecurity', label: 'Cybersecurity' },
                { value: 'data_protection', label: 'Data Protection & Privacy' },
                { value: 'digital_economy', label: 'Digital Economy' },
                { value: 'education_literacy', label: 'Digital Education & Literacy' },
                { value: 'infrastructure', label: 'Digital Infrastructure' },
                { value: 'research_reports', label: 'Research & Reports' },
                { value: 'legal_frameworks', label: 'Legal Frameworks' },
                { value: 'other', label: 'Other' }
            ];
        },

        getDocumentTypeOptions() {
            return [
                { value: 'report', label: 'Report' },
                { value: 'policy', label: 'Policy Document' },
                { value: 'research', label: 'Research Paper' },
                { value: 'guideline', label: 'Guidelines' },
                { value: 'case_study', label: 'Case Study' },
                { value: 'presentation', label: 'Presentation' },
                { value: 'manual', label: 'Manual/Handbook' },
                { value: 'legislation', label: 'Legislation' },
                { value: 'other', label: 'Other' }
            ];
        },

        async loadDocumentStats() {
            try {
                const response = await fetch(`${API_BASE}/api/documents/stats/`);
                if (response.ok) {
                    this.documentStats = await response.json();
                    this.totalChunks = this.documentStats.embedding_stats?.total_chunks || 0;
                    console.log('Document stats loaded:', this.documentStats);
                } else {
                    console.error('Failed to load document stats');
                }
            } catch (error) {
                console.error('Error loading document stats:', error);
            }
        },

        async deleteDocument(docId) {
            if (confirm('Are you sure you want to delete this document? This will also remove all its embeddings.')) {
                try {
                    const response = await fetch(`${API_BASE}/api/documents/${docId}/delete/`, {
                        method: 'DELETE'
                    });

                    if (response.ok) {
                        const result = await response.json();
                        console.log('Delete result:', result);
                        
                        // Refresh the document list
                        await this.loadDocuments();
                        await this.loadDocumentStats();
                        
                        // Show success message
                        this.uploadStatus = result.message;
                        this.uploadSuccess = true;
                        setTimeout(() => {
                            this.uploadStatus = '';
                        }, 3000);
                    } else {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Failed to delete document');
                    }
                } catch (error) {
                    console.error('Error deleting document:', error);
                    this.uploadStatus = `Failed to delete document: ${error.message}`;
                    this.uploadSuccess = false;
                    setTimeout(() => {
                        this.uploadStatus = '';
                    }, 5000);
                }
            }
        },

        async reEmbedDocument(docId) {
            if (confirm('This will re-process the document and recreate its embeddings. Continue?')) {
                try {
                    const response = await fetch(`${API_BASE}/api/documents/${docId}/re-embed/`, {
                        method: 'POST'
                    });

                    if (response.ok) {
                        const result = await response.json();
                        console.log('Re-embed result:', result);
                        
                        // Refresh the document list
                        await this.loadDocuments();
                        await this.loadDocumentStats();
                        
                        // Show success message
                        this.uploadStatus = result.message;
                        this.uploadSuccess = true;
                        setTimeout(() => {
                            this.uploadStatus = '';
                        }, 3000);
                    } else {
                        const errorData = await response.json();
                        throw new Error(errorData.error || 'Failed to re-embed document');
                    }
                } catch (error) {
                    console.error('Error re-embedding document:', error);
                    this.uploadStatus = `Failed to re-embed document: ${error.message}`;
                    this.uploadSuccess = false;
                    setTimeout(() => {
                        this.uploadStatus = '';
                    }, 5000);
                }
            }
        },

        getLanguageName(code) {
            const languages = {
                'en': 'English',
                'fr': 'French',
                'sw': 'Swahili',
                'am': 'Amharic'
            };
            return languages[code] || code.toUpperCase();
        },

        getFileTypeIcon(fileName) {
            const extension = fileName.split('.').pop().toLowerCase();
            switch (extension) {
                case 'pdf':
                    return 'fas fa-file-pdf text-red-600';
                case 'docx':
                case 'doc':
                    return 'fas fa-file-word text-blue-600';
                case 'txt':
                    return 'fas fa-file-alt text-gray-600';
                default:
                    return 'fas fa-file text-gray-600';
            }
        },

        formatDate(dateString) {
            if (!dateString) return '';
            return new Date(dateString).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        },

        formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    };
}

// Settings Manager Component
function settingsManager() {
    return {
        modelStatus: 'online',
        chromaStatus: 'active',
        temperature: 0.7,
        maxTokens: 1024,
        autoRefresh: true,
        notifications: false,
        darkMode: false,

        init() {
            this.loadSettings();
        },

        loadSettings() {
            // Load settings from localStorage or API
            const savedSettings = localStorage.getItem('gpt-draa-settings');
            if (savedSettings) {
                const settings = JSON.parse(savedSettings);
                Object.assign(this, settings);
            }
        },

        saveSettings() {
            // Save settings to localStorage
            const settings = {
                temperature: this.temperature,
                maxTokens: this.maxTokens,
                autoRefresh: this.autoRefresh,
                notifications: this.notifications,
                darkMode: this.darkMode
            };
            localStorage.setItem('gpt-draa-settings', JSON.stringify(settings));
        },

        toggleSetting(settingName) {
            this[settingName] = !this[settingName];
            this.saveSettings();
            
            // Apply immediate changes
            if (settingName === 'darkMode') {
                this.applyTheme();
            }
        },

        applyTheme() {
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
            } else {
                document.documentElement.classList.remove('dark');
            }
        },

        async clearChatHistory() {
            if (confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) {
                try {
                    // Clear chat messages from localStorage or API
                    localStorage.removeItem('chat-messages');
                    alert('Chat history cleared successfully.');
                } catch (error) {
                    console.error('Error clearing chat history:', error);
                    alert('Failed to clear chat history.');
                }
            }
        },

        async resetDatabase() {
            if (confirm('Are you sure you want to reset the vector database? This will remove all embedded documents and require re-uploading.')) {
                try {
                    const response = await fetch('/api/reset-database/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    });
                    
                    if (response.ok) {
                        alert('Vector database reset successfully.');
                    } else {
                        throw new Error('Failed to reset database');
                    }
                } catch (error) {
                    console.error('Error resetting database:', error);
                    alert('Failed to reset database.');
                }
            }
        },

        async exportData() {
            try {
                const response = await fetch('/api/export-data/', {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `gpt-draa-data-${new Date().toISOString().split('T')[0]}.json`;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    throw new Error('Failed to export data');
                }
            } catch (error) {
                console.error('Error exporting data:', error);
                alert('Failed to export data.');
            }
        }
    };
}

// Register all Alpine.js components
document.addEventListener('alpine:init', () => {
    console.log('Registering Alpine.js components...');
    
    // Register all components
    Alpine.data('appController', appController);
    Alpine.data('dashboard', dashboard);
    Alpine.data('fileUpload', fileUpload);
    Alpine.data('quickAsk', quickAsk);
    Alpine.data('chatInterface', chatInterface);
    Alpine.data('documentManager', documentManager);
    Alpine.data('settingsManager', settingsManager);
    
    console.log('All Alpine.js components registered successfully');
});
