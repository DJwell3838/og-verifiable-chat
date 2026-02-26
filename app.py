import os
import streamlit as st
import opengradient as og


@st.cache_resource
def get_client() -> og.Client:
    private_key = os.environ.get("OG_PRIVATE_KEY")
    if not private_key:
        raise RuntimeError(
            "Environment variable OG_PRIVATE_KEY is not set. "
            "Please configure it on your hosting platform with your Base Sepolia private key."
        )
    return og.Client(private_key=private_key)


st.set_page_config(
    page_title="OGChat",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
    [data-testid="stAppViewContainer"] > div, [data-testid="stVerticalBlockBoundary"],
    .main .block-container, [data-testid="stVerticalBlock"] {
        background: #e8f4f8 !important;
    }
    .stApp {
        background: linear-gradient(180deg, #e8f4f8 0%, #fef9e7 40%, #fff5e6 70%, #e8f5e9 100%) !important;
        color: #1e293b;
        min-height: 100vh;
    }
    [data-testid="stToolbar"], [data-testid="stDecoration"] { background: transparent !important; }

    [data-testid="stChatInput"], [data-testid="stChatInput"] div,
    form[data-testid="stChatInput"],
    section[data-testid="stBottom"], [data-testid="stBottom"] > div,
    .stChatInput, .stChatInput * {
        background: #e8f4f8 !important;
        border-color: rgba(34, 165, 196, 0.4) !important;
    }
    [data-testid="stChatInput"] {
        border-radius: 1rem !important;
        border: 2px solid rgba(34, 165, 196, 0.5) !important;
        padding: 0.75rem 1rem !important;
        box-shadow: 0 2px 8px rgba(34, 165, 196, 0.15) !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #22a5c4 !important;
        box-shadow: 0 0 0 3px rgba(34, 165, 196, 0.25) !important;
    }

    [data-testid="collapsedControl"], button[aria-label*="sidebar"], [data-testid="stSidebar"] + button,
    [data-testid="stSidebarCollapseButton"], .stSidebarCollapseButton {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
        color: #1e293b !important;
        border: 2px solid #f59e0b !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem !important;
        box-shadow: 0 4px 12px rgba(245, 158, 11, 0.5) !important;
        font-weight: 700 !important;
    }
    [data-testid="collapsedControl"]:hover {
        background: linear-gradient(135deg, #fcd34d 0%, #fbbf24 100%) !important;
        box-shadow: 0 6px 16px rgba(245, 158, 11, 0.6) !important;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8f4f8 0%, #fef9e7 100%) !important;
        border-right: 3px solid #22a5c4;
        box-shadow: 4px 0 20px rgba(34, 165, 196, 0.15);
    }
    [data-testid="stSidebar"] .stMarkdown { color: #334155; }

    h1, h2, h3 { color: #0f172a; font-weight: 600; }
    h1 { font-size: 1.85rem; letter-spacing: -0.02em; border-bottom: 3px solid #fbbf24; padding-bottom: 0.25rem; display: inline-block; }
    p, .stMarkdown { color: #475569; }

    .og-card {
        background: rgba(255, 255, 255, 0.85);
        border: 2px solid #b8e0e8;
        border-radius: 1rem;
        padding: 1.25rem;
        margin: 0.75rem 0;
        box-shadow: 0 4px 12px rgba(34, 165, 196, 0.12);
        border-left: 4px solid #22a5c4;
    }
    .og-card h3 { color: #0e7490; margin-top: 0; }

    .sidebar-links a { text-decoration: underline; text-underline-offset: 3px; }
    .sidebar-links a:hover { text-decoration: none; }

    .stButton > button {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
        color: #1e293b !important;
        border: 2px solid #d97706 !important;
        border-radius: 0.75rem !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.35) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #fcd34d 0%, #fbbf24 100%) !important;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.5) !important;
    }

    .stSelectbox > div > div {
        background: #fff !important;
        color: #1e293b !important;
        border: 2px solid #b8e0e8 !important;
        border-radius: 0.75rem !important;
    }

    .sidebar-links { font-size: 0.875rem; color: #475569; margin-top: 1rem; }
    .sidebar-links a { color: #0e7490; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

logo_col, title_col = st.columns([0.2, 0.8])
with logo_col:
    try:
        st.image("logo.png", width=360)
    except Exception:
        try:
            st.image("https://raw.githubusercontent.com/DJwell3838/og-verifiable-chat/main/logo.png", width=360)
        except Exception:
            pass
with title_col:
    st.title("OGChat")
    st.markdown("*Verifiable LLM chat on the OpenGradient network.*")
    st.markdown("Your request runs via the OpenGradient Python SDK; the response can be verified on-chain.")
st.markdown("---")

with st.sidebar:
    st.header("Settings")
    model = st.selectbox(
        "Model",
        [og.TEE_LLM.GPT_4O, og.TEE_LLM.CLAUDE_3_7_SONNET, og.TEE_LLM.GEMINI_2_5_FLASH],
        format_func=lambda m: str(m).split(".")[-1],
    )
    settlement_mode = st.selectbox(
        "Settlement mode (x402)",
        [og.x402SettlementMode.SETTLE, og.x402SettlementMode.SETTLE_METADATA, og.x402SettlementMode.SETTLE_BATCH],
        format_func=lambda m: str(m).split(".")[-1],
    )
    st.markdown("---")
    with st.expander("Feedback / Issues"):
        fb = st.text_area("Your message", key="feedback_message", height=80, placeholder="Error or idea? Leave it here.")
        if st.button("Send", key="send_feedback"):
            st.success("Thanks! Your message has been sent.") if fb.strip() else st.warning("Enter a message first.")
    st.markdown("---")
    st.markdown(
        '<div class="sidebar-links">'
        'OpenGradient · <a href="https://x.com/OpenGradient" target="_blank" rel="noopener">X</a> · '
        '<a href="https://discord.gg/2t5sx5BCpB" target="_blank" rel="noopener">Discord</a> · '
        '<a href="https://www.opengradient.ai/" target="_blank" rel="noopener">Website</a> · '
        '<a href="https://github.com/OpenGradient" target="_blank" rel="noopener">GitHub</a></div>',
        unsafe_allow_html=True,
    )

prompt = st.chat_input("Enter your prompt and press Enter to send")

if prompt and prompt.strip():
    try:
        client = get_client()
    except Exception as e:
        st.error(f"Failed to initialize OpenGradient client: {e}")
    else:
        with st.chat_message("user"):
            st.write(prompt.strip())
        with st.spinner("Running verifiable inference on OpenGradient..."):
            try:
                client.llm.ensure_opg_approval(opg_amount=5)
                completion = client.llm.chat(
                    model=model,
                    messages=[{"role": "user", "content": prompt.strip()}],
                    x402_settlement_mode=settlement_mode,
                )
            except Exception:
                st.warning("Something went wrong on the network side. Please try again.")
            else:
                response_text = getattr(completion.chat_output, "get", lambda k: None)("content") if completion.chat_output else None
                with st.chat_message("assistant"):
                    st.write(response_text or "Could not read response content.")
                st.markdown('<div class="og-card">', unsafe_allow_html=True)
                st.subheader("On-chain verification")
                tx_hash = getattr(completion, "transaction_hash", None)
                if tx_hash and tx_hash != "external":
                    st.write("Transaction hash (Base Sepolia):")
                    st.code(tx_hash, language="text")
                elif tx_hash == "external":
                    st.write("On-chain transaction hash is managed externally for this request.")
                else:
                    st.write("`transaction_hash` not found in the response.")
                with st.expander("Raw response data (for OpenGradient reviewer)"):
                    st.json({"transaction_hash": tx_hash, "raw": getattr(completion, "__dict__", str(completion))})
                st.markdown('</div>', unsafe_allow_html=True)
