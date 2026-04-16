import streamlit as st
import pandas as pd
import random
import os
from gtts import gTTS
import base64
import uuid

# =====================================
# ページ設定
# =====================================
st.set_page_config(page_title="英単語テスト", layout="centered")

# =====================================
# 音声再生（自動再生 / HTML audio）
# gTTSは通信が必要。失敗してもアプリが落ちないようにする
# =====================================
def speak(text: str):
    filename = f"temp_{uuid.uuid4().hex}.mp3"
    try:
        tts = gTTS(text=text, lang="en")
        tts.save(filename)

        with open(filename, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        # 正しい audio タグ：source の src に dataURI を入れる
        html = f"""
        <audio autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"音声生成に失敗しました（ネット接続等を確認）: {e}")

    finally:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass

# =====================================
# 共通CSS（PCは今のまま / スマホだけ圧縮）
# =====================================
st.markdown(
    """
<style>
/* ===== 共通 ===== */
.word-box {
    background-color: #f0f2f6;
    padding: 30px;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 10px;
    border: 2px solid #ddd;
    position: relative;
}
.hint-box {
    background-color: #fff3cd;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 20px;
    color: #856404;
}
.stButton>button {
    height: 3em;
    font-size: 18px;
    border-radius: 10px;
    width: 100%;
}
.answer-spacer {
    height: 100px;
}

/* 結果画面の見た目（最低限） */
.grid-header {
    font-size: 24px;
    font-weight: 800;
    margin: 8px 0 10px 0;
}
.grid-container {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
}
.grid-item {
    background: #f8f9fa;
    border: 1px solid #e5e7eb;
    padding: 10px;
    border-radius: 10px;
}

/* ===== スマホ専用：スクロールを減らす ===== */
@media (max-width: 768px) {
    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0.6rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }

    .word-box {
        padding: 16px;
        margin-bottom: 6px;
        border-radius: 14px;
    }

    .word-box h1 {
        font-size: 1.8rem;
        margin: 0.4rem 0;
        line-height: 1.15;
    }

    .word-box h2 {
        font-size: 1.15rem;
        margin: 0.3rem 0;
        line-height: 1.2;
    }

    .hint-box {
        padding: 8px;
        font-size: 0.92rem;
        margin-bottom: 8px;
        border-radius: 12px;
    }

    .stButton>button {
        height: 2.55em;
        font-size: 16px;
        border-radius: 12px;
        margin-bottom: 6px;
    }

    .answer-spacer {
        height: 26px !important;
    }
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

# =====================================
# 1&2: 設定画面
# =====================================
if st.session_state.status == "setting":
    st.title("📚 チェックテストを始める")

    book_options = {
        "ターゲット1900": "target1900.csv",
        "ターゲット1400": "target1400.csv",
        "ターゲット1200": "target1200.csv",
        "ターゲット1000": "target1000.csv",
        "システム英単語": "sis-tan.csv",
        "LEAP": "leap.csv",
        "LEAP(旧)": "leaped.csv",
        "速読英単語必修編": "sokutan2.csv",
        "速読英熟語": "sokuzyuku.csv",
        "いろはにほへと": "いろはに.csv",
    }

    selected_book_name = st.selectbox("1: 本を選ぶ", list(book_options.keys()))
    csv_filename = book_options[selected_book_name]

    st.write("2: テスト範囲指定")
    col1, col2 = st.columns(2)
    start_no = col1.number_input("開始番号", value=1, min_value=1)
    end_no = col2.number_input("終了番号", value=100, min_value=1)

    if st.button("3: 単語テスト実行！"):
        try:
            current_dir = os.path.dirname(__file__)
            csv_path = os.path.join(current_dir, csv_filename)

            # CSV読み込み（必要なら encoding="utf-8-sig" 等も試してOK）
            df = pd.read_csv(csv_path, names=["no", "english", "japanese", "hint"])

            # ★ hint正規化（NaN/空白/"nan"を全部「ヒントなし」に統一）
            df["hint"] = df["hint"].fillna("").astype(str).str.strip()
            df.loc[df["hint"].str.lower() == "nan", "hint"] = ""

            mask = (df["no"] >= start_no) & (df["no"] <= end_no)
            target_words = df.loc[mask].to_dict("records")

            if not target_words:
                st.error("その範囲に単語がありません！CSVの中身を確認してください。")
            else:
                st.session_state.test_list = random.sample(target_words, len(target_words))
                st.session_state.current_idx = 0
                st.session_state.show_ans = False
                st.session_state.show_hint = False
                st.session_state.status = "testing"
                st.rerun()

        except FileNotFoundError:
            st.error(f"ファイルが見つかりません: {csv_filename} を app.py と同じフォルダに置いてください。")
        except Exception as e:
            st.error(f"読み込みでエラー: {e}")

# =====================================
# 3: テスト画面
# =====================================
elif st.session_state.status == "testing":
    q = st.session_state.test_list[st.session_state.current_idx]

    # hintがあるか判定（正規化済み想定）
    hint_text = str(q.get("hint", "")).strip()
    has_hint = (hint_text != "" and hint_text.lower() != "nan")

    # スマホで「テスト画面だけ」スクロールをさらに出にくくする（必要なら）
    # これを強くすると、端末によっては完全にスクロールが止まります。
    # 結果画面まで止めたくないので "testing" の時だけ入れます。
    st.markdown(
        """
<style>
@media (max-width: 768px) {
  /* テスト画面中だけ、必要なら強制的に縦スクロールを抑える */
  /* 完全に止めたい場合は下のコメントを外してください */
  /* html, body { overflow: hidden !important; } */
}
</style>
""",
        unsafe_allow_html=True
    )

    st.title("📖 テスト")

    # 左：表示 / 右：操作（PCはそのまま、スマホは自動で縦に積まれます）
    col_main, col_ctrl = st.columns([8, 2])

    # --- 左側：問題と回答 ---
    with col_main:
        st.markdown(f"<div class='word-box'><h1>{q['english']}</h1></div>", unsafe_allow_html=True)

        # ヒント表示（show_hint かつ hintあり）
        if st.session_state.show_hint and has_hint:
            st.markdown(f"<div class='hint-box'>{hint_text}</div>", unsafe_allow_html=True)
        else:
            st.write("")

        # 答え表示
        if st.session_state.show_ans:
            st.markdown(
                f"<div class='word-box' style='background-color:#e1f5fe;'><h2>{q['japanese']}</h2></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown("<div class='answer-spacer'></div>", unsafe_allow_html=True)

    # --- 右側：操作ボタン ---
    with col_ctrl:
        if st.button("🔊 音声"):
            speak(q["english"])

        st.write("---")

        # 答え
        if not st.session_state.show_ans:
            if st.button("👁️ 答え"):
                st.session_state.show_ans = True
                st.rerun()

        # ★ ヒントがある単語だけ「💡 一言」を出す
        if has_hint and not st.session_state.show_hint:
            if st.button("💡 一言"):
                st.session_state.show_hint = True
                st.rerun()

        st.write("---")

        # 判定
        if st.button("〇"):
            st.session_state.results["〇"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = False
            st.session_state.show_hint = False
            if st.session_state.current_idx >= len(st.session_state.test_list):
                st.session_state.status = "result"
            st.rerun()

        if st.button("△"):
            st.session_state.results["△"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = False
            st.session_state.show_hint = False
            if st.session_state.current_idx >= len(st.session_state.test_list):
                st.session_state.status = "result"
            st.rerun()

        if st.button("×"):
            st.session_state.results["×"].append(q)
            st.session_state.current_idx += 1
            st.session_state.show_ans = False
            st.session_state.show_hint = False
            if st.session_state.current_idx >= len(st.session_state.test_list):
                st.session_state.status = "result"
            st.rerun()

        st.write("---")
        if st.button("中止"):
            st.session_state.status = "result"
            st.rerun()

# =====================================
# 4: 結果画面
# =====================================
elif st.session_state.status == "result":
    st.title("📊 復習リスト")

    col_left, col_right = st.columns(2)

    # 左：△
    with col_left:
        st.markdown("<div class='grid-header'>△</div>", unsafe_allow_html=True)
        if st.session_state.results["△"]:
            html = "<div class='grid-container'>"
            for i in st.session_state.results["△"]:
                html += f"<div class='grid-item'>{i['english']} ／ {i['japanese']}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.write("なし")

    # 右：×
    with col_right:
        st.markdown("<div class='grid-header'>×</div>", unsafe_allow_html=True)
        if st.session_state.results["×"]:
            html = "<div class='grid-container'>"
            for i in st.session_state.results["×"]:
                html += f"<div class='grid-item'>{i['english']} ／ {i['japanese']}</div>"
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.write("なし")

    st.write("---")
    if st.button("最初に戻る"):
        st.session_state.clear()
        st.rerun()
