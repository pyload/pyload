{% autoescape true %}

// API Keys Management (Modal-based)
$(document).ready(function() {
    // Inject Manage API Keys button into Users tab header/actions if not present
    const usersTab = $('#users');
    if (usersTab.length && $('#open-api-keys-modal-btn').length === 0) {
        const header = usersTab.find('h3, h2').first();
        const actionsContainer = header.length ? header : usersTab;
        const openBtn = $(`
            <button type="button" class="btn btn-default pull-right" id="open-api-keys-modal-btn" style="margin-left:8px;">
                <span class="glyphicon glyphicon-lock"></span> Manage API Keys
            </button>
        `);
        actionsContainer.append(openBtn);
    }

    // Create API Keys Modal (Bootstrap) if it doesn't exist
    if ($('#apiKeysModal').length === 0) {
        const modalHtml = $(`
            <div class="modal fade" id="apiKeysModal" tabindex="-1" role="dialog" aria-labelledby="apiKeysModalLabel">
              <div class="modal-dialog" role="document">
                <div class="modal-content">
                  <div class="modal-header">
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                    <h4 class="modal-title" id="apiKeysModalLabel">API Keys</h4>
                  </div>
                  <div class="modal-body">
                    <p>Manage your API keys for programmatic access to pyLoad.</p>
                    <table class="table table-striped" id="api-keys-table">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Created</th>
                          <th>Valid Until</th>
                          <th>Last Used</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody id="api-keys-tbody">
                        <tr><td colspan="4" class="text-center">Loading...</td></tr>
                      </tbody>
                    </table>
                  </div>
                  <div class="modal-footer">
                    <button type="button" class="btn btn-primary" id="generate-api-key-btn">
                      <span class="glyphicon glyphicon-plus"></span> Generate New Key
                    </button>
                    <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                  </div>
                </div>
              </div>
            </div>
        `);
        $('body').append(modalHtml);
    }

    // Open modal from Users tab button
    $(document).on('click', '#open-api-keys-modal-btn', function() {
        $('#apiKeysModal').modal('show');
        loadApiKeys();
    });

    // Also refresh keys whenever modal is shown manually
    $('#apiKeysModal').on('shown.bs.modal', function () {
        loadApiKeys();
    });

    // Generate new API key button inside modal
    $(document).on('click', '#generate-api-key-btn', function() {
        showGenerateKeyPrompt();
    });

    // Delete API key button inside modal
    $(document).on('click', '.delete-key-btn', function() {
        const keyId = $(this).data('key-id');
        if (confirm('Are you sure you want to delete this API key?')) {
            deleteApiKey(keyId);
        }
    });
});

function loadApiKeys() {
    $.ajax({
        url: '/api/get_apikeys',
        type: 'GET',
        dataType: 'json',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        success: function(data) {
            const tbody = $('#apikeys_table');

            if (!tbody.length) return; // Modal not present yet

            if (data.error) {
                tbody.html('<tr><td colspan="4" class="text-danger">Error loading API keys</td></tr>');
                return;
            }

            if (!data || data.length === 0) {
                tbody.html('<tr><td colspan="4" class="text-center">No API keys yet</td></tr>');
                return;
            }

            let html = '';
            $.each(data, function(index, key) {
                const createdDate = new Date(key.created_at).toLocaleString();
                const lastUsedDate = key.last_used ? new Date(key.last_used).toLocaleString() : 'Never';
                html += `
                    <tr>
                        <td>${escapeHtml(key.name)}</td>
                        <td>${createdDate}</td>
                        <td>${lastUsedDate}</td>
                        <td>
                            <button class="btn btn-sm btn-danger delete-key-btn" data-key-id="${key.id}">
                                <span class="glyphicon glyphicon-trash"></span> Delete
                            </button>
                        </td>
                    </tr>
                `;
            });
            tbody.html(html);
        },
        error: function(error) {
            console.error('Error loading API keys:', error);
            const tbody = $('#api-keys-tbody');
            if (tbody.length) {
                tbody.html('<tr><td colspan="4" class="text-danger">Error loading API keys</td></tr>');
            }
        }
    });
}

function showGenerateKeyPrompt() {
    const keyName = prompt('Enter a name for this API key:', 'My API Key');
    if (keyName === null) return;

    if (keyName.trim() === '') {
        alert('Please enter a name for the API key');
        return;
    }

    generateApiKey(keyName);
}

function generateApiKey(name) {
    $.ajax({
        url: '/api/generate_api_key',
        type: 'POST',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({ name: name }),
        success: function(data) {
            if (data.error) {
                alert('Error generating API key: ' + data.error);
                return;
            }

            // Show the generated key
            const keyValue = data.key;
            const message = `API Key generated successfully!\n\nKey: ${keyValue}\n\nPlease save this key in a secure location. You won't be able to see it again!\n\nUsage:\nAdd the header: X-API-Key: ${keyValue}`;
            alert(message);

            // Reload the keys list inside modal
            loadApiKeys();
        },
        error: function(error) {
            console.error('Error generating API key:', error);
            alert('Error generating API key');
        }
    });
}

function deleteApiKey(keyId) {
    $.ajax({
        url: '/api/delete_api_key',
        type: 'DELETE',
        dataType: 'json',
        contentType: 'application/json',
        data: JSON.stringify({ key_id: keyId }),
        success: function(data) {
            if (data.error) {
                alert('Error deleting API key: ' + data.error);
                return;
            }

            alert('API key deleted successfully');
            loadApiKeys();
        },
        error: function(error) {
            console.error('Error deleting API key:', error);
            alert('Error deleting API key');
        }
    });
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

{% endautoescape %}
