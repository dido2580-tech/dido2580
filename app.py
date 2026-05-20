"""
배리어프리 보이스 페르소나 시뮬레이터 — PoC v1.0
Kakao AI Multimodal CIC · Executive Demo
"""
import copy
import io
import json
import math
import struct
import time
import wave

import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="배리어프리 보이스 페르소나 시뮬레이터",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #FFE500 0%, #FF6B35 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: #2D1200;
        font-size: 2rem;
        margin: 0;
        font-weight: 800;
    }
    .main-header p {
        color: #4A2000;
        margin: 0.4rem 0 0 0;
        font-size: 0.92rem;
    }
    .step-badge {
        background: #1A1A2E;
        color: #FFE500;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.5px;
        margin-right: 8px;
        vertical-align: middle;
    }
    .transformed-text {
        font-size: 1.35rem;
        line-height: 2.0;
        color: #1A1A2E;
        background: white;
        padding: 1.3rem 1.6rem;
        border-radius: 10px;
        border-left: 5px solid #FFE500;
        margin-top: 0.6rem;
    }
    .persona-pill {
        display: inline-block;
        padding: 4px 13px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .waveform-box {
        background: #0D1117;
        border-radius: 12px;
        padding: 1.6rem 1.2rem;
        text-align: center;
        font-family: monospace;
        border: 1px solid #21262D;
    }
    .waveform-bar {
        font-size: 1.6rem;
        color: #39D353;
        letter-spacing: 4px;
        word-break: break-all;
    }
    .waveform-meta {
        font-size: 0.72rem;
        color: #8B949E;
        margin-top: 0.6rem;
        letter-spacing: 0.8px;
    }
    .waveform-label {
        font-size: 0.72rem;
        color: #8B949E;
        margin-bottom: 0.6rem;
        letter-spacing: 1px;
    }
    .param-row {
        display: flex;
        justify-content: space-between;
        padding: 7px 0;
        border-bottom: 1px solid #F3F4F6;
        font-size: 0.87rem;
    }
    .param-label { color: #6B7280; }
    .param-value { font-weight: 600; color: #111827; }
    .kakao-badge {
        background: #FFE500;
        color: #3A1A00;
        font-weight: 700;
        font-size: 0.68rem;
        padding: 2px 7px;
        border-radius: 4px;
    }
    .demo-badge {
        background: #E8F5E9;
        color: #2E7D32;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 2px 7px;
        border-radius: 4px;
    }
    .idle-placeholder {
        text-align: center;
        padding: 3.5rem 2rem;
    }
    .idle-placeholder .icon { font-size: 4.5rem; }
    .idle-placeholder .title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #374151;
        margin-top: 1rem;
    }
    .idle-placeholder .subtitle {
        font-size: 0.88rem;
        color: #9CA3AF;
        margin-top: 0.5rem;
    }
    .pipeline-step {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 14px;
        background: #F9FAFB;
        border-radius: 8px;
        margin-bottom: 6px;
        font-size: 0.88rem;
    }
    .pipeline-step .check { color: #22C55E; font-weight: 700; }

    /* ── Linkage Lab 교차 애니메이션 로고 ── */
    @keyframes ll-show-light {
        0%,  42% { opacity: 1; }
        50%, 92% { opacity: 0; }
        100%     { opacity: 1; }
    }
    @keyframes ll-show-dark {
        0%,  42% { opacity: 0; }
        50%, 92% { opacity: 1; }
        100%     { opacity: 0; }
    }

    .ll-switcher {
        position: relative;
        display: inline-block;
    }
    /* 라이트 버전 (흰 배경, 어두운 글씨) */
    .ll-v-light {
        display: inline-flex;
        align-items: baseline;
        gap: 7px;
        background: #FFFFFF;
        padding: 7px 14px;
        border-radius: 8px;
        animation: ll-show-light 5s ease-in-out infinite;
    }
    /* 다크 버전 (검정 배경, 흰 글씨) */
    .ll-v-dark {
        position: absolute;
        top: 0; left: 0;
        display: inline-flex;
        align-items: baseline;
        gap: 7px;
        background: #2B2B2B;
        padding: 7px 14px;
        border-radius: 8px;
        animation: ll-show-dark 5s ease-in-out infinite;
        white-space: nowrap;
    }
    /* 공통 텍스트 */
    .ll-brand-light {
        font-size: 0.95rem;
        font-weight: 300;
        color: #3A3A3A;
        letter-spacing: 0.3px;
        white-space: nowrap;
    }
    .ll-brand-light b { font-weight: 500; }
    .ll-sub-light {
        font-size: 0.62rem;
        color: #AAAAAA;
        font-weight: 300;
        white-space: nowrap;
    }
    .ll-brand-dark {
        font-size: 0.95rem;
        font-weight: 300;
        color: rgba(255,255,255,0.92);
        letter-spacing: 0.3px;
        white-space: nowrap;
    }
    .ll-brand-dark b { font-weight: 500; }
    .ll-sub-dark {
        font-size: 0.62rem;
        color: rgba(255,255,255,0.45);
        font-weight: 300;
        white-space: nowrap;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_INPUT = (
    "에러 코드 404: 지문 생체 인증에 3회 연속 실패하여 계정이 잠겼습니다. "
    "고객센터로 문의하십시오."
)

USER_TYPE_OPTIONS = [
    "👴 70대 시니어 (키오스크 초보)",
    "👁️ 시각장애인 (파워유저)",
    "🧩 인지 저하 사용자",
]

SITUATION_OPTIONS = [
    "🔴 오류 발생",
    "🔵 일반 안내",
    "💬 일상 대화",
]

USER_TYPE_KEY = {
    "👴 70대 시니어 (키오스크 초보)": "senior",
    "👁️ 시각장애인 (파워유저)": "visually_impaired",
    "🧩 인지 저하 사용자": "cognitive_decline",
}

SITUATION_KEY = {
    "🔴 오류 발생": "error_recovery",
    "🔵 일반 안내": "guidance",
    "💬 일상 대화": "conversation",
}

LANG_LEVEL_LABEL = {
    1: "일반 문체",
    2: "쉬운 말",
    3: "AAC 수준",
    4: "핵심 키워드",
}

PERSONA_META = {
    "hk_warm_guide": {
        "label": "💛 따뜻한 안내자",
        "bg": "#FFF3CD",
        "color": "#856404",
        "freq": 440,
        "desc": "미소가 느껴지는 부드러운 안내. 상승하는 억양으로 신뢰를 전달.",
    },
    "hk_empathetic_care": {
        "label": "💙 공감형 케어",
        "bg": "#DBEAFE",
        "color": "#1D4ED8",
        "freq": 330,
        "desc": "미안함을 담은 들숨(apologetic_sigh)으로 시작하는 위로의 목소리.",
    },
    "hk_calm_navigator": {
        "label": "💚 차분한 내비게이터",
        "bg": "#DCFCE7",
        "color": "#166534",
        "freq": 392,
        "desc": "압축된 다이나믹으로 명확하고 권위있게 길을 안내.",
    },
    "hk_urgent_alert": {
        "label": "🔴 긴급 알림",
        "bg": "#FEE2E2",
        "color": "#991B1B",
        "freq": 523,
        "desc": "높은 볼륨·빠른 발화로 즉각적인 주의를 환기.",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA — Transformed Text  (LLM 역할 대체 Python 딕셔너리)
# ─────────────────────────────────────────────────────────────────────────────
MOCK_TEXT = {
    ("senior", "error_recovery"): (
        "괜찮아요. 손가락 인식이 잘 안 됐어요.\n"
        "세 번이나 안 됐거든요.\n"
        "잠깐 기다리셨다가 고객센터에 전화해 보세요.\n"
        "전화번호는 1588-1234예요. 천천히 하셔도 돼요."
    ),
    ("senior", "guidance"): (
        "이쪽으로 오세요. 천천히 따라오시면 돼요.\n"
        "어려우시면 말씀만 해주세요. 제가 도와드릴게요."
    ),
    ("senior", "conversation"): (
        "안녕하세요! 오늘 뭐 도와드릴까요?\n"
        "편하게 천천히 말씀하세요. 잘 들을게요."
    ),
    ("visually_impaired", "error_recovery"): (
        "지문 인증 3회 실패로 계정이 잠겼습니다.\n"
        "잠금 해제: 고객센터 1588-1234 문의 시 즉시 처리됩니다.\n"
        "통화 연결 버튼은 현재 화면 하단 오른쪽입니다."
    ),
    ("visually_impaired", "guidance"): (
        "현재 위치: 홈 화면입니다.\n"
        "상단 검색 창, 중앙 메뉴 6개, 하단 탭 바로 구성되어 있습니다.\n"
        "원하시는 항목을 말씀해 주세요."
    ),
    ("visually_impaired", "conversation"): (
        "안녕하세요. 무엇을 도와드릴까요?\n"
        "음성으로 말씀하시거나 화면을 탭하셔도 됩니다."
    ),
    ("cognitive_decline", "error_recovery"): (
        "괜찮아요.\n"
        "멈춰요.\n"
        "전화해요.\n"
        "번호: 일오팔팔 — 일이삼사."
    ),
    ("cognitive_decline", "guidance"): (
        "여기 눌러요.\n"
        "이게 맞아요.\n"
        "잘 하셨어요."
    ),
    ("cognitive_decline", "conversation"): (
        "네. 괜찮아요.\n"
        "천천히요.\n"
        "같이 해요."
    ),
}

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA — Base Prosody Presets  (헤이카카오 Voice DNA 기반)
# ─────────────────────────────────────────────────────────────────────────────
BASE_PROSODY_PRESETS = {
    "senior": {
        "persona_id": "hk_empathetic_care",
        "emotion_tag": "apologetic_empathy",
        "speech_rate": {"value": 0.78, "progressive_slowdown": True},
        "pitch": {"baseline_semitones": -1.0, "contour_style": "warm_descend"},
        "volume": {"level": 0.75, "dynamic_range": "compressed"},
        "breathing": {
            "pre_utterance_breath": {
                "enabled": True,
                "duration_ms": 420,
                "breath_type": "apologetic_sigh",
            },
            "mid_clause_micro_pause_prob": 0.65,
        },
        "pauses": {
            "sentence_gap_ms": 1100,
            "clause_gap_ms": 450,
            "keyword_pre_pause_ms": 250,
        },
        "emphasis": {
            "target_words": ["괜찮아요", "천천히", "도와드릴게요"],
            "style": "slow_articulate",
        },
        "articulation": {"clarity_boost": True, "formant_shift": 0.10},
        "target_profile": {
            "user_type": "senior",
            "language_simplification_level": 2,
            "cognitive_load_level": 4,
        },
    },
    "visually_impaired": {
        "persona_id": "hk_calm_navigator",
        "emotion_tag": "calm_authority",
        "speech_rate": {"value": 0.92, "progressive_slowdown": False},
        "pitch": {"baseline_semitones": 0.0, "contour_style": "gentle_rise"},
        "volume": {"level": 0.82, "dynamic_range": "normal"},
        "breathing": {
            "pre_utterance_breath": {
                "enabled": True,
                "duration_ms": 180,
                "breath_type": "gentle_prep",
            },
            "mid_clause_micro_pause_prob": 0.30,
        },
        "pauses": {
            "sentence_gap_ms": 650,
            "clause_gap_ms": 280,
            "keyword_pre_pause_ms": 300,
        },
        "emphasis": {
            "target_words": ["1588-1234", "오른쪽", "홈 화면"],
            "style": "pitch_raise",
        },
        "articulation": {"clarity_boost": True, "formant_shift": -0.05},
        "target_profile": {
            "user_type": "visually_impaired",
            "language_simplification_level": 1,
            "cognitive_load_level": 3,
        },
    },
    "cognitive_decline": {
        "persona_id": "hk_empathetic_care",
        "emotion_tag": "patient_reiteration",
        "speech_rate": {"value": 0.68, "progressive_slowdown": True},
        "pitch": {"baseline_semitones": -0.5, "contour_style": "flat"},
        "volume": {"level": 0.78, "dynamic_range": "compressed"},
        "breathing": {
            "pre_utterance_breath": {
                "enabled": True,
                "duration_ms": 500,
                "breath_type": "apologetic_sigh",
            },
            "mid_clause_micro_pause_prob": 0.80,
        },
        "pauses": {
            "sentence_gap_ms": 1500,
            "clause_gap_ms": 700,
            "keyword_pre_pause_ms": 400,
        },
        "emphasis": {
            "target_words": ["괜찮아요", "천천히", "같이"],
            "style": "slow_articulate",
        },
        "articulation": {"clarity_boost": True, "formant_shift": 0.15},
        "target_profile": {
            "user_type": "cognitive_decline",
            "language_simplification_level": 3,
            "cognitive_load_level": 5,
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# CORE LOGIC — Prosody Builder
# ─────────────────────────────────────────────────────────────────────────────
def build_prosody(user_type: str, situation: str) -> dict:
    """
    Return the full ProsodicSpeechRequest JSON for a given (user_type, situation).
    Starts from the base preset for user_type and applies situation overrides.
    헤이카카오 원음 성우 Voice DNA 기반 감정 세공 파라미터.
    """
    params = copy.deepcopy(BASE_PROSODY_PRESETS[user_type])

    # ── Situation overrides ──────────────────────────────────────────────────
    if situation == "guidance":
        params["emotion_tag"] = "gentle_guidance"
        params["breathing"]["pre_utterance_breath"]["breath_type"] = "gentle_prep"
        if user_type in ("senior", "cognitive_decline"):
            params["persona_id"] = "hk_warm_guide"
        params["target_profile"]["cognitive_load_level"] = max(
            1, params["target_profile"]["cognitive_load_level"] - 1
        )

    elif situation == "conversation":
        params["emotion_tag"] = "warm_assurance"
        params["speech_rate"]["value"] = round(
            min(params["speech_rate"]["value"] + 0.05, 1.20), 2
        )
        params["breathing"]["pre_utterance_breath"]["breath_type"] = "warm_smile_breath"
        if user_type in ("senior", "cognitive_decline"):
            params["persona_id"] = "hk_warm_guide"
        params["target_profile"]["cognitive_load_level"] = 2

    # error_recovery: use base preset as-is (already tuned for confusion/distress)

    # ── Add schema metadata ──────────────────────────────────────────────────
    result = {
        "_schema": "BarrierFreeVoicePersonaRequest/v1.0",
        "_comment": (
            f"헤이카카오 원음 성우 Voice DNA 기반 감정 세공 파라미터 "
            f"— {user_type} × {situation}"
        ),
        "_voice_dna_note": (
            "breathing.breath_type 필드의 들숨 패턴과 progressive_slowdown은 "
            "17년 캐릭터 연기 경험에서 추출된 헤이카카오 Voice DNA의 핵심 차별화 요소입니다."
        ),
    }
    result.update(params)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO — Sine-wave tone generator (외부 패키지 불필요)
# ─────────────────────────────────────────────────────────────────────────────
def generate_voice_tone(persona_id: str, duration: float = 2.5) -> bytes:
    """
    Generate a persona-characteristic WAV tone using Python's standard library.
    Each persona maps to a distinct fundamental frequency to simulate voice DNA.
    """
    freq = PERSONA_META[persona_id]["freq"]
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    amplitude = 18000
    fade_in_s, fade_out_s = 0.06, 0.18

    frames = []
    for i in range(n_samples):
        t = i / sample_rate
        # Fundamental + 2 harmonics for richer timbre
        wave_val = (
            0.70 * math.sin(2 * math.pi * freq * t)
            + 0.20 * math.sin(2 * math.pi * freq * 2 * t)
            + 0.10 * math.sin(2 * math.pi * freq * 3 * t)
        )
        # Amplitude envelope: fade in / sustain / fade out
        env = min(t / fade_in_s, 1.0, (duration - t) / fade_out_s)
        # Gentle vibrato at 5.5 Hz simulates natural voice modulation
        vibrato = 1 + 0.018 * math.sin(2 * math.pi * 5.5 * t)
        sample = int(amplitude * wave_val * env * vibrato)
        sample = max(-32767, min(32767, sample))
        frames.append(struct.pack("<h", sample))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
    return buf.getvalue()


def waveform_art(persona_id: str) -> str:
    """Return a Unicode block waveform pattern themed to each persona."""
    patterns = {
        "hk_warm_guide":      "▁▂▃▄▅▆▅▄▃▅▇█▇▅▃▄▆▇▆▄▃▂▄▅▆▅▄▃▂▁",
        "hk_empathetic_care": "▁▁▂▃▃▄▄▅▅▄▄▃▃▄▅▆▅▄▃▂▂▃▄▃▂▁▁▁▁▁",
        "hk_calm_navigator":  "▂▃▄▅▅▆▆▇▇▆▆▅▅▄▄▅▅▆▆▅▅▄▄▃▃▂▂▃▃▂",
        "hk_urgent_alert":    "▁▄▇█▇▄▁▄▇█▇▄▁▅█▅▁▃▇█▇▃▁▄▇█▇▄▁▁",
    }
    return patterns.get(persona_id, "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁")


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
    <div style='text-align:center; padding: 1.2rem 0 1.8rem 0; border-bottom:1px solid #E5E7EB;'>
        <div style='font-size:2.8rem;'>🎙️</div>
        <div style='font-weight:800; font-size:1rem; color:#1A1A2E; margin-top:0.5rem;'>
            배리어프리 보이스 페르소나
        </div>
        <div style='font-size:0.72rem; color:#9CA3AF; margin-top:3px;'>
            Kakao AI Multimodal CIC · PoC v1.0
        </div>
        <div style='margin-top:0.6rem;'>
            <span class='kakao-badge'>KAKAO</span>
            &nbsp;
            <span class='demo-badge'>DEMO</span>
        </div>
        <div style='margin-top:1rem; height:34px;'>
            <div class='ll-switcher'>
                <div class='ll-v-light'>
                    <span class='ll-brand-light'>Linkage <b>Lab</b></span>
                    <span class='ll-sub-light'>a kakao company</span>
                </div>
                <div class='ll-v-dark'>
                    <span class='ll-brand-dark'>Linkage <b>Lab</b></span>
                    <span class='ll-sub-dark'>a kakao company</span>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("#### 🎯 타깃 유저")
    selected_user = st.selectbox(
        "타깃 유저",
        USER_TYPE_OPTIONS,
        label_visibility="collapsed",
    )

    st.markdown("#### 📌 발화 상황")
    selected_situation = st.selectbox(
        "발화 상황",
        SITUATION_OPTIONS,
        label_visibility="collapsed",
    )

    # Live persona preview in sidebar
    user_type = USER_TYPE_KEY[selected_user]
    situation = SITUATION_KEY[selected_situation]
    preview_params = build_prosody(user_type, situation)
    persona_id_preview = preview_params["persona_id"]
    pm_preview = PERSONA_META[persona_id_preview]

    st.divider()
    st.markdown("**🎭 활성화될 보이스 페르소나**")
    st.markdown(
        f"<span class='persona-pill' style='background:{pm_preview['bg']};"
        f"color:{pm_preview['color']};'>{pm_preview['label']}</span>",
        unsafe_allow_html=True,
    )
    st.caption(pm_preview["desc"])

    st.divider()
    with st.expander("ℹ️ 이 시뮬레이터에 대하여"):
        st.markdown(
            """
        **배리어프리 보이스 페르소나** B2B 솔루션의 핵심 파이프라인을 시연합니다.

        ```
        📷 Vision  → 감정 상태 인식
        ✍️  Text    → 쉬운 언어 변환 (LLM)
        🔊 Audio   → 감정 맞춤 TTS 출력
        ```

        실제 제품에서는 **Claude API** + **카카오 보이스 모델**이
        실시간으로 연동됩니다.
        """
        )


# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class='main-header'>
    <div style='display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:1rem;'>
        <div>
            <h1>🎙️ 배리어프리 보이스 페르소나 시뮬레이터</h1>
            <p>Barrier-Free Voice Persona · Multimodal Pipeline PoC · Kakao AI CIC</p>
        </div>
        <div style='display:flex; align-items:center; padding-top:0.3rem; height:38px;'>
            <div class='ll-switcher'>
                <div class='ll-v-light'>
                    <span class='ll-brand-light' style='font-size:1.05rem;'>Linkage <b>Lab</b></span>
                    <span class='ll-sub-light' style='font-size:0.65rem;'>a kakao company</span>
                </div>
                <div class='ll-v-dark'>
                    <span class='ll-brand-dark' style='font-size:1.05rem;'>Linkage <b>Lab</b></span>
                    <span class='ll-sub-dark' style='font-size:0.65rem;'>a kakao company</span>
                </div>
            </div>
        </div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Input Section
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### 📥 기존 IT 오류 메시지 입력")

col_input, col_target = st.columns([3, 1])
with col_input:
    input_text = st.text_area(
        "변환할 딱딱한 시스템 메시지를 입력하세요",
        value=DEFAULT_INPUT,
        height=95,
        help="실제 서비스에서 발생하는 에러 메시지나 안내문을 입력하세요.",
    )
with col_target:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"**타깃:** {selected_user}\n\n**상황:** {selected_situation}")

run_btn = st.button(
    "🚀  보이스 페르소나 변환 및 감정 매핑 실행",
    type="primary",
    use_container_width=True,
)

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN — Processing & Results
# ─────────────────────────────────────────────────────────────────────────────
if run_btn:

    # ── Pipeline processing animation ────────────────────────────────────────
    progress_bar = st.progress(0, text="🧠 Vision 모듈: 사용자 감정 상태 분석 중...")
    time.sleep(0.4)
    progress_bar.progress(30, text="✍️ LLM 오케스트레이터: 언어 변환 및 페르소나 선택 중...")
    time.sleep(0.4)
    progress_bar.progress(65, text="🎼 Audio 엔진: Voice DNA 프로소디 렌더링 중...")
    time.sleep(0.4)
    progress_bar.progress(100, text="✅ 파이프라인 실행 완료!")
    time.sleep(0.3)
    progress_bar.empty()

    # ── Compute outputs ───────────────────────────────────────────────────────
    prosody = build_prosody(user_type, situation)
    persona_id = prosody["persona_id"]
    pm = PERSONA_META[persona_id]
    transformed = MOCK_TEXT.get((user_type, situation), "변환된 텍스트가 없습니다.")
    lang_lvl = prosody["target_profile"]["language_simplification_level"]

    # ── Summary banner ────────────────────────────────────────────────────────
    st.success(
        f"✅ **파이프라인 완료**  |  "
        f"페르소나: **{pm['label']}**  |  "
        f"감정 태그: `{prosody['emotion_tag']}`  |  "
        f"언어 레벨: `{lang_lvl} — {LANG_LEVEL_LABEL[lang_lvl]}`"
    )

    # ── Key metrics row ───────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    speed = prosody["speech_rate"]["value"]
    gap   = prosody["pauses"]["sentence_gap_ms"]
    breath = prosody["breathing"]["pre_utterance_breath"]["breath_type"]
    clarity = "ON ✓" if prosody["articulation"]["clarity_boost"] else "OFF"
    m1.metric("발화 속도", f"×{speed}", delta=f"{round((speed - 1) * 100)}%", delta_color="inverse")
    m2.metric("문장 간 휴지", f"{gap} ms")
    m3.metric("들숨 패턴", breath.replace("_", " ").title())
    m4.metric("명료도 강화", clarity)

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # RESULT 1 — Text Transformation
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<span class='step-badge'>STEP 01</span>"
        f"<span style='font-weight:700; font-size:1.1rem;'>🗣️ Text 변환 — 쉬운 언어로 재작성</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_before, col_arrow, col_after = st.columns([5, 1, 5])

    with col_before:
        st.markdown("**📄 원문 (딱딱한 IT 메시지)**")
        st.warning(f"🚫  {input_text}")

    with col_arrow:
        st.markdown(
            "<div style='text-align:center; font-size:2.2rem; padding-top:1.6rem;'>➡️</div>",
            unsafe_allow_html=True,
        )

    with col_after:
        st.markdown(
            f"**✨ 변환 결과** &nbsp;"
            f"<span class='persona-pill' style='background:{pm['bg']};"
            f"color:{pm['color']};'>{pm['label']}</span>",
            unsafe_allow_html=True,
        )
        html_text = transformed.replace("\n", "<br>")
        st.markdown(
            f"<div class='transformed-text'>{html_text}</div>",
            unsafe_allow_html=True,
        )

    st.caption(
        f"🔤 언어 단순화 레벨: **{lang_lvl} — {LANG_LEVEL_LABEL[lang_lvl]}**  |  "
        f"인지 부하 지수: **{prosody['target_profile']['cognitive_load_level']} / 5**"
    )

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # RESULT 2 — Prosody JSON
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<span class='step-badge'>STEP 02</span>"
        f"<span style='font-weight:700; font-size:1.1rem;'>⚙️ Prosody 데이터 — 감정 세공 파라미터 JSON</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_json, col_interp = st.columns([3, 2])

    with col_json:
        st.code(json.dumps(prosody, ensure_ascii=False, indent=2), language="json")

    with col_interp:
        st.markdown("**📋 파라미터 해석**")

        key_params = [
            ("🎭 페르소나", pm["label"]),
            ("😊 감정 태그", prosody["emotion_tag"]),
            (
                "⏱️ 발화 속도",
                f"×{prosody['speech_rate']['value']}"
                + (" · 점진 감속" if prosody["speech_rate"]["progressive_slowdown"] else ""),
            ),
            ("🎵 억양 윤곽", prosody["pitch"]["contour_style"]),
            ("💨 들숨 유형", prosody["breathing"]["pre_utterance_breath"]["breath_type"]),
            ("⏸️ 문장 휴지", f"{prosody['pauses']['sentence_gap_ms']} ms"),
            ("✨ 강조 스타일", prosody["emphasis"]["style"]),
            ("🔊 명료도", "활성화" if prosody["articulation"]["clarity_boost"] else "비활성화"),
        ]
        for label, value in key_params:
            st.markdown(
                f"<div class='param-row'>"
                f"<span class='param-label'>{label}</span>"
                f"<span class='param-value'>{value}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            "💡 **Voice DNA 핵심 포인트**\n\n"
            "`breathing.breath_type`에 담긴 들숨 패턴과 "
            "`progressive_slowdown`은 17년 성우 연기 경험에서 "
            "추출된 **헤이카카오 Voice DNA**의 핵심 차별화 요소입니다."
        )

    st.divider()

    # ══════════════════════════════════════════════════════════════════════════
    # RESULT 3 — Audio Simulation
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(
        f"<span class='step-badge'>STEP 03</span>"
        f"<span style='font-weight:700; font-size:1.1rem;'>🔊 Audio 시뮬레이션 — 보이스 페르소나 출력</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    col_audio, col_wave = st.columns([1, 2])

    with col_audio:
        st.markdown(f"**페르소나 특성 톤 미리듣기**")
        st.caption(
            f"{pm['label']}  |  특성 주파수 {PERSONA_META[persona_id]['freq']} Hz"
        )
        with st.spinner("🎼 Voice DNA 톤 렌더링 중..."):
            audio_bytes = generate_voice_tone(persona_id, duration=2.5)
        st.audio(audio_bytes, format="audio/wav")
        st.markdown(
            f"<span class='persona-pill' style='background:{pm['bg']};"
            f"color:{pm['color']};'>{pm['label']}</span>",
            unsafe_allow_html=True,
        )

    with col_wave:
        st.markdown("**실시간 파형 시각화 (시뮬레이션)**")
        wave_chars = waveform_art(persona_id)
        pitch_st = prosody["pitch"]["baseline_semitones"]
        breath_type = prosody["breathing"]["pre_utterance_breath"]["breath_type"]
        st.markdown(
            f"<div class='waveform-box'>"
            f"<div class='waveform-label'>▶ VOICE PERSONA ENGINE · RENDERING</div>"
            f"<div class='waveform-bar'>{wave_chars}</div>"
            f"<div class='waveform-meta'>"
            f"RATE: {prosody['speech_rate']['value']}x  "
            f"| PITCH: {pitch_st:+.1f}st  "
            f"| BREATH: {breath_type.upper()}"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.caption(
            "⚠️ **PoC 시연 모드**: 실제 제품에서는 헤이카카오 원음 성우의 Voice DNA가 "
            "파인튜닝된 TTS 모델(VITS2 또는 ClovaVoice API)을 통해 감정 맞춤 음성으로 "
            "실시간 합성됩니다."
        )

    # ── Pipeline summary ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🔁 파이프라인 실행 요약")

    pipeline_log = [
        ("📷 Vision", "사용자 감정 상태 인식 완료"),
        ("📦 Context", f"타깃: {selected_user}  |  상황: {selected_situation}"),
        (
            "🧠 LLM 오케스트레이터",
            f"페르소나: {pm['label']}  |  감정 태그: {prosody['emotion_tag']}",
        ),
        (
            "✍️ Text 변환",
            f"언어 단순화 레벨 {lang_lvl} ({LANG_LEVEL_LABEL[lang_lvl]}) 적용",
        ),
        (
            "🎼 Audio 합성",
            f"Voice DNA 톤 렌더링 완료  |  특성 주파수: {PERSONA_META[persona_id]['freq']} Hz",
        ),
        ("📤 출력 완료", "시연 성공 ✅"),
    ]
    for step, desc in pipeline_log:
        st.markdown(
            f"<div class='pipeline-step'>"
            f"<span class='check'>✓</span>"
            f"<strong>{step}</strong>"
            f"<span style='color:#6B7280; margin-left:4px;'>— {desc}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# IDLE STATE
# ─────────────────────────────────────────────────────────────────────────────
else:
    st.markdown(
        """
    <div class='idle-placeholder'>
        <div class='icon'>🎙️</div>
        <div class='title'>
            사이드바에서 타깃 유저와 상황을 선택한 후<br>
            <b>보이스 페르소나 변환 및 감정 매핑 실행</b> 버튼을 누르세요.
        </div>
        <div class='subtitle'>
            Vision → Text → Audio 멀티모달 파이프라인이 실시간으로 실행됩니다.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**📷 STEP 01 — Vision**\n\n사용자의 감정 상태와 상황을 인식합니다.")
    with col2:
        st.info("**✍️ STEP 02 — Text**\n\n타깃에 맞게 쉬운 언어로 변환하고\n프로소디 파라미터를 결정합니다.")
    with col3:
        st.info("**🔊 STEP 03 — Audio**\n\n헤이카카오 Voice DNA 기반\n감정 맞춤 음성을 합성합니다.")
