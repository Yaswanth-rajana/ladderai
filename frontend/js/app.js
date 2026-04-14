// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Page navigation
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const page = btn.dataset.page;
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        document.getElementById(`${page}-page`).classList.add('active');
        
        if (page === 'dashboard') loadDocuments();
        if (page === 'stats') loadStatistics();
    });
});

// File upload handling
const fileInput = document.getElementById('file-input');
const uploadArea = document.getElementById('upload-area');

uploadArea.addEventListener('click', () => fileInput.click());
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = '#667eea';
});
uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = '#ccc';
});
uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(f => f.type === 'application/pdf');
    if (files.length > 0) uploadFiles(files);
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) uploadFiles(Array.from(e.target.files));
});

async function uploadFiles(files) {
    const progressDiv = document.getElementById('upload-progress');
    const resultsDiv = document.getElementById('upload-results');
    const progressFill = document.getElementById('progress-fill');
    const statusText = document.getElementById('upload-status');
    
    progressDiv.style.display = 'block';
    resultsDiv.innerHTML = '';
    
    let completed = 0;
    const results = [];
    
    for (const file of files) {
        statusText.textContent = `Uploading ${file.name}...`;
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${API_BASE_URL}/documents/upload`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            completed++;
            progressFill.style.width = `${(completed / files.length) * 100}%`;
            progressFill.textContent = `${Math.round((completed / files.length) * 100)}%`;
            
            results.push({
                filename: file.name,
                success: response.ok,
                document_id: data.document_id,
                message: data.message || (response.ok ? 'Success' : 'Failed')
            });
        } catch (error) {
            results.push({
                filename: file.name,
                success: false,
                message: error.message
            });
        }
    }
    
    statusText.textContent = 'Upload complete!';
    displayUploadResults(results);
    
    setTimeout(() => {
        progressDiv.style.display = 'none';
        loadDocuments();
    }, 2000);
}

function displayUploadResults(results) {
    const resultsDiv = document.getElementById('upload-results');
    resultsDiv.innerHTML = '<h3>Upload Results:</h3>';
    
    results.forEach(result => {
        const resultDiv = document.createElement('div');
        resultDiv.className = `document-item`;
        resultDiv.innerHTML = `
            <div class="document-header">
                <span class="document-vendor">${result.filename}</span>
                <span class="document-status ${result.success ? 'status-completed' : 'status-failed'}">
                    ${result.success ? '✓ Uploaded' : '✗ Failed'}
                </span>
            </div>
            <div class="document-details">
                <span>${result.message}</span>
                ${result.document_id ? `<span>ID: ${result.document_id.substring(0, 8)}...</span>` : ''}
            </div>
        `;
        resultsDiv.appendChild(resultDiv);
    });
}

// Load documents
async function loadDocuments() {
    const listDiv = document.getElementById('documents-list');
    listDiv.innerHTML = '<div class="loading">Loading documents...</div>';
    
    try {
        const response = await fetch(`${API_BASE_URL}/documents/`);
        const documents = await response.json();
        
        if (documents.length === 0) {
            listDiv.innerHTML = '<div class="loading">No documents found. Upload some invoices!</div>';
            return;
        }
        
        displayDocuments(documents);
    } catch (error) {
        listDiv.innerHTML = `<div class="loading">Error loading documents: ${error.message}</div>`;
    }
}

function displayDocuments(documents) {
    const listDiv = document.getElementById('documents-list');
    const searchFilter = document.getElementById('search-filter').value.toLowerCase();
    const statusFilter = document.getElementById('status-filter').value;
    
    let filtered = documents.filter(doc => {
        const matchesSearch = !searchFilter || 
            (doc.extracted_data?.vendor_name?.toLowerCase().includes(searchFilter)) ||
            (doc.extracted_data?.invoice_number?.toLowerCase().includes(searchFilter));
        const matchesStatus = statusFilter === 'all' || doc.status === statusFilter;
        return matchesSearch && matchesStatus;
    });
    
    if (filtered.length === 0) {
        listDiv.innerHTML = '<div class="loading">No matching documents found.</div>';
        return;
    }
    
    listDiv.innerHTML = filtered.map(doc => `
        <div class="document-item" onclick="showDocumentDetail('${doc.id}')">
            <div class="document-header">
                <span class="document-vendor">${doc.extracted_data?.vendor_name || 'Unknown Vendor'}</span>
                <span class="document-status status-${doc.status}">${doc.status}</span>
            </div>
            <div class="document-details">
                <span>📄 ${doc.extracted_data?.invoice_number || 'No Invoice #'}</span>
                <span>📅 ${doc.extracted_data?.invoice_date || 'No Date'}</span>
                <span>💰 ${doc.extracted_data?.currency || ''} ${doc.extracted_data?.total_amount?.toFixed(2) || '0'}</span>
                <span class="confidence-badge confidence-${getConfidenceLevel(doc.confidence)}">
                    🎯 ${doc.confidence || 0}%
                </span>
                ${doc.validation_errors?.length > 0 ? 
                    `<span class="error-badge">⚠️ ${doc.validation_errors.length} errors</span>` : 
                    '<span class="error-badge">✅ Valid</span>'}
            </div>
        </div>
    `).join('');
    
    // Add search and filter listeners
    document.getElementById('search-filter').addEventListener('input', () => displayDocuments(documents));
    document.getElementById('status-filter').addEventListener('change', () => displayDocuments(documents));
}

function getConfidenceLevel(confidence) {
    if (confidence >= 80) return 'high';
    if (confidence >= 50) return 'medium';
    return 'low';
}

// Show document detail modal
async function showDocumentDetail(documentId) {
    const modal = document.getElementById('detail-modal');
    const modalBody = document.getElementById('modal-body');
    
    modalBody.innerHTML = '<div class="loading">Loading document details...</div>';
    modal.style.display = 'block';
    
    try {
        const response = await fetch(`${API_BASE_URL}/documents/${documentId}`);
        const doc = await response.json();
        
        modalBody.innerHTML = `
            <div style="padding: 20px;">
                <h2>Invoice Details</h2>
                
                <div class="card" style="margin-top: 20px;">
                    <h3>📋 Extracted Information</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr><td style="padding: 8px;"><strong>Vendor:</strong></td><td>${doc.extracted_data?.vendor_name || 'N/A'}</td></tr>
                        <tr><td style="padding: 8px;"><strong>Invoice #:</strong></td><td>${doc.extracted_data?.invoice_number || 'N/A'}</td></tr>
                        <tr><td style="padding: 8px;"><strong>Date:</strong></td><td>${doc.extracted_data?.invoice_date || 'N/A'}</td></tr>
                        <tr><td style="padding: 8px;"><strong>Currency:</strong></td><td>${doc.extracted_data?.currency || 'N/A'}</td></tr>
                        <tr><td style="padding: 8px;"><strong>Total Amount:</strong></td><td>${doc.extracted_data?.currency || ''} ${doc.extracted_data?.total_amount?.toFixed(2) || '0'}</td></tr>
                        <tr><td style="padding: 8px;"><strong>Tax Amount:</strong></td><td>${doc.extracted_data?.currency || ''} ${doc.extracted_data?.tax_amount?.toFixed(2) || '0'}</td></tr>
                    </table>
                </div>
                
                ${doc.extracted_data?.line_items?.length > 0 ? `
                <div class="card">
                    <h3>📦 Line Items</h3>
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr><th style="text-align: left; padding: 8px;">Description</th><th>Qty</th><th>Unit Price</th><th>Line Total</th></tr>
                        </thead>
                        <tbody>
                            ${doc.extracted_data.line_items.map(item => `
                                <tr>
                                    <td style="padding: 8px;">${item.description || 'N/A'}</td>
                                    <td style="text-align: center;">${item.quantity || 0}</td>
                                    <td style="text-align: right;">${doc.extracted_data.currency || ''} ${item.unit_price?.toFixed(2) || '0'}</td>
                                    <td style="text-align: right;">${doc.extracted_data.currency || ''} ${item.line_total?.toFixed(2) || '0'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ` : ''}
                
                <div class="card">
                    <h3>✅ Validation Results</h3>
                    <p><strong>Confidence Score:</strong> 
                        <span class="confidence-badge confidence-${getConfidenceLevel(doc.confidence)}" style="font-size: 1.2rem;">
                            ${doc.confidence || 0}%
                        </span>
                    </p>
                    ${doc.validation_errors?.length > 0 ? `
                        <div style="background: #fed7d7; padding: 12px; border-radius: 8px; margin-top: 10px;">
                            <strong>⚠️ Validation Errors:</strong>
                            <ul style="margin-top: 10px; margin-left: 20px;">
                                ${doc.validation_errors.map(err => `<li>${err}</li>`).join('')}
                            </ul>
                        </div>
                    ` : '<div style="background: #c6f6d5; padding: 12px; border-radius: 8px;">✅ No validation errors found!</div>'}
                </div>
                
                <div class="card">
                    <h3>📊 Processing Metadata</h3>
                    <table style="width: 100%;">
                        <tr><td><strong>Status:</strong></td><td>${doc.status}</td></tr>
                        <tr><td><strong>Processing Time:</strong></td><td>${doc.processing_time_ms?.toFixed(2)} ms</td></tr>
                        <tr><td><strong>Pages:</strong></td><td>${doc.pages || 1}</td></tr>
                        <tr><td><strong>Created:</strong></td><td>${new Date(doc.created_at).toLocaleString()}</td></tr>
                    </table>
                </div>
                
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button class="btn btn-secondary" onclick="reprocessDocument('${doc.id}')">🔄 Reprocess</button>
                    <button class="btn btn-danger" onclick="closeModal()">Close</button>
                </div>
            </div>
        `;
    } catch (error) {
        modalBody.innerHTML = `<div class="loading">Error: ${error.message}</div>`;
    }
}

// Reprocess document
async function reprocessDocument(documentId) {
    if (!confirm('Reprocess this invoice? This will re-extract all data.')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/documents/reprocess/${documentId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            alert('Reprocessing started! The document will be updated shortly.');
            setTimeout(() => {
                showDocumentDetail(documentId);
                loadDocuments();
            }, 2000);
        } else {
            alert('Failed to start reprocessing');
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_BASE_URL}/documents/stats/summary`);
        const stats = await response.json();
        
        document.getElementById('total-docs').textContent = stats.total_documents;
        document.getElementById('success-rate').textContent = `${stats.success_rate}%`;
        document.getElementById('avg-confidence').textContent = `${stats.average_confidence}%`;
        document.getElementById('avg-time').textContent = `${stats.average_processing_time_ms}ms`;
        
        // Load error report
        await loadErrorReport();
        
        // Load monitoring metrics
        await loadMonitoringMetrics();
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadErrorReport() {
    const errorDiv = document.getElementById('error-report');
    
    try {
        const response = await fetch(`${API_BASE_URL}/documents/`);
        const docs = await response.json();
        
        const lowConfidence = docs.filter(d => d.confidence && d.confidence < 70);
        const withErrors = docs.filter(d => d.validation_errors?.length > 0);
        const missingFields = [];
        
        docs.forEach(doc => {
            if (doc.extracted_data) {
                const missing = [];
                if (!doc.extracted_data.vendor_name) missing.push('vendor_name');
                if (!doc.extracted_data.invoice_number) missing.push('invoice_number');
                if (!doc.extracted_data.invoice_date) missing.push('invoice_date');
                missingFields.push(...missing);
            }
        });
        
        const mostMissing = {};
        missingFields.forEach(f => mostMissing[f] = (mostMissing[f] || 0) + 1);
        
        errorDiv.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card" style="background: #f56565;">
                    <h3>Low Confidence (<70%)</h3>
                    <p>${lowConfidence.length}</p>
                </div>
                <div class="stat-card" style="background: #ed8936;">
                    <h3>Documents with Errors</h3>
                    <p>${withErrors.length}</p>
                </div>
            </div>
            ${Object.keys(mostMissing).length > 0 ? `
                <h3>Most Common Missing Fields:</h3>
                <ul>
                    ${Object.entries(mostMissing).map(([field, count]) => `<li>${field}: ${count} time(s)</li>`).join('')}
                </ul>
            ` : '<p>No missing fields detected!</p>'}
        `;
    } catch (error) {
        errorDiv.innerHTML = `<div class="loading">Error loading error report: ${error.message}</div>`;
    }
}

async function loadMonitoringMetrics() {
    const metricsDiv = document.getElementById('monitoring-metrics');
    
    try {
        const response = await fetch(`${API_BASE_URL}/documents/`);
        const docs = await response.json();
        
        const completed = docs.filter(d => d.status === 'completed');
        const avgConfidence = completed.reduce((sum, d) => sum + (d.confidence || 0), 0) / (completed.length || 1);
        const avgTime = completed.reduce((sum, d) => sum + (d.processing_time_ms || 0), 0) / (completed.length || 1);
        
        metricsDiv.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card" style="background: #48bb78;">
                    <h3>Extraction Success Rate</h3>
                    <p>${((completed.length / docs.length) * 100).toFixed(1)}%</p>
                </div>
                <div class="stat-card" style="background: #4299e1;">
                    <h3>Average Confidence</h3>
                    <p>${avgConfidence.toFixed(1)}%</p>
                </div>
                <div class="stat-card" style="background: #9f7aea;">
                    <h3>Average Processing Time</h3>
                    <p>${avgTime.toFixed(0)}ms</p>
                </div>
                <div class="stat-card" style="background: #ed8936;">
                    <h3>Total Processed</h3>
                    <p>${completed.length}</p>
                </div>
            </div>
        `;
    } catch (error) {
        metricsDiv.innerHTML = `<div class="loading">Error loading metrics: ${error.message}</div>`;
    }
}

// Modal handling
function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

document.querySelector('.close').addEventListener('click', closeModal);
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) closeModal();
};

// Initial load
loadDocuments();