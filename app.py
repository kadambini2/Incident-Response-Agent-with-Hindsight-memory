"""Streamlit UI: memory on/off, recalled incidents, feedback loop."""
import uuid

import streamlit as st

import agent
import memory

st.set_page_config(page_title="Incident Response Agent", page_icon="🚨", layout="wide")
st.title("🚨 Incident Response Agent (powered by Hindsight memory)")

with st.sidebar:
    use_memory = st.toggle("Use Hindsight memory", value=True)
    st.caption("Turn off to see the generic, memory-less answer.")
    if st.button("Reflect: find patterns in past incidents"):
        with st.spinner("Reflecting over memory..."):
            st.info(memory.reflect_patterns())

service = st.text_input("Service", "payments-api")
alert = st.text_area("Alert / error log", "ERROR 504 upstream timeout; connection pool exhausted after deploy", height=120)

if st.button("Diagnose", type="primary") and alert.strip():
    with st.spinner("Thinking..."):
        st.session_state.result = agent.diagnose(f"Service: {service}\n{alert}", use_memory)
        st.session_state.incident_id = f"LIVE-{uuid.uuid4().hex[:6]}"
        st.session_state.service = service

res = st.session_state.get("result")
if res:
    left, right = st.columns([3, 2])
    with left:
        st.subheader("Diagnosis")
        st.markdown(res["answer"])
        st.write("Did this fix work?")
        c1, c2, _ = st.columns([1, 1, 4])
        if c1.button("✅ Worked"):
            memory.retain_feedback(st.session_state.incident_id, st.session_state.service, res["answer"][:500], True)
            st.success("Saved to memory.")
        if c2.button("❌ Failed"):
            memory.retain_feedback(st.session_state.incident_id, st.session_state.service, res["answer"][:500], False)
            st.warning("Saved to memory.")
    with right:
        st.subheader(f"Recalled from memory ({len(res['memories'])})")
        if not res["memories"]:
            st.caption("Nothing recalled (memory off or no matches).")
        for m in res["memories"]:
            with st.expander(m[:70] + "..."):
                st.text(m)
