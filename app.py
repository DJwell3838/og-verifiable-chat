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

st.title("OpenGradient Verifiable Chat")
st.write(
    """
This app demonstrates how to run **verifiable LLM chat via OpenGradient**.

- The request is executed on the OpenGradient network using the Python SDK  
- The model response is accompanied by a **transaction hash** that can be verified on-chain
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

st.subheader("Prompt")
prompt = st.text_area(
    "Enter your prompt",
    height=160,
    placeholder="Example: Explain in simple terms how OpenGradient works and why verifiable inference matters.",
)

if st.button("Run verifiable inference on OpenGradient", type="primary"):
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
                    # Ensure there is enough OPG allowance for x402 payments
                    client.llm.ensure_opg_approval(opg_amount=5)

                    completion = client.llm.chat(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        x402_settlement_mode=settlement_mode,
                    )
                except Exception as e:
                    st.error(f"Error while calling OpenGradient: {e}")
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
                            {
                                "transaction_hash": tx_hash,
                                "raw": getattr(completion, "__dict__", str(completion)),
                            }
                        )
