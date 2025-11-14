const API_BASE_URL = window.location.origin;

let creators = [];
let fans = [];
let systemPrompts = [];
let selectedCreator = null;
let selectedFan = null;
let selectedSystemPrompt = null;
let chatMessages = [];
let pendingRecommendations = null;

// Get API key from localStorage
function getApiKey() {
    return localStorage.getItem('api_key') || '';
}

// Fetch data from API
async function fetchData(endpoint, options = {}) {
    try {
        const apiKey = getApiKey();
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': apiKey,
                ...options.headers,
            },
        });

        if (!response.ok) {
            // Handle 401 Unauthorized (invalid API key or session expired)
            if (response.status === 401) {
                // Clear API key and redirect to login
                localStorage.removeItem('api_key');
                window.location.href = '/login';
                return;
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        throw error;
    }
}

// Load all data
async function loadData() {
    try {
        const [creatorsData, fansData, promptsData] = await Promise.all([
            fetchData('/get_creators'),
            fetchData('/get_fans'),
            fetchData('/get_system_prompts')
        ]);

        creators = creatorsData.creators || [];
        fans = fansData.fans || [];
        systemPrompts = promptsData.system_prompts || [];

        renderCreators();
        renderFans();
        renderSystemPrompts();
    } catch (error) {
        showError('Failed to load data. Please check if the Flask server is running.');
        console.error(error);
    }
}

// Get sample data structure for creating new records
function getSampleData(type) {
    if (type === 'creator') {
        const sample = creators.length > 0 ? creators[0] : {};
        const baseData = {
            creator_name: '',
            niches: [],
            persona: [],
            nsfw: false,
            emojis_enabled: false
        };
        // Add any additional fields from existing records
        if (Object.keys(sample).length > 0) {
            Object.keys(sample).forEach(k => {
                if (k !== 'id' && k !== 'created_at' && k !== 'updated_at' && !baseData.hasOwnProperty(k)) {
                    const val = sample[k];
                    if (val === null || val === undefined) {
                        baseData[k] = '';
                    } else if (Array.isArray(val)) {
                        baseData[k] = [];
                    } else if (typeof val === 'boolean') {
                        baseData[k] = false;
                    } else if (typeof val === 'number') {
                        baseData[k] = 0;
                    } else {
                        baseData[k] = '';
                    }
                }
            });
        }
        return baseData;
    } else if (type === 'fan') {
        const sample = fans.length > 0 ? fans[0] : {};
        const baseData = {
            fan_name: '',
            lifetime_spend: 0
        };
        // Add any additional fields from existing records
        if (Object.keys(sample).length > 0) {
            Object.keys(sample).forEach(k => {
                if (k !== 'id' && k !== 'created_at' && k !== 'updated_at' && !baseData.hasOwnProperty(k)) {
                    const val = sample[k];
                    if (val === null || val === undefined) {
                        baseData[k] = '';
                    } else if (Array.isArray(val)) {
                        baseData[k] = [];
                    } else if (typeof val === 'boolean') {
                        baseData[k] = false;
                    } else if (typeof val === 'number') {
                        baseData[k] = 0;
                    } else {
                        baseData[k] = '';
                    }
                }
            });
        }
        return baseData;
    } else if (type === 'system_prompt') {
        const sample = systemPrompts.length > 0 ? systemPrompts[0] : {};
        const baseData = {
            system_prompt: ''
        };
        // Add any additional fields from existing records
        if (Object.keys(sample).length > 0) {
            Object.keys(sample).forEach(k => {
                if (k !== 'id' && k !== 'created_at' && k !== 'updated_at' && !baseData.hasOwnProperty(k)) {
                    const val = sample[k];
                    if (val === null || val === undefined) {
                        baseData[k] = '';
                    } else if (Array.isArray(val)) {
                        baseData[k] = [];
                    } else if (typeof val === 'boolean') {
                        baseData[k] = false;
                    } else if (typeof val === 'number') {
                        baseData[k] = 0;
                    } else {
                        baseData[k] = '';
                    }
                }
            });
        }
        return baseData;
    }
    return {};
}

