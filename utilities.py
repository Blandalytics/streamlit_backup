import streamlit as st

def load_css():
    st.markdown(
        """
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,700;9..40,900&family=Work+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
    :root{
      --surface-1:#13152A; --surface-2:#181A2C; --surface-3:#21243A;
      --cyan:#55e8ff; --cyan-header:#73efff; --amber:#ffc277; --amber-muted:rgba(255,194,119,0.82);
      --text-nav:#cbd7fd; --text-cell:#f0f1f5; --text-team:rgba(180,187,215,0.68);
      --border-tab:rgba(255,255,255,0.13); --border-table:rgba(118,138,190,0.22);
      --border-row:rgba(140,165,210,0.11); --border-thead:rgba(157,244,255,0.22);
      --row-a:rgba(48,58,97,0.46); --row-b:rgba(42,51,85,0.38);
      --gold:#f5b950;
    }
    [data-testid="stAppViewContainer"], [data-testid="stMain"]{
      background-color:var(--surface-1);
      background-image:url("data:image/svg+xml,%3Csvg%20width%3D%222364%22%20height%3D%222589%22%20viewBox%3D%220%200%202364%202589%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%0A%20%20%3Cdefs%3E%0A%20%20%20%20%3ClinearGradient%20id%3D%22base%22%20x1%3D%220%22%20y1%3D%220%22%20x2%3D%222364%22%20y2%3D%222589%22%20gradientUnits%3D%22userSpaceOnUse%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%23171A2B%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2248%25%22%20stop-color%3D%22%2321243A%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%23181B2C%22/%3E%0A%20%20%20%20%3C/linearGradient%3E%0A%0A%20%20%20%20%3CradialGradient%20id%3D%22r1%22%20cx%3D%220%22%20cy%3D%220%22%20r%3D%221%22%20gradientUnits%3D%22userSpaceOnUse%22%0A%20%20%20%20%20%20gradientTransform%3D%22translate%28425.52%20207.12%29%20scale%281702.08%201190.94%29%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%23BED7FF%22%20stop-opacity%3D%220.085%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2252%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%3C/radialGradient%3E%0A%0A%20%20%20%20%3CradialGradient%20id%3D%22r2%22%20cx%3D%220%22%20cy%3D%220%22%20r%3D%221%22%20gradientUnits%3D%22userSpaceOnUse%22%0A%20%20%20%20%20%20gradientTransform%3D%22translate%281796.64%20466.02%29%20scale%281371.12%20984.82%29%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%2378A5EB%22%20stop-opacity%3D%220.055%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2254%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%3C/radialGradient%3E%0A%0A%20%20%20%20%3CradialGradient%20id%3D%22r3%22%20cx%3D%220%22%20cy%3D%220%22%20r%3D%221%22%20gradientUnits%3D%22userSpaceOnUse%22%0A%20%20%20%20%20%20gradientTransform%3D%22translate%28472.8%202278.32%29%20scale%281654.8%201346.28%29%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%2391B9F5%22%20stop-opacity%3D%220.06%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2256%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%3C/radialGradient%3E%0A%0A%20%20%20%20%3CradialGradient%20id%3D%22r4%22%20cx%3D%220%22%20cy%3D%220%22%20r%3D%221%22%20gradientUnits%3D%22userSpaceOnUse%22%0A%20%20%20%20%20%20gradientTransform%3D%22translate%282080.32%202122.98%29%20scale%281087.44%201605.18%29%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%23D2E4FF%22%20stop-opacity%3D%220.052%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2255%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%3C/radialGradient%3E%0A%0A%20%20%20%20%3ClinearGradient%20id%3D%22l1%22%20x1%3D%220%22%20y1%3D%220%22%20x2%3D%222364%22%20y2%3D%222589%22%0A%20%20%20%20%20%20gradientUnits%3D%22userSpaceOnUse%22%20gradientTransform%3D%22rotate%28-17%201182%201294.5%29%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-color%3D%22%23FFFFFF%22%20stop-opacity%3D%220.045%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2218%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2238%25%22%20stop-color%3D%22%2387AFF0%22%20stop-opacity%3D%220.052%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2261%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%22100%25%22%20stop-color%3D%22%23D2E4FF%22%20stop-opacity%3D%220.04%22/%3E%0A%20%20%20%20%3C/linearGradient%3E%0A%0A%20%20%20%20%3ClinearGradient%20id%3D%22l2%22%20x1%3D%220%22%20y1%3D%222589%22%20x2%3D%222364%22%20y2%3D%220%22%0A%20%20%20%20%20%20gradientUnits%3D%22userSpaceOnUse%22%20gradientTransform%3D%22rotate%289%201182%201294.5%29%22%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%220%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2228%25%22%20stop-color%3D%22%236E91D7%22%20stop-opacity%3D%220.045%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2249%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%2273%25%22%20stop-color%3D%22%23E6F0FF%22%20stop-opacity%3D%220.032%22/%3E%0A%20%20%20%20%20%20%3Cstop%20offset%3D%22100%25%22%20stop-opacity%3D%220%22/%3E%0A%20%20%20%20%3C/linearGradient%3E%0A%20%20%3C/defs%3E%0A%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23base%29%22/%3E%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23l2%29%22/%3E%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23l1%29%22/%3E%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23r4%29%22/%3E%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23r3%29%22/%3E%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23r2%29%22/%3E%0A%20%20%3Crect%20width%3D%222364%22%20height%3D%222589%22%20fill%3D%22url%28%23r1%29%22/%3E%0A%3C/svg%3E%0A");
      background-size:cover; background-position:center top; background-repeat:no-repeat; background-attachment:fixed;
    }
    [data-testid="stHeader"]{background:transparent;}
    html, body, [data-testid="stAppViewContainer"]{color:var(--text-cell); font-family:'DM Sans',sans-serif;}
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3{
      font-family:'DM Sans',sans-serif; font-weight:900; color:var(--cyan);
    }
    [data-testid="stMarkdownContainer"] a{color:var(--cyan-header);}
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li{color:var(--text-nav);}
    /* Date input — styled to the new guide's flat-surface Dropdown, matching the
       selectbox next to it. st.date_input is still a BaseWeb input (not
       react-aria), so it's targeted via data-baseweb — verified against the live
       DOM, not guessed. */
    [data-testid="stDateInput"] div[data-baseweb="input"]{
      position:relative; height:36px; border-radius:8px;
      background:var(--surface-3) !important;
      box-shadow:inset 0 1px 0 rgba(255,255,255,0.06) !important;
      border:1px solid var(--border-tab) !important; overflow:hidden;
    }
    [data-testid="stDateInput"] div[data-baseweb="input"]::after{
      content:''; position:absolute; inset:0; border-radius:inherit; pointer-events:none;
      box-shadow:inset 0 1px 0 rgba(255,255,255,0.3);
    }
    [data-testid="stDateInput"] div[data-baseweb="input"]:focus-within{
      border-radius:8px 8px 0 0;
    }
    [data-testid="stDateInput"] div[data-baseweb="base-input"]{
      background:transparent !important; height:100%;
    }
    [data-testid="stDateInputField"]{
      background:transparent !important; border:none !important; box-shadow:none !important;
      color:var(--text-nav) !important; font:500 14px/1.2 'Work Sans',sans-serif !important;
      padding-left:13px !important; height:100% !important;
    }
    [data-testid="stDateInputField"]:focus-visible{outline:none;}
    [data-baseweb="popover"]{
      background:var(--surface-3) !important;
      border:1px solid #404460 !important;
      box-shadow:0 8px 18px rgba(0,0,0,0.28), inset 1px 0 0 rgba(255,255,255,0.02), inset -1px 0 0 rgba(255,255,255,0.02) !important;
      border-radius:8px !important;
    }
    [data-baseweb="popover"]::before{
      content:''; position:absolute; z-index:1; pointer-events:none;
      top:0; left:7px; right:7px; height:1px;
      background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,0.18) 14%,rgba(255,255,255,0.08) 50%,rgba(255,255,255,0.18) 86%,rgba(255,255,255,0));
    }
    [data-baseweb="calendar"]{background:transparent !important;}
    /* Dropdown — st.selectbox styled to the new guide's flat-surface Dropdown
       ("the only dropdown pattern in the system" as of v1.4), replacing the
       earlier gradient badge trigger. Streamlit (1.60+) renders this as a
       react-aria ComboBox, not the older BaseWeb Select, so it's targeted by
       role/data-testid rather than data-baseweb — verified against the live
       DOM, not guessed. */
    [data-testid="stSelectbox"] div[role="group"]{
      position:relative; height:36px; border-radius:8px;
      background:var(--surface-3) !important;
      box-shadow:inset 0 1px 0 rgba(255,255,255,0.06) !important;
      border:1px solid var(--border-tab) !important; overflow:hidden;
    }
    [data-testid="stSelectbox"] div[role="group"]::after{
      content:''; position:absolute; inset:0; border-radius:inherit; pointer-events:none;
      box-shadow:inset 0 1px 0 rgba(255,255,255,0.3);
    }
    [data-testid="stSelectbox"] div[role="group"]:has(input[aria-expanded="true"]){
      border-radius:8px 8px 0 0;
    }
    [data-testid="stSelectbox"] input[role="combobox"]{
      background:transparent !important; border:none !important; box-shadow:none !important;
      color:var(--text-nav) !important; font:500 14px/1.2 'Work Sans',sans-serif !important;
      padding-left:13px !important;
    }
    [data-testid="stSelectbox"] input[role="combobox"]:focus-visible{outline:none;}
    [data-testid="stSelectbox"] button[aria-haspopup="listbox"]{
      background:transparent !important; border:none !important;
    }
    [data-testid="stSelectbox"] button[aria-haspopup="listbox"] svg{
      color:var(--text-team); fill:var(--text-team); width:14px; height:14px;
    }
    [data-testid="stSelectboxVirtualDropdown"]{
      background:var(--surface-3) !important;
      border:1px solid #404460 !important;
      box-shadow:0 8px 18px rgba(0,0,0,0.28), inset 1px 0 0 rgba(255,255,255,0.02), inset -1px 0 0 rgba(255,255,255,0.02) !important;
      border-radius:0 0 8px 8px !important; margin-top:-1px;
    }
    [data-testid="stSelectboxVirtualDropdown"]::before{
      content:''; position:absolute; z-index:1; pointer-events:none;
      top:0; left:7px; right:7px; height:1px;
      background:linear-gradient(90deg,rgba(255,255,255,0),rgba(255,255,255,0.18) 14%,rgba(255,255,255,0.08) 50%,rgba(255,255,255,0.18) 86%,rgba(255,255,255,0));
    }
    [data-testid="stSelectboxVirtualDropdown"]::after{
      content:''; position:absolute; inset:0; border-radius:inherit; pointer-events:none;
      box-shadow:inset 1px 0 0 rgba(255,255,255,0.02), inset -1px 0 0 rgba(255,255,255,0.02);
    }
    [data-testid="stSelectboxVirtualDropdown"] [role="listbox"]{
      padding-top:8px; padding-bottom:8px; background:transparent !important;
    }
    [data-testid="stSelectboxVirtualDropdown"] [role="option"] [data-item-hl]{
      font:400 14px/1.2 'Work Sans',sans-serif; color:var(--text-nav) !important;
      padding-left:14px; height:100%; display:flex; align-items:center;
      background:transparent !important;
    }
    [data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"]{
      background:#315fa8 !important;
    }
    [data-testid="stSelectboxVirtualDropdown"] [role="option"][data-focused="true"] [data-item-hl]{
      color:#fff !important;
    }
    *:focus-visible{outline:2px solid var(--cyan); outline-offset:2px;}
    .plpd-table-wrap{
      border:1px solid var(--border-table); border-radius:10px; overflow:hidden; position:relative;
      box-shadow:0 0 0 1px rgba(7,9,18,0.3), 0 18px 30px rgba(0,0,0,0.28);
    }
    table.plpd-data{width:100%; border-collapse:collapse; font-family:'Work Sans',sans-serif;}
    table.plpd-data th{
      background:var(--surface-3, #2E3658); background-color:#2E3658;
      font:600 12px 'Work Sans',sans-serif; color:var(--cyan-header);
      height:34.5px; text-align:right; padding:0 14px; white-space:nowrap;
      border-bottom:1px solid var(--border-thead);
    }
    table.plpd-data th.l{text-align:left;}
    table.plpd-data td{
      font:400 14px 'Work Sans',sans-serif; color:var(--text-cell);
      text-align:right; padding:0 14px; height:44px;
      border-bottom:1px solid var(--border-row); font-variant-numeric:tabular-nums;
    }
    table.plpd-data td.l{text-align:left;}
    table.plpd-data tr:nth-child(odd) td{background:var(--row-a);}
    table.plpd-data tr:nth-child(even) td{background:var(--row-b);}
    table.plpd-data td.gold{color:var(--gold); font-weight:700;}
    </style>
    """,
        unsafe_allow_html=True,
    )
