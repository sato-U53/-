import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import base64
import uuid
import time
import streamlit.components.v1 as components

# =====================================
# ページ設定
# =====================================
st.set_page_config(page_title="英単語テスト", layout="centered")

# =====================================
# 音声再生
# =====================================
def speak(text: str):
    filename = f"temp_{uuid.uuid4().hex}.mp3"
    try:
        tts = gTTS(text=text, lang="en")
        tts.save(filename)
        with open(filename, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        html = f'<audio autoplay="true"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
        st.markdown(html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"音声生成エラー: {e}")
    finally:
        if os.path.exists(filename):
            try: os.remove(filename)
            except: pass

# =====================================
# 強力なキーボード操作用JavaScript (長押し防止)
# =====================================
def keyboard_handler():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        
        function pressButton(label) {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const target = buttons.find(btn => {
                const text = btn.innerText || "";
                if (['〇', '△', '×'].includes(label)) return text.trim() === label;
                return text.includes(label);
            });
            if (target) target.click();
        }

        doc.onkeydown = function(e) {
            if (e.repeat) return; // 長押し時は一回だけ
            const key = e.key.toLowerCase();
            if (key === 'p') pressButton('🔊');
            if (key === 'o') pressButton('👁️');
            if (key === 'k') pressButton('〇');
            if (key === 'l') pressButton('△');
            if (key === ';') pressButton('×');
        };
        </script>
        """,
        height=0
    )

# =====================================
# CSS (長文対策・はみ出し＆隠れ防止強化版)
# =====================================
st.markdown(
    """
<style>
/* 枠自体の最小高さを 180px に拡大し、縦に溢れた場合はスクロールできるようにする */
.word-box, .answer-box, .answer-spacer { 
    min-height: 180px;      /* 以前より高さを大きく確保してブレを防止 */
    height: auto;
    max-height: 260px;      /* 限界値を決めて下のボタンが潰れるのを防ぐ */
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 15px;
    margin-bottom: 10px;
    box-sizing: border-box;
    border: 2px solid transparent;
    padding: 20px;          /* 内側に十分な余白を作ってはみ出しを防ぐ */
    overflow-y: auto;       /* 万が一限界を超えたら枠内でスクロール可能にする */
}

.word-box { background-color: #f0f2f6; border-color: #ddd; }
.answer-box { background-color: #e3f2fd; border-color: #bbdefb; }
.answer-spacer { background-color: transparent; } /* 答えがない時もこの高さを維持 */

/* 答えの文字が絶対に溢れないように調整 */
.answer-box h2 {
    font-size: 1.35rem;     /* 文字サイズを少し抑えめに */
    font-weight: bold;
    margin: 0;
    text-align: center;
    line-height: 1.5;
    word-break: break-word; /* 単語や文章の途中で綺麗に折り返す */
    white-space: normal;    /* 自動折り返しを強制 */
    width: 100%;
}

/* ヒントエリアも高さを固定 */
.hint-container {
    height: 80px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.hint-box { 
    background-color: #fff3cd; 
    padding: 10px 20px; 
    border-radius: 10px; 
    color: #856404; 
    text-align: center;
    width: 100%;
}

.stButton>button { height: 3.2em; font-size: 18px; border-radius: 10px; width: 100%; font-weight: bold; }
.timer-text { font-size: 1.6rem; font-weight: bold; color: #e63946; text-align: center; }
.grid-item { background: #f8f9fa; border: 1px solid #e5e7eb; padding: 10px; border-radius: 10px; margin-bottom: 5px; }

@media (max-width: 768px) {
    .word-box, .answer-box, .answer-spacer { min-height: 130px; }
    .answer-box h2 { font-size: 1.15rem; } /* スマホではさらに文字を小さくして収める */
}
</style>
""",
    unsafe_allow_html=True
)

# =====================================
# セッション状態の初期化
# =====================================
if "status" not in st.session_state:
    st.session_state.status = "setting"
    st.session_state.results = {"〇": [], "△": [], "×": []}
    st.session_state.history = []

# =====================================
# 設定画面
# =====================================
if st.session_state.status == "setting":
    st.title("📚 単語テスト設定")
    book_options = {
        "ターゲット1900": "taget1900(6).csv", "ターゲット1400": "target1400.csv",
        "ターゲット1200": "target1200.csv", "ターゲット1000": "target1000.csv",
        "システム英単語": "sis-tan.csv", "LEAP(新)": "leap.csv",
        "LEAP(旧)": "leaped.csv", "速読英単語[必修編]": "sokutan2.csv","速読英単語[入門編]": "sokutan1.csv",
        "速読英熟語": "sokuzyuku.csv", "いろはにほへと": "いろはに.csv",
    }
    selected_book_name = st.selectbox("1: 本を選ぶ", list(book_options.keys()))
    csv_filename = book_options[selected_book_name]

    col1, col2 = st.columns(2)
    start_no = col1.number_input("開始番号", value=1, min_value=1)
    end_no = col2.number_input("終了番号", value=100, min_value=1)

    if st.button("テスト開始！"):
        try:
            csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
            df = pd.read_csv(csv_path, names=["no", "english", "japanese", "hint"])
            df["hint"] = df["hint"].fillna("").astype(str).str.strip()
            mask = (df["no"] >= start_no) & (df["no"] <= end_no)
            target_words = df.loc[mask].to_dict("records")

            if not target_words:
                st.error("指定範囲に単語が見つかりません。")
            else:
                st.session_state.test_list = random.sample(target_words, len(target_words))
                st.session_state.current_idx = 0
                st.session_state.show_ans = False
                st.session_state.show_hint = False
                st.session_state.results = {"〇": [], "△": [], "×": []}
                st.session_state.history = []
                st.session_state.start_time = time.time()
                st.session_state.status = "testing"
                st.rerun()
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")

# =====================================
# テスト画面
# =====================================
elif st.session_state.status == "testing":
    keyboard_handler()
    
    total_q = len(st.session_state.test_list)
    idx = st.session_state.current_idx
    q = st.session_state.test_list[idx]

    t_col1, t_col2 = st.columns([2, 1])
    t_col1.write(f"**Progress: {idx + 1} / {total_q}**")
    elapsed = int(time.time() - st.session_state.start_time)
    t_col2.markdown(f"<div class='timer-text'>⏳ {elapsed}s</div>", unsafe_allow_html=True)
    st.progress((idx + 1) / total_q)

    hint_val = str(q.get("hint", "")).strip()
    has_hint = (hint_val != "" and hint_val.lower() != "nan")

    col_main, col_ctrl = st.columns([7, 3])

    with col_main:
        # 単語表示（固定高）
        st.markdown(f"<div class='word-box'><h1>{q['english']}</h1></div>", unsafe_allow_html=True)
        
        # ヒントエリア（固定高）
        st.markdown("<div class='hint-container'>", unsafe_allow_html=True)
        if st.session_state.show_hint and has_hint:
            st.markdown(f"<div class='hint-box'>{hint_val}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 答えエリア（長文対応・はみ出さない仕様）
        if st.session_state.show_ans:
            st.markdown(f"<div class='answer-box'><h2>{q['japanese']}</h2></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='answer-spacer'></div>", unsafe_allow_html=True)

    with col_ctrl:
        st.button("🔊 音声", on_click=lambda: speak(q["english"]))
        
        if not st.session_state.show_ans:
            if st.button("👁️ 答え", type="primary"):
                st.session_state.show_ans = True
                st.rerun()
        
        if has_hint and not st.session_state.show_hint:
            if st.button("💡 ヒント"):
                st.session_state.show_hint = True
                st.rerun()

        st.write("---")
        # 判定ボタン
        c1, c2, c3 = st.columns(3)
        if c1.button("〇"):
            st.session_state.history.append("〇")
            st.session_state.results["〇"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            if st.session_state.current_idx >= total_q: st.session_state.status = "result"
            st.rerun()
        if c2.button("△"):
            st.session_state.history.append("△")
            st.session_state.results["△"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            if st.session_state.current_idx >= total_q: st.session_state.status = "result"
            st.rerun()
        if c3.button("×"):
            st.session_state.history.append("×")
            st.session_state.results["×"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            if st.session_state.current_idx >= total_q: st.session_state.status = "result"
            st.rerun()

        st.write("---")
        if idx > 0 and st.button("⬅️ 戻る"):
            prev = st.session_state.history.pop()
            st.session_state.results[prev].pop()
            st.session_state.current_idx -= 1
            st.session_state.show_ans = st.session_state.show_hint = False
            st.session_state.start_time = time.time()
            st.rerun()
        
        if st.button("終了"):
            st.session_state.status = "result"
            st.rerun()

# =====================================
# 結果画面
# =====================================
elif st.session_state.status == "result":
    st.title("📊 結果報告")
    res = st.session_state.results
    total = sum(len(v) for v in res.values())
    
    if total > 0:
        acc = (len(res["〇"]) / total) * 100
        st.metric("正答率", f"{acc:.1f}%")
        cols = st.columns(3)
        cols[0].info(f"〇: {len(res['〇'])}")
        cols[1].warning(f"△: {len(res['△'])}")
        cols[2].error(f"×: {len(res['×'])}")

    st.write("---")
    cl, cr = st.columns(2)
    with cl:
        st.subheader("△ (復習)")
        for i in res["△"]: st.markdown(f"<div class='grid-item'>{i['english']} : {i['japanese']}</div>", unsafe_allow_html=True)
    with cr:
        st.subheader("× (要練習)")
        for i in res["×"]: st.markdown(f"<div class='grid-item'>{i['english']} : {i['japanese']}</div>", unsafe_allow_html=True)

    st.write("---")
    retry = res["△"] + res["×"]
    if retry and st.button("🔄 不安な単語を再テスト", type="primary"):
        st.session_state.test_list = random.sample(retry, len(retry))
        st.session_state.current_idx = 0
        st.session_state.results = {"〇": [], "△": [], "×": []}
        st.session_state.history = []
        st.session_state.start_time = time.time()
        st.session_state.status = "testing"
        st.rerun()
    if st.button("🏠 戻る"):
        st.session_state.clear()
        st.rerun()