// Show create modal
window.showCreateModal = function(type) {
    const modal = document.getElementById('details-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalActions = document.getElementById('modal-actions');

    const typeLabels = {
        'creator': 'Creator',
        'fan': 'Fan',
        'system_prompt': 'System Prompt'
    };

    modalTitle.textContent = `Create New ${typeLabels[type] || type}`;
    
    // Get sample data structure
    const sampleData = getSampleData(type);
    
    // Store create data
    window.currentEditData = { type: type, id: null, original: sampleData, isNew: true };

    // Render edit mode (which works for creating too)
    enterEditMode();
    modal.classList.add('active');
};

// Render creators
function renderCreators() {
    const container = document.getElementById('creator-content');
    if (creators.length === 0) {
        container.innerHTML = '<div class="empty-state">No creators found</div>';
        return;
    }

    container.innerHTML = '';
    creators.forEach(creator => {
        const isSelected = selectedCreator?.id === creator.id;
        const niches = Array.isArray(creator.niches) ? creator.niches.join(', ') : creator.niches || 'N/A';
        const persona = creator.persona ? (Array.isArray(creator.persona) ? creator.persona.join(', ') : creator.persona) : '';
        const name = creator.name || creator.creator_name || `Creator ${creator.id}`;

        const card = document.createElement('div');
        card.className = `item-card ${isSelected ? 'selected' : ''}`;
        card.onclick = () => window.selectCreator(creator.id);
        
        card.innerHTML = `
            <div class="item-card-header">
                <div class="item-name">${escapeHtml(name)}</div>
            </div>
            <div class="item-details">
                <span class="badge">Niche: ${escapeHtml(niches)}</span>
                ${persona ? `<span class="badge">Persona: ${escapeHtml(persona)}</span>` : ''}
            </div>
            <button class="view-details-btn" onclick="event.stopPropagation(); showCreatorDetails('${creator.id}')">
                📋 View Details
            </button>
        `;
        
        container.appendChild(card);
    });
}

// Render fans
function renderFans() {
    const container = document.getElementById('fan-content');
    if (fans.length === 0) {
        container.innerHTML = '<div class="empty-state">No fans found</div>';
        return;
    }

    container.innerHTML = '';
    fans.forEach(fan => {
        const isSelected = selectedFan?.id === fan.id;
        const name = fan.name || fan.fan_name || `Fan ${fan.id}`;
        // Convert to number and handle null/undefined/string values
        const lifetimeSpend = parseFloat(fan.lifetime_spend) || 0;

        const card = document.createElement('div');
        card.className = `item-card ${isSelected ? 'selected' : ''}`;
        card.onclick = () => window.selectFan(fan.id);
        
        card.innerHTML = `
            <div class="item-card-header">
                <div class="item-name">${escapeHtml(name)}</div>
            </div>
            <div class="item-details">
                <span class="badge highlight">Lifetime Spend: $${lifetimeSpend.toFixed(2)}</span>
            </div>
            <button class="view-details-btn" onclick="event.stopPropagation(); showFanDetails('${fan.id}')">
                📋 View Details
            </button>
        `;
        
        container.appendChild(card);
    });
}

// Render system prompts
function renderSystemPrompts() {
    const container = document.getElementById('system-prompt-content');
    if (systemPrompts.length === 0) {
        container.innerHTML = '<div class="empty-state">No system prompts found</div>';
        return;
    }

    container.innerHTML = '';
    systemPrompts.forEach(prompt => {
        const isSelected = selectedSystemPrompt?.id === prompt.id;
        const preview = prompt.system_prompt ? prompt.system_prompt.substring(0, 100) + '...' : 'No preview available';
        const shortId = prompt.id ? prompt.id.substring(0, 8) + '...' : 'Unknown';

        const card = document.createElement('div');
        card.className = `item-card ${isSelected ? 'selected' : ''}`;
        card.onclick = () => window.selectSystemPrompt(prompt.id);
        
        card.innerHTML = `
            <div class="item-card-header">
                <div class="item-name">Prompt ${escapeHtml(shortId)}</div>
            </div>
            <div class="item-details">
                <div class="prompt-preview">${escapeHtml(preview)}</div>
            </div>
            <button class="view-details-btn" onclick="event.stopPropagation(); showSystemPromptDetails('${prompt.id}')">
                📋 View Details
            </button>
        `;
        
        container.appendChild(card);
    });
}

// Selection functions - make them global so onclick handlers can access them
window.selectCreator = function(id) {
    selectedCreator = creators.find(c => c.id === id);
    renderCreators();
    updateGenerateButton();
    checkAndLoadChat();
};

window.selectFan = function(id) {
    selectedFan = fans.find(f => f.id === id);
    renderFans();
    updateGenerateButton();
    checkAndLoadChat();
};

window.selectSystemPrompt = function(id) {
    selectedSystemPrompt = systemPrompts.find(p => p.id === id);
    renderSystemPrompts();
    updateGenerateButton();
    
    // Enable chatbot input if creator and fan are already selected
    if (selectedCreator && selectedFan) {
        const input = document.getElementById('chatbot-input');
        const sendBtn = document.getElementById('chatbot-send-btn');
        input.disabled = false;
        sendBtn.disabled = false;
    }
};

// Update generate button state
function updateGenerateButton() {
    const btn = document.getElementById('generate-btn');
    const canGenerate = selectedCreator && selectedFan && selectedSystemPrompt;

    if (canGenerate) {
        btn.classList.remove('disabled');
        btn.classList.add('enabled');
        btn.disabled = false;
    } else {
        btn.classList.remove('enabled');
        btn.classList.add('disabled');
        btn.disabled = true;
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = `⚠️ ${message}`;
    errorDiv.style.display = 'block';
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}

// Generate recommendations - calls the recommended_chats API
async function generateRecommendations() {
    if (!selectedCreator || !selectedFan || !selectedSystemPrompt) {
        showError('Please select a creator, fan, and system prompt');
        return;
    }

    const btn = document.getElementById('generate-btn');
    btn.disabled = true;
    btn.textContent = 'Generating...';

    const errorDiv = document.getElementById('error-message');
    errorDiv.style.display = 'none';

    const recommendationsDiv = document.getElementById('recommendations-container');
    recommendationsDiv.style.display = 'none';

    try {
        // Call the recommended_chats API endpoint
        const response = await fetchData('/recommended_chats', {
            method: 'POST',
            body: JSON.stringify({
                creator_id: selectedCreator.id,
                fan_id: selectedFan.id,
                system_prompt_id: selectedSystemPrompt.id,
                chat_type: 'text'
            }),
        });

        // Check for error in response first
        if (response.error) {
            throw new Error(response.error);
        }

        // Validate recommendations before displaying
        if (response.recommendations && Array.isArray(response.recommendations) && response.recommendations.length > 0) {
            // Filter out any recommendations that look like error messages
            const validRecommendations = response.recommendations.filter(rec => {
                const content = rec.content || '';
                // Check if content looks like an error message (contains "Recommended reply" with persona/niches info)
                if (content.includes('Recommended reply') && (content.includes('based on persona:') || content.includes('based on persona'))) {
                    return false; // This is likely an error placeholder, not a real recommendation
                }
                return true;
            });
            
            if (validRecommendations.length > 0) {
                renderRecommendations(validRecommendations);
            } else {
                throw new Error('No valid recommendations generated. The AI service may be experiencing issues. Please try again.');
            }
        } else {
            throw new Error('No recommendations received from server.');
        }
    } catch (error) {
        showError(error.message || 'Failed to generate recommendations');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.textContent = '✨ Generate Recommendations';
        updateGenerateButton();
    }
}

// Render recommendations
function renderRecommendations(recommendations) {
    const container = document.getElementById('recommendations-container');
    container.style.display = 'block';

    container.innerHTML = `
        <div class="recommendations-container">
            <div class="recommendations-header">
                <h2>💬 Generated Recommendations</h2>
                <p>${recommendations.length} reply options</p>
            </div>
            <div class="recommendations-grid">
                ${recommendations.map((rec, index) => {
                    const confidence = rec.confidence ? (rec.confidence * 100).toFixed(0) : 'N/A';
                    const chatType = rec.chat_type || 'text';
                    const content = escapeHtml(rec.content || 'No content');
                    return `
                        <div class="recommendation-card">
                            <div class="recommendation-number">#${index + 1}</div>
                            <div class="recommendation-content">${content}</div>
                            <div class="recommendation-footer">
                                <span class="confidence-badge">Confidence: ${confidence}%</span>
                                <span class="chat-type-badge">${chatType}</span>
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;

    // Scroll to recommendations
    container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Format value for display
function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'boolean') return value ? 'Yes' : 'No';
    if (Array.isArray(value)) return value.join(', ');
    if (typeof value === 'object') return JSON.stringify(value, null, 2);
    return String(value);
}

// Show creator details modal
window.showCreatorDetails = function(creatorId) {
    const creator = creators.find(c => c.id === creatorId);
    if (!creator) return;

    const modal = document.getElementById('details-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalActions = document.getElementById('modal-actions');

    const name = creator.name || creator.creator_name || `Creator ${creator.id}`;
    modalTitle.textContent = `Creator: ${escapeHtml(name)}`;

    // Store original data for editing
    window.currentEditData = { type: 'creator', id: creatorId, original: creator };

    renderDetailsView(creator, modalBody, modalActions);
    modal.classList.add('active');
};

// Show fan details modal
window.showFanDetails = function(fanId) {
    const fan = fans.find(f => f.id === fanId);
    if (!fan) return;

    const modal = document.getElementById('details-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalActions = document.getElementById('modal-actions');

    const name = fan.name || fan.fan_name || `Fan ${fan.id}`;
    modalTitle.textContent = `Fan: ${escapeHtml(name)}`;

    // Store original data for editing
    window.currentEditData = { type: 'fan', id: fanId, original: fan };

    renderDetailsView(fan, modalBody, modalActions);
    modal.classList.add('active');
};

// Show system prompt details modal
window.showSystemPromptDetails = function(promptId) {
    const prompt = systemPrompts.find(p => p.id === promptId);
    if (!prompt) return;

    const modal = document.getElementById('details-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalBody = document.getElementById('modal-body');
    const modalActions = document.getElementById('modal-actions');

    modalTitle.textContent = `System Prompt Details`;

    // Store original data for editing
    window.currentEditData = { type: 'system_prompt', id: promptId, original: prompt };

    renderDetailsView(prompt, modalBody, modalActions);
    modal.classList.add('active');
};

// Render details view (read-only)
function renderDetailsView(data, modalBody, modalActions) {
    let html = '';
    for (const [key, value] of Object.entries(data)) {
        if (key === 'id') continue;
        const formattedValue = formatValue(value);
        const isLongText = key === 'system_prompt' && formattedValue.length > 100;
        
        html += `
            <div class="detail-row" data-field="${key}">
                <div class="detail-label">${escapeHtml(key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))}</div>
                <div class="detail-value">
                    ${isLongText ? `<pre>${escapeHtml(formattedValue)}</pre>` : escapeHtml(formattedValue)}
                </div>
            </div>
        `;
    }

    modalBody.innerHTML = html;
    modalActions.innerHTML = `<button class="edit-btn" onclick="enterEditMode()">✏️ Edit</button>`;
    modalActions.style.display = 'flex';
}

// Enter edit mode
window.enterEditMode = function() {
    if (!window.currentEditData) return;

    const modalBody = document.getElementById('modal-body');
    const modalActions = document.getElementById('modal-actions');
    const data = window.currentEditData.original;

    let html = '';
    for (const [key, value] of Object.entries(data)) {
        if (key === 'id' || key === 'created_at' || key === 'updated_at') continue;
        const fieldName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += createEditField(key, value, fieldName);
    }

    modalBody.innerHTML = html;
    const isNew = window.currentEditData.isNew;
    modalActions.innerHTML = `
        <button class="save-btn" onclick="saveChanges()">💾 ${isNew ? 'Create' : 'Save'}</button>
        <button class="cancel-btn" onclick="${isNew ? 'closeDetailsModal()' : 'cancelEdit()'}">❌ Cancel</button>
    `;
    modalActions.style.display = 'flex';
};

// Create edit field based on value type
function createEditField(key, value, label) {
    if (value === null || value === undefined) {
        return `
            <div class="detail-row" data-field="${key}">
                <div class="detail-label">${escapeHtml(label)}</div>
                <div class="detail-value">
                    <input type="text" name="${key}" value="" placeholder="Enter value">
                </div>
            </div>
        `;
    }

    if (typeof value === 'boolean') {
        return `
            <div class="detail-row" data-field="${key}">
                <div class="detail-label">${escapeHtml(label)}</div>
                <div class="detail-value">
                    <div class="checkbox-wrapper">
                        <input type="checkbox" name="${key}" ${value ? 'checked' : ''}>
                        <span>${value ? 'Yes' : 'No'}</span>
                    </div>
                </div>
            </div>
        `;
    }

    if (Array.isArray(value)) {
        const itemsHtml = value.map((item, index) => `
            <div class="array-item">
                <input type="text" name="${key}[]" value="${escapeHtml(String(item))}" data-index="${index}">
                <button type="button" class="remove-array-item" onclick="removeArrayItem(this)">Remove</button>
            </div>
        `).join('');
        
        return `
            <div class="detail-row" data-field="${key}">
                <div class="detail-label">${escapeHtml(label)}</div>
                <div class="detail-value">
                    <div class="array-input">
                        ${itemsHtml}
                        <button type="button" class="add-array-item" onclick="addArrayItem('${key}')">+ Add Item</button>
                    </div>
                </div>
            </div>
        `;
    }

    if (typeof value === 'object') {
        const jsonValue = JSON.stringify(value, null, 2);
        return `
            <div class="detail-row" data-field="${key}">
                <div class="detail-label">${escapeHtml(label)}</div>
                <div class="detail-value">
                    <textarea name="${key}" rows="6">${escapeHtml(jsonValue)}</textarea>
                </div>
            </div>
        `;
    }

    // String or number - use textarea for long text, input for short
    const isLongText = String(value).length > 100 || key === 'system_prompt';
    if (isLongText) {
        return `
            <div class="detail-row" data-field="${key}">
                <div class="detail-label">${escapeHtml(label)}</div>
                <div class="detail-value">
                    <textarea name="${key}" rows="8">${escapeHtml(String(value))}</textarea>
                </div>
            </div>
        `;
    }

    return `
        <div class="detail-row" data-field="${key}">
            <div class="detail-label">${escapeHtml(label)}</div>
            <div class="detail-value">
                <input type="text" name="${key}" value="${escapeHtml(String(value))}">
            </div>
        </div>
    `;
}

// Add array item
window.addArrayItem = function(fieldName) {
    const fieldRow = document.querySelector(`[data-field="${fieldName}"]`);
    const arrayInput = fieldRow.querySelector('.array-input');
    const newItem = document.createElement('div');
    newItem.className = 'array-item';
    newItem.innerHTML = `
        <input type="text" name="${fieldName}[]" value="" data-index="${Date.now()}">
        <button type="button" class="remove-array-item" onclick="removeArrayItem(this)">Remove</button>
    `;
    const addButton = arrayInput.querySelector('.add-array-item');
    arrayInput.insertBefore(newItem, addButton);
};

// Remove array item
window.removeArrayItem = function(button) {
    button.closest('.array-item').remove();
};

// Cancel edit
window.cancelEdit = function() {
    if (!window.currentEditData) return;
    
    // If it's a new record, close the modal. Otherwise, go back to view mode.
    if (window.currentEditData.isNew) {
        closeDetailsModal();
        return;
    }
    
    const modalBody = document.getElementById('modal-body');
    const modalActions = document.getElementById('modal-actions');
    
    renderDetailsView(window.currentEditData.original, modalBody, modalActions);
};

// Save changes
window.saveChanges = async function() {
    if (!window.currentEditData) return;

    const modalBody = document.getElementById('modal-body');
    const saveBtn = modalBody.closest('.modal-content').querySelector('.save-btn');
    saveBtn.disabled = true;
    const isNew = window.currentEditData.isNew;
    saveBtn.textContent = isNew ? '💾 Creating...' : '💾 Saving...';

    try {
        const inputs = modalBody.querySelectorAll('input, textarea, select');
        const updateData = { id: window.currentEditData.id };
        
        // First, collect array fields
        const arrayFields = {};
        inputs.forEach(input => {
            if (input.name.endsWith('[]')) {
                const fieldName = input.name.replace('[]', '');
                if (!arrayFields[fieldName]) {
                    arrayFields[fieldName] = [];
                }
                const trimmedValue = input.value.trim();
                if (trimmedValue) {
                    arrayFields[fieldName].push(trimmedValue);
                }
            }
        });
        
        // Add array fields to updateData
        for (const [key, value] of Object.entries(arrayFields)) {
            updateData[key] = value;
        }
        
        // Then handle non-array fields
        inputs.forEach(input => {
            if (input.name.endsWith('[]')) return; // Skip array inputs, already handled
            
            const key = input.name;
            let value;
            
            if (input.type === 'checkbox') {
                value = input.checked;
            } else {
                value = input.value;
            }
            
            // Try to parse as number if it looks like one
            if (typeof value === 'string' && value !== '' && !isNaN(value) && value.trim() !== '') {
                const numValue = parseFloat(value);
                if (!isNaN(numValue)) {
                    value = numValue;
                }
            }
            
            // Try to parse as JSON if it looks like JSON
            if (typeof value === 'string' && (value.startsWith('[') || value.startsWith('{'))) {
                try {
                    value = JSON.parse(value);
                } catch {
                    // Keep as string if parsing fails
                }
            }
            
            updateData[key] = value;
        });

        // Determine endpoint and method
        let endpoint = '';
        let method = 'PUT';
        
        if (window.currentEditData.isNew) {
            // Creating new record
            method = 'POST';
            if (window.currentEditData.type === 'creator') {
                endpoint = '/create_creator';
            } else if (window.currentEditData.type === 'fan') {
                endpoint = '/create_fan';
            } else if (window.currentEditData.type === 'system_prompt') {
                endpoint = '/create_system_prompt';
            }
            // Remove id from create data
            delete updateData.id;
        } else {
            // Updating existing record
            if (window.currentEditData.type === 'creator') {
                endpoint = '/update_creator';
            } else if (window.currentEditData.type === 'fan') {
                endpoint = '/update_fan';
            } else if (window.currentEditData.type === 'system_prompt') {
                endpoint = '/update_system_prompt';
            }
        }

        const response = await fetchData(endpoint, {
            method: method,
            body: JSON.stringify(updateData)
        });

        if (response.success) {
            const newRecord = response[window.currentEditData.type] || response.creator || response.fan || response.system_prompt;
            
            if (window.currentEditData.isNew) {
                // Add new record to local data
                if (window.currentEditData.type === 'creator') {
                    creators.push(newRecord);
                    renderCreators();
                } else if (window.currentEditData.type === 'fan') {
                    fans.push(newRecord);
                    renderFans();
                } else if (window.currentEditData.type === 'system_prompt') {
                    systemPrompts.push(newRecord);
                    renderSystemPrompts();
                }
                
                // Show success and close modal
                alert('✅ ' + (response.message || 'Created successfully'));
                closeDetailsModal();
            } else {
                // Update existing record in local data
                if (window.currentEditData.type === 'creator') {
                    const index = creators.findIndex(c => c.id === window.currentEditData.id);
                    if (index !== -1) {
                        creators[index] = newRecord;
                        renderCreators();
                    }
                } else if (window.currentEditData.type === 'fan') {
                    const index = fans.findIndex(f => f.id === window.currentEditData.id);
                    if (index !== -1) {
                        fans[index] = newRecord;
                        renderFans();
                    }
                } else if (window.currentEditData.type === 'system_prompt') {
                    const index = systemPrompts.findIndex(p => p.id === window.currentEditData.id);
                    if (index !== -1) {
                        systemPrompts[index] = newRecord;
                        renderSystemPrompts();
                    }
                }

                // Update current edit data
                window.currentEditData.original = newRecord;
                
                // Show success and refresh view
                alert('✅ ' + (response.message || 'Updated successfully'));
                cancelEdit();
            }
        }
    } catch (error) {
        alert('❌ Error: ' + (error.message || 'Failed to update'));
        console.error('Update error:', error);
    } finally {
        saveBtn.disabled = false;
        const isNew = window.currentEditData?.isNew;
        saveBtn.textContent = isNew ? '💾 Create' : '💾 Save';
    }
};

// Close details modal
window.closeDetailsModal = function() {
    const modal = document.getElementById('details-modal');
    modal.classList.remove('active');
    window.currentEditData = null;
};

// Setup modal close handlers (will be called in main DOMContentLoaded)
function setupModalHandlers() {
    const modal = document.getElementById('details-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeDetailsModal();
            }
        });

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                closeDetailsModal();
            }
        });
    }
}

// Load chat history
async function loadChatHistory() {
    if (!selectedCreator || !selectedFan) {
        return;
    }

    try {
        const response = await fetchData(`/get_chat_history?creator_id=${selectedCreator.id}&fan_id=${selectedFan.id}`);
        chatMessages = response.messages || [];
        renderChatMessages();
    } catch (error) {
        console.error('Error loading chat history:', error);
        chatMessages = [];
        renderChatMessages();
    }
}

// Check if both creator and fan are selected, then load chat
function checkAndLoadChat() {
    const chatbotContainer = document.getElementById('chatbot-container');
    
    if (selectedCreator && selectedFan) {
        chatbotContainer.classList.add('active');
        
        const input = document.getElementById('chatbot-input');
        const sendBtn = document.getElementById('chatbot-send-btn');
        
        if (selectedSystemPrompt) {
            input.disabled = false;
            sendBtn.disabled = false;
        } else {
            input.disabled = true;
            sendBtn.disabled = true;
        }
        
        loadChatHistory();
    } else {
        // Keep chatbot visible but show message that selections are needed
        chatbotContainer.classList.add('active');
        const messagesContainer = document.getElementById('chatbot-messages');
        if (messagesContainer && !messagesContainer.querySelector('.message')) {
            messagesContainer.innerHTML = '<div class="empty-state">Select a creator and fan to start chatting</div>';
        }
    }
}

