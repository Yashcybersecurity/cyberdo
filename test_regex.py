import re

root_vars = """:root{
  --bg-app: #F2EDE4;
  --bg-sidebar: #2A1A12;
  --bg-card: #FFFDF9;
  --bg-element: #FAF7F2;
  --bg-hover: #E8DFD0;
  --border: #D8CFC4;
  --border-light: #E8E0D5;
  --text-primary: #2A1A12;
  --text-secondary: #5C4A3A;
  --text-muted: #9A8070;
  --accent: #C96A45;
  --accent-glow: rgba(201,106,69,0.25);
  --accent-gradient: linear-gradient(135deg, #C96A45, #E07B39);
  --danger: #C0392B; --warning: #D4881A; --success: #2D7A4A; --info: #2E6E8A;
  --danger-bg: #FEE8E5; --warning-bg: #FEF3DC;
  --success-bg: #E5F5EC; --info-bg: #E3EEF4;
  --radius: 12px; --radius-sm: 8px;
  --shadow: 0 4px 20px rgba(61,43,31,0.08);
  --glow: 0 4px 15px var(--accent-glow);
}"""

for f_name in ['index.html', 'db_records.html']:
    with open(f_name, 'r') as f:
        html = f.read()
    html = re.sub(r':root\s*\{.*?\}', root_vars, html, flags=re.DOTALL)
    
    html = html.replace('rgba(0,0,0,0.3)', 'rgba(61,43,31,0.08)')
    html = html.replace('rgba(0,0,0,0.4)', 'rgba(61,43,31,0.12)')
    html = html.replace('rgba(0,0,0,0.5)', 'rgba(61,43,31,0.25)')
    html = html.replace('rgba(0,0,0,0.2)', 'rgba(61,43,31,0.06)')
    html = html.replace('rgba(0,0,0,0.7)', 'rgba(42,26,18,0.5)')
    html = html.replace('rgba(0,0,0,0.6)', 'rgba(42,26,18,0.4)')
    html = html.replace('rgba(239,68,68,0.15)', 'rgba(192,57,43,0.15)')

    html = html.replace('#F97316', 'var(--accent)')
    html = html.replace('rgba(249,115,22,0.15)', 'var(--accent-glow)')
    html = html.replace('border:1px solid rgba(249,115,22,0.2)', 'border:1px solid rgba(201,106,69,0.3)')

    if f_name == 'index.html':
        html = html.replace('.sidebar-brand{padding:24px;border-bottom:1px solid var(--border);', '.sidebar-brand{padding:24px;border-bottom:1px solid rgba(255,255,255,0.08);')
        html = html.replace('.brand-name{font-family:\'Fraunces\',serif;font-size:18px;font-weight:700;color:var(--text-primary);line-height:1.2}', '.brand-name{font-family:\'Fraunces\',serif;font-size:18px;font-weight:700;color:#FFFDF9;line-height:1.2}')
        html = html.replace('.brand-tagline{font-size:10px;color:var(--text-secondary);', '.brand-tagline{font-size:10px;color:rgba(255,255,255,0.4);')
        html = html.replace('.close-sidebar-btn{display:none;font-size:20px;background:none;border:none;color:var(--text-muted);cursor:pointer;}', '.close-sidebar-btn{display:none;font-size:20px;background:none;border:none;color:rgba(255,255,255,0.5);cursor:pointer;}')

        html = html.replace('.sidebar-scroll::-webkit-scrollbar-thumb{background:var(--border-light);border-radius:2px;}', '.sidebar-scroll::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.2);border-radius:2px;}')

        html = html.replace('.sidebar-section-label{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--text-muted);', '.sidebar-section-label{font-size:11px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.3);')
        html = html.replace('.nav-item{display:flex;align-items:center;gap:12px;padding:10px 16px;border-radius:8px;color:var(--text-secondary);', '.nav-item{display:flex;align-items:center;gap:12px;padding:10px 16px;border-radius:8px;color:rgba(255,255,255,0.6);')
        html = html.replace('.nav-item:hover{background:var(--bg-hover);color:var(--text-primary)}', '.nav-item:hover{background:rgba(255,255,255,0.08);color:#FFFDF9;}')

        html = html.replace('.sidebar-footer{padding:16px;border-top:1px solid var(--border);margin-top:auto;}', '.sidebar-footer{padding:16px;border-top:1px solid rgba(255,255,255,0.08);margin-top:auto;}')
        html = html.replace('.user-card{display:flex;align-items:center;gap:12px;padding:12px;border-radius:10px;background:var(--bg-element);cursor:pointer;border:1px solid var(--border);transition:border-color .2s}', '.user-card{display:flex;align-items:center;gap:12px;padding:12px;border-radius:10px;background:rgba(255,255,255,0.05);cursor:pointer;border:1px solid rgba(255,255,255,0.05);transition:border-color .2s}')
        html = html.replace('.user-card:hover{border-color:var(--border-light)}', '.user-card:hover{border-color:rgba(255,255,255,0.15)}')
        html = html.replace('.user-name{font-size:13px;font-weight:600;color:var(--text-primary)}', '.user-name{font-size:13px;font-weight:600;color:#FFFDF9}')
        html = html.replace('.user-role{font-size:11px;color:var(--text-muted)}', '.user-role{font-size:11px;color:rgba(255,255,255,0.4)}')

        html = html.replace('background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.3);color:#A78BFA;', 'background:var(--info-bg);border:1px solid var(--info);color:var(--info);')
        html = html.replace('box-shadow:0 0 10px currentColor', 'box-shadow:0 0 6px currentColor')
        html = html.replace('rgba(239,68,68,0.1)', 'var(--danger-bg)')
        html = html.replace('rgba(239,68,68,0.2)', 'rgba(192,57,43,0.25)')

    with open(f_name, 'w') as f:
        f.write(html)
        
print("Rewrite finished.")
