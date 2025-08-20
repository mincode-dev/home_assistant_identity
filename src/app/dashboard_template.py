"""
Dashboard HTML template for the ICP Identity Manager.
This module contains the new dashboard with canister management functionality.
"""

def generate_dashboard_html(identity_info, stats, backups, canisters, actor_principal):
    """Generate the complete dashboard HTML."""
    
    # Generate canister HTML
    canister_html = ""
    if canisters:
        for canister in canisters:
            canister_id = canister["id"]
            canister_name = canister.get("name", canister_id[:8])
            methods = canister.get("methods", [])
            last_used = canister.get("last_used", "Never")
            
            method_buttons = ""
            for method in methods:
                method_buttons += f'<button class="button method-btn" onclick="callMethod(\'{canister_id}\', \'{method}\')">{method}</button>'
            
            if not method_buttons:
                method_buttons = '<p class="no-methods">No methods available</p>'
            
            canister_html += f"""
            <div class="canister-card">
                <h4>🔗 {canister_name}</h4>
                <p><code>{canister_id}</code></p>
                <small>Last used: {last_used[:19].replace('T', ' ') if last_used != 'Never' else 'Never'}</small>
                <div class="method-buttons">
                    {method_buttons}
                </div>
                <button class="button danger small" onclick="removeCanister('{canister_id}')">Remove</button>
            </div>
            """
    else:
        canister_html = "<p class='no-canisters'>No canisters registered. Add one below! 🚀</p>"
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ICP Identity Manager</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; color: white; margin-bottom: 30px; }}
            .header h1 {{ margin: 0; font-size: 2.5em; text-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
            .header p {{ margin: 10px 0; opacity: 0.9; font-size: 1.1em; }}
            .info-box {{ background: white; padding: 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .button {{ background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; margin: 8px; font-weight: 500; transition: all 0.2s; display: inline-block; text-decoration: none; }}
            .button:hover {{ background: #0056b3; transform: translateY(-1px); }}
            .button.danger {{ background: #dc3545; }}
            .button.danger:hover {{ background: #c82333; }}
            .button.success {{ background: #28a745; }}
            .button.success:hover {{ background: #218838; }}
            .button.small {{ padding: 8px 16px; font-size: 12px; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin: 25px 0; }}
            .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; text-align: center; }}
            .stat-card h4 {{ margin: 0 0 10px 0; font-size: 14px; opacity: 0.9; }}
            .stat-card p {{ margin: 0; font-size: 24px; font-weight: bold; }}
            .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }}
            .status-connected {{ background: #d4edda; color: #155724; }}
            code {{ background: #f8f9fa; padding: 4px 8px; border-radius: 4px; font-family: 'Monaco', 'Consolas', monospace; font-size: 13px; }}
            .network-info {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 15px; border-radius: 8px; margin: 15px 0; }}
            .canister-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
            .canister-card {{ background: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 4px solid #007bff; }}
            .canister-card h4 {{ margin: 0 0 10px 0; color: #333; }}
            .canister-card small {{ color: #6c757d; display: block; margin-bottom: 10px; }}
            .method-buttons {{ margin: 15px 0; }}
            .method-btn {{ background: #6c757d; margin: 4px; padding: 8px 12px; font-size: 12px; }}
            .method-btn:hover {{ background: #5a6268; }}
            .no-methods {{ color: #6c757d; font-style: italic; margin: 10px 0; }}
            .no-canisters {{ text-align: center; color: #6c757d; font-size: 18px; margin: 40px 0; }}
            .add-canister-form {{ background: #e9ecef; padding: 20px; border-radius: 12px; margin: 20px 0; }}
            .form-group {{ margin: 15px 0; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            .form-group input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; box-sizing: border-box; }}
            .principal-info {{ background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%); color: white; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; }}
            .loading {{ opacity: 0.6; pointer-events: none; }}
            .result-box {{ margin: 10px 0; padding: 10px; border-radius: 6px; font-family: monospace; font-size: 12px; }}
            .result-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
            .result-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏠 ICP Identity Manager</h1>
                <p>Home Assistant Internet Computer Protocol Integration</p>
                <div class="status-badge status-connected">Connected</div>
            </div>
            
            <div class="info-box">
                <h3>Identity Information</h3>
                <p><strong>Principal:</strong> <code>{identity_info['principal']}</code></p>
                <p><strong>Public Key:</strong> <code>{identity_info['public_key'][:32]}...</code></p>
                <div class="network-info">
                    <strong>Network:</strong> {identity_info['network'].upper()} 
                    <small>({identity_info.get('agent_url', 'N/A')})</small>
                </div>
                {f'<div class="principal-info"><strong>Actor Principal:</strong> <code>{actor_principal}</code></div>' if actor_principal else ''}
            </div>
            
            <div class="info-box">
                <h3>🔗 Canister Management</h3>
                <div class="canister-grid">
                    {canister_html}
                </div>
                
                <div class="add-canister-form">
                    <h4>➕ Add New Canister</h4>
                    <div class="form-group">
                        <label for="canisterId">Canister ID:</label>
                        <input type="text" id="canisterId" placeholder="3y3bg-2qaaa-aaaaj-azroa-cai" value="3y3bg-2qaaa-aaaaj-azroa-cai">
                    </div>
                    <div class="form-group">
                        <label for="canisterName">Name (optional):</label>
                        <input type="text" id="canisterName" placeholder="M_AUTONOME">
                    </div>
                    <button class="button success" onclick="addCanister()">🚀 Add Canister</button>
                    <div id="addResult"></div>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <h4>Registered Canisters</h4>
                    <p>{len(canisters)}</p>
                </div>
                <div class="stat-card">
                    <h4>Backup Files</h4>
                    <p>{stats['backup_count']}</p>
                </div>
                <div class="stat-card">
                    <h4>Data Size</h4>
                    <p>{stats['data_size_mb']:.1f} MB</p>
                </div>
                <div class="stat-card">
                    <h4>Mnemonic Status</h4>
                    <p>{'✅ Stored' if identity_info['has_mnemonic'] else '❌ Missing'}</p>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <button class="button" onclick="createBackup()">📦 Create Backup</button>
                <button class="button" onclick="window.open('/stats', '_blank')">📊 View Stats</button>
                <button class="button danger" onclick="regenerateIdentity()">🔄 Regenerate Identity</button>
            </div>
            
            <div class="info-box">
                <h3>Recent Backups</h3>
                {'<p>No backups available</p>' if not backups else ''.join([f'<p>📁 {backup["created_at"][:19].replace("T", " ")}</p>' for backup in backups[:5]])}
            </div>
        </div>
        
        <script>
            async function addCanister() {{
                const canisterId = document.getElementById('canisterId').value.trim();
                const canisterName = document.getElementById('canisterName').value.trim();
                const resultDiv = document.getElementById('addResult');
                
                if (!canisterId) {{
                    resultDiv.innerHTML = '<div class="result-box result-error">Please enter a canister ID</div>';
                    return;
                }}
                
                resultDiv.innerHTML = '<div class="result-box">Adding canister...</div>';
                
                try {{
                    const response = await fetch('/canisters/add', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            canister_id: canisterId,
                            name: canisterName || undefined,
                            network: 'mainnet'
                        }})
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.innerHTML = `<div class="result-box result-success">✅ ${{result.message}}<br>Authenticated: ${{result.authenticated ? 'Yes' : 'No'}}</div>`;
                        setTimeout(() => location.reload(), 2000);
                    }} else {{
                        resultDiv.innerHTML = `<div class="result-box result-error">❌ ${{result.error}}</div>`;
                    }}
                }} catch (error) {{
                    resultDiv.innerHTML = `<div class="result-box result-error">❌ Network error: ${{error.message}}</div>`;
                }}
            }}
            
            async function removeCanister(canisterId) {{
                if (confirm(`Remove canister ${{canisterId}}?`)) {{
                    try {{
                        const response = await fetch(`/canisters/${{canisterId}}`, {{
                            method: 'DELETE'
                        }});
                        
                        if (response.ok) {{
                            alert('✅ Canister removed successfully');
                            location.reload();
                        }} else {{
                            const error = await response.json();
                            alert(`❌ Failed to remove canister: ${{error.error}}`);
                        }}
                    }} catch (error) {{
                        alert(`❌ Network error: ${{error.message}}`);
                    }}
                }}
            }}
            
            async function callMethod(canisterId, methodName) {{
                const resultDiv = document.createElement('div');
                resultDiv.className = 'result-box';
                resultDiv.textContent = `Calling ${{methodName}}...`;
                event.target.parentNode.appendChild(resultDiv);
                
                try {{
                    const response = await fetch(`/canisters/${{canisterId}}/${{methodName}}`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ args: [] }})
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        resultDiv.className = 'result-box result-success';
                        resultDiv.innerHTML = `✅ ${{methodName}}: <pre>${{JSON.stringify(result.result, null, 2)}}</pre>`;
                    }} else {{
                        resultDiv.className = 'result-box result-error';
                        resultDiv.textContent = `❌ ${{methodName}}: ${{result.error}}`;
                    }}
                }} catch (error) {{
                    resultDiv.className = 'result-box result-error';
                    resultDiv.textContent = `❌ Network error: ${{error.message}}`;
                }}
                
                setTimeout(() => resultDiv.remove(), 10000);
            }}
            
            async function regenerateIdentity() {{
                if (confirm('⚠️ This will generate a new identity and cannot be undone.\\n\\nA backup will be created automatically.\\n\\nContinue?')) {{
                    try {{
                        const response = await fetch('/regenerate', {{method: 'POST'}});
                        if (response.ok) {{
                            alert('✅ Identity regenerated successfully!\\nOld identity backed up automatically.');
                            location.reload();
                        }} else {{
                            const error = await response.text();
                            alert('❌ Failed to regenerate identity: ' + error);
                        }}
                    }} catch (error) {{
                        alert('❌ Network error: ' + error.message);
                    }}
                }}
            }}
            
            async function createBackup() {{
                try {{
                    const response = await fetch('/backup', {{method: 'POST'}});
                    if (response.ok) {{
                        const result = await response.json();
                        alert('✅ Backup created successfully!\\nPath: ' + result.backup_path);
                        location.reload();
                    }} else {{
                        const error = await response.text();
                        alert('❌ Failed to create backup: ' + error);
                    }}
                }} catch (error) {{
                    alert('❌ Network error: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """