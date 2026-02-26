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
    page_title="OpenGradient Verifiable Chat",
    page_icon="💬",
)

OG_PRIMARY = "#facc15"
OG_PRIMARY_HOVER = "#fde047"
OG_BG = "#020617"
OG_PANEL = "#030712"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {OG_BG}; color: #e5e7eb; font-family: system-ui, sans-serif; }}
    [data-testid="stSidebar"] {{ background-color: {OG_PANEL}; border-right: 1px solid rgba(148,163,184,0.25); }}
    h1, h2, h3, h4 {{ color: #f9fafb; }}
    .stButton > button {{
        background-color: {OG_PRIMARY}; color: #111827; border-radius: 999px; border: none;
        padding: 0.55rem 1.4rem; font-weight: 600; box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    }}
    .stButton > button:hover {{ background-color: {OG_PRIMARY_HOVER}; box-shadow: 0 6px 14px rgba(0,0,0,0.45); }}
    textarea, .stTextInput input {{
        background-color: #020617 !important; color: #e5e7eb !important;
        border-radius: 0.75rem !important; border: 1px solid rgba(148,163,184,0.6) !important;
    }}
    textarea:focus, .stTextInput input:focus {{ border-color: {OG_PRIMARY} !important; box-shadow: 0 0 0 1px {OG_PRIMARY}55 !important; }}
    .stSelectbox > div > div {{
        background-color: #020617 !important; color: #e5e7eb !important;
        border-radius: 0.75rem !important; border: 1px solid rgba(148,163,184,0.6) !important;
    }}
    .social-footer {{
        margin-top: 2rem; padding-top: 1rem; border-top: 1px solid rgba(55,65,81,0.8);
        text-align: center; font-size: 0.9rem; color: #9ca3af;
    }}
    .social-footer a {{ color: {OG_PRIMARY}; text-decoration: none; margin: 0 0.4rem; font-weight: 500; }}
    .social-footer a:hover {{ text-decoration: underline; }}
    .enter-hint {{ font-size: 0.85rem; color: #9ca3af; margin-top: 0.25rem; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("OpenGradient Verifiable Chat")
st.write(
    """
This app demonstrates how to run **verifiable LLM chat via OpenGradient**.

- The request is executed on the OpenGradient network using the Python SDK  
- The model response is accompanied by metadata that can be verified on-chain
"""
)

with st.sidebar:
    st.header("Settings")
    model = st.selectbox(
        "Model",
        [
            og.TEE_LLM.GPT_4O,
            og.TEE_LLM.CLAUDE_3_7_SONNET,
            og.TEE_LLM.GEMINI_2_5_FLASH,
        ],
        format_func=lambda m: str(m).split(".")[-1],
    )
    settlement_mode = st.selectbox(
        "Settlement mode (x402)",
        [
            og.x402SettlementMode.SETTLE,
            og.x402SettlementMode.SETTLE_METADATA,
            og.x402SettlementMode.SETTLE_BATCH,
        ],
        format_func=lambda m: str(m).split(".")[-1],
    )
    st.markdown("---")
    with st.expander("Feedback / Issues"):
        feedback_text = st.text_area(
            "Your message", key="feedback_message", height=90,
            placeholder="Hit an error or have an idea? Leave it here.",
        )
        if st.button("Send", key="send_feedback"):
            if feedback_text.strip():
                st.success("Thanks! Your message has been sent.")
            else:
                st.warning("Please enter a message before sending.")

st.subheader("Prompt")

with st.form("prompt_form", clear_on_submit=False):
    prompt = st.text_area(
        "Enter your prompt",
        height=160,
        placeholder="Example: Explain in simple terms how OpenGradient works and why verifiable inference matters.",
        key="prompt_input",
    )
    st.markdown('<p class="enter-hint">Press <kbd>Enter</kbd> to send, <kbd>Shift+Enter</kbd> for new line.</p>', unsafe_allow_html=True)
    submitted = st.form_submit_button("Run verifiable inference on OpenGradient")

if submitted:
    if not prompt.strip():
        st.warning("Please enter a prompt first.")
    else:
        try:
            client = get_client()
        except Exception as e:
            st.error(f"Failed to initialize OpenGradient client: {e}")
        else:
            with st.spinner("Running verifiable inference on the OpenGradient network..."):
                try:
                    client.llm.ensure_opg_approval(opg_amount=5)
                    completion = client.llm.chat(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        x402_settlement_mode=settlement_mode,
                    )
                except Exception:
                    st.warning(
                        "It looks like something went wrong on the network side. "
                        "Please try sending your request again."
                    )
                else:
                    response_text = None
                    try:
                        response_text = completion.chat_output.get("content")
                    except Exception:
                        pass
                    st.subheader("Model response")
                    if response_text:
                        st.write(response_text)
                    else:
                        st.write("Could not read `chat_output['content']` from the response.")
                        st.json(getattr(completion, "__dict__", str(completion)))
                    st.subheader("On-chain verification")
                    tx_hash = getattr(completion, "transaction_hash", None)
                    if tx_hash and tx_hash != "external":
                        st.write("Transaction hash (Base Sepolia):")
                        st.code(tx_hash, language="text")
                    elif tx_hash == "external":
                        st.write("On-chain transaction hash is managed externally for this request.")
                    else:
                        st.write("`transaction_hash` field not found in the response.")
                    with st.expander("Raw response data (for OpenGradient reviewer)"):
                        st.json(
                            {"transaction_hash": tx_hash, "raw": getattr(completion, "__dict__", str(completion))}
                        )

# Enter key → submit form (Shift+Enter = new line)
st.markdown(
    """
    <script>
    (function() {
        function attachEnterSubmit() {
            var main = document.querySelector('main');
            if (!main) return;
            var ta = main.querySelector('textarea');
            var btn = main.querySelector('button[type="submit"]');
            if (!ta || !btn) return;
            if (ta.dataset.enterDone) return;
            ta.dataset.enterDone = '1';
            ta.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    btn.click();
                }
            });
        }
        if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attachEnterSubmit);
        else attachEnterSubmit();
        setTimeout(attachEnterSubmit, 500);
    })();
    </script>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="social-footer">
      <span>OpenGradient links:</span>
      <a href="https://x.com/OpenGradient" target="_blank" rel="noopener noreferrer">X</a> ·
      <a href="https://discord.gg/2t5sx5BCpB" target="_blank" rel="noopener noreferrer">Discord</a> ·
      <a href="https://www.opengradient.ai/" target="_blank" rel="noopener noreferrer">Website</a> ·
      <a href="https://github.com/OpenGradient" target="_blank" rel="noopener noreferrer">GitHub</a>
    </div>
    """,
    unsafe_allow_html=True,
)