// Render chat messages
function renderChatMessages() {
    const container = document.getElementById('chatbot-messages');
    
    if (chatMessages.length === 0) {
        container.innerHTML = '<div class="empty-state">No messages yet. Start the conversation!</div>';
        // Still show pending recommendations if any
        if (pendingRecommendations && pendingRecommendations.length > 0) {
            renderPendingRecommendations();
        }
        return;
    }
    
    container.innerHTML = chatMessages.map(msg => {
        const sender = msg.sender || 'fan';
        const content = escapeHtml(msg.content || '');
        const time = msg.created_at ? new Date(msg.created_at).toLocaleTimeString() : '';
        
        return `
            <div class="message ${sender}">
                <div>
                    <div class="message-content">${content}</div>
                    ${time ? `<div class="message-time">${time}</div>` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // Show pending recommendations if any (after messages)
    if (pendingRecommendations && pendingRecommendations.length > 0) {
        renderPendingRecommendations();
    }
    
    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

// Show loading indicator
function showLoadingIndicator(message = 'Thinking...') {
    const container = document.getElementById('chatbot-messages');
    const loadingHtml = `
        <div class="message loading" id="loading-indicator">
            <div class="message-content">
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', loadingHtml);
    container.scrollTop = container.scrollHeight;
}

// Hide loading indicator
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// Render pending recommendations in chat
function renderPendingRecommendations() {
    const container = document.getElementById('chatbot-messages');
    
    const recommendationsHtml = `
        <div class="recommendations-pending">
            <h3>✨ AI Recommendations</h3>
            <p>Select a reply to send:</p>
            <div class="recommendation-options">
                ${pendingRecommendations.map((rec, index) => {
                    const content = escapeHtml(rec.content || '');
                    return `
                        <div class="recommendation-option" onclick="selectRecommendation(${index})">
                            ${content}
                        </div>
                    `;
                }).join('')}
            </div>
        </div>
    `;
    
    container.insertAdjacentHTML('beforeend', recommendationsHtml);
    container.scrollTop = container.scrollHeight;
}

// Handle fan sending a message
async function sendFanMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (!message || !selectedCreator || !selectedFan) {
        return;
    }
    
    // Disable input while sending
    input.disabled = true;
    const sendBtn = document.getElementById('chatbot-send-btn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    
    try {
        // Send fan message to database
        await fetchData('/send_fan_message', {
            method: 'POST',
            body: JSON.stringify({
                fan_id: selectedFan.id,
                creator_id: selectedCreator.id,
                content: message
            })
        });
        
        // Clear input
        input.value = '';
        
        // Reload chat history to show the new message
        await loadChatHistory();
        
        // Clear any existing pending recommendations
        pendingRecommendations = null;
        
        // Generate recommendations
        if (selectedSystemPrompt) {
            showLoadingIndicator('Generating recommendations...');
            try {
                await generateChatRecommendations();
            } finally {
                hideLoadingIndicator();
            }
        }
    } catch (error) {
        showError(error.message || 'Failed to send message');
        console.error(error);
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
}

// Show error message in chat window
function showChatError(message) {
    const container = document.getElementById('chatbot-messages');
    const errorHtml = `
        <div class="message error-message">
            <div>
                <div class="message-content error-content">⚠️ ${escapeHtml(message)}</div>
                <div class="message-time">${new Date().toLocaleTimeString()}</div>
            </div>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', errorHtml);
    container.scrollTop = container.scrollHeight;
}

// Generate chat recommendations
async function generateChatRecommendations() {
    if (!selectedCreator || !selectedFan || !selectedSystemPrompt) {
        return;
    }
    
    try {
        const response = await fetchData('/recommended_chats', {
            method: 'POST',
            body: JSON.stringify({
                creator_id: selectedCreator.id,
                fan_id: selectedFan.id,
                system_prompt_id: selectedSystemPrompt.id,
                chat_type: 'text'
            })
        });
        
        // Check for error in response first
        if (response.error) {
            throw new Error(response.error);
        }
        
        // Validate recommendations before displaying
        if (response.recommendations && Array.isArray(response.recommendations) && response.recommendations.length > 0) {
            // Filter out any recommendations that look like error messages
            const validRecommendations = response.recommendations.filter(rec => {
                const content = rec.content || '';
                // Check if content looks like an error message (contains "Recommended reply" with persona/niches info)
                if (content.includes('Recommended reply') && (content.includes('based on persona:') || content.includes('based on persona'))) {
                    return false; // This is likely an error placeholder, not a real recommendation
                }
                return true;
            });
            
            if (validRecommendations.length > 0) {
                pendingRecommendations = validRecommendations;
                renderPendingRecommendations();
            } else {
                throw new Error('No valid recommendations generated. Please try again.');
            }
        } else {
            throw new Error('No recommendations received from server.');
        }
    } catch (error) {
        console.error('Error generating recommendations:', error);
        hideLoadingIndicator();
        
        // Extract error message - handle both API errors and general errors
        let errorMessage = error.message || 'Failed to generate recommendations. Please try again.';
        
        // If it's an API error, try to extract a more user-friendly message
        if (errorMessage.includes('Internal server error:')) {
            // Extract the actual error message after "Internal server error:"
            const match = errorMessage.match(/Internal server error:\s*(.+)/);
            if (match && match[1]) {
                errorMessage = match[1];
            }
        }
        
        // Parse Mistral API errors for better user messages
        if (errorMessage.includes('Mistral API error:')) {
            // Try to extract JSON error message if present
            const jsonMatch = errorMessage.match(/"message"\s*:\s*"([^"]+)"/);
            if (jsonMatch && jsonMatch[1]) {
                errorMessage = jsonMatch[1];
            } else if (errorMessage.includes('Status 429')) {
                errorMessage = 'Service capacity exceeded. Please try again in a moment.';
            } else if (errorMessage.includes('Status 401')) {
                errorMessage = 'API authentication failed. Please check your API key.';
            } else if (errorMessage.includes('Status 500')) {
                errorMessage = 'AI service error. Please try again later.';
            }
        }
        
        // Show error in chat window
        showChatError(errorMessage);
        
        // Also show in error message div for visibility
        showError(errorMessage);
    }
}

// Handle creator selecting a recommendation
window.selectRecommendation = async function(index) {
    if (!pendingRecommendations || !pendingRecommendations[index]) {
        return;
    }
    
    const selectedRec = pendingRecommendations[index];
    const sendBtn = document.getElementById('chatbot-send-btn');
    sendBtn.disabled = true;
    sendBtn.textContent = 'Sending...';
    
    // Remove the recommendations UI and show loading
    const container = document.getElementById('chatbot-messages');
    const recommendationsDiv = container.querySelector('.recommendations-pending');
    if (recommendationsDiv) {
        recommendationsDiv.remove();
    }
    
    showLoadingIndicator('Sending reply...');
    
    try {
        // Store selected reply
        await fetchData('/chatter_selected_chat_reply', {
            method: 'POST',
            body: JSON.stringify({
                fan_id: selectedFan.id,
                creator_id: selectedCreator.id,
                reply_content: selectedRec.content,
                reply_id: selectedRec.reply_id,
                chat_type: 'text'
            })
        });
        
        // Clear pending recommendations
        pendingRecommendations = null;
        
        // Hide loading and reload chat history to show the new message
        hideLoadingIndicator();
        await loadChatHistory();
    } catch (error) {
        hideLoadingIndicator();
        showError(error.message || 'Failed to send reply');
        console.error(error);
    } finally {
        sendBtn.disabled = false;
        sendBtn.textContent = 'Send';
    }
};

// Handle logout
async function handleLogout() {
    try {
        await fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        // Clear API key and redirect to login
        localStorage.removeItem('api_key');
        window.location.href = '/login';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Check if API key exists, if not redirect to login
    if (!getApiKey()) {
        window.location.href = '/login';
        return;
    }

    // Setup modal handlers
    setupModalHandlers();

    // Event listeners
    document.getElementById('generate-btn').addEventListener('click', generateRecommendations);
    
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            handleLogout();
        });
    }
    
    const chatbotInput = document.getElementById('chatbot-input');
    const chatbotSendBtn = document.getElementById('chatbot-send-btn');
    
    chatbotSendBtn.addEventListener('click', sendFanMessage);
    
    chatbotInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendFanMessage();
        }
    });

    // Load data on page load
    loadData();
});

