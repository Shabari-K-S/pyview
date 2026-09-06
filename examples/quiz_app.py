"""Systems Architecture & Python Trivia Quiz."""

import pyview as pv

QUESTIONS = [
    {
        "question": "What mechanism in Python is best suited for per-session context isolation without global locks?",
        "options": ["A) contextvars.ContextVar", "B) Global dictionaries with mutexes", "C) OS subprocesses only", "D) Class variables"],
        "correct_index": 0,
        "explanation": "`contextvars.ContextVar` allows concurrent execution contexts to preserve isolated variables across async and thread boundaries without shared state leaks.",
    },
    {
        "question": "Why should text input fields dispatch on blur/Enter rather than raw keypresses?",
        "options": ["A) WebSockets cannot send strings", "B) To avoid triggering redundant full-script reruns on every keystroke", "C) JavaScript requires it", "D) It makes the browser faster"],
        "correct_index": 1,
        "explanation": "Debouncing to blur/Enter prevents flooding the backend execution loop with intermediate rerun cycles while the user is actively typing.",
    },
    {
        "question": "In a reactive rerun framework, how do buttons differ from value input widgets?",
        "options": ["A) Text input has no state", "B) Buttons are persistent; text inputs are transient", "C) Buttons are transient triggers (True only on click rerun); text inputs are persistent", "D) There is no difference"],
        "correct_index": 2,
        "explanation": "Buttons evaluate to True only during the single rerun cycle initiated by the click event, then reset to False on subsequent reruns.",
    },
    {
        "question": "Why is offloading user scripts to worker threads essential for an async FastAPI backend?",
        "options": ["A) FastAPI cannot run without threads", "B) To prevent synchronous/blocking Python user scripts from stalling the async event loop", "C) Threading increases memory usage", "D) WebSockets only work with threads"],
        "correct_index": 1,
        "explanation": "Running user scripts in worker threads ensures WebSocket connections and the server async event loop remain fully responsive.",
    },
]

# Initialize Quiz State
if "q_index" not in pv.session_state:
    pv.session_state.q_index = 0
if "score" not in pv.session_state:
    pv.session_state.score = 0
if "answered" not in pv.session_state:
    pv.session_state.answered = False
if "is_correct" not in pv.session_state:
    pv.session_state.is_correct = False

q_idx = pv.session_state.q_index
total_q = len(QUESTIONS)

# Main Quiz Header
pv.title("🧠 Systems Architecture Trivia")
pv.write("Test your understanding of reactive execution loops, context isolation, and async web runtimes.")

# Top Progress & Score Strip
col_p, col_s, col_r = pv.columns([2, 2, 1])
with col_p:
    pv.metric("Quiz Progress", f"{min(q_idx + 1, total_q)} / {total_q}")
with col_s:
    pv.metric("Current Score", f"{pv.session_state.score} pts", delta=f"{pv.session_state.score}/{total_q}")
with col_r:
    pv.write("") # spacing
    if pv.button("🔄 Restart Quiz", key="btn_restart_top"):
        pv.session_state.q_index = 0
        pv.session_state.score = 0
        pv.session_state.answered = False

pv.divider()

# Active Question or Final Screen
if q_idx < total_q:
    curr = QUESTIONS[q_idx]
    
    with pv.card(f"Question {q_idx + 1} of {total_q}"):
        pv.write(f"### {curr['question']}")
        pv.divider()
        
        if not pv.session_state.answered:
            pv.write("👉 **Choose an answer:**")
            
            # 2x2 Option Buttons Grid
            c1, c2 = pv.columns([1, 1])
            with c1:
                if pv.button(curr["options"][0], key=f"btn_opt_{q_idx}_0"):
                    pv.session_state.answered = True
                    pv.session_state.score += 1 if curr["correct_index"] == 0 else 0
                    pv.session_state.is_correct = (curr["correct_index"] == 0)
                if pv.button(curr["options"][1], key=f"btn_opt_{q_idx}_1"):
                    pv.session_state.answered = True
                    pv.session_state.score += 1 if curr["correct_index"] == 1 else 0
                    pv.session_state.is_correct = (curr["correct_index"] == 1)
            with c2:
                if pv.button(curr["options"][2], key=f"btn_opt_{q_idx}_2"):
                    pv.session_state.answered = True
                    pv.session_state.score += 1 if curr["correct_index"] == 2 else 0
                    pv.session_state.is_correct = (curr["correct_index"] == 2)
                if pv.button(curr["options"][3], key=f"btn_opt_{q_idx}_3"):
                    pv.session_state.answered = True
                    pv.session_state.score += 1 if curr["correct_index"] == 3 else 0
                    pv.session_state.is_correct = (curr["correct_index"] == 3)
        else:
            if pv.session_state.is_correct:
                pv.success("✅ **Correct!** Excellent systems engineering knowledge.")
            else:
                correct_str = curr["options"][curr["correct_index"]]
                pv.error(f"❌ **Incorrect!** The correct answer was: `{correct_str}`")
                
            with pv.expander("🔍 Deep-Dive Explanation", expanded=True):
                pv.write(curr["explanation"])
                
            pv.divider()
            next_label = "🏁 View Final Results" if q_idx + 1 == total_q else "➡️ Next Question"
            if pv.button(next_label, key=f"btn_next_{q_idx}"):
                pv.session_state.q_index += 1
                pv.session_state.answered = False

else:
    # Final Results Screen
    final_score = pv.session_state.score
    pct = (final_score / total_q) * 100
    
    with pv.card("🏆 Quiz Completed!"):
        c_score, c_rating = pv.columns([1, 1])
        with c_score:
            pv.metric("Final Score", f"{final_score} / {total_q}", delta=f"{pct:.0f}%", delta_color="normal")
        with c_rating:
            if pct == 100:
                pv.success("🌟 **Mastery Level**: Outstanding grasp of reactive systems!")
            elif pct >= 75:
                pv.info("👏 **Proficient**: Solid understanding of core runtime fundamentals.")
            else:
                pv.warning("📚 **Keep Learning**: Review the architecture guide and try again.")
                
        pv.divider()
        if pv.button("🔄 Retake Quiz", key="btn_retake_quiz"):
            pv.session_state.q_index = 0
            pv.session_state.score = 0
            pv.session_state.answered = False
